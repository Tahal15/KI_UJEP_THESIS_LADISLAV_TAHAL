CREATE TABLE [dbo].[ETL_RunLog] (
    [RunID] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [JobName] NVARCHAR(100) NOT NULL,       -- název úlohy, napø. "LoadCameraData" nebo "LoadVodomery"
    [Topic] NVARCHAR(200) NULL,            -- pokud se loguje i konkrétní topic, mùže být NULL
    [StartTime] DATETIME2 NOT NULL,
    [EndTime] DATETIME2 NULL,
    [Status] NVARCHAR(20) NOT NULL,        -- 'RUNNING', 'SUCCESS', 'ERROR', ...
    [RowsInserted] BIGINT NULL,
    [RowsUpdated] BIGINT NULL,             -- pokud dìláš i update
    [ErrorMessage] NVARCHAR(MAX) NULL      -- detail chyby
);


