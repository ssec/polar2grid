import sys
import ctypes
import numpy
from polar2grid import libtiff
TIFFDataType = libtiff.TIFFDataType
TIFFFieldInfo = libtiff.TIFFFieldInfo
ttype2ctype = libtiff.ttype2ctype

# MACROS/defines
FIELD_CUSTOM=65

class TIFFExtender(object):
    def __init__(self, new_tag_list):
        self._ParentExtender = None
        self.new_tag_list = new_tag_list
        def extender_pyfunc(tiff_struct):
            libtiff.libtiff.TIFFMergeFieldInfo(tiff_struct, self.new_tag_list, len(self.new_tag_list))

            if self._ParentExtender:
                self._ParentExtender(tiff_struct)

            # Just make being a void function more obvious
            return

        # ctypes callback function prototype (return void, arguments void pointer)
        self.EXT_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        # ctypes callback function instance
        self.EXT_FUNC_INST = self.EXT_FUNC(extender_pyfunc)

        libtiff.libtiff.TIFFSetTagExtender.restype = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        self._ParentExtender = libtiff.libtiff.TIFFSetTagExtender(self.EXT_FUNC_INST)

# Utility functions
def add_tags(tag_list):
    for field_info in tag_list:
        setattr(libtiff, "TIFFTAG_" + str(field_info.field_name).upper(), field_info.field_tag)
        if field_info.field_writecount > 1 and field_info.field_type != TIFFDataType.TIFF_ASCII:
            libtiff.tifftags[field_info.field_tag] = (ttype2ctype[field_info.field_type]*field_info.field_writecount, lambda d:d.contents[:])
        else:
            libtiff.tifftags[field_info.field_tag] = (ttype2ctype[field_info.field_type], lambda d:d.value)

    return TIFFExtender(tag_list)

def write_list(list_elems, c_type):
    return (c_type * len(list_elems))(*list_elems)

def read_list(first_elem, num_elems, dtype=numpy.float32):
    return list(numpy.frombuffer(numpy.core.multiarray.int_asbuffer(ctypes.addressof(first_elem), ctypes.sizeof(first_elem)*num_elems), dtype))

### TEST FUNCTIONS ###

def test_write():
    a = libtiff.TIFF.open("test.tif", "w")

    a.SetField("ARTIST", "DAVID HOESE")
    a.SetField("NINJOTESTBYTE", 42)
    a.SetField("NINJOTESTSTR", "FAKE")
    a.SetField("NINJOTESTUINT16", 42)
    a.SetField("NINJOTESTUINT32", (1,2,3,4,5,6,7,8,9,10))
    #a.SetField("NINJOTESTUINT32", write_list((1,2,3,4,5,6,7,8,9,10), ctypes.c_uint32))
    a.SetField("XPOSITION", 42.0)
    a.SetField("PRIMARYCHROMATICITIES", (1.0, 2, 3, 4, 5, 6))
    #a.SetField("PRIMARYCHROMATICITIES", write_list((1.0, 2, 3, 4, 5, 6), ctypes.c_float))

    arr = numpy.ones((512,512), dtype=numpy.uint8)
    arr[:,:] = 255
    a.write_image(arr)

    print "SUCCESS"

def test_read():
    a = libtiff.TIFF.open("test.tif", "r")

    print a.read_image()
    print a.GetField("XPOSITION")
    print a.GetField("ARTIST")
    print a.GetField("NINJOTESTBYTE")
    print a.GetField("NINJOTESTUINT16")
    print a.GetField("NINJOTESTUINT32")
    #print read_list(a.GetField("NINJOTESTUINT32"), 10, dtype=numpy.uint32)
    print a.GetField("NINJOTESTSTR")
    print a.GetField("PRIMARYCHROMATICITIES")
    #print read_list(a.GetField("PRIMARYCHROMATICITIES"), 6, dtype=numpy.float32)

def main():
    # Define a C structure that says how each tag should be used
    test_tags = [
        TIFFFieldInfo(40100, 1, 1, TIFFDataType.TIFF_BYTE, FIELD_CUSTOM, True, False, "NinjoTestbyte"),
        TIFFFieldInfo(40103, 10, 10, TIFFDataType.TIFF_LONG, FIELD_CUSTOM, True, False, "NinjoTestuint32"),
        TIFFFieldInfo(40102, 1, 1, TIFFDataType.TIFF_SHORT, FIELD_CUSTOM, True, False, "NinjoTestuint16"),
        TIFFFieldInfo(40101, -1, -1, TIFFDataType.TIFF_ASCII, FIELD_CUSTOM, True, False, "NinjoTeststr")
        ]
    test_tags_struct = libtiff.tag_array(len(test_tags))(*test_tags)

    # Tell the python library about these new tags
    test_extender = add_tags(test_tags_struct)
    test_write()
    test_read()

if __name__ == "__main__":
    sys.exit(main())

