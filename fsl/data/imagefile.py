#!/usr/bin/env python
#
# imagefile.py - Convenience functions for adding/stripping supported
# file extensions to/from image file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

# The file extensions which we understand. This list is used
# as the default if if the allowedExts parameter is not passed
# to any of the functions in this module.
_allowedExts = ['.nii', '.img', '.hdr', '.nii.gz', '.img.gz']

_descriptions = ['NIFTI1 images',
                 'ANALYZE75 images',
                 'NIFTI1/ANALYZE75 headers',
                 'Compressed NIFTI1 images',
                 'Compressed ANALYZE75/NIFTI1 images']


# The default file extension (TODO read this from $FSLOUTPUTTYPE)
_defaultExt  = '.nii.gz'


def wildcard(allowedExts=None):
    """
    """
    
    if allowedExts is None:
        allowedExts  = _allowedExts
        descs        = _descriptions
    else:
        descs        = allowedExts


    exts = ['*{}'.format(ext) for ext in allowedExts]

    wcParts = ['|'.join((desc,ext)) for (desc,ext) in zip(descs, exts)]

    print  '|'.join(wcParts)
    return '|'.join(wcParts)
    


def isSupported(filename, allowedExts=None):
    """
    Returns True if the given file has a supported extension, False
    otherwise.
    """

    if allowedExts is None: allowedExts = _allowedExts

    return any(map(lambda ext: filename.endswith(ext, allowedExts)))


def removeExt(filename, allowedExts=None):
    """
    Removes the extension from the given file name. Raises a ValueError
    if the file has an unsupported extension.
    """

    if allowedExts is None: allowedExts = _allowedExts

    # figure out the extension of the given file
    extMatches = map(lambda ext: filename.endswith(ext), allowedExts)

    # the file does not have a supported extension
    if not any(extMatches):
        raise ValueError('Unsupported file type')

    # figure out the length of the matched extension
    extIdx = extMatches.index(True)
    extLen = len(allowedExts[extIdx])

    # and trim it from the file name
    return filename[:-extLen]

    

def addExt(
        prefix,
        mustExist=False,
        allowedExts=None,
        defaultExt=None):
    """
    Adds a file extension to the given file prefix. If mustExist is False
    (the default), and the file does not already have a supported
    extension, the default extension is appended and the new file name
    returned. If the prefix already has a supported extension, it is
    returned unchanged.

    If mustExist is True, the function checks to see if any files exist
    that have the given prefix, and a supported file extension.  A
    ValueError is raised if:

       - No files exist with the given prefix and a supported extension.
       - More than one file exists with the given prefix, and a supported
         extension.

    Otherwise the full file name is returned.
    """

    if allowedExts is None: allowedExts = _allowedExts
    if defaultExt  is None: defaultExt  = _defaultExt

    if not mustExist:

        # the provided file name already
        # ends with a supported extension 
        if any(map(lambda ext: prefix.endswith(ext), allowedExts)):
            return prefix

        return prefix + defaultExt

    # If the provided prefix already ends with a
    # supported extension , check to see that it exists
    if any(map(lambda ext: prefix.endswith(ext), allowedExts)):
        extended = [prefix]
        
    # Otherwise, make a bunch of file names, one per
    # supported extension, and test to see if exactly
    # one of them exists.
    else:
        extended = map(lambda ext: prefix + ext, allowedExts)

    exists = map(op.isfile, extended)

    # Could not find any supported file
    # with the specified prefix
    if not any(exists):
        raise ValueError(
            'Could not find a supported file with prefix {}'.format(prefix))

    # Ambiguity! More than one supported
    # file with the specified prefix
    if len(filter(bool, exists)) > 1:
        raise ValueError('More than one file with prefix {}'.format(prefix))

    # Return the full file name of the
    # supported file that was found
    extIdx = exists.index(True)
    return extended[extIdx]
