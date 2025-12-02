import traceback
import time
import mariadb
from datetime import datetime
import signal
import csv
import tempfile
import os
import sys

# Nastavení
LIMIT_ROWS = 99999999999
BATCH_SIZE = 500000

stop_requested = False
def signal_handler(sig, frame):
    global stop_requested
    stop_requested = True
    print("\n🛑 Přerušení detekováno. Dokončuji aktuální dávku a ukončuji skript...")

signal.signal(signal.SIGINT, signal_handler)

def get_db_connection():
    return mariadb.connect(
        host="localhost",
        port=3308,
        user="admin",
        password="C0lumnStore!",
        database="mttgueries",
        autocommit=False,
        local_infile=True # Nutné pro LOAD DATA LOCAL INFILE
    )

# --- ZRUŠENÍ TŘÍDY DimensionCache ---

def insert_dimensions_bulk_set_based(cursor, staging_data):
    """
    Sada-orientované vkládání dimenzí (efektivní náhrada INSERT IGNORE).
    """
    print(f"📊 Vkládám nové dimenze pomocí INSERT SELECT LEFT JOIN...")
    
    # 1. Použijeme dočasnou tabulku pro unikátní hodnoty v dávce
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS TempDimensionsBulk;")
    cursor.execute("""
        CREATE TEMPORARY TABLE TempDimensionsBulk (
            City VARCHAR(255),
            Sensor VARCHAR(255),
            LP VARCHAR(50),
            DetectionType VARCHAR(50),
            VehClass VARCHAR(50),
            Country VARCHAR(50)
        );
    """)

    # Připravíme data k vložení do dočasné tabulky (Python zpracovává jen unikáty pro tuto dávku)
    cities = set(row[2] for row in staging_data if row[2])
    sensors = set(row[6] for row in staging_data if row[6])
    lps = set(row[5] for row in staging_data if row[5])
    detections = set(row[3] for row in staging_data if row[3])
    vehicles = set(row[7] for row in staging_data if row[7] is not None)
    countries = set(row[8] for row in staging_data if row[8])

    # Sjednotíme data a vložíme do dočasné tabulky
    temp_data = []
    max_len = max(len(cities), len(sensors), len(lps), len(detections), len(vehicles), len(countries))

    # Tato část je neefektivní v Pythonu, pokud se dělá pro KAŽDOU DIMENZI zvlášť.
    # Proto se použije jen jedna dočasná tabulka pro všechny dimenze (zjednodušený přístup)
    
    # Pro jednoduchost se vrátíme k hromadnému INSERT IGNORE, který je pro MariaDB v pořádku
    # a je snazší na údržbu než 6x INSERT INTO SELECT LEFT JOIN.
    
    if cities:
        cursor.executemany("INSERT IGNORE INTO DimCity (CityName) VALUES (%s)", [(c,) for c in cities])
    if sensors:
        cursor.executemany("INSERT IGNORE INTO DimSensor (SensorCode) VALUES (%s)", [(s,) for s in sensors])
    if lps:
        cursor.executemany("INSERT IGNORE INTO DimLP (LicensePlate) VALUES (%s)", [(l,) for l in lps])
    if detections:
        cursor.executemany("INSERT IGNORE INTO DimDetectionType (DetectionType) VALUES (%s)", [(d,) for d in detections])
    if vehicles:
        cursor.executemany("INSERT IGNORE INTO DimVehicleClass (VehicleClass) VALUES (%s)", [(v,) for v in vehicles])
    if countries:
        cursor.executemany("INSERT IGNORE INTO DimCountry (CountryCode) VALUES (%s)", [(c,) for c in countries])
    
    print(f"   ✔ Vloženo nových dimenzí.")


def round_time_to_minute(dt):
    """Zaokrouhlí datetime na minutu"""
    if not dt:
        return None
    return dt.replace(second=0, microsecond=0)

def insert_facts_bulk_file(cursor, staging_data, max_key):
    """
    EXTRÉMNÍ OPTIMALIZACE pro ColumnStore: LOAD DATA INFILE
    Tento kód generuje klíč v Pythonu, což je správné pro ColumnStore.
    """
    print(f"📥 Připravuji {len(staging_data):,} řádků pro bulk insert...")
    start_time = time.time()
    
    # 1. Načteme VŠECHNY KLÍČE dimenzí PŘED vkládáním faktů
    # To je nutné, protože ColumnStore bulk loader NEUMÍ JOINy!
    class DimensionCache:
        def __init__(self, c):
            # Tady načítáme VŠECHNY klíče, což je v ColumnStore nutné!
            c.execute("SELECT CityKey, CityName FROM DimCity")
            self.city = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT SensorKey, SensorCode FROM DimSensor")
            self.sensor = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT LPKey, LicensePlate FROM DimLP")
            self.lp = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT DetectionTypeKey, DetectionType FROM DimDetectionType")
            self.detection = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT VehicleClassKey, VehicleClass FROM DimVehicleClass")
            self.vehicle = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT CountryKey, CountryCode FROM DimCountry")
            self.country = {row[1]: row[0] for row in c.fetchall()}
            c.execute("SELECT TimeKey, FullDate FROM DimTime")
            self.time = {row[1]: row[0] for row in c.fetchall()}

    cache = DimensionCache(cursor) # Načteme cache jen před vkládáním faktů

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', suffix='.csv')
    csv_path = temp_file.name
    
    try:
        writer = csv.writer(temp_file)
        new_key = max_key
        
        # Zapíšeme data do CSV
        for row in staging_data:
            new_key += 1
            stg_id, original_time, city, detection, utc, lp, sensor, vehicle, country, velocity = row
            
            # Zaokrouhlení času a Lookup klíčů
            rounded_time = round_time_to_minute(original_time)
            
            time_key = cache.time.get(rounded_time, -1)
            sensor_key = cache.sensor.get(sensor, -1) if sensor else -1
            detection_key = cache.detection.get(detection, -1) if detection else -1
            lp_key = cache.lp.get(lp, -1) if lp else -1
            country_key = cache.country.get(country, -1) if country else -1
            vehicle_key = cache.vehicle.get(vehicle, -1) if vehicle is not None else -1
            city_key = cache.city.get(city, -1) if city else -1
            
            # Zapsat řádek do CSV (s CameraDetectionKey)
            writer.writerow([
                new_key, time_key, sensor_key, detection_key, lp_key,
                country_key, vehicle_key, city_key, velocity if velocity is not None else '\\N'
            ])
        
        temp_file.close()
        
        # BULK INSERT přes LOAD DATA INFILE
        print(f"   ➤ Spouštím LOAD DATA INFILE (ColumnStore bulk insert)...")
        
        csv_path_escaped = csv_path.replace('\\', '/')
        
        load_sql = f"""
            LOAD DATA LOCAL INFILE '{csv_path_escaped}'
            INTO TABLE FactCameraDetection
            FIELDS TERMINATED BY ',' 
            LINES TERMINATED BY '\n'
            (CameraDetectionKey, TimeKey, SensorKey, DetectionTypeKey, LPKey, 
             CountryKey, VehicleClassKey, CityKey, @velocity)
            SET Velocity = NULLIF(@velocity, '\\\\N')
        """
        
        cursor.execute(load_sql)
        inserted_count = cursor.rowcount
        
        duration = round(time.time() - start_time, 2)
        print(f"✅ Fakta vložena za {duration}s ({inserted_count:,} řádků) - {inserted_count/duration:,.0f} řádků/s")
        
        return inserted_count, new_key
        
    finally:
        try:
            os.unlink(csv_path)
        except:
            pass

def process_batch(batch):
    current_id, batch_end = batch
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"\n➡️  Zpracovávám dávku: LandingID {current_id} až {batch_end}")
        
        # Načteme staging data
        print("   ➤ Načítám data ze stagingu...")
        cursor.execute("""
            SELECT StgID, OriginalTime, City, DetectionType, Utc, LP, 
                         Sensor, VehClass, ILPC, Velocity
            FROM Stg_CameraCamea
            WHERE LandingID BETWEEN %s AND %s
            ORDER BY StgID
        """, (current_id, batch_end))
        
        staging_data = cursor.fetchall()
        print(f"   ✔ Načteno {len(staging_data):,} řádků")
        
        if not staging_data:
            print("   ⚠️ Žádná data k zpracování")
            return 0, batch_end
        
        # Vložíme nové dimenze (Sada-orientovaný INSERT IGNORE je OK)
        insert_dimensions_bulk_set_based(cursor, staging_data)
        conn.commit() # Commit dimenzí
        
        # Získáme maximální klíč pro ruční generování
        cursor.execute("SELECT COALESCE(MAX(CameraDetectionKey), 0) FROM FactCameraDetection")
        max_key = cursor.fetchone()[0]
        
        # Vložíme fakta přes LOAD DATA INFILE (s ručně generovaným klíčem)
        inserted_count, new_max_key = insert_facts_bulk_file(cursor, staging_data, max_key)
        conn.commit() # Commit faktů
        
        print(f"🎯 Dávka {current_id}-{batch_end} úspěšně dokončena.")
        return inserted_count, batch_end
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Chyba při zpracování dávky {current_id}-{batch_end}: {str(e)}")
        print(traceback.format_exc()) 
        return 0, current_id
    finally:
        cursor.close()
        conn.close()

# Funkce main() zůstává beze změny

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

        # Získání max. ID ze Stagingu
        cursor.execute("""
            SELECT COALESCE(MAX(LastLoadedID), 0)
            FROM ETL_IncrementalControl
            WHERE Topic LIKE '/Bilina/kamery/camea/%%';
        """)
        max_id = cursor.fetchone()[0] or 0

        # Získání posledního zpracovaného ID pro Fact
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
            print(f"\n✅ ETL již proběhlo, nebo nejsou k dispozici nová data.")
            status = "SUCCESS"
            return

        print(f"\n🚀 Zpracování záznamů s LandingID od {current_id:,} do {batch_limit:,} (dávky: {BATCH_SIZE:,})...\n")

        batches = [
            (i, min(i + BATCH_SIZE - 1, batch_limit)) 
            for i in range(current_id, batch_limit + 1, BATCH_SIZE)
        ]
        print(f"🔁 Připraveno dávek: {len(batches)}\n")
        
        last_processed_id = current_id

        for idx, batch in enumerate(batches, 1):
            if stop_requested:
                print("⏹ Přerušení uživatelem potvrzeno. ETL se ukončuje...")
                break
            
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = total_inserted / elapsed if elapsed > 0 else 0
            remaining_rows = batch_limit - last_processed_id
            eta = remaining_rows / rate if rate > 0 else 0
            
            print(f"[{idx}/{len(batches)}] Celková rychlost: {rate:,.0f} řádků/s | ETA: {eta/60:.1f} min")
            
            inserted, new_id = process_batch(batch)
            total_inserted += inserted

            if new_id > last_processed_id:
                last_processed_id = new_id

                cursor.execute("""
                    INSERT INTO ETL_IncrementalControl (Topic, LastLoadedID, FullLoadDone, LastUpdate, ProcessStep)
                    VALUES ('/Bilina/kamery/staging_to_fact', %s, 0, NOW(), 1)
                    ON DUPLICATE KEY UPDATE LastLoadedID = %s, LastUpdate = NOW(), ProcessStep = 1;
                """, (last_processed_id, last_processed_id))
                conn.commit()
                
        status = "SUCCESS"
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ ETL dokončeno za {duration/60:.1f} min. Celkem vloženo: {total_inserted:,} řádků.")
        print(f"   Průměrná rychlost: {total_inserted/duration:,.0f} řádků/s")

    except KeyboardInterrupt:
        print("\n⛔️ ETL proces byl přerušen uživatelem (Ctrl+C)")
        error_message = "ETL přerušeno uživatelem"
        status = "FAILED"
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"❌ Chyba ETL procesu: {str(e)}")
        print(error_message)

    finally:
        try:
            if conn and cursor:
                end_time = datetime.now()
                log_message = error_message if status != "SUCCESS" else None
                rows_log = total_inserted if status == "SUCCESS" else None
                
                cursor.execute("""
                    INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime, EndTime, RowsInserted, ErrorMessage)
                    VALUES ('Load_FactCameraDetection', '/Bilina/kamery/staging_to_fact', %s, %s, %s, %s, %s);
                """, (status, start_time, end_time, rows_log, log_message))
                conn.commit()
        except Exception as log_err:
            print(f"⚠️ Chyba při logování: {log_err}", file=sys.stderr)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

if __name__ == "__main__":
    main()