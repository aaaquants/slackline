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
import traceback
logger = Logging(__name__).logger

def initialize_csv(context):
        csv_fetcher(context,'data/MSFT.csv','signals')

def handle_data_csv(context):
    if random.randint(0,context.A) == 3:
        order(context,'MSFT',random.randint(-1,2))
    if random.randint(0,context.A) == 3:
        order(context,'AAPL',random.randint(-1,2))

def run_csv(A):
    data = CSVDataFactory(['data/MSFT.csv','data/AAPL.csv'])()
    strategy = Strategy(config,handle_data=handle_data_csv,initialize=initialize_csv)
    strategy.context.A = A
    result = strategy.run(data,start=datetime(2012,1,1),finish=datetime(2014,12,12))
    return result

def prepare_fig(perf):
    plot(perf['pnl'])

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


def compute(A):
    perf = run_csv(A)
    return prepare_fig(perf)



if __name__=="__main__":
    print compute(30)
