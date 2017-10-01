from numpy import *
import numpy as np
import traceback
from core.utils import *
# from slackline.cythons.functions import cyth_pnl
logger = Logging(__name__,'/tmp/slackline.log').logger

class Performance():
    def __init__(self,config):
        self.cols = [u'AAPL', u'MOVAV', u'MSFT', u'algo_volatility',
       u'algorithm_period_return', u'alpha', u'benchmark_period_return',
       u'benchmark_volatility', u'beta', u'capital_used', u'ending_cash',
       u'ending_exposure', u'ending_value', u'excess_return',
       u'gross_leverage', u'information', u'long_exposure', u'long_value',
       u'longs_count', u'max_drawdown', u'max_leverage', u'net_leverage',
       u'orders', u'period_close', u'period_label', u'period_open', u'pnl',
       u'portfolio_value', u'positions', u'returns', u'sharpe',
       u'short_exposure', u'short_value', u'shorts_count', u'sortino',
       u'starting_cash', u'starting_exposure', u'starting_value',
       u'trading_periods', u'transactions', u'treasury_period_return']
        self.pnl_curve = []
        self.dates = []
        self.ddwn = []
        self.this_ddwn = []
        self.hwm = 0
        self.config = config
        self.perf_log = {}
        self.previous_date = None
        self.trading_periods = 0
        self.start_prices = {}
        self.benchmark_returns = []
        self.benchmark_value = []
        self.strategy_returns = [0]
        self.portf_vals = []

    def calc_execution_performance(self,context):
        times = {key:map(lambda x:x.total_seconds(),context.portfolio.execution_time[key]) for key in context.portfolio.execution_time.keys()}
        losses = context.portfolio.execution_loss
        return times, losses

    def plot_results(self,plot_result):
        if plot_result:
            plot(self.pnl_curve);show()

    def log(self,context,price_field='four',log_all=True):
        try:
            for key in context.symbols:
                if not key in self.start_prices:
                    if key in context.current and 'four' in dir(context.current[key]) and ~isnan(context.current[key].four):
                        self.start_prices[key] = context.current[key].four

            self.transactions = []
            self.trading_periods += 1
            current_date = get_current_date(context)

            # THE CYTHON IMPLEMENTATION IS VERY SLIGHTLY SLOWER.
            if context.config.EXEC_MODE=='mid': self.pnl_curve.append(context.portfolio.calc_pnl())
            # self.pnl_curve.append(cyth_pnl(context.portfolio))
            elif context.config.EXEC_MODE=='cross': self.pnl_curve.append(context.portfolio.fast_calc_pnl())
            if log_all:
                long_short = context.portfolio.calc_ls()
                short_exposure,long_exposure = context.portfolio.calc_exposure()
                current_portfolio_value = context.portfolio.cash+(long_exposure+short_exposure)
                start_prices = array([self.start_prices[k] for k in self.start_prices])
                self.perf_log[self.trading_periods] = {
                        'date':current_date,
                        'pnl':self.pnl_curve[-1],
                        'positions':long_short,
                        'long_exposure':long_exposure,
                        'short_exposure':short_exposure,
                        'portfolio_value':current_portfolio_value,
                        'cash':context.portfolio.cash,
                        'execution_loss': sum([sum(context.portfolio.execution_loss[key]) for key in context.portfolio.execution_loss])
                        }
        except:
            print traceback.format_exc()
            # print '---------------------->>>',context.current[key]
            logger.info(traceback.format_exc())


    def get_latest_performance(self):
        idx = self.perf_log.keys()
        if len(idx):
            return self.perf_log[max(idx)]
        else:
            return None

    def get_results(self,context):
        self.calc_execution_performance(context)
        results = DataFrame.from_dict(self.perf_log).T
        return results

