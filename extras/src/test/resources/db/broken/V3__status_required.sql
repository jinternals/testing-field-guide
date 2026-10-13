-- the version someone wrote first: no backfill
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;
