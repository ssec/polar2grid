FUNCTION BRITE_M, V, R

;+
; DESCRIPTION:
;    Compute brightness temperature given monochromatic Planck radiance.
;
; USAGE:
;    RESULT = BRITE_M(V, R)
;
; INPUT PARAMETERS:
;    V         Wavenumber (inverse centimeters)
;    R         Planck radiance (milliWatts per square meter per
;              steradian per inverse centimeter)
;
; OUTPUT PARAMETERS:
;    BRIGHT_M    Brightness temperature (Kelvin)
;
; MODIFICATION HISTORY:
; Liam.Gumley@ssec.wisc.edu
; http://cimss.ssec.wisc.edu/~gumley
; $Id: brite_m.pro,v 1.2 2000/03/15 20:33:50 gumley Exp $
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

rcs_id = '$Id: brite_m.pro,v 1.2 2000/03/15 20:33:50 gumley Exp $'

;- Constants are from "The Fundamental Physical Constants",
;- Cohen, E. R. and B. N. Taylor, Physics Today, August 1993.

;- Planck constant (Joule second)
h = 6.6260755e-34

;- Speed of light in vacuum (meters per second)
c = 2.9979246e+8

;- Boltzmann constant (Joules per Kelvin)      
k = 1.380658e-23

;- Derived constants      
c1 = 2.0 * h * c * c
c2 = (h * c) / k

;- Convert wavenumber to inverse meters
vs = 1.0e+2 * v
      
;- Compute brightness temperature
return, c2 * vs / alog(c1 * vs^3 / (1.0e-5 * r) + 1.0)

END
