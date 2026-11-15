CREATE TABLE IF NOT EXISTS meter_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meter_id INTEGER NOT NULL,
    bill_id INTEGER NOT NULL,
    date_start TEXT NOT NULL,
    date_end TEXT NOT NULL,
    value_start INTEGER NOT NULL,
    value_end INTEGER NOT NULL,
    FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE RESTRICT,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE RESTRICT,
    CHECK (date_end >= date_start)
);

CREATE INDEX IF NOT EXISTS idx_readings_meter_id ON meter_readings(meter_id);
CREATE INDEX IF NOT EXISTS idx_readings_bill_id ON meter_readings(bill_id);