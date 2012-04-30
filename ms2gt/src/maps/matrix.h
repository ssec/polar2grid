/*========================================================================
 * matrix - allocate 2-D matrix
 *
 * 13-Jan-1993 K.Knowles knowles@sastrugi.colorado.edu 303-492-0644
 * National Snow & Ice Data Center, University of Colorado, Boulder
 *========================================================================*/
#ifndef matrix_h_
#define matrix_h_

static const char matrix_h_rcsid[] = "$Header: /usr/local/src/maps/matrix.h,v 1.4 1996/05/16 16:54:57 knowles Exp $";

#define matrix_ZERO 1

void **matrix(int rows, int cols, int bytes, int zero);

#endif
