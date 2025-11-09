import pyodbc
import traceback
from multiprocessing import Pool, cpu_count
import time
from datetime import datetime

# Konfigurace
LIMIT_ROWS = 999999999
BATCH_SIZE = 50000

def get_db_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=TAHAL\\DATA_WAREHOUSE;"
        "Database=DWH;"
        "UID=sa;"
        "PWD=HesloProBakalarku2025*;",
        autocommit=False
    )

def insert_dimensions(cursor, current_id, batch_end):
    print(f"📊 Vkládám nové hodnoty do dimenzí (LandingID {current_id}-{batch_end})...")
    cursor.execute("""
        SELECT DISTINCT
            City, Sensor, LP, DetectionType, LTRIM(RTRIM(VehClass)) AS VehClass, ILPC
        INTO ##TempDimensions
        FROM Stg.CameraCamea
        WHERE LandingID BETWEEN ? AND ?;
    """, (current_id, batch_end))

    cursor.execute("""
        INSERT INTO dbo.DimCity (CityName)
        SELECT City 
        FROM ##TempDimensions 
        WHERE City IS NOT NULL AND City <> ''
        EXCEPT
        SELECT CityName FROM dbo.DimCity;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimSensor (SensorCode)
        SELECT Sensor 
        FROM ##TempDimensions 
        WHERE Sensor IS NOT NULL AND Sensor <> ''
        EXCEPT
        SELECT SensorCode FROM dbo.DimSensor;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimLP (LicensePlate)
        SELECT LP 
        FROM ##TempDimensions 
        WHERE LP IS NOT NULL AND LP <> ''
        EXCEPT
        SELECT LicensePlate FROM dbo.DimLP;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimDetectionType (DetectionType)
        SELECT DetectionType 
        FROM ##TempDimensions 
        WHERE DetectionType IS NOT NULL AND DetectionType <> ''
        EXCEPT
        SELECT DetectionType FROM dbo.DimDetectionType;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimVehicleClass (VehicleClass)
        SELECT VehClass 
        FROM ##TempDimensions 
        WHERE VehClass IS NOT NULL AND VehClass <> ''
        EXCEPT
        SELECT VehicleClass FROM dbo.DimVehicleClass;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimCountry (CountryCode)
        SELECT ILPC
        FROM ##TempDimensions 
        WHERE ILPC IS NOT NULL AND ILPC <> ''
        EXCEPT
        SELECT CountryCode FROM dbo.DimCountry;
    """)

    cursor.execute("DROP TABLE ##TempDimensions;")

def insert_facts(cursor, current_id, batch_end):
    """
    Vrátíme reálný počet vložených řádků, abychom mohli logovat případné rozdíly oproti počtu řádků ve stagingu.
    """
    print(f"📥 Vkládám fakta (LandingID {current_id}-{batch_end})...")
    start_time = time.time()

    # Nejprve zjistíme, kolik záznamů je ve stagingu (v daném ID rozsahu).
    cursor.execute("""
        SELECT COUNT(*)
        FROM Stg.CameraCamea
        WHERE LandingID BETWEEN ? AND ?;
    """, (current_id, batch_end))
    stg_count = cursor.fetchone()[0]

    # Provedeme samotný INSERT do Fact tabulky
    cursor.execute("""
        INSERT INTO dbo.FactCameraDetection (
            TimeKey, 
            SensorKey, 
            DetectionTypeKey, 
            LPKey, 
            CountryKey, 
            VehicleClassKey, 
            CityKey, 
            Velocity
        )
        SELECT
            ISNULL(T.TimeKey, -1),
            ISNULL(Sen.SensorKey, -1),
            ISNULL(DT.DetectionTypeKey, -1),
            ISNULL(LP.LPKey, -1),
            ISNULL(Co.CountryKey, -1),
            ISNULL(VC.VehicleClassKey, -1),
            ISNULL(Ci.CityKey, -1),
            S.Velocity
        FROM Stg.CameraCamea AS S
        LEFT JOIN dbo.DimTime T
            ON CAST(S.OriginalTime AS DATE) = CAST(T.FullDate AS DATE)
            AND DATEPART(HOUR, S.OriginalTime) = T.HourNum
            AND DATEPART(MINUTE, S.OriginalTime) = T.MinuteNum
        LEFT JOIN dbo.DimSensor Sen ON S.Sensor = Sen.SensorCode
        LEFT JOIN dbo.DimDetectionType DT ON S.DetectionType = DT.DetectionType
        LEFT JOIN dbo.DimLP LP ON S.LP = LP.LicensePlate
        LEFT JOIN dbo.DimCountry Co ON S.ILPC = Co.CountryCode
        LEFT JOIN dbo.DimVehicleClass VC ON LTRIM(RTRIM(S.VehClass)) = LTRIM(RTRIM(VC.VehicleClass))
        LEFT JOIN dbo.DimCity Ci ON S.City = Ci.CityName
        WHERE S.LandingID BETWEEN ? AND ?;
    """, (current_id, batch_end))

    # Získáme reálný počet vložených řádků
    cursor.execute("SELECT @@ROWCOUNT;")
    inserted_count = cursor.fetchone()[0]

    duration = round(time.time() - start_time, 2)
    print(f"✅ Fakta vložena za {duration} s (vložených řádků: {inserted_count}, staging: {stg_count})")

    # Pokud se nevložily všechny řádky, zalogujeme rozdíl
    difference = stg_count - inserted_count
    if difference > 0:
        print(f"⚠️  {difference} řádků NEBYLO vloženo (z {stg_count} ve stagingu).")
       
        #  - Duplicate PK? 
        #  - Filtr v WHERE? 
        #  - Trigger atd.
        # např. zkusit dohledat, které řádky to byly, a uložit to do nějaké log tabulky.

    return inserted_count, stg_count

def process_batch(batch):
    current_id, batch_end = batch
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"\n➡️  Zpracovávám dávku: LandingID {current_id} až {batch_end}")
        insert_dimensions(cursor, current_id, batch_end)
        inserted_count, stg_count = insert_facts(cursor, current_id, batch_end)
        conn.commit()
        print(f"🎯 Dávka {current_id}-{batch_end} úspěšně dokončena.")
        return inserted_count  # Vracíme počet reálně vložených řádků
    except Exception as e:
        conn.rollback()
        print(f"❌ Chyba při zpracování dávky {current_id}-{batch_end}: {str(e)}")
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    try:
        conn_dwh = get_db_connection()
        cursor_dwh = conn_dwh.cursor()

        # 1) Zjistíme max. ID v /Bilina/kamery/camea/
        cursor_dwh.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic = '/Bilina/kamery/camea/%';
        """)
        max_id = cursor_dwh.fetchone()[0] or 0

        # 2) Načteme poslední zpracované ID pro /Bilina/kamery/staging_to_fact
        cursor_dwh.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic = '/Bilina/kamery/staging_to_fact';
        """)
        last_loaded_id = cursor_dwh.fetchone()[0] or 0

        # Pokud je 0, vezmeme min. LandingID z tabulky Stg.CameraCamea
        if last_loaded_id == 0:
            cursor_dwh.execute("SELECT COALESCE(MIN(LandingID), 0) FROM Stg.CameraCamea;")
            last_loaded_id = cursor_dwh.fetchone()[0] or 0

        current_id = last_loaded_id
        batch_limit = min(current_id + LIMIT_ROWS - 1, max_id)
        print(f"\n🚀 Zpracování záznamů s LandingID od {current_id} do {batch_limit}...\n")

        batches = [(i, min(i + BATCH_SIZE - 1, batch_limit)) 
                   for i in range(current_id, batch_limit + 1, BATCH_SIZE)]

        total_inserted = 0
        for batch in batches:
            inserted = process_batch(batch)
            total_inserted += inserted

        # 6) Aktualizace stavu ETL
        cursor_dwh.execute("""
            MERGE INTO ETL_IncrementalControl AS target
            USING (SELECT '/Bilina/kamery/staging_to_fact' AS Topic, ? AS LastLoadedID, SYSDATETIME() AS LastUpdate) AS source
            ON target.Topic = source.Topic
            WHEN MATCHED THEN UPDATE
                SET target.LastLoadedID = source.LastLoadedID,
                    target.LastUpdate = source.LastUpdate,
                    target.ProcessStep = 1
            WHEN NOT MATCHED THEN
                INSERT (Topic, LastLoadedID, FullLoadDone, LastUpdate, ProcessStep)
                VALUES (source.Topic, source.LastLoadedID, 0, source.LastUpdate, 1);
        """, (batch_limit,))

        # Zalogování do ETL_RunLog – tentokrát s počtem „reálně vložených“ řádků.
        cursor_dwh.execute("""
            INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, RowsInserted)
            VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', 'SUCCESS', SYSDATETIME(), ?);
        """, (total_inserted,))

        conn_dwh.commit()
        print(f"\n✅ ETL dokončeno. Celkem vloženo (reálně): {total_inserted} řádků.")

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"❌ Chyba ETL procesu: {str(e)}")
        cursor_dwh.execute("""
            INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, EndTime, ErrorMessage)
            VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', 'FAILED', SYSDATETIME(), SYSDATETIME(), ?);
        """, (error_traceback,))
        conn_dwh.commit()

    finally:
        cursor_dwh.close()
        conn_dwh.close()

if __name__ == "__main__":
    main()
