import sys
sys.dont_write_bytecode = True
import unittest
from datetime import datetime
from core.data_factory import *
from core.engine import Strategy
from core.utils import get_history, get_current_date
from core.order import order
from core.optimizer import run_validation, run_walk_forward,Optimize
import config.test_config as tcfg

def initialize_test(context):
    context.count = 0

def handle_data_stream(context):
    if random.randint(0,1000) == 23:
        order(context,'A',random.randint(-1,2))
    if random.randint(0,1000) == 23:
        order(context,'B',random.randint(-1,2))
    MA = mean(get_history(context,'B',field='ask',period=3))

def handle_data_switchover(context):
    if random.randint(0,10) == 2:
        order(context,'NASDAQ:MSFT',1)

def initialize_step(context):
    context.cnt = 0
def handle_data_step(context):
    context.cnt +=1
    if context.cnt == 2:
        order(context,'step_function',1,field='one')
    elif context.cnt == 180:
        order(context,'step_function',-1)


def handle_data_web(context):
        order(context,'F',random.randint(-2,2))
        order(context,'CSCO',random.randint(-2,2))

def initialize_csv_opt(context):
    pass

def init_optimization_csv(params):
  # Here we want deterministic behaviour, not random numbers
    params.random_thresh = 24
    params.random_nr = 24

def handle_data_opt(context):
    if context.params.random_thresh == context.params.random_nr:
                order(context,'AAPL',1)
    if context.params.random_thresh == context.params.random_nr:
                order(context,'MSFT',-1)


def initialize_grid_search(context):
    pass

def init_grid_search(params):
    params.alpha = [20,30]
    params.beta = [40]


def handle_data_grid_search(context):
    for symbol in ['B','A']:
        try:
            MA1 = mean(get_history(context,symbol,field='ask',period=context.params.current[0]))
            MA2 = mean(get_history(context,symbol,field='ask',period=context.params.current[1]))
            if MA1 < MA2:
                order(context,symbol,1)
            elif MA1 > MA2:
                order(context,symbol,-1)

        except: pass


class TestCode(unittest.TestCase):

    def test_run_stream(self):
        data = StreamDataFactory('data/test_stream.csv')
        strategy = Strategy(tcfg,handle_data=handle_data_stream)
        result = strategy.tick_stream(data)
        self.assertTrue('pnl' in result)
        self.assertTrue(len(result['portfolio_value'])!=tcfg.INITIAL_CASH)

    def test_run_switchover(self):
        data = CSVDataFactory(['data/NASDAQ:MSFT.csv'])()
        strategy = Strategy(tcfg,handle_data=handle_data_switchover)
        strategy.run(data,start=datetime(2014,7,1),finish=datetime(2014,12,12))

        data = GoogLiveFactory(['NASDAQ:MSFT'])
        dat = eval(data.mydata())
        self.assertTrue('bid' in dat)
        self.assertTrue('ask' in dat)
        self.assertTrue('ticker' in dat)
        self.assertEqual(dat['ticker'],'NASDAQ:MSFT')

    def test_run_web(self):
        tcfg.PRINT_TRADES = False
        data = WebDataFactory(['F','CSCO'],datetime(2017, 1, 1),datetime(2017, 3, 1),source='google')()
        strategy = Strategy(tcfg,handle_data=handle_data_web)
        results = strategy.run(data)
        self.assertTrue(results['pnl'][results['pnl'].keys()[-1]]!=0)

    def test_run_train_test(self):
        tcfg.PRINT_OPTIMIZATION_RUN = False
        tcfg.PRINT_TRADES = False
        tcfg.DELAYED_EXECUTION = False
        results = run_validation(CSVDataFactory,['data/MSFT.csv','data/AAPL.csv'],
                        datetime(2014,5,1),
                        datetime(2014,6,12),
                        datetime(2014,7,12),
                        4,
                        handle_data=handle_data_opt,
                        initialize=initialize_csv_opt,
                        init_optimization=init_optimization_csv,
                        config = tcfg)
        self.assertTrue(results[0]['pnl']!=0)

    def test_step_function(self):
        data = CSVDataFactory(['data/step_function.csv'])()
        strategy = Strategy(tcfg,handle_data=handle_data_step,initialize=initialize_step)
        results = strategy.run(data)
        self.assertTrue(results['pnl'][results['pnl'].keys()[-1]]==50)
        self.assertTrue(results['portfolio_value'][results['portfolio_value'].keys()[-1]]==100050)

    def test_grid_search(self):
        optimize = Optimize(config=tcfg,handle_data=handle_data_grid_search,init_optimization=init_grid_search,initialize=initialize_grid_search)
        optimize.run_grid_search(StreamDataFactory,mode='stream',stream_fname='data/test_stream.csv')
        self.assertTrue(len(optimize.results)==2)
        self.assertTrue('params' in optimize.results[0])
        self.assertTrue('pnl' in optimize.results[1])
