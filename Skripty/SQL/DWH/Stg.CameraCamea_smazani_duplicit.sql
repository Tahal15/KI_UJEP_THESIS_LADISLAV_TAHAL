WITH CTE AS (
    SELECT 
        [StgID],
        [LandingID],
        [LoadDttm],
        [OriginalTime],
        [City],
        [DetectionType],
        [Utc],
        [LP],
        [Sensor],
        [VehClass],
        [ILPC],
        [Velocity],
        ROW_NUMBER() OVER(
            PARTITION BY 
                [LandingID], -- Klíèový sloupec pro identifikaci duplicit
                [OriginalTime], 
                [City], 
                [DetectionType], 
                [Utc], 
                [LP], 
                [Sensor], 
                [VehClass], 
                [ILPC], 
                [Velocity]
            ORDER BY [StgID]
        ) AS RowNum
    FROM [DWH].[Stg].[CameraCamea]
)
DELETE FROM CTE WHERE RowNum > 1;