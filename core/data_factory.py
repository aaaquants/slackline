import sys
sys.dont_write_bytecode = True
import bcolz
import os
from scipy import stats
from pylab import *
from datetime import datetime
from dateutil.parser import parse
from numpy import *
import numpy as np
import json
from time import sleep
import pandas_datareader.data as web
from pandas import DataFrame,date_range,Series,Panel,read_csv,MultiIndex
from core.logger import Logging
from googlefinance import getQuotes
from config import random_factory_config as rcfg
import traceback
logger = Logging(__name__,'/tmp/slackline.log').logger

class RandomDataFactory():
    def __init__(self,rcfg):
        self.periods = rcfg.PERIODS
        self.N = rcfg.N
        self.trend_bias = rcfg.TREND_BIAS
        self.start = rcfg.START
        self.start_price = rcfg.START_PRICE
        self.freq = rcfg.FREQ
        self.resample_freq = rcfg.RESAMPLE_FREQ
        self.create_data()

    def create_data(self):
        index = date_range(self.start,freq=self.freq,periods=self.periods)
        k = cumsum(random.randn(self.periods,self.N)+self.trend_bias,0)*random.random(self.N)+self.start_price
        self.data = {}
        for i in range(self.N):
            df = DataFrame(k[:,i],index=index).resample(self.resample_freq).ohlc()
            df.columns = ['one','two','three','four']
            df['date'] = df.index
            df.index.name = 'date'
            self.data[str(i)] = df
        self.mydata = Panel(self.data)

    def __call__(self):
        return self.mydata


class WebDataFactory():
    def __init__(self,symbols,start,end,source='yahoo'):
        self.start = start
        self.end = end
        self.source = source
        self.symbols = symbols
        self.panel=web.DataReader(self.symbols, self.source, self.start, self.end)
        self.panel = self.panel.transpose(2,1,0)
        self.create_data()

    def create_data(self):
        self.mydata = {}
        for i in self.symbols:
            index_mod = [int((ii - datetime(1970,1,1)).total_seconds()) for ii in self.panel[str(i)].index]
            self.panel[str(i)]['date'] = index_mod
            self.panel[str(i)].columns = ['one','two','three','four','five','date']

    def __call__(self):
        return self.panel

class CSVDataFactory:
    '''
    This reads csv price data. The columns are labelled one to five since we sometimes have bid/ask and
    sometimes ohlc. The data are received like this:
    ----------------------------------------------------------
    data = CSVDataFactory(['data/MSFT.csv','data/AAPL.csv'])()
    ----------------------------------------------------------
    '''
    def __init__(self,fnames):
        self.data = {}
        for fname in fnames:
            df = read_csv(fname,index_col=[0],parse_dates=True)
            df.columns = ['one','two','three','four','five']
            df.index.name = 'date'
            df['date'] = df.index
            self.data[str(fname.split('.')[0].replace('data/',''))] = df
        self.mydata = Panel(self.data)

    def __call__(self):
        return self.mydata

class GoogLiveFactory():
    '''
    This gets live streaming data from google finance
    ----------------------------------------------------------
    data = GoogLiveFactory(['CURRENCY:EURAUD','CURRENCY:USDAUD'])
    ----------------------------------------------------------
    '''
    def __init__(self,symbols,delay=True):
        self.symbols = symbols
        self.func = self.source()
        self.RAND_DELAY = delay

    def random_sleep(self):
        sleep(1+abs(random.randn()))

    def source(self):
        while True:
            if self.RAND_DELAY:
                self.random_sleep()

            quotes = json.loads(json.dumps(getQuotes(self.symbols), indent=2))
            for quote in quotes:
                tick = {'bid':float(quote['LastTradePrice']),'ask':float(quote['LastTradePrice']),'ticker':quote['Index']+':'+quote['StockSymbol'],'time':str(datetime.now())}
                yield json.dumps(tick)

    def mydata(self):
        return self.func.next()

class StreamDataFactory():
    def __init__(self,fname):
        self.fid = open(fname)

    def mydata(self):
        return self.fid.readline()


if __name__=="__main__":
    pass

    # fact = WebDataFactory(["F","IBM","CSCO","GOOG"],datetime(2010, 1, 1),datetime(2017, 1, 1),source='google')()
    # print fact

    # data = CSVDataFactory(['data/AAPL.csv','data/MSFT.csv'])
    # print data.mydata

    # data = CSVDataFactory2(['data/AAPL.csv','data/MSFT.csv','data/ETR.csv'])
    # print data.mydata

    # data = GoogLiveFactory(['MSFT'])
    # data = GoogLiveFactory(['CURRENCY:EURAUD,CURRENCY:USDAUD'])
    # for i in range(200):
        # print data.mydata()

    # data = RandomDataFactory(rcfg)
    # print data.mydata

    # data = StreamDataFactory('data/test_stream.csv')
    # print data.mydata()

