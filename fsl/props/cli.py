#!/usr/bin/env python
#
# cli.py - Generate command line arguments for a HasPropertyies object.
#
# This module provides two functions:
#  - addParserArguments: Given an argparser.ArgumentParser and a
#                        HasProperties class (or instance), adds arguments
#                        to the parser for each PropertyBase attribute of
#                        the HasProperties class.
#
#  - applyArguments:     Given a HasProperties instance and an
#                        argparse.Namespace object assumed to have been
#                        created by the parser mentioned above, sets the
#                        property values of the HasProperties instance from
#                        the values stored in the Namespace object.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import sys
import argparse

import matplotlib.cm as mplcm

import properties as props

# The functions below add an argument to an ArgumentParser for a
# specific property type.

def _String(parser, propCls, propName, propHelp, shortArg, longArg):
    """
    Adds an argument to the given parser for the given String property.
    
    Parameters:
    
      - parser:   An argparse.ArgumentParser instance.
    
      - propCls:  A HasProperties class.
    
      - propName: Name of the property.
    
      - propHelp: Custom help text for the property.
    
      - shortArg: String to use as the short argument.
    
      - longArg:  String to use as the long argument.
    """
    parser.add_argument(shortArg, longArg, help=propHelp) 

    
def _Boolean(parser, propCls, propName, propHelp, shortArg, longArg):
    parser.add_argument(shortArg,
                        longArg,
                        help=propHelp,
                        action='store_true')

    
def _Int(parser, propCls, propName, propHelp, shortArg, longArg):
    parser.add_argument(shortArg,
                        longArg,
                        help=propHelp,
                        metavar='INT',
                        type=int)

    
def _Real(parser, propCls, propName, propHelp, shortArg, longArg):
    parser.add_argument(shortArg,
                        longArg,
                        help=propHelp,
                        metavar='REAL',
                        type=float)


def _Bounds(parser, propCls, propName, propHelp, shortArg, longArg):
    ndims = getattr(propCls, propName)._ndims
    parser.add_argument(shortArg,
                        longArg,
                        help=propHelp,
                        metavar='N',
                        type=float,
                        nargs=2 * ndims)

    
def _ColourMap(parser, propCls, propName, propHelp, shortArg, longArg):

    # Attempt to retrieve a matplotlib.cm.ColourMap
    # instance given its name
    def parse(cmapName):
        try:
            return mplcm.get_cmap(cmapName)
        except:
            raise argparse.ArgumentTypeError(
                'Unknown colour map: {}'.format(cmapName))
    
    parser.add_argument(shortArg,
                        longArg,
                        help=propHelp,
                        type=parse,
                        metavar='CMAP',
                        action='store')



def applyArguments(hasProps, arguments):
    """
    Given a HasProperties instance and an argparser.Namespace instance,
    sets the property values of the HasProperties instance from the
    values stored in the Namespace object.
    """
    
    propNames, propObjs = hasProps.getAllProperties()
    for propName, propObj in zip(propNames, propObjs):
        
        val = getattr(arguments, propName, None)

        if val is None: continue
            
        setattr(hasProps, propName, getattr(arguments, propName))

    
def _getShortArgs(propCls, propNames, exclude=''):
    """
    Generates unique single-letter argument names for each
    of the names in the given list of property names. Any
    letters in the exclude string are not used as short
    arguments.
    """

    letters   = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    shortArgs = {}

    for propName in propNames:

        # if '_shortArgs' is present on the hasProps
        # object, and there is an entry for the
        # current property, use that entry.
        if hasattr(propCls, '_shortArgs'):
            if propName in propCls._shortArgs:

                # throw an error if that entry
                # has already been used, or
                # should be excluded
                if propCls._shortArgs[propName] in shortArgs.values() or \
                   propCls._shortArgs[propName] in exclude:
                    raise RuntimeError(
                        'Duplicate or excluded short argument for property '
                        '{}.{}: {}'.format(
                            propCls.__name__,
                            propName,
                            propCls._shortArgs[propName]))
                                       
                shortArgs[propName] = propCls._shortArgs[propName]
                continue

        # use the first unique letter in the
        # property name or, if that doesn't
        # work, in the alphabet
        for c in propName + letters:
            
            if (c not in shortArgs.values()) and (c not in exclude):
                shortArgs[propName] = c
                break

    if any([name not in shortArgs for name in propNames]):
        raise RuntimeError('Could not generate default short arguments '
                           'for HasProperties object {} - please provide '
                           'custom short arguments via a _shortArgs '
                           'attribute'.format(propCls.__name__))
        
    return shortArgs

    
def addParserArguments(
        propCls,
        parser,
        cliProps=None,
        shortArgs=None,
        longArgs=None,
        propHelp=None,
        exclude=''):
    """
    Adds arguments to the given argparse.ArgumentParser, providing a command
    line interface to the properties of the given HasProperties object.
    Parameters:

      - propCls:   A props.HasProperties class. An instance may alternately
                   be passed.
    
      - parser:    An argparse.ArgumentParser to add arguments to.
    
      - cliProps:  List containing the names of properties to add arguments
                   for. If None, and an attribute called '_cliProps' is
                   present on the hasProps object, the value of that attribute
                   is used. Otherwise an argument is added for all properties.
    
      - shortArgs: Dict containing {propName: shortArg} mappings, to be used
                   as the short (typically single letter) argument flag for
                   each property. If None, and an attribute called '_shortArgs'
                   is present on the hasProps object, the value of that
                   attribute is used. Otherwise, short arguments are
                   automatically generated for each property.
    
      - longArgs:  Dict containing {propName: longArg} mappings, to be used
                   as the long argument flag for each property. If None, and
                   an attribute called '_longArgs' is present on the hasProps
                   object, the value of that attribute is used. Otherwise,
                   the name of each property is used as its long argument.
    
      - propHelp:  Dict containing {propName: helpString] mappings, to be used
                   as the help text for each property. If None, and an
                   attribute called '_propHelp' is present on the hasProps
                   object, the value of that attribute is used. Otherwise,
                   no help string is used.
    
      - exclude:   String containing letters which should not be used as short
                   arguments.
    """

    if isinstance(propCls, props.HasProperties):
        propCls = propCls.__class__

    if cliProps is None:
        if hasattr(propCls, '_cliProps'):
            cliProps = propCls._cliProps
        else:
            cliProps = propCls.getAllProperties()[0]

    if propHelp is None:
        if hasattr(propCls, '_help'):
            propHelp = propCls._help
        else:
            propHelp = {}

    if longArgs is None:
        if hasattr(propCls, '_longArgs'): longArgs = propCls._longArgs
        else:                             longArgs = {}

    shortArgs = _getShortArgs(propCls, cliProps)

    for propName in cliProps:

        propObj    = propCls.getProp(propName)
        propType   = propObj.__class__.__name__
        parserFunc = getattr(
            sys.modules[__name__],
            '_{}'.format(propType), None)

        if parserFunc is None:
            log.warn('No CLI parser function for property {} '
                     '(type {})'.format(propName, propType))
            continue

        shortArg =  '-{}'.format(shortArgs[propName])
        longArg  = '--{}'.format(longArgs.get(propName, propName))

        parserFunc(parser,
                   propCls,
                   propName,
                   propHelp.get(propName, None),
                   shortArg,
                   longArg)
