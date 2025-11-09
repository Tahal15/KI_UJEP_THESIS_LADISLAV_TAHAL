import pyodbc
import json
from datetime import datetime

BATCH_SIZE = 10000  

def parse_city_from_topic(topic_str: str) -> str:
    """ Extrahuje město z topicu. """
    if not topic_str.startswith("/"):
        return "Unknown"
    parts = topic_str.strip("/").split("/")
    return parts[0] if len(parts) >= 3 else "Unknown"

# Připojení k databázím
conn_landing = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=TAHAL\\DATA_LAKE;"
    "Database=mqttentries;"
    "UID=sa;"
    "PWD=HesloProBakalarku2025*;"
)
cursor_landing = conn_landing.cursor()

conn_dwh = pyodbc.connect(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=TAHAL\\DATA_WAREHOUSE;"
    "Database=DWH;"
    "UID=sa;"
    "PWD=HesloProBakalarku2025*;"
)
cursor_dwh = conn_dwh.cursor()

JOB_NAME = "Load_CameraCamea"
TOPIC = "/Bilina/kamery/camea/%"

# 1) Najít poslední načtené ID pro daný topic
cursor_dwh.execute("SELECT LastLoadedID FROM ETL_IncrementalControl WHERE Topic = ?", (TOPIC,))
row = cursor_dwh.fetchone()
last_loaded_id = row[0] if row else 0
print(f"DEBUG: last_loaded_id = {last_loaded_id}")

# 2) Vložit nový běh ETL do logovací tabulky a získat RunID pomocí OUTPUT
cursor_dwh.execute("""
    INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime)
    OUTPUT inserted.RunID
    VALUES (?, ?, 'RUNNING', SYSDATETIME());
""", (JOB_NAME, TOPIC))
run_id_row = cursor_dwh.fetchone()
run_id = run_id_row[0] if run_id_row else None
conn_dwh.commit()

print(f"DEBUG: Nový ETL RunID = {run_id}")

try:
    # 3) Výběr dat z landing zóny po dávkách
    select_sql = """
        SELECT id, [time], [topic], [payload]
        FROM mqttentries.dbo.mqttentries
        WHERE topic LIKE ? AND id > ?
        ORDER BY id
    """
    cursor_landing.execute(select_sql, (TOPIC, last_loaded_id))

    insert_sql = """
    INSERT INTO [Stg].[CameraCamea]
    (
        LandingID, OriginalTime, City, DetectionType, Utc,
        LP, Sensor, VehClass, ILPC, Velocity, LoadDttm
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
    """

    rows_inserted = 0
    max_loaded_id = last_loaded_id
    batch = []

    while True:
        rows = cursor_landing.fetchmany(BATCH_SIZE)
        if not rows:
            break  # Konec dat

        for r in rows:
            landing_id, original_time, topic, payload_str = r
            city = parse_city_from_topic(topic)

            # JSON parsing
            try:
                payload_json = json.loads(payload_str)
            except json.JSONDecodeError:
                payload_json = {}

            detection_type = payload_json.get("detectionType")
            utc_str = payload_json.get("utc")
            lp = payload_json.get("lp")
            sensor = payload_json.get("sensor")
            veh_class = payload_json.get("vehClass")
            ilpc = payload_json.get("ilpc")
            velocity = payload_json.get("velocity")

            # Převody formátů
            utc_dt = None
            if utc_str:
                try:
                    utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    pass

            veh_class = int(veh_class) if isinstance(veh_class, str) else veh_class
            velocity = int(velocity) if isinstance(velocity, str) else velocity

            batch.append((landing_id, original_time, city, detection_type, utc_dt,
                          lp, sensor, veh_class, ilpc, velocity))
            rows_inserted += 1
            max_loaded_id = max(max_loaded_id, landing_id)

        cursor_dwh.executemany(insert_sql, batch)
        conn_dwh.commit()
        batch.clear()  # Uvolnění paměti

    # 4) Aktualizace ETL_IncrementalControl
    cursor_dwh.execute("""
        MERGE INTO ETL_IncrementalControl AS Target
        USING (SELECT ? AS Topic, ? AS LastLoadedID, SYSDATETIME() AS LastUpdate, 1 AS FullLoadDone) AS Source
        ON Target.Topic = Source.Topic
        WHEN MATCHED AND Target.LastLoadedID < Source.LastLoadedID THEN
            UPDATE SET Target.LastLoadedID = Source.LastLoadedID, Target.LastUpdate = Source.LastUpdate, Target.FullLoadDone = 1
        WHEN NOT MATCHED THEN
            INSERT (Topic, LastLoadedID, LastUpdate, FullLoadDone)
            VALUES (Source.Topic, Source.LastLoadedID, Source.LastUpdate, Source.FullLoadDone);
    """, (TOPIC, max_loaded_id))
    conn_dwh.commit()

    # 5) Aktualizace ETL_RunLog na 'SUCCESS'
    if run_id is not None:
        cursor_dwh.execute("""
            UPDATE ETL_RunLog
            SET EndTime = SYSDATETIME(), Status = 'SUCCESS', RowsInserted = ?
            WHERE RunID = ?
        """, (rows_inserted, run_id))
        conn_dwh.commit()

        # Kontrola, že se log skutečně změnil
        cursor_dwh.execute("SELECT Status, RowsInserted FROM ETL_RunLog WHERE RunID = ?", (run_id,))
        debug_log = cursor_dwh.fetchone()
        print("DEBUG: Stav logu po úspěšném dokončení:", debug_log)

    print(f"✅ ETL dokončeno: {rows_inserted} řádků vloženo do Stg.CameraCamea.")

except Exception as e:
    # Při chybě nastavíme ERROR stav
    error_message = str(e)
    if run_id is not None:
        cursor_dwh.execute("""
            UPDATE ETL_RunLog
            SET EndTime = SYSDATETIME(), Status = 'ERROR', ErrorMessage = ?
            WHERE RunID = ?
        """, (error_message, run_id))
        conn_dwh.commit()
    print(f"❌ Chyba během ETL: {error_message}")

finally:
    cursor_landing.close()
    cursor_dwh.close()
    conn_landing.close()
    conn_dwh.close()
