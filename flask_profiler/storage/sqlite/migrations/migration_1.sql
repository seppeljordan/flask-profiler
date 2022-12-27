BEGIN TRANSACTION;
CREATE TABLE "measurements" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "startedAt" REAL,
    "endedAt" REAL,
    "elapsed" REAL,
    "method" TEXT,
    "context" TEXT,
    "name" TEXT
);
CREATE INDEX "measurement_index" ON "measurements" (
    "startedAt", "name", "method"
);
CREATE TABLE "keyword_arguments" (
    "measurement" INTEGER,
    "key" TEXT,
    "value" TEXT,
    PRIMARY KEY("measurement", "key"),
    FOREIGN KEY("measurement") REFERENCES "measurements"("ID") ON DELETE CASCADE
);
CREATE INDEX "keyword_argument_index" ON "keyword_arguments" (
    "measurement", "key", "value"
);
PRAGMA user_version = 1;
COMMIT TRANSACTION;
