#!/usr/bin/env python
#
# featDemo.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys

import Tkinter as tk
import            ttk
import tkprop  as tkp

# Currently only supports first-level analysis/full analysis
class FeatOptions(tkp.HasProperties):

    brainBackgroundThreshold = tkp.Percentage(default=10)

    # Design efficiency options
    noiseLevel         = tkp.Percentage(default=0.66)
    temporalSmoothness = tkp.Double(default=0.34, minval=-1.0, maxval=1.0)
    zThreshold         = tkp.Double(default=5.3, minval=0.0)
    inputData          = tkp.List(minlen=1, listType=tkp.FilePath(exists=True), default=['',''])
    outputDirectory    = tkp.FilePath(isFile=False)


class FeatFrame(tk.Frame):
    
    def __init__(self, parent, featOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        self.tkpFrame = tkp.buildGUI(self, featOpts)
        self.tkpFrame.pack(fill=tk.BOTH, expand=1)

        self.buttonFrame = tk.Frame(self)
        self.runButton   = ttk.Button(self.buttonFrame,
                                      text='Run FEAT',
                                      command=parent.destroy)
        self.quitButton  = ttk.Button(self.buttonFrame,
                                      text='Quit',
                                      command=parent.destroy)

        self.runButton  .pack(fill=tk.X, expand=1, side=tk.LEFT) 
        self.quitButton .pack(fill=tk.X, expand=1, side=tk.RIGHT)
        self.buttonFrame.pack(fill=tk.X) 


if __name__ == '__main__':

    app  = tk.Tk()
    fopts = FeatOptions()

    frame = FeatFrame(app, fopts)

    print('Before')
    print(fopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(fopts)
