Inkscape clean-path
===================

An inkscape extension to work around typical path issues.
Processing a complex SVG file for use with machines like LaserCutters,
Embroidery, VinylCutter, or EggBots may fail with obscure error messages. Often
the implementations of the drivers differ in their support of SVG corner cases.
This extension attempts to make your SVG file suitable for such tools.
Further suggestions welcome!

Actions
-------

Multiple actions can be performed on paths, that do not alter the apperance, but may help other
extensions and tools to successfully work on a path. Or change paths behaviour according to a users intent.

Possible actions are

* Chain Paths <br>
  Multiple paths or subpaths that end or start at the same point (or very close) are combined into one larger path.

* Remove Duplicates <br>
  Paths or objects that appear in the same place multiple times are reduced to only one.

* Remove Degenerated Paths <br>
  Paths with less than 2 points can exist in SVG, but cannot be seen or selected in inkscape.

* Remove Duplicate Points <br>
  Path segments of length 0 are removed from a path. Two adjacient points in a path may form a loop -
  these are not removed.

* Break Apart - Keep holes <br>
  Separates subpaths into individual paths if they do not overlap.
  Similar to the builtin 'Break Apart' operation from the 'Path' menue, but preserves holes.

* Resolve self-intersecting paths <br>
  This is tricky. Not implemented.

* Ungroup groups of one object

* Remove empty groups


Usage
-----
Select multiple pathlike objects. If the status line shows you different object types,
then use "Path -> Object to Path". This is needed as we operate only on paths only.
Then select "Extensions -> Modify Path -> Clean Path" to open the settings dialog.

For the action 'Chain Paths' you can choose the maximum endpoint distance for
path ends to be linked, and the combination method: snap the points together,
or create a linking path segment.  Note, that paths never fork. This means,
that if there are three or more path ends at the same location, only two are
actually chained together. The others are added as subpaths.

The action 'Remove Duplicates' only removes mathemativcally exact duplicates.
E.g. a straight line from A to B with an additional point in the middle is a
different thing than a straigth from A to B. But different colors or fills do
not make a difference.

'Break Apart - Keep Holes' only works correctly with the NonZero Fill rule. A
ring created with EvenOdd rule may break into two circles. A warning is printed
when Paths with EvenOdd rule are being processed.


Installation
============

Copy the two files clean_path.inx and
clean_path.py to your computer:

Ubuntu / SUSE
-------------
* ~/.config/inkscape/extensions/ or
* /usr/share/inkscape/extensions/

Arch Linux
----------
* pacman -S inkscape
* git clone https://github.com/jnweiger/inkscape-clean-path.git
* cd inkscape-master
* sudo python2 setup.py build && sudo python2 setup.py install
* sudo cp clean_path.* /usr/share/inkscape/extensions/

Windows
-------
* Download https://github.com/jnweiger/inkscape-clean-path/archive/master.zip
* Navigate to your Downloads folder and double-click on **inkscape-clean-path-master.zip**
* Download and install the free test version of **winzip** from http://www.winzip.com, if needed.
* Click open the **inkscape-clean-path-master** folder.
* Select the following two items (with Ctrl-Click): **clean_path.inx**, and **clean_path.py**
* Extract to My Computer **C:\Program Files\Inkscape\share\extensions**


Mac OS X
--------
Copy the two files clean_path.inx and clean_path.py to your computer:
* ~/.config/inkscape/extensions/ or
*  /Applications/Inkscape.app/Contents/Resources/extensions/ .

To download the files from github, you can right click on the 'RAW' button and use your file managers 'save as' function.  Please check the size of the files. If the *.inx file is more than 2kb, you probably saved the webpage containing the file, instead of the file itself.



