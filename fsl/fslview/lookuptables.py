#!/usr/bin/env python
#
# lookuptables.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


class LookupTable(object):

    
    def __init__(self, lutName):
        self.__lutName = lutName
        self.__names   = {}
        self.__colours = {}


    def __len__(self):
        return len(self.__names.keys())

        
    def lutName(self):
        return self.__lutName


    def values(self):
        return sorted(self.__names.keys())


    def names(self):
        return [self.__names[v] for v in self.values()]

    
    def colours(self):
        return [self.__colours[v] for v in self.values()]

    
    def name(self, value):
        return self.__names[value]

        
    def colour(self, value):
        return self.__colours[value]


    def set(self, value, name, colour):

        # At the moment, we are restricting
        # lookup tables to be unsigned 16 bit.
        # See gl/textures/lookuptabletexture.py
        if not isinstance(value, (int, long)) or \
           value < 0 or value > 65535:
            raise ValueError('Lookup table values must be '
                             '16 bit unsigned integers.')
          
        self.__names[  value] = name
        self.__colours[value] = colour


    def load(self, lutFile):
        
        with open(lutFile, 'rt') as f:
            lines = f.readlines()

            for line in lines:
                tkns = line.split()

                label = int(     tkns[0])
                r     = float(   tkns[1])
                g     = float(   tkns[2])
                b     = float(   tkns[3])
                lName = ' '.join(tkns[4:])

                self.set(label, lName, (r, g, b))

        return self


import os.path as op

all_luts = []
dirname  = op.join(op.dirname(__file__), 'luts')

all_luts.append(
    LookupTable('Harvard-Oxford').load(
        op.join(dirname, 'harvard-oxford-cortical.txt')))
