DECLARE @StartDate DATETIME = '2024-01-01';
DECLARE @EndDate DATETIME = '2025-12-31';
DECLARE @CurrentDate DATETIME = @StartDate;

WHILE @CurrentDate <= @EndDate
BEGIN
    INSERT INTO [dbo].[DimTime] (
        FullDate, 
        YearNum, 
        MonthNum, 
        DayNum, 
        DayOfWeekNum,
        HourNum,
        MinuteNum
    )
    VALUES (
        @CurrentDate,
        YEAR(@CurrentDate),
        MONTH(@CurrentDate),
        DAY(@CurrentDate),
        DATEPART(WEEKDAY, @CurrentDate),
        DATEPART(HOUR, @CurrentDate),
        DATEPART(MINUTE, @CurrentDate)
    )

    SET @CurrentDate = DATEADD(MINUTE, 1, @CurrentDate)
END

