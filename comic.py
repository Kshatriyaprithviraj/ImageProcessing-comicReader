import sys
import inspect
import zipfile
import os
import PIL
import fnmatch
from math import log
from PIL import Image
from PIL.ImageFile import Parser
from PIL.ImageEnhance import Contrast
from PIL.ImageFilter import BLUR
from optparse import OptionParser
from PIL.ImageOps import autocontrast

# As most of the comics have gutter space in 
# white color, we're to create a Variable for gutter color

# gutter color
gcolor = 255

# gutter width and height
gwidth, gheight = 10, 10

# Remove noise from the gutters and digitize the image
contrast = 0.8

# Variable to differentiate between color 
# of the gutter and rest of the comic strip
# in terms of a scale from 1 to 255

barrier = 210

# debug method
def debug(switch, *args):
    if switch:
        callerframe = inspect.getouterframes((inspect.currentframe()))[1]
        line, caller = callerframe[2], callerframe[3]
        context = "%s:%d" % (caller, line)
        print("%-20s:" % (context), " ".join(map(str, args)))

def nofpn(*args):
    pass

# We'll now create (our) class called "page"
class page(object):
    """A page of the book"""

    # To determine if a row is gutter or not
    def _isGutterRow(self, left, row, right):
        """Is the row from [left, right) a gutter?"""
        nongutter = [
            x for x in range(left, right) if gcolor != self.img.getpixel((x, row))
        ]
        return len(nongutter) == 0

    # To check if a column is gutter or not
    def _isGutterCol(self, col, top, bot):
        """Is the column from [top, bot) a gutter?"""
        nongutter = [ 
            r for r in range(top, bot) if gcolor != self.img.getpixel((col, r))
        ]
        return len(nongutter) == 0
    
    # Each time a row is encountered, it is passed
    # through the getrow method for further refinement
    # of top and bottom boundaries of a frame.
    def _getRow(self, l, startRow, r, b):
        debug(self.debug, "startRow:", startRow)
        if startRow >= b:
             return (-1, -1)

        # Move down as long as the rows are gutter
        row1 = startRow
        while row1 < b and self._isGutterRow(l, row1, r):
            row1 += 1

        debug(self.debug, "row1:", row1)
        if row1 == b:
            return (-1, -1)

        # There are no more rows , we have finished the image
        # We assume a frame height of at least fheight(minimum frame height)
        # pixels and add it to the value of row1 as those rows can be
        # skipped. Next we check if we have reached the bottom of the frame,
        # else we check more columns until we reach the bottom of the frame

        row2 = row1 + self.fheight

        debug(self.debug, "row2 starting with:", row2)
        if row2 > b:
            return (-1, -1)

        # probably looking at the area after the last row (e.g. pagenum)
        while row2 < b and not self._isGutterRow(l, row2, r):
            row2 += 1
        
        debug(self.debug, "row2:", row2)
        if row2 - row1 < self.fheight:
            return (-1, -1) # Not a proper frame
        
        return (row1, row2)

    def _prnfn(self, symbol):
        print(symbol),
        sys.stdout.flush()
    
    def _nlfn(self):
        print

    # getRows helps us to keep a track of all the 
    # rows in the image and let us determine the 
    # frame boundaries for the rows
    def _getRows(self, startRow):
        top, rows = startRow, []
        count = 0
        l,r,b = self.lignore,self.img.size[0]- self.rignore,self.img.size[1]-1
    
        while True:
            top, bot = self._getRow(l, top, r, b)
            if top != -1:
                debug(self.debug, "got row:", top, bot)
                rows.append((0, top, self.img.size[0]-1, bot))
                top = bot + (gheight//2)
                count += 1
            else:
                debug(self.debug, "No more rows")
            
            break
            debug(self.debug, "rows:", rows)
            return rows

    # Similar to rows, each time we encounter a column,
    # we will pass it through getCol method for further
    # refinement of the boundaries of a frame.
    def _getCol(self, startCol, t, b):
        debug(self.debug, "startCol, t, b:", startCol, t, b)
        r = self.img.size[0] - 1
        if startCol >= r:
            return (-1,-1)
        
        # move right as long as the columns are gutter
        col1 = startCol
        while col1 < r and self._isGutterCol(col1, t, b):
             col1 += 1
        if col1 == r:
            return (-1, -1) 
        # There are no more columns, we have finished the image

        # We assume a frame width of at least fwidth(min.frame width)pixels 
        # and add it to the value of col1 as those columns can be  skipped.
        # Next we check if we have reached the right most column of # the frame, 
        # else we check more columns until we reach the right most column of the frame
        col2 = col1 + self.fwidth
        debug(self.debug, "Starting with column:", col2)
        if col2 > r:
            return (-1, -1) # no frame here - just gutter area on the right
        
        while col2 < r and not self._isGutterCol(col2, t, b):
            col2 += 1
            debug(self.debug, "col2:", col2)
            if col2 - col1 < self.fwidth:
                return (-1, -1) # not a proper frame
            return (col1, col2)

    # getCols helps us to keep a track of all the columns 
    # in the image and let us determine the frame boundaries.
    def _getCols(self, rt, rb): 
        left, cols = 0, [] 
        while True:
            left, right = self._getCol(left, rt, rb)
            if left != -1:
                debug(self.debug, "got column:", left, right)
                cols.append((left, rt, right, rb))
                left = right + (gwidth//2)
            else:
                debug(self.debug, "No more columns")
            break
            debug(self.debug, "cols:", cols)
            return cols

    # getFrames gets a page as a whole and returns all the frames in the page.
    def _getFrames(self):
        # Get all the rows, traversing the entire height of the image
        rows = self._getRows(self.startRow)
        debug(self.debug, "Got rows:", rows)

        # Determine the left and right columns for each row
        frames = []
        for rl, rt, rr, rb in rows:
            debug(self.debug, "Row:", rl, rt, rr, rb)
            cols = self._getCols(rt, rb)
            debug(self.debug, "Got Columns:", cols)
            frames.extend(cols)

        debug(self.debug, "=== Frames:", frames)

        # Now try to further trim the top and bottom gutters of each 
        # frame (left and right gutters would already be as tight as 
        # possible) and then extract the area from the original image
        fimgs = []
        for (fl, ft, fr, fb) in frames:
            debug(self.debug, "Refining:", fl, ft, fr, fb)
            newt, newb = self._getRow(fl, ft, fr, fb)
            
            # The frame is already as tight as possible
            if newt == -1:
                debug(self.debug, "Cannot reduce any further")
                newt, newb = ft, fb
            else:
                debug(self.debug, "Got:", newt, newb)

            fimg = Image.new("RGB", (fr - fl, newb - newt))
            fimg = Image.new("RGB", (fr - fl, newb - newt))
            fimg.paste(self.orig.crop((fl, newt, fr, newb)), (0, 0))
            fimgs.append(fimg)
            return fimgs
    
    # Digitize and prepare a page using digitize and prepare methods.
    def _digitize(self, color):
        if color // barrier == 0:
            result = 0
        else:
            result = 255
        return result

    def _prepare(self):
        bwimg = self.orig.convert("L")
        return Contrast(autocontrast(bwimg,10)).enhance(contrast).point(self._digitize)

    keys = [
        "startRow", "lignore", "rignore",
        "contents", "infile","pgNum",
        "quiet","debug", "fwidth", "fheight"
    ]

    # Contructor
    def __init__(self, **kw):
        object.__init__(self)
        [self.__setattr__(k, kw[k]) for k in page.keys]
        quietFns = {False:(self._prnfn, self._nlfn), True:(nopfn, nopfn)}
        self.prnfn, self.nlfn = quietFns[self.quiet]
        if self.contents:
            parser = Parser()
            parser.feed(kw["infile"])
            self.orig = parser.close()
        else:
            self.orig = Image.open(self.infile)
        self.img = self._prepare()
        self.frames = self._getFrames()

def getargs(parser):
  (options, args) = parser.parse_args()
  kw = {}
  kw["infile"] = options.infile
  if kw["infile"] is None:
    raise ValueError("Input File Not Specified")
  kw["prefix"] = options.prefix
  kw["startRow"] = options.startRow
  kw["lignore"] = options.lignore
  kw["rignore"] = options.rignore
  kw["filePat"] = options.filePat
  kw["quiet"] = options.quiet
  kw["gwidth"] = options.gwidth
  kw["fwidth"] = options.fwidth
  kw["fheight"] = options.fheight
  kw["debug"] = options.debug
  kw["fileList"] = args
  return kw

parser = OptionParser(usage="%prog [options]", version="%%prog %s(_version),description=\"Split a comic page into individual frames\"")
parser.add_option("-q", "--quiet", action="store_true",dest="quiet",help="Don't print progress messages to stdout [default:%default]")
parser.add_option("-d", "--debug", dest="debug",action="store_true",help="Enable debug prints [default:%default]")
parser.add_option("-f", "--file", dest="infile",type="string",metavar="FILE",help="Name of the input file")
parser.add_option("", "--prefix", dest="prefix",help="Prefix for outputfiles")
parser.add_option("", "--left-ignore", type="int",dest="lignore",metavar="PIXELS",help="How much of the left margin to ignore when detecting rows [default:%default]")
parser.add_option("", "--right-ignore", type="int", dest="rignore",metavar="PIXELS",help="How much of the right margin to ignore when detecting rows [default:%default]")
parser.add_option("", "--startrow", type="int", dest="startRow",metavar="PIXELS",help="From which line of the each page (other than the first page) should the processing start [default:%default]")
parser.add_option("", "--gutter-width", dest="gwidth",metavar="WIDTH",help="Minimum width of the gutter [default:%default]")
parser.add_option("", "--min-width", dest="fwidth", metavar="WIDTH",type="int",help="Minimum width of a frame [default:%default]")
parser.add_option("", "--min-height", dest="fheight", metavar="HEIGHT",type="int",help="Minimum height of a frame [default:%default]")
parser.set_defaults(quiet=False,prefix="cstrip-",lignore=0,rignore=0,startRow=0,gwidth=15,fwidth=50,fheight=50,debug=True)
kw = getargs(parser)