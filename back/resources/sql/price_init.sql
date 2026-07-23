CREATE TABLE IF NOT EXISTS price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    price REAL,
    reason_news_id INTEGER,
    FOREIGN KEY (item_id) REFERENCES item (id),
    FOREIGN KEY (reason_news_id) REFERENCES news (id)
);
