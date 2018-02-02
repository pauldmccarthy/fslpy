#!/usr/bin/env python
#
# imcp.py - Functions for moving/copying NIFTI image files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for moving/copying NIFIT image files.

.. autosummary::
   :nosignatures:

   imcp
   immv
"""


import                   os
import os.path        as op
import                   shutil

import nibabel        as nib

import fsl.utils.path as fslpath
import fsl.data.image as fslimage


def imcp(src,
         dest,
         overwrite=False,
         useDefaultExt=False,
         move=False):
    """Copy the given ``src`` file to destination ``dest``.

    A :class:`.fsl.utils.path.PathError` is raised if anything goes wrong.

    :arg src:           Path to copy. If ``allowedExts`` is provided,
                        the file extension can be omitted.

    :arg dest:          Destination path. Can be an incomplete file
                        specification (i.e. without the extension), or a
                        directory.

    :arg overwrite:     If ``True`` this function will overwrite files that
                        already exist. Defaults to ``False``.

    :arg useDefaultExt: Defaults to ``False``. If ``True``, the destination
                        file type will be set according to the default
                        extension, specified by
                        :func:`~fsl.data.image.defaultExt`. If the source
                        file does not have the same type as the default
                        extension, it will be converted. If ``False``, the
                        source file type is not changed.

    :arg move:          If ``True``, the files are moved, instead of being
                        copied. See :func:`immv`.
    """

    # special case - non-existent directory
    if dest.endswith('/') and not op.isdir(dest):
        raise fslpath.PathError('Directory does not exist: {}'.format(dest))

    if op.isdir(dest):
        dest = op.join(dest, op.basename(src))

    src  = op.abspath(src)
    dest = op.abspath(dest)

    srcBase,  srcExt  = fslimage.splitExt(src)
    destBase, destExt = fslimage.splitExt(dest)

    # src was specified without an
    # extension, or the specified
    # src does not have an allowed
    # extension.
    if srcExt == '':

        # Try to resolve the specified src
        # path - if src does not exist, or
        # does not have an allowed extension,
        # addExt will raise an error
        src = fslimage.addExt(src, mustExist=True)

        # We've resolved src to a
        # full filename - split it
        # again to get its extension
        srcBase, srcExt = fslimage.splitExt(src)

    if not op.exists(src):
        raise fslpath.PathError('imcp error - source path '
                                'does not exist: {}'.format(src))

    # Figure out the destination file
    # extension/type. If useDefaultExt
    # is True, we use the default
    # extension. Otherwise, if no
    # destination file extension is
    # provided, we use the source
    # extension.
    if   useDefaultExt: destExt = fslimage.defaultExt()
    elif destExt == '': destExt = srcExt

    # Resolve any file group differences
    # e.g. we don't care if the src is
    # specified as file.hdr, and the dest
    # is specified as file.img - if src
    # and dest are part of the same file
    # group, we replace the dest extension
    # with the src extension.
    if srcExt != destExt:
        for group in fslimage.FILE_GROUPS:
            if srcExt in group and destExt in group:
                destExt = srcExt
                break

    dest = destBase + destExt

    # Give up if we don't have permission.
    if          not os.access(op.dirname(dest), os.W_OK | os.X_OK):
        raise fslpath.PathError('imcp error - cannot write to {}'.format(dest))

    if move and not os.access(op.dirname(src),  os.W_OK | os.X_OK):
        raise fslpath.PathError('imcp error - cannot move from {}'.format(src))

    # If the source file type does not
    # match the destination file type,
    # we need to perform a conversion.
    #
    # This is more expensive in terms of
    # io and cpu, but programmatically
    # very easy - nibabel does all the
    # hard work.
    if srcExt != destExt:

        if not overwrite and op.exists(dest):
            raise fslpath.PathError('imcp error - destination already '
                                    'exists ({})'.format(dest))

        img = nib.load(src)
        nib.save(img, dest)

        if move:
            # if input is an image pair, we
            # need to remove all input files
            srcs = fslpath.getFileGroup(src,
                                        fslimage.ALLOWED_EXTENSIONS,
                                        fslimage.FILE_GROUPS)
            for src in srcs:
                os.remove(src)

        return

    # Otherwise we do a file copy. This
    # is actually more complicated than
    # converting the file type due to
    # hdr/img pairs ...
    #
    # If the source is part of a file group,
    # e.g. src.img/src.hdr), we need to copy
    # the whole set of files. So here we
    # build a list of source files that need
    # to be copied/moved. The getFileGroup
    # function returns all other files that
    # are associated with this file (i.e.
    # part of the same group).
    #
    # We store the sources as separate
    # (base, ext) tuples, so we don't
    # have to re-split when creating
    # destination paths.
    #
    # The unambiguous flag tells getFileGroup
    # to raise an error if the source appears
    # to be part of an incopmlete file group
    # (e.g. file.hdr without an accompanying
    # file.img).
    copySrcs = fslpath.getFileGroup(src,
                                    fslimage.ALLOWED_EXTENSIONS,
                                    fslimage.FILE_GROUPS,
                                    fullPaths=False,
                                    unambiguous=True)
    copySrcs = [(srcBase, e) for e in copySrcs]

    # Build a list of destinations for each
    # copy source - we build this list in
    # advance, so we can fail if any of the
    # destinations already exist. We also
    # re-combine the source bases/extensions.
    copyDests = [destBase + e for (b, e) in copySrcs]
    copySrcs  = [b        + e for (b, e) in copySrcs]

    # Fail if any of the destination
    # paths already exist
    if not overwrite and any([op.exists(d) for d in copyDests]):
        raise fslpath.PathError('imcp error - a destination path already '
                                'exists ({})'.format(', '.join(copyDests)))

    # Do the copy/move
    for src, dest in zip(copySrcs, copyDests):
        if move: shutil.move(src, dest)
        else:    shutil.copy(src, dest)


def immv(src,
         dest,
         overwrite=False,
         useDefaultExt=False):
    """Move the specified ``src`` to the specified ``dest``. See :func:`imcp`.
    """
    imcp(src,
         dest,
         overwrite=overwrite,
         useDefaultExt=useDefaultExt,
         move=True)
