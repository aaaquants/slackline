# from __future__ import print_function
from datetime import datetime,timedelta
from core.data_factory import *
from core.engine import *
from core.utils import *
from core.logger import Logging
import config.config as config
import config.config as cfg
import traceback
from core.optimizer import *
logger = Logging(__name__,'/tmp/slackline.log').logger
#*************************************************************************************
'''
This function takes data from a large file and streams them
into the backtester rather than loading them into memory beforehand.
'''
def handle_data_stream(context):
        if random.randint(0,1000) == 23:
            order(context,'A',random.randint(-1,2))
        if random.randint(0,1000) == 23:
            order(context,'B',random.randint(-1,2))
        # MA = mean(get_history(context,'B',field='ask',period='1D'))
        MA = mean(get_history(context,'B',field='ask',period=3))
        # MA = mean(get_history(context,'B',field='ask'))
        print MA

def run_stream():
    cfg.LOG_FREQUENCY = 5
    data = StreamDataFactory('data/test_stream.csv')
    strategy = Strategy(config=cfg,handle_data=handle_data_stream)
    strategy.tick_stream(data)
#*************************************************************************************
'''
This function produces random data and runs a backtest on them.
'''
def handle_data_random(context):
    print mean(get_history(context,'1','5D','four'))
    if random.randint(0,100) == 23:
        order(context,'1',random.randint(0,2))

def run_random():
    import config.random_factory_config as rcfg
    data = RandomDataFactory(rcfg)()
    strategy = Strategy(config=cfg,handle_data=handle_data_random)
    strategy.run(data)
#*************************************************************************************
'''
This function gets live market data from google and runs a strategy with them
'''
def handle_data_live(context):
    # print 'ABT:',get_current_price(context,'ABT')
    # print 'GOOG:',get_current_price(context,'GOOG')
    if random.randint(0,10) == 2:
        for symbol in context.data.symbols:
            order(context,symbol,random.randint(-1,2))
        # order(context,'NASDAQ:GOOG',random.randint(-1,1))
        # order(context,'CURRENCY:EURAUD',random.randint(-1,2))

def run_live():
    data = GoogLiveFactory(['ASX:ABT','NASDAQ:GOOG','CURRENCY:EURAUD','CURRENCY:USDAUD'])
    strategy = Strategy(config=cfg,handle_data=handle_data_live)
    strategy.tick_stream(data)

#*************************************************************************************
'''
This function runs a backtest on historical data and
then switches to live data. Note that the file names
have to have the exchange id in the name.
'''
def initialize_switchover(context):
        csv_fetcher(context,'data/MSFT.csv','signals')

def handle_data_switchover(context):
    if random.randint(0,10) == 2:
        order(context,'NASDAQ:MSFT',1)
        order(context,'NASDAQ:AAPL',1)

def run_switchover():
    data = CSVDataFactory(['data/NASDAQ:MSFT.csv','data/NASDAQ:AAPL.csv'])()
    strategy = Strategy(config=cfg,handle_data=handle_data_switchover,initialize=initialize_switchover)
    strategy.run(data,start=datetime(2012,1,1),finish=datetime(2014,12,12))

    data = GoogLiveFactory(['NASDAQ:AAPL','NASDAQ:MSFT'])
    strategy.tick_stream(data)
#*************************************************************************************
'''
This strategy runs with data pulled from the web, like google or yahoo.
'''
def handle_data_web(context):
    if random.randint(0,100) == 23:
        order(context,'F',random.randint(0,2))
        order(context,'CSCO',random.randint(-2,2))


def run_web():
    data = WebDataFactory(['F','CSCO'],datetime(2010, 1, 1),datetime(2017, 1, 1),source='google')()
    strategy = Strategy(config=cfg,handle_data=handle_data_web)
    strategy.run(data)

#*************************************************************************************
'''
This runs off a custom csv file that exists locally. Unlike in the
streaming case, all data are loaded into memory first.
'''
def initialize_csv(context):
        pass
        csv_fetcher(context,'data/MSFT.csv','signals')

def handle_data_csv(context):
    # print get_current_date(context)
    # print mean(get_from_fetcher(context,'signals','50D','Close'))
    # print mean(get_history(context,'MSFT','5D','four'))
    if random.randint(0,100) == 23:
        order(context,'MSFT',random.randint(-100,100))
    if random.randint(0,100) == 23:
        order(context,'AAPL',random.randint(-100,100))
    # if random.randint(0,100) == 23:
        # order(context,'ETR',random.randint(-1,2))

        # context.record('some',random.randn())
        # context.record('other',random.randn())

def run_csv():
    # data = CSVDataFactory(['data/MSFT.csv','data/AAPL.csv','data/ETR.csv'])()
    data = CSVDataFactory(['data/MSFT.csv','data/AAPL.csv'])()
    strategy = Strategy(config=cfg,handle_data=handle_data_csv,initialize=initialize_csv)
    strategy.run(data,start=datetime(2012,1,1),finish=datetime(2014,12,12))

#*************************************************************************************
'''
This runs a monte-carlo sweep with train and test set.
'''
def run_train_test():
    def initialize_csv_opt(context):
            csv_fetcher(context,'data/MSFT.csv','signals')

    def init_optimization_csv(params):
        params.random_thresh = random.randint(23,200)
        params.random_nr = random.randint(23,200)

    def handle_data_opt(context):
        # print context.params.random_thresh
        if random.randint(0,context.params.random_thresh) == context.params.random_nr:
            order(context,'AAPL',random.randint(-2,2))

    return run_validation(CSVDataFactory,['data/MSFT.csv','data/AAPL.csv'],datetime(2012,1,1),datetime(2014,6,12),datetime(2015,6,12),10,
                    handle_data=handle_data_opt,
                    initialize=initialize_csv_opt,
                    init_optimization=init_optimization_csv,
                    config = cfg)

#*************************************************************************************
'''
This runs a simple monte-carlo sweep.
'''
def run_optimize():
    def initialize_csv_opt(context):
            csv_fetcher(context,'data/MSFT.csv','signals')

    def init_optimization_csv(params):
        params.random_thresh = random.randint(23,200)
        params.random_nr = random.randint(23,200)

    def handle_data_opt(context):
        # print context.params.random_thresh
        if random.randint(0,context.params.random_thresh) == context.params.random_nr:
            order(context,'AAPL',random.randint(-2,2))

    data = CSVDataFactory(['data/MSFT.csv','data/AAPL.csv'])()
    optimize = Optimize(config=cfg,handle_data=handle_data_opt,init_optimization=init_optimization_csv,initialize=initialize_csv_opt)
    optimize.run_mc_sweep(data,numb_runs=10,start=datetime(2012,1,1),finish=datetime(2013,12,12))
    return optimize.results

# #*************************************************************************************
'''
This runs a simple monte-carlo sweep with streaming data.
Here, we need to re-open the file for every new iteration.
Therefore, we have to pass the class name to data and initialize
it for every new iteration.
We also have to pass the source file name that is then passed
on when the data source is initialized.
'''
def init_stream_opt(params):
    params.random_thresh = random.randint(123,200)
    params.random_nr = 150 #random.randint(23,200)

def handle_data_stream_opt(context):
    # print context.params.random_thresh
    if random.randint(0,context.params.random_thresh) == context.params.random_nr:
        order(context,'A',random.randint(-1,2))


def run_stream_opt():
    cfg.LOG_FREQUENCY = 5
    optimize = Optimize(config=cfg,handle_data=handle_data_stream_opt,init_optimization=init_stream_opt)
    optimize.run_mc_sweep(StreamDataFactory,numb_runs=8,mode='stream',stream_fname='data/test_stream.csv')
    # print optimize.results
    return optimize.results

# #*************************************************************************************
'''
This runs a grid search optimisation.
'''
def initialize_grid_search(context):
    pass

def init_grid_search(params):
    params.alpha = range(5,35,5)
    params.beta = range(35,75,5)
    params.gamma = range(75,105,5)


def handle_data_grid_search(context):
    # print context.params.current,get_current_date(context)
    for symbol in ['B','A']:
        try:
            MA1 = mean(get_history(context,symbol,field='ask',period=context.params.current[0]))
            MA2 = mean(get_history(context,symbol,field='ask',period=context.params.current[1]))
            MA3 = mean(get_history(context,symbol,field='ask',period=context.params.current[2]))
            S = 1
            if MA1+S < MA2 < MA3-S:
                order(context,symbol,1)
            elif MA1-S > MA2 > MA3+S:
                order(context,symbol,-1)

        except: pass


def run_grid_search():
    from config import config as cfg
    cfg.LOG_FREQUENCY = 5
    optimize = Optimize(config=cfg,handle_data=handle_data_grid_search,init_optimization=init_grid_search,initialize=initialize_grid_search)
    optimize.run_grid_search(StreamDataFactory,mode='stream',stream_fname='data/test_stream.csv')
    return optimize.results

#*************************************************************************************
#*************************************************************************************
def walk_forward(instruments,start,finish,train_period,test_period,num_runs):
    def initialize(context):
            csv_fetcher(context,'data/MSFT.csv','mysig')

    def init_optimization(params):
        params.random_thresh = random.randint(1,20)
        params.random_nr = random.randint(1,20)


    def handle_data(context):
        k = context.signals['mysig']
        if random.randint(0,context.params.random_thresh) == context.params.random_nr:
            order(context,'AAPL',random.randint(-2,2))


    run_walk_forward(CSVDataFactory,
                    instruments,
                    start,
                    finish,
                    train_period,
                    test_period,
                    num_runs,
                    handle_data=handle_data,
                    initialize=initialize,
                    init_optimization=init_optimization,
                    config=cfg)

def run_bitstamp():
    def handle_data_stream(context):
        print 'current:',context.current['BTC'].one,context.current['BTC'].four
        if random.randint(0,100) == 23:
            order(context,'BTC',random.randint(-1,2))

    data = BitstampFactory()
    strategy = BitcoinStrategy(config=cfg,handle_data=handle_data_stream)
    strategy.tick_stream(data)


#*************************************************************************************

if __name__=='__main__':
    # run_csv()
    # run_web()
    # run_live()
    # run_random()
    # run_stream()
    # run_stream_opt()
    # print run_optimize()
    # print run_train_test()
    # walk_forward(['data/MSFT.csv','data/AAPL.csv'],datetime(2012,1,1),datetime(2015,6,12),timedelta(days=100),timedelta(days=50),40)
    # run_grid_search()
    # run_switchover()
    run_bitstamp()

