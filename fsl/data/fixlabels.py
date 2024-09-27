#!/usr/bin/env python
#
# fixlabels.py - Functions for loading/saving FIX/ICA-AROMA label files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for loading/saving FIX/ICA-AROMA label files.

.. autosummary::
   :nosignatures:

   loadLabelFile
   saveLabelFile
   isNoisyComponent
   InvalidLabelFileError
"""


import itertools as it
import              math
import os.path   as op


def loadLabelFile(filename,
                  includeLabel=None,
                  excludeLabel=None,
                  returnIndices=False,
                  missingLabel='Unknown',
                  returnProbabilities=False):
    """Loads component labels from the specified file. The file is assumed
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
              following format is also accepted (this format is generated
              by ICA-AROMA)::

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

      - ``'True'`` if the component has been classified as *bad*, ``'False'``
        otherwise. This field is optional - if the last non-numeric
        comma-separated token on a line is not equal to ``True`` or ``False``
        (case-insensitive) , it is interpreted as a component label.

      - A value between 0 and 1, which gives the probability of the component
        being signal, as generated by an automatic classifier (e.g. FIX). This
        field is optional - it is output by some versions of FIX.

    The last line of the file contains the index (starting from 1) of all
    *bad* components, i.e. those components which are not classified as
    signal or unknown.

    :arg filename:            Name of the label file to load.

    :arg includeLabel:        If the file contains a single line containing a
                              list component indices, this label will be used
                              for the components in the list. Defaults to
                              ``'Unclassified noise'`` for FIX-like files, and
                              ``'Movement'`` for ICA-AROMA-like files.

    :arg excludeLabel:        If the file contains a single line containing
                              component indices, this label will be used for
                              the  components that are not in the list.
                              Defaults to ``'Signal'`` for FIX-like files, and
                              ``'Unknown'`` for ICA-AROMA-like files.

    :arg returnIndices:       Defaults to ``False``. If ``True``, a list
                              containing the noisy component numbers that were
                              listed in the file is returned.

    :arg missingLabel:        Label to use for any components which are not
                              present (only used for label files, not for noise
                              component files).

    :arg returnProbabilities: Defaults to ``False``. If ``True``, a list
                              containing the component classification
                              probabilities is returned. If the file does not
                              contain probabilities, every value in this list
                              will be nan.

    :returns: A tuple containing:

               - The path to the melodic directory as specified in the label
                 file

               - A list of lists, one list per component, with each list
                 containing the labels for the corresponding component.

               - If ``returnIndices is True``, a list of the noisy component
                 indices (starting from 1) that were specified in the file.

               - If ``returnProbabilities is True``, a list of the component
                 classification probabilities that were specified in the
                 file (all nan if they are not in the file).

    .. note:: Some label files generated by old versions of FIX/Melview do
              not contain a line for every component (unknown/unlabelled
              components may not be listed). For these files, and also for
              files which only contain a component list, there is no way of
              knowing how many components were in the data, so the returned
              list may contain fewer entries than there are components.
    """

    filename      = op.abspath(filename)
    probabilities = None
    signalLabels  = None

    with open(filename, 'rt') as f:
        lines = f.readlines()

    if len(lines) < 1:
        raise InvalidLabelFileError(f'{filename}: Invalid FIX classification '
                                    'file - not enough lines')

    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l != '']

    # If the file contains one or two lines, we
    # assume that it is just a comma-separated list
    # of noise components (possibly preceeded by
    # the MELODIC directory path)
    if len(lines) <= 2:
        melDir, noisyComps, allLabels, signalLabels = \
            _parseSingleLineLabelFile(lines, includeLabel, excludeLabel)
        probabilities = [math.nan] * len(allLabels)

    # Otherwise, we assume that it is a full label file.
    else:
        melDir, noisyComps, allLabels, probabilities = \
            _parseFullLabelFile(filename, lines, missingLabel)

    # There's no way to validate
    # the melodic directory path,
    # but let's try anyway.
    if melDir is not None:
        if len(melDir.split(',')) >= 3:
            raise InvalidLabelFileError(
                f'{filename}: First line does not look like '
                f'a MELODIC directory path: {melDir}')

        # The melodic directory path should
        # either be an absolute path, or
        # be specified relative to the location
        # of the label file.
        if not op.isabs(melDir):
            melDir = op.join(op.dirname(filename), melDir)

    # Validate the labels against
    # the noisy list - all components
    # in the noisy list should not
    # have 'signal' or 'unknown' labels
    for i, labels in enumerate(allLabels):

        comp  = i + 1
        noise = isNoisyComponent(labels, signalLabels)

        if noise and (comp not in noisyComps):
            raise InvalidLabelFileError(f'{filename}: Noisy component {comp} '
                                        f'has invalid labels: {labels}')

    for comp in noisyComps:

        i      = comp - 1
        labels = allLabels[i]
        noise  = isNoisyComponent(labels, signalLabels)

        if not noise:
            raise InvalidLabelFileError(f'{filename}: Noisy component {comp} '
                                        'is missing a noise label')

    retval = [melDir, allLabels]

    if returnIndices:       retval.append(noisyComps)
    if returnProbabilities: retval.append(probabilities)

    return tuple(retval)


def _parseSingleLineLabelFile(lines, includeLabel, excludeLabel):
    """Called by :func:`loadLabelFile`. Parses the contents of an
    ICA-AROMA-style label file which just contains a list of noise
    components (and possibly the MELODIC directory path), e.g.::

        filtered_func_data.ica
        [2, 5, 6, 7]
    """
    signalLabels = None
    noisyComps   = lines[-1]

    if len(lines) == 2: melDir = lines[0]
    else:               melDir = None

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
        if noisyComps[0] == '[': includeLabel = 'Unclassified noise'
        else:                    includeLabel = 'Movement'

    if excludeLabel is None:
        if noisyComps[0] == '[': excludeLabel = 'Signal'
        else:                    excludeLabel = 'Unknown'
    else:
        signalLabels = [excludeLabel]

    # Remove any leading/trailing
    # whitespace or brackets.
    noisyComps = noisyComps.strip(' []')
    noisyComps = [int(i) for i in noisyComps.split(',')]
    allLabels  = []

    for i in range(max(noisyComps)):
        if (i + 1) in noisyComps: allLabels.append([includeLabel])
        else:                     allLabels.append([excludeLabel])

    return melDir, noisyComps, allLabels, signalLabels


def _parseFullLabelFile(filename, lines, missingLabel):
    """Called by :func:`loadLabelFile`. Parses the contents of a
    FIX/Melview-style label file which contains labels for each component,
    e.g.:

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
    """
    melDir     = lines[0]
    noisyComps = lines[-1].strip(' []').split(',')
    noisyComps = [c      for c in noisyComps if c != '']
    noisyComps = [int(c) for c in noisyComps]

    # Parse the labels for every component.
    # Initially store as a {comp : ([labels], probability)} dict.
    allLabels = {}
    for i, compLine in enumerate(lines[1:-1]):

        tokens = compLine.split(',')
        tokens = [t.strip() for t in tokens]

        if len(tokens) < 3:
            raise InvalidLabelFileError(
                f'{filename}: Invalid FIX classification '
                f'file - line: {i + 1}: {compLine}')

        try:
            compIdx = int(tokens[0])
            if compIdx in allLabels:
                raise ValueError()

        except ValueError:
            raise InvalidLabelFileError(
                f'{filename}: Invalid FIX classification '
                f'file - line {i + 1}: {compLine}')

        tokens      = tokens[1:]
        probability = math.nan

        # last token could be classification probability
        if _isfloat(tokens[-1]):
            probability = float(tokens[-1])
            tokens      = tokens[:-1]

        # true/false is ignored as it is superfluous
        if tokens[-1].lower() in ('true', 'false'):
            tokens = tokens[:-1]

        allLabels[compIdx] = tokens, probability

    # Convert {comp : [labels]} into a list
    # of lists, filling in missing components
    allLabelsList = []
    probabilities = []
    for i in range(max(it.chain(allLabels.keys(), noisyComps))):
        labels, prob = allLabels.get(i + 1, ([missingLabel], math.nan))
        allLabelsList.append(labels)
        probabilities.append(prob)
    allLabels = allLabelsList

    return melDir, noisyComps, allLabels, probabilities


def _isfloat(s):
    """Returns True if the given string appears to contain a floating
    point number, False otherwise.
    """
    try:
        float(s)
        return True
    except Exception:
        return False


def saveLabelFile(allLabels,
                  filename,
                  dirname=None,
                  listBad=True,
                  signalLabels=None,
                  probabilities=None):
    """Saves the given classification labels to the specified file. The
    classifications are saved in the format described in the
    :func:`loadLabelFile` method.

    :arg allLabels:     A list of lists, one list for each component, where
                        each list contains the labels for the corresponding
                        component.

    :arg filename:      Name of the file to which the labels should be saved.

    :arg dirname:       If provided, is output as the first line of the file.
                        Intended to be a relative path to the MELODIC analysis
                        directory with which this label file is associated. If
                        not provided, a ``'.'`` is output as the first line.

    :arg listBad:       If ``True`` (the default), the last line of the file
                        will contain a comma separated list of components which
                        are deemed 'noisy' (see :func:`isNoisyComponent`).

    :arg signalLabels:  Labels which should be deemed 'signal' - see the
                        :func:`isNoisyComponent` function.

    :arg probabilities: Classification probabilities. If provided, the
                        probability for each component is saved to the file.
    """

    lines      = []
    noisyComps = []

    if probabilities is not None and len(probabilities) != len(allLabels):
        raise ValueError('len(probabilities) != len(allLabels)')

    # The first line - the melodic directory name
    if dirname is None:
        dirname = '.'

    lines.append(dirname)

    # A line for each component
    for i, labels in enumerate(allLabels):

        comp   = i + 1
        noise  = isNoisyComponent(labels, signalLabels)

        # Make sure there are no
        # commas in any label names
        labels = [l.replace(',', '_') for l in labels]
        tokens = [str(comp)] + labels + [str(noise)]

        if probabilities is not None:
            tokens.append(f'{probabilities[i]:0.6f}')

        lines.append(', '.join(tokens))

        if noise:
            noisyComps.append(comp)

    # A line listing the bad components
    if listBad:
        lines.append('[' + ', '.join([str(c) for c in noisyComps]) + ']')

    with open(filename, 'wt') as f:
        f.write('\n'.join(lines) + '\n')


def isNoisyComponent(labels, signalLabels=None):
    """Given a set of component labels, returns ``True`` if the component
    is ultimately classified as noise, ``False`` otherwise.

    :arg signalLabels: Labels which are deemed signal. If a component has
                       no labels in this list, it is deemed noise. Defaults
                       to ``['Signal', 'Unknown']``.
    """
    if signalLabels is None:
        signalLabels = ['signal', 'unknown']

    signalLabels = [l.lower() for l in signalLabels]
    labels       = [l.lower() for l in labels]
    noise        = not any([sl in labels for sl in signalLabels])

    return noise


class InvalidLabelFileError(Exception):
    """Exception raised by the :func:`loadLabelFile` function when an attempt
    is made to load an invalid label file.
    """
