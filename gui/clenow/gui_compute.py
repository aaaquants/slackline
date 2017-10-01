import sys
sys.dont_write_bytecode = True
from datetime import datetime,timedelta
from core.data_factory import *
from core.engine import *
from core.utils import *
from pylab import plot,show
import os,time,glob
from core.logger import Logging
import config.config as config
from dateutil.parser import parse
import traceback
from talib import ATR
logger = Logging(__name__).logger



# symbols = ['MSFT','AAPL','IBM','CSCO','GOOG','F','XOM','AMZN','GE','T','JPM','WFC','BAC','KO','INTC']
# symbols = ['MSFT','AAPL','IBM']

def initialize_csv(context):
    # context.ma_lkbk = 200
    # context.atr_lkbk = 20
    # context.lr_lkbk = 200
    # context.max_items = 1
    # context.risk_factor = 0.01
    context.long_range_slope_lkbk = 250

def handle_data_csv(context):
    long_range_slopes = []
    try:
        liq = context.performance.get_latest_performance()['portfolio_value']
    except:
        liq = 0
    new_pos_sizes = []
    isbull = []
    symbols=context.data.items
    for symbol in symbols:
        hist = get_history(context,symbol,'500D','four')
        MA = mean(hist)
        isbull.append(get_current_price(context,symbol)>MA)
        try:
            lr =stats.linregress(range(len(hist)),hist)
            atr = ATR(asarray(get_history(context,symbol,'500D','two')),
                      asarray(get_history(context,symbol,'500D','three')),
                      asarray(get_history(context,symbol,'500D','four')),
                      context.atr_lkbk)[-1]
            new_pos_sizes.append(floor(liq * context.risk_factor / atr))
            long_range_slopes.append(lr[0]*abs(lr[2])*context.long_range_slope_lkbk)
        except:
            new_pos_sizes.append(np.nan)
            long_range_slopes.append(np.nan)
            print traceback.format_exc()

    tradable_symbols = argsort(long_range_slopes[::-1])[:context.max_items]
    for i,symbol in enumerate(symbols):
        if isnan(new_pos_sizes[i]) or isnan(long_range_slopes[i]): continue
        if symbol in context.portfolio.positions:
            order_size = new_pos_sizes[i] - sum(context.portfolio.positions[symbol])
            if isbull[i] and (i in tradable_symbols) and order_size:
                order(context,symbol,order_size)
            elif not isbull[i] and sum(context.portfolio.positions[symbol]):
                order(context,symbol,-sum(context.portfolio.positions[symbol]))
        else:
            order_size = new_pos_sizes[i]
            if isbull[i] and (i in tradable_symbols) and order_size:
                order(context,symbol,order_size)



def run_csv(start,finish,symbols,lr_lkbk,ma_lkbk,atr_lkbk,risk_factor,max_items):
    sep_symbols = symbols.split(',')

    data = WebDataFactory(sep_symbols,
                          start,
                          finish,
                          source='google')()

    strategy = Strategy(config,handle_data=handle_data_csv,initialize=initialize_csv)

    strategy.context.lr_lkbk = lr_lkbk
    strategy.context.ma_lkbk = ma_lkbk
    strategy.context.atr_lkbk = atr_lkbk
    strategy.context.risk_factor = risk_factor
    strategy.context.max_items = max_items

    result = strategy.run(data,start=parse(start),finish=parse(finish))
    return result


def prepare_fig(result):
    plot(result.date,result.pnl)
    ylabel('PnL')

    if not os.path.isdir('static'):
        os.mkdir('static')
    else:
        # Remove old plot files
        for filename in glob.glob(os.path.join('static', '*.png')):
            os.remove(filename)
    # Use time since Jan 1, 1970 in filename in order make
    # a unique filename that the browser has not chached
    plotfile = os.path.join('static', str(time.time()) + '.png')
    plt.savefig(plotfile)
    return plotfile


def compute(start,finish,symbols,lr_lkbk,ma_lkbk,atr_lkbk,risk_factor,max_items):
    perf = run_csv(start,finish,symbols,lr_lkbk,ma_lkbk,atr_lkbk,risk_factor,max_items)
    return prepare_fig(perf)



if __name__=="__main__":
    print compute(30)
