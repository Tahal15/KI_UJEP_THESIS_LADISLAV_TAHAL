#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import signal
import subprocess
import json
import logging
import re
import gc
from collections import deque
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

# ===================== KONFIG =====================

LANDING_CONN = {
    "host": "localhost",
    "port": 5433,
    "dbname": "datove_jezero",
    "user": "tahal",
    "password": "tohlejeroothesloprobakalarku2025",
    "application_name": "etl_dynamic_seq_landing",
}

STAGING_CONN = {
    "host": "localhost",
    "port": 5434,
    "dbname": "datovy_sklad",
    "user": "tahal",
    "password": "tohlejeroothesloprobakalarku2025",
    "application_name": "etl_dynamic_seq_staging",
}

TARGET_SCHEMA = "mttgueries"
LOG_FILE = "etl_dynamic_sequential.log"

FETCH_SIZE = 5000
BATCH_SIZE = 5000

# UPOZORNĚNÍ: payload už se NEUKLÁDÁ, ukládají se jen rozflattenované sloupce.
# COPY režim je volitelný (výchozí vypnuto kvůli jednoduchosti).
USE_COPY = False

# WSL vypínání po Ctrl+C:
# - Pokud necháš prázdné, skript automaticky vypne všechny běžící WSL distribuce
#   kromě "docker-desktop" a "docker-desktop-data".
# - Pokud sem uvedeš seznam, vypne jen ty konkrétní názvy (docker nezasáhne).
WSL_SHUTDOWN_DISTROS = []  # např. ["Ubuntu-22.04"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, "a", "utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

_shutdown_requested = False
_open_resources = []

def _list_running_wsl_distros():
    """Vrátí seznam běžících WSL distr. (kromě docker-desktop*)."""
    try:
        out = subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True, check=False)
        lines = (out.stdout or "").splitlines()
        distros = []
        for ln in lines[1:]:
            # Očekávaný formát:  NAME              STATE           VERSION
            name = ln.split()[0] if ln.strip() else ""
            if not name:
                continue
            if name.lower().startswith("docker-desktop"):
                continue
            if "running" in ln.lower():
                distros.append(name)
        return distros
    except Exception:
        return []

def _shutdown_wsl_safely():
    """Ukončí jen ne-dockerové WSL distribuce, Docker nechá běžet."""
    if platform.system() != "Windows":
        return
    try:
        targets = WSL_SHUTDOWN_DISTROS[:] if WSL_SHUTDOWN_DISTROS else _list_running_wsl_distros()
        if not targets:
            log.info("WSL: není co vypínat (nebo jen Docker).")
            return
        for name in targets:
            if name.lower().startswith("docker-desktop"):
                continue
            subprocess.run(["wsl", "-t", name], check=False, capture_output=True)
            log.info(f"WSL: ukončena distribuce '{name}'.")
    except Exception as e:
        log.warning(f"WSL vypínání selhalo: {e}")

# ============== SIGINT / CLEANUP ==============

def _cleanup_and_exit(signum=None, frame=None):
    global _shutdown_requested
    if _shutdown_requested:
        return
    _shutdown_requested = True
    log.info("Zachycen SIGINT – provádím úklid…")

    for res in _open_resources:
        try:
            if hasattr(res, "close"):
                res.close()
        except Exception:
            pass
    _open_resources.clear()
    gc.collect()

    # Bezpečné WSL vypnutí (Docker zůstane běžet)
    _shutdown_wsl_safely()

    log.info("Úklid hotov. Končím.")
    os._exit(130)

signal.signal(signal.SIGINT, _cleanup_and_exit)
signal.signal(signal.SIGTERM, _cleanup_and_exit)

# ============== UTILITKY ==============

_RE_NON_ALNUM = re.compile(r"[^a-z0-9_]")
_RE_MULTI_UNDERS = re.compile(r"_+")

def try_utf8(x):
    if isinstance(x, bytes):
        for enc in ("utf-8", "cp1250", "latin-1"):
            try:
                return x.decode(enc)
            except Exception:
                continue
        return x.decode("utf-8", errors="ignore")
    if isinstance(x, str):
        return x
    return str(x)

def sanitize_column_name(name: str) -> str:
    name = name.strip().lower()
    name = _RE_NON_ALNUM.sub("_", name)
    name = _RE_MULTI_UNDERS.sub("_", name).strip("_")
    if not name or name[0].isdigit():
        name = "col_" + name
    return name

def flatten_json_iter(obj, prefix=""):
    out = {}
    stack = deque([(prefix, obj)])
    while stack:
        pref, val = stack.pop()
        if isinstance(val, str):
            s = val.strip()
            if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                try:
                    val = json.loads(s.replace("'", '"'))
                except Exception:
                    pass
        if isinstance(val, dict):
            for k, v in val.items():
                key = sanitize_column_name(pref + str(k))
                stack.append((key + "_", v))
        elif isinstance(val, list):
            for i, v in enumerate(val):
                stack.append((f"{pref}{i}_", v))
        else:
            clean_key = sanitize_column_name(pref[:-1]) if pref.endswith("_") else sanitize_column_name(pref)
            out[clean_key] = val
    return out

def infer_pg_type(v):
    if isinstance(v, bool): return "BOOLEAN"
    if isinstance(v, int): return "BIGINT"
    if isinstance(v, float): return "DOUBLE PRECISION"
    if isinstance(v, (dict, list)): return "JSONB"
    try:
        # Zkusit datum – pokud se povede, je to TIMESTAMPTZ
        datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return "TIMESTAMPTZ"
    except Exception:
        pass
    
    # Zkusit, zda je to číslo i ve stringu, abychom preferovali text
    # pro jakékoli nekonzistentní datové typy
    s = str(v).strip()
    if s and s.replace('.', '', 1).isdigit():
         # Pokud je to platné číslo (int nebo float), necháme ho jako DOUBLE PRECISION (nejobecnější číselný typ)
         return "DOUBLE PRECISION"
        
    return "TEXT" # Vše ostatní je TEXT

def safe_json(payload):
    txt = try_utf8(payload).strip()
    try:
        js = json.loads(txt)
    except Exception:
        if txt.startswith("{") and "'" in txt and '"' not in txt:
            try:
                js = json.loads(txt.replace("'", '"'))
            except Exception:
                return {"raw_value": txt}
        else:
            return {"raw_value": txt}
    if isinstance(js, list) and len(js) == 1 and isinstance(js[0], dict):
        js = js[0]
    stack = deque([js])
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            for k, vv in list(v.items()):
                if isinstance(vv, str):
                    s = vv.strip()
                    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                        try:
                            v[k] = json.loads(s.replace("'", '"'))
                        except Exception:
                            pass
                if isinstance(v.get(k), (dict, list)):
                    stack.append(v[k])
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], str):
                    s = v[i].strip()
                    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                        try:
                            v[i] = json.loads(s.replace("'", '"'))
                        except Exception:
                            pass
                if isinstance(v[i], (dict, list)):
                    stack.append(v[i])
    return js

def get_staging_col_types(cur, table, cols):
    """Získá datové typy z databáze pro dané sloupce (používá se pro validaci)."""
    if not cols:
        return {}
        
    # Musíme použít tuplu pro ANY a vyfiltrovat None, jinak psycopg2 selže
    col_tuple = tuple(c for c in cols if c not in ("stgid", "landingid", "originaltime", "topic", "loaddttm"))
    if not col_tuple:
        return {}
        
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema=%s AND table_name=%s 
        AND column_name IN %s;
    """, (TARGET_SCHEMA, table, col_tuple))
    
    return {r["column_name"]: r["data_type"].upper() for r in cur.fetchall()}
def ensure_table_and_columns(cur, table, sample):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TARGET_SCHEMA}.{table} (
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
            cur.execute(f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS "{col}" {t};')
            existing.add(col)
    return existing

def build_manual_clusters(_):
    manual_groups = {
        8: ["/Energo/DCUK/SML133/SML133-01/act", "/Energo/DCUK/SML133/SML133-01"],
        10: ["/Energo/DCUK/SML133/SML133-01/har", "/Energo/DCUK/SML133/SML133-01/osc"],
    }
    clusters = []
    orange = set(manual_groups.get(8, [])) | set(manual_groups.get(10, []))
    if orange:
        clusters.append({"group": "8_10", "topics": orange})
    for gid, tps in manual_groups.items():
        if gid in (8, 10):
            continue
        clusters.append({"group": str(gid), "topics": set(tps)})
    return clusters

# ============== ETL ==============

def process_cluster(cluster):
    gid = cluster["group"]
    topics = list(cluster["topics"])
    table = f"stg_manual_group_{gid}"
    rows_inserted = 0

    log.info(f"▶️ Start cluster {gid} ({len(topics)} topiců)")

    conn_l = conn_s = cur_l = cur_s = None
    try:
        conn_l = psycopg2.connect(**LANDING_CONN)
        conn_l.autocommit = False
        _open_resources.append(conn_l)

        with conn_l:
            cur_l = conn_l.cursor(
                name=f"stream_{gid}",
                cursor_factory=RealDictCursor,
                withhold=False
            )
            _open_resources.append(cur_l)
            cur_l.itersize = FETCH_SIZE
            cur_l.execute(
                """
                SELECT id, time, topic, payload
                FROM mttgueries.mqttentries
                WHERE topic = ANY(%s)
                ORDER BY id
                """,
                (topics,),
            )

            conn_s = psycopg2.connect(**STAGING_CONN)
            conn_s.autocommit = False
            _open_resources.append(conn_s)
            cur_s = conn_s.cursor()
            _open_resources.append(cur_s)

            first_batch = cur_l.fetchmany(FETCH_SIZE)
            if not first_batch:
                log.warning(f"Cluster {gid} je prázdný.")
                return (gid, 0, "EMPTY", "")

            js0 = safe_json(first_batch[0]["payload"])
            flat_sample = flatten_json_iter(js0)
            existing_cols = ensure_table_and_columns(cur_s, table, flat_sample)
            conn_s.commit()
            
            # Získání datových typů z databáze
            col_types = get_staging_col_types(cur_s, table, existing_cols)

            dyn_cols = sorted(existing_cols - {"stgid", "landingid", "originaltime", "topic", "loaddttm"})
            base_cols = ["landingid", "originaltime", "topic", "loaddttm"]
            insert_cols = base_cols + dyn_cols
            colnames_sql = ", ".join(f'"{c}"' for c in insert_cols)

            buffer = []

            def flush_buffer():
                nonlocal buffer, rows_inserted
                if not buffer:
                    return
                if USE_COPY:
                    import io, csv
                    sio = io.StringIO()
                    csv.writer(sio, lineterminator="\n").writerows(buffer)
                    sio.seek(0)
                    cur_s.copy_expert(
                        f'COPY {TARGET_SCHEMA}.{table} ({colnames_sql}) FROM STDIN WITH (FORMAT CSV)',
                        sio
                    )
                else:
                    execute_values(
                        cur_s,
                        f'INSERT INTO {TARGET_SCHEMA}.{table} ({colnames_sql}) VALUES %s',
                        buffer,
                        page_size=1000
                    )
                rows_inserted += len(buffer)
                buffer.clear()
                gc.collect()

            batch_no = 1
            current_batch = first_batch
            now_utc = lambda: datetime.now(timezone.utc)

            while current_batch:
                for r in current_batch:
                    if _shutdown_requested:
                        raise KeyboardInterrupt

                    js = safe_json(r["payload"])
                    flat = flatten_json_iter(js)

                    new_cols = set(flat.keys()) - set(dyn_cols) - {"stgid","landingid","originaltime","topic","loaddttm"}
                    if new_cols:
                        flush_buffer()
                        ensure_table_and_columns(cur_s, table, {c: flat[c] for c in new_cols})
                        conn_s.commit()
                        
                        # Aktualizace seznamu dynamických sloupců a jejich typů po ALTER TABLE
                        existing_cols = {row[0] for row in cur_s.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_schema=%s AND table_name=%s;
                        """, (TARGET_SCHEMA, table)).fetchall()}
                        col_types = get_staging_col_types(cur_s, table, existing_cols)
                        dyn_cols = sorted(existing_cols - {"stgid","landingid","originaltime","topic","loaddttm"})
                        insert_cols = base_cols + dyn_cols
                        colnames_sql = ", ".join(f'"{c}"' for c in insert_cols)

                    row_vals = [
                        int(r["id"]),
                        datetime.fromisoformat(str(r["time"]).replace("Z", "+00:00")) if r["time"] else None,
                        str(r["topic"]) if r["topic"] is not None else None,
                        now_utc(),
                    ]
                    
                    # HLAVNÍ MÍSTO OPRAVY: Kontrola a konverze hodnot
                    for k in dyn_cols:
                        v = flat.get(k)
                        pg_type = col_types.get(k, 'TEXT') # Default je TEXT
                        
                        converted_v = v

                        if v is None:
                            # Prázdné hodnoty jsou vždy OK
                            converted_v = None
                        elif pg_type in ('BIGINT', 'INTEGER', 'DOUBLE PRECISION', 'NUMERIC'):
                            # Zkusit konvertovat na číslo, jinak vložit NULL
                            try:
                                # Pro PostgreSQL: Použijeme float pro obecnou konverzi čísel
                                converted_v = float(v) 
                            except (ValueError, TypeError):
                                # Zde zachytíme chybu jako "3f not retrieved"
                                # Místo chyby vložíme NULL
                                converted_v = None 
                                log.warning(f"Nekonzistentní hodnota (NULL): Cluster {gid}, sloupec {k}, hodnota '{v}' (očekáván {pg_type})")
                        elif isinstance(v, (dict, list)) and pg_type == 'JSONB':
                            converted_v = json.dumps(v, ensure_ascii=False)
                        elif isinstance(v, datetime) and pg_type == 'TIMESTAMPTZ':
                            converted_v = v.astimezone(timezone.utc).isoformat()
                        else:
                            # Ostatní (TEXT) nebo nekovertovatelné typy
                            converted_v = v if isinstance(v, (int, float, str, bool)) else str(v)
                            
                        row_vals.append(converted_v)

                    buffer.append(tuple(row_vals))
                    if len(buffer) >= BATCH_SIZE:
                        flush_buffer()

                flush_buffer()
                conn_s.commit()
                log.info(f"💾 Dávka {batch_no} hotová ({rows_inserted} řádků celkem)")
                batch_no += 1
                current_batch = cur_l.fetchmany(FETCH_SIZE)

            log.info(f"✅ Cluster {gid} hotový ({rows_inserted} řádků).")
            return (gid, rows_inserted, "SUCCESS", "")

    except KeyboardInterrupt:
        log.warning("Zpracování přerušeno uživatelem (Ctrl+C).")
        return (gid, rows_inserted, "INTERRUPTED", "")
    except Exception as e:
        log.exception(f"❌ Chyba v clusteru {gid}: {e}")
        try:
            if conn_s:
                conn_s.rollback()
        except Exception:
            pass
        return (gid, rows_inserted, "ERROR", str(e))
    finally:
        for obj in (cur_s, conn_s, cur_l, conn_l):
            if obj:
                try: obj.close()
                except Exception: pass
                try: _open_resources.remove(obj)
                except Exception: pass
        gc.collect()

def build_manual_clusters(_topic_keys_unused):
    manual_groups = {
       25: ["/ttndata/voda/eui-24e124713d167798", "/ttndata/voda/eui-24e124713d321242-vzdalenost-06", "/ttndata/voda/eui-24e124713d321639-vzdalenost-05", "/ttndata/voda/eui-24e124713d321868-vzdalenost-04", "/ttndata/voda/eui-24e124713d325844-vzdalenost-07", "/ttndata/voda/eui-3538363668386d0c-vzdalenost-010", "/ttndata/voda/eui-353836366b386c0c-vzdalenost-009", "/ttndata/voda/eui-353836366b387a0c-vzdalenost-008", "/ttndata/voda/eui-8cf95720000d4a63-vzdalenost-011", "/ttndata/voda/eui-8cf95720000d4b69-vzdalenost-012", "/voda/KA-01", "/voda/KA-18", "/voda/KA-19", "/voda/KA-20"],
        26: ["/udp1881/15102001", "/udp1881/15102002", "/udp1881/15102004", "/udp1881/15102005", "/udp1881/15102006", "/udp1881/15102007", "/udp1881/15102008", "/udp1881/15102010", "/udp1881/15102011", "/udp1881/15102012", "/udp1881/15102013", "/udp1881/15102014", "/udp1881/15102015", "/udp1881/15102016", "/udp1881/15102017", "/udp1881/15102019", "/udp1881/15102020", "/udp1881/15102022", "/udp1881/15102023", "/udp1881/15102024", "/udp1881/15102025", "/udp1881/15102026", "/udp1881/15102027", "/udp1881/15102028", "/udp1881/15102029", "/udp1881/15102030", "/udp1881/15102031", "/udp1881/15102032", "/udp1881/15102033", "/udp1881/15102034", "/udp1881/15102035", "/udp1881/15102036", "/udp1881/15102038", "/udp1881/15102039", "/udp1881/28072001", "/udp1881/28072002", "/udp1881/28072003", "/udp1881/28072004", "/udp1881/28072005", "/udp1881/28072006", "/udp1881/28072007", "/udp1881/28072008", "/udp1881/28072009", "/udp1881/28072010", "/udp1881/28072011", "/udp1881/28072012", "/udp1881/28072013", "/udp1881/28072014", "/udp1881/28072015", "/udp1881/28072017", "/udp1881/28072018", "/udp1881/28072019", "/udp1881/28072020", "/udp1881/28072021", "/udp1881/28072023", "/udp1881/28072024", "/udp1881/28072025", "/udp1881/28072026", "/udp1881/28072027", "/udp1881/28072028", "/udp1881/28072029", "/udp1881/28072031", "/udp1881/28072033", "/udp1881/28072034", "/udp1881/28072035", "/udp1881/28072036", "/udp1881/28072037", "/udp1881/28072038", "/udp1881/28072039", "/udp1881/28072040", "/udp1881/28072041", "/udp1881/28072042", "/udp1881/28072043", "/udp1881/28072044", "/udp1881/28072045", "/udp1881/28072046", "/udp1881/28072047", "/udp1881/28072048", "/udp1881/28072049", "/udp1881/28072050", "/udp1881/ffffffff", "/voda//udp1881/15102010", "/voda//udp1881/15102023", "/voda//udp1881/15102024", "/voda//udp1881/15102032", "/voda//udp1881/15102039", "/voda//udp1881/28072017", "/voda//udp1881/28072018", "/voda//udp1881/28072024", "/voda//udp1881/28072028", "/voda//udp1881/28072031", "/voda//udp1881/28072036", "/voda//udp1881/28072038", "/voda//udp1881/28072040", "/voda//udp1881/ffffffff", "/voda/BI-01", "/voda/BI-02", "/voda/BI-03", "/voda/BI-04", "/voda/CH-04", "/voda/DE-01", "/voda/DE-04", "/voda/DE-11", "/voda/DE-12", "/voda/DE-13", "/voda/DE-14", "/voda/DE-15", "/voda/KA-05", "/voda/KA-06", "/voda/KA-07", "/voda/KA-08", "/voda/KA-11", "/voda/KA-13", "/voda/KA-14", "/voda/KA-16", "/voda/KA-17", "/voda/LI-01", "/voda/LI-02", "/voda/LI-03", "/voda/LI-04", "/voda/LI-05", "/voda/LT-02", "/voda/LT-03", "/voda/LT-04", "/voda/LT-05", "/voda/LT-06", "/voda/LT-07", "/voda/LY-03", "/voda/MO-01", "/voda/MO-02", "/voda/PO-01", "/voda/PO-02", "/voda/PO-04", "/voda/PO-05", "/voda/PO-06", "/voda/RL-01", "/voda/RU-01", "/voda/RU-03", "/voda/RU-04", "/voda/RU-05", "/voda/RU-06", "/voda/RU-07", "/voda/RU-08", "/voda/RU-09", "/voda/RU-10", "/voda/TE-02", "/voda/TE-04", "/voda/TE-05", "/voda/TE-06", "/voda/TE-07", "/voda/TE-08", "/voda/TE-09", "/voda/TE-10", "/voda/TE-11", "/voda/TE-12", "/voda/TE-13", "/voda/UL-01", "/voda/UL-02", "/voda/UL-03", "/voda/UL-04", "/voda/UL-05", "/voda/UL-06", "/voda/UL-07", "/voda/UL-09", "/voda/UL-10", "/voda/UL-13", "/voda/UL-19", "/voda/UL-20", "/voda/UL-21"],
    }

    
    clusters = []
    orange = set(manual_groups.get(8, [])) | set(manual_groups.get(10, []))
    if orange:
        clusters.append({"group": "8_10", "topics": orange})
    for gid, tps in manual_groups.items():
        if gid in (8, 10):
            continue
        clusters.append({"group": str(gid), "topics": set(tps)})
    return clusters

def main():
    clusters = build_manual_clusters({})
    log.info(f"Celkem {len(clusters)} clusterů ke zpracování (sekvenčně).")
    for cluster in clusters:
        gid, rows, status, err = process_cluster(cluster)
        if status == "SUCCESS":
            log.info(f"✔️ {gid}: {rows} vloženo")
        elif status == "EMPTY":
            log.info(f"ℹ️ {gid}: žádná data")
        elif status == "INTERRUPTED":
            log.warning(f"⏹ {gid}: přerušeno uživatelem")
            break
        else:
            log.warning(f"⚠️ {gid}: {status} ({err})")
    log.info("🏁 ETL dokončeno pro všechny clustery.")

if __name__ == "__main__":
    main()
