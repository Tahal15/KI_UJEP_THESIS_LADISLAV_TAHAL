IF OBJECT_ID('[dbo].[DimCity]', 'U') IS NOT NULL
    DROP TABLE [dbo].[DimCity];
GO

CREATE TABLE [dbo].[DimCity]
(
    CityKey  INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    CityName VARCHAR(100) NOT NULL,
    IsActive BIT          DEFAULT 1
);
GO
