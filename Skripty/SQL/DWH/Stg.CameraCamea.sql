USE [DWH];
GO

-- 2.1: Schéma pro staging
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Stg')
    EXEC('CREATE SCHEMA [Stg]');
GO

-- 2.2: Staging tabulka pro kamery /Bilina/kamery/camea/...
IF OBJECT_ID('[Stg].[CameraCamea]', 'U') IS NOT NULL
    DROP TABLE [Stg].[CameraCamea];
GO

CREATE TABLE [Stg].[CameraCamea]
(
    StgID                INT IDENTITY(1,1) NOT NULL PRIMARY KEY,  -- lokální PK ve stagingu
    LandingID            INT,          -- odkaz na ID z landing (pokud chceš)
    LoadDttm             DATETIME2(3)  DEFAULT SYSUTCDATETIME(),  -- kdy jsme nahráli do stagingu
    OriginalTime         DATETIME2(3), -- z landing sloupce [time]
	City				 VARCHAR(50), -- Bude parsováno z topicu
    detectionType        VARCHAR(50),
    utc                  DATETIME2(3), -- budeme konvertovat z JSON, pokud je to validní formát
    lp                   VARCHAR(50),  -- SPZ
    sensor               VARCHAR(50),
    vehClass             INT,
    ilpc                 VARCHAR(5),
    velocity             INT
    -- klidnì další sloupce, pokud se v JSON vyskytují a potøebuješ je
);
GO
