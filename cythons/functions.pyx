from slackline.core.order import order
cimport numpy as np
cimport cython
import numpy as np

cdef extern from "math.h":
    double sqrt(double m)

def calc_adj(float orig_spread,float alpha,float beta, float N):
    cdef float adj
    adj = orig_spread - (N*beta)-alpha
    return adj

cdef greater_than(float a, float b):
    return a > b

cdef less_than(float a, float b):
    return a < b

cdef equals(float a, float b):
    return a == b

cdef c_and(bint a, bint b):
    return (a & b)

cdef c_and3(bint a, bint b, bint c):
    return a & b & c

@cython.boundscheck(False)
def c_std(np.ndarray[np.float64_t, ndim=1] a):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef double m = 0.0
    for i in range(n):
        m += a[i]
    m /= n
    cdef double v = 0.0
    for i in range(n):
        v += (a[i] - m)**2
    return sqrt(v / n)


def classic_lstsqr(double[:] x_list,double[:] y_list):
    """ Computes the least-squares solution to a linear matrix equation. """
    """https://relate.cs.illinois.edu/course/cs357-f15/file-version/68fa8dd5f1a58eb5d5e81218d37a59f892ca861b/media/least-squares/linregr_least_squares_fit.html"""
    cdef int N = len(x_list)
    cdef double x_avg = c_sum2(x_list)/N
    cdef double y_avg = c_sum2(y_list)/N
    cdef double var_x = 0 
    cdef double cov_xy = 0
    cdef double temp
    cdef double slope
    cdef double y_interc
    cdef int i
    for i in range(N):
        temp = x_list[i] - x_avg
        var_x += temp**2
        cov_xy += temp * (y_list[i] - y_avg)
    slope = cov_xy / var_x
    y_interc = y_avg - slope*x_avg
    return (slope, y_interc)

cdef c_sum(long[:] y):   
    cdef int N = y.shape[0]
    cdef int x = y[0]
    cdef int i
    for i in xrange(1,N):
        x += y[i]
    return x

cdef c_sum2(double[:] y):   
    cdef int N = y.shape[0]
    cdef double x = y[0]
    cdef int i
    for i in xrange(1,N):
        x += y[i]
    return x

cdef c_mult1(long[:] a, double b):
    cdef int N = a.shape[0]
    cdef double[:] res = np.zeros(N)
    for i in xrange(N):
        res[i] = a[i] * b
    return res

cdef c_mult2(long[:] a, double[:] b):
    cdef int N = a.shape[0]
    cdef double[:] res = np.zeros(N)
    for i in xrange(N):
        res[i] = a[i] * b[i]
    return res

def cyth_pnl(self):
    cdef float pnl = 0
    cdef float pnl_k = 0
    cdef float net = 0
    cdef long [:] q
    cdef double p
    cdef double [:] v
    for instrument in self.positions.keys():
        if not instrument in self.locked_pnl:
            self.locked_pnl[instrument] = 0

        q = np.array(self.positions[instrument])
        p = np.array(self.context.current[instrument].four)
        v = np.array(self.price[instrument])
        net = c_sum2(c_mult1(q,p))
        pnl_k=-c_sum2(c_mult2(q,v))+net+self.locked_pnl[instrument]
        pnl += pnl_k
        if sum(self.positions[instrument])==0:
            self.positions[instrument] = [0]
            self.price[instrument] = [0]
            self.locked_pnl[instrument] = pnl_k
    if pnl == 0:
        pnl = c_sum2([self.locked_pnl[key] for key in self.locked_pnl])
    return pnl
    #cdef float pnl = 0
    #cdef float net = 0
    #cdef long [:] q
    #cdef double p
    #cdef double [:] v
    #for instrument in self.positions.keys():
        #q = np.array(self.positions[instrument])
        #p = np.array(self.context.current[instrument].four)
        #v = np.array(self.price[instrument])
        #net = c_sum2(c_mult1(q,p))
        #pnl+=-c_sum2(c_mult2(q,v))+net
    #return pnl


def spread_logic(context, int lr_lkbk, float bandwidth, float locked_bw, float multiplier, float orig_spread,int max_clip):

    cdef long[:] A
    cdef int NClips
    cdef float adj

    if context.alpha and context.beta:
        adj = calc_adj(orig_spread,context.alpha,context.beta,lr_lkbk)

        if 'A' in context.portfolio.positions and 'B' in context.portfolio.positions:

            
                A = np.array(context.portfolio.positions['A'])
                B = np.array(context.portfolio.positions['B'])
                NClips = c_sum(A)
                if not NClips == -c_sum(B)/2:
                    return locked_bw

                #print NClips, c_sum(B)
                # SHORT SIDE
                if c_and(equals(NClips, 0), greater_than(adj, bandwidth*multiplier)):
                 
                    order(context,'A',-1,exec_mode=context.mode)
                    order(context,'B',2,exec_mode=context.mode)
                    
                    locked_bw = bandwidth
                
                # LONG SIDE
                elif c_and(equals(NClips, 0), less_than(adj, -bandwidth*multiplier)):
                 
                    order(context,'A',1,exec_mode=context.mode)
                    order(context,'B',-2,exec_mode=context.mode)
                    
                    locked_bw = bandwidth
                
                if less_than(NClips,0):
                    ## SHORT SIDE
                    if c_and(less_than(-max_clip, NClips), greater_than(adj, -locked_bw*((NClips-1)*multiplier))):
                        #print "enter short:",-locked_bw*((NClips-1)*multiplier),locked_bw,NClips,multiplier
                        order(context,'A',-1,exec_mode=context.mode)
                        order(context,'B',2,exec_mode=context.mode)
                    
                    elif c_and(less_than(NClips, -1), less_than(adj, -locked_bw * ((NClips+1)*multiplier))):
                        #print 'exit short:',-locked_bw * ((NClips+1)*multiplier) 
                        order(context,'A',1,exec_mode=context.mode)
                        order(context,'B',-2,exec_mode=context.mode)
                    
                    if c_and(equals(NClips,-1), less_than(adj, 0)):
                    
                        order(context,'A',1,exec_mode=context.mode)
                        order(context,'B',-2,exec_mode=context.mode)

                elif greater_than(NClips,0):
                    ## LONG SIDE
                    if c_and(greater_than(max_clip, NClips), less_than(adj, -locked_bw*(multiplier*(NClips+1)))):
                        #print "enter long:",-locked_bw*((NClips+1)*multiplier) 
                        order(context,'A',1,exec_mode=context.mode)
                        order(context,'B',-2,exec_mode=context.mode)
                    
                    elif c_and(greater_than(NClips, 1), greater_than(adj, -locked_bw * ((NClips-1)*multiplier))):
                        #print 'exit long:',-locked_bw * ((NClips-1)*multiplier) 
                        order(context,'A',-1,exec_mode=context.mode)
                        order(context,'B',2,exec_mode=context.mode)
                    
                    if c_and(equals(NClips,1), greater_than(adj, 0)):
                    
                        order(context,'A',-1,exec_mode=context.mode)
                        order(context,'B',2,exec_mode=context.mode)

        # THIS IS TO AVOID OVERWRITING OF THE LOADED ORDER BEFORE EXECUTION
        elif not('A' in context.portfolio.positions or 'B' in context.portfolio.positions):

            if greater_than(adj, bandwidth*multiplier):
                
                order(context,'A',-1,exec_mode=context.mode)
                order(context,'B',2,exec_mode=context.mode)

                locked_bw = bandwidth

            elif less_than(adj, -bandwidth*multiplier):
                
                order(context,'A',1,exec_mode=context.mode)
                order(context,'B',-2,exec_mode=context.mode)

                locked_bw = bandwidth

    return locked_bw

