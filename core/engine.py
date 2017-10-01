import sys
sys.dont_write_bytecode = True
from core.utils import get_current_date,parse_d
import cPickle
from collections import deque
import traceback
from pylab import *
from numpy import *
from pandas import DataFrame,Series,Panel
import json
import bcolz
from core.logger import Logging
from copy import deepcopy
from datetime import datetime
# from ipdb import set_trace
from core.portfolio import *
from core.performance import Performance
from core.order import *
logger = Logging(__name__,'/tmp/slackline.log').logger

def handle_data(context):
    pass

def initialize(context):
    pass

def init_optimization(params):
    pass

def config():
    pass

class Tick():
    pass



class Context():
    def __init__(self):
        self.portfolio = Portfolio(self)
        self.load = {}
        self.order_pos = {}
        self.before_trading = True
        self.tick = {}
        self.current = {}
        self.order_submission_time = {}
        self.order_submission_price = {}
        self.signals = {}
        self.stream_history = {}
        self.recorder = {}
        self.this_transactions = []
        self.this_orders = []
        self.execution_field = {}
        self.current_minute = -1
        self.current_hour = -1
        self.current_day = -1
        self.current_month = -1
        self.current_second = -1
        self.market_open = False
        self.trades =[]
        self.exec_message = {}

    def record(self,field,value):
        current_date = get_current_date(self)
        if not current_date in self.recorder.keys():
            self.recorder[current_date]={}
        self.recorder[current_date][field] = value

class DataSource():
    def __init__(self,data):
        self.data = data

    def _emit_data(self):
        index = self.data[self.data.keys()[0]].index
        keys = self.data.keys()
        for date in index:
            data = {}
            for k in self.data:
                data[k] = self.data[k].T[date]
            yield date,data


class Strategy():
    def __init__(self,config=config,handle_data=handle_data,initialize=initialize):
        self.context = Context()
        self.context.performance = Performance(config)
        self.config = config
        self.context.config = config
        self.handle_data = handle_data
        self.initialize = initialize
        self.context.symbols = []
        self.error_count = 0
        self.context.portfolio.cash = config.INITIAL_CASH
        self.count = 0
        if self.config.LOG_TRADES_TO_FILE:
            fid = open(self.config.TRADES_FILE,'w')

    def run(self,data,start=datetime(1970,1,1),finish=datetime(2050,1,1)):
        self.context.mode = 'bulk'
        self.context.data = data
        self.initialize(self.context)
        self.data_source = DataSource(data)
        q = self.data_source._emit_data()

        finished = False
        while not finished:
            self.context.this_transactions = []
            self.context.this_orders = []
            # sys.stdout.write("\rTrading Periods --> %s  " % self.context.performance.trading_periods)
            # sys.stdout.flush()
            if not finished:
                try:
                    date,dat = q.next()
                    self.context.current_date = date
                    self.context.symbols = dat.keys()
                    self.context.current = dat
                except:
                    # print '\n\n*****data finished*****\n\n'
                    finished = True
                    logger.warning(traceback.format_exc())
            for key in self.context.current:
                if key in self.context.load:
                    if self.context.load[key] == 0 and self.config.DELAYED_EXECUTION:
                        order_execution(self.context,key)
                        self.context.load[key] = -1
                    else:
                        self.context.load[key] -= 1

            if not finished:
                if not(start < date < finish):
                    if date < finish:
                        continue
                    else:
                        break

                self.context.performance.dates.append(date)
                try: self.handle_data(self.context)
                except:
                    pass
                    print traceback.format_exc()
                self.context.performance.log(self.context)

        result = self.context.performance.get_results(self.context)
        result.to_csv(open(self.config.RESULTS_FILE,'w'))
        return result



    def tick_stream(self,data,start=datetime(1970,1,1),finish=datetime(2050,1,1)):
        '''
        Ticks need to be in the form:
        {'ask': 22038, 'bid': 22036, 'ticker': 'A', 'time': '2016-12-16 12:34:23.28195'}
        '''
        self.context.mode = 'stream'
        self.config.DELAYED_EXECUTION = True
        finished = False
        self.initialize(self.context)
        self.context.data = data
        while not finished:
            self.count += 1
            self.context.this_transactions = []
            self.context.this_orders = []
            try:
                from_source = data.mydata()
                if not from_source:
                    self.error_count += 1
                    if self.error_count > 100:
                        finished = True
                    else:
                        continue
                from_source = from_source.replace("'",'"')
                line = json.loads(from_source)
                try:
                    key = line['ticker']
                    if not key in self.context.symbols:
                        self.context.symbols.append(key)
                    self.context.current[key] = Tick()
                    self.context.current[key].one = line['bid']
                    self.context.current[key].four = line['ask']
                    self.context.current[key].date = line['time']
                    self.context.performance.dates.append(line['time'])
                    if key in  self.context.stream_history:
                        self.context.stream_history[key].append({'bid':line['bid'],'ask':line['ask'],'time':line['time']})
                    else:
                        self.context.stream_history[key] = deque(maxlen=self.context.config.STREAM_HISTORY_LEN)
                        self.context.stream_history[key].append({'bid':line['bid'],'ask':line['ask'],'time':line['time']})
                    self.error_count = 0
                except:
                    logger.warning(traceback.format_exc())
                    print traceback.format_exc()
                    self.error_count += 1
            except ValueError:
                pass
                # print '--------------------------------'
                logger.warning(traceback.format_exc())
                # print '--------------------------------'
                # print '\n\n*****data finished*****\n\n'

            if key in self.context.load:
                if self.context.load[key] == 0:
                    tick_execution(self.context,key)
                    self.context.load.pop(key)
                else:
                    self.context.load[key]-=1

            if not finished:
                if not(start < parse_d(self.context.current[key].date) < finish):
                    if parse_d(self.context.current[key].date) < finish:
                        continue
                    else:
                        break
                try: self.handle_data(self.context)
                except:
                    logger.warning(traceback.format_exc())
                if not self.count%self.config.LOG_FREQUENCY:
                    self.context.performance.log(self.context)

        result = self.context.performance.get_results(self.context)
        result.to_csv(open(self.config.RESULTS_FILE,'w'))
        return result

if __name__=="__main__":
    source = DataSource()
