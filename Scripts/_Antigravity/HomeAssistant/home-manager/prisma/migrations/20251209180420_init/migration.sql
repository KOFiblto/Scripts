-- CreateTable
CREATE TABLE "Floorplan" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "imagePath" TEXT NOT NULL,
    "width" REAL NOT NULL,
    "height" REAL NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Device" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "floorplanId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "protocol" TEXT NOT NULL,
    "pinCode" TEXT,
    "qrCodePath" TEXT,
    "xPos" REAL NOT NULL,
    "yPos" REAL NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Device_floorplanId_fkey" FOREIGN KEY ("floorplanId") REFERENCES "Floorplan" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
