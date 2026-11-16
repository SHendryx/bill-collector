CREATE TABLE IF NOT EXISTS meter_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meter_id INTEGER NOT NULL,
    bill_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_value DECIMAL NOT NULL,
    end_value DECIMAL NOT NULL,
    FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE RESTRICT,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE RESTRICT,
    CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_readings_meter_id ON meter_readings(meter_id);
CREATE INDEX IF NOT EXISTS idx_readings_bill_id ON meter_readings(bill_id);