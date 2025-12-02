import pymysql
import json
from datetime import datetime

BATCH_SIZE = 10000
JOB_NAME = "Load_CameraCamea"
TOPIC = "/Bilina/kamery/camea/%"

def parse_city_from_topic(topic_str: str) -> str:
    if not topic_str.startswith("/"):
        return "Unknown"
    parts = topic_str.strip("/").split("/")
    return parts[0] if len(parts) >= 3 else "Unknown"

# Připojení k MariaDB – landing zóna
conn_landing = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="tohlejeroothesloprobakalarku2025",
    database="mttgueries",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.Cursor
)
cursor_landing = conn_landing.cursor()

# Připojení k MariaDB – DWH
conn_dwh = pymysql.connect(
    host="localhost",
    port=3308,
    user="admin",
    password="C0lumnStore!",
    database="mttgueries",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.Cursor
)
cursor_dwh = conn_dwh.cursor()

# 1) Najdi poslední načtené ID
cursor_dwh.execute("SELECT LastLoadedID FROM ETL_IncrementalControl WHERE Topic = %s", (TOPIC,))
row = cursor_dwh.fetchone()
last_loaded_id = row[0] if row else 0
print(f"DEBUG: last_loaded_id = {last_loaded_id}")

# 2) Logování běhu ETL
cursor_dwh.execute("""
    INSERT INTO ETL_RunLog (JobName, Topic, Status, StartTime)
    VALUES (%s, %s, 'RUNNING', NOW())
""", (JOB_NAME, TOPIC))
conn_dwh.commit()
run_id = cursor_dwh.lastrowid
print(f"DEBUG: Nový ETL RunID = {run_id}")

try:
    # 3) Výběr dat z landing zóny
    select_sql = """
        SELECT id, time, topic, payload
        FROM mqttentries
        WHERE topic LIKE %s AND id > %s
        ORDER BY id
    """
    cursor_landing.execute(select_sql, (TOPIC, last_loaded_id))

    insert_sql = """
        INSERT INTO Stg_CameraCamea
        (
            LandingID, OriginalTime, City, DetectionType, Utc,
            LP, Sensor, VehClass, ILPC, Velocity, LoadDttm
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """

    rows_inserted = 0
    max_loaded_id = last_loaded_id
    batch = []

    while True:
        rows = cursor_landing.fetchmany(BATCH_SIZE)
        if not rows:
            break

        for r in rows:
            landing_id, original_time, topic, payload_str = r
            city = parse_city_from_topic(topic)

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
        batch.clear()

    # 4) Aktualizace ETL_IncrementalControl
    cursor_dwh.execute("""
        INSERT INTO ETL_IncrementalControl (Topic, LastLoadedID, LastUpdate, FullLoadDone)
        VALUES (%s, %s, NOW(), 1)
        ON DUPLICATE KEY UPDATE
            LastLoadedID = VALUES(LastLoadedID),
            LastUpdate = VALUES(LastUpdate),
            FullLoadDone = 1
    """, (TOPIC, max_loaded_id))
    conn_dwh.commit()

    # 5) Ukončení běhu jako SUCCESS
    cursor_dwh.execute("""
        UPDATE ETL_RunLog
        SET EndTime = NOW(), Status = 'SUCCESS', RowsInserted = %s
        WHERE RunID = %s
    """, (rows_inserted, run_id))
    conn_dwh.commit()

    print(f"✅ ETL dokončeno: {rows_inserted} řádků vloženo do Stg_CameraCamea.")

except Exception as e:
    error_message = str(e)
    print(f"❌ Chyba během ETL: {error_message}")
    cursor_dwh.execute("""
        UPDATE ETL_RunLog
        SET EndTime = NOW(), Status = 'ERROR', ErrorMessage = %s
        WHERE RunID = %s
    """, (error_message, run_id))
    conn_dwh.commit()

finally:
    cursor_landing.close()
    cursor_dwh.close()
    conn_landing.close()
    conn_dwh.close()
