.. _quick-start:

Quick start
===========


.. _quick-start-the-interface:

The interface
-------------


When you first start *FSLeyes*, you will be presented with something that
looks like this:


.. image:: images/quick_start_interface_1.png
   :align: center


This is slightly boring, so let's load an image. Select the *File/Add overlay
from file* menu option, and choose a `.nii.gz` image to load.
          
Now things are a bit more interesting:


.. image:: images/quick_start_interface_2.png
   :align: center


Let's take a closer look at the components of the *FSLeyes* interface...


.. image:: images/quick_start_interface_overview.png
   :align: center


The view
^^^^^^^^


.. sidebar:: What is an *overlay*?
             :subtitle: And why aren't they just called *images* instead?

             An :ref:`overlay <overlays>` is an image, or other data file,
             that you have loaded into *FSLeyes*.  While *FSLeyes* is first
             and foremost a NIFTI image viewer, the term *overlay* is used,
             instead of *image*, because *FSLeyes* supports other
             non-volumetric data types, and will hopefully support more in the
             future.


The view is where your overlays are displayed. By default, an *orthographic*
view is shown; you can also select a *lightbox* view, or some plot views, from
the *View* menu.


Let's stick with the orthographic view for now. It displays your overlay on
three *canvases*, along the three primary axes. For a NIFTI image which is
oriented acording to the MNI152 template, these canvases will correspond to
the sagittal, coronal, and axial planes.


.. |command_key| unicode:: U+2318


You can interact with an orthographic view in a number of ways:


 - Click, or click and drag, to change the current location.
 - Right click and drag to draw a zoom rectangle. When you release the mouse,
   the view will zoom in to that rectangle.
 - Hover the mouse over one canvas, and use your mouse wheel to change the
   current location along the depth axis for that canvas.
 - Hold down the |command_key| (under OSX) or Control key (under Linux), and
   use your mouse wheel to zoom in and out of a canvas.
 - When a canvas is zoomed in, you can middle-click and drag to pan around.
 - Hold down the shift key, then click and drag the mouse to adjust the
   brightness and contrast of the currently selected overlay. Moving the
   mouse vertically will adjust the contrast, and horizontally will adjust
   the brightness.


The overlay list
^^^^^^^^^^^^^^^^


.. |up_arrow|   unicode:: U+25B2
.. |down_arrow| unicode:: U+25BC

           
The :ref:`overlay list <controls-overlay-list>` displays a list of all
overlays that you have loaded. With this list you can:


     - Change the currently selected overlay, by clicking on the overlay
       name.
     - Add/remove overlays with the + and - buttons
     - Change the overlay display order with the |up_arrow| and |down_arrow|
       buttons
     - Show/hide each overlay with the eye button, or by double clicking on
       the overlay name
     - Link overlay display properties with the chainlink button


The toolbars
^^^^^^^^^^^^


The :ref:`overlay toolbar <controls-overlay-toolbar>` allows you to adjust
display properties of the currently selected overlay. Pushing the gear button
will open a dialog containing all of the overlay display settings. Pushing the
information button opens a dialog containing information about the overlay.


The :ref:`ortho toolbar <controls-ortho-toolbar>` allows you to adjust the
layout of the ortho view. For example, you can toggle each of the canvases on
and off, and switch between vertical, horizontal, or grid layouts. Pushing the
spanner icon will open a dialog containing all of the ortho view settings.


The location panel
^^^^^^^^^^^^^^^^^^


The :ref:`location panel <controls-location-panel>` shows the current display
location, in terms of the currently selected overlay. It also shows the
overlay data value at the current location, for every loaded overlay.
   

.. _quick-start-how-do-i:

How do I ...
------------


Load an overlay?
^^^^^^^^^^^^^^^^


You can load an overlay by doing one of the following:

1. The *File/Add overlay from file* menu option allows you to choose a file to
   load (e.g. a `.nii`, `.nii.gz`, or `.vtk` file).

2. The *File/Add overlay from directory* menu option allows you to choose a
   directory to load (e.g. a `.feat`, `.ica`, or `dtifit` directory).

3. The *File/Add standard* menu option allows you to choose a file from the
   `$FSLDIR/data/standard/` directory to load.

4. The + button on the overlay list allows you to choose a file to load.


.. note:: The *File/Add standard* menu option will be disabled if your FSL
          environment is not configured correctly.


Open another ortho/lightbox view?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The *View* menu allows you to open another view. You can open as many views as
you like.


Open/close control panels/toolbars?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The *Settings* menu contains a sub-menu for every open view, which allows you
to toggle the control panels and toolbars for that view, and perform a few
other tasks. For exmaple, if you want to add an :ref:`edit toolbar
<controls-edit-toolbar>`, you would select the *Settings/Ortho view 1/Edit
toolbar* menu option.


Show/hide the cursor/anatomical labels?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Click the spanner button, on the ortho toolbar, to bring up the ortho view
settings panel.



Take a screenshot?
^^^^^^^^^^^^^^^^^^


Click the camera icon on the ortho toolbar, or select the *Settings/Ortho view
1/Take screenshot* menu item.



Link/unlink the display properties across multiple views?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


If you have more than one view open (e.g. an ortho view and a lightbox view),
and you want the overlay display settings to be the same across all views,
open the view settings panel for each view (via the toolbar spanner button, or
the *Settings/<view name>/View settings panel* menu option), and make sure
that the *Sync overlay display settings* box is checked or unchecked.


Classify ICA components?
^^^^^^^^^^^^^^^^^^^^^^^^


Load your `.ica` directory (or the `.ica/melodic_IC` image file), then open
the melodic perspective (the *View/Perspectives/Melodic mode* menu
option). Use the :ref:`melodic classification panel
<controls-melodic-ic-classification>` to label components, and load/save
label files.


Save the current view/control panel layout?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


When you close *FSLeyes*, the current layout is saved to a configuration
file. This layout is then restored the next time you open *FSLeyes*.  You can
also save a layout at any time by defining a new :ref:`perspective
<perspectives>`: Choose the *View/Perspectives/Save current perspective* menu
item, and give your layout a name. You can then restore it at any time by
selecting it in the *View/Perspectives* menu.
