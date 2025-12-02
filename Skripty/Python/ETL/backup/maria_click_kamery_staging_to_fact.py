from clickhouse_driver import Client
from datetime import datetime
import time
import signal
import sys
import traceback

# =========================
# 🔧 KONFIGURACE
# =========================
BATCH_SIZE = 500000   # můžeš zvětšit, ClickHouse zvládá i miliony
stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    stop_requested = True
    print("\n🛑 Přerušení detekováno. Dokončuji aktuální dávku a ukončuji skript...")

signal.signal(signal.SIGINT, signal_handler)

# =========================
# 💾 PŘIPOJENÍ DO CLICKHOUSE
# =========================
def get_ch_client():
    return Client(
        host="localhost",
        port=9000,
        user="tahal",
        password="tohlejeroothesloprobakalarku2025",
        database="default"
    )

# =========================
# 📈 DIMENZE
# =========================
def insert_dimensions(ch, start_id, end_id):
    print(f"📊 Aktualizuji dimenze (LandingID {start_id}-{end_id})...")

    # 1️⃣ DimCity
    ch.execute("""
        INSERT INTO DimCity (CityName)
        SELECT DISTINCT City
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
          AND City != ''
          AND City NOT IN (SELECT CityName FROM DimCity)
    """, {"start": start_id, "end": end_id})

    # 2️⃣ DimSensor
    ch.execute("""
        INSERT INTO DimSensor (SensorCode)
        SELECT DISTINCT Sensor
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
          AND Sensor != ''
          AND Sensor NOT IN (SELECT SensorCode FROM DimSensor)
    """, {"start": start_id, "end": end_id})

    # 3️⃣ DimLP
    ch.execute("""
        INSERT INTO DimLP (LicensePlate)
        SELECT DISTINCT LP
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
          AND LP != ''
          AND LP NOT IN (SELECT LicensePlate FROM DimLP)
    """, {"start": start_id, "end": end_id})

    # 4️⃣ DimDetectionType
    ch.execute("""
        INSERT INTO DimDetectionType (DetectionType)
        SELECT DISTINCT DetectionType
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
          AND DetectionType != ''
          AND DetectionType NOT IN (SELECT DetectionType FROM DimDetectionType)
    """, {"start": start_id, "end": end_id})

    # 5️⃣ DimVehicleClass
    ch.execute("""
        INSERT INTO DimVehicleClass (VehicleClass)
        SELECT DISTINCT TRIM(CAST(multiIf(VehClass IS NULL, '', toString(VehClass)) AS String))
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
        AND TRIM(CAST(multiIf(VehClass IS NULL, '', toString(VehClass)) AS String)) != ''
        AND TRIM(CAST(multiIf(VehClass IS NULL, '', toString(VehClass)) AS String)) NOT IN (SELECT VehicleClass FROM DimVehicleClass)
    """, {"start": start_id, "end": end_id})




    # 6️⃣ DimCountry
    ch.execute("""
        INSERT INTO DimCountry (CountryCode)
        SELECT DISTINCT ILPC
        FROM Stg_CameraCamea
        WHERE LandingID BETWEEN %(start)s AND %(end)s
          AND ILPC != ''
          AND ILPC NOT IN (SELECT CountryCode FROM DimCountry)
    """, {"start": start_id, "end": end_id})

    print("✅ Dimenze aktualizovány.")

# =========================
# 💡 FAKTA
# =========================
def insert_facts(ch, start_id, end_id):
    print(f"📥 Vkládám fakta (LandingID {start_id}-{end_id})...")
    start_time = time.time()

    # hromadný INSERT přes JOIN na dimenze
    ch.execute("""
    INSERT INTO FactCameraDetection
    (TimeKey, SensorKey, DetectionTypeKey, LPKey, CountryKey, VehicleClassKey, CityKey, Velocity)
    SELECT
        toUnixTimestamp(OriginalTime) AS TimeKey,

        -- SENSOR
        multiIf(s.SensorKey = 0 OR s.SensorKey IS NULL, 4294967295, s.SensorKey) AS SensorKey,

        -- DETECTION TYPE
        multiIf(d.DetectionTypeKey = 0 OR d.DetectionTypeKey IS NULL, 4294967295, d.DetectionTypeKey) AS DetectionTypeKey,

        -- LP
        multiIf(l.LPKey = 0 OR l.LPKey IS NULL, 4294967295, l.LPKey) AS LPKey,

        -- COUNTRY
        multiIf(c.CountryKey = 0 OR c.CountryKey IS NULL, 4294967295, c.CountryKey) AS CountryKey,

        -- VEHICLE CLASS
        multiIf(v.VehicleClassKey = 0 OR v.VehicleClassKey IS NULL, 4294967295, v.VehicleClassKey) AS VehicleClassKey,

        -- CITY
        multiIf(ci.CityKey = 0 OR ci.CityKey IS NULL, 4294967295, ci.CityKey) AS CityKey,

        toFloat64OrZero(toString(stg.Velocity)) AS Velocity
    FROM Stg_CameraCamea AS stg

    LEFT JOIN DimSensor AS s 
    ON TRIM(toString(stg.Sensor)) != '' AND toString(stg.Sensor) = s.SensorCode

    LEFT JOIN DimDetectionType AS d 
    ON TRIM(toString(stg.DetectionType)) != '' AND toString(stg.DetectionType) = d.DetectionType

    LEFT JOIN DimLP AS l 
    ON TRIM(toString(stg.LP)) != '' AND toString(stg.LP) = l.LicensePlate

    LEFT JOIN DimCountry AS c 
    ON TRIM(toString(stg.ILPC)) != '' AND toString(stg.ILPC) = c.CountryCode

    LEFT JOIN DimVehicleClass AS v 
    ON TRIM(toString(stg.VehClass)) != '' AND toString(stg.VehClass) = v.VehicleClass

    LEFT JOIN DimCity AS ci 
    ON TRIM(toString(stg.City)) != '' AND toString(stg.City) = ci.CityName

    WHERE LandingID BETWEEN %(start)s AND %(end)s
    """, {"start": start_id, "end": end_id})

    dur = round(time.time() - start_time, 2)
    print(f"✅ Fakta vložena za {dur}s.")
    return 1

# =========================
# 🔁 DÁVKOVÉ ZPRACOVÁNÍ
# =========================
def process_batch(ch, start_id, end_id):
    try:
        insert_dimensions(ch, start_id, end_id)
        insert_facts(ch, start_id, end_id)
        print(f"🎯 Dávka {start_id}-{end_id} dokončena.\n")
    except Exception as e:
        print(f"❌ Chyba při dávce {start_id}-{end_id}: {str(e)}")
        print(traceback.format_exc())

# =========================
# 🚀 MAIN
# =========================
def main():
    ch = get_ch_client()
    start_time = datetime.now()

    max_id = ch.execute("SELECT max(LandingID) FROM Stg_CameraCamea")[0][0] or 0
    min_id = ch.execute("SELECT min(LandingID) FROM Stg_CameraCamea")[0][0] or 0

    print(f"\n🚀 Zpracování záznamů (LandingID {min_id}–{max_id})...\n")

    for start_id in range(min_id, max_id + 1, BATCH_SIZE):
        if stop_requested:
            print("⏹ Přerušení uživatelem potvrzeno. ETL se ukončuje...")
            break
        end_id = min(start_id + BATCH_SIZE - 1, max_id)
        process_batch(ch, start_id, end_id)

    end_time = datetime.now()
    print(f"\n✅ ETL dokončeno v {end_time - start_time}.\n")

if __name__ == "__main__":
    main()
