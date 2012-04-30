FUNCTION MODIS_PLANCK, TEMP, BAND, UNITS

;+
; DESCRIPTION:
;    Compute Planck radiance for an EOS-AM MODIS infrared band.
;
;    Spectral responses for each IR detector were obtained from MCST:
;    ftp://mcstftp.gsfc.nasa.gov/incoming/MCST/PFM_L1B_LUT_4-30-99
;
;    An average spectral response for each infrared band was
;    computed. The band-averaged spectral response data were used
;    to compute the effective central wavenumbers and temperature
;    correction coefficients included in this module.
;
; USAGE:
;    RESULT = MODIS_PLANCK(TEMP, BAND, UNITS)
;
; INPUT PARAMETERS:
;    TEMP          Brightness temperature (Kelvin)
;    BAND          MODIS IR band number (20-25, 27-36)
;    UNITS         Flag defining radiance units
;                  0 => milliWatts per square meter per steradian per
;                       inverse centimeter
;                  1 => Watts per square meter per steradian per micron
;
; OUTPUT PARAMETERS:
;    MODIS_PLANCK  Planck radiance (units are determined by UNITS)
;                  Note that a value of -1.0 is returned if
;                  TEMP .LE. 0.0, or BAND is not in range 20-25, 27-36.
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: modis_planck.pro,v 1.2 2000/03/15 20:33:50 gumley Exp $
;
; Copyright (C) 1999, 2000 Liam E. Gumley
;
; This program is free software; you can redistribute it and/or
; modify it under the terms of the GNU General Public License
; as published by the Free Software Foundation; either version 2
; of the License, or (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
;-

rcs_id = '$Id: modis_planck.pro,v 1.2 2000/03/15 20:33:50 gumley Exp $'

;- BAND-AVERAGED MODIS SPECTRAL RESPONSE FUNCTIONS FOR EOS-AM
;- TEMPERATURE RANGE FOR FIT WAS  180.00 K TO  320.00 K
;- BANDS
;-   20,  21,  22,  23,
;-   24,  25,  26,  27,
;-   28,  29,  30,  31,
;-   32,  33,  34,  35,
;-   36
;- NOTE THAT BAND 26 VALUES ARE SET TO ZERO

;- Effective central wavenumber (inverse centimenters)
cwn = [$
  2.641775E+03, 2.505277E+03, 2.518028E+03, 2.465428E+03, $
  2.235815E+03, 2.200346E+03, 0.0,          1.477967E+03, $
  1.362737E+03, 1.173190E+03, 1.027715E+03, 9.080884E+02, $
  8.315399E+02, 7.483394E+02, 7.308963E+02, 7.188681E+02, $
  7.045367E+02]

;- Temperature correction slope (no units)
tcs = [$
  9.993411E-01, 9.998646E-01, 9.998584E-01, 9.998682E-01, $
  9.998819E-01, 9.998845E-01, 0.0,          9.994877E-01, $
  9.994918E-01, 9.995495E-01, 9.997398E-01, 9.995608E-01, $
  9.997256E-01, 9.999160E-01, 9.999167E-01, 9.999191E-01, $
  9.999281E-01]

;- Temperature correction intercept (Kelvin)
tci = [$
  4.770532E-01, 9.262664E-02, 9.757996E-02, 8.929242E-02, $
  7.310901E-02, 7.060415E-02, 0.0,          2.204921E-01, $
  2.046087E-01, 1.599191E-01, 8.253401E-02, 1.302699E-01, $
  7.181833E-02, 1.972608E-02, 1.913568E-02, 1.817817E-02, $
  1.583042E-02]

;- Check input parameters and return if they are bad
if (band lt 20) or (band gt 36) or (band eq 26) then return, -1.0

     
;- Compute Planck radiance

if (units eq 1) then begin

  ;- Radiance units are
  ;- Watts per square meter per steradian per micron

  result = planck_m(1.0e+4 / cwn[band - 20], $
    temp * tcs[band - 20] + tci[band - 20])

endif else begin

  ;-  Radiance units are
  ;-  milliWatts per square meter per steradian per wavenumber

  result = planc_m(cwn[band - 20], temp * tcs[band - 20] + tci[band - 20])

endelse

;- Return result to caller
return, result

END
