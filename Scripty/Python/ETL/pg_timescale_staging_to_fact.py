import psycopg2
from psycopg2.extras import execute_values # 💡 DŮLEŽITÝ NOVÝ IMPORT
import traceback
from datetime import datetime
import time
import signal
import sys
import os


# =========================================================
# 🔧 KONFIGURACE
# =========================================================

# Zvýšení dávky (pouze pokud máš dostatek RAM, jinak ponech 500000)
BATCH_SIZE = 500000 
stop_requested = False # globální proměnná pro bezpečné ukončení skriptu

# --- Nastavení připojení k PostgreSQL DWH (podle docker-compose3.yml) ---
DB_CONN = {
    "host": "localhost", # Změň na "pg-warehouse", pokud běžíš uvnitř Docker sítě
    "port": 5434,
    "database": "datovy_sklad",
    "user": "tahal",
    "password": "tohlejeroothesloprobakalarku2025"
}


# --- Handler pro přerušení Ctrl+C ---
def signal_handler(sig, frame):
    """Zachytí přerušení (SIGINT) a nastaví příznak pro bezpečné ukončení."""
    global stop_requested
    stop_requested = True
    print("\n🛑 Přerušení detekováno. Dokončuji aktuální dávku a ukončuji skript...")

# registrace signálu
signal.signal(signal.SIGINT, signal_handler)


# =========================================================
# 💾 PŘIPOJENÍ DO POSTGRESQL
# =========================================================
def get_pg_connection():
    """Vytvoří připojení k PostgreSQL databázi (s transakcemi)."""
    return psycopg2.connect(**DB_CONN)


# =========================================================
# 📈 DIMENZE (OPTIMALIZOVANÉ)
# =========================================================
def insert_dimensions(conn, start_id, end_id):
    """
    Optimalizovaně aktualizuje dimenzní tabulky. 
    Načte data JEDNOU, filtruje unikátní hodnoty v Pythonu 
    a provede hromadný INSERT přes execute_values.
    """
    print(f"📊 Optimalizovaně aktualizuji dimenze (landingid {start_id}-{end_id})...")
    cursor = conn.cursor()

    # 1. JEDNO NAČTENÍ DAT ze stagingu (pouze unikátní hodnoty z dané dávky)
    # Získáváme pouze sloupce pro dimenze.
    sql_select = """
    SELECT DISTINCT
        -- NOVÉ: Parsování města z topicu (druhá část)
        NULLIF(TRIM(SPLIT_PART(t.topic, '/', 2)), '') AS city,
        NULLIF(TRIM(t.sensor), '') AS sensor,
        NULLIF(TRIM(t.lp), '') AS lp,
        NULLIF(TRIM(t.detectiontype), '') AS detectiontype,
        NULLIF(TRIM(t.vehclass::text), '') AS vehclass,
        NULLIF(TRIM(t.ilpc), '') AS ilpc
    FROM mttgueries.bilina_decin_kamery t
    WHERE t.landingid BETWEEN %s AND %s
    """
    
    # Používáme execute_values pro hromadné inserty
    
    cursor.execute(sql_select, (start_id, end_id))
    rows = cursor.fetchall()
    
    # 2. Extrakce UNIKÁTNÍCH hodnot pro každou dimenzi v Pythonu
    
    cities = set()
    sensors = set()
    lps = set()
    detection_types = set()
    vehicle_classes = set()
    countries = set()
    
    # Rozdělení dat do sad pro každou dimenzi
    for row in rows:
        # Používáme sady (sety) pro automatickou deduplikaci v Pythonu, 
        # a vkládáme je jako tuple (hodnota,) kvůli execute_values formátu.
        if row[0]: cities.add((row[0],)) # city
        if row[1]: sensors.add((row[1],)) # sensor
        if row[2]: lps.add((row[2],)) # lp
        if row[3]: detection_types.add((row[3],)) # detectiontype
        if row[4]: vehicle_classes.add((row[4],)) # vehclass
        if row[5]: countries.add((row[5],)) # ilpc (country)

    # 3. Hromadný INSERT s ON CONFLICT DO NOTHING pro každou dimenzi (výrazně rychlejší)
    
    if cities:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimcity (cityname) VALUES %s ON CONFLICT (cityname) DO NOTHING", 
            list(cities)
        )
        
    if sensors:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimsensor (sensorcode) VALUES %s ON CONFLICT (sensorcode) DO NOTHING", 
            list(sensors)
        )
        
    if lps:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimlp (licenseplate) VALUES %s ON CONFLICT (licenseplate) DO NOTHING", 
            list(lps)
        )
        
    if detection_types:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimdetectiontype (detectiontype) VALUES %s ON CONFLICT (detectiontype) DO NOTHING", 
            list(detection_types)
        )
        
    if vehicle_classes:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimvehicleclass (vehicleclass) VALUES %s ON CONFLICT (vehicleclass) DO NOTHING", 
            list(vehicle_classes)
        )
        
    if countries:
        execute_values(
            cursor, 
            "INSERT INTO mttgueries.dimcountry (countrycode) VALUES %s ON CONFLICT (countrycode) DO NOTHING", 
            list(countries)
        )


    print("✅ Dimenze optimalizovaně aktualizovány.")
    cursor.close()


# =========================================================
# 💡 FAKTA
# =========================================================
def insert_facts(conn, start_id, end_id):
    """
    Vloží záznamy do faktové tabulky mttgueries.factcameradetection.
    Používá konvenci: všechna malá písmena, bez podtržítek.
    """
    print(f"📥 Vkládám fakta (landingid {start_id}-{end_id})...")
    start_time = time.time()

    cursor = conn.cursor()

    # Hromadný INSERT přes JOIN na dimenze
    cursor.execute("""
    INSERT INTO mttgueries.factcameradetection (
        detectiontime,
        timekey, sensorkey, detectiontypekey, lpkey, countrykey, vehicleclasskey, citykey, velocity
    )
    SELECT
        stg.originaltime, -- Sloupec ze stagingu
        COALESCE(t.timekey, -1),
        COALESCE(s.sensorkey, -1),
        COALESCE(d.detectiontypekey, -1),
        COALESCE(l.lpkey, -1),
        COALESCE(c.countrykey, -1),
        COALESCE(v.vehicleclasskey, -1),
        COALESCE(ci.citykey, -1),
        stg.velocity::real AS velocity -- Sloupec ze stagingu
    FROM mttgueries.bilina_decin_kamery AS stg

    -- JOIN na dimtime: EXTRACT je obecně efektivnější než DATE_PART
    LEFT JOIN mttgueries.dimtime AS t
    ON stg.originaltime::DATE = t.fulldate 
    AND EXTRACT(HOUR FROM stg.originaltime) = t.hournum  -- 💡 Optimalizace
    AND EXTRACT(MINUTE FROM stg.originaltime) = t.minutenum -- 💡 Optimalizace

    -- Ostatní JOINy na dimenze (beze změn)
    LEFT JOIN mttgueries.dimsensor AS s
    ON NULLIF(TRIM(stg.sensor), '') = s.sensorcode

    LEFT JOIN mttgueries.dimdetectiontype AS d
    ON NULLIF(TRIM(stg.detectiontype), '') = d.detectiontype

    LEFT JOIN mttgueries.dimlp AS l
    ON NULLIF(TRIM(stg.lp), '') = l.licenseplate

    LEFT JOIN mttgueries.dimcountry AS c
    ON NULLIF(TRIM(stg.ilpc), '') = c.countrycode

    LEFT JOIN mttgueries.dimvehicleclass AS v
    ON NULLIF(TRIM(stg.vehclass::text), '') = v.vehicleclass

    -- JOIN na dimcity s parsováním topicu
    LEFT JOIN mttgueries.dimcity AS ci
    ON NULLIF(TRIM(SPLIT_PART(stg.topic, '/', 2)), '') = ci.cityname

    WHERE stg.landingid BETWEEN %s AND %s
    """, (start_id, end_id))

    inserted_count = cursor.rowcount
    dur = round(time.time() - start_time, 2)
    print(f"✅ Fakta vložena ({inserted_count} řádků) za {dur}s.")
    cursor.close()
    return inserted_count


# =========================================================
# 🔁 DÁVKOVÉ ZPRACOVÁNÍ
# =========================================================
def process_batch(start_id, end_id):
    """
    Zpracuje jednu dávku záznamů a commitne transakci.
    """
    conn = None
    try:
        conn = get_pg_connection()
        insert_dimensions(conn, start_id, end_id)
        insert_facts(conn, start_id, end_id)
        conn.commit() # COMMIT transakce pro PostgreSQL
        print(f"🎯 Dávka {start_id}-{end_id} dokončena a potvrzena.\n")
        return 1
    except Exception as e:
        if conn:
            conn.rollback() # ROLLBACK při chybě
        print(f"❌ Chyba při dávce {start_id}-{end_id}: {str(e)}")
        print(traceback.format_exc())
        return 0
    finally:
        if conn:
            conn.close()


# =========================================================
# 🚀 MAIN
# =========================================================
def main():
    """Hlavní řídicí funkce ETL procesu."""
    conn = None
    total_start_time = time.time() # Měříme čas od začátku
    
    try:
        # Získání MIN/MAX ID ze stagingu
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Důležité: Získáváme celkový počet řádků (použitelné pro statistiku)
        cursor.execute("SELECT COALESCE(max(landingid), 0), COALESCE(min(landingid), 0), COUNT(landingid) FROM mttgueries.bilina_decin_kamery")
        max_id, min_id, total_rows = cursor.fetchone()
        
        # Ošetření případu, kdy je tabulka prázdná
        if max_id is None:
            max_id = 0
        if min_id is None:
            min_id = 0

        cursor.close()
        # Připojení zavíráme dříve, aby se mohlo použít pro každou dávku
        conn.close() 
        
    except Exception as e:
        print(f"❌ Chyba při získávání rozsahu ID: {str(e)}")
        sys.exit(1) # Ukončení při chybě připojení

    
    # --- PŘIDANÉ SLEDOVÁNÍ POSTUPU ---
    
    if min_id == 0 or max_id < min_id:
        print("\nℹ️ Staging tabulka je prázdná nebo rozsahy ID jsou neplatné. Nic ke zpracování.")
        return

    # Celkový počet dávek
    total_processing_range = max_id - min_id + 1
    total_batches = (total_processing_range + BATCH_SIZE - 1) // BATCH_SIZE
    
    batches_processed = 0
    total_rows_processed = 0
    
    print(f"\n🚀 Zpracování záznamů (landingid {min_id}–{max_id}).")
    print(f"📦 Celkem dávek k provedení: **{total_batches}** (Velikost dávky: {BATCH_SIZE}).\n")

    # Zpracování po dávkách
    for start_id in range(min_id, max_id + 1, BATCH_SIZE):
        if stop_requested:
            print("⏹ Přerušení uživatelem potvrzeno. ETL se ukončuje...")
            break
        
        # Výpočet konce dávky
        end_id = min(start_id + BATCH_SIZE - 1, max_id)
        
        # Zpracování
        # batch_start_time = time.time() # Nyní měříme jen celkový čas
        
        # Zpracuje dávku a vrátí 1 při úspěchu
        success = process_batch(start_id, end_id) 
        
        # Aktualizace metrik
        if success:
            batches_processed += 1
            # Realistický počet zpracovaných řádků (přibližně velikost dávky, poslední menší)
            current_batch_rows = min(BATCH_SIZE, max_id - start_id + 1)
            total_rows_processed += current_batch_rows
            
            # --- ZOBRAZENÍ STAVU ---
            
            elapsed_time = time.time() - total_start_time
            # Ošetření dělení nulou
            avg_time_per_batch = elapsed_time / batches_processed if batches_processed > 0 else 0
            
            # Odhad zbývajícího času
            batches_remaining = total_batches - batches_processed
            estimated_remaining_time = avg_time_per_batch * batches_remaining
            
            # Formátování výstupu
            time_str = time.strftime("%H:%M:%S", time.gmtime(estimated_remaining_time))
            progress_percent = (batches_processed / total_batches) * 100
            
            print(f"✨ **POSTUP:** Dávka {batches_processed}/{total_batches} ({progress_percent:.1f}%) | "
                      f"Odhad zbývajícího času: **{time_str}** | "
                      f"Prům. čas na dávku: {avg_time_per_batch:.2f}s")
            print("--------------------------------------------------\n")


    # Závěrečný souhrn
    total_elapsed_time = time.time() - total_start_time
    total_rows_in_range = max_id - min_id + 1
    
    # Rychlost v řádcích za sekundu
    if total_elapsed_time > 0 and total_rows_processed > 0:
        rows_per_second = total_rows_processed / total_elapsed_time
        speed_summary = f"({rows_per_second:,.0f} řádků/s)"
    else:
        speed_summary = ""

    # Převedení celkové doby na čitelný formát
    end_time_readable = str(datetime.now() - datetime.fromtimestamp(total_start_time)).split('.')[0]
    
    print(f"\n✅ **ETL DOKONČENO** v **{end_time_readable}** {speed_summary}.")
    print(f"Zpracováno celkem {total_rows_processed:,} řádků.")


# =========================================================
# ▶️ SPUŠTĚNÍ
# =========================================================
if __name__ == "__main__":
    main()