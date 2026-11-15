CREATE TABLE IF NOT EXISTS meters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL UNIQUE,
    account_id INTEGER NOT NULL,
    unit_of_measure UNIT_OF_MEASURE NOT NULL
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_meters_account_id ON meters(account_id);