from pydantic import BaseModel

class Item(BaseModel):
    id: int
    name: str
    description: str
    price: float
    
class ItemPriceHistory(BaseModel):
    id: int
    price: float
    news_id: int