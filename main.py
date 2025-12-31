from fastapi import FastAPI,HTTPException
import uvicorn
from menu import Order,OrderResponse
from enum import Enum
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="飲料點餐系統")

# 掛載 static 資料夾
app.mount("/static", StaticFiles(directory="static"), name="static")
menu={
    "台灣茗茶系列":{
        "台灣靛紅":{"M":25,"L":30},
        "台灣純綠":{"M":25,"L":30},
        "台灣青茶":{"M":25,"L":30},
        "台灣烏龍":{"M":25,"L":30},
        "台灣烏龍綠":{"M":25,"L":30},
        "台灣烏龍青":{"M":25,"L":30},
        "超級青茶(瓶)":{"M":0,"L":40},
    },
    "伯爵紅茶系列":{
        "伯爵紅茶":{"M":25,"L":30},
        "梅子伯爵":{"M":35,"L":40},
        "伯爵奶茶":{"M":40,"L":45},
    }
}

order_options={
    "冰量":["正常冰","少冰","微冰","去冰","常溫","熱"],
    "糖量":["正常糖","半糖","少糖","微糖","無糖"],
    "加料區":["珍珠","波霸","QQ","椰果","寒天","藍莓凍","布丁"]
}

#下拉式選單
class CategoryName(str,Enum):
    tea_1 ="台灣茗茶系列"
    tea_2 ="伯爵紅茶系列"


#API端點區

@app.get("/")
def read_root():
    return {"message":"請在連結後方加入/docs查看API文件"}

#取得完整菜單
@app.get("/menu") 
def get_all_menu():
    return menu

#依系列取得菜單
@app.get("/menu/{category}")
def get_menu(category:CategoryName):
    return menu[category]

#取得點餐選項
@app.get("/options")
def get_options():
    return order_options

order_db=[]

#新增訂單
@app.post("/order",response_model=OrderResponse)
def create_order(user_order:Order):
    #搜尋菜單找價格
    found_price = None
    for category,drinks in menu.items():
        if user_order.drink_name in drinks:
            #取得大小杯的價格
            found_price = drinks[user_order.drink_name].get(user_order.size)
            break

    #找不到飲料或大小寫錯就報錯
    if found_price is None or found_price==0:
        raise HTTPException(status_code=404,detail="找不到該飲料或該尺寸不供應")
    
    #建立訂單結果
    total = found_price
    #如果加料清單有東西,每樣+10元
    total += len(user_order.add)*10

    new_id = len(order_db)+1
    receipt=OrderResponse(
        id=new_id,
        drink_name=user_order.drink_name,
        size=user_order.size,
        sugar=user_order.sugar,
        ice=user_order.ice,
        add=user_order.add,
        total_price=total
    )

    order_db.append(receipt)
    return receipt

#取得訂單
@app.get("/orders")
def get_all_orders():
    return order_db

if __name__ == "__main__":
    uvicorn.run(app,host='127.0.0.1',port=8000)