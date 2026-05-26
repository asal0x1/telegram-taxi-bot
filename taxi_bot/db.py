import sqlite3

from config import *

def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            language TEXT,
            time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tariff_id INTEGER,
            name TEXT,
            phone TEXT,
            car_model TEXT,
            car_number TEXT
            )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            driver_id INTEGER,
            tariff_id INTEGER,
            from_lat FLOAT,
            from_lon FLOAT,
            to_location TEXT,
            distance_km FLOAT,
            total_price FLOAT, 
            status TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS tariffs (
            tariff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, 
            base_price FLOAT,
            price_per_km FLOAT
                )
        ''')

def create_tariff(name, base_price, price_per_km):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        INSERT OR IGNORE INTO tariffs
        (price_per_km, name, base_price)
        VALUES (?, ?, ?)
        ''', (price_per_km, name, base_price))

def add_user(user_id, name, phone, language):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO users (user_id, name, phone, language)
        VALUES (?, ?, ?, ?)
        ''', (user_id, name, phone, language))

def get_user(user_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cur.fetchone()

def create_order(user_id, from_lon, from_lat, to_location, tariff_id, distance_km, total_price, status = "pending"):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO orders
        (user_id, from_lon, from_lat, to_location, tariff_id, distance_km, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, from_lon, from_lat, to_location, tariff_id, distance_km, total_price, 'pending'))

def assign_driver(order_id, driver_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        UPDATE orders 
        SET driver_id = ?,
        status = ?
        WHERE order_id= ?
        ''', (driver_id, 'assigned', order_id))

def update_status(order_id, status):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        UPDATE orders SET status = ? 
        WHERE order_id = ?''', (status, order_id))

def add_driver(driver_id, tariff_id, name, phone, car_model, car_number ):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO drivers
        (driver_id, tariff_id, name, phone, car_model, car_number )
        VALUES (?, ?, ?, ?, ?, ?)''',
                    (driver_id, tariff_id, name, phone, car_model, car_number))

def get_user_orders(user_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM orders WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,))
        return cur.fetchall()

def get_pending_orders():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM orders 
        WHERE status = 'pending'
        ORDER BY created_at DESC
        ''')
        return cur.fetchall()

def get_drivers():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM drivers
        WHERE  = 1
        ''')
        return cur.fetchall()

def get_order(order_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM orders 
        WHERE order_id = ?
        ''', (order_id,))
        return cur.fetchone()

def get_driver(driver_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM drivers 
        WHERE driver_id = ?
        ''', (driver_id,))
        return cur.fetchone()

def update_language(user_id, language):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        UPDATE users 
        SET language = ?
        WHERE user_id = ?
        ''', (language, user_id))

def get_tariffs():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT * FROM tariffs 
        ''')
        return cur.fetchall()

def get_active_driver_by_tariff(tariff_id):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('''
        SELECT  FROM drivers 
        WHERE tariff_id = ?
        ''', (tariff_id,))
        return cur.fetchone()





