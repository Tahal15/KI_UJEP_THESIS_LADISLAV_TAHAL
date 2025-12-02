import pyodbc
import traceback
from multiprocessing import Pool, cpu_count

"""
Tento skript provádí inkrementální ETL (Extract, Transform, Load) proces pro zpracování dat z kamerového systému v lokalitě Bílina.

🔹 1️⃣ Připojení k DWH:
    - Připojí se k databázi DWH pomocí ODBC.

🔹 2️⃣ Zjištění ID pro inkrementální načítání:
    - Načte maximální ID z tabulky `ETL_IncrementalControl` pro `/Bilina/kamery/camea/`, aby určil nejnovější dostupná data.
    - Načte poslední zpracované ID pro `/Bilina/kamery/staging_to_fact`.
    - Pokud `staging_to_fact` ještě nebylo spuštěno, zjistí minimální `LandingID` ve `Stg.CameraCamea`.

🔹 3️⃣ Nastavení rozsahu pro inkrementální zpracování:
    - Definuje `current_id` jako výchozí ID pro načítání.
    - Vypočítá maximální ID (`batch_limit`), které bude zpracováno v tomto běhu.
    - Omezuje počet zpracovaných řádků na hodnotu `LIMIT_ROWS`.

🔹 5️⃣ Přesun dat do faktové tabulky `FactCameraDetection`:
    - Přesouvá transakční data (detekce z kamer) do `FactCameraDetection`, kde propojí data s dimenzemi `DimTime` a `DimCamera`.
    - Omezuje počet zpracovaných řádků podle `LIMIT_ROWS`.

🔹 6️⃣ Logování ETL procesu:
    - Aktualizuje tabulku `ETL_IncrementalControl`, aby uchoval informaci o posledním načteném ID.
    - Zaznamenává běh ETL procesu do `ETL_RunLog`.

🔹 7️⃣ Úspěšné dokončení nebo chyba:
    - Po úspěšném dokončení aktualizuje stav běhu na `SUCCESS` v `ETL_RunLog`.
    - Pokud dojde k chybě, zaznamená chybu včetně tracebacku do `ETL_RunLog`.

🔹 8️⃣ Ukončení připojení:
    - Uzavře kurzor a spojení s databází.

Skript je optimalizován pro inkrementální načítání a efektivní ETL zpracování dat.
"""


# Připojení k DWH
def get_db_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=TAHAL\\DATA_WAREHOUSE;"
        "Database=DWH;"
        "UID=sa;"
        "PWD=HesloProBakalarku2025*;",
        autocommit=False  # Vypnutí autocommit pro lepší kontrolu transakcí
    )

# Testovací limit pro inkrement
LIMIT_ROWS = 999999999
BATCH_SIZE = 10000

# Funkce pro vkládání do dimenzí
def insert_dimensions(cursor, current_id, batch_end):
    # Vytvoření dočasné tabulky pro jedinečné hodnoty
    cursor.execute("""
        SELECT DISTINCT
            City, Sensor, LP, DetectionType, LTRIM(RTRIM(VehClass)) AS VehClass, ILPC
        INTO ##TempDimensions
        FROM Stg.CameraCamea
        WHERE LandingID BETWEEN ? AND ?;
    """, (current_id, batch_end))

    # Vložení do dimenzí z dočasné tabulky
    cursor.execute("""
        INSERT INTO dbo.DimCity (CityName)
        SELECT City FROM ##TempDimensions WHERE City IS NOT NULL
        EXCEPT SELECT CityName FROM dbo.DimCity;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimSensor (SensorCode)
        SELECT Sensor FROM ##TempDimensions WHERE Sensor IS NOT NULL AND Sensor <> ''
        EXCEPT SELECT SensorCode FROM dbo.DimSensor;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimLP (LicensePlate)
        SELECT LP FROM ##TempDimensions WHERE LP IS NOT NULL AND LP <> ''
        EXCEPT SELECT LicensePlate FROM dbo.DimLP;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimDetectionType (DetectionType)
        SELECT DetectionType FROM ##TempDimensions WHERE DetectionType IS NOT NULL AND DetectionType <> ''
        EXCEPT SELECT DetectionType FROM dbo.DimDetectionType;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimVehicleClass (VehicleClass)
        SELECT VehClass FROM ##TempDimensions WHERE VehClass IS NOT NULL
        EXCEPT SELECT VehicleClass FROM dbo.DimVehicleClass;
    """)

    cursor.execute("""
        INSERT INTO dbo.DimCountry (CountryCode)
        SELECT ILPC FROM ##TempDimensions WHERE ILPC IS NOT NULL AND ILPC <> ''
        EXCEPT SELECT CountryCode FROM dbo.DimCountry;
    """)

    # Vyčištění dočasné tabulky
    cursor.execute("DROP TABLE ##TempDimensions;")

# Funkce pro vkládání do faktové tabulky
def insert_facts(cursor, current_id, batch_end):
    cursor.execute("""
        INSERT INTO dbo.FactCameraDetection (
            TimeKey, SensorKey, DetectionTypeKey, LPKey, CountryKey, VehicleClassKey, Velocity
        )
        SELECT
            T.TimeKey,
            Sen.SensorKey,
            DT.DetectionTypeKey,
            LP.LPKey,
            Co.CountryKey,
            VC.VehicleClassKey,
            S.Velocity
        FROM Stg.CameraCamea AS S
        JOIN dbo.DimTime T
            ON CAST(S.OriginalTime AS DATE) = CAST(T.FullDate AS DATE)
            AND DATEPART(HOUR, S.OriginalTime) = T.HourNum
            AND DATEPART(MINUTE, S.OriginalTime) = T.MinuteNum
        JOIN dbo.DimSensor Sen ON S.Sensor = Sen.SensorCode
        JOIN dbo.DimDetectionType DT ON S.DetectionType = DT.DetectionType
        JOIN dbo.DimLP LP ON S.LP = LP.LicensePlate
        JOIN dbo.DimCountry Co ON S.ILPC = Co.CountryCode
        JOIN dbo.DimVehicleClass VC ON LTRIM(RTRIM(S.VehClass)) = LTRIM(RTRIM(VC.VehicleClass))
        WHERE S.LandingID BETWEEN ? AND ?;
    """, (current_id, batch_end))

# Hlavní funkce pro zpracování dávky
def process_batch(batch):
    current_id, batch_end = batch
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        insert_dimensions(cursor, current_id, batch_end)
        insert_facts(cursor, current_id, batch_end)
        conn.commit()
        rows_inserted = cursor.rowcount
        print(f"Uloženo {rows_inserted} řádků (LandingID {current_id} až {batch_end}).")
        return rows_inserted
    except Exception as e:
        conn.rollback()
        print(f"❌ Chyba při zpracování dávky {current_id}-{batch_end}: {str(e)}")
        return 0
    finally:
        cursor.close()
        conn.close()

# Hlavní skript
def main():
    try:
        conn_dwh = get_db_connection()
        cursor_dwh = conn_dwh.cursor()

        # Zjištění ID pro zpracování
        cursor_dwh.execute("SELECT COALESCE(MAX(LastLoadedID), 0) FROM ETL_IncrementalControl WHERE Topic = '/Bilina/kamery/camea/%';")
        max_id = cursor_dwh.fetchone()[0] or 0

        cursor_dwh.execute("SELECT COALESCE(MAX(LastLoadedID), 0) FROM ETL_IncrementalControl WHERE Topic = '/Bilina/kamery/staging_to_fact';")
        last_loaded_id = cursor_dwh.fetchone()[0] or 0

        if last_loaded_id == 0:
            cursor_dwh.execute("SELECT COALESCE(MIN(LandingID), 0) FROM Stg.CameraCamea;")
            last_loaded_id = cursor_dwh.fetchone()[0] or 0

        current_id = last_loaded_id
        batch_limit = min(current_id + LIMIT_ROWS - 1, max_id)

        print(f"Zpracování záznamů s LandingID od {current_id} do {batch_limit}...")

        # Příprava dávek pro paralelní zpracování
        batches = [(i, min(i + BATCH_SIZE - 1, batch_limit)) for i in range(current_id, batch_limit + 1, BATCH_SIZE)]

        # Paralelní zpracování dávek
        with Pool(processes=cpu_count()) as pool:
            results = pool.map(process_batch, batches)
            rows_inserted_total = sum(results)

        # Aktualizace ETL_IncrementalControl a ETL_RunLog
        cursor_dwh.execute("""
            MERGE INTO ETL_IncrementalControl AS target
            USING (SELECT '/Bilina/kamery/staging_to_fact' AS Topic, ? AS LastLoadedID, SYSDATETIME() AS LastUpdate) AS source
            ON target.Topic = source.Topic
            WHEN MATCHED THEN UPDATE SET target.LastLoadedID = source.LastLoadedID, target.LastUpdate = source.LastUpdate, target.ProcessStep = 1
            WHEN NOT MATCHED THEN INSERT (Topic, LastLoadedID, FullLoadDone, LastUpdate, ProcessStep)
            VALUES (source.Topic, source.LastLoadedID, 0, source.LastUpdate, 1);
        """, (batch_limit,))

        cursor_dwh.execute("""
            INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, RowsInserted)
            VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', 'SUCCESS', SYSDATETIME(), ?);
        """, (rows_inserted_total,))

        conn_dwh.commit()
        print(f"✅ Přesunuto {rows_inserted_total} řádků do FactCameraDetection.")

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        print(f"❌ Chyba ETL procesu: {error_message}")

        # Zalogování chyby
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