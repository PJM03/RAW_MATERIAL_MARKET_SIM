CREATE TRIGGER IF NOT EXISTS sync_item_price_after_insert
AFTER INSERT ON price
BEGIN
    UPDATE item
    SET price = NEW.price
    WHERE id = NEW.item_id;
END;