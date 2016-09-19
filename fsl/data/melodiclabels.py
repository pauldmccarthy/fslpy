#!/usr/bin/env python
#
# melodiclabels.py - Loading/saving/managing melodic IC labels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MelodicClassification` class, which is
used to manage component classifications of a :class:`.MelodicImage`.

A handful of standalone IO functions are also contained in this module, for
saving/loading component classifications to/from file:

.. autosummary::
   :nosignatures:

   loadLabelFile
   saveLabelFile
"""


import logging
import os.path as op

import fsl.utils.notifier as notifier


log = logging.getLogger(__name__)


class MelodicClassification(notifier.Notifier):
    """The ``MelodicClassification`` class is a convenience class for managing
    a collection of component classification labels.


    .. autosummary::
       :nosignatures:

       hasLabel
       hasComponent
       getLabels
       getComponents
       addLabel
       addComponent
       removeLabel
       removeComponent
       clearLabels
       clearComponents

    The ``MelodicClassification`` class uses the :class:`.Notifier` interface
    to notify listeners about changes to the labels. Listeners can be 
    registered to be notified on the following topics:

      - ``added``:   A new label was added to a component.
      - ``removed``: A label was removed from a component.

    When either of these events occur, the value passed to registered
    listeners will contain a list of ``(component, label)``) tuples,
    which specify the labels that were added/removed.

    .. note:: All component labels are internally stored as lower case;
              their cased version (whatever is initially used) is accessible
              via the :meth:`getDisplayLabel` method.
    """

    
    def __init__(self, melimage):
        """Create a ``MelodicClassification`` instance.

        :arg melimage: A :class:`.MelodicImage` instance.
        """

        self.__melimage      = melimage
        self.__ncomps        = melimage.numComponents()
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
        self.__labels        = None
        self.__components    = None

        self.clear()


    def getDisplayLabel(self, label):
        """Returns the display name for the given label. """
        return self.__displayLabels.get(label.lower(), label)


    def clear(self):
        """Removes all labels from all components. """

        self.__components = {}
        self.__labels     = [[] for i in range(self.__ncomps)]
        

    def load(self, filename):
        """Loads component labels from the specified file. See the
        :func:`loadLabelFile` function.

        .. note:: This method adds to, but does not replace, any existing
                  component classifications stored by this
                  ``MelodicClassification``. Call the :meth:`clear` method,
                  before calling ``load``, if you want to discard any existing
                  classifications.
        """

        # Read the labels in
        _, allLabels = loadLabelFile(filename)

        # More labels in the file than there are in
        # melodic_IC - that doesn't make any sense.
        if len(allLabels) > self.__ncomps:
            raise InvalidLabelFileError(
                'The number of components in {} does '
                'not match the number of components in '
                '{}!'.format(filename, self.__melimage.dataSource))

        # Less labels in the file than there are in
        # the melodic_IC image - this is ok, as the
        # file may have only contained a list of
        # noisy components. We'll label the remaining
        # components as 'Unknown'.
        elif len(allLabels) < self.__ncomps:
            for i in range(len(allLabels), self.__ncomps):
                allLabels.append(['Unknown'])

        # Add the labels to this melclass object
        with self.skipAll(topic='added'):
            for i, labels in enumerate(allLabels):
                for label in labels:
                    self.addLabel(i, label)

    
    def save(self, filename):
        """Saves the component classifications stored by this
        ``MeloidicClassification`` to the specified file. See the
        :func:`saveMelodicLabelFile` function.
        """

        allLabels = []

        for c in range(self.__ncomps):
            labels = [self.getDisplayLabel(l) for l in self[c]]
            allLabels.append(labels)

        saveLabelFile(self.__melimage.getMelodicDir(),
                      allLabels,
                      filename)


    def getLabels(self, component):
        """Returns all labels of the specified component. """
        return list(self.__labels[component])


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
                     ``MelodicClassification`` class.

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

        self.__components[label]     = comps        
        self.__labels[    component] = labels

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
        self.addLabel(component, label)


    def removeComponent(self, label, component, notify=True):
        """Removes the given label from the given component. """
        self.removeLabel(component, label, notify)

    
    def clearComponents(self, label):
        """Removes the given label from all components. """
        
        components = self.getComponents(label)
        removed    = []

        for comp in components:
            if self.removeComponent(label, comp, notify=False):
                removed.append((comp, label))

        if len(removed) > 0:
            self.notify(topic='removed', value=removed)


def loadLabelFile(filename, includeLabel=None, excludeLabel=None):
    """Loads component labels from the specified file. The file is assuemd
    to be of the format generated by FIX, Melview or ICA-AROMA; such a file
    should have a structure resembling the following::

    
        filtered_func_data.ica
        1, Signal, False
        2, Unclassified Noise, True
        3, Unknown, False
        4, Signal, False
        5, Unclassified Noise, True
        6, Unclassified Noise, True
        7, Unclassified Noise, True
        8, Signal, False
        [2, 5, 6, 7]


    .. note:: This function will also parse files which only contain a
              component list, e.g.::

                  [2, 5, 6, 7]

              The square brackets may or may not be present, i.e. the
              following format is also accepted::

                  2, 5, 6, 7

              In this case, the returned melodic directory path will be
              ``None``.  The ``includeLabel`` and ``excludeLabel`` arguments
              allow you to control the labels assigned to included/excluded
              components.

    
    The first line of the file contains the name of the melodic directory.
    Then, one line is present for each component, containing the following,
    separated by commas:

      - The component index (starting from 1).
      - One or more labels for the component (multiple labels must be
        comma-separated).
      - ``'True'`` if the component has been classified as *bad*,
        ``'False'`` otherwise.

    
    The last line of the file contains the index (starting from 1) of all
    *bad* components, i.e. those components which are not classified as
    signal or unknown.

    :arg filename:     Name of the label file to load.

    :arg includeLabel: If the file contains a single line containing a list
                       component indices, this label will be used for the
                       components in the list. Defaults to 'Unclassified
                       noise' for FIX-like files, and 'Motion' for
                       ICA-AROMA-like files.
    
    :arg excludeLabel: If the file contains a single line containing component
                       indices, this label will be used for the components
                       that are not in the list.  Defaults to 'Signal' for
                       FIX-like files, and 'Unknown' for ICA-AROMA-like files.

    :returns: A tuple containing the path to the melodic directory
              as specified in the label file, and a list of lists, one
              list per component, with each list containing the labels for
              the corresponding component.
    """

    filename = op.abspath(filename)

    with open(filename, 'rt') as f:
        lines = f.readlines()

    if len(lines) < 1:
        raise InvalidLabelFileError('Invalid FIX classification '
                                    'file - not enough lines')

    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l != '']

    # If the file contains a single
    # line, we assume that it is just
    # a comma-separated list of noise
    # components.
    if len(lines) == 1:

        line = lines[0]
            
        # if the list is contained in
        # square brackets, we assume
        # that it is a FIX output file,
        # where included components have
        # been classified as noise, and
        # excluded components as signal.
        # 
        # Otherwise we assume that it
        # is an AROMA file, where
        # included components have
        # been classified as being due
        # to motion, and excluded
        # components unclassified.
        if includeLabel is None:
            if line[0] == '[': includeLabel = 'Unclassified noise'
            else:              includeLabel = 'Movement'
                
        if excludeLabel is None:
            if line[0] == '[': excludeLabel = 'Signal'
            else:              excludeLabel = 'Unknown'

        # Remove any leading/trailing
        # whitespace or brackets.
        line = lines[0].strip(' []')

        melDir     = None 
        noisyComps = [int(i) for i in line.split(',')]
        allLabels  = []

        for i in range(max(noisyComps)):
            if (i + 1) in noisyComps: allLabels.append([includeLabel])
            else:                     allLabels.append([excludeLabel])

    # Otherwise, we assume that
    # it is a full label file.
    else:

        melDir     = lines[0]
        noisyComps = map(int, lines[-1].strip(' []').split(', '))

        # The melodic directory path should
        # either be an absolute path, or
        # be specified relative to the location
        # of the label file.
        if not op.isabs(melDir):
            melDir = op.join(op.dirname(filename), melDir)
        
        # Parse the labels for every component
        # We do not add the labels as we go
        # because, if something is wrong with
        # the file contents, we don't want this
        # MelodicClassification instance to be
        # modified. So we'll assign the labels
        # afterwards.
        allLabels = []
        for i, compLine in enumerate(lines[1:-1]):

            tokens = compLine.split(',')
            tokens = [t.strip() for t in tokens]

            if len(tokens) < 3:
                raise InvalidLabelFileError(
                    'Invalid FIX classification file - '
                    'line {}: {}'.format(i + 1, compLine))

            try:
                compIdx = int(tokens[0])
                
            except:
                raise InvalidLabelFileError(
                    'Invalid FIX classification file - '
                    'line {}: {}'.format(i + 1, compLine))
                    
            compLabels = tokens[1:-1]

            if compIdx != i + 1:
                raise InvalidLabelFileError(
                    'Invalid FIX classification file - wrong component '
                    'number at line {}: {}'.format(i + 1, compLine))

            allLabels.append(compLabels)

    # Validate the labels against
    # the noisy list - all components
    # in the noisy list should not
    # have 'signal' or 'unknown' labels
    for i, labels in enumerate(allLabels):

        comp  = i + 1
        noise = isNoisyComponent(labels)

        if noise and (comp not in noisyComps):
            raise InvalidLabelFileError('Noisy component {} has invalid '
                                        'labels: {}'.format(comp, labels))

    for comp in noisyComps:
        
        i      = comp - 1
        labels = allLabels[i]
        noise  = isNoisyComponent(labels)
        
        if not noise:
            raise InvalidLabelFileError('Noisy component {} is missing '
                                        'a noise label'.format(comp)) 

    return melDir, allLabels


def saveLabelFile(melDir, allLabels, filename):
    """Saves the component classifications stored by this
    ``MeloidicClassification`` to the specified file. The classifications
    are saved in the format described in the :meth:`loadLabelFile` method.
    """
    
    lines      = []
    noisyComps = []

    # The first line - the melodic directory name
    lines.append(op.abspath(melDir))

    # A line for each component
    for i, labels in enumerate(allLabels):

        comp   = i + 1
        noise  = isNoisyComponent(labels)

        # Make sure there are no
        # commas in any label names
        labels = [l.replace(',', '_') for l in labels]
        tokens = [str(comp)] + labels + [str(noise)]

        lines.append(', '.join(tokens))

        if noise:
            noisyComps.append(comp)

    # A line listing the bad components
    lines.append('[' + ', '.join([str(c) for c in noisyComps]) + ']')

    with open(filename, 'wt') as f:
        f.write('\n'.join(lines) + '\n')


def isNoisyComponent(labels):
    """Given a set of component labels, returns ``True`` if the component
    is ultimately classified as noise, ``False`` otherwise.
    """

    labels = [l.lower() for l in labels]
    noise  = ('signal' not in labels) and ('unknown' not in labels)

    return noise
    

class InvalidLabelFileError(Exception):
    """Exception raised by the :meth:`MelodicClassification.load` method and
    the :func:`loadMelodicLabelFile` function when an attempt is made to load
    an invalid label file.
    """
    pass
