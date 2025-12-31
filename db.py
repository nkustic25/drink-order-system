import sqlite3

DB_FILE = "tea_shop.db"

def get_db_conn():
    """ 建立資料庫連線並回傳 """
    conn = sqlite3.connect(DB_FILE)
    # 讓查詢結果可以用欄位名稱存取 (例如 row["drink_name"])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ 初始化資料庫結構 (僅在資料表不存在時建立) """
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # 建立菜單表
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        category TEXT, 
        drink_name TEXT, 
        price_m INTEGER, 
        price_l INTEGER)''')
    
    # 建立選項表
    cursor.execute('''CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        type TEXT, 
        name TEXT)''')

    # 建立訂單表
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        drink_name TEXT, 
        size TEXT, 
        sugar TEXT, 
        ice TEXT, 
        toppings TEXT, 
        total_price INTEGER, 
        created_at TEXT)''')

    conn.commit()
    conn.close()