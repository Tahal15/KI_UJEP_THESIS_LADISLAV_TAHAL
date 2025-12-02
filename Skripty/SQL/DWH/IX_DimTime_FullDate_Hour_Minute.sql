CREATE NONCLUSTERED INDEX IX_DimTime_FullDate_Hour_Minute
ON dbo.DimTime (FullDate, HourNum, MinuteNum);
