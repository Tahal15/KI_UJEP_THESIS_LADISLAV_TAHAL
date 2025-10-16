INSERT INTO DimTime
SELECT
    number + 1104071 AS TimeKey,                            -- začátek číslování
    toDateTime('2024-01-01 00:00:00') + number * 60 AS FullDate, -- každá minuta
    toYear(toDateTime('2024-01-01 00:00:00') + number * 60) AS YearNum,
    toMonth(toDateTime('2024-01-01 00:00:00') + number * 60) AS MonthNum,
    toDayOfMonth(toDateTime('2024-01-01 00:00:00') + number * 60) AS DayNum,
    toDayOfWeek(toDateTime('2024-01-01 00:00:00') + number * 60) AS DayOfWeekNum, -- 1=Mon ... 7=Sun
    toHour(toDateTime('2024-01-01 00:00:00') + number * 60) AS HourNum,
    toMinute(toDateTime('2024-01-01 00:00:00') + number * 60) AS MinuteNum
FROM numbers(
    dateDiff('minute', toDateTime('2024-01-01 00:00:00'), toDateTime('2025-12-31 23:59:00')) + 1
);


INSERT INTO DimTime
SELECT
    toUnixTimestamp(ts) AS TimeKey,
    ts AS FullDate,
    toYear(ts) AS YearNum,
    toMonth(ts) AS MonthNum,
    toDayOfMonth(ts) AS DayNum,
    toDayOfWeek(ts) AS DayOfWeekNum,
    toHour(ts) AS HourNum,
    toMinute(ts) AS MinuteNum
FROM (
    SELECT addMinutes(toDateTime('2024-01-01 00:00:00'), number) AS ts
    FROM system.numbers
    LIMIT 1051200 -- cca 2 roky po minutách
);

ALTER TABLE FactCameraDetection ADD COLUMN CameraDetectionKey UUID DEFAULT generateUUIDv4();

