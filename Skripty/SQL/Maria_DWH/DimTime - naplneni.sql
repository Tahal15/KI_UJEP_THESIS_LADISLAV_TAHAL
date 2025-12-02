DELIMITER $$

DROP PROCEDURE IF EXISTS FillDimTime $$
CREATE PROCEDURE FillDimTime()
BEGIN
    DECLARE currentDate DATETIME DEFAULT '2024-01-01 00:00:00';
    DECLARE endDate DATETIME DEFAULT '2025-12-31 23:59:00';
    DECLARE timeKey INT DEFAULT 1104071; 

    WHILE currentDate <= endDate DO
        INSERT INTO DimTime (
            TimeKey,
            FullDate,
            YearNum,
            MonthNum,
            DayNum,
            DayOfWeekNum,
            HourNum,
            MinuteNum
        )
        VALUES (
            timeKey,
            currentDate,
            YEAR(currentDate),
            MONTH(currentDate),
            DAY(currentDate),
            DAYOFWEEK(currentDate),
            HOUR(currentDate),
            MINUTE(currentDate)
        );

        SET timeKey = timeKey + 1;
        SET currentDate = DATE_ADD(currentDate, INTERVAL 1 MINUTE);
    END WHILE;
END $$

DELIMITER ;

CALL FillDimTime();