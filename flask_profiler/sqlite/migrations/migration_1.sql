BEGIN TRANSACTION;
CREATE TABLE "measurements" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "route_name" TEXT,
    "start_timestamp" REAL,
    "end_timestamp" REAL,
    "method" TEXT
);
CREATE INDEX "measurement_index" ON "measurements" (
    "start_timestamp", "name", "method"
);
PRAGMA user_version = 1;
COMMIT TRANSACTION;
