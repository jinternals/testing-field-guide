-- new column; existing rows get NULL
ALTER TABLE orders ADD COLUMN status text;
