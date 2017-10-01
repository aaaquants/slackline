import sys
sys.dont_write_bytecode = True
import cPickle
from collections import deque
import traceback
from pylab import *
from numpy import *
from pandas import DataFrame,Series,Panel
import json
from core.logger import Logging
from copy import deepcopy
from datetime import datetime
# from ipdb import set_trace
import core.engine as engine
logger = Logging(__name__,'/tmp/slackline.log').logger

def config():
    pass

def handle_data(context):
    pass

def initialize(context):
    pass

def init_optimization(params):
    pass

class OptimizationParameters:
    def __init__(self):
        pass

class Optimize:
    def __init__(self,config=config,handle_data=handle_data,initialize=initialize,init_optimization=init_optimization):
        self.config = config
        self.handle_data = handle_data
        self.initialize = initialize
        self.optimization_performance = []
        self.optimization_parameters = []
        self.params = OptimizationParameters()
        self.init_optimization = init_optimization
        self.previous_results = None

    def run_mc_sweep(self,data,numb_runs=10,mode='bulk',start=datetime(1970,1,1),finish=datetime(2050,1,1),stream_fname=''):
        for i in range(numb_runs):
            if self.previous_results:
                    self.params.previous_params = self.previous_results[i]['params']
            if self.config.PRINT_OPTIMIZATION_RUN:
                print '-----------------------------------------------'
                print '      mc-sweep run {}'.format(i)
                print '-----------------------------------------------'
            self.init_optimization(self.params)
            self.strategy = engine.Strategy(config=self.config,handle_data=self.handle_data,initialize=self.initialize)
            self.strategy.context.params = self.params
            if mode == 'stream':
                this_data = data(stream_fname)
                perf = self.strategy.tick_stream(this_data,start=start,finish=finish)
            else:
                perf = self.strategy.run(data,start=start,finish=finish)
            self.optimization_performance.append(perf.T[perf.T.keys()[-1]])
            self.optimization_parameters.append(deepcopy(self.params.__dict__))
        self.analyze()

    def mesh_params(self):
        dim = len(self.params.__dict__)
        num = prod([len(self.params.__dict__[key]) for key in self.params.__dict__])
        self.params.grid = array(array(meshgrid(*[self.params.__dict__[i] for i in self.params.__dict__])).reshape(dim,num))
        num_runs = self.params.grid.shape[1]
        return num_runs


    def run_grid_search(self,data,mode='bulk',start=datetime(1970,1,1),finish=datetime(2050,1,1),stream_fname=''):
        self.init_optimization(self.params)
        num_runs = self.mesh_params()
        for i in range(num_runs):
            self.params.current = self.params.grid[:,i]
            if self.previous_results:
                self.params.previous_params = self.previous_results[i]['params']
            if self.config.PRINT_OPTIMIZATION_RUN:
                print '-----------------------------------------------'
                print '      mc-sweep run {}'.format(i)
                print '-----------------------------------------------'
            self.strategy = engine.Strategy(config=self.config,handle_data=self.handle_data,initialize=self.initialize)
            self.strategy.context.params = self.params
            # self.config.PRINT_TRADES = False
            if mode == 'stream':
                this_data = data(stream_fname)
                perf = self.strategy.tick_stream(this_data,start=start,finish=finish)
            else:
                perf = self.strategy.run(data,start=start,finish=finish)
            self.optimization_performance.append(perf.T[perf.T.keys()[-1]])
            self.optimization_parameters.append(deepcopy(self.params.__dict__))
        self.analyze()

    def analyze(self):
        self.results = []
        for i,j in zip( self.optimization_parameters,self.optimization_performance):
            self.results.append({'params':i,'pnl':j['pnl']})

def find_best(results,field='pnl'):
    '''
    This function extracts the best run from results
    '''
    best = None
    hwm = -10000000
    for i in results:
        if i[field] > hwm:
            hwm = i[field]
            best = i
    return [best]

def run_validation(data_factory,instruments,start_is,finish_is,finish_oos,num_runs,
                    handle_data=handle_data,
                    initialize=initialize,
                    init_optimization=init_optimization,
                    config = config):

    def init_test(params):
        for key in params.previous_params.keys():
            '''This is kinda bad practise but I dont know a better way here:'''
            exec('params.%s = params.previous_params["%s"]'%(key,key))

    def run_optimize(start,finish,num_runs,instruments):
        data = data_factory(instruments)()
        optimize = Optimize(config,handle_data=handle_data,init_optimization=init_optimization,initialize=initialize)
        optimize.run_mc_sweep(data,numb_runs=num_runs,start=start,finish=finish)
        return optimize.results


    def run_train_test(results,start,finish,instruments):
        data = data_factory(instruments)()
        optimize = Optimize(config,handle_data=handle_data,init_optimization=init_test,initialize=initialize)

        results = find_best(results,field='pnl')

        # Running the test series
        optimize.previous_results = results
        optimize.run_mc_sweep(data,numb_runs=len(results),start=start,finish=finish)
        return optimize.results

    results = run_optimize(start_is,finish_is,num_runs,instruments)
    return run_train_test(results,finish_is,finish_oos,instruments)


def run_walk_forward(data_factory,
                    instruments,
                    start,
                    finish,
                    train_period,
                    test_period,
                    num_runs,
                    handle_data=handle_data,
                    initialize=initialize,
                    init_optimization=init_optimization,
                    config = config):

    start_is = start - test_period
    while True:
        start_is = start_is + test_period
        finish_is = start_is + train_period
        start_oos = finish_is
        finish_oos = start_oos + test_period
        if start_is < finish-train_period-test_period:
            run_validation(data_factory,instruments,start_is,finish_is,finish_oos,num_runs,
                    handle_data=handle_data,
                    initialize=initialize,
                    init_optimization=init_optimization,
                    config = config)
        else:
            break
