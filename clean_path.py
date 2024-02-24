#!/usr/bin/env python
#
# Inkscape extension making long continuous paths from shorter pieces.
# (C) 2015 juewei@fabmail.org
#
# code snippets visited to learn the extension 'effect' interface:
# - convert2dashes.py
# - http://github.com/jnweiger/inkscape-silhouette
# - http://github.com/jnweiger/inkscape-gears-dev
# - http://sourceforge.net/projects/inkcut/
# - http://code.google.com/p/inkscape2tikz/
# - http://code.google.com/p/eggbotcode/
#
# 2015-11-30 jw, V0.1 -- initial draught

__version__ = '0.1'	# Keep in sync with clean_path.inx ca line 22
__author__ = 'Juergen Weigert <juergen@fabmail.org>'

import sys, os, shutil, time, logging, tempfile, math

debug = True
#debug = False

# search path, so that inkscape libraries are found when we are standalone.
sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):	# windows
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
elif sys_platform.startswith('darwin'):	# mac
  sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
else:   				# linux
  # if sys_platform.startswith('linux'):
  sys.path.append('/usr/share/inkscape/extensions')

# inkscape libraries
import inkex
import cubicsuperpath

inkex.localize()

from optparse import SUPPRESS_HELP

def uutounit(self,nn,uu):
  try:
    return self.uutounit(nn,uu)		# inkscape 0.91
  except:
    return inkex.uutounit(nn,uu)	# inkscape 0.48

class ChainPaths(inkex.Effect):
  """
  Inkscape Extension make long continuous paths from smaller parts
  """
  def __init__(self):
    # Call the base class constructor.
    inkex.Effect.__init__(self)

    # For handling an SVG viewbox attribute, we will need to know the
    # values of the document's <svg> width and height attributes as well
    # as establishing a transform from the viewbox to the display.
    self.chain_epsilon = 0.01
    self.snap_ends = True
    self.segments_done = {}
    self.min_missed_distance_sq = None
    self.chained_count = 0

    try:
      self.tty = open("/dev/tty", 'w')
    except:
      try:
        self.tty = open("CON:", 'w')	# windows. Does this work???
      except:
        self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
    if debug: print >>self.tty, "__init__"

    self.OptionParser.add_option('-V', '--version',
          action = 'store_const', const=True, dest='version', default=False,
          help='Just print version number ("'+__version__+'") and exit.')
    self.OptionParser.add_option('-s', '--snap', action='store', dest='snap_ends', type='inkbool', default=True, help='snap end-points together when connecting')
    self.OptionParser.add_option('-u', '--units', action='store', dest="units", type="string", default="mm", help="measurement unit for epsilon")
    self.OptionParser.add_option('-e', '--epsilon', action='store',
          type='float', dest='chain_epsilon', default=0.01, help="Max. distance to connect [mm]")

  def version(self):
    return __version__
  def author(self):
    return __author__

  def calc_unit_factor(self, units='mm'):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        dialog_units = uutounit(self, 1.0, units)
        self.unit_factor = 1.0 / dialog_units
        return self.unit_factor

  def reverse_segment(self, seg):
    r = []
    for s in reversed(seg):
      # s has 3 elements: handle1, point, handle2
      # Swap handles.
      s.reverse()
      r.append(s)
    return r

  def set_segment_done(self, id, n, msg=''):
    if not id in self.segments_done:
      self.segments_done[id] = {}
    self.segments_done[id][n] = True
    if debug: print >>self.tty, "done", id, n, msg

  def is_segment_done(self, id, n):
    if not id in self.segments_done:
      return False
    if n in self.segments_done[id]:
      return True
    return False

  def link_segments(self, seg1, seg2):
    if self.snap_ends:
      seg = seg1[:-1]
      p1 = seg1[-1]
      p2 = seg2[0]
      # fuse p1 and p2 to create one new point:
      # first handle from p1, point coordinates averaged, second handle from p2
      seg.append([ [ p1[0][0]             ,  p1[0][1]             ],
                   [(p1[1][0]+p2[1][0])*.5, (p1[1][1]+p2[1][1])*.5],
                   [          p2[2][0]    ,           p2[2][1]    ] ])
      seg.extend(seg2[1:])
    else:
      seg = seg1[:]
      seg.extend(seg2[:])
    self.chained_count += 1
    return seg


  def near_ends(self, end1, end2):
    """ requires self.eps_sq to be the square of the near distance """
    dx = end1[0] - end2[0]
    dy = end1[1] - end2[1]
    d_sq = dx * dx + dy * dy
    if d_sq > self.eps_sq:
      if self.min_missed_distance_sq is None:
        self.min_missed_distance_sq = d_sq
      elif self.min_missed_distance_sq > d_sq:
        self.min_missed_distance_sq = d_sq
      return False
    else:
      return True


  def effect(self):
    if self.options.version:
      print __version__
      sys.exit(0)

    self.calc_unit_factor(self.options.units)

    if self.options.snap_ends     is not None: self.snap_ends     = self.options.snap_ends
    if self.options.chain_epsilon is not None: self.chain_epsilon = self.options.chain_epsilon
    if self.chain_epsilon < 0.0001: self.chain_epsilon = 0.0001	# keep a minimum.
    self.eps_sq = self.chain_epsilon * self.unit_factor * self.chain_epsilon * self.unit_factor

    if not len(self.selected.items()):
      inkex.errormsg(_("Please select one or more objects."))
      return

    segments = []
    for id, node in self.selected.iteritems():
      if node.tag != inkex.addNS('path','svg'):
        inkex.errormsg(_("Object "+id+" is not a path. Try\n  - Path->Object to Path\n  - Object->Ungroup"))
        return
      if debug: print >>self.tty, "id="+str(id), "tag="+str(node.tag)
      path_d = cubicsuperpath.parsePath(node.get('d'))
      sub_idx = -1
      for sub in path_d:
        sub_idx += 1
        # sub=[[[200.0, 300.0], [200.0, 300.0], [175.0, 290.0]], [[175.0, 265.0], [220.37694, 256.99876], [175.0, 240.0]], [[175.0, 215.0], [200.0, 200.0], [200.0, 200.0]]]
        # this is a path of three points. All the bezier handles are included. the Structure is:
        # [[handle0_x, point0, handle0_1], [handle1_0, point1, handle1_2], [handle2_1, point2, handle2_x]]
        if debug: print >>self.tty, "   sub="+str(sub)
        end1=[sub[0][1][0],sub[0][1][1]]
        end2=[sub[-1][1][0],sub[-1][1][1]]

        while ((len(sub) > 1) and self.near_ends(end1, end2)):
          # FIXME: this also splits any closed path. eg. a rectangle.
          if debug: print >>self.tty, "splitting self-reversing path, length:", len(sub)
          ## We split the path and generate more snippets.
          splitp=[sub[-2][1][0],sub[-2][1][1]]
          segments.append({'id': id, 'n': sub_idx, 'end1': splitp, 'end2':end2, 'seg': [sub[-2],sub[-1]]})
          sub_idx += 1
          sub.pop()
          end2=splitp

        segments.append({'id': id, 'n': sub_idx, 'end1': end1, 'end2':end2, 'seg': sub})
      if node.get(inkex.addNS('type','sodipodi')):
        del node.attrib[inkex.addNS('type', 'sodipodi')]
    if debug: print >>self.tty, "-------- seen:"
    for s in segments:
      if debug: print >>self.tty, s['id'],s['n'],s['end1'],s['end2']

    # chain the segments
    obsoleted = 0
    remaining = 0
    for id, node in self.selected.iteritems():
      # path_style = simplestyle.parseStyle(node.get('style'))
      path_d = cubicsuperpath.parsePath(node.get('d'))
      new=[]
      cur_idx = -1
      for cur in path_d:
        cur_idx += 1
	if not self.is_segment_done(id, cur_idx):
	  # quadratic algorithm: we check both ends of the current segment.
	  # If one of them is near another known end from the segments list, we
	  # chain this segment to the current segment and remove it from the
	  # list,
	  # end1-end1 or end2-end2: The new segment is reversed.
	  # end1-end2: The new segment is prepended to the current segment.
	  # end2-end1: The new segment is appended to the current segment.
	  self.set_segment_done(id, cur_idx, "output")	# do not cross with ourselves.
	  end1=[cur[0][1][0],cur[0][1][1]]
	  end2=[cur[-1][1][0],cur[-1][1][1]]
	  segments_idx = 0
	  while segments_idx < len(segments):
	    seg = segments[segments_idx]
	    if self.is_segment_done(seg['id'], seg['n']):
	      segments_idx += 1
	      continue

	    if (self.near_ends(end1, seg['end1']) or
	        self.near_ends(end2, seg['end2'])):
	      seg['seg'] = self.reverse_segment(seg['seg'])
	      seg['end1'],seg['end2'] = seg['end2'],seg['end1']
	      if debug: print >>self.tty, "reversed seg", seg['id'], seg['n']

	    if self.near_ends(end1, seg['end2']):
	      # prepend seg to cur
	      self.set_segment_done(seg['id'], seg['n'], 'prepended to '+id+' '+str(cur_idx))
	      cur = self.link_segments(seg['seg'], cur)
	      end1=[cur[0][1][0],cur[0][1][1]]
	      segments_idx = 0
	      continue

	    if self.near_ends(end2, seg['end1']):
	      # append seg to cur
	      self.set_segment_done(seg['id'], seg['n'], 'appended to '+id+' '+str(cur_idx))
	      cur = self.link_segments(cur, seg['seg'])
	      end2=[cur[-1][1][0],cur[-1][1][1]]
	      segments_idx = 0
	      continue

	    segments_idx += 1

	  new.append(cur)

      if not len(new):
        # node.clear()
        node.getparent().remove(node)
	obsoleted += 1
        if debug: print >>self.tty, "Path node obsoleted:", id
      else:
        remaining += 1
        node.set('d',cubicsuperpath.formatPath(new))

    # statistics:
    print >>self.tty, "Path nodes obsoleted:", obsoleted, "\nPath nodes remaining:", remaining
    if self.min_missed_distance_sq is not None:
      print >>self.tty, "min_missed_distance:", math.sqrt(float(self.min_missed_distance_sq))/self.unit_factor, '>', self.chain_epsilon, self.options.units
    print >>self.tty, "Successful link operations: ", self.chained_count

if __name__ == '__main__':
        e = ChainPaths()

        e.affect()
        sys.exit(0)    # helps to keep the selection
