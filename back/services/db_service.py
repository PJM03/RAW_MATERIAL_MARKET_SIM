import sqlite3 as sql
import os, json
from schemas.item_schema import Item, ItemPriceHistory
    
sql_init_dir = "./resources/sql/"
sql_init_files = [
    "item_init.sql",
    "news_init.sql",
    "price_init.sql",
    "item_price_trigger.sql"
]
    
class DBService:
    def __init__(self: DBService):
        self.conn = sql.connect("system.db", check_same_thread=False, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.cursor.execute("PRAGMA journal_mode = WAL;")
        self.cursor.execute("PRAGMA busy_timeout = 5000;")
        
        for filename in sql_init_files:
            with open(os.path.join(sql_init_dir, filename), "r") as f:
                self.cursor.execute(f.read())
                self.conn.commit()
            
    def get_items(self: DBService):
        self.cursor.execute("SELECT * FROM item")
        result = self.cursor.fetchall()
        return [Item(id=x[0], name=x[1], description=x[2], price=x[3]) for x in result]
    
    def get_item(self: DBService, item_id: int):
        self.cursor.execute("SELECT * FROM item WHERE id = ? LIMIT 1", (item_id, ))
        result = self.cursor.fetchone()
        return Item(id=result[0], name=result[1], description=result[2], price=result[3])
    
    def get_price_history(self: DBService, item_id: int):
        self.cursor.execute("SELECT item_id, price, reason_news_id FROM price WHERE item_id = ?", (item_id, ))
        result = self.cursor.fetchall()
        return [ItemPriceHistory(id=x[0], price=x[1], news_id=x[2]) for x in result]
    
    def get_news(self: DBService, news_id: int):
        self.cursor.execute("SELECT news, trend, issued_at FROM news WHERE id = ? LIMIT 1", (news_id, ))
        result = self.cursor.fetchone()
        return {"id": news_id, "trend": result[1], "news": result[0], "issued_at": result[2]}
    
    def get_latest_news(self: DBService):
        self.cursor.execute("SELECT * FROM news ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        return {"id": result[0], "news": result[1], "trend": result[2], "related_items": result[3]}
        
    def new_news(self: DBService, news: dict):
        res_data = news['response_data']
        self.cursor.execute("""
                            INSERT INTO news(
                                news, trend, related_items
                            ) VALUES (
                                ?, ?, ?
                            )
                    """, (res_data.news, res_data.trend,
                          json.dumps([{"item": x.item, "change_rate": x.change_rate} for x in res_data.items], ensure_ascii=False)
                          ))
        self.conn.commit()
        news_id = self.cursor.lastrowid
        
        for item in res_data.items:
            self.cursor.execute("""
                        INSERT INTO price(item_id, price, reason_news_id)
                        SELECT 
                            id,
                            price * (1 + ?),
                            ?
                        FROM item
                        WHERE name = ?
                        """, (item.change_rate, news_id, item.item))
            self.conn.commit()