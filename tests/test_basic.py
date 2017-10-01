import sys
sys.dont_write_bytecode = True
import unittest
from datetime import datetime
from core.data_factory import *
from core.engine import Strategy
from core.utils import get_history, get_current_date
from core.order import order
import config.test_config as tcfg
from ipdb import set_trace

def initialize_test(context):
    context.count = 0


def handle_data(context):
    context.count += 1
    if not context.count%10:
        order(context,'1',1)


class TestCode(unittest.TestCase):
    def test_data_factory(self):
        tcfg.PRINT_TRADES = False
        data = RandomDataFactory(tcfg)()
        self.assertTrue('1' in data.keys())
        self.assertTrue(len(data['0'])==100)

        data = WebDataFactory(["F"],datetime(2010, 1, 1),datetime(2010, 1, 10),source='google')()
        self.assertTrue('F' in data)
        self.assertTrue(len(data['F'])==5)

        data = CSVDataFactory(['data/MSFT.csv'])()
        self.assertTrue('MSFT' in data)

        data = eval(StreamDataFactory('data/test_stream.csv').mydata())
        self.assertTrue('bid' in data)
        self.assertTrue('ask' in data)
        self.assertTrue('time' in data)

        d = GoogLiveFactory(['AAPL','GOOG'],delay=False)
        data = d.mydata()
        self.assertTrue('bid' in data)
        self.assertTrue('ask' in data)
        self.assertTrue('time' in data)

    def test_utils(self):
        data = RandomDataFactory(tcfg)()
        tcfg.DELAYED_EXECUTION = False
        tcfg.PRINT_TRADES = False
        strategy = Strategy(tcfg,initialize=initialize_test,handle_data=handle_data)
        perf = strategy.run(data)

        # Testing performance
        self.assertTrue('pnl' in perf.keys())

        # Testing utility functions
        self.assertEqual(str(strategy.context.current['1'].date),'2000-01-05 03:00:00')
        self.assertEqual(get_current_date(strategy.context),datetime(2000,1,5,3))
        self.assertEqual(len(get_history(strategy.context,'1',period='1D',field='four')),25)
        self.assertEqual(len(get_history(strategy.context,'1',period='1H',field='four')),2)
        self.assertTrue(abs(mean(get_history(strategy.context,'1',period='1D',field='four'))-200)<20)

        # # Testing Order for immediate execution
        self.assertEqual(strategy.context.order_pos['1'],1)
        self.assertEqual(0,strategy.context.portfolio.execution_time['1'][3].total_seconds())
        self.assertTrue(0==strategy.context.portfolio.execution_loss['1'][3])


        # # Testing Order for delayed execution
        tcfg.DELAYED_EXECUTION = True
        tcfg.PRINT_TRADES = False
        strategy = Strategy(tcfg,handle_data=handle_data,initialize=initialize_test)
        perf = strategy.run(data)
        self.assertEqual(3600,strategy.context.portfolio.execution_time['1'][2].total_seconds())
        self.assertTrue(0!=strategy.context.portfolio.execution_loss['1'][3])



