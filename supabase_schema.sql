-- Supabase Schema for Vatican Monitor
-- Run this in your Supabase SQL Editor

-- Table for target dates to monitor
CREATE TABLE IF NOT EXISTS target_dates (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for monitor status
CREATE TABLE IF NOT EXISTS monitor_status (
    id INTEGER PRIMARY KEY DEFAULT 1,
    check_count INTEGER DEFAULT 0,
    alerts_sent INTEGER DEFAULT 0,
    last_check TIMESTAMP WITH TIME ZONE,
    last_results JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial status row
INSERT INTO monitor_status (id, check_count, alerts_sent, last_results)
VALUES (1, 0, 0, '{}')
ON CONFLICT (id) DO NOTHING;

-- Table for alerted products (to avoid duplicate alerts)
CREATE TABLE IF NOT EXISTS alerted_products (
    id SERIAL PRIMARY KEY,
    product_key VARCHAR(100) NOT NULL UNIQUE,
    alerted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_target_dates_date ON target_dates(date);
CREATE INDEX IF NOT EXISTS idx_alerted_products_key ON alerted_products(product_key);

-- Enable Row Level Security (optional, for public access)
-- ALTER TABLE target_dates ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE monitor_status ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alerted_products ENABLE ROW LEVEL SECURITY;

-- If you want public read/write access (for serverless functions):
-- CREATE POLICY "Allow all" ON target_dates FOR ALL USING (true);
-- CREATE POLICY "Allow all" ON monitor_status FOR ALL USING (true);
-- CREATE POLICY "Allow all" ON alerted_products FOR ALL USING (true);
