import pymysql
import json
from datetime import datetime
import time
from clickhouse_driver import Client

BATCH_SIZE = 5000  # zvětši, pokud máš dost RAM a rychlé sítě
JOB_NAME = "Load_CameraCamea"
TOPIC = "/Bilina/kamery/camea/%"

def parse_city_from_topic(topic_str: str) -> str:
    if not topic_str.startswith("/"):
        return "Unknown"
    parts = topic_str.strip("/").split("/")
    return parts[0] if len(parts) >= 3 else "Unknown"

def safe_str(val):
    return val if val is not None else ""

# Připojení k MariaDB – landing zóna (SSCursor = server-side cursor)
conn_landing = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="tohlejeroothesloprobakalarku2025",
    database="mttgueries",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.SSCursor
)
cursor_landing = conn_landing.cursor()

# Připojení k ClickHouse – DWH
ch_client = Client(
    host="localhost",
    port=9000,  # nativní protokol (rychlejší než HTTP)
    user="tahal",
    password="tohlejeroothesloprobakalarku2025",
    database="default"
)

# 1) Najdi poslední načtené ID
result = ch_client.execute(
    "SELECT LastLoadedID FROM ETL_IncrementalControl WHERE Topic = %(topic)s",
    {"topic": TOPIC}
)
last_loaded_id = result[0][0] if result else 0
print(f"DEBUG: last_loaded_id = {last_loaded_id}")

# 2) Logování běhu ETL
start_time = datetime.now()
run_id = int(datetime.timestamp(start_time))
ch_client.execute(
    "INSERT INTO ETL_RunLog (RunID, JobName, Topic, Status, StartTime, EndTime, RowsInserted, ErrorMessage) VALUES",
    [(run_id, JOB_NAME, TOPIC, "RUNNING", start_time, None, 0, "")]
)

try:
    # 3) Výběr dat z landing zóny
    select_sql = """
        SELECT id, time, topic, payload
        FROM mqttentries
        WHERE topic LIKE %s AND id > %s
        ORDER BY id
    """
    cursor_landing.execute(select_sql, (TOPIC, last_loaded_id))

    rows_inserted = 0
    max_loaded_id = last_loaded_id
    batch_number = 0
    total_start = time.time()

    while True:
        rows = cursor_landing.fetchmany(BATCH_SIZE)
        if not rows:
            break

        batch_number += 1
        batch = []
        for landing_id, original_time, topic, payload_str in rows:
            city = parse_city_from_topic(topic)

            try:
                payload_json = json.loads(payload_str)
            except json.JSONDecodeError:
                payload_json = {}

            detection_type = payload_json.get("detectionType", "")
            utc_str = payload_json.get("utc")
            lp = payload_json.get("lp", "")
            sensor = payload_json.get("sensor", "")
            veh_class = payload_json.get("vehClass")
            ilpc = payload_json.get("ilpc", "")
            velocity = payload_json.get("velocity")

            utc_dt = None
            if utc_str:
                try:
                    utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    pass

            veh_class = int(veh_class) if veh_class else None
            velocity = int(velocity) if velocity else None

            batch.append((
                landing_id,
                original_time,
                safe_str(city),
                safe_str(detection_type),
                utc_dt,
                safe_str(lp),
                safe_str(sensor),
                veh_class,
                safe_str(ilpc),
                velocity,
                datetime.now()
            ))
            rows_inserted += 1
            max_loaded_id = max(max_loaded_id, landing_id)

        # Insert dávky do ClickHouse
        batch_start = time.time()
        ch_client.execute(
            """
            INSERT INTO Stg_CameraCamea
            (LandingID, OriginalTime, City, DetectionType, Utc,
             LP, Sensor, VehClass, ILPC, Velocity, LoadDttm)
            VALUES
            """,
            batch
        )
        batch_time = time.time() - batch_start

        print(
            f"DEBUG: Batch {batch_number} vložen ({len(batch)} řádků) "
            f"| celkem {rows_inserted} "
            f"| {batch_time:.2f} s na batch "
            f"| {len(batch)/batch_time:.0f} řádků/s"
        )

    total_time = time.time() - total_start
    print(f"⏱️ Celkový čas: {total_time:.2f} s pro {rows_inserted} řádků "
          f"({rows_inserted/total_time:.0f} řádků/s)")

    # 4) Aktualizace ETL_IncrementalControl
    ch_client.execute(
        """
        INSERT INTO ETL_IncrementalControl (Topic, LastLoadedID, LastUpdate, FullLoadDone)
        VALUES
        """,
        [(TOPIC, max_loaded_id, datetime.now(), 1)]
    )

    # 5) Ukončení běhu jako SUCCESS
    ch_client.execute(
        """
        INSERT INTO ETL_RunLog (RunID, JobName, Topic, Status, StartTime, EndTime, RowsInserted, ErrorMessage)
        VALUES
        """,
        [(run_id, JOB_NAME, TOPIC, "SUCCESS", start_time, datetime.now(), rows_inserted, "")]
    )

    print(f"✅ ETL dokončeno: {rows_inserted} řádků vloženo do ClickHouse.")

except Exception as e:
    error_message = str(e)
    print(f"❌ Chyba během ETL: {error_message}")
    ch_client.execute(
        """
        INSERT INTO ETL_RunLog (RunID, JobName, Topic, Status, StartTime, EndTime, RowsInserted, ErrorMessage)
        VALUES
        """,
        [(run_id, JOB_NAME, TOPIC, "ERROR", start_time, datetime.now(), 0, error_message)]
    )

finally:
    cursor_landing.close()
    conn_landing.close()
