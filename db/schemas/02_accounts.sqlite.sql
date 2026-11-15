CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL UNIQUE,
    biller_id INTEGER NOT NULL,
    FOREIGN KEY (biller_id) REFERENCES billers(id)
);

CREATE INDEX IF NOT EXISTS idx_accounts_biller_id ON accounts(biller_id);