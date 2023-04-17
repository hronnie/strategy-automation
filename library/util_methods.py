import requests
import os
import decimal
import logging


def get_formatted_price(logger, raw_price, symbol_info): 
    """
    Gets the formatted price which is acceptable for Bybit
    """
    logger.debug(f'Entered into get_formatted_price with the following parameters: raw_price: {raw_price}, symbol_info: {symbol_info}')
    price_precision = symbol_info['price_scale']
    tick_size = float(symbol_info['price_filter']['tick_size'])
    rounded_price = round(raw_price / tick_size) * tick_size
    return "{:.{}f}".format(rounded_price, price_precision)

def get_formatted_quantity(logger, current_price, leverage, symbol_info, dollar_amount): 
    """
    Gets the formatted quantity which is acceptable for Bybit
    """
    logger.debug(f'Entered into get_formatted_price with the following parameters: current_price: {current_price}, leverage: {leverage}, dollar_amount: {dollar_amount}, symbol_info: {symbol_info}')
    quantity_precision = symbol_info['lot_size_filter']['qty_step']
    decimal_precision = decimal.Decimal(str(quantity_precision))
    quantity_precision = abs(decimal_precision.as_tuple().exponent)
    raw_quantity = float(dollar_amount) * leverage / float(current_price)
    return "{:0.0{}f}".format(raw_quantity, quantity_precision)


def send_telegram_message(message):
    """
    Sends a telegram message.
    """
    TOKEN = os.environ.get('TELEGRAM_API_KEY')
    CHAT_ID = -1001472971338
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url)
    except Exception as e:
        error_msg = f"Couldn't communicate with telegram {e}"
        raise Exception(error_msg)    
    
def add_sub_percentage(price, percentage, is_add): 
    """
    You can add or substract a percentage from a price number.
    is_add = True: Add
    is_add = False: Substract
    """
    if is_add:
        multiplier = 0.01 * (100 + percentage)
    else: 
        multiplier = 0.01 * (100 - percentage)
    return price * multiplier

def get_bog_logger(symbol):
    log_file_name = f'hedge_bot__{symbol}'
    logging.basicConfig(
        level=logging.DEBUG,  
        format='%(asctime)s [%(levelname)s] %(message)s', 
        handlers=[
            logging.FileHandler(f'{log_file_name}.log'),  
            logging.StreamHandler() 
        ]
    )
    return logging.getLogger(log_file_name)