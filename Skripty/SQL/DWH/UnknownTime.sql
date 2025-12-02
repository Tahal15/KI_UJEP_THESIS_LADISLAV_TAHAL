-- DimTime - vložení UNKNOWN øádku s TimeKey = -1
IF NOT EXISTS (SELECT 1 FROM dbo.DimTime WHERE TimeKey = -1)
BEGIN
    SET IDENTITY_INSERT dbo.DimTime ON;

    INSERT INTO dbo.DimTime (
        TimeKey, FullDate, YearNum, MonthNum,
        DayNum, DayOfWeekNum, HourNum, MinuteNum
    )
    VALUES (
        -1, '1900-01-01 00:00:00.000', 1900, 1,
        1, 1, 0, 0
    );

    SET IDENTITY_INSERT dbo.DimTime OFF;
END;
