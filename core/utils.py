import sys
sys.dont_write_bytecode = True
from datetime import datetime,timedelta
from dateutil.parser import parse
from pandas import read_csv,Series,DataFrame
from numpy import *
import numpy as np
import bcolz
from core.logger import Logging
import config.config as config
# from ipdb import set_trace
logger = Logging(__name__,'/tmp/slackline.log').logger


def handle_data(context):
    pass

def initialize(context):
    pass

def init_optimization(params):
    pass

def parse_d(d):
    '''
    Parse a fixed date format. Much faster than the dateutil parser.
    '''
    # print d
    year = int(d[:4])
    month = int(d[5:7])
    day = int(d[8:10])
    hour = int(d[11:13])
    minute = int(d[14:16])
    second = int(d[17:19])
    microsecond = int(d[20:])
    return datetime(year, month, day, hour, minute, second, microsecond)

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


def csv_fetcher(context,fname,name):
    '''
    This takes time-stamped signals from a csv file, turns them into
    unix timestamps and aligns them with the price data timestamps.
    -----------------------------------------------------------
    csv_fetcher(context,'data/MSFT.csv','signals')
    -----------------------------------------------------------
    '''
    # READ csv FILE AND REINDEX TO UNIX TIMESTAMP
    signals = read_csv(fname,index_col=[0],parse_dates=True)
    signals_new =[]
    for key in signals.keys():
        signals_new.append(Series(asarray(signals[key]),signals.index,name=key))

    # GET INDEX OF UNIX TIMESTAMPED PRICE DATA
    index_of_price_data = context.data[context.data.keys()[0]]

    # CREATE DATAFRAME FROM TIME SERIES
    df = DataFrame(signals_new).T

    # APPEND SIGNAL TO context.signals
    context.signals[name] = df

def get_from_fetcher(context,name,period,field):
    '''
    This gets historical signals from the fetcher. The field needs to be
    specified with a lambda function sice we call a bcolz field which does
    not have a label. The call looks like this:
    -----------------------------------------------------------
    get_signals(context,'signals','5D',lambda x:x.Close)
    -----------------------------------------------------------
    '''
    if 'S' in period:
        seconds = int(period.replace('S',''))
    elif 'M' in period:
        seconds = int(period.replace('M',''))*60
    elif 'H' in period:
        seconds = int(period.replace('H',''))*3600
    elif 'D' in period:
        seconds = int(period.replace('D',''))*86400

    try:
        current_date = context.current_date
        start_date = current_date - timedelta(0,seconds)
        mask = (context.signals[name].index >= start_date) & (context.signals[name].index <= current_date)
        return context.signals[name].loc[mask][field]
    except:
        return np.nan

def get_current_price(context,ticker,field='four'):
    try:
        return getattr(context.current[ticker],field)
    except:
        return None

def is_new_second(context):
    this_second = str(max([context.current[key].date for key in context.current.keys()])).split(":")[2].split(".")[0]
    if this_second != context.current_second:
        new_second = True
    else:
        new_second = False
    context.current_second = this_second
    return new_second

def is_new_minute(context):
    this_minute = str(min([context.current[key].date for key in context.current.keys()])).split(":")[1]
    if this_minute != context.current_minute:
        new_minute = True
    else:
        new_minute = False
    context.current_minute = this_minute
    return new_minute

def is_new_hour(context):
    this_hour = str(min([context.current[key].date for key in context.current.keys()])).split(" ")[1].split(":")[0]
    if this_hour != context.current_hour:
        new_hour = True
    else:
        new_hour = False
    context.current_hour = this_hour
    return new_hour

def is_new_day(context):
    this_day = str(min([context.current[key].date for key in context.current.keys()])).split(" ")[0].split("-")[2]
    if this_day != context.current_day:
        new_day = True
    else:
        new_day = False
    context.current_day = this_day
    return new_day

def is_new_month(context):
    this_month = str(min([context.current[key].date for key in context.current.keys()])).split(" ")[0].split("-")[1]
    new_month = False
    if this_month != context.current_month:
        new_month = True
    else:
        new_month = False
    context.current_month = this_month
    return new_month

def is_trading_day(context,market_open,market_close):
    '''
    This function takes integers for the opening and closing times for speed reasons.
    So, 9:15AM would be 915, 4:30PM would be 1630.
    '''
    this_time = int("".join(str(min([context.current[key].date for key in context.current.keys()])).split(" ")[1].split(":")[0:2]))
    opening = False
    if context.market_open==False and this_time > market_open and this_time<market_close:
        context.market_open = True
        opening = True
    elif this_time>=market_close and context.market_open:
        context.market_open = False
        opening = False
    return opening

def get_current_date(context):
    try:
        return context.current_date
    except:
        is_proper_date = False
        i = 0
        while not is_proper_date:
            try:
                date = parse(context.current[context.current.keys()[i]].date)
                is_proper_date = True
                return date
            except:
                i += 1

def get_history(context,instrument,period=None,field=None):
    '''
    This functions calls historical data from the price series.
    '''
    if period and type(period) is str:
        if 'S' in period:
            seconds = int(period.replace('S',''))
        elif 'M' in period:
            seconds = int(period.replace('M',''))*60
        elif 'H' in period:
            seconds = int(period.replace('H',''))*3600
        elif 'D' in period:
            seconds = int(period.replace('D',''))*86400

    if field == 'four':
        this_row = lambda row: row.four
    elif field == 'one':
        this_row = lambda row: row.one
    elif field == 'two':
        this_row = lambda row: row.two
    elif field == 'three':
        this_row = lambda row: row.three

    if context.mode == 'bulk':
        current_date = context.current_date
        start_date = current_date - timedelta(0,seconds)
        mask = (context.data[instrument].index >= start_date) & (context.data[instrument].index <= current_date)
        return context.data[instrument].loc[mask][field]

    if context.mode == 'stream':
        current_date = context.current[context.current.keys()[0]].date
        if not period:
            return [i[field] for i in context.stream_history[instrument]]
        elif type(period)==str:
            return [i[field] for i in context.stream_history[instrument] if (parse_d(current_date) - parse_d(i['time'])).total_seconds()<seconds]
        elif type(period == int):
            if instrument in context.stream_history:
                return [i[field] for i in list(context.stream_history[instrument])[-period:]]
            else: return [np.nan]

