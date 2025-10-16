CREATE TABLE [dbo].[ETL_IncrementalControl] (
    [ControlID] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [Topic] NVARCHAR(200) NOT NULL,
    [LastLoadedID] BIGINT NULL,         -- Poslední zpracované ID v Landing
    [FullLoadDone] BIT NOT NULL,        -- Oznaèí, zda je již hotový poèáteèní (full) load
    [LastUpdate] DATETIME2 NOT NULL,    -- Kdy se naposledy tahle øádka zmìnila
    CONSTRAINT UQ_Topic UNIQUE (Topic)  -- Každý topic jedineènì
);