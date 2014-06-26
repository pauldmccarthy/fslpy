#!/usr/bin/env python
#
# notebook.py - Re-implementation of the wx.Notebook widget
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

"""Re-implementation of the :class:`wx.Notebook` widget.

This :class:`Notebook` implementation supports page enabling/disabling, and
page visibility.

I didn't want it to come to this, but both the
:class:`wx.lib.agw.aui.AuiNotebook` and :class:`wx.lib.agw.flatnotebook`
are too difficult to use. The ``AuiNotebook`` requires me to use an
``AuiManager`` for layout, and the ``flatnotebook`` has layout/fitting
issues.
"""


import wx


class Notebook(wx.Panel):
    """A :class:`wx.Panel` which provides :class:`wx.Notebook`-like
    functionality. Manages the display of multiple child windows. A
    row of buttons along the top allows the user to select which
    child window to display.
    """

    def __init__(self, parent):
        """Create a :class:`Notebook` object.

        :param parent: The :mod:`wx` parent object.
        """
        
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        
        self.buttonPanel = wx.Panel(self)

        self.sizer       = wx.BoxSizer(wx.VERTICAL)
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.            SetSizer(self.sizer)
        self.buttonPanel.SetSizer(self.buttonSizer)

        self.dividerLine = wx.StaticLine(self, style=wx.LI_HORIZONTAL)

        # a row of buttons along the top
        self.sizer.Add(
            self.buttonPanel,
            border=5,
            flag=wx.EXPAND | wx.ALIGN_CENTER | wx.TOP | wx.RIGHT | wx.LEFT)

        # a horizontal line separating the buttons from the pages
        self.sizer.Add(
            self.dividerLine,
            border=5,
            flag=wx.EXPAND | wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT)

        # a vertical line at the start of the button row
        self.buttonSizer.Insert(
            0,
            wx.StaticLine(self.buttonPanel, style=wx.VERTICAL),
            border=3,
            flag=wx.EXPAND | wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT | wx.TOP)

        self._pages    = []
        self._buttons  = []
        self._selected = None


    def DoGetBestClientSize(self):
        """Calculate and return the best (minimum) size for the
        :class:`Notebook` widget. The returned size is the minimum
        size of the largest page, plus the size of the button panel.
        """

        buttonSize = self.buttonPanel.GetBestSize()
        pageSizes  = map(lambda p: p.GetBestSize(), self._pages)

        buttonWidth  = buttonSize.GetWidth()
        buttonHeight = buttonSize.GetHeight()

        divLineHeight = self.dividerLine.GetBestSize().GetHeight()

        pageWidths  = map(lambda ps: ps.GetWidth(),  pageSizes)
        pageHeights = map(lambda ps: ps.GetHeight(), pageSizes)
        
        myWidth  = max([buttonWidth] + pageWidths)                 + 20
        myHeight = max(pageHeights) + buttonHeight + divLineHeight + 20
        
        return wx.Size(myWidth, myHeight)

        
    def FindPage(self, page):
        """Returns the index of the given page, or :data:`wx.NOT_FOUND`
        if the page is not in this notebook.
        """
        try:    return self._pages.index(page)
        except: return wx.NOT_FOUND


    def InsertPage(self, index, page, text):
        """Inserts the given page into the notebook at the specified
        index. A button for the page is also added to the button row,
        with the specified text.
        """

        if (index > len(self._pages)) or (index < 0):
            raise IndexError('Index out of range: {}'.format(index))

        # index * 2 because we add a vertical
        # line after every button (and + 1 for
        # the line at the start of the button row)
        button    = wx.StaticText(self.buttonPanel, label=text)
        buttonIdx = index * 2 + 1

        self._pages.  insert(index, page)
        self._buttons.insert(index, button)

        # index + 2 to account for the button panel and
        # the horizontal divider line (see __init__)
        self.sizer.Insert(
            index + 2, page, border=5, flag=wx.EXPAND | wx.ALL, proportion=1)

        self.buttonSizer.Insert(
            buttonIdx,
            button,
            flag=wx.ALIGN_CENTER)

        # A vertical line at the end of every button
        self.buttonSizer.Insert(
            buttonIdx + 1,
            wx.StaticLine(self.buttonPanel, style=wx.VERTICAL),
            border=3,
            flag=wx.EXPAND | wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT | wx.TOP)

        # When the button is pushed, show the page
        # (unless the button has been disabled)
        def _showPage(ev):
            if not button.IsEnabled(): return
            self.SetSelection(self.FindPage(page))
            
        button.Bind(wx.EVT_LEFT_DOWN, _showPage)

        page.Layout()
        page.Fit()
        
        self.buttonPanel.Layout()
        self.buttonPanel.Fit()

        self.SetMinClientSize(self.DoGetBestClientSize())

        self.Layout()
        self.Fit()

        
    def AddPage(self, page, text):
        """Adds the given page (and a corresponding button
        with the given text) to the end of the notebook.
        """
        self.InsertPage(len(self._pages), page, text)


    def RemovePage(self, index):
        """Removes the page at the specified
        index, but does not destroy it.
        """

        if (index >= len(self._pages)) or (index < 0):
            raise IndexError('Index out of range: {}'.format(index)) 

        buttonIdx = index * 2 + 1
        pageIdx   = index + 2
        
        self._buttons.pop(index)
        self._pages  .pop(index)

        # Destroy the button for this page (and the
        # vertical line that comes after the button)
        self.buttonSizer.Remove(buttonIdx)
        self.buttonSizer.Remove(buttonIdx + 1)

        # Remove the page but do not destroy it
        self.pagePanel  .Detach(pageIdx)

        
    def DeletePage(self, index):
        """Removes the page at the specified index,
        and (attempts to) destroy it.
        """ 
        page = self._pages[index]
        self.RemovePage(index)
        page.Destroy()


    def GetSelection(self):
        """Returns the index of the currently selected page."""
        return self._selected


    def SetSelection(self, index):
        """Sets the displayed page to the one at the specified index."""

        if index < 0 or index >= len(self._pages):
            raise IndexError('Index out of range: {}'.format(index))

        self._selected = index

        for i in range(len(self._pages)):
            
            page     = self._pages[  i]
            button   = self._buttons[i]
            showThis = i == self._selected

            if showThis:
                button.SetBackgroundColour('#ffffff')
                page.Show()
            else:
                button.SetBackgroundColour(None)
                page.Hide()
                
        button.Layout()
        self.buttonPanel.Layout()
        self.Layout()
        self.Refresh()

        
    def AdvanceSelection(self, forward=True):
        """Selects the next (or previous, if ``forward``
        is ``False``) enabled page.
        """

        if forward: offset =  1
        else:       offset = -1

        newSelection = (self.GetSelection() + offset) % len(self._pages)

        while newSelection != self._selected:

            if self._buttons[newSelection].IsEnabled():
                break

            newSelection = (self._selected + offset) % len(self._pages)

        self.SetSelection(newSelection)


    def EnablePage(self, index):
        """Enables the page at the specified index."""
        self._buttons[index].Enable()

        
    def DisablePage(self, index):
        """Disables the page at the specified index."""
        self._buttons[index].Disable()
        
        if self.GetSelection() == index:
            self.AdvanceSelection()

        self.Refresh()

            
    def ShowPage(self, index):
        """Shows the page at the specified index."""
        self.EnablePage(index)
        self._buttons[index].Show()
        self._pages[  index].Show()
        self.buttonPanel.Layout()
        self.Refresh()

        
    def HidePage(self, index):
        """Hides the page at the specified index."""

        self._buttons[index].Hide()
        self._pages[  index].Hide()

        # we disable the page as well as hiding it,, as the
        # AdvanceSelection method, and button handlers, use
        # button.IsEnabled to determine whether a page is
        # active or not. 
        self.DisablePage(index)

        self.buttonPanel.Layout()
        self.buttonPanel.Refresh()
