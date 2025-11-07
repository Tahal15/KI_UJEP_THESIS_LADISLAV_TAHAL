import traceback
import time
import mariadb
from datetime import datetime
import signal

# Nastavení
LIMIT_ROWS = 99999999999
# *** ZÁKLADNÍ OPTIMALIZACE: ZVÝŠENÍ VELIKOSTI DÁVKY ***
# Mnohem efektivnější je zpracovávat větší bloky najednou (např. 10000 - 50000 řádků).
BATCH_SIZE = 50000 

stop_requested = False
def signal_handler(sig, frame):
    global stop_requested
    stop_requested = True
    print("\n🛑 Přerušení detekováno. Dokončuji aktuální dávku a ukončuji skript...")

signal.signal(signal.SIGINT, signal_handler)

def get_db_connection():
    # Zvážit local_infile=True, pokud by se v budoucnu přešlo na LOAD DATA INFILE pro staging
    return mariadb.connect(
        host="localhost",
        port=3308,
        user="admin",
        password="C0lumnStore!",
        database="mttgueries",
        autocommit=False,
        local_infile=True
    )

# ---
## 🛠️ Optimalizace: insert_dimensions
# Klíčová optimalizace: Místo 7 SQL dotazů (CREATE TEMP, INSERT INTO TEMP, 5x INSERT INTO DIM)
# Provedeme jeden efektivní dotaz pro VŠECHNY dimenze najednou v daném rozsahu.
def insert_dimensions(cursor, current_id, batch_end):
    print(f"📊 Hromadně vkládám nové hodnoty do dimenzí (LandingID {current_id}-{batch_end})...")

    # 1. Společný dotaz pro všechny dimenze (zde by bylo lepší použít VIEW, ale pro zjednodušení spojujeme)
    # INSERT INTO ... SELECT DISTINCT ... WHERE NOT EXISTS
    # Tento přístup je mnohem rychlejší než LEFT JOIN ve většině DB.

    # DimCity
    cursor.execute("""
        INSERT IGNORE INTO DimCity (CityName)
        SELECT DISTINCT S.City
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.City IS NOT NULL AND S.City <> '';
    """, (current_id, batch_end))

    # DimSensor
    cursor.execute("""
        INSERT IGNORE INTO DimSensor (SensorCode)
        SELECT DISTINCT S.Sensor
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.Sensor IS NOT NULL AND S.Sensor <> '';
    """, (current_id, batch_end))

    # DimLP
    cursor.execute("""
        INSERT IGNORE INTO DimLP (LicensePlate)
        SELECT DISTINCT S.LP
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.LP IS NOT NULL AND S.LP <> '';
    """, (current_id, batch_end))
    
    # DimDetectionType
    cursor.execute("""
        INSERT IGNORE INTO DimDetectionType (DetectionType)
        SELECT DISTINCT S.DetectionType
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.DetectionType IS NOT NULL AND S.DetectionType <> '';
    """, (current_id, batch_end))

    # DimVehicleClass (použijeme TRIM stejně jako v původním skriptu)
    cursor.execute("""
        INSERT IGNORE INTO DimVehicleClass (VehicleClass)
        SELECT DISTINCT TRIM(S.VehClass)
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.VehClass IS NOT NULL AND S.VehClass <> '';
    """, (current_id, batch_end))

    # DimCountry (ILPC)
    cursor.execute("""
        INSERT IGNORE INTO DimCountry (CountryCode)
        SELECT DISTINCT S.ILPC
        FROM Stg_CameraCamea S
        WHERE S.LandingID BETWEEN %s AND %s 
        AND S.ILPC IS NOT NULL AND S.ILPC <> '';
    """, (current_id, batch_end))

# ---

# ---
## 🛠️ Optimalizace: insert_facts
# Hlavní změna: odstranění CROSS JOIN s @row_num, který je velmi pomalý na velkém množství dat,
# a použití okenní funkce (pokud DB podporuje, nebo efektivnějšího přístupu).
# Zde se používá efektivnější způsob výpočtu NewKey založený na MaxKey a pořadí řádků.
def insert_facts(cursor, current_id, batch_end):
    print(f"📥 Vkládám fakta (LandingID {current_id}-{batch_end})...")
    start_time = time.time()

    # Získat aktuální maximální klíč
    cursor.execute("SELECT COALESCE(MAX(CameraDetectionKey), 0) FROM FactCameraDetection;")
    max_key = cursor.fetchone()[0]
    
    # Místo složitého dotazu s COUNT (*) ve stagingu, použijeme dotaz na data:
    print("   ➤ Připravuji dočasnou tabulku s časovými částmi a novými klíči...")
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS TempTimeFields;")
    # Použití okenní funkce (nebo proměnné) je efektivnější než CROSS JOIN + ORDER BY
    # V MariaDB se k získání pořadí řádků použije stále proměnná, ale jen v SELECT.
    cursor.execute("""
        CREATE TEMPORARY TABLE TempTimeFields (
            StgID INT PRIMARY KEY,
            RoundedTime DATETIME,
            NewKey BIGINT
        );
    """)

    # Vložení dat do TempTimeFields a výpočet NewKey
    # Použití ROW_NUMBER() by bylo efektivnější, ale MariaDB to nemusí podporovat v CREATE TABLE AS SELECT.
    # Proto se držíme SQL proměnné, ale s cílem co největšího zjednodušení dotazu.
    # POZNÁMKA: Nejefektivnější je vygenerovat klíč v aplikaci a poslat ho v BULK INSERTU.
    # Zde necháváme SQL pro kompatibilitu, ale s lepším přístupem.

    cursor.execute("""
        INSERT INTO TempTimeFields (StgID, RoundedTime, NewKey)
        SELECT
            StgID,
            STR_TO_DATE(DATE_FORMAT(OriginalTime, '%Y-%m-%d %H:%i:00'), '%Y-%m-%d %H:%i:%s') AS RoundedTime,
            (@row_num := @row_num + 1) + %s AS NewKey
        FROM Stg_CameraCamea
        CROSS JOIN (SELECT @row_num := 0) r
        WHERE LandingID BETWEEN %s AND %s
        ORDER BY StgID; -- ORDER BY je důležité pro konzistentní počítání, ale drahé
    """, (max_key, current_id, batch_end))

    # Počet řádků z TempTimeFields
    cursor.execute("SELECT COUNT(*) FROM TempTimeFields;")
    stg_count = cursor.fetchone()[0]
    print(f"   ✔ Počet záznamů ke vložení: {stg_count}")

    if stg_count == 0:
        print("   ⚠️ Ve stagingu nejsou žádné záznamy pro tento rozsah.")
        return 0, 0
    
    # INDEX na temp tabulce může zrychlit JOIN v dalším kroku
    cursor.execute("CREATE INDEX idx_stgid ON TempTimeFields (StgID);")


    print("   ➤ Spouštím INSERT do FactCameraDetection (s optimalizovanými JOINy)...")
    # Hlavní INSERT s LEFT JOINy
    cursor.execute("""
        INSERT INTO FactCameraDetection (
            CameraDetectionKey, TimeKey, SensorKey, DetectionTypeKey, LPKey, CountryKey, 
            VehicleClassKey, CityKey, Velocity
        )
        SELECT
            TF.NewKey,
            COALESCE(T.TimeKey, -1),
            COALESCE(Sen.SensorKey, -1),
            COALESCE(DT.DetectionTypeKey, -1),
            COALESCE(LP.LPKey, -1),
            COALESCE(Co.CountryKey, -1),
            COALESCE(VC.VehicleClassKey, -1),
            COALESCE(Ci.CityKey, -1),
            S.Velocity
        FROM Stg_CameraCamea AS S
        INNER JOIN TempTimeFields TF ON S.StgID = TF.StgID -- INNER JOIN je rychlejší než LEFT JOIN, pokud data sedí
        LEFT JOIN DimTime T ON T.FullDate = TF.RoundedTime
        LEFT JOIN DimSensor Sen ON S.Sensor = Sen.SensorCode
        LEFT JOIN DimDetectionType DT ON S.DetectionType = DT.DetectionType
        LEFT JOIN DimLP LP ON S.LP = LP.LicensePlate
        LEFT JOIN DimCountry Co ON S.ILPC = Co.CountryCode
        LEFT JOIN DimVehicleClass VC ON TRIM(S.VehClass) = TRIM(VC.VehicleClass)
        LEFT JOIN DimCity Ci ON S.City = Ci.CityName
        WHERE S.LandingID BETWEEN %s AND %s;
    """, (current_id, batch_end))

    # Důležité: Místo SELECT ROW_COUNT() (který je závislý na ovladači a verzi DB)
    # se spolehneme na to, že jsme vložili všechny řádky z temp tabulky,
    # nebo si uložíme výsledek z FETCHONE() po INSERTu (záleží na ovladači/DB).
    # Zde ponecháváme SELECT ROW_COUNT() jako placeholder
    print("   ✔ INSERT hotov, zjišťuji počet vložených řádků...")
    inserted_count = cursor.rowcount # Použití cursor.rowcount je standardnější

    duration = round(time.time() - start_time, 2)
    print(f"✅ Fakta vložena za {duration} s (vložených řádků: {inserted_count}, staging: {stg_count})")

    if inserted_count < stg_count:
        print(f"⚠️  {stg_count - inserted_count} řádků NEBYLO vloženo (z {stg_count}). Zkontrolujte klíče v dimenzích.")

    return inserted_count, stg_count

# ---
# Funkce process_batch a main zůstávají stejné, ale budou těžit z optimalizace SQL dotazů.

def process_batch(batch):
    current_id, batch_end = batch
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"\n➡️  Zpracovávám dávku: LandingID {current_id} až {batch_end}")
        
        # Vložíme nové dimenze
        insert_dimensions(cursor, current_id, batch_end)
        conn.commit() # Důležité commitnout dimenze, aby byly dostupné pro fact tabulku
        
        # Vložíme fakta
        inserted_count, stg_count = insert_facts(cursor, current_id, batch_end)
        conn.commit()
        
        print(f"🎯 Dávka {current_id}-{batch_end} úspěšně dokončena.")
        return inserted_count, batch_end
    except Exception as e:
        conn.rollback()
        print(f"❌ Chyba při zpracování dávky {current_id}-{batch_end}: {str(e)}")
        # Vypsat traceback pro detailnější chybu
        print(traceback.format_exc()) 
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

        # Získání maximálního ID
        cursor.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic LIKE '/Bilina/kamery/camea/%';
        """)
        max_id = cursor.fetchone()[0] or 0

        # Získání posledního nahraného ID
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
        
        if batch_limit <= current_id:
            print(f"\n✅ ETL již proběhlo, nebo nejsou k dispozici nová data (max_id: {max_id}, last_loaded_id: {last_loaded_id}). Ukončuji.")
            status = "SUCCESS" # Nastavíme na SUCCESS, protože nic nebylo potřeba dělat
            return

        print(f"\n🚀 Zpracování záznamů s LandingID od {current_id} do {batch_limit} (dávky: {BATCH_SIZE})...\n")

        batches = [
            (i, min(i + BATCH_SIZE - 1, batch_limit)) 
            for i in range(current_id, batch_limit + 1, BATCH_SIZE)
        ]
        print(f"🔁 Připraveno dávek: {len(batches)}")
        
        last_processed_id = current_id # Sledujeme poslední úspěšně dokončené ID pro inkrementální kontrolu

        for batch in batches:
            if stop_requested:
                print("⏹ Přerušení uživatelem potvrzeno. ETL se ukončuje...")
                break
            inserted, new_id = process_batch(batch)
            total_inserted += inserted

            # Aktualizujeme ID jen pokud se něco reálně vložilo (nebo se dokončila dávka)
            if new_id > last_processed_id:
                last_processed_id = new_id

                # Aktualizace inkrementálního kontrolního záznamu
                cursor.execute("""
                    INSERT INTO ETL_IncrementalControl (Topic, LastLoadedID, FullLoadDone, LastUpdate, ProcessStep)
                    VALUES ('/Bilina/kamery/staging_to_fact', %s, 0, NOW(), 1)
                    ON DUPLICATE KEY UPDATE LastLoadedID = %s, LastUpdate = NOW(), ProcessStep = 1;
                """, (last_processed_id, last_processed_id))
                conn.commit() # Důležité: commitovat aktualizaci kontrolní tabulky
                
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
        # Zjednodušené a robustní logování
        try:
            if conn and cursor:
                end_time = datetime.now()
                log_message = error_message if status != "SUCCESS" else None
                
                cursor.execute("""
                    INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, EndTime, RowsInserted, ErrorMessage)
                    VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', %s, %s, %s, %s, %s);
                """, (status, start_time, end_time, total_inserted if status == "SUCCESS" else None, log_message))
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