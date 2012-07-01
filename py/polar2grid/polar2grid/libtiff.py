#!/usr/bin/env python
"""
Ctypes based wrapper to libtiff library.

See TIFF.__doc__ for usage information.

Homepage:  http://pylibtiff.googlecode.com/

Edited by David Hoese to further expand on functionality
"""
__author__ = 'Pearu Peterson'
__author__ = 'David Hoese'
#__date__ = 'April 2009'
__date__ = 'June 2012'
__license__ = 'BSD'
__all__ = ['libtiff', 'TIFF']

import numpy as np

import os
import sys
import logging
import ctypes
import ctypes.util

log = logging.getLogger(__name__)

def get_library_filename():
    if os.name=='nt':
        # assume that the directory of libtiff3.dll is in PATH.
        lib = ctypes.util.find_library('libtiff3')
        if lib is None:
            # try default installation path:
            lib = r'C:\Program Files\GnuWin32\bin\libtiff3.dll'
            if os.path.isfile (lib):
                print 'You should add %r to PATH environment variable and reboot.' % (os.path.dirname (lib))
            else:
                lib = None
    else:
        if hasattr(sys, 'frozen') and sys.platform == 'darwin' and os.path.exists('../Frameworks/libtiff.dylib'):
            # py2app support, see Issue 8.
            lib = '../Frameworks/libtiff.dylib'
        else:
            lib = ctypes.util.find_library('tiff')
    if lib is None:
        raise ImportError('Failed to find TIFF library. Make sure that libtiff is installed and its location is listed in PATH|LD_LIBRARY_PATH|..')

    log.debug("libtiff library found %s" % lib)
    return lib

def load_library(lib_fn=None):
    if lib_fn is None:
        lib_fn = get_library_filename()

    libtiff = ctypes.cdll.LoadLibrary(lib_fn)
    return libtiff

def get_header_defs(libtiff=None, lib_fn=None):
    if lib_fn is None:
        lib_fn = get_library_filename()
    if libtiff is None:
        libtiff = load_library(lib_fn=lib_fn)

    libtiff.TIFFGetVersion.restype = ctypes.c_char_p
    libtiff.TIFFGetVersion.argtypes = []

    libtiff_version_str = libtiff.TIFFGetVersion()
    i = libtiff_version_str.lower().split().index('version')
    assert i!=-1,`libtiff_version_str`
    libtiff_version = libtiff_version_str.split()[i+1]

    tiff_h_name = 'tiff_h_%s' % (libtiff_version.replace ('.','_'))

    try:
        exec 'import %s as tiff_h' % (tiff_h_name)
    except ImportError:
        tiff_h = None

    if tiff_h is None:
        include_tiff_h = os.path.join(os.path.split(lib_fn)[0], '..', 'include', 'tiff.h')
        if not os.path.isfile(include_tiff_h):
            # fix me for windows:
            include_tiff_h = os.path.join('/usr','include','tiff.h')
        if not os.path.isfile(include_tiff_h):
            raise ValueError('Failed to find TIFF header file (may be need to run: sudo apt-get install libtiff4-dev)')
        # Read TIFFTAG_* constants for the header file:
        f = open (include_tiff_h, 'r')
        l = []
        d = {}
        for line in f.readlines():
            if not line.startswith('#define'): continue
            words = line[7:].lstrip().split()[:2]
            if len (words)!=2: continue
            name, value = words
            i = value.find('/*')
            if i!=-1: value = value[:i]
            if value in d:
                value = d[value]
            else:
                value = eval(value)
            d[name] = value
            l.append('%s = %s' % (name, value))
        f.close()


        fn = os.path.join (os.path.dirname (os.path.abspath (__file__)), tiff_h_name+'.py')
        print 'Generating %r' % (fn)
        f = open(fn, 'w')
        f.write ('\n'.join(l) + '\n')
        f.close()
    else:
        d = tiff_h.__dict__

    d['TIFFTAG_CZ_LSMINFO'] = 34412
    return d

def get_tag_names(header_def):
    all_tags = header_def.copy()
    for k in all_tags.keys():
        if k.startswith("_"):
            del all_tags[k]
    return all_tags

def create_tag_maps(header_dict):
    define_to_name_map = dict(Orientation={}, Compression={},
                              PhotoMetric={}, PlanarConfig={},
                              SampleFormat={}, FillOrder={},
                              FaxMode={}, TiffTag = {}
                              )

    name_to_define_map = dict(Orientation={}, Compression={},
                              PhotoMetric={}, PlanarConfig={},
                              SampleFormat={}, FillOrder={},
                              FaxMode={}, TiffTag = {}
                              )

    for name, value in d.items():
        if name.startswith ('_'): continue
        # FIXME: Make the rest of this file not use globals, but access from the 2 maps returned
        exec 'global %s; %s = %s' % (name, name, value)
        for n in define_to_name_map:
            if name.startswith(n.upper()):
                define_to_name_map[n][value] = name        
                name_to_define_map[n][name] = value

    return name_to_define_map,define_to_name_map


# Actually load the library
# FIXME: Rename d, non-descriptive name
lib = get_library_filename()
libtiff = load_library(lib_fn=lib)
d = header_def = get_header_defs(libtiff=libtiff, lib_fn=lib)
all_tags = get_tag_names(header_def)
name_to_define_map,define_to_name_map = create_tag_maps(all_tags)

                
# types defined by tiff.h
class c_ttag_t(ctypes.c_uint): pass
class c_tdir_t(ctypes.c_uint16): pass
class c_tsample_t(ctypes.c_uint16): pass
class c_tstrip_t(ctypes.c_uint32): pass
class c_ttile_t(ctypes.c_uint32): pass
class c_tsize_t(ctypes.c_int32): pass
class c_toff_t(ctypes.c_int32): pass
class c_tdata_t(ctypes.c_void_p): pass
class c_thandle_t(ctypes.c_void_p): pass

# types defined for creating custom tags
FIELD_CUSTOM = 65

class TIFFDataType(object):
    """Place holder for the enum in C.

    typedef enum {
        TIFF_NOTYPE = 0,    /* placeholder */
        TIFF_BYTE   = 1,    /* 8-bit unsigned integer */
        TIFF_ASCII  = 2,    /* 8-bit bytes w/ last byte null */
        TIFF_SHORT  = 3,    /* 16-bit unsigned integer */
        TIFF_LONG   = 4,    /* 32-bit unsigned integer */
        TIFF_RATIONAL   = 5,    /* 64-bit unsigned fraction */
        TIFF_SBYTE  = 6,    /* !8-bit signed integer */
        TIFF_UNDEFINED  = 7,    /* !8-bit untyped data */
        TIFF_SSHORT = 8,    /* !16-bit signed integer */
        TIFF_SLONG  = 9,    /* !32-bit signed integer */
        TIFF_SRATIONAL  = 10,   /* !64-bit signed fraction */
        TIFF_FLOAT  = 11,   /* !32-bit IEEE floating point */
        TIFF_DOUBLE = 12,   /* !64-bit IEEE floating point */
        TIFF_IFD    = 13    /* %32-bit unsigned integer (offset) */
    } TIFFDataType;
    """
    ctype = ctypes.c_int
    TIFF_NOTYPE = 0
    TIFF_BYTE = 1
    TIFF_ASCII = 2
    TIFF_SHORT = 3
    TIFF_LONG = 4
    TIFF_RATIONAL = 5
    TIFF_SBYTE = 6
    TIFF_UNDEFINED = 7
    TIFF_SSHORT = 8
    TIFF_SLONG = 9
    TIFF_SRATIONAL = 10
    TIFF_FLOAT = 11
    TIFF_DOUBLE = 12
    TIFF_IFD = 13

ttype2ctype = {
    TIFFDataType.TIFF_NOTYPE : None,
    TIFFDataType.TIFF_BYTE : ctypes.c_ubyte,
    TIFFDataType.TIFF_ASCII : ctypes.c_char_p,
    TIFFDataType.TIFF_SHORT : ctypes.c_uint16,
    TIFFDataType.TIFF_LONG : ctypes.c_uint32,
    TIFFDataType.TIFF_RATIONAL : ctypes.c_double, # Should be unsigned
    TIFFDataType.TIFF_SBYTE : ctypes.c_byte,
    TIFFDataType.TIFF_UNDEFINED : ctypes.c_char,
    TIFFDataType.TIFF_SSHORT : ctypes.c_int16,
    TIFFDataType.TIFF_SLONG : ctypes.c_int32,
    TIFFDataType.TIFF_SRATIONAL : ctypes.c_double,
    TIFFDataType.TIFF_FLOAT : ctypes.c_float,
    TIFFDataType.TIFF_DOUBLE : ctypes.c_double,
    TIFFDataType.TIFF_IFD : ctypes.c_uint32
    }

#ctype2ntype = {
#    ctypes.c_ubyte : numpy.ubyte,
#    ctypes.c_char_p : numpy.char_p,
#    ctypes.c_uint16,
#    ctypes.c_uint32,
#    ctypes.c_double,
#    ctypes.c_byte,
#    ctypes.c_char,
#    ctypes.c_int16,
#    ctypes.c_int32,
#    ctypes.c_float
#    }
class TIFFFieldInfo(ctypes.Structure):
    """
    typedef struct {
        ttag_t  field_tag;      /* field's tag */
        short   field_readcount;    /* read count/TIFF_VARIABLE/TIFF_SPP */
        short   field_writecount;   /* write count/TIFF_VARIABLE */
        TIFFDataType field_type;    /* type of associated data */
        unsigned short field_bit;   /* bit in fieldsset bit vector */
        unsigned char field_oktochange; /* if true, can change while writing */
        unsigned char field_passcount;  /* if true, pass dir count on set */
        char    *field_name;        /* ASCII name */
        } TIFFFieldInfo;
    """
    _fields_ = [
            ("field_tag", ctypes.c_uint32),
            ("field_readcount", ctypes.c_short),
            ("field_writecount", ctypes.c_short),
            ("field_type", TIFFDataType.ctype),
            ("field_bit", ctypes.c_ushort),
            ("field_oktochange", ctypes.c_ubyte),
            ("field_passcount", ctypes.c_ubyte),
            ("field_name", ctypes.c_char_p)
            ]

def tag_array(num_tags):
    return TIFFFieldInfo * num_tags

def write_list(list_elems, c_type):
    return (c_type * len(list_elems))(*list_elems)

def read_list(first_elem, num_elems, dtype=np.float32):
    return list(numpy.frombuffer(numpy.core.multiarray.int_asbuffer(ctypes.addressof(first_elem), ctypes.sizeof(first_elem)*num_elems), dtype))

tifftags = {

# conversion of None means it is an array of known size (no count is passed to GetField)
# conversion of None shouldn't need to be used for ASCII values
#TODO:
#TIFFTAG_DOTRANGE                2      uint16*
#TIFFTAG_HALFTONEHINTS           2      uint16*
#TIFFTAG_PAGENUMBER              2      uint16*
#TIFFTAG_YCBCRSUBSAMPLING        2      uint16*
#TIFFTAG_EXTRASAMPLES            2      uint16*,uint16**  count & types array
#TIFFTAG_FAXFILLFUNC             1      TIFFFaxFillFunc*  G3/G4 compression pseudo-tag
#TIFFTAG_JPEGTABLES              2      u_short*,void**   count & tables
#TIFFTAG_SUBIFD                  2      uint16*,uint32**  count & offsets array
#TIFFTAG_TRANSFERFUNCTION        1 or 3 uint16**          1<<BitsPerSample entry arrays
#TIFFTAG_ICCPROFILE              2      uint32*,void**    count, profile data

    # TIFFTAG: type, conversion  
    TIFFTAG_COLORMAP: (ctypes.c_uint16, lambda d:(d[0].contents[:],d[1].contents[:],d[2].contents[:])),# 3 uint16* for Set, 3 uint16** for Get; size:(1<<BitsPerSample arrays)
    TIFFTAG_ARTIST: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_COPYRIGHT: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_DATETIME: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_DOCUMENTNAME: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_HOSTCOMPUTER: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_IMAGEDESCRIPTION: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_INKNAMES: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_MAKE: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_MODEL: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_PAGENAME: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_SOFTWARE: (ctypes.c_char_p, lambda d:d.value),
    TIFFTAG_TARGETPRINTER: (ctypes.c_char_p, lambda d:d.value),

    TIFFTAG_BADFAXLINES: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_CONSECUTIVEBADFAXLINES: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_GROUP3OPTIONS: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_GROUP4OPTIONS: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_IMAGEDEPTH: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_IMAGEWIDTH: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_IMAGELENGTH: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_SAMPLESPERPIXEL: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_ROWSPERSTRIP: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_SUBFILETYPE: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_TILEDEPTH: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_TILELENGTH: (ctypes.c_uint32, lambda d:d.value),
    TIFFTAG_TILEWIDTH: (ctypes.c_uint32, lambda d:d.value),

    # TODO: Handle variable length pointers
    TIFFTAG_STRIPBYTECOUNTS: (ctypes.POINTER(ctypes.c_uint32), lambda d:d.contents),
    TIFFTAG_STRIPOFFSETS: (ctypes.POINTER(ctypes.c_uint32), lambda d:d.contents),
    TIFFTAG_TILEBYTECOUNTS: (ctypes.POINTER(ctypes.c_uint32), lambda d:d.contents),
    TIFFTAG_TILEOFFSETS: (ctypes.POINTER(ctypes.c_uint32), lambda d:d.contents),
        
    TIFFTAG_BITSPERSAMPLE: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_CLEANFAXDATA: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_COMPRESSION: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_DATATYPE: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_FILLORDER: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_INKSET: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_MATTEING: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_MAXSAMPLEVALUE: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_MINSAMPLEVALUE: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_ORIENTATION: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_PHOTOMETRIC: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_PLANARCONFIG: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_PREDICTOR: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_RESOLUTIONUNIT: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_SAMPLEFORMAT: (ctypes.c_uint16, lambda d:d.value),
    TIFFTAG_YCBCRPOSITIONING: (ctypes.c_uint16, lambda d:d.value),

    TIFFTAG_JPEGQUALITY: (ctypes.c_int, lambda d:d.value),
    TIFFTAG_JPEGCOLORMODE: (ctypes.c_int, lambda d:d.value),
    TIFFTAG_JPEGTABLESMODE: (ctypes.c_int, lambda d:d.value),
    TIFFTAG_FAXMODE: (ctypes.c_int, lambda d:d.value),

    TIFFTAG_SMAXSAMPLEVALUE: (ctypes.c_double, lambda d:d.value),
    TIFFTAG_SMINSAMPLEVALUE: (ctypes.c_double, lambda d:d.value),

    TIFFTAG_STONITS: (ctypes.c_double, lambda d:d.value),

    TIFFTAG_XPOSITION: (ctypes.c_float, lambda d:d.value),
    TIFFTAG_XRESOLUTION: (ctypes.c_float, lambda d:d.value),
    TIFFTAG_YPOSITION: (ctypes.c_float, lambda d:d.value),
    TIFFTAG_YRESOLUTION: (ctypes.c_float, lambda d:d.value),

    TIFFTAG_PRIMARYCHROMATICITIES: (ctypes.c_float*6, lambda d:d.contents[:]),
    TIFFTAG_REFERENCEBLACKWHITE: (ctypes.c_float*6, lambda d:d.contents[:]),
    TIFFTAG_WHITEPOINT: (ctypes.c_float*2, lambda d:d.contents[:]),
    TIFFTAG_YCBCRCOEFFICIENTS: (ctypes.c_float*3, lambda d:d.contents[:]),

    TIFFTAG_CZ_LSMINFO: (c_toff_t, lambda d:d.value) # offset to CZ_LSMINFO record

}


def debug(func):
    return func
    def new_func(*args, **kws):
        print 'Calling',func.__name__
        r = func (*args, **kws)
        return r
    return new_func

class TIFF(ctypes.c_void_p):
    """ Holds a pointer to TIFF object.

    To open a tiff file for reading, use

      tiff = TIFF.open (filename, more='r')
      
    To read an image from a tiff file, use

      image = tiff.read_image()

    where image will be a numpy array.

    To read all images from a tiff file, use

      for image in tiff.iter_images():
          # do stuff with image

    To creat a tiff file containing numpy array as image, use

      tiff = TIFF.open(filename, mode='w')
      tiff.write_image(array)
      tiff.close()

    To copy and change tags from a tiff file:

      tiff_in =  TIFF.open(filename_in)
      tiff_in.copy (filename_out, compression=, bitspersample=, sampleformat=,...)
    """

    @staticmethod
    def get_tag_name(tagvalue):
        for kind in define_to_name_map:
            tagname = define_to_name_map[kind].get (tagvalue)
            if tagname is not None:
                return tagname

    @staticmethod
    def get_tag_define(tagname):
        if '_' in tagname:
            kind, name = tagname.rsplit('_',1)
            return name_to_define_map[kind.title()][tagname.upper()]
        for kind in define_to_name_map:
            tagvalue = name_to_define_map[kind].get((kind+'_'+tagname).upper ())
            if tagvalue is not None:
                return tagvalue

    @classmethod
    def open(cls, filename, mode='r'):
        """ Open tiff file as TIFF.
        """
        tiff = libtiff.TIFFOpen(filename, mode)
        if tiff.value is None:
            raise TypeError ('Failed to open file '+`filename`)
        return tiff

    @staticmethod
    def get_numpy_type(bits, sample_format=None):
        """ Return numpy dtype corresponding to bits and sample format.
        """
        typ = None
        if bits==1:
            pass
        elif sample_format==SAMPLEFORMAT_IEEEFP:
            typ = getattr(np,'float%s' % (bits))
        elif sample_format==SAMPLEFORMAT_UINT or sample_format is None:
            typ = getattr(np,'uint%s' % (bits))
        elif sample_format==SAMPLEFORMAT_INT:
            typ = getattr(np,'int%s' % (bits))
        elif sample_format==SAMPLEFORMAT_COMPLEXIEEEFP:
            typ = getattr(np,'complex%s' % (bits))
        else:
            raise NotImplementedError (`sample_format`)
        return typ

    @debug
    def read_image(self, verbose=False):
        """ Read image from TIFF and return it as an array.
        """
        width = self.GetField('ImageWidth')
        height = self.GetField('ImageLength')
        bits = self.GetField('BitsPerSample')
        sample_format = self.GetField('SampleFormat')
        compression = self.GetField('Compression')

        typ = self.get_numpy_type(bits, sample_format)

        if typ is None:
            if bits==1: # TODO: check for correctness
                typ = np.uint8
                itemsize = 1
            elif bits==4: # TODO: check for correctness
                typ = np.uint32
                itemsize = 4
            else:
                raise NotImplementedError (`bits`)
        else:
            itemsize = bits/8

        size = width * height * itemsize
        arr = np.zeros((height, width), typ)

        if compression==COMPRESSION_NONE:
            ReadStrip = self.ReadRawStrip
        else:
            ReadStrip = self.ReadEncodedStrip

        pos = 0
        elem = None
        for strip in range (self.NumberOfStrips()):
            if elem is None:
                elem = ReadStrip(strip, arr.ctypes.data + pos, size)
            elif elem:
                elem = ReadStrip(strip, arr.ctypes.data + pos, min(size - pos, elem))
            pos += elem
        return arr

    @staticmethod
    def _fix_compression(value):
        if isinstance(value, int):
            return value
        elif value is None:
            return COMPRESSION_NONE
        elif isinstance(value, str):
            return name_to_define_map['Compression']['COMPRESSION_'+value.upper()]
        else:
            raise NotImplementedError(`value`)

    @staticmethod
    def _fix_sampleformat(value):
        if isinstance(value, int):
            return value
        elif value is None:
            return SAMPLEFORMAT_UINT            
        elif isinstance(value, str):
            return dict(int=SAMPLEFORMAT_INT, uint=SAMPLEFORMAT_UINT,
                        float=SAMPLEFORMAT_IEEEFP, complex=SAMPLEFORMAT_COMPLEXIEEEFP)[value.lower()]
        else:
            raise NotImplementedError(`value`)

    def write_image(self, arr, compression=None, write_rgb=False):
        """ Write array as TIFF image.

        Parameters
        ----------
        arr : :numpy:`ndarray`
          Specify image data of rank 1 to 3.
        compression : {None, 'ccittrle', 'ccittfax3','ccitt_t4','ccittfax4','ccitt_t6','lzw','ojpeg','jpeg','next','ccittrlew','packbits','thunderscan','it8ctpad','it8lw','it8mp','it8bl','pixarfilm','pixarlog','deflate','adobe_deflate','dcs','jbig','sgilog','sgilog24','jp2000'}
        write_rgb: bool
          Write rgb image if data is of size 3xWxH (otherwise, writes a multipage TIFF).
        """
        COMPRESSION = self._fix_compression (compression)

        arr = np.ascontiguousarray(arr)
        sample_format = None
        if arr.dtype in np.sctypes['float']:
            sample_format = SAMPLEFORMAT_IEEEFP
        elif arr.dtype in np.sctypes['uint']+[numpy.bool]:
            sample_format = SAMPLEFORMAT_UINT
        elif arr.dtype in np.sctypes['int']:
            sample_format = SAMPLEFORMAT_INT
        elif arr.dtype in np.sctypes['complex']:
            sample_format = SAMPLEFORMAT_COMPLEXIEEEFP
        else:
            raise NotImplementedError(`arr.dtype`)
        shape=arr.shape
        bits = arr.itemsize * 8

        if compression==COMPRESSION_NONE:
            WriteStrip = self.WriteRawStrip
        else:
            WriteStrip = self.WriteEncodedStrip

        if len(shape)==1:
            width, = shape
            size = width * arr.itemsize
            self.SetField(TIFFTAG_IMAGEWIDTH, width)
            self.SetField(TIFFTAG_IMAGELENGTH, 1)
            self.SetField(TIFFTAG_BITSPERSAMPLE, bits)
            self.SetField(TIFFTAG_COMPRESSION, COMPRESSION)
            self.SetField(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK)
            self.SetField(TIFFTAG_ORIENTATION, ORIENTATION_RIGHTTOP)
            self.SetField(TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG)
            if sample_format is not None:
                self.SetField(TIFFTAG_SAMPLEFORMAT, sample_format)
            WriteStrip(0, arr.ctypes.data, size)
            self.WriteDirectory()

        elif len(shape)==2:
            height, width = shape
            size = width * height * arr.itemsize

            self.SetField(TIFFTAG_IMAGEWIDTH, width)
            self.SetField(TIFFTAG_IMAGELENGTH, height)
            self.SetField(TIFFTAG_BITSPERSAMPLE, bits)
            self.SetField(TIFFTAG_COMPRESSION, COMPRESSION)
            #self.SetField(TIFFTAG_SAMPLESPERPIXEL, 1)
            self.SetField(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK)
            self.SetField(TIFFTAG_ORIENTATION, ORIENTATION_RIGHTTOP)
            self.SetField(TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG)

            if sample_format is not None:
                self.SetField(TIFFTAG_SAMPLEFORMAT, sample_format)

            WriteStrip(0, arr.ctypes.data, size)            
            self.WriteDirectory()
        elif len(shape)==3:
            depth, height, width = shape
            size = width * height * arr.itemsize
            if depth == 3 and write_rgb:
                self.SetField(TIFFTAG_IMAGEWIDTH, width)
                self.SetField(TIFFTAG_IMAGELENGTH, height)
                self.SetField(TIFFTAG_BITSPERSAMPLE, bits)
                self.SetField(TIFFTAG_COMPRESSION, COMPRESSION)
                self.SetField(TIFFTAG_SAMPLESPERPIXEL, 3)
                self.SetField(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_RGB)
                self.SetField(TIFFTAG_PLANARCONFIG, PLANARCONFIG_SEPARATE)

                if sample_format is not None:
                    self.SetField(TIFFTAG_SAMPLEFORMAT, sample_format)
                for n in range(depth):
                    WriteStrip(n, arr[n, :, :].ctypes.data, size)
                self.WriteDirectory()
            else:
                for n in range(depth):
                    self.SetField(TIFFTAG_IMAGEWIDTH, width)
                    self.SetField(TIFFTAG_IMAGELENGTH, height)
                    self.SetField(TIFFTAG_BITSPERSAMPLE, bits)
                    self.SetField(TIFFTAG_COMPRESSION, COMPRESSION)
                    #self.SetField(TIFFTAG_SAMPLESPERPIXEL, 1)
                    self.SetField(TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK)
                    self.SetField(TIFFTAG_ORIENTATION, ORIENTATION_RIGHTTOP)
                    self.SetField(TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG)

                    if sample_format is not None:
                        self.SetField(TIFFTAG_SAMPLEFORMAT, sample_format)

                    WriteStrip(0, arr[n].ctypes.data, size)
                    self.WriteDirectory()
        else:
            raise NotImplementedError (`shape`)

    def write_tiles(self, arr):
        num_trows = self.GetField("TileLength")
        if num_trows is None:
            raise ValueError("TIFFTAG_TILELENGTH must be set to write tiles")
        num_tcols = self.GetField("TileWidth")
        if num_tcols is None:
            raise ValueError("TIFFTAG_TILEWIDTH must be set to write tiles")
        num_irows = self.GetField("ImageLength")
        if num_irows is None:
            raise ValueError("TIFFTAG_IMAGELENGTH must be set to write tiles")
        num_icols = self.GetField("ImageWidth")
        if num_icols is None:
            raise ValueError("TIFFTAG_TILEWIDTH must be set to write tiles")

        if arr.shape[0] != num_irows or arr.shape[1] != num_icols:
            raise ValueError("Input array %r must have same shape as image tags %r" % (arr.shape,(num_irows,num_icols)))

        status = 1
        # Rows
        for i in range(0, num_irows, num_trows):
            # Cols
            for j in range(0, num_icols, num_tcols):
                # If we are over the edge of the image, use 0 as fill
                if ((i + num_trows) > num_irows) or ((j + num_tcols) > num_icols):
                    x = np.zeros((num_trows, num_tcols), dtype=np.uint8)
                    x[:num_irows-i,:num_icols-j] = arr[i:i+num_trows, j:j+num_tcols]
                else:
                    x = arr[i:i+num_trows,j:j+num_tcols]

                x = np.ascontiguousarray(x)
                log.debug("Writing tile at x: %d, y: %d" % (j,i))
                r = libtiff.TIFFWriteTile(self, x.ctypes.data, j, i, 0, 0)
                status = status & r.value

        return status

    def iter_images(self, verbose=False):
        """ Iterator of all images in a TIFF file.
        """
        yield self.read_image(verbose=verbose)
        if not self.LastDirectory():
            while 1:
                self.ReadDirectory()
                yield self.read_image(verbose=verbose)
                if self.LastDirectory():
                    break

    def __del__(self):
        self.close()

    @debug
    def FileName(self): return libtiff.TIFFFileName(self)
    @debug
    def CurrentRow(self): return libtiff.TIFFCurrentRow(self)
    @debug
    def CurrentStrip(self): return libtiff.TIFFCurrentStrip(self)
    @debug
    def CurrentTile(self): return libtiff.TIFFCurrentTile(self)
    @debug
    def CurrentDirectory(self): return libtiff.TIFFCurrentDirectory(self)
    @debug
    def LastDirectory(self): return libtiff.TIFFLastDirectory(self)
    @debug
    def ReadDirectory(self): return libtiff.TIFFReadDirectory(self)
    @debug
    def WriteDirectory(self): 
        r = libtiff.TIFFWriteDirectory(self)
        assert r==1, `r`
    @debug
    def SetDirectory(self, dirnum): return libtiff.TIFFSetDirectory(self, dirnum)
    @debug
    def Fileno(self): return libtiff.TIFFFileno(self)
    @debug
    def GetMode(self): return libtiff.TIFFGetMode(self)
    @debug
    def IsTiled(self): return libtiff.TIFFIsTiled(self)
    @debug
    def IsByteSwapped(self): return libtiff.TIFFIsByteSwapped(self)
    @debug
    def IsUpSampled(self): return libtiff.TIFFIsUpSampled(self)
    @debug
    def IsMSB2LSB(self): return libtiff.TIFFIsMSB2LSB(self)
    @debug
    def NumberOfStrips(self): return libtiff.TIFFNumberOfStrips(self).value

    #@debug
    def ReadRawStrip(self, strip, buf, size): 
        return libtiff.TIFFReadRawStrip(self, strip, buf, size).value
    def ReadEncodedStrip(self, strip, buf, size): 
        return libtiff.TIFFReadEncodedStrip(self, strip, buf, size).value

    def StripSize(self): 
        return libtiff.TIFFStripSize(self).value
    def RawStripSize(self, strip): 
        return libtiff.TIFFStripSize(self, strip).value

    @debug
    def WriteRawStrip(self, strip, buf, size): 
        r = libtiff.TIFFWriteRawStrip(self, strip, buf, size)
        assert r.value==size,`r.value, size`

    @debug
    def WriteEncodedStrip(self, strip, buf, size): 
        r = libtiff.TIFFWriteEncodedStrip(self, strip, buf, size)
        assert r.value==size,`r.value, size`

    closed = False
    def close(self, libtiff=libtiff): 
        if not self.closed and self.value is not None:
            libtiff.TIFFClose(self)
            self.closed = True
        return
    #def (self): return libtiff.TIFF(self)

    @debug
    def GetField(self, tag, ignore_undefined_tag=True, count=None):
        """ Return TIFF field value with tag.

        tag can be numeric constant TIFFTAG_<tagname> or a
        string containing <tagname>.
        """
        if tag in ['PixelSizeX', 'PixelSizeY', 'RelativeTime']:
            descr = self.GetField('ImageDescription')
            if not descr:
                return
            i = descr.find (tag)
            if i==-1:
                return
            value = eval(descr[i+len (tag):].lstrip().split()[0])
            return value

        if isinstance(tag, str):
            tag = eval('TIFFTAG_' + tag.upper())

        t = tifftags.get(tag)
        if t is None:
            if not ignore_undefined_tag:
                print 'Warning: no tag %r defined' % (tag)
            return
        data_type, convert = t

        if tag == TIFFTAG_COLORMAP:
            bps = self.GetField("BitsPerSample")
            if bps is None:
                log.warning("BitsPerSample is required to get ColorMap, assuming 8 bps...")
                bps = 8
            num_cmap_elems = 1 << bps
            data_type = data_type * num_cmap_elems
            pdt = ctypes.POINTER(data_type)
            rdata = pdt()
            gdata = pdt()
            bdata = pdt()
            rdata_ptr = ctypes.byref(rdata)
            gdata_ptr = ctypes.byref(gdata)
            bdata_ptr = ctypes.byref(bdata)

            # ignore count, it's not used for colormap
            libtiff.TIFFGetField.argtypes = libtiff.TIFFGetField.argtypes[:2] + [ctypes.c_void_p]*3
            r = libtiff.TIFFGetField(self, tag, rdata_ptr, gdata_ptr, bdata_ptr)
            data = (rdata,gdata,bdata)
        else:
            if hasattr(data_type, "_length_"):
                pdt = ctypes.POINTER(data_type)
                data = pdt()
                data_ptr = ctypes.byref(data)
            else:
                data = data_type()
                data_ptr = ctypes.byref(data)

            if count is None:
                libtiff.TIFFGetField.argtypes = libtiff.TIFFGetField.argtypes[:2] + [ctypes.c_void_p]
                r = libtiff.TIFFGetField(self, tag, data_ptr)
            else:
                libtiff.TIFFGetField.argtypes = libtiff.TIFFGetField.argtypes[:2] + [ctypes.c_uint, ctypes.c_void_p]
                r = libtiff.TIFFGetField(self, tag, count, data_ptr)

        if not r: # tag not defined for current directory
            if not ignore_undefined_tag:
                print 'Warning: tag %r not defined in currect directory' % (tag)
            return None

        return convert(data)

    #@debug
    def SetField (self, tag, value, count=None):
        """ Set TIFF field value with tag.

        tag can be numeric constant TIFFTAG_<tagname> or a
        string containing <tagname>.
        """

        if isinstance(tag, str):
            tag = eval('TIFFTAG_' + tag.upper())

        t = tifftags.get(tag)
        if t is None:
            print 'Warning: no tag %r defined' % (tag)
            return

        data_type, convert = t
        if data_type == ctypes.c_float:
            data_type = ctypes.c_double


        if tag == TIFFTAG_COLORMAP:
            # ColorMap passes 3 values each a c_uint16 pointer
            try:
                if len(value) != 3:
                    log.error("TIFFTAG_COLORMAP expects 3 uint16* arrays (not %d) as a list/tuple of lists" % len(value))
                    r_arr,g_arr,b_arr = None,None,None
                else:
                    r_arr,g_arr,b_arr = value
            except TypeError:
                log.error("TIFFTAG_COLORMAP expects 3 uint16* arrays as a list/tuple of lists")
                r_arr,g_arr,b_arr = None,None,None

            if r_arr is None:
                return

            bps = self.GetField("BitsPerSample")
            if bps is None:
                log.warning("BitsPerSample is required to get ColorMap, assuming 8 bps...")
                bps = 8
            num_cmap_elems = 1 << bps
            data_type = data_type * num_cmap_elems

            r_ptr = data_type(*r_arr)
            g_ptr = data_type(*g_arr)
            b_ptr = data_type(*b_arr)

            libtiff.TIFFSetField.argtypes = libtiff.TIFFSetField.argtypes[:2] + [ctypes.POINTER(data_type)]*3
            r = libtiff.TIFFSetField(self, tag, r_ptr, g_ptr, b_ptr)
        else:
            try:
                # Value is an iterable
                value_length = len(value)
                data = data_type(*value)
            except TypeError:
                # Value is not an iterable
                data = data_type(value)

            if count is None:
                libtiff.TIFFSetField.argtypes = libtiff.TIFFSetField.argtypes[:2] + [data_type]
                r = libtiff.TIFFSetField(self, tag, data)
            else:
                libtiff.TIFFSetField.argtypes = libtiff.TIFFSetField.argtypes[:2] + [ctypes.c_uint, data_type]
                r = libtiff.TIFFSetField(self, tag, count, data)

        return r

    def info(self):
        """ Return a string containing <tag name: field value> map.
        """
        l = []
        l.append ('FileName: %s' % (self.FileName()))
        for tagname in ['Artist', 'CopyRight', 'DateTime', 'DocumentName',
                        'HostComputer', 'ImageDescription', 'InkNames',
                        'Make', 'Model', 'PageName', 'Software', 'TargetPrinter',
                        'BadFaxLines', 'ConsecutiveBadFaxLines',
                        'Group3Options', 'Group4Options',
                        'ImageDepth', 'ImageWidth', 'ImageLength',
                        'RowsPerStrip', 'SubFileType',
                        'TileDepth', 'TileLength', 'TileWidth',
                        'StripByteCounts', 'StripOffSets',
                        'TileByteCounts', 'TileOffSets',
                        'BitsPerSample', 'CleanFaxData', 'Compression',
                        'DataType', 'FillOrder', 'InkSet', 'Matteing',
                        'MaxSampleValue', 'MinSampleValue', 'Orientation',
                        'PhotoMetric', 'PlanarConfig', 'Predictor', 
                        'ResolutionUnit', 'SampleFormat', 'YCBCRPositioning',
                        'JPEGQuality', 'JPEGColorMode', 'JPEGTablesMode',
                        'FaxMode', 'SMaxSampleValue', 'SMinSampleValue',
                        #'Stonits',
                        'XPosition', 'YPosition', 'XResolution', 'YResolution',
                        'PrimaryChromaticities', 'ReferenceBlackWhite',
                        'WhitePoint', 'YCBCRCoefficients',
                        'PixelSizeX','PixelSizeY', 'RelativeTime',
                        'CZ_LSMInfo'
                        ]:
            v = self.GetField(tagname)
            if v:
                if isinstance (v, int):
                    v = define_to_name_map.get(tagname, {}).get(v, v)
                l.append('%s: %s' % (tagname, v))
                if tagname=='CZ_LSMInfo':
                    print CZ_LSMInfo(self)
        return '\n'.join(l)
        
    def copy(self, filename, **kws):
        """ Copy opened TIFF file to a new file.

        Use keyword arguments to redefine tag values.

        Parameters
        ----------
        filename : str
          Specify the name of file where TIFF file is copied to.
        compression : {'none', 'lzw', 'deflate', ...}
          Specify compression scheme.
        bitspersample : {8,16,32,64,128,256}
          Specify bit size of a sample.
        sampleformat : {'uint', 'int', 'float', 'complex'}
          Specify sample format.
        """
        other = TIFF.open(filename, mode='w')
        define_rewrite = {}
        for name, value in kws.items():
            define = TIFF.get_tag_define(name)
            assert define is not None
            if name=='compression':
                value = TIFF._fix_compression(value)
            if name=='sampleformat':
                value = TIFF._fix_sampleformat(value)
            define_rewrite[define] = value
        name_define_list = name_to_define_map['TiffTag'].items()
        self.SetDirectory(0)
        self.ReadDirectory()
        while 1:
            other.SetDirectory(self.CurrentDirectory())
            bits = self.GetField('BitsPerSample')
            sample_format = self.GetField('SampleFormat')
            assert bits >=8, `bits, sample_format, dtype`
            itemsize = bits // 8
            dtype = self.get_numpy_type(bits, sample_format)
            for name, define in name_define_list:
                orig_value = self.GetField(define)
                if orig_value is None and define not in define_rewrite:
                    continue
                if name.endswith('OFFSETS') or name.endswith('BYTECOUNTS'):
                    continue
                if define in define_rewrite:
                    value = define_rewrite[define]
                else:
                    value = orig_value
                if value is None:
                    continue
                other.SetField(define, value)
            new_bits = other.GetField('BitsPerSample')
            new_sample_format = other.GetField('SampleFormat')
            new_dtype = other.get_numpy_type(new_bits, new_sample_format)
            assert new_bits >=8, `new_bits, new_sample_format, new_dtype`
            new_itemsize = new_bits // 8
            strip_size = self.StripSize()
            new_strip_size = self.StripSize()
            buf = np.zeros(strip_size // itemsize, dtype)
            for strip in range(self.NumberOfStrips()):
                elem = self.ReadEncodedStrip(strip, buf.ctypes.data, strip_size)
                if elem>0:
                    new_buf = buf.astype(new_dtype)
                    other.WriteEncodedStrip(strip, new_buf.ctypes.data, (elem * new_itemsize)//itemsize)
            self.ReadDirectory()
            if self.LastDirectory ():
                break
        other.close ()

import struct
import numpy
class CZ_LSMInfo:

    def __init__(self, tiff):
        self.tiff = tiff
        self.filename = tiff.FileName()
        self.offset = tiff.GetField(TIFFTAG_CZ_LSMINFO)
        self.extract_info()

    def extract_info (self):
        if self.offset is None:
            return
        f = libtiff.TIFFFileno(self.tiff)
        fd = os.fdopen(f, 'r')
        pos = fd.tell()
        self.offset = self.tiff.GetField(TIFFTAG_CZ_LSMINFO)
        print os.lseek(f, 0, 1)

        print pos
        #print libtiff.TIFFSeekProc(self.tiff, 0, 1)
        fd.seek(0)
        print struct.unpack ('HH', fd.read (4))
        print struct.unpack('I',fd.read (4))
        print struct.unpack('H',fd.read (2))
        fd.seek(self.offset)
        d = [('magic_number', 'i4'),
             ('structure_size', 'i4')]
        print pos, numpy.rec.fromfile(fd, d, 1)
        fd.seek(pos)
        #print hex (struct.unpack('I', fd.read (4))[0])
        #fd.close()


    def __str__ (self):
        return '%s: %s' % (self.filename, self.offset)

libtiff.TIFFOpen.restype = TIFF
libtiff.TIFFOpen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]


libtiff.TIFFFileName.restype = ctypes.c_char_p
libtiff.TIFFFileName.argtypes = [TIFF]

libtiff.TIFFFileno.restype = ctypes.c_int
libtiff.TIFFFileno.argtypes = [TIFF]

libtiff.TIFFCurrentRow.restype = ctypes.c_uint32
libtiff.TIFFCurrentRow.argtypes = [TIFF]

libtiff.TIFFCurrentStrip.restype = c_tstrip_t
libtiff.TIFFCurrentStrip.argtypes = [TIFF]

libtiff.TIFFCurrentTile.restype = c_ttile_t
libtiff.TIFFCurrentTile.argtypes = [TIFF]

libtiff.TIFFCurrentDirectory.restype = c_tdir_t
libtiff.TIFFCurrentDirectory.argtypes = [TIFF]

libtiff.TIFFLastDirectory.restype = ctypes.c_int
libtiff.TIFFLastDirectory.argtypes = [TIFF]

libtiff.TIFFReadDirectory.restype = ctypes.c_int
libtiff.TIFFReadDirectory.argtypes = [TIFF]

libtiff.TIFFWriteDirectory.restype = ctypes.c_int
libtiff.TIFFWriteDirectory.argtypes = [TIFF]

libtiff.TIFFSetDirectory.restype = ctypes.c_int
libtiff.TIFFSetDirectory.argtypes = [TIFF, c_tdir_t]

libtiff.TIFFFileno.restype = ctypes.c_int
libtiff.TIFFFileno.argtypes = [TIFF]

libtiff.TIFFGetMode.restype = ctypes.c_int
libtiff.TIFFGetMode.argtypes = [TIFF]

libtiff.TIFFIsTiled.restype = ctypes.c_int
libtiff.TIFFIsTiled.argtypes = [TIFF]

libtiff.TIFFIsByteSwapped.restype = ctypes.c_int
libtiff.TIFFIsByteSwapped.argtypes = [TIFF]

libtiff.TIFFIsUpSampled.restype = ctypes.c_int
libtiff.TIFFIsUpSampled.argtypes = [TIFF]

libtiff.TIFFIsMSB2LSB.restype = ctypes.c_int
libtiff.TIFFIsMSB2LSB.argtypes = [TIFF]

libtiff.TIFFGetField.restype = ctypes.c_int
libtiff.TIFFGetField.argtypes = [TIFF, c_ttag_t, ctypes.c_void_p]

libtiff.TIFFSetField.restype = ctypes.c_int
libtiff.TIFFSetField.argtypes = [TIFF, c_ttag_t, ctypes.c_void_p] # last item is reset in TIFF.SetField method

libtiff.TIFFNumberOfStrips.restype = c_tstrip_t
libtiff.TIFFNumberOfStrips.argtypes = [TIFF]

libtiff.TIFFReadRawStrip.restype = c_tsize_t
libtiff.TIFFReadRawStrip.argtypes = [TIFF, c_tstrip_t, c_tdata_t, c_tsize_t]

libtiff.TIFFWriteRawStrip.restype = c_tsize_t
libtiff.TIFFWriteRawStrip.argtypes = [TIFF, c_tstrip_t, c_tdata_t, c_tsize_t]

libtiff.TIFFReadEncodedStrip.restype = c_tsize_t
libtiff.TIFFReadEncodedStrip.argtypes = [TIFF, c_tstrip_t, c_tdata_t, c_tsize_t]

libtiff.TIFFWriteEncodedStrip.restype = c_tsize_t
libtiff.TIFFWriteEncodedStrip.argtypes = [TIFF, c_tstrip_t, c_tdata_t, c_tsize_t]

libtiff.TIFFStripSize.restype = c_tsize_t
libtiff.TIFFStripSize.argtypes = [TIFF]

libtiff.TIFFRawStripSize.restype = c_tsize_t
libtiff.TIFFRawStripSize.argtypes = [TIFF, c_tstrip_t]

# For adding custom tags (must be void pointer otherwise callback seg faults
libtiff.TIFFMergeFieldInfo.restype = ctypes.c_int32
libtiff.TIFFMergeFieldInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]

# Tile Support
# TODO:
#   TIFFTileRowSize64
#   TIFFTileSize64
#   TIFFVTileSize
#   TIFFVTileSize64
libtiff.TIFFTileRowSize.restype = c_tsize_t
libtiff.TIFFTileRowSize.argtypes = [TIFF]

libtiff.TIFFTileSize.restype = c_tsize_t
libtiff.TIFFTileSize.argtypes = [TIFF]

libtiff.TIFFComputeTile.restype = c_ttile_t
libtiff.TIFFComputeTile.argtypes = [TIFF, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, c_tsample_t]

libtiff.TIFFCheckTile.restype = ctypes.c_int
libtiff.TIFFCheckTile.argtypes = [TIFF, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, c_tsample_t]

libtiff.TIFFNumberOfTiles.restype = c_ttile_t
libtiff.TIFFNumberOfTiles.argtypes = [TIFF]

libtiff.TIFFReadTile.restype = c_tsize_t
libtiff.TIFFReadTile.argtypes = [TIFF, c_tdata_t, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, c_tsample_t]

libtiff.TIFFWriteTile.restype = c_tsize_t
libtiff.TIFFWriteTile.argtypes = [TIFF, c_tdata_t, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, c_tsample_t]

libtiff.TIFFReadEncodedTile.restype = ctypes.c_int
libtiff.TIFFReadEncodedTile.argtypes = [TIFF, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong]

libtiff.TIFFReadRawTile.restype = c_tsize_t
libtiff.TIFFReadRawTile.argtypes = [TIFF, c_ttile_t, c_tdata_t, c_tsize_t]

libtiff.TIFFReadRGBATile.restype = ctypes.c_int
libtiff.TIFFReadRGBATile.argtypes = [TIFF, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]

libtiff.TIFFWriteEncodedTile.restype = c_tsize_t
libtiff.TIFFWriteEncodedTile.argtypes = [TIFF, c_ttile_t, c_tdata_t, c_tsize_t]

libtiff.TIFFWriteRawTile.restype = c_tsize_t
libtiff.TIFFWriteRawTile.argtypes = [TIFF, c_ttile_t, c_tdata_t, c_tsize_t]

libtiff.TIFFDefaultTileSize.restype = None
libtiff.TIFFDefaultTileSize.argtypes = [TIFF, ctypes.c_uint32, ctypes.c_uint32]

libtiff.TIFFClose.restype = None
libtiff.TIFFClose.argtypes = [TIFF]

# Support for TIFF warning and error handlers:
TIFFWarningHandler = ctypes.CFUNCTYPE(None,
                                      ctypes.c_char_p, # Module
                                      ctypes.c_char_p, # Format
                                      ctypes.c_void_p) # va_list
TIFFErrorHandler = ctypes.CFUNCTYPE(None,
                                      ctypes.c_char_p, # Module
                                      ctypes.c_char_p, # Format
                                      ctypes.c_void_p) # va_list

# This has to be at module scope so it is not garbage-collected
_null_warning_handler = TIFFWarningHandler(lambda module, fmt, va_list: None)
_null_error_handler = TIFFErrorHandler(lambda module, fmt, va_list: None)

def suppress_warnings():
    libtiff.TIFFSetWarningHandler(_null_warning_handler)
def suppress_errors():
    libtiff.TIFFSetErrorHandler(_null_error_handler)

def _test_read(filename=None):
    import sys
    import time
    if filename is None:
        if len(sys.argv) != 2:
            print 'Run `libtiff.py <filename>` for testing.'
            return
        filename = sys.argv[1]
    print 'Trying to open', filename, '...',
    tiff = TIFF.open(filename)
    print 'ok'
    print 'Trying to show info ...\n','-'*10
    print tiff.info()
    print '-'*10,'ok'
    print 'Trying show images ...'
    t = time.time ()
    i = 0
    for image in tiff.iter_images(verbose=True):
        #print image.min(), image.max(), image.mean ()
        i += 1
    print '\tok',(time.time ()-t)*1e3,'ms',i,'images'



def _test_write():
    tiff = TIFF.open('/tmp/libtiff_test_write.tiff', mode='w')
    arr = np.zeros ((5,6), np.uint32)
    for i in range(arr.shape[0]):
        for j in range (arr.shape[1]):
            arr[i,j] = i + 10*j
    print arr
    tiff.write_image(arr)
    del tiff

def _test_write_float():
    tiff = TIFF.open('/tmp/libtiff_test_write.tiff', mode='w')
    arr = np.zeros ((5,6), np.float64)
    for i in range(arr.shape[0]):
        for j in range (arr.shape[1]):
            arr[i,j] = i + 10*j
    print arr
    tiff.write_image(arr)
    del tiff

    tiff = TIFF.open('/tmp/libtiff_test_write.tiff', mode='r')
    print tiff.info()
    arr2 = tiff.read_image()
    print arr2

def _test_copy():
    tiff = TIFF.open('/tmp/libtiff_test_compression.tiff', mode='w')
    arr = np.zeros ((5,6), np.uint32)
    for i in range(arr.shape[0]):
        for j in range (arr.shape[1]):
            arr[i,j] = 1+i + 10*j
    #from scipy.stats import poisson
    #arr = poisson.rvs (arr)
    tiff.SetField('ImageDescription', 'Hey\nyou')
    tiff.write_image(arr, compression='lzw')
    del tiff

    tiff = TIFF.open('/tmp/libtiff_test_compression.tiff', mode='r')
    print tiff.info()
    arr2 = tiff.read_image()

    assert (arr==arr2).all(),'arrays not equal'

    for compression in ['none','lzw','deflate']:
        for sampleformat in ['int','uint','float']:
            for bitspersample in [256,128,64,32,16,8]:
                if sampleformat=='float' and (bitspersample < 32 or bitspersample > 128):
                    continue
                if sampleformat in ['int','uint'] and bitspersample > 64:
                    continue
                #print compression, sampleformat, bitspersample
                tiff.copy ('/tmp/libtiff_test_copy2.tiff', 
                           compression=compression,
                           imagedescription='hoo',
                           sampleformat=sampleformat,
                           bitspersample=bitspersample)
                tiff2 = TIFF.open('/tmp/libtiff_test_copy2.tiff', mode='r')
                arr3 = tiff2.read_image()
                assert (arr==arr3).all(),'arrays not equal %r' % ((compression, sampleformat, bitspersample),)
    print 'test copy ok'

def default_tile_tags():
    a = TIFF.open("test.tif", "w")
    a.SetField("ARTIST", "David Hoese")
    a.SetField("TILEWIDTH", 512)
    a.SetField("TILELENGTH", 512)
    a.SetField("ImageWidth", 2500)
    a.SetField("ImageLength", 2500)
    a.SetField("BITspersample", 8)
    a.SetField("compression", 1)
    a.SetField("PHOTOMETRIC", PHOTOMETRIC_MINISBLACK)
    #a.SetField("ORIENTATION", ORIENTATION_BOTLEFT)
    a.SetField("ORIENTATION", ORIENTATION_TOPLEFT)
    #a.SetField("ORIENTATION", ORIENTATION_LEFTTOP)
    a.SetField("Planarconfig", PLANARCONFIG_CONTIG)
    a.SetField("sampleformat", SAMPLEFORMAT_UINT)

    #libtiff.TIFFWriteTile.argtypes = libtiff.TIFFWriteTile.argtypes[:-1]
    arr = np.tile(range(500), (2500,5)).astype(np.uint8)
    num_trows = 512
    num_tcols = 512
    num_irows = 2500
    num_icols = 2500
    # Rows
    #for i in range(0, num_irows, num_trows):
    for i in range(0, num_irows, num_trows):
        # Cols
        for j in range(0, num_icols, num_tcols):
            if ((i + num_trows) > num_irows) or ((j + num_tcols) > num_icols):
                x = np.zeros((num_trows, num_tcols), dtype=np.uint8)
                tmp = arr[i : i + num_trows, j : j + num_tcols]
                print "Temp shape ",tmp.shape
                x[:num_irows-i,:num_icols-j] = tmp
                #x[:tmp.shape[0],512-tmp.shape[1]:512] = tmp
                #if i + num_trows > num_irows: x = tmp
                #else:
                #    x = np.zeros((tmp.shape[0],tmp.shape[1]/4))
                #    #x[0,:32] = tmp[0,:32]
                #    x[:,0] = tmp[0,0]
                #    print x[0]
                #x = tmp
                #print x[0]
                #print x[15]
            else:
                x = arr[i:i+num_trows,j:j+num_tcols]
            #x = np.ascontiguousarray(arr[j:j+num_tcols,i:i+num_trows])
            #x = np.ascontiguousarray(arr[i:i+num_trows,j:j+num_tcols])
            x = np.ascontiguousarray(x)
            print i,j,
            print x.shape,
            print x[0,-1]
            #libtiff.TIFFWriteRawTile(a, libtiff.TIFFComputeTile(a, j, i, 0, 0), x.ctypes.data, x.shape[0]*x.shape[1])
            libtiff.TIFFWriteTile(a, x.ctypes.data, j, i, 0, 0)

    #libtiff.TIFFWriteTile(a, first_tile.ctypes.data, 512, 0, 0)
    #libtiff.TIFFWriteTile(a, first_tile.ctypes.data, 1024, 0, 0)
    #libtiff.TIFFWriteTile(a, first_tile.ctypes.data, 1536, 0, 0)
    #libtiff.TIFFWriteTile(a, last_tile.ctypes.data, 2048, 0, 0)
    #libtiff.TIFFWriteTile(a, first_tile.ctypes.data, 0, 512, 0)


if __name__=='__main__':
    #_test_write_float()
    #_test_write()
    #_test_read()
    #_test_copy()
    default_tile_tags()
    
