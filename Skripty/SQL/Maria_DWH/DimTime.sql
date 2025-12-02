CREATE TABLE DimTime (
    TimeKey INT PRIMARY KEY,
    FullDate DATETIME NOT NULL,
    YearNum INT NOT NULL,
    MonthNum TINYINT NOT NULL,
    DayNum TINYINT NOT NULL,
    DayOfWeekNum TINYINT NOT NULL,
    HourNum TINYINT NOT NULL,
    MinuteNum TINYINT NOT NULL,
    INDEX IX_DimTime_FullDate (FullDate),
    INDEX IX_DimTime_FullDate_Hour_Minute (FullDate, HourNum, MinuteNum)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
