#此檔定義菜單與訂單格式

from pydantic import BaseModel
#BaseModel是一個基礎模板。所有資料格式都繼承它，這樣FastAPI才會自動幫你檢查資料
from typing import List, Optional
#Optional:告訴電腦這個欄位是選填的

class Order(BaseModel): #客人的點餐單
    drink_name: str
    size: str
    sugar: str
    ice: str
    add: List[str]=[]

class OrderResponse(Order): #回傳收據
    id: int
    total_price: int