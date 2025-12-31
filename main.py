from fastapi import FastAPI, HTTPException, Query
import uvicorn
import json
from datetime import datetime
from menu import Order, OrderResponse
from enum import Enum
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import db  # 引入 db.py

# 1. 手動定義系列選單 (Enum)
class CategorySelect(str, Enum):
    all = "全部"
    t1="台灣茗茶系列"
    t2="伯爵紅茶系列"
    t3="台灣靛紅系列"
    t4="台灣綠茶系列"
    t5="台灣青茶系列"
    t6="台灣烏龍系列"
    t7="陳年普洱系列"
    t8="經典風味系列"
    t9="新鮮現榨系列"
    t10="冰菓系列"
    t11="調和風味系列"
    t12="咖啡系列"
    t13="頂級生乳拿鐵系列"

class OptionType(str, Enum):
    all = "全部"
    ice = "冰量"
    sugar = "糖量"
    topping = "加料區"
# 2. 現代化生命週期管理 (取代舊的 on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：初始化資料庫
    db.init_db()
    yield
    # 關閉時：可在此處清理資源

app = FastAPI(title="飲料訂單-API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", summary="檢查連線")
def read_root():
    return {"message": "資料庫已連線，請前往 /docs"}

# 3. 取得菜單 (支援下拉選單過濾)
@app.get("/menu", summary="取得菜單品項", description="可從下拉選單選擇特定系列，或查看全部")
def get_all_menu(
    category: CategorySelect = Query(CategorySelect.all, description="飲品系列")
):
    conn = db.get_db_conn()
    
    if category == CategorySelect.all:
        rows = conn.execute("SELECT * FROM menu").fetchall()
    else:
        rows = conn.execute("SELECT * FROM menu WHERE category = ?", (category.value,)).fetchall()
    
    conn.close()
    
    result = {}
    for row in rows:
        cat = row["category"]
        if cat not in result: result[cat] = {}
        result[cat][row["drink_name"]] = {"M": row["price_m"], "L": row["price_l"]}
    return result

@app.get("/options", summary="取得點餐選項", description="可選擇特定類別（如：加料區）或查看所有選項")
def get_options(
    option_type: OptionType = Query(OptionType.all, description="請選擇要查詢的選項類別")
):
    conn = db.get_db_conn()
    
    # 根據選單決定 SQL 語法
    if option_type == OptionType.all:
        rows = conn.execute("SELECT * FROM options").fetchall()
    else:
        rows = conn.execute("SELECT * FROM options WHERE type = ?", (option_type.value,)).fetchall()
        
    conn.close()
    
    # 建立回傳格式
    # 如果選特定的類別，只會回傳那個類別的 List；如果選全部，就回傳原本的字典
    if option_type == OptionType.all:
        res = {"冰量": [], "糖量": [], "加料區": []}
        for row in rows:
            res[row["type"]].append(row["name"])
        return res
    else:
        # 只回傳該類別的陣列，例如 ["珍珠", "波霸"...]
        return {option_type.value: [row["name"] for row in rows]}
@app.post("/order", response_model=OrderResponse, summary="提交訂單", description="計算總額並存入資料庫歷史紀錄")
def create_order(user_order: Order):
    conn = db.get_db_conn()
    drink = conn.execute("SELECT * FROM menu WHERE drink_name = ?", (user_order.drink_name,)).fetchone()
    
    if not drink:
        conn.close()
        raise HTTPException(status_code=404, detail="找不到該飲料")
    
    found_price = drink["price_m"] if user_order.size == "M" else drink["price_l"]
    total = found_price + (len(user_order.add) * 10)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.cursor()
    cursor.execute('''INSERT INTO orders (drink_name, size, sugar, ice, toppings, total_price, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (user_order.drink_name, user_order.size, user_order.sugar, 
                    user_order.ice, json.dumps(user_order.add), total, current_time))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return OrderResponse(
        id=new_id,
        drink_name=user_order.drink_name,
        size=user_order.size,
        sugar=user_order.sugar,
        ice=user_order.ice,
        add=user_order.add,
        total_price=total,
        created_at=current_time
    )

@app.get("/orders", summary="取得歷史訂單", description="查看所有歷史點餐紀錄")
def get_all_orders():
    conn = db.get_db_conn()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    
    orders = []
    for row in rows:
        orders.append({
            "id": row["id"],
            "drink_name": row["drink_name"],
            "size": row["size"],
            "sugar": row["sugar"],
            "ice": row["ice"],
            "add": json.loads(row["toppings"]),
            "total_price": row["total_price"],
            "created_at": row["created_at"]
        })
    return orders

@app.post("/menu/item", summary="新增飲料", description="手動往資料庫增加新的飲料品項")
def add_menu_item(
    category: str = Query(..., description="系列名稱"), 
    drink_name: str = Query(..., description="飲品名稱"), 
    price_m: int = Query(..., description="中杯價格"), 
    price_l: int = Query(..., description="大杯價格")
):
    conn = db.get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO menu (category, drink_name, price_m, price_l) VALUES (?, ?, ?, ?)",
            (category, drink_name, price_m, price_l)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"新增失敗: {str(e)}")
    conn.close()
    return {"message": f"成功新增：{drink_name}"}

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)
