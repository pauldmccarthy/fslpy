#!/usr/bin/env python
#
# mesh.py - The TriangleMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Mesh` class, which represents a
3D model made of triangles.

See also the following modules:

  .. autosummary::

     fsl.data.vtk
     fsl.data.gifti
     fsl.data.freesurfer

A handful of standalone functions are provided in this module, for doing
various things with meshes:

  .. autosummary::
     :nosignatures:

     calcFaceNormals
     calcVertexNormals
     needsFixing
"""


import logging
import collections

import six
import deprecation

import os.path as op
import numpy   as np

import fsl.utils.meta      as meta
import fsl.utils.notifier  as notifier
import fsl.utils.transform as transform


log = logging.getLogger(__name__)


class Mesh(notifier.Notifier, meta.Meta):
    """The ``Mesh`` class represents a 3D model. A mesh is defined by a
    collection of ``N`` vertices, and ``M`` triangles.  The triangles are
    defined by ``(M, 3)`` indices into the list of vertices.


    A ``Mesh`` instance has the following attributes:


    ============== ======================================================
    ``name``       A name, typically the file name sans-suffix.

    ``dataSource`` Full path to the mesh file (or ``None`` if there is
                   no file associated with this mesh).

    ``nvertices``  The number of vertices in the mesh.

    ``vertices``   A ``(n, 3)`` array containing the currently selected
                   vertices. You can assign  a vertex set key to this
                   attribute to change the selected vertex set.

    ``bounds``     The lower and upper bounds

    ``indices``    A ``(m, 3)`` array containing the vertex indices
                   for ``m`` triangles

    ``normals``    A  ``(m, 3)`` array containing face normals for the
                   triangles

    ``vnormals``   A ``(n, 3)`` array containing vertex normals for the
                   the current vertices.

    ``trimesh``    (if the `trimesh <https://github.com/mikedh/trimesh>`_
                   library is present) A ``trimesh.Trimesh`` object which
                   can be used for geometric queries on the mesh.
    ============== ======================================================


    **Vertex sets**


    A ``Mesh`` object can be associated with multiple sets of vertices, but
    only one set of triangles. Vertices can be added via the
    :meth:`addVertices` method. Each vertex set must be associated with a
    unique key - you can then select the current vertex set via the
    :meth:`vertices` property. Most ``Mesh`` methods will raise a ``KeyError``
    if you have not added any vertex sets, or selected a vertex set. The
    following methods are available for managing vertex sets:

    .. autosummary::
       :nosignatures:

       loadVertices
       addVertices
       selectedVertices
       vertexSets


    **Vertex data**


    A ``Mesh`` object can store vertex-wise data. The following methods can be
    used for adding/retrieving vertex data:

    .. autosummary::
       :nosignatures:

       loadVertexData
       addVertexData
       getVertexData
       vertexDataSets
       clearVertexData


    **Notification**


    The ``Mesh`` class inherits from the :class:`Notifier` class. Whenever the
    ``Mesh`` vertex set is changed, a notification is emitted via the
    ``Notifier`` interface, with a topic of ``'vertices'``. When this occurs,
    the :meth:`vertices`, :meth:`bounds`, :meth:`normals` and :attr:`vnormals`
    properties will all change so that they return data specific to the newly
    selected vertex set.


    **Metadata**


    The ``Mesh`` class also inherits from the :class:`Meta` class, so
    any metadata associated with the ``Mesh`` may be added via those methods.


    **Geometric queries**


    If the ``trimesh`` library is present, the following methods may be used
    to perform geometric queries on a mesh:

    .. autosummary::
       :nosignatures:

       rayIntersection
       planeIntersection
       nearestVertex
    """


    def __new__(cls, *args, **kwargs):
        """Create a ``Mesh``. We must override ``__new__``, otherwise the
        :class:`Meta` and :class:`Notifier` ``__new__`` methods will not be
        called correctly.
        """
        return super(Mesh, cls).__new__(cls, *args, **kwargs)


    def __init__(self,
                 indices,
                 name='mesh',
                 dataSource=None,
                 vertices=None,
                 fixWinding=False):
        """Create a ``Mesh`` instance.

        Before a ``Mesh`` can be used, some vertices must be added via the
        :meth:`addVertices` method.

        :arg indices:    A list of indices into the vertex data, defining the
                         mesh triangles.

        :arg name:       A name for this ``Mesh``.

        :arg dataSource: The data source for this ``Mesh``.

        :arg vertices:   Initial vertex set to add - given the key
                         ``'default'``.

        :arg fixWinding: Ignored if ``vertices is None``. Passed through to the
                         :meth:`addVertices` method along with ``vertices``.
        """

        self.__name       = name
        self.__dataSource = dataSource
        self.__indices    = np.asarray(indices).reshape((-1, 3))
        self.__nvertices  = self.__indices.max() + 1

        # This attribute is used to store
        # the currently selected vertex set,
        # used as a kety into all of the
        # dictionaries below.
        self.__selected = None

        # Flag used to keep track of whether
        # the triangle winding order has been
        # "fixed" - see the addVertices method.
        self.__fixed = False

        # All of these are populated
        # in the addVertices method
        self.__vertices = collections.OrderedDict()
        self.__loBounds = collections.OrderedDict()
        self.__hiBounds = collections.OrderedDict()

        # These get populated on
        # normals/vnormals accesses
        self.__faceNormals = collections.OrderedDict()
        self.__vertNormals = collections.OrderedDict()

        # this gets populated in
        # the addVertexData method
        self.__vertexData  = collections.OrderedDict()

        # this gets populated
        # in the trimesh method
        self.__trimesh = collections.OrderedDict()

        # Add initial vertex
        # set if provided
        if vertices is not None:
            self.addVertices(vertices, fixWinding=fixWinding)


    def __repr__(self):
        """Returns a string representation of this ``Mesh`` instance. """
        return '{}({}, {})'.format(type(self).__name__,
                                   self.name,
                                   self.dataSource)


    def __str__(self):
        """Returns a string representation of this ``Mesh`` instance.
        """
        return self.__repr__()


    @property
    def name(self):
        """Returns the name of this ``Mesh``. """
        return self.__name


    @property
    def dataSource(self):
        """Returns the data source of this ``Mesh``. """
        return self.__dataSource


    @property
    def nvertices(self):
        """Returns the number of vertices in the mesh. """
        return self.__nvertices


    @property
    def vertices(self):
        """The ``(N, 3)`` vertices of this mesh. """
        return self.__vertices[self.__selected]


    @vertices.setter
    def vertices(self, key):
        """Select the current vertex set - a ``KeyError`` is raised
        if no vertex set with the specified ``key`` has been added.

        When the current vertex set is changed, a notification is emitted
        through the :class:`.Notifier` interface, with the topic
        ``'vertices'``.
        """

        # Force a key error if
        # the key is invalid
        self.__vertices[key]

        if self.__selected != key:
            self.__selected = key
            self.notify(topic='vertices')


    @property
    def indices(self):
        """The ``(M, 3)`` triangles of this mesh. """
        return self.__indices


    @property
    def normals(self):
        """A ``(M, 3)`` array containing surface normals for every
        triangle in the mesh, normalised to unit length.
        """

        selected = self.__selected
        indices  = self.__indices
        vertices = self.__vertices[selected]
        fnormals = self.__faceNormals.get(selected, None)

        if fnormals is None:
            fnormals = calcFaceNormals(vertices, indices)
            self.__faceNormals[selected] = fnormals

        return fnormals


    @property
    def vnormals(self):
        """A ``(N, 3)`` array containing normals for every vertex
        in the mesh.
        """

        selected = self.__selected
        indices  = self.__indices
        vertices = self.__vertices[selected]
        vnormals = self.__vertNormals.get(selected, None)

        if vnormals is None:
            vnormals = calcVertexNormals(vertices, indices, self.normals)
            self.__vertNormals[selected] = vnormals

        return vnormals


    @property
    def bounds(self):
        """Returns a tuple of values which define a minimal bounding box that
        will contain all of the currently selected vertices in this
        ``Mesh`` instance. The bounding box is arranged like so:

            ``((xlow, ylow, zlow), (xhigh, yhigh, zhigh))``
        """

        lo = self.__loBounds[self.__selected]
        hi = self.__hiBounds[self.__selected]

        return lo, hi


    def loadVertices(self, infile, key=None, **kwargs):
        """Loads vertex data from the given ``infile``, and adds it as a vertex
        set with the given ``key``. This implementation supports loading vertex
        data from white-space delimited text files via ``numpy.loadtxt``, but
        sub-classes may override this method to support additional file types.


        :arg infile: File to load data from.

        :arg key:    Key to pass to :meth:`addVertices`. If not provided,
                     set to ``infile`` (converted to an absolute path)

        All of the other arguments are passed through to :meth:`addVertices`.

        :returns:    The loaded vertices.
        """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        vertices = np.loadtxt(infile)

        return self.addVertices(vertices, key, **kwargs)


    def addVertices(self, vertices, key=None, select=True, fixWinding=False):
        """Adds a set of vertices to this ``Mesh``.

        :arg vertices:   A `(n, 3)` array containing ``n`` vertices, compatible
                         with the indices specified in :meth:`__init__`.

        :arg key:        A key for this vertex set. If ``None`` defaults to
                         ``'default'``.

        :arg select:     If ``True`` (the default), this vertex set is
                         made the currently selected vertex set.

        :arg fixWinding: Defaults to ``False``. If ``True``, the vertex
                         winding order of every triangle is is fixed so they
                         all have outward-facing normal vectors.

        :returns:        The vertices, possibly reshaped

        :raises:         ``ValueError`` if the provided ``vertices`` array
                         has the wrong number of vertices.
        """

        if key is None:
            key = 'default'

        vertices = np.asarray(vertices)
        lo       = vertices.min(axis=0)
        hi       = vertices.max(axis=0)

        # Don't allow vertices of
        # different size to be added
        try:
            vertices = vertices.reshape(self.nvertices, 3)

        # reshape raised an error -
        # wrong number of vertices
        except ValueError:
            raise ValueError('{}: invalid number of vertices: '
                             '{} != ({}, 3)'.format(key,
                                                    vertices.shape,
                                                    self.nvertices))

        self.__vertices[key] = vertices
        self.__loBounds[key] = lo
        self.__hiBounds[key] = hi

        if select:
            self.vertices = key

        # indices already fixed?
        if fixWinding and (not self.__fixed):
            indices      = self.indices
            normals      = self.normals
            needsFix     = needsFixing(vertices, indices, normals, lo, hi)
            self.__fixed = True

            # See needsFixing documentation
            if needsFix:

                indices[:, [1, 2]] = indices[:, [2, 1]]

                for k, fn in self.__faceNormals.items():
                    self.__faceNormals[k] = fn * -1

        return vertices


    def vertexSets(self):
        """Returns a list containing the keys of all vertex sets. """
        return list(self.__vertices.keys())


    def selectedVertices(self):
        """Returns the key of the currently selected vertex set. """
        return self.__selected


    def loadVertexData(self, infile, key=None):
        """Loads vertex-wise data from the given ``infile``, and adds it with
        the given ``key``. This implementation supports loading data from
        whitespace-delimited text files via ``numpy.loadtxt``, but sub-classes
        may override this method to support additional file types.

        :arg infile: File to load data from.

        :arg key:    Key to pass to :meth:`addVertexData`. If not provided,
                     set to ``infile`` (converted to an absolute path)

        :returns:    The loaded vertex data.
        """

        infile = op.abspath(infile)

        if key is None:
            key = infile

        vertexData = np.loadtxt(infile)

        return self.addVertexData(key, vertexData)


    def addVertexData(self, key, vdata):
        """Adds a vertex-wise data set to the ``Mesh``. It can be retrieved
        by passing the specified ``key`` to the :meth:`getVertexData` method.

        :returns: The vertex data, possibly reshaped.
        """

        nvertices = self.nvertices

        if vdata.ndim not in (1, 2) or vdata.shape[0] != nvertices:
            raise ValueError('{}: incompatible vertex data '
                             'shape: {}'.format(key, vdata.shape))

        vdata                  = vdata.reshape(nvertices, -1)
        self.__vertexData[key] = vdata

        return vdata


    def getVertexData(self, key):
        """Returns the vertex data for the given ``key`` from the
        internal vertex data cache. If there is no vertex data iwth the
        given key, a ``KeyError`` is raised.
        """

        return self.__vertexData[key]


    def clearVertexData(self):
        """Clears the internal vertex data cache - see the
        :meth:`addVertexData` and :meth:`getVertexData` methods.
        """
        self.__vertexData = collections.OrderedDict()


    def vertexDataSets(self):
        """Returns a list of keys for all loaded vertex data sets. """
        return list(self.__vertexData.keys())


    @property
    def trimesh(self):
        """Reference to a ``trimesh.Trimesh`` object which can be used for
        geometric operations on the mesh.

        If the ``trimesh`` or ``rtree`` libraries are not available, this
        function returns ``None``, and none of the geometric query methods
        will do anything.
        """

        # trimesh is an optional dependency - rtree
        # is a depedendency of trimesh which is a
        # wrapper around libspatialindex, without
        # which trimesh can't be used for calculating
        # ray-mesh intersections.
        try:
            import trimesh
            import rtree   # noqa
        except ImportError:
            log.warning('trimesh is not available')
            return None

        tm = self.__trimesh.get(self.__selected, None)

        if tm is None:
            tm = trimesh.Trimesh(self.vertices,
                                 self.indices,
                                 process=False,
                                 validate=False)

            self.__trimesh[self.__selected] = tm

        return tm


    def rayIntersection(self, origins, directions, vertices=False):
        """Calculate the intersection between the mesh, and the rays defined by
        ``origins`` and ``directions``.

        :arg origins:    Sequence of ray origins
        :arg directions: Sequence of ray directions
        :returns:        A tuple containing:

                           - A ``(n, 3)`` array containing the coordinates
                             where the mesh was intersected by each of the
                             ``n`` rays.

                           - A ``(n,)`` array containing the indices of the
                             triangles that were intersected by each of the
                             ``n`` rays.
        """

        trimesh = self.trimesh

        if trimesh is None:
            return np.zeros((0, 3)), np.zeros((0,))

        tris, rays, locs = trimesh.ray.intersects_id(
            origins,
            directions,
            return_locations=True,
            multiple_hits=False)

        if len(tris) == 0:
            return np.zeros((0, 3)), np.zeros((0,))

        # sort by ray. I'm Not sure if this is
        # needed - does trimesh do it for us?
        rayIdxs = np.asarray(np.argsort(rays), np.int)
        locs    = locs[rayIdxs]
        tris    = tris[rayIdxs]

        return locs, tris


    def nearestVertex(self, points):
        """Identifies the nearest vertex to each of the provided points.

        :arg points: A ``(n, 3)`` array containing the points to query.

        :returns:    A tuple containing:

                      - A ``(n, 3)`` array containing the nearest vertex for
                        for each of the ``n`` input points.

                      - A ``(n,)`` array containing the indices of each vertex.

                      - A ``(n,)`` array containing the distance from each
                        point to the nearest vertex.
        """

        trimesh = self.trimesh

        if trimesh is None:
            return np.zeros((0, 3)), np.zeros((0, )), np.zeros((0, ))

        dists, idxs = trimesh.nearest.vertex(points)
        verts       = self.vertices[idxs, :]

        return verts, idxs, dists


    def planeIntersection(self,
                          normal,
                          origin,
                          distances=False):
        """Calculate the intersection of this ``TriangleMesh`` with
        the plane defined by ``normal`` and ``origin``.

        :arg normal:    Vector defining the plane orientation

        :arg origin:    Point defining the plane location

        :arg distances: If ``True``, barycentric coordinates for each
                        intersection line vertex are calculated and returned,
                        giving their respective distance from the intersected
                        triangle vertices.

        :returns:       A tuple containing

                          - A ``(m, 2, 3)`` array containing ``m`` vertices:
                            of a set of lines, defining the plane intersection

                          - A ``(m,)`` array containing the indices of the
                            ``m`` triangles that were intersected.

                          - (if ``distances is True``) A ``(m, 2, 3)`` array
                            containing the barycentric coordinates of each
                            line vertex with respect to its intersected
                            triangle.
        """

        trimesh = self.trimesh

        if trimesh is None:
            return np.zeros((0, 3)), np.zeros((0, 3))

        import trimesh.intersections as tmint
        import trimesh.triangles     as tmtri

        lines, faces = tmint.mesh_plane(
            trimesh,
            plane_normal=normal,
            plane_origin=origin,
            return_faces=True)

        if not distances:
            return lines, faces

        # Calculate the barycentric coordinates
        # (distance from triangle vertices) for
        # each intersection line

        triangles = self.vertices[self.indices[faces]].repeat(2, axis=0)
        points    = lines.reshape((-1, 3))

        if triangles.size > 0:
            dists = tmtri.points_to_barycentric(triangles, points)
            dists = dists.reshape((-1, 2, 3))
        else:
            dists = np.zeros((0, 2, 3))

        return lines, faces, dists


def calcFaceNormals(vertices, indices):
    """Calculates face normals for the mesh described by ``vertices`` and
    ``indices``.

    :arg vertices: A ``(n, 3)`` array containing the mesh vertices.
    :arg indices:  A ``(m, 3)`` array containing the mesh triangles.
    :returns:      A ``(m, 3)`` array containing normals for every triangle in
                   the mesh.
    """

    v0 = vertices[indices[:, 0]]
    v1 = vertices[indices[:, 1]]
    v2 = vertices[indices[:, 2]]

    fnormals = np.cross((v1 - v0), (v2 - v0))
    fnormals = transform.normalise(fnormals)

    return fnormals


def calcVertexNormals(vertices, indices, fnormals):
    """Calculates vertex normals for the mesh described by ``vertices``
    and ``indices``.

    :arg vertices: A ``(n, 3)`` array containing the mesh vertices.
    :arg indices:  A ``(m, 3)`` array containing the mesh triangles.
    :arg fnormals: A ``(m, 3)`` array containing the face/triangle normals.
    :returns:      A ``(n, 3)`` array containing normals for every vertex in
                   the mesh.
    """

    vnormals = np.zeros((vertices.shape[0], 3), dtype=np.float)

    # TODO make fast. I can't figure
    # out how to use np.add.at to
    # accumulate the face normals for
    # each vertex.
    for i in range(indices.shape[0]):

        v0, v1, v2 = indices[i]

        vnormals[v0, :] += fnormals[i]
        vnormals[v1, :] += fnormals[i]
        vnormals[v2, :] += fnormals[i]

    # normalise to unit length
    return transform.normalise(vnormals)


def needsFixing(vertices, indices, fnormals, loBounds, hiBounds):
    """Determines whether the triangle winding order, for the mesh described by
    ``vertices`` and ``indices``, needs to be flipped.

    If this function returns ``True``, the given ``indices`` and ``fnormals``
    need to be adjusted so that all face normals are facing outwards from the
    centre of the mesh. The necessary adjustments are as follows::

        indices[:, [1, 2]] = indices[:, [2, 1]]
        fnormals           = fnormals * -1

    :arg vertices: A ``(n, 3)`` array containing the mesh vertices.
    :arg indices:  A ``(m, 3)`` array containing the mesh triangles.
    :arg fnormals: A ``(m, 3)`` array containing the face/triangle normals.
    :arg loBounds: A ``(3, )`` array contaning the low vertex bounds.
    :arg hiBounds: A ``(3, )`` array contaning the high vertex bounds.

    :returns:      ``True`` if the ``indices`` and ``fnormals`` need to be
                   adjusted, ``False`` otherwise.
    """

    # Define a viewpoint which is
    # far away from the mesh.
    camera = loBounds - (hiBounds - loBounds)

    # Find the nearest vertex
    # to the viewpoint
    dists = np.sqrt(np.sum((vertices - camera) ** 2, axis=1))
    ivert = np.argmin(dists)
    vert  = vertices[ivert]

    # Pick a triangle that
    # this vertex is in and
    # ges its face normal
    itri = np.where(indices == ivert)[0][0]
    n    = fnormals[itri, :]

    # Make sure the angle between the
    # normal, and a vector from the
    # vertex to the camera is positive
    # If it isn't, we need to flip the
    # triangle winding order.
    return np.dot(n, transform.normalise(camera - vert)) < 0


class TriangleMesh(Mesh):
    """Deprecated - use :class:`fsl.data.mesh.Mesh`, or one of its sub-classes
    instead.
    """


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use fsl.data.mesh.Mesh, or one '
                                    'of its sub-classes instead')
    def __init__(self, data, indices=None, fixWinding=False):

        import fsl.data.vtk as fslvtk

        if isinstance(data, six.string_types):
            name       = op.basename(data)
            dataSource = data
            mesh       = fslvtk.VTKMesh(data, fixWinding=False)
            vertices   = mesh.vertices
            indices    = mesh.indices

        else:
            name       = 'TriangleMesh'
            dataSource = None
            vertices   = data

        Mesh.__init__(self, indices, name=name, dataSource=dataSource)
        self.addVertices(vertices, 'default', fixWinding=fixWinding)


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use the Mesh class instead')
    def loadVertexData(self, dataSource, vertexData=None):

        nvertices = self.vertices.shape[0]

        # Currently only white-space delimited
        # text files are supported
        if vertexData is None:
            vertexData = np.loadtxt(dataSource)
            vertexData.reshape(nvertices, -1)

        if vertexData.shape[0] != nvertices:
            raise ValueError('Incompatible size: {}'.format(dataSource))

        self.addVertexData(dataSource, vertexData)

        return vertexData


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use bounds instead')
    def getBounds(self):
        """Deprecated - use :meth:`bounds` instead. """
        return self.bounds


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use the Mesh class instead')
    def getVertexData(self, dataSource):
        try:
            return Mesh.getVertexData(self, dataSource)
        except KeyError:
            return self.loadVertexData(dataSource)


@deprecation.deprecated(deprecated_in='1.6.0',
                        removed_in='2.0.0',
                        details='Use fsl.data.vtk.loadVTKPolydataFile instead')
def loadVTKPolydataFile(*args, **kwargs):
    """Deprecated - use :func:`fsl.data.vtk.loadVTKPolydataFile` instead. """
    import fsl.data.vtk as fslvtk
    return fslvtk.loadVTKPolydataFile(*args, **kwargs)


@deprecation.deprecated(deprecated_in='1.6.0',
                        removed_in='2.0.0',
                        details='Use fsl.data.vtk.getFIRSTPrefix instead')
def getFIRSTPrefix(*args, **kwargs):
    """Deprecated - use :func:`fsl.data.vtk.getFIRSTPrefix` instead. """
    import fsl.data.vtk as fslvtk
    return fslvtk.getFIRSTPrefix(*args, **kwargs)


@deprecation.deprecated(deprecated_in='1.6.0',
                        removed_in='2.0.0',
                        details='Use fsl.data.vtk.findReferenceImage instead')
def findReferenceImage(*args, **kwargs):
    """Deprecated - use :func:`fsl.data.vtk.findReferenceImage` instead. """
    import fsl.data.vtk as fslvtk
    return fslvtk.findReferenceImage(*args, **kwargs)


ALLOWED_EXTENSIONS = ['.vtk']
"""Deprecated, will be removed in fslpy 2.0.0. Use
:attr:`fsl.data.vtk.ALLOWED_EXTENSIONS` instead."""


EXTENSION_DESCRIPTIONS = ['VTK polygon model file']
"""Deprecated, will be removed in fslpy 2.0.0. Use
:attr:`fsl.data.vtk.EXTENSION_DESCRIPTIONS` instead."""
