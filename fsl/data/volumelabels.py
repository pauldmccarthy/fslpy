#!/usr/bin/env python
#
# volumelabels.py - The VolumeLabels class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`VolumeLabels` class, which is used to
manage labels associated with the volumes of an :class:`.Image`.  This class
is primarily used for managing component classifications of a
:class:`.MelodicImage`.

See also the :func:`.fixlabels` module for loading/saving melodic label files.
"""


import logging

import fsl.utils.notifier as notifier
import fsl.data.fixlabels as fixlabels


log = logging.getLogger(__name__)


class VolumeLabels(notifier.Notifier):
    """The ``VolumeLabels`` class is a convenience class for managing a
    collection of classification labels for the volumes of an :class:`.Image`.

    The ``VolumeLabels`` class refers to *volumes* as *components*, because
    it was originally written to manage classification labels associated wirh
    the components of a Melodic analysis.

    The following methods are available on a ``VolumeLabels`` instance:

    .. autosummary::
       :nosignatures:

       clear
       load
       save
       numComponents
       hasLabel
       hasComponent
       getLabels
       getAllLabels
       getDisplayLabel
       getComponents
       addLabel
       addComponent
       removeLabel
       removeComponent
       clearLabels
       clearComponents

    The ``VolumeLabels`` class uses the :class:`.Notifier` interface
    to notify listeners about changes to the labels. Listeners can be
    registered to be notified on the following topics:

      - ``added``:   A new label was added to a component.
      - ``removed``: A label was removed from a component.

    When either of these events occur, the value passed to registered
    listeners will contain a list of ``(component, label)``) tuples,
    which specify the labels that were added/removed.

    .. note:: All component labels are internally stored as lower case;
              however, their cased version (whatever is initially used) is
              accessible via the :meth:`getDisplayLabel` method.
    """


    def __init__(self, nvolumes):
        """Create a ``VolumeLabels`` instance.

        :arg nvolumes: Number of volumes to be classified. This cannot be
                       changed.
        """

        self.__ncomps        = nvolumes
        self.__displayLabels = {}

        # __labels is a list of lists, one list
        # for each component, containing the
        # labels for that component.
        #
        # __components is a dictionary of
        #
        #   { label : [component] } mappings
        #
        # containing the same information, but
        # making lookup by label a bit quicker.
        #
        # These are initialised in clear()
        self.__labels     = None
        self.__components = None

        self.clear()

    def numComponents(self):
        """Returns the number of components (a.k.a. volumes) that this
        ``VolumeLabels`` instance is managing.
        """
        return self.__ncomps


    def getDisplayLabel(self, label):
        """Returns the display name for the given label. """
        return self.__displayLabels.get(label.lower(), label)


    def clear(self):
        """Removes all labels from all components. """

        self.__components = {}
        self.__labels     = [[] for i in range(self.__ncomps)]


    def load(self, filename):
        """Loads component labels from the specified file. See the
        :func:`.fixlabels.loadLabelFile` function.

        .. note:: This method adds to, but does not replace, any existing
                  component classifications stored by this
                  ``VolumeLabels`` instance. Call the :meth:`clear` method,
                  before calling ``load``, if you want to discard any existing
                  classifications.
        """

        # Read the labels in
        _, allLabels = fixlabels.loadLabelFile(filename)

        # More labels in the file than there are in
        # this labels instance - that doesn't make
        # any sense.
        if len(allLabels) > self.__ncomps:
            raise fixlabels.InvalidLabelFileError(
                'Wrong number of components in {}!'.format(filename))

        # Less labels in the file than there are in
        # this labels instance - this is ok, as the
        # file may have only contained a list of
        # noisy components. We'll label the remaining
        # components as 'Unknown'.
        elif len(allLabels) < self.__ncomps:
            for i in range(len(allLabels), self.__ncomps):
                allLabels.append(['Unknown'])

        # Add the labels to this object
        with self.skipAll(topic='added'):
            for i, labels in enumerate(allLabels):
                for label in labels:
                    self.addLabel(i, label)


    def save(self, filename, dirname=None):
        """Saves the component classifications stored by this ``VolumeLabels``
        instance to the specified file. See the
        :func:`.fixlabels.saveLabelFile` function.
        """

        allLabels = []

        for c in range(self.__ncomps):
            labels = [self.getDisplayLabel(l) for l in self.getLabels(c)]
            allLabels.append(labels)

        fixlabels.saveLabelFile(allLabels, filename, dirname=dirname)


    def getLabels(self, component):
        """Returns all labels of the specified component. """
        return list(self.__labels[component])


    def getAllLabels(self):
        """Returns all labels that are currently associated with any
        component.
        """
        return list(self.__components.keys())


    def hasLabel(self, component, label):
        """Returns ``True`` if the specified component has the specified label,
        ``False`` otherwise.
        """
        label = label.lower()
        return label in self.__labels[component]


    def addLabel(self, component, label, notify=True):
        """Adds the given label to the given component.

        :arg notify: If ``True`` (the default), the :meth:`.Notifier.notify`
                     method will be called, with the ``'added'`` topic.
                     This parameter is only intended for uses interal to the
                     ``VolumeLabels`` class.

        :returns: ``True`` if the label was added, ``False`` if the label was
                  already present.
        """

        display = label
        label   = label.lower()
        labels  = list(self.__labels[component])
        comps   = list(self.__components.get(label, []))

        if label in labels:
            return False

        labels.append(label)
        comps .append(component)

        self.__displayLabels[label]     = display
        self.__components[   label]     = comps
        self.__labels[       component] = labels

        log.debug('Label added to component: {} <-> {}'.format(component,
                                                               label))

        if notify:
            self.notify(topic='added', value=[(component, label)])

        return True


    def removeLabel(self, component, label, notify=True):
        """Removes the given label from the given component.

        :returns: ``True`` if the label was removed, ``False`` if the
                  component did not have this label.
        """

        label  = label.lower()
        labels = list(self.__labels[component])
        comps  = list(self.__components.get(label, []))

        if label not in labels:
            return False

        labels.remove(label)
        comps .remove(component)

        if len(comps) == 0:
            self.__components.pop(label, None)
        else:
            self.__components[label] = comps

        self.__labels[component] = labels

        log.debug('Label removed from component: {} <-> {}'.format(component,
                                                                   label))

        if notify:
            self.notify(topic='removed', value=[(component, label)])

        return True


    def clearLabels(self, component):
        """Removes all labels from the given component. """

        labels  = self.getLabels(component)
        removed = []

        for label in labels:
            if self.removeLabel(component, label, notify=False):
                removed.append((component, label))

        log.debug('Labels cleared from component: {}'.format(component))

        if len(removed) > 0:
            self.notify(topic='removed', value=removed)


    def getComponents(self, label):
        """Returns a list of all components which have the given label. """
        label = label.lower()
        return list(self.__components.get(label, []))


    def hasComponent(self, label, component):
        """Returns ``True`` if the given compoennt has the given label,
        ``False`` otherwise.
        """
        return component in self.getComponents(label)


    def addComponent(self, label, component):
        """Adds the given label to the given component. """
        return self.addLabel(component, label)


    def removeComponent(self, label, component, notify=True):
        """Removes the given label from the given component. """
        return self.removeLabel(component, label, notify)


    def clearComponents(self, label):
        """Removes the given label from all components. """

        components = self.getComponents(label)
        removed    = []

        for comp in components:
            if self.removeComponent(label, comp, notify=False):
                removed.append((comp, label))

        if len(removed) > 0:
            self.notify(topic='removed', value=removed)
