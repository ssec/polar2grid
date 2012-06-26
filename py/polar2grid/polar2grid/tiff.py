import sys
import ctypes
import numpy
from libtiff import libtiff_ctypes
from libtiff import TIFF

# MACROS/defines
FIELD_CUSTOM=65

### Redefinition of C structs ###
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

tiff2ctypes = {
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

class TIFFExtender(object):
    def __init__(self, new_tag_list):
        self._ParentExtender = None
        self.new_tag_list = new_tag_list
        def extender_pyfunc(tiff_struct):
            libtiff_ctypes.libtiff.TIFFMergeFieldInfo.restype = ctypes.c_int32
            libtiff_ctypes.libtiff.TIFFMergeFieldInfo.argtypes = [ctypes.c_void_p, type(new_tag_list), ctypes.c_uint32]
            libtiff_ctypes.libtiff.TIFFMergeFieldInfo(tiff_struct, self.new_tag_list, len(self.new_tag_list))

            if self._ParentExtender:
                self._ParentExtender(tiff_struct)

            # Just make being a void function more obvious
            return

        # ctypes callback function prototype (return void, arguments void pointer)
        self.EXT_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        # ctypes callback function instance
        self.EXT_FUNC_INST = self.EXT_FUNC(extender_pyfunc)

        self._ParentExtender = libtiff_ctypes.libtiff.TIFFSetTagExtender(self.EXT_FUNC_INST)

# Utility functions
def tag_array(num_tags):
    return TIFFFieldInfo * num_tags

def add_tags(tag_list):
    for field_info in tag_list:
        setattr(libtiff_ctypes, "TIFFTAG_" + str(field_info.field_name).upper(), field_info.field_tag)
        libtiff_ctypes.tifftags[field_info.field_tag] = (tiff2ctypes[field_info.field_type], lambda d:d.value)

    return TIFFExtender(tag_list)

### DEFINE NEW TAGS ###

# Define Tag Numbers and total number of tags
NUM_NINJO_TAGS = 4
NINJO_BYTE = 40000
NINJO_STR = 40001
NINJO_UINT16 = 40002
NINJO_UINT32 = 40003

# Define a C structure that says how each tag should be used
# XXX: The read and write counts shouldn't all need to be -1, but otherwise libtiff gives a warning
ninjo_tags = tag_array(NUM_NINJO_TAGS)
ninjo_tags_inst = ninjo_tags(
        TIFFFieldInfo(NINJO_BYTE, -1, -1, TIFFDataType.TIFF_BYTE, FIELD_CUSTOM, True, True, "NinjoTestbyte"),
        TIFFFieldInfo(NINJO_UINT32, -1, -1, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, True, "NinjoTestuint32"),
        TIFFFieldInfo(NINJO_UINT16, -1, -1, TIFFDataType.TIFF_SHORT, FIELD_CUSTOM, True, True, "NinjoTestuint16"),
        TIFFFieldInfo(NINJO_STR, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "NinjoTeststr")
        )

# Tell the python library about these new tags
ninjo_extender = add_tags(ninjo_tags_inst)

### TEST FUNCTIONS ###

def test_write():
    a = TIFF.open("test.tif", "w")

    a.SetField("ARTIST", "DAVID HOESE")
    a.SetField("NINJOTESTBYTE", 42)
    a.SetField("NINJOTESTUINT16", 42)
    a.SetField("NINJOTESTUINT32", 42)
    a.SetField("NINJOTESTSTR", "FAKE")
    a.SetField("XPOSITION", 42.0)

    arr = numpy.ones((512,512), dtype=numpy.uint8)
    arr[:,:] = 255
    a.write_image(arr)

    print "SUCCESS"

def test_read():
    a = TIFF.open("test.tif", "r")

    print a.read_image()
    print a.GetField("XPOSITION")
    print a.GetField("ARTIST")
    print a.GetField("NINJOTESTBYTE")
    print a.GetField("NINJOTESTUINT16")
    print a.GetField("NINJOTESTUINT32")
    print a.GetField("NINJOTESTSTR")

def main():
    test_write()
    test_read()

if __name__ == "__main__":
    sys.exit(main())

