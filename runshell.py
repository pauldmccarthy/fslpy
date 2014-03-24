#!/usr/bin/env python
#
# runshell.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import subprocess as subp


import threading as thread
import Queue     as queue

import Tkinter as tk
import            ttk


def run(cmd, tkRoot, modal=True):
    """
    Runs the given command, displaying the output in a Tkinter window.
    """

    proc   = None
    window = tk.Toplevel()
    frame  = ttk.Frame(window)

    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(   0, weight=1)

    text    = tk.Text(frame, wrap="none")
    vScroll = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=text.yview)
    hScroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text.xview)

    def kill():
        try:    proc.terminate()
        except: pass

    btnFrame    = ttk.Frame(frame)
    killButton  = ttk.Button(btnFrame, text="Kill process", command=kill)
    closeButton = ttk.Button(btnFrame, text="Close window",
                             command=window.destroy())

    text    .grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    hScroll .grid(row=1, column=0, sticky=tk.E+tk.W)
    vScroll .grid(row=0, column=1, sticky=tk.N+tk.S)
    btnFrame.grid(row=2, column=0, sticky=tk.E+tk.W, columnspan=2)

    btnFrame.columnconfigure(0, weight=1)
    btnFrame.columnconfigure(1, weight=1)
    killButton .grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    closeButton.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)

    text.insert('1.0', ' '.join(cmd) + '\n\n')

    # Run the command
    proc = subp.Popen(cmd, stdout=subp.PIPE, bufsize=1, stderr=subp.STDOUT)
    outq = queue.Queue()

    
    def writeToDialog():
        """
        Reads a string from the output queue,
        and appends it to the tk Text widget.
        """
        
        try:                output = outq.get_nowait()
        except queue.Empty: output = None

        if output is not None: text.insert('end', output)

        
    def pollOutput():
        """
        Reads the output of the process, line by line, and
        writes it (asynchronously) to the tk Text widget.
        """
        
        for line in proc.stdout:
            print line,
            outq.put(line)
            tkRoot.after_idle(writeToDialog)
            
        outq.put('\nProcess finished\n')
        tkRoot.after_idle(writeToDialog)
        killButton.configure(state='disabled')

        
    # poll the process output on a separate thread
    outputThread        = thread.Thread(target=pollOutput)
    outputThread.daemon = True
    outputThread.start()

    # make this window modal
    if modal:
        window.transient(tkRoot)
        window.grab_set()
        tkRoot.wait_window(window) 


    


    
