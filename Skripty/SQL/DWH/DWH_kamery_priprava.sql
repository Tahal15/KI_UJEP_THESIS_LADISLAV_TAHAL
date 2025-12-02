USE [DWH];
GO

------------------------------------------------------------------------------
-- 1. Vytvoøení schémat (pro poøádek)
------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Stg')
    EXEC('CREATE SCHEMA [Stg]');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
    EXEC('CREATE SCHEMA [dbo]');
GO

------------------------------------------------------------------------------
-- 2. STAGING tabulka pro kamery
------------------------------------------------------------------------------
IF OBJECT_ID('[Stg].[CameraCamea]', 'U') IS NOT NULL
    DROP TABLE [Stg].[CameraCamea];
GO

CREATE TABLE [Stg].[CameraCamea]
(
    StgID            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    LandingID        INT       NULL,   -- odkaz na ID z landing
    LoadDttm         DATETIME2(3) DEFAULT SYSUTCDATETIME(),
    OriginalTime     DATETIME2(3) NULL,   -- z landing sloupce [time]
    City             VARCHAR(50) NULL,    -- vyparsované mìsto z topic (napø. Bilina, Decin)
    DetectionType    VARCHAR(50) NULL,
    Utc              DATETIME2(3) NULL,   -- z JSON klíèe "utc"
    LP               VARCHAR(50)  NULL,   -- SPZ
    Sensor           VARCHAR(50)  NULL,   -- napø. "BI-TP-O2"
    VehClass         INT          NULL,
    ILPC             VARCHAR(5)   NULL,   -- zemì SPZ
    Velocity         INT          NULL
);
GO

------------------------------------------------------------------------------
-- 3. Dimenze: DimTime
--   
IF OBJECT_ID('[dbo].[DimTime]', 'U') IS NOT NULL
    DROP TABLE [dbo].[DimTime];
GO
CREATE TABLE [dbo].[DimTime]
(
    TimeKey       INT IDENTITY(1,1) NOT NULL,
    FullDate      DATETIME   NOT NULL,  -- Zmìnìno z DATE na DATETIME
    YearNum       INT        NOT NULL,
    MonthNum      TINYINT    NOT NULL,
    DayNum        TINYINT    NOT NULL,
    DayOfWeekNum  TINYINT    NOT NULL,
    HourNum       TINYINT    NOT NULL,  -- Pøidán sloupec pro hodiny
    MinuteNum     TINYINT    NOT NULL,  -- Pøidán sloupec pro minuty
    CONSTRAINT PK_DimTime PRIMARY KEY (TimeKey)
);
GO

------------------------------------------------------------------------------
-- 4. Dimenze: DimCity
------------------------------------------------------------------------------
IF OBJECT_ID('[dbo].[DimCity]', 'U') IS NOT NULL
    DROP TABLE [dbo].[DimCity];
GO

CREATE TABLE [dbo].[DimCity]
(
    CityKey  INT IDENTITY(1,1) NOT NULL,
    CityName VARCHAR(100) NOT NULL,
    IsActive BIT          DEFAULT 1,
    CONSTRAINT PK_DimCity PRIMARY KEY (CityKey)
);
GO

------------------------------------------------------------------------------
-- 5. Dimenze: DimCamera
------------------------------------------------------------------------------
IF OBJECT_ID('[dbo].[DimCamera]', 'U') IS NOT NULL
    DROP TABLE [dbo].[DimCamera];
GO

CREATE TABLE [dbo].[DimCamera]
(
    CameraKey  INT IDENTITY(1,1) NOT NULL,
    CameraCode VARCHAR(50) NOT NULL,  -- napø. "BI-TP-O2"
    CityKey    INT         NULL,      -- cizí klíè do DimCity (pokud kamera patøí do 1 mìsta)
    CameraName VARCHAR(200) NULL,
    IsActive   BIT          DEFAULT 1,
    CONSTRAINT PK_DimCamera PRIMARY KEY (CameraKey),
    CONSTRAINT FK_DimCamera_DimCity
        FOREIGN KEY (CityKey) REFERENCES [dbo].[DimCity](CityKey)
);
GO

------------------------------------------------------------------------------
-- 6. Faktová tabulka: FactCameraDetection
--    Obsahuje cizí klíè na DimTime, DimCamera (a volitelnì i DimCity)
--    
------------------------------------------------------------------------------
IF OBJECT_ID('[dbo].[FactCameraDetection]', 'U') IS NOT NULL
    DROP TABLE [dbo].[FactCameraDetection];
GO

CREATE TABLE [dbo].[FactCameraDetection]
(
    CameraDetectionKey INT IDENTITY(1,1) NOT NULL,
    TimeKey            INT              NOT NULL,  -- FK do DimTime
    CameraKey          INT              NOT NULL,  -- FK do DimCamera
    DetectionType      VARCHAR(50)      NULL,
    LP                 VARCHAR(50)      NULL,       -- SPZ
    ILPC               VARCHAR(5)       NULL,       -- zemì
    VehClass           INT              NULL,
    Velocity           INT              NULL,
    CONSTRAINT PK_FactCameraDetection PRIMARY KEY (CameraDetectionKey),
    CONSTRAINT FK_FactCameraDetection_DimTime
        FOREIGN KEY (TimeKey) REFERENCES [dbo].[DimTime](TimeKey),
    CONSTRAINT FK_FactCameraDetection_DimCamera
        FOREIGN KEY (CameraKey) REFERENCES [dbo].[DimCamera](CameraKey)
);
GO
