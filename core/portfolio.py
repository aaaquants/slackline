from numpy import *
import numpy as np
# from ipdb import set_trace

class Portfolio:
    def __init__(self,context):
        self.positions = {}
        self.benchmark_positions = {}
        self.entry = {}
        self.price  = {}
        self.context = context
        self.execution_time = {}
        self.execution_loss = {}
        self.cash = 100000
        self.starting_cash = self.cash
        self.locked_pnl = {}

    def calc_pnl(self):
        pnl = 0
        for instrument in self.positions.keys():
            q = array(self.positions[instrument])
            p = array(self.context.current[instrument].four)
            v = array(self.price[instrument])
            net = np.sum(q*p)
            pnl+=-np.dot(q,v)+net
        return pnl

    def fast_calc_pnl(self):
        pnl = 0
        for instrument in self.positions.keys():
            if not instrument in self.locked_pnl:
                self.locked_pnl[instrument] = 0

            q = array(self.positions[instrument])
            ask = array(self.context.current[instrument].four)
            bid = array(self.context.current[instrument].one)
            v = array(self.price[instrument])

            # This is a better pnl calculation but it may not be so good for bars
            net = np.sum(q)*(ask*(q<0)+bid*(q>0))[0]

            # This is the standard pnl calculation
            pnl_k=-np.sum(q*v)+net+self.locked_pnl[instrument]
            pnl += pnl_k
        return pnl

    def calc_ls(self):
        positions ={}
        for instrument in self.positions.keys():
            positions[instrument] = sum(self.positions[instrument])
        return positions

    def calc_exposure(self):
        short_exposure = 0
        long_exposure = 0
        for instrument in self.positions.keys():
            pos = sum(self.positions[instrument])
            exposure = self.context.current[instrument].four*pos
            if exposure > 0:
                long_exposure+=exposure
            else:
                short_exposure+=exposure
        # set_trace()
        return short_exposure,long_exposure
