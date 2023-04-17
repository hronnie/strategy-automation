import time
import datetime
import sys
from bybit_connect import buy_or_sell, get_current_price, change_exit_orders
from util_methods import send_telegram_message, get_bog_logger
from cycle_handlers import handle_error_and_exit, log_init_values, populate_long_inputs, populate_short_inputs, execute_init_orders, signal_missed_trade, check_positions_quantity_integrity, is_open_hedge_order_too_late, populate_is_main_long, get_status, exit_bot



symbol = input("Symbol: ").upper() + "USDT"
logger = get_bog_logger(symbol)






price_inputs = long_inputs if is_main_long else short_inputs
price_input_perc = long_inputs_perc if is_main_long else short_inputs_perc

log_init_values(logger, dollar_amount, leverage, symbol, max_iteration, is_main_long, price_inputs, price_input_perc)

execute_init_orders(logger, symbol, dollar_amount, leverage, price_inputs, is_main_long)

logger.info('Init order has been executed successfully!')


def handle_main_loop(is_first_position_created, is_no_hedge_yet, iteration):
    try:
        is_long_pos_exist, is_short_pos_exist, is_long_order_exist, is_short_order_exist = get_status(logger, symbol)
        logger.debug(f"Status:\nis_main_long: {is_main_long} \nLong Position exist: {is_long_pos_exist}\nLong Order exist: {is_long_order_exist}\nShort Position exist: {is_short_pos_exist}\nShort Order exist: {is_short_order_exist}")

        is_long_pos_and_short_order_exist = is_long_pos_exist and not is_long_order_exist and not is_short_pos_exist and is_short_order_exist
        is_short_pos_and_long_order_exist = is_short_pos_exist and not is_short_order_exist and not is_long_pos_exist and is_long_order_exist
        is_nothing_exist = not is_short_pos_exist and not is_short_order_exist and not is_long_pos_exist and not is_long_order_exist
        is_only_long_order_exist = not is_short_pos_exist and not is_short_order_exist and not is_long_pos_exist and is_long_order_exist
        is_only_short_order_exist = not is_short_pos_exist and is_short_order_exist and not is_long_pos_exist and not is_long_order_exist
        is_long_good_dir = is_long_pos_exist and not is_short_pos_exist and not is_long_order_exist and is_short_order_exist and is_main_long
        is_short_good_dir = not is_long_pos_exist and is_short_pos_exist and is_long_order_exist and not is_short_order_exist and not is_main_long
        
        if is_long_pos_exist and not is_long_order_exist and is_short_pos_exist and not is_short_order_exist: 
            is_no_hedge_yet = handle_hedging_in_process(symbol, is_no_hedge_yet, is_main_long, iteration, max_iteration)
        
        elif ((is_long_pos_and_short_order_exist and is_main_long) or (is_short_pos_and_long_order_exist and not is_main_long)) and not is_first_position_created: 
            is_first_position_created = True
            send_telegram_message('Symbol: ' + symbol + ", First position has been created")            

        elif (not is_long_order_exist and not is_short_order_exist) and ((is_long_pos_exist and not is_short_pos_exist and is_main_long) or (not is_long_pos_exist and is_short_pos_exist and not is_main_long)): 
            is_no_hedge_yet = True
            iteration = handle_hedge_recreation(symbol, is_main_long, max_iteration, price_inputs, iteration)      

        elif not is_long_pos_exist and not is_short_pos_exist and is_long_order_exist and is_short_order_exist: 
            handle_only_orders_exist(logger, start_time, symbol, is_main_long, price_inputs)  
        
        elif is_nothing_exist or (is_only_short_order_exist and is_main_long) or (is_only_long_order_exist and not is_main_long): 
            handle_strategy_won(logger, start_time, symbol, is_main_long)

        elif is_long_good_dir or is_short_good_dir: 
            pass

        else: 
            general_error_msg = f"Inconsistent status: is_long_pos_exist: {is_long_pos_exist}, is_short_pos_exist: {is_short_pos_exist}, is_long_order_exist: {is_long_order_exist}, is_short_order_exist: {is_short_order_exist}. Removes everyting and exit."
            handle_error_and_exit(logger, start_time, symbol, general_error_msg, is_long_side = is_main_long)    
        return is_first_position_created, is_no_hedge_yet, iteration      

    except Exception as e: 
        error_msg = f"Symbol: {symbol}. An error occured in the main loop:" + str(e)
        logger.error(error_msg)
        send_telegram_message(error_msg)
        error_cnt += 1
        if error_cnt < MAX_ERROR_CNT:
            return
        else: 
            handle_error_and_exit(logger, start_time, symbol, error_msg, is_main_long, 0, True)

is_first_position_created = False
is_no_hedge_yet = True
while True: 
    logger.debug("*********************** START OF CYCLE**********************")
    logger.debug('Starting cycle. Iteration: ' + str(iteration))
    time.sleep(CYCLE_DURATION)
    is_first_position_created, is_no_hedge_yet, iteration = handle_main_loop(is_first_position_created, is_no_hedge_yet, iteration)
    logger.debug("*********************** END OF CYCLE**********************")
