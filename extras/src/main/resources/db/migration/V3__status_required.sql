-- backfill first, THEN make it required
UPDATE orders SET status = 'PLACED' WHERE status IS NULL;
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
