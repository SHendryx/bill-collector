CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    amount_due DECIMAL NOT NULL,
    due_date DATE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
    CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_bills_account_id ON bills(account_id);
CREATE INDEX IF NOT EXISTS idx_bills_due_date ON bills(due_date);