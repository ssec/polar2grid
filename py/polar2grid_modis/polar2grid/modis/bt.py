#!/usr/bin/env python
# encoding: utf-8
"""
Purpose: convert MODIS to Brightness Temp
Created by rayg Aug 2012.

:author:       Eva Schiffer (evas)
:author:       Ray Garcia (rayg)
:contact:      evas@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2013 University of Wisconsin SSEC. All rights reserved.
:date:         Jan 2013
:license:      GNU GPLv3

Copyright (C) 2013 Space Science and Engineering Center (SSEC),
 University of Wisconsin-Madison.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

This file is part of the polar2grid software package. Polar2grid takes
satellite observation data, remaps it, and writes it to a file format for
input into another program.
Documentation: http://www.ssec.wisc.edu/software/polar2grid/

    Written by David Hoese    January 2013
    University of Wisconsin-Madison 
    Space Science and Engineering Center
    1225 West Dayton Street
    Madison, WI  53706
    david.hoese@ssec.wisc.edu

"""
__docformat__ = "restructuredtext en"

# copypasta! 
BT_FORTRAN = """
      REAL FUNCTION MODIS_BRIGHT_SHIFT(RAD, BAND, UNITS)

C-----------------------------------------------------------------------
C!F77
C
C!DESCRIPTION:
C    Compute brightness temperature for a MODIS infrared band
C    on Terra or Aqua.
C
C    Spectral responses for each IR detector were obtained from MCST:
C    ftp://ftp.mcst.ssai.biz/pub/permanent/MCST in directories
C    PFM_L1B_LUT_4-30-99 (Terra) and FM1_RSR_LUT_07-10-01 (Aqua).
C
C    An average spectral response for all detectors in each band was
C    computed. The detector-averaged spectral response data were used
C    to compute the effective central wavenumbers and temperature
C    correction coefficients included in this module.
C
C    NOTE: The plaform name ('Terra' or 'Aqua') is passed to this
C    function via the common block defined in 'platform_name.inc'.
C
C    NOTE: Aqua bands 27, 28, 34-36 use "shifted" central wave numbers.
C          See comments below.
C
C!INPUT PARAMETERS:
C    RAD (REAL)      Planck radiance (units are determined by UNITS)
C    BAND (LONG)     MODIS IR band number (20-25, 27-36)
C    UNITS (LONG)    Flag defining radiance units
C                    0 => milliWatts per square meter per
C                         steradian per inverse centimeter
C                    1 => Watts per square meter per
C                         steradian per micron
C
C!OUTPUT PARAMETERS:
C    MODIS_BRIGHT_SHIFT  Brightness temperature (Kelvin)
C                  Note that a value of -1.0 is returned if
C                  RAD .LE. 0.0, or BAND is not in range 20-25, 27-36.
C
C!REVISION HISTORY:
C    Liam.Gumley@ssec.wisc.edu
C    May 2010 SRF shifts are added to some Aqua bands (see Line 120-124)
C
C!TEAM-UNIQUE HEADER:
C    Developed by the MODIS Group, CIMSS/SSEC, UW-Madison.
C
C!END
C-----------------------------------------------------------------------

      IMPLICIT NONE

c ... Include files
      include 'platform_name.inc'
      
c ... Arguments
      real rad
      integer band, units

c ... Local variables
      real cwn_terra(16), tcs_terra(16), tci_terra(16)
      real cwn_aqua(16), tcs_aqua(16), tci_aqua(16)
      real cwn, tcs, tci
      integer index

c ... External functions
      real bright_m, brite_m
      external bright_m, brite_m
            
c ... Data statements

c-----------------------------------------------------------------------

c     TERRA MODIS DETECTOR-AVERAGED SPECTRAL RESPONSE
c     (LIAM GUMLEY 2003/06/05)

c     BAND 20 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 21 TEMPERATURE RANGE WAS  180.00 K TO  400.00 K
c     BAND 22 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 23 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 24 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 25 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 27 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 28 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 29 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 30 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 31 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 32 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 33 TEMPERATURE RANGE WAS  180.00 K TO  330.00 K
c     BAND 34 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 35 TEMPERATURE RANGE WAS  180.00 K TO  310.00 K
c     BAND 36 TEMPERATURE RANGE WAS  180.00 K TO  310.00 K

c     BANDS
c      20,  21,  22,  23,
c      24,  25,  27,  28,
c      29,  30,  31,  32,
c      33,  34,  35,  36,

c ... Effective central wavenumbers (inverse centimeters)
      data cwn_terra/
     &  2.641767E+03, 2.505274E+03, 2.518031E+03, 2.465422E+03,
     &  2.235812E+03, 2.200345E+03, 1.478026E+03, 1.362741E+03,
     &  1.173198E+03, 1.027703E+03, 9.081998E+02, 8.315149E+02,
     &  7.483224E+02, 7.309089E+02, 7.188677E+02, 7.045309E+02/

c ... Temperature correction slopes (no units)
      data tcs_terra/ 
     &  9.993487E-01, 9.998699E-01, 9.998604E-01, 9.998701E-01,
     &  9.998825E-01, 9.998849E-01, 9.994942E-01, 9.994937E-01,
     &  9.995643E-01, 9.997499E-01, 9.995880E-01, 9.997388E-01,
     &  9.999192E-01, 9.999171E-01, 9.999174E-01, 9.999264E-01/

c ... Temperature correction intercepts (Kelvin)
      data tci_terra/
     &  4.744530E-01, 9.091094E-02, 9.694298E-02, 8.856134E-02,
     &  7.287017E-02, 7.037161E-02, 2.177889E-01, 2.037728E-01,
     &  1.559624E-01, 7.989879E-02, 1.176660E-01, 6.856633E-02,
     &  1.903625E-02, 1.902709E-02, 1.859296E-02, 1.619453E-02/

c-----------------------------------------------------------------------

c     AQUA MODIS DETECTOR-AVERAGED SPECTRAL RESPONSE WITH SPECTRAL SHIFT
c     (LIAM GUMLEY 2005/02/21)
c     Band 27: +5.0 1/cm
c     Band 28: +2.0 1/cm
c     Band 34: +0.8 1/cm
c     Band 35: +0.8 1/cm
c     Band 36: +1.0 1/cm

c     BAND 20 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 21 TEMPERATURE RANGE WAS  180.00 K TO  400.00 K
c     BAND 22 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 23 TEMPERATURE RANGE WAS  180.00 K TO  350.00 K
c     BAND 24 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 25 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 27 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 28 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 29 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 30 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 31 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 32 TEMPERATURE RANGE WAS  180.00 K TO  340.00 K
c     BAND 33 TEMPERATURE RANGE WAS  180.00 K TO  330.00 K
c     BAND 34 TEMPERATURE RANGE WAS  180.00 K TO  320.00 K
c     BAND 35 TEMPERATURE RANGE WAS  180.00 K TO  310.00 K
c     BAND 36 TEMPERATURE RANGE WAS  180.00 K TO  310.00 K

c     BANDS
c       20,  21,  22,  23,
c       24,  25,  27,  28,
c       29,  30,  31,  32,
c       33,  34,  35,  36,

c ... Effective central wavenumbers (inverse centimeters)
      data cwn_aqua/
     &  2.647418E+03, 2.511763E+03, 2.517910E+03, 2.462446E+03,
     &  2.248296E+03, 2.209550E+03, 1.479292E+03, 1.363638E+03,
     &  1.169637E+03, 1.028715E+03, 9.076808E+02, 8.308397E+02,
     &  7.482977E+02, 7.315760E+02, 7.190090E+02, 7.045020E+02/

c ... Temperature correction slopes (no units)
      data tcs_aqua/ 
     &  9.993438E-01, 9.998680E-01, 9.998649E-01, 9.998729E-01,
     &  9.998738E-01, 9.998774E-01, 9.995754E-01, 9.994906E-01,
     &  9.995439E-01, 9.997496E-01, 9.995483E-01, 9.997404E-01,
     &  9.999194E-01, 9.999071E-01, 9.999177E-01, 9.999211E-01/

c ... Temperature correction intercepts (Kelvin)
      data tci_aqua/
     &  4.792821E-01, 9.260598E-02, 9.387793E-02, 8.659482E-02,
     &  7.854801E-02, 7.521532E-02, 1.828557E-01, 2.051362E-01,
     &  1.628724E-01, 8.003410E-02, 1.290129E-01, 6.810679E-02,
     &  1.895925E-02, 2.131206E-02, 1.858586E-02, 1.737030E-02/

c-----------------------------------------------------------------------

c ... Set default return value
      modis_bright_shift = -1.0

c ... Check input parameters and return if they are bad
      if (rad .le. 0.0 .or.
     &    band .lt. 20 .or.
     &    band .gt. 36 .or.
     &    band .eq. 26) return

c ... Get index into coefficient arrays
      if (band .le. 25) then
        index = band - 19
      else
        index = band - 20
      endif
      
c ... Get the coefficients for Terra or Aqua
      if (platform_name(1:5) .eq. 'Terra' .or.
     &    platform_name(1:5) .eq. 'terra' .or.
     &    platform_name(1:5) .eq. 'TERRA') then
        cwn = cwn_terra(index)
        tcs = tcs_terra(index)
        tci = tci_terra(index)
      else if (platform_name(1:4) .eq. 'Aqua' .or.
     &         platform_name(1:4) .eq. 'aqua' .or.
     &         platform_name(1:4) .eq. 'AQUA') then
        cwn = cwn_aqua(index)
        tcs = tcs_aqua(index)
        tci = tci_aqua(index)
      else
        call message('modis_bright_shift.f',
     &    'Platform name not recognized ' //
     &    '[OPERATOR ACTION: Contact SDST]', 0, 2)
      endif
     
c ... Compute brightness temperature
      if (units .eq. 1) then

c ...   Radiance units are
c ...   Watts per square meter per steradian per micron
        modis_bright_shift = (bright_m(1.0e+4 / cwn, rad) - tci) / tcs

      else

c ...   Radiance units are
c ...   milliWatts per square meter per steradian per wavenumber
        modis_bright_shift = (brite_m(cwn, rad) - tci) / tcs

      endif

      END
"""


import os, sys, re, logging
import numpy as np
from collections import namedtuple

LOG = logging.getLogger(__name__)

# exponential notation regex 
EXPO = r'[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?'

# group with combination of [\n&,\s] between them
EXPO_GRP = r'(?:[\n&,\s]+('+EXPO+r'))'

# data statement with name, followed by 16 coefficients, ending with slash
RE_DATA = re.compile( r'data (\w+)\s*/'+EXPO_GRP*16+r'\s*/', re.I|re.M)

# read the fortran source into a string
# BT_FORTRAN = file('modis_bright_shift.f').read()

# convert list of strings into a coefficient table
_mk_coeff_array = lambda x: (x[0], np.array([float(v) for v in x[1:]], dtype=np.float64))

# and let'er rip
MODIS_COEFF_TABLE = dict( _mk_coeff_array(x) for x in RE_DATA.findall(BT_FORTRAN) )

modis_coeffs = namedtuple('modis_coeffs', 'cwn tcs tci')


def _coeffs(platform, offset):
    p = platform.split(' ')[0].lower()
    return modis_coeffs(cwn = MODIS_COEFF_TABLE['cwn_' + p][offset],
                        tcs = MODIS_COEFF_TABLE['tcs_' + p][offset],
                        tci = MODIS_COEFF_TABLE['tci_' + p][offset])


"""
c  Fundamental constants required for the monochromatic
c  Planck function routines PLANCK_M, PLANC_M, BRIGHT_M, BRITE_M
c
c  Taken from the NIST Reference on Constants, Units, and Uncertainty
c
c  http://physics.nist.gov/cuu/Constants/
c
c  See also:
c
c  Mohr, P.J. and B.N. Taylor, "CODATA recommended values of the
c    fundamental physical constants: 1998", Reviews of Modern Physics,
c    Vol.72, No.2, 2000.
"""

# ... Planck constant (Joule second)
h = 6.62606876e-34

# ... Speed of light in vacuum (meters per second)
c = 2.99792458e+8

# ... Boltzmann constant (Joules per Kelvin)      
k = 1.3806503e-23

# ... Derived constants      
c1 = 2.0 * h * c * c
c2 = (h * c) / k





def micron_bt(w, r):
    zult = np.empty_like(r, dtype=np.float64)
    if r.dtype != np.float64:
        r = r.astype(np.float64)
    zult[:] = np.nan
    mask = (r > 0.0)
    ws = 1.0e-6 * w
    zult[mask] = c2 / (ws * np.log(c1 / (1.0e6 * r[mask] * ws**5) + 1.0))
    return zult


def wnum_bt(v, r):
    zult = np.empty_like(r, dtype=np.float64)
    if r.dtype != np.float64:
        r = r.astype(np.float64)
    zult[:] = np.nan
    mask = (r > 0.0)
    vs = 1.0e+2 * v
    zult[mask] = c2 * vs / np.log(c1 * vs**3 / (1.0e-5 * r[mask]) + 1.0)
    return zult


def bright_shift(platform, rad, band, units="micron"):
    """compute brightness temperature for MODIS on Terra and Aqua

    :arg platform: "Terra" or "Aqua"
    :arg rad: radiance spectra, arbitrary shape
    :arg band: band number
    :keyword units: "micron" implying Watts per square meter per steradian per micron for radiance
            or "wavenumber" implying milliWatts per square meter per steradian per wavenumber
    
    .. note::
    
        the return array is in Kelvin and contains numpy.nan values where the inputs
        could not be processed

    """    
    offset = (band - 20) if (band <= 25) else (band - 21)
    assert(offset >=0 and offset <16)
    C = _coeffs(platform, offset)
    LOG.debug('Coeffs loaded at offset %d: %s' % (offset, C))

    if units == 'micron': # Watts per square meter per steradian per micron
        return (micron_bt(1.0e+4 / C.cwn, rad) - C.tci) / C.tcs
    elif units == 'wavenumber': #  milliWatts per square meter per steradian per wavenumber
        return (wnum_bt(C.cwn, rad) - C.tci) / C.tcs
    else:
        raise ValueError("units must be 'wavenumber' or 'micron'")


def _test1():
    from pprint import pprint
    shape = (147, 31) # arbitrary image-like
    rad = np.random.ranf(shape) - 0.1
    bt = bright_shift('Terra', rad, 24, 'wavenumber')
    pprint(bt)

def _test2 () :
    """
    This test is based on the averaged coefficients for both Aqua and Terra.
    The reverse calculations were done using an IDL version of this code provided by Liam.
    The radiances for three bands that should result in temperatures of 250K were
    calculated.
    
    For now the test only runs in 'micron' (Watts per square meter per steradian per micron)
    mode. The radiances for 'wavenumber' mode are also given below
    
    William calculated these:
    
        Assuming Watts per square meter per steradian per micron, radiance will be:
        
        Band 20 = 0.0389763
        Band 27 = 1.70482
        Band 31 = 3.97578
        
        Assuming milliWatts per square meter per steradian per inverse centimeter:
        
        Band 20 = 0.0558482
        Band 27 = 7.80456
        Band 31 = 48.2132
    
    If you use these radiances as an input, and you should get approx 250 as a result. 
    """
    
    MICRON_RADS = {
                    20: 0.0389763,
                    27: 1.70482,
                    31: 3.97578
                  }
    WAVENUM_RADS = \
                  {
                    20: 0.0558482,
                    27: 7.80456,
                    31: 48.2132
                  }
    EXPECTED_BT = 250.0
    
    # the micron test
    results_Aqua  = { }
    results_Terra = { }
    
    for band_key in MICRON_RADS.keys() :
        results_Aqua [band_key] = bright_shift("Aqua",  np.array([MICRON_RADS[band_key]]), band_key, units="micron")[0]
        results_Terra[band_key] = bright_shift("Terra", np.array([MICRON_RADS[band_key]]), band_key, units="micron")[0]
    
    print ("Micron Expected Result: %dK" % EXPECTED_BT )
    print ("Aqua  Results by Band: " + str(results_Aqua))
    print ("Terra Results by Band: " + str(results_Terra))
    
    # the wave number test
    results_Aqua  = { }
    results_Terra = { }
    
    for band_key in WAVENUM_RADS.keys() :
        results_Aqua [band_key] = bright_shift("Aqua",  np.array([WAVENUM_RADS[band_key]]), band_key, units="wavenumber")[0]
        results_Terra[band_key] = bright_shift("Terra", np.array([WAVENUM_RADS[band_key]]), band_key, units="wavenumber")[0]
    
    print ("Wave Number Expected Result: %dK" % EXPECTED_BT )
    print ("Aqua  Results by Band: " + str(results_Aqua))
    print ("Terra Results by Band: " + str(results_Terra))


def main():
    import optparse
    usage = """
%prog [options] ...

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--test', dest="self_test",
                    action="store_true", default=False, help="run self-tests") 
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
                    help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    # parser.add_option('-o', '--output', dest='output',
    #                 help='location to store output')
    # parser.add_option('-I', '--include-path', dest="includes",
    #                 action="append", help="include path to append to GCCXML call")                           
    (options, args) = parser.parse_args()

    if options.self_test:
        # FIXME - run any self-tests
        # import doctest
        # doctest.testmod()
        sys.exit(2)

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3,options.verbosity)])

#     if not args:
#         parser.error( 'incorrect arguments, try -h or --help.' )
#         return 9
       
    _test1()
    _test2()

    return 0


if __name__=='__main__':
    sys.exit(main())
    
    

    

