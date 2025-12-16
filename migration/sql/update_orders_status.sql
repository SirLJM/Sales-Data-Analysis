UPDATE orders
SET status = 'active'
WHERE status = 'draft';

-- Create index on status column for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

-- Create index on created_at for sorting active orders
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);

-- Add comment to status column
COMMENT ON COLUMN orders.status IS 'Order status: active, archived, cancelled';
