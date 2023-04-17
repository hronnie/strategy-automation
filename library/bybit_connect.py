from pybit import usdt_perpetual
import time
import os
from util_methods import get_formatted_price, get_formatted_quantity

def get_client(): 
    return usdt_perpetual.HTTP(
        endpoint="https://api.bybit.com",
        api_key=os.environ.get('BYBIT_API_KEY'),
        api_secret=os.environ.get('BYBIT_API_SECRET')
    )    

def get_symbol_info(logger, symbol):
    """
    Gets the symbol info from Bybit
    """
    logger.debug(f'Entered into get_symbol_info with the following parameters: symbol: {symbol}')
    try: 
        client_unauth = usdt_perpetual.HTTP(endpoint="https://api.bybit.com")
        symbol_info = client_unauth.query_symbol()['result']
        return [sym for sym in symbol_info if sym['name'] == symbol][0]    
    except Exception as e:
        error_msg = f"Couldn't get symbol info from Bybit {e}"
        logger.error(error_msg)
        raise Exception(error_msg)  
    

def buy_or_sell(logger, is_buy, symbol, dollar_amount, tp_percent=0, sl_percent=0, leverage=1, open_shift=0, entry_price_input=0, tp_price_input=0, sl_price_input=0): 
    """
    Creates a buy or sell order with their exit orders. You can set the exit orders with percentage or exact price. It will take which are not 0.
    Validation will filter out all invalid values.
    It creates conditional orders by default but if the main side entry price is exactly the current price then it catches Bybit exception and 
    creates a new market order.
    """
    logger.debug(f'Entered into buy_or_sell with the following parameters: is_buy: {is_buy}, symbol: {symbol}, dollar_amount: {dollar_amount}, tp_percent: {tp_percent}, sl_percent: {sl_percent}, leverage: {leverage}, open_shift: {open_shift}, entry_price_input: {entry_price_input}, tp_price_input: {tp_price_input}, sl_price_input: {sl_price_input}')
    try:
        client = get_client()
        bybit_current_price_str = get_current_price(logger, symbol, True)
        bybit_current_price = float(bybit_current_price_str)
        symbol_info = get_symbol_info(logger, symbol)
        position_info = client.my_position()['result']
    except Exception as e: 
        error_msg = f"Could get price from Bybit {e}"
        logger.error(error_msg)
        raise Exception(error_msg)    

    for data_dict in position_info:
        if data_dict['data']['symbol'] == symbol:
            current_leverage = data_dict['data']['leverage']
            break

    # ****** VALIDATION ******
    def validate():
        if sl_percent == 0 and sl_price_input == 0:
            print("Stop loss is not defined")
            return -1
        if tp_percent == 0 and tp_price_input == 0:
            print("Take profit is not defined")
            return -1
        if sl_percent > 0 and sl_price_input > 0:
            print("Stop loss is ambiguous")
            return -1
        if tp_percent > 0 and tp_price_input > 0:
            print("Take profit is ambiguous")
            return -1
        
        if tp_price_input > 0 and entry_price_input > 0: 
            if is_buy and tp_price_input < entry_price_input:
                print("tp_price_input should be greater than entry_price_input")
                return -1 
            if is_buy == False and tp_price_input > entry_price_input:
                print("tp_price_input should be less than entry_price_input")
                return -1
        
        if tp_price_input > 0 and entry_price_input == 0: 
            if is_buy and tp_price_input < bybit_current_price:
                print("tp_price_input should be greater than binance_current_price")
                return -1 
            if is_buy == False and tp_price_input > bybit_current_price:
                print("tp_price_input should be less than binance_current_price")
                return -1
        
        if sl_price_input > 0 and entry_price_input > 0: 
            if is_buy and sl_price_input > entry_price_input:
                print("sl_price_input should be less than entry_price_input")
                return -1 
            if is_buy == False and sl_price_input < entry_price_input:
                print("sl_price_input should be greater than entry_price_input")
                return -1
        
        if sl_price_input > 0 and entry_price_input == 0: 
            if is_buy and sl_price_input > bybit_current_price:
                print("sl_price_input should be less than binance_current_price")
                return -1 
            if is_buy == False and sl_price_input < bybit_current_price:
                print("sl_price_input should be greater than binance_current_price")
                return -1
        return 0
    validate_result = validate()
    if validate_result == -1: 
        return
    # ****** VALIDATION END ******

    def get_entry_price(symbol_info): 
        if entry_price_input == 0: 
            raw_entry_price = bybit_current_price
        else: 
            raw_entry_price = entry_price_input
        if is_buy: 
            raw_shifted_price = 0.01 * (100 - open_shift) * raw_entry_price
        else: 
            raw_shifted_price = 0.01 * (100 + open_shift) * raw_entry_price

        return get_formatted_price(logger, raw_shifted_price, symbol_info)

    def get_sl_price(symbol_info): 
        if sl_price_input == 0: 
            if is_buy:
                sl_raw_price = 0.01 * (100 - sl_percent) * float(entry_price)
            else: 
                sl_raw_price = 0.01 * (100 + sl_percent) * float(entry_price)
        else: 
            sl_raw_price = sl_price_input   
        return get_formatted_price(logger, sl_raw_price, symbol_info)

    def get_tp_price(symbol_info): 
        if tp_price_input == 0: 
            if is_buy: 
                tp_raw_price = 0.01 * (100 + tp_percent) * float(entry_price)
            else: 
                tp_raw_price = 0.01 * (100 - tp_percent) * float(entry_price)
        else: 
            tp_raw_price = tp_price_input   
        return get_formatted_price(logger, tp_raw_price, symbol_info)

    entry_price = get_entry_price(symbol_info)
    formatted_qty = get_formatted_quantity(logger, entry_price, leverage, symbol_info, dollar_amount)
    sl_price = get_sl_price(symbol_info)
    tp_price = get_tp_price(symbol_info)

    if current_leverage != leverage:
        try: 
            client.set_leverage(symbol=symbol, category='linear', buy_leverage=leverage, sell_leverage=leverage)
        except Exception as e:
            error_msg = f"Couldn't set leverage {e}"
            logger.error(error_msg)
            raise Exception(error_msg)        

    if is_buy:
        side_limit = 'Buy'
        position_idx = 1
    else: 
        side_limit = 'Sell'
        position_idx = 2

    try:
        client.place_conditional_order(   
            category = 'linear',
            symbol= symbol,
            side = side_limit,
            order_type = 'Market',
            qty = formatted_qty,
            price = entry_price,
            stop_px = entry_price,
            trigger_price = entry_price,
            base_price = bybit_current_price_str,
            take_profit=tp_price,
            stop_loss=sl_price,
            time_in_force = 'GoodTillCancel',
            reduce_only = False,
            close_on_trigger = False,
            position_idx=position_idx)
    except Exception as e: 
        if e.status_code == 130075:
            try:
                client.place_active_order(   
                    category = 'linear',
                    symbol= symbol,
                    side = side_limit,
                    order_type = 'Market',
                    qty = formatted_qty,
                    take_profit=tp_price,
                    stop_loss=sl_price,
                    time_in_force = 'GoodTillCancel',
                    reduce_only = False,
                    close_on_trigger = False,
                    position_idx=1)         
            except Exception as e:
                error_msg = f"Couldn't place order at Bybit {e}"
                logger.error(error_msg)
                raise Exception(error_msg)            


def close_position(logger, symbol, is_long_position):
    """
    Close one side position by the symbol.
    is_long_position = True: closes the long position
    is_long_position = False: closes the short position
    """
    logger.debug(f'Entered into close_position with the following parameters: symbol: {symbol}, is_long_position: {is_long_position}')
    try: 
        client = get_client()
        positions = client.my_position(category='linear',symbol=symbol)['result']
        position = None

        side = 'Buy' if is_long_position else 'Sell'
        close_side = 'Buy' if side == 'Sell' else 'Sell'
        position_idx = 1 if is_long_position else 2
        for pos_dict in positions: 
            if pos_dict['size'] > 0 and pos_dict['side'] == side:
                position = pos_dict
        if position == None:
            return
        client.place_active_order(   
            category = 'linear',
            symbol= symbol,
            side = close_side,
            order_type = 'Market',
            qty = position['size'],
            time_in_force = 'ImmediateOrCancel',
            reduce_only = True,
            close_on_trigger = True,
            position_idx=position_idx) 
    except Exception as e:
        error_msg = f"Couldn't place order at Bybit {e}"
        logger.error(error_msg)
        raise Exception(error_msg)       
    

def get_positions(logger, symbol):
    """
    Gets all position for the symbol both long and shorts
    """ 
    logger.debug(f'Entered into get_positions with the following parameters: symbol: {symbol}')
    time.sleep(1)
    try:        
        client = get_client()
        positions = client.my_position(category='linear',symbol=symbol)['result']
    except Exception as e:
        error_msg = f"Couldn't get positions from Bybit {e}"
        logger.error(error_msg)
        raise Exception(error_msg)    
    is_long_pos_exist = False
    is_short_pos_exist = False
    for pos_dict in positions: 
        if pos_dict['size'] > 0 and pos_dict['side'] == 'Buy':
            is_long_pos_exist = True
        if pos_dict['size'] > 0 and pos_dict['side'] == 'Sell':
            is_short_pos_exist = True
    return is_long_pos_exist, is_short_pos_exist


def get_orders(logger, symbol):
    """
    Get all orders for the symbol. This method can handle both active and conditional orders but ignores exit orders.
    """
    logger.debug(f'Entered into get_orders with the following parameters: symbol: {symbol}')
    time.sleep(1)
    try:    
        client = get_client()
        orders = client.get_conditional_order(category='linear', symbol=symbol, order_filter='Order')['result']['data']
        orders_active = client.get_active_order(category='linear', symbol=symbol, order_filter='Order')['result']['data']
    except Exception as e:
        error_msg = f"Couldn't get orders from Bybi {e}"
        logger.error(error_msg)
        raise Exception(error_msg)         
    is_long_order_exist = False
    is_short_order_exist = False
    if orders != None:
        for order_dict in orders: 
            is_new_order = order_dict['order_status'] in ['Untriggered', 'New'] and order_dict['order_type'] in ['Limit', 'Market'] and order_dict['take_profit'] > 0
            if is_new_order and order_dict['side'] == 'Buy':
                is_long_order_exist = True
            if is_new_order and order_dict['side'] == 'Sell':
                is_short_order_exist = True 
    if orders_active != None:
        for order_dict in orders_active: 
            is_new_order = order_dict['order_status'] in ['Untriggered', 'New'] and order_dict['order_type'] in ['Limit', 'Market'] and order_dict['take_profit'] > 0
            if is_new_order and order_dict['side'] == 'Buy':
                is_long_order_exist = True
            if is_new_order and order_dict['side'] == 'Sell':
                is_short_order_exist = True 
    return is_long_order_exist, is_short_order_exist 

def get_current_price(logger, symbol, str_format):
    """
    Gets the current price. You can choose format: str_format = True >> String, otherwise float
    """
    logger.debug(f'Entered into get_current_price with the following parameters: symbol: {symbol}')
    try:
        client_unauth = usdt_perpetual.HTTP(endpoint="https://api.bybit.com")
        symbol_price_info = client_unauth.latest_information_for_symbol(symbol=symbol)
        bybit_current_price_str = symbol_price_info['result'][0]['last_price']
        bybit_current_price = float(bybit_current_price_str)
        if str_format:
            return bybit_current_price_str
        return bybit_current_price
    except Exception as e:
        error_msg = f"Couldn't get current price {e}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
def get_pnl(logger, symbol, start_time): 
    """
    Calculates the sum of the PnL from the start time
    """
    try: 
        client = get_client()
        logger.debug(f'Entered into get_pnl with the following parameters: ')
        closed_profit_data = client.closed_profit_and_loss(symbol=symbol, category="linear")['result']['data']
        filtered_data = [d['closed_pnl'] for d in closed_profit_data if d['created_at'] >= start_time]
        return sum(filtered_data)
    except Exception as e:
        error_msg = f"Error during getting pnl: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
def change_exit_orders(logger, symbol, is_long, take_profit, stop_loss):
    """
    Changes the exit orders for a buy or sell position
    """
    logger.debug(f'Entered into change_exit_orders with the following parameters: start_time: symbol: {symbol}, is_long: {is_long}, take_profit: {take_profit}, stop_loss: {stop_loss}')
    client = get_client()
    position_idx = 1 if is_long else 2
    symbol_info = get_symbol_info(logger, symbol)
    take_profit_prec = get_formatted_price(logger, take_profit, symbol_info)
    stop_loss_prec = get_formatted_price(logger, stop_loss, symbol_info)
    client.set_trading_stop(symbol=symbol, category="linear", position_idx=position_idx, take_profit=take_profit_prec, stop_loss=stop_loss_prec)
