#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic ETL for MQTT topics (PostgreSQL → PostgreSQL)
Author: Ladislav Tahal & ChatGPT
Version: 3.3 – fixed transaction rollback + faster + safer reads
"""

import psycopg2, json, gc, logging
from datetime import datetime
from psycopg2.extras import RealDictCursor, execute_batch

# ================== CONFIG =====================
LANDING_CONN = {
    "host": "localhost", "port": 5433, "dbname": "datove_jezero",
    "user": "tahal", "password": "tohlejeroothesloprobakalarku2025"
}
STAGING_CONN = {
    "host": "localhost", "port": 5434, "dbname": "datovy_sklad",
    "user": "tahal", "password": "tohlejeroothesloprobakalarku2025"
}
TARGET_SCHEMA = "mttgueries"
BATCH_SIZE = 2000
LOG_FILE = "etl_dynamic.log"
# ===============================================

# ---------- logging ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, "a", "utf-8"),
              logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# ---------- helpers ----------------------------
def normalize_topic_name(topic):
    topic = topic.strip("/").replace("-", "_").replace(":", "_").replace(".", "_")
    topic = topic.replace("/", "_").replace("__", "_")
    return f"stg_{topic.lower()}"

def get_logical_topic(topic, depth=3):
    parts = [p for p in topic.strip("/").split("/") if p]
    return "/" + "/".join(parts[:depth])

def flatten_json(y, prefix=""):
    out = {}
    def flatten(x, name=""):
        if isinstance(x, dict):
            for a in x:
                key = str(a).strip() if a else "unknown"
                flatten(x[a], f"{name}{key}_")
        elif isinstance(x, list):
            out[name[:-1] or "array"] = json.dumps(x)
        else:
            out[name[:-1] or "value"] = x
    flatten(y, prefix)
    clean = {}
    i = 1
    for k, v in out.items():
        c = k.strip("_").lower().replace("-", "_").replace(".", "_")
        if not c:
            c = f"col_{i}"; i += 1
        clean[c] = v
    return clean

def infer_pg_type(v):
    if isinstance(v, bool): return "BOOLEAN"
    if isinstance(v, int):  return "BIGINT"
    if isinstance(v, float):return "DOUBLE PRECISION"
    if isinstance(v, (dict, list)): return "JSONB"
    try:
        datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return "TIMESTAMPTZ"
    except Exception:
        return "TEXT"

def ensure_table_and_columns(cur, table, sample):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{table}(
            stgid BIGSERIAL PRIMARY KEY,
            landingid BIGINT,
            originaltime TIMESTAMPTZ,
            topic TEXT,
            loaddttm TIMESTAMPTZ DEFAULT now()
        );
    """)
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema=%s AND table_name=%s;
    """, (TARGET_SCHEMA, table))
    existing = {r[0] for r in cur.fetchall()}
    for col, val in sample.items():
        if col not in existing:
            t = infer_pg_type(val)
            cur.execute(
                f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS {col} {t};'
            )
            existing.add(col)
    return existing

def insert_batch(cur, table, batch):
    if not batch: return
    keys = sorted({k for _,_,_,flat in batch for k in flat.keys()})
    base_cols = ["landingid","originaltime","topic","loaddttm"]
    cols = base_cols + keys
    collist = ", ".join(cols)
    ph = "(" + ", ".join(["%s"] * len(cols)) + ")"
    sql = f"INSERT INTO {TARGET_SCHEMA}.{table} ({collist}) VALUES {ph}"
    rows=[]
    now = datetime.now()
    for lid,tm,tp,flat in batch:
        vals=[lid,tm,tp,now]+[flat.get(k) for k in keys]
        rows.append(vals)
    execute_batch(cur, sql, rows, page_size=500)
    batch.clear(); gc.collect()

# ---------- safe execute for landing -----------
def safe_execute_l(cur, sql, params=None):
    try:
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
    except Exception as e:
        # pokud landing připojení chytne chybu, rollbackni
        try:
            cur.connection.rollback()
        except Exception:
            pass
        raise e

# ---------- main ETL ---------------------------
def main():
    conn_l = psycopg2.connect(**LANDING_CONN)
    conn_s = psycopg2.connect(**STAGING_CONN)

    # landing = read-only, autocommit → žádná "aborted transaction"
    conn_l.set_session(readonly=True, autocommit=True)
    conn_s.set_session(autocommit=False)

    cur_l = conn_l.cursor(cursor_factory=RealDictCursor)
    cur_s = conn_s.cursor()

    # řídicí tabulky
    cur_s.execute(f"""
        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.etl_incremental_control(
            topic TEXT PRIMARY KEY,
            last_loaded_id BIGINT DEFAULT 0,
            last_update TIMESTAMPTZ
        );
    """)
    cur_s.execute(f"""
        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.etl_run_log(
            run_id BIGSERIAL PRIMARY KEY,
            topic TEXT,
            start_time TIMESTAMPTZ,
            end_time TIMESTAMPTZ,
            status TEXT,
            rows_inserted BIGINT,
            error_message TEXT
        );
    """)
    conn_s.commit()

    safe_execute_l(cur_l, "SELECT DISTINCT topic FROM mttgueries.mqttentries;")
    all_topics = [r["topic"] for r in cur_l.fetchall()]
    log.info(f"Loaded {len(all_topics)} MQTT topics")

    logical = {}
    for t in all_topics:
        base = get_logical_topic(t)
        logical.setdefault(base, []).append(t)
    log.info(f"Identified {len(logical)} logical groups")

    def ensure_new_columns(cur, table, flat_dict, existing_cols: set):
        new_cols = [c for c in flat_dict.keys() if c not in existing_cols]
        if not new_cols: return
        for c in new_cols:
            t = infer_pg_type(flat_dict[c])
            cur.execute(f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS {c} {t};')
            existing_cols.add(c)

    for lg_topic, topics in logical.items():
        start = datetime.now(); rows_ins = 0; status = "RUNNING"; err = ""
        tname = normalize_topic_name(lg_topic)
        log.info(f"→ {lg_topic} ({len(topics)} topics) → {tname}")

        try:
            cur_s.execute(
                f"SELECT last_loaded_id FROM {TARGET_SCHEMA}.etl_incremental_control WHERE topic=%s;",
                (lg_topic,)
            )
            r = cur_s.fetchone(); last_id = r[0] if r else 0

            safe_execute_l(cur_l, """
                SELECT payload FROM mttgueries.mqttentries
                WHERE topic=%s AND payload IS NOT NULL
                ORDER BY id DESC LIMIT 1;
            """, (topics[0],))
            s = cur_l.fetchone()
            if not s:
                log.warning(f"No payload for {lg_topic}")
                status = "SUCCESS"
                continue

            try:
                js = json.loads(s["payload"])
                if isinstance(js, list) and js: js = js[0]
            except Exception:
                js = {"value": s["payload"]}
            flat_sample = flatten_json(js)
            existing_cols = ensure_table_and_columns(cur_s, tname, flat_sample)
            conn_s.commit()

            for tp in topics:
                safe_execute_l(cur_l, """
                    SELECT id, time, topic, payload
                    FROM mttgueries.mqttentries
                    WHERE topic=%s AND id>%s ORDER BY id;
                """, (tp, last_id))

                while True:
                    rows = cur_l.fetchmany(BATCH_SIZE)
                    if not rows: break
                    batch=[]
                    for rrow in rows:
                        payload = rrow["payload"]
                        try: js = json.loads(payload)
                        except Exception: js = {"value": payload}

                        if isinstance(js, list):
                            for el in js:
                                flat = flatten_json(el)
                                ensure_new_columns(cur_s, tname, flat, existing_cols)
                                batch.append((rrow["id"], rrow["time"], rrow["topic"], flat))
                        else:
                            flat = flatten_json(js)
                            ensure_new_columns(cur_s, tname, flat, existing_cols)
                            batch.append((rrow["id"], rrow["time"], rrow["topic"], flat))

                    if batch:
                        n = len(batch)
                        insert_batch(cur_s, tname, batch)
                        conn_s.commit()
                        rows_ins += n
                        log.info(f"{tname}: +{n} (total {rows_ins})")

                        last_id = rows[-1]["id"]
                        cur_s.execute(f"""
                            INSERT INTO {TARGET_SCHEMA}.etl_incremental_control(topic,last_loaded_id,last_update)
                            VALUES(%s,%s,now())
                            ON CONFLICT(topic) DO UPDATE
                            SET last_loaded_id=EXCLUDED.last_loaded_id,
                                last_update=EXCLUDED.last_update;
                        """, (lg_topic, last_id))
                        conn_s.commit()

            status="SUCCESS"
            log.info(f"✅ {lg_topic} done | {rows_ins} rows")

        except Exception as e:
            # rollback obou připojení – jinak zůstane bloklá transakce
            try: conn_s.rollback()
            except Exception: pass
            try: conn_l.rollback()
            except Exception: pass
            status="ERROR"; err=str(e)
            log.exception(f"❌ Error {lg_topic}: {e}")

        finally:
            cur_s.execute(f"""
                INSERT INTO {TARGET_SCHEMA}.etl_run_log(topic,start_time,end_time,status,rows_inserted,error_message)
                VALUES(%s,%s,now(),%s,%s,%s);
            """,(lg_topic,start,status,rows_ins,err))
            conn_s.commit()

    cur_l.close(); cur_s.close()
    conn_l.close(); conn_s.close()
    log.info("🏁 ETL finished for all logical topics.")

if __name__=="__main__":
    main()
