-- Získání kompletní struktury tabulek vèetnì constraintù, indexù a výchozích hodnot

SELECT 
    c.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    ISNULL(c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION) AS ColumnLength,
    c.NUMERIC_SCALE,
    c.IS_NULLABLE,
    tc.CONSTRAINT_TYPE,
    kcu.CONSTRAINT_NAME,
    dc.definition AS DefaultValue,
    fk.referenced_table AS ForeignKey_ReferencedTable,
    fk.referenced_column AS ForeignKey_ReferencedColumn,
    i.IndexName,
    i.IndexType,
    i.IsUnique
FROM INFORMATION_SCHEMA.COLUMNS c

-- Join constraints
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON c.TABLE_NAME = kcu.TABLE_NAME AND c.COLUMN_NAME = kcu.COLUMN_NAME
LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME AND kcu.TABLE_NAME = tc.TABLE_NAME

-- Default constraints
LEFT JOIN (
    SELECT 
        t.name AS table_name,
        c.name AS column_name,
        dc.definition
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
    INNER JOIN sys.tables t ON t.object_id = c.object_id
) dc ON dc.table_name = c.TABLE_NAME AND dc.column_name = c.COLUMN_NAME

-- Foreign keys
LEFT JOIN (
    SELECT 
        OBJECT_NAME(f.parent_object_id) AS table_name,
        COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name,
        OBJECT_NAME(f.referenced_object_id) AS referenced_table,
        COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
    FROM sys.foreign_keys AS f
    INNER JOIN sys.foreign_key_columns AS fc 
        ON f.OBJECT_ID = fc.constraint_object_id
) fk ON fk.table_name = c.TABLE_NAME AND fk.column_name = c.COLUMN_NAME

-- Indexes
LEFT JOIN (
    SELECT 
        t.name AS TableName,
        ind.name AS IndexName,
        ind.type_desc AS IndexType,
        col.name AS ColumnName,
        ind.is_unique AS IsUnique
    FROM sys.indexes ind 
    INNER JOIN sys.index_columns ic 
        ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id 
    INNER JOIN sys.columns col 
        ON ic.object_id = col.object_id AND ic.column_id = col.column_id 
    INNER JOIN sys.tables t 
        ON ind.object_id = t.object_id
    WHERE ind.is_primary_key = 0 AND ind.is_unique_constraint = 0
) i ON i.TableName = c.TABLE_NAME AND i.ColumnName = c.COLUMN_NAME

-- Filtrované tabulky
WHERE c.TABLE_NAME IN (
    'DimCity', 'DimSensor', 'DimLP', 'DimDetectionType',
    'DimVehicleClass', 'DimCountry', 'DimTime', 'FactCameraDetection'
)
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
