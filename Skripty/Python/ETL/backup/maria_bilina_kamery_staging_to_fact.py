import traceback
import time
import mariadb
from datetime import datetime
import signal

# Nastavení
LIMIT_ROWS = 99999999999
BATCH_SIZE = 1000

stop_requested = False
def signal_handler(sig, frame):
    global stop_requested
    stop_requested = True
    print("\n🛑 Přerušení detekováno. Dokončuji aktuální dávku a ukončuji skript...")

signal.signal(signal.SIGINT, signal_handler)

def get_db_connection():
    return mariadb.connect(
        host="localhost",
        port=3307,
        user="root",
        password="tohlejeroothesloprobakalarku2025",
        database="mttgueries",
        autocommit=False
    )

def insert_dimensions(cursor, current_id, batch_end):
    print(f"📊 Vkládám nové hodnoty do dimenzí (LandingID {current_id}-{batch_end})...")

    # 1. DROP a CREATE temp table bez dat
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS TempDimensions;")
    cursor.execute("""
        CREATE TEMPORARY TABLE TempDimensions (
            City VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
            Sensor VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
            LP VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
            DetectionType VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
            VehClass VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
            ILPC VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        );
    """)

    # 2. Vložení dat zvlášť
    cursor.execute("""
        INSERT INTO TempDimensions (City, Sensor, LP, DetectionType, VehClass, ILPC)
        SELECT DISTINCT
            City, Sensor, LP, DetectionType, TRIM(VehClass), ILPC
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %s AND %s;
    """, (current_id, batch_end))

    # INSERTy do dimenzí pomocí LEFT JOIN
    cursor.execute("""
        INSERT INTO DimCity (CityName)
        SELECT DISTINCT tmp.City
        FROM TempDimensions tmp
        LEFT JOIN DimCity dim ON dim.CityName = tmp.City
        WHERE tmp.City IS NOT NULL AND tmp.City <> '' AND dim.CityName IS NULL;
    """)

    cursor.execute("""
        INSERT INTO DimSensor (SensorCode)
        SELECT DISTINCT tmp.Sensor
        FROM TempDimensions tmp
        LEFT JOIN DimSensor dim ON dim.SensorCode = tmp.Sensor
        WHERE tmp.Sensor IS NOT NULL AND tmp.Sensor <> '' AND dim.SensorCode IS NULL;
    """)

    cursor.execute("""
        INSERT INTO DimLP (LicensePlate)
        SELECT DISTINCT tmp.LP
        FROM TempDimensions tmp
        LEFT JOIN DimLP dim ON dim.LicensePlate = tmp.LP
        WHERE tmp.LP IS NOT NULL AND tmp.LP <> '' AND dim.LicensePlate IS NULL;
    """)

    cursor.execute("""
        INSERT INTO DimDetectionType (DetectionType)
        SELECT DISTINCT tmp.DetectionType
        FROM TempDimensions tmp
        LEFT JOIN DimDetectionType dim ON dim.DetectionType = tmp.DetectionType
        WHERE tmp.DetectionType IS NOT NULL AND tmp.DetectionType <> '' AND dim.DetectionType IS NULL;
    """)

    cursor.execute("""
        INSERT INTO DimVehicleClass (VehicleClass)
        SELECT DISTINCT tmp.VehClass
        FROM TempDimensions tmp
        LEFT JOIN DimVehicleClass dim ON dim.VehicleClass = tmp.VehClass
        WHERE tmp.VehClass IS NOT NULL AND tmp.VehClass <> '' AND dim.VehicleClass IS NULL;
    """)

    cursor.execute("""
        INSERT INTO DimCountry (CountryCode)
        SELECT DISTINCT tmp.ILPC
        FROM TempDimensions tmp
        LEFT JOIN DimCountry dim ON dim.CountryCode = tmp.ILPC
        WHERE tmp.ILPC IS NOT NULL AND tmp.ILPC <> '' AND dim.CountryCode IS NULL;
    """)



def insert_facts(cursor, current_id, batch_end):
    print(f"📥 Vkládám fakta (LandingID {current_id}-{batch_end})...")
    start_time = time.time()

    print("   ➤ Zjišťuji počet řádků ve stagingu...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %s AND %s;
    """, (current_id, batch_end))
    stg_count = cursor.fetchone()[0]
    print(f"   ✔ Počet ve stagingu: {stg_count}")

    if stg_count == 0:
        print("   ⚠️ Ve stagingu nejsou žádné záznamy pro tento rozsah.")
        return 0, 0

    print("   ➤ Připravuji dočasnou tabulku s časovými částmi...")
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS TempTimeFields;")
    cursor.execute("""
        CREATE TEMPORARY TABLE TempTimeFields AS
        SELECT
            StgID,
            STR_TO_DATE(DATE_FORMAT(OriginalTime, '%Y-%m-%d %H:%i:00'), '%Y-%m-%d %H:%i:%s') AS RoundedTime
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %s AND %s;
    """, (current_id, batch_end))

    print("   ➤ Spouštím INSERT do FactCameraDetection...")
    cursor.execute("""
        INSERT INTO FactCameraDetection (
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
            COALESCE(T.TimeKey, -1),
            COALESCE(Sen.SensorKey, -1),
            COALESCE(DT.DetectionTypeKey, -1),
            COALESCE(LP.LPKey, -1),
            COALESCE(Co.CountryKey, -1),
            COALESCE(VC.VehicleClassKey, -1),
            COALESCE(Ci.CityKey, -1),
            S.Velocity
        FROM Stg_CameraCamea AS S
        LEFT JOIN TempTimeFields TF ON S.StgID = TF.StgID
        LEFT JOIN DimTime T 
            ON T.FullDate = TF.RoundedTime
        LEFT JOIN DimSensor Sen ON S.Sensor = Sen.SensorCode
        LEFT JOIN DimDetectionType DT ON S.DetectionType = DT.DetectionType
        LEFT JOIN DimLP LP ON S.LP = LP.LicensePlate
        LEFT JOIN DimCountry Co ON S.ILPC = Co.CountryCode
        LEFT JOIN DimVehicleClass VC ON TRIM(S.VehClass) = TRIM(VC.VehicleClass)
        LEFT JOIN DimCity Ci ON S.City = Ci.CityName
        WHERE S.LandingID BETWEEN %s AND %s;
    """, (current_id, batch_end))

    print("   ✔ INSERT hotov, zjišťuji počet vložených řádků...")
    cursor.execute("SELECT ROW_COUNT();")
    inserted_count = cursor.fetchone()[0]

    duration = round(time.time() - start_time, 2)
    print(f"✅ Fakta vložena za {duration} s (vložených řádků: {inserted_count}, staging: {stg_count})")

    if inserted_count < stg_count:
        print(f"⚠️  {stg_count - inserted_count} řádků NEBYLO vloženo (z {stg_count})")

    return inserted_count, stg_count

def process_batch(batch):
    current_id, batch_end = batch
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"\n➡️  Zpracovávám dávku: LandingID {current_id} až {batch_end}")
        insert_dimensions(cursor, current_id, batch_end)
        conn.commit()
        inserted_count, stg_count = insert_facts(cursor, current_id, batch_end)
        conn.commit()
        print(f"🎯 Dávka {current_id}-{batch_end} úspěšně dokončena.")
        return inserted_count, batch_end
    except Exception as e:
        conn.rollback()
        print(f"❌ Chyba při zpracování dávky {current_id}-{batch_end}: {str(e)}")
        return 0, current_id
    finally:
        cursor.close()
        conn.close()

def main():
    conn = None
    cursor = None
    start_time = datetime.now()
    total_inserted = 0
    status = "FAILED"
    error_message = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic LIKE '/Bilina/kamery/camea/%';
        """)
        max_id = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic = '/Bilina/kamery/staging_to_fact';
        """)
        last_loaded_id = cursor.fetchone()[0] or 0

        if last_loaded_id == 0:
            cursor.execute("SELECT COALESCE(MIN(LandingID), 0) FROM Stg_CameraCamea;")
            last_loaded_id = cursor.fetchone()[0] or 0

        current_id = last_loaded_id
        batch_limit = min(current_id + LIMIT_ROWS - 1, max_id)
        print(f"\n🚀 Zpracování záznamů s LandingID od {current_id} do {batch_limit}...\n")

        batches = [
            (i, min(i + BATCH_SIZE - 1, batch_limit)) 
            for i in range(current_id, batch_limit + 1, BATCH_SIZE)
        ]
        print(f"🔁 Připraveno dávek: {len(batches)}")

        for batch in batches:
            if stop_requested:
                print("⏹ Přerušení uživatelem potvrzeno. ETL se ukončuje...")
                break
            inserted, new_id = process_batch(batch)
            total_inserted += inserted

            # aktualizujeme ID jen pokud se něco reálně vložilo
            if inserted > 0:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM ETL_IncrementalControl
                    WHERE Topic = '/Bilina/kamery/staging_to_fact';
                """)
                exists = cursor.fetchone()[0] > 0

                if exists:
                    cursor.execute("""
                        UPDATE ETL_IncrementalControl
                        SET LastLoadedID = %s,
                            LastUpdate = NOW(),
                            ProcessStep = 1
                        WHERE Topic = '/Bilina/kamery/staging_to_fact';
                    """, (new_id,))
                else:
                    cursor.execute("""
                        INSERT INTO ETL_IncrementalControl (Topic, LastLoadedID, FullLoadDone, LastUpdate, ProcessStep)
                        VALUES ('/Bilina/kamery/staging_to_fact', %s, 0, NOW(), 1);
                    """, (new_id,))
                conn.commit()
        status = "SUCCESS"
        print(f"\n✅ ETL dokončeno. Celkem vloženo (reálně): {total_inserted} řádků.")

    except KeyboardInterrupt:
        print("\n⛔️ ETL proces byl přerušen uživatelem (Ctrl+C)")
        error_message = "ETL přerušeno uživatelem (KeyboardInterrupt)"
        status = "FAILED"

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"❌ Chyba ETL procesu: {str(e)}")

    finally:
        try:
            if cursor and conn:
                end_time = datetime.now()
                if status == "SUCCESS":
                    cursor.execute("""
                        INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, EndTime, RowsInserted)
                        VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', %s, %s, %s, %s);
                    """, (status, start_time, end_time, total_inserted))
                else:
                    cursor.execute("""
                        INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, EndTime, ErrorMessage)
                        VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', %s, %s, %s, %s);
                    """, (status, start_time, end_time, error_message))
                conn.commit()
        except Exception as log_err:
            print(f"⚠️ Chyba při logování do ETL_RunLog: {log_err}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

if __name__ == "__main__":
    main()
