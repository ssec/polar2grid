/*------------------------------------------------------------------------
 * transverse_mercator
 *------------------------------------------------------------------------*/
static const char transverse_mercator_c_rcsid[] = "$Id: transverse_mercator.c 16072 2010-01-30 19:39:09Z brodzik $";

#include "proj.h"
#include "define.h"
#include "mapx.h"

static void init_mlfn(mapx_class *current);
static double tm_mlfn(mapx_class *current, double phi);
static void init_phi1fn(mapx_class *current);
static double phi1fn(mapx_class *current, double mu);

const char *id_transverse_mercator(void)
{
  return transverse_mercator_c_rcsid;
}

int init_transverse_mercator(mapx_class *current)
{
  current->Rg =
    current->equatorial_radius / current->scale * current->center_scale;
  return 0;
}

int transverse_mercator(mapx_class *current,
			double lat, double lon, double *x, double *y)
{
  double phi, lam;
  double cos_phi, b, alpha;
  int ret_code;

  *x = 0.0;
  *y = 0.0;
  ret_code = 0;
  phi = RADIANS (lat);
  cos_phi = cos(phi);
  lam = RADIANS (lon - current->lon0);
  b = cos_phi * sin(lam);

  if ((fabs(fabs(b) - 1.0)) < 1e-7) {
    ret_code = -1;
  } else {
    *x = 0.5 * current->Rg * log((1.0 + b)/(1.0 - b));
    alpha = acos(cos_phi * cos(lam) / sqrt(1.0 - b*b));
    if (lat < 0.0)
      alpha = -alpha;
    *y = current->Rg * (alpha - RADIANS(current->lat0));
  }

  *x += current->false_easting;
  *y += current->false_northing;
  
  return(ret_code);
}

int inverse_transverse_mercator(mapx_class *current,
				double x, double y, double *lat, double *lon)
{
  double phi, lam, f, sinh_x, d, cos_d, alpha;

  x -= current->false_easting;
  y -= current->false_northing;

  f = exp(x / current->Rg);
  sinh_x = 0.5 * (f - 1 / f);
  d = RADIANS(current->lat0) + y / current->Rg;
  cos_d = cos(d);
  alpha = sqrt((1.0 - cos_d * cos_d) / (1.0 + sinh_x * sinh_x));
  phi = asinz(alpha);
  if (d < 0.0)
    phi = -phi;
  if (sinh_x == 0.0 && cos_d == 0)
    lam = 0.0;
  else
    lam = atan2(sinh_x, cos_d);

  *lat = DEGREES(phi);
  *lon = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  
  return 0;
}

/*------------------------------------------------------------------------
 * transverse_mercator_ellipsoid
 *------------------------------------------------------------------------*/

int init_transverse_mercator_ellipsoid(mapx_class *current)
{
  int ret_code;
  double phi0;

  ret_code = 0;
  if (current->e2 < 0.00001) {
    current->geo_to_map =
      (int (*)(void *, double, double, double *, double *))transverse_mercator;
    current->map_to_geo =
    (int (*)(void *, double, double, double *, double *))inverse_transverse_mercator;
    ret_code = init_transverse_mercator(current);
  } else {
    current->Rg  = current->equatorial_radius / current->scale;
    current->esp = current->e2 / (1.0 - current->e2);

    init_mlfn(current);
    phi0 = RADIANS(current->lat0);
    current->ml0 = tm_mlfn(current, phi0);
    
    init_phi1fn(current);
  }

  return(ret_code);
}

int transverse_mercator_ellipsoid(mapx_class *current,
				  double lat, double lon, 
				  double *x, double *y)
{
  double phi, lam;
  double cos_phi, sin_phi;
  double al, als, c, tq, t, con, n, ml;
    
  phi = RADIANS(lat);
  lam = RADIANS(lon - current->lon0);
  ml  = tm_mlfn(current, phi);

  if (fabs(PI / 2.0 - fabs(phi)) < 1e-6) {
    *x = 0.0;
    *y = current->center_scale * (ml - current->ml0);
  } else {
    cos_phi = cos(phi);
    sin_phi = sin(phi);
    al  = cos_phi * lam;
    als = al * al;
    c   = current->esp * cos_phi * cos_phi;
    tq  = tan(phi);
    t   = tq * tq;
    con = sqrt(1.0 - current->e2 * sin_phi * sin_phi);
    n   = current->Rg / con;

    *x = current->center_scale *
      n * al * (1.0 + als / 6.0 *
		(1.0 - t + c + als / 20.0 *
		 (5.0 - 18.0 * t + t*t + 72.0 * c - 58.0 * current->esp)));
    *y = current->center_scale *
      (ml - current->ml0 + n * tq * als *
       (0.5 + als / 24.0 *
	(5.0 - t + 9.0 * c + 4.0 * c*c + als / 30.0 *
	 (61.0 - 58.0 * t + t*t + 600.0 * c - 330.0 * current->esp))));
  }

  *x += current->false_easting;
  *y += current->false_northing;
  
  return 0;
}

int inverse_transverse_mercator_ellipsoid(mapx_class *current,
					  double x, double y, 
					  double *lat, double *lon)
{
  double phi, lam;
  double mu, ml, phi1, fabs_phi, phi_test;
  double cos_phi1, sin_phi1;
  double c, c2, tq, t, t2, con, n, r, d, d2;

  x -= current->false_easting;
  y -= current->false_northing;

  ml = current->ml0 + y / current->center_scale;
  mu = ml / (current->Rg * current->e0);
  phi1 = phi1fn(current, mu);

  phi_test = PI / 2.0;
  fabs_phi = fabs(phi1);
  if (fabs_phi > phi_test ||
      fabs(fabs_phi - phi_test) < 1e-6) {
    phi = sign(y) * phi_test;
    lam = 0.0;
  } else {
    cos_phi1 = cos(phi1);
    sin_phi1 = sin(phi1);
    c   = current->esp * cos_phi1 * cos_phi1;
    c2  = c * c;
    tq  = tan(phi1);
    t   = tq * tq;
    t2  = t * t;
    con = sqrt(1.0 - current->e2 * sin_phi1 * sin_phi1);
    n   = current->Rg / con;
    r   = current->Rg * (1.0 - current->e2)/(con * con * con);
    d   = x / (n * current->center_scale);
    d2  = d * d;

    phi = phi1 - (n * tq * d2 / r) *
      (0.5 - d2 / 24.0 *
       (5.0 + 3.0 * t + 10.0 * c - 4.0 * c2 - 9.0 * current->esp - d2 / 30.0 *
	(61.0 + 90.0 * t + 298.0 * c + 45.0 * t2 - 252.0 * current->esp
	 - 3.0 * c2)));
    fabs_phi = fabs(phi);
    if (fabs_phi > phi_test ||
	fabs(fabs_phi - phi_test) < 1e-6) {
      phi = sign(y) * phi_test;
      lam = 0.0;
    } else {

      lam = d * (1.0 - d2 / 6.0 *
		 (1.0 + 2.0 * t + c - d2 / 20 *
		  (5 - 2.0 * c + 28.0 * t - 3.0 * c2 + 8.0 * current->esp
		   + 24.0 * t2))) / cos_phi1;
    }
  }
  
  *lat = DEGREES(phi);
  *lon  = DEGREES(lam) + current->lon0;
  NORMALIZE(*lon);
  return 0;
}

/*------------------------------------------------------------------------
 * init_mlfn - compute constants e0, e1p, e2p, and e3p used in a series for
 * calculating the distance along a meridian.
 * (modified gctp function)
 *
 *	input : current - pointer to current mapx_class structure.
 *                      - uses current->e2 = eccentricity squared = e^2 = es.
 *
 *      output: current->e0
 *              current->e1p
 *              current->e2p
 *              current->e3p
 *
 *	result: none
 *
 *      derivation:
 *        From Snyder p. 61:
 *          M/a = e0 * phi
 *                - e1 * sin(2*phi)
 *                + e2 * sin(4*phi)
 *                - e3 * sin(6*phi)
 *          where:
 *            e0 = 1 - e^2/4 - 3e^4/64 - 5e^6/256
 *            e1 = 3e^2/8 + 3e^4/32 + 45e^6/1024
 *            e2 = 15e^4/256 + 45e^6/1024
 *            e3 = 35e^6/3072
 *
 *        From Snyder p. 19:
 *          M/a = e0 * phi
 *                + sin(2*phi) * (e1p + cos(2*phi)
 *                                * (e2p + cos(2*phi) * e3p))
 *          where:
 *            e0 = 1 - e^2/4 - 3e^4/64 - 5e^6/256
 *            e0 = 1 - e^2/4 * (1 + 3e^2/16 + 5e^4/64)
 *            e0 = 1 - e^2/4 * (1 + e^2/16 * (3 + 5e^2/4)
 *            e0 = 1 - 0.25e^2 * (1 + e^2/16 * (3 + 1.25e^2))

 *            e1p = -e1 - (-e3)
 *            e1p = e3 - e1
 *            e1p = 35e^6/3072 - (3e^2/8 + 3e^4/32 + 45e^6/1024)
 *            e1p = -3e^2/8 - 3e^4/32 - 100e^6/3072
 *            e1p = -3e^2/8 - 3e^4/32 - 25e^6/768
 *            e1p = -1e^2/8 * (3 + 3e^2/4 + 25e^4/96)
 *            e1p = -1e^2/8 * (3 + e^2/4 * (3 + 25e^2/24))
 *            e1p = -0.125e^2 * (3 + 0.25e^2 * (3 + 25e^2/24))
 *
 *            e2p = 2e2
 *            e2p = 2 * (15e^4/256 + 45e^6/1024)
 *            e2p = 15e^4/128 + 45e^6/512)
 *            e2p = 15e^4/128 * (1 + 3e^2/4)
 *            e2p = 0.1178175e^4 * (1 + 0.75e^2)
 *
 *            e3p = -4e3
 *            e3p = -4 * (35e^6/3072)
 *            e3p = -35e^6/768
 *------------------------------------------------------------------------*/
static void init_mlfn(mapx_class *current)
{
  double es, es2, es3;

  es = current->e2;
  es2 = es * es;
  es3 = es2 * es;
  current->e0  = 1.0 - 0.25 * es * (1.0 + es / 16.0 * (3.0 + 1.25 * es));
  current->e1p = -0.125 * es * (3.0 + 0.25 * es * (3.0 + 25.0 * es / 24.0));
  current->e2p = 0.1178175 * es2 * (1 + 0.75 * es);
  current->e3p = -35.0 * es3 / 768.0;
}

/*------------------------------------------------------------------------
 * tm_mlfn -  computes the value of M which is the distance along a
 *            meridian from the Equator to latitude phi.
 * (modified gctp function)
 *
 *	input : current - pointer to current mapx_class structure.
 *                      - uses current->Rg = scaled equatorial radius = a
 *                             current->e0
 *                             current->e1p
 *                             current->e2p
 *                             current->e3p
 *              phi - latitude in radians
 *
 *	result: ml - distance along a meridian from the equator to
 *                   latitude phi
 *
 *      derivation:
 *        From Snyder p. 19:
 *          M = a * e0 * phi
 *                + sin(2*phi) * (e1p + cos(2*phi)
 *                                * (e2p + cos(2*phi) * e3p))
 *------------------------------------------------------------------------*/
static double tm_mlfn(mapx_class *current, double phi)
{
  double phi2;
  double cos_phi2;

  phi2 = 2 * phi;
  cos_phi2 = cos(phi2);
  return(current->Rg *
	 (current->e0 * phi
	  + sin(phi2) * (current->e1p
			 + cos_phi2 * (current->e2p
				       + cos_phi2 * current->e3p))));
}

/*------------------------------------------------------------------------
 * init_phi1fn - compute constants f1, f2, f3, and f4 used in a series for
 *        calculating the "footprint latitude" phi1.
 *
 *	input : current - pointer to current mapx_class structure.
 *                        uses current->e2 = eccentricity squared = e^2
 *
 *      output: current->f1
 *              current->f2
 *              current->f3
 *              current->f4
 *
 *	result: none.
 *
 *      derivation:
 *        From Snyder p. 63:
 *          phi1 = mu + Asin(2mu) + Bsin(4mu) + Csin(6mu) + Dsin(8mu)
 *          where:
 *            e1 = (1-sqrt(1-e^2))/(1+sqrt(1-e^2))
 *            A = 3e1/2 - 27e1^3/32
 *            B = 21e1^2/16 - 55e1^4/32
 *            C = 151e1^3/96
 *            D = 1097e1^4/512
 *
 *        From Snyder p. 19:
 *          phi1 = mu + sin(2mu)
 *                      * (f1 + cos(2mu)
 *                         * (f2 + cos(2mu)
 *                            * f3 + cos(2mu) * f4))
 *          where:
 *            f1 = A - C
 *            f1 = (3e1/2 - 27e1^3/32) - (151e1^3/96)
 *            f1 = 3e1/2 - 232e1^3/96
 *            f1 = e1/2 * (3 - 166e1^2/96)
 *            f1 = 0.5e1 * (3 - 83e1^2/48)
 *
 *            f2 = 2B - 4D
 *            f2 = 2 * (21e1^2/16 - 55e1^4/32) - 4 * (1097e1^4/512)
 *            f2 = 42e1^2/16 - 110e1^4/32 - 4388e1^4/512
 *            f2 = 21e1^2/8 - 6148e1^4/512
 *            f2 = e1^2/8 * (21 - 6148e1^2/64)
 *            f2 = 0.125e1^2 * (21 - 1537e1^2/16)
 *
 *            f3 = 4C
 *            f3 = 4 * (151e1^3/96)
 *            f3 = 604e1^3/96
 *            f3 = 151e1^3/24
 *
 *            f4 = 8D
 *            f4 = 8 * (1097e1^4/512)
 *            f4 = 8776e1^4/512
 *            f4 = 1097e1^4/64
 *------------------------------------------------------------------------*/
static void init_phi1fn(mapx_class *current)
{
  double e1, e1s, e1c, e1q;

  e1 = sqrt(1 - current->e2);
  e1 = (1 - e1) / (1 + e1);
  e1s = e1 * e1;
  e1c = e1 * e1s;
  e1q = e1 * e1c;

  current->f1 = 0.5 * e1 * (3.0 - 83.0 * e1s / 48.0);
  current->f2 = 0.125 * e1s * (21.0 - 1537.0 * e1s / 16.0);
  current->f3 = 151.0 * e1c / 24.0;
  current->f4 = 1097.0 * e1q * 64.0;
}

/*------------------------------------------------------------------------
 * phi1fn - compute the "footprint latitude" phi1.
 *
 *	input : current - pointer to current mapx_class structure.
 *                        uses current->f1
 *                             current->f2
 *                             current->f3
 *                             current->f4
 *              mu - angle in radians (see Snyder p. 63)
 *
 *	result: phi1 - the "footprint latitude" or the latitude at the
 *              central meridian which has the same y coordinate a that
 *              of the point (phi, lam).
 *
 *      derivation:
 *        From Snyder p. 63:
 *          phi1 = mu + Asin(2mu) + Bsin(4mu) + Csin(6mu) + Dsin(8mu)
 *          where:
 *            A = 3e1/2 - 27e1^3/32
 *            B = 21e1^2/16 - 55e1^4/32
 *            C = 151e1^3/96
 *            D = 1097e1^4/512
 *
 *        From Snyder p. 19:
 *          phi1 = mu + sin(2mu)
 *                      * (f1 + cos(2mu)
 *                         * (f2 + cos(2mu)
 *                            * f3 + cos(2mu) * f4))
 *          where:
 *            f1 = A - C
 *            f2 = 2B - 4D
 *            f3 = 4C
 *            f4 = 8D
 *------------------------------------------------------------------------*/
static double phi1fn(mapx_class *current, double mu)
{
  double mu2 = 2 * mu;
  double cos_mu2 = cos(mu2);
  return(mu + sin(mu2) *
	 (current->f1 + cos_mu2 *
	  (current->f2 + cos_mu2 *
	   (current->f3 + cos_mu2 *
	    current->f4))));
}
