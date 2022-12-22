CREATE TABLE "measurements" (
    "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "startedAt" REAL,
    "endedAt" REAL,
    "elapsed" REAL,
    "args" TEXT,
    "kwargs" TEXT,
    "method" TEXT,
    "context" TEXT,
    "name" TEXT
);
CREATE INDEX "measurement_index" ON "measurements" (
    "startedAt", "endedAt", "elapsed", "name", "method"
);
