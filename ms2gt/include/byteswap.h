/*========================================================================
 * byteswap.h - byte swapping macros
 *
 *	if compiled with -DNO_SWAP then SWAP* macros do nothing
 *	SWAP4 and SWAP2 evaluate their arguments exactly once
 *	so, for example, val = SWAP4(atoi(*argv++)) should work
 *
 *	27-July-1992 K.Knowles
 *========================================================================*/
#ifndef SWAP_H_
#define SWAP_H_

#ifndef NO_SWAP

static char swap_1b_v_;
static short swap_2b_v_;
static long swap_4b_v_;

/*------------------------------------------------------------------------
 * void SWAP2_IS(short *) - in situ two byte swap
 *------------------------------------------------------------------------*/
#define SWAP2_IS(x) \
( swap_1b_v_ = ((char*)x)[0], \
  ((char*)x)[0] = ((char*)x)[1], \
  ((char*)x)[1] = swap_1b_v_  )

/*------------------------------------------------------------------------
 * short SWAP2(short) - two byte swapped value of any integer expression
 *------------------------------------------------------------------------*/
#define SWAP2(x) (swap_2b_v_=x, SWAP2_IS(&swap_2b_v_), swap_2b_v_)

/*------------------------------------------------------------------------
 * void SWAP4_IS(long *) - in situ four byte swap
 *------------------------------------------------------------------------*/
#define SWAP4_IS(x) \
( swap_1b_v_ = ((char*)x)[0], \
  ((char*)x)[0] = ((char*)x)[3], \
  ((char*)x)[3] = swap_1b_v_, \
  swap_1b_v_ = ((char*)x)[1], \
  ((char*)x)[1] = ((char*)x)[2], \
  ((char*)x)[2] = swap_1b_v_  )

/*------------------------------------------------------------------------
 * long SWAP4(long) - four byte swapped value of any integer expression
 *------------------------------------------------------------------------*/
#define SWAP4(x) (swap_4b_v_=x, SWAP4_IS(&swap_4b_v_), swap_4b_v_)

#else

#define SWAP4_IS(x)
#define SWAP2_IS(x)
#define SWAP4(x) (x)
#define SWAP2(x) (x)

#endif

#endif





