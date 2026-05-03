-- PostgreSQL initialization script
-- Create the operations table for logging

CREATE TABLE IF NOT EXISTS operations (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    message VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL
);

-- Create an index on date for faster queries
CREATE INDEX IF NOT EXISTS idx_operations_date ON operations(date DESC);

-- Create an index on operation_type for filtering
CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(operation_type);
