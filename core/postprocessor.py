import sys
sys.dont_write_bytecode = True
from pandas import read_csv
from pylab import *
from numpy import *
# from ipdb import set_trace
from dateutil.parser import parse

results = read_csv('../results/result.dat',index_col=0,parse_dates=True)
trades = open('../results/trades.dat')

tr = {}
dates = {}
for i in trades:
    line = eval(i)
    symbol = line[2]
    quantity = int(line[4])
    price = int(line[6])
    date = line[0]
    if symbol in tr:
        tr[symbol].append([quantity,price])
        dates[symbol].append(date)
    else:
        tr[symbol] = [[quantity,price]]
        dates[symbol] = [date]
realized_pnl = 0
final_positions = {}
number_of_trades = 0
pnl_per_instrument = {}
mean_pnl_per_instrument = {}
median_pnl_per_instrument = {}
position_sizes = {}
for symbol in tr:
    a = array(tr[symbol])
    pnl_per_instrument[symbol] = -sum(a[:,0]*a[:,1])
    mean_pnl_per_instrument[symbol] = -mean(a[:,0]*a[:,1])
    median_pnl_per_instrument[symbol] = -median(a[:,0]*a[:,1])
    realized_pnl += -sum(a[:,0]*a[:,1])
    final_positions[symbol] = sum(a[:,0])
    number_of_trades += a.shape[0]
    position_sizes[symbol] = cumsum(a[:,0])

mean_profit_per_trade = realized_pnl/float(number_of_trades)

print realized_pnl,final_positions,number_of_trades,mean_profit_per_trade,pnl_per_instrument,mean_pnl_per_instrument,median_pnl_per_instrument
show()




# set_trace()
long_count = []
short_count = []
positions = {}
positions_count = {}
count = 0
for pos in results.positions:
    count += 1
    pos = eval(pos)
    longs=0
    shorts = 0
    if not pos=={}:
        for key in pos:
            if pos[key]>0:
                longs+=1
            else:
                shorts+=1

            if key in positions:
                positions[key].append(pos[key])
                positions_count[key].append(count)
            else:
                positions[key] = [pos[key]]
                positions_count[key] = [count]
    long_count.append(longs)
    short_count.append(shorts)
alpha = []
beta = []
sharpe = []
sortino = []
volatility = []
delta = median(map(lambda x:x.total_seconds(),diff(map(parse,results.date))))
frequency = sqrt(86400/delta*252)
for i in range(10,len(results.index)):
    b,a = polyfit(
            (results.benchmark_value.ix[:i].pct_change()+1).cumprod().fillna(0),
            (results.portfolio_value.ix[:i].pct_change()+1).cumprod().fillna(0),
            1)
    alpha.append(a)
    beta.append(b)
    volatility.append(results.benchmark_value.ix[:i].pct_change().std()*frequency)
    if results.portfolio_value.ix[:i].pct_change().std():
        sharpe.append(
            results.portfolio_value.ix[:i].pct_change().mean()/
            results.portfolio_value.ix[:i].pct_change().std()*frequency)
        sortino.append(
            results.portfolio_value.ix[:i].pct_change().mean()/
            results.portfolio_value.ix[:i].pct_change()
                    [results.portfolio_value.ix[:i].pct_change()<0].std()*frequency)
    else:
        sharpe.append(0)
        sortino.append(0)


a = 6
b = 2
subplot(a,b,1)
results.pnl.plot()
ylabel('PnL')

subplot(a,b,2)
results.portfolio_value.plot()
ylabel('Portfolio Value')


subplot(a,b,3)
(results.portfolio_value.pct_change()+1).cumprod().plot()
(results.benchmark_value.pct_change()+1).cumprod().plot()
ylabel('Portfolio/Benchmark Returns')

subplot(a,b,4)
plot(results.index,long_count)
plot(results.index,short_count)
ylabel('Long/Short Count')

subplot(a,b,5)
plot(results.index[10:],beta)
plot(results.index[10:],alpha)
ylabel('Beta/Alpha')

subplot(a,b,6)
semilogy(results.index[10:],sharpe)
semilogy(results.index[10:],sortino)
ylabel('Sharpe/Sortino')

subplot(a,b,7)
plot(results.index[10:],volatility)
ylabel('Volatility')

subplot(a,b,8)
results.execution_loss.plot()
ylabel('Execution Loss')

subplot(a,b,9)
results.long_exposure.plot()
results.short_exposure.plot()
ylabel('Long/Short Exposure')

subplot(a,b,10)
((results.long_exposure-results.short_exposure)/results.portfolio_value).plot()
ylabel('Leverage')

subplot(a,b,11)
results.cash.plot()
ylabel('Cash')

subplot(a,b,12)
for key in positions:
    plot(positions_count[key],positions[key])
ylabel('Positions')

show()
