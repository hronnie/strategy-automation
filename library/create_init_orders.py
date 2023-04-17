from db_connect import create_table, insert_data, get_data
from cycle_handler_new import populate_inputs, log_init_values, execute_init_orders
from util_methods import get_bog_logger


symbol = input("Symbol: ").upper() + "USDT"
logger = get_bog_logger(symbol)
strategy_inputs = populate_inputs(logger, symbol)
log_init_values(logger, strategy_inputs)
execute_init_orders(logger, strategy_inputs)

create_table()
insert_data(strategy_inputs)
print(get_data(symbol))

