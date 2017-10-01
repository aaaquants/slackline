from core.utils import *


def order(context,instrument,pos,field='four'):
    context.execution_field['instrument'] = field

    # THIS TRIGGERS IF WE SPECIFY THE WRONG INSTRUMENT
    if len(context.portfolio.positions) and (not instrument in context.portfolio.positions) and context.before_trading==True:
        print '---Trying to order wrong instrument---',instrument
        exit()
    context.before_trading = False
    context.order_pos[instrument] = pos

    if context.config.DELAYED_EXECUTION == False:
        context.load[instrument] = -1
        # WE DON'T HAVE EXECUTION LOSSES HERE
        _ct = get_current_date(context)
        context.order_submission_time[instrument] = _ct

        # 'ask' is later used for the 'close' field as well
        context.order_submission_price[instrument] = {'one':context.current[instrument].one,'four':context.current[instrument].four}
        order_execution(context,instrument)

    elif context.config.DELAYED_EXECUTION == True and context.config.DELAY_CYCLES == 0:
        context.load[instrument] = -1
        # WE DON'T HAVE EXECUTION LOSSES HERE
        _ct = get_current_date(context)
        context.order_submission_time[instrument] = _ct

        # 'ask' is later used for the 'close' field as well
        context.order_submission_price[instrument] = {'one':context.current[instrument].one,'four':context.current[instrument].four}
        tick_execution(context,instrument)

    else:
        context.load[instrument] = context.config.DELAY_CYCLES-1
        # SETTING UP EXECUTION DELAY
        _ct = get_current_date(context)
        if not instrument in context.order_submission_time or not context.order_submission_time[instrument]:
            context.order_submission_time[instrument] = _ct
            # 'ask' is later used for the 'close' field as well
            context.order_submission_price[instrument] = {'one':context.current[instrument].one,'four':context.current[instrument].four}

        if context.config.PRINT_TRADES:
            print 'Order Loaded',instrument,pos,_ct,getattr(context.current[instrument],context.execution_field['instrument'])
            pass



def order_execution(context,instrument):
    '''
    This function executes bar data
    '''
    current_date = get_current_date(context)
    # EXECUTION VECTOR ALREADY EXISTS
    if instrument in context.portfolio.positions:
        context.portfolio.positions[instrument].append(context.order_pos[instrument])
        context.portfolio.entry[instrument].append(current_date)
        context.portfolio.price[instrument].append(getattr(context.current[instrument],context.execution_field['instrument']))
        context.portfolio.execution_time[instrument].append(current_date-context.order_submission_time[instrument])

        side = sign(context.order_pos[instrument])
        # Here we call the field 'ask' while it should be 'close' for consistency
        context.portfolio.execution_loss[instrument].append((getattr(context.current[instrument],context.execution_field['instrument'])-context.order_submission_price[instrument][context.execution_field['instrument']])*side)

    # EXECUTION VECTOR DOES NOT EXIST YET
    else:
        context.portfolio.positions[instrument]=[context.order_pos[instrument]]
        context.portfolio.entry[instrument] = [current_date]
        context.portfolio.price[instrument] = [getattr(context.current[instrument],context.execution_field['instrument'])]
        context.portfolio.execution_time[instrument] = [current_date-context.order_submission_time[instrument]]

        side = sign(context.order_pos[instrument])
        # Here we call the field 'ask' while it should be 'close' for consistency
        context.portfolio.execution_loss[instrument] = \
        [(getattr(context.current[instrument],context.execution_field['instrument'])-context.order_submission_price[instrument][context.execution_field['instrument']])*side]

    context.order_submission_time[instrument] = None
    context.portfolio.cash -= context.order_pos[instrument]*context.portfolio.price[instrument][-1]
    reporting(context,instrument,0,current_date)


def tick_execution(context,instrument):
    '''
    This function executes tick data
    '''
    current_date = get_current_date(context)
    # EXECUTION VECTOR ALREADY EXISTS
    if instrument in context.portfolio.positions:
        context.portfolio.positions[instrument].append(context.order_pos[instrument])
        context.portfolio.entry[instrument].append(current_date)
        context.portfolio.execution_time[instrument].append(current_date-context.order_submission_time[instrument])
        if context.config.EXEC_MODE=='cross':
            # ON THE LONG SIDE
            if context.order_pos[instrument]>=0:
                context.portfolio.price[instrument].append(context.current[instrument].four)
                context.portfolio.execution_loss[instrument].append(context.current[instrument].four-context.order_submission_price[instrument]['four'])
            # ON THE SHORT SIDE
            else:
                context.portfolio.price[instrument].append(context.current[instrument].one)
                context.portfolio.execution_loss[instrument].append(context.current[instrument].one-context.order_submission_price[instrument]['one'])
        elif context.config.EXEC_MODE == 'mid':
            context.portfolio.price[instrument].append((context.current[instrument].four+context.current[instrument].one)/2.)
            context.portfolio.execution_loss[instrument].append((context.current[instrument].four+context.current[instrument].one)/2.-(context.order_submission_price[instrument]['four']+context.order_submission_price[instrument]['one'])/2.)

    # EXECUTION VECTOR DOES NOT EXIST YET
    else:
        context.portfolio.positions[instrument]=[context.order_pos[instrument]]
        context.portfolio.entry[instrument] = [current_date]
        context.portfolio.execution_time[instrument] = [current_date-context.order_submission_time[instrument]]
        if context.config.EXEC_MODE=='cross':
            # ON THE LONG SIDE
            if context.order_pos[instrument]>=0:
                context.portfolio.price[instrument] = [context.current[instrument].four]
                try: context.portfolio.execution_loss[instrument].append(context.current[instrument].four-context.order_submission_price[instrument]['four'])
                except: context.portfolio.execution_loss[instrument] = [context.current[instrument].four-context.order_submission_price[instrument]['four']]
            # ON THE SHORT SIDE
            else:
                context.portfolio.price[instrument] = [context.current[instrument].one]
                try: context.portfolio.execution_loss[instrument].append(context.current[instrument].one-context.order_submission_price[instrument]['one'])
                except: context.portfolio.execution_loss[instrument] = [context.current[instrument].one-context.order_submission_price[instrument]['one']]
        elif context.config.EXEC_MODE == 'mid':
            context.portfolio.price[instrument] = [(context.current[instrument].four+context.current[instrument].one)/2.]
            try: context.portfolio.execution_loss[instrument].append((context.current[instrument].four+context.current[instrument].one)/2. \
                    -(context.order_submission_price[instrument]['four']+context.order_submission_price[instrument]['one'])/2.)
            except: context.portfolio.execution_loss[instrument] = [(context.current[instrument].four+context.current[instrument].one)/2. \
                    -(context.order_submission_price[instrument]['four']+context.order_submission_price[instrument]['one'])/2.]


    if context.order_pos[instrument] < 0:
        context.execution_field['instrument'] = 'one'
    else:
        context.execution_field['instrument'] = 'four'

    context.order_submission_time[instrument] = None
    context.portfolio.cash -= context.order_pos[instrument]*context.portfolio.price[instrument][-1]
    reporting(context,instrument,0,current_date)

class Equity:
    def __init__(self,quantity,symbol=None,asset_name=None,exchange=None,tz='UTC'):
        self.quantity = quantity
        self.symbol = symbol
        self.asset_name = asset_name
        self.exchange = exchange
        self.tz = tz


def reporting(context,instrument,commission,current_date):
    positions = sum(context.portfolio.positions[instrument])
    if len(context.performance.pnl_curve):
        pnl = context.performance.pnl_curve[-1]
    else: pnl = 0
    msg = (str(get_current_date(context)), \
            'EXECUTION:',instrument, \
            ' quantity:',context.order_pos[instrument],\
            ' price:',getattr(context.current[instrument],context.execution_field['instrument']), \
            ' positions:',positions,
            ' pnl:',round(pnl,3),
            ' msg:',str(context.exec_message))
    logger.info(msg)
    order_id = random.randint(10000000,100000000)
    if context.config.PRINT_TRADES:
        print msg

    if context.config.LOG_TRADES_TO_FILE:
        fid = open(context.config.TRADES_FILE,'a')
        fid.write(str(msg)+'\n')
        fid.close()

