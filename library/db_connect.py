import sqlite3

DB_NAME = 'trading_data.db'

def create_table():
    conn = sqlite3.connect('trading_data.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS trading_data (
                    symbol TEXT PRIMARY KEY,
                    dollar_amount REAL,
                    leverage INTEGER,
                    iteration INTEGER,
                    is_main_long BOOLEAN,
                    entry REAL,
                    profit_perc REAL,
                    profit_price REAL,
                    jump_in_perc REAL,
                    jump_in_price REAL,
                    give_up_perc REAL,
                    give_up_price REAL,
                    threshold_perc REAL,
                    threshold_price REAL,
                    hedge_destroy_price REAL,
                    max_iteration INTEGER
                 )''')

    conn.commit()
    conn.close()

def insert_data(strategy_inputs):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    print(strategy_inputs)
    print('Keys in strategy_inputs:', strategy_inputs.keys())
    print(strategy_inputs['iteration'])
    c.execute("INSERT INTO trading_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
        strategy_inputs['symbol'],
        strategy_inputs['dollar_amount'],
        strategy_inputs['leverage'],
        strategy_inputs['iteration'],
        strategy_inputs['is_main_long'],
        strategy_inputs['entry'],
        strategy_inputs['profit_perc'],
        strategy_inputs['profit_price'],
        strategy_inputs['jump_in_perc'],
        strategy_inputs['jump_in_price'],
        strategy_inputs['give_up_perc'],
        strategy_inputs['give_up_price'],
        strategy_inputs['threshold_perc'],
        strategy_inputs['threshold_price'],
        strategy_inputs['hedge_destroy_price'],
        strategy_inputs['max_iteration']
    ))    

    conn.commit()
    conn.close()

def get_data(symbol):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM trading_data WHERE symbol=?", (symbol,))
    row = c.fetchone()
    result = None
    if row is not None:
        strategy_inputs = {
            'symbol': row[0],
            'dollar_amount': row[1],
            'leverage': row[2],
            'iteration,': row[3],
            'is_main_long': bool(row[4]),
            'entry': row[5],
            'profit_perc': row[6],
            'profit_price': row[7],
            'jump_in_perc': row[8],
            'jump_in_price': row[9],
            'give_up_perc': row[10],
            'give_up_price': row[11],
            'threshold_perc': row[12],
            'threshold_price': row[13],
            'hedge_destroy_price': row[14],
            'max_iteration': row[15]
        }
        result = strategy_inputs

    conn.close()
    return result

def update_data(symbol, column, new_value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(f"UPDATE trading_data SET {column} = ? WHERE symbol = ?", (new_value, symbol))

    conn.commit()
    conn.close()

def clear_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM trading_data")

    conn.commit()
    conn.close()



def drop_table():
    conn = sqlite3.connect('trading_data.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS trading_data")

    conn.commit()
    conn.close()

# Example usage
# drop_table()


# data = {
#     'symbol': 'AAPL',
#     'dollar_amount': 1000,
#     'leverage': 2,
#     'is_main_long': True,
#     'entry': 150.5,
#     'profit_perc': 0.1,
#     'profit_price': 165.55,
#     'jump_in_perc': 0.02,
#     'jump_in_price': 153.51,
#     'give_up_perc': 0.03,
#     'give_up_price': 146.99,
#     'threshold_perc': 0.04,
#     'hedge_destroy_price': 144.48
# }

# Example usage
# create_table()
# insert_data('AAPL', 1000, 2, 7, True, 150.5, 0.1, 165.55, 0.02, 153.51, 0.03, 146.99, 0.04, 144.48, 3)
# print(get_data('AAPL'))
# update_data('AAPL', 'dollar_amount', 1200)
# print(get_data('AAPL'))

# Example usage
# clear_table()

