#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2, json, gc, logging, re, hashlib, itertools, collections
from datetime import datetime
from psycopg2.extras import RealDictCursor, execute_batch

LANDING_CONN = {
    "host": "localhost", "port": 5433, "dbname": "datove_jezero",
    "user": "tahal", "password": "tohlejeroothesloprobakalarku2025"
}
STAGING_CONN = {
    "host": "localhost", "port": 5434, "dbname": "datovy_sklad",
    "user": "tahal", "password": "tohlejeroothesloprobakalarku2025"
}
TARGET_SCHEMA = "mttgueries"
BATCH_SIZE = 200
WRITE_BATCH = 100
SIMILARITY_THRESHOLD = 0.5
LOG_FILE = "etl_dynamic_fuzzy_v3.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, "a", "utf-8"), logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# --- Pomocné funkce (beze změny) ---

def try_utf8(s):
    if isinstance(s, bytes):
        for enc in ("utf-8", "latin-1", "windows-1250"):
            try: return s.decode(enc)
            except Exception: continue
        return s.decode("utf-8", errors="ignore")
    elif isinstance(s, str):
        return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
    return str(s)

def flatten_json(y, prefix=""):
    out = {}
    def flatten(x, name=""):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], f"{name}{a}_")
        elif isinstance(x, list):
            if x and isinstance(x[0], (dict, list)):
                flatten(x[0], f"{name}array_")
            else:
                out[name[:-1] or "array"] = json.dumps(x, ensure_ascii=False)
        else:
            out[name[:-1] or "value"] = x
    flatten(y, prefix)
    clean = {}
    for k, v in out.items():
        c = k.strip("_").lower().replace("-", "_").replace(".", "_")
        if not c: c = "value"
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
    except Exception: return "TEXT"

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
            cur.execute(f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS {col} {t};')
            existing.add(col)
    return existing

def ensure_new_columns(cur, table, flat_dict, existing_cols):
    new_cols = [c for c in flat_dict.keys() if c not in existing_cols]
    if not new_cols: return existing_cols
    for c in new_cols:
        t = infer_pg_type(flat_dict[c])
        cur.execute(f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS {c} {t};')
        existing_cols.add(c)
    return existing_cols

def insert_batch(cur, table, batch, existing_cols):
    if not batch: return existing_cols
    all_keys = sorted({k for _,_,_,flat in batch for k in flat.keys()})
    for k in all_keys:
        if k not in existing_cols:
            cur.execute(f'ALTER TABLE {TARGET_SCHEMA}.{table} ADD COLUMN IF NOT EXISTS {k} TEXT;')
            existing_cols.add(k)
    base_cols = ["landingid","originaltime","topic","loaddttm"]
    cols = base_cols + all_keys
    sql = f"INSERT INTO {TARGET_SCHEMA}.{table} ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})"
    now = datetime.now()
    for i in range(0, len(batch), WRITE_BATCH):
        chunk = batch[i:i+WRITE_BATCH]
        rows=[]
        for lid,tm,tp,flat in chunk:
            vals=[lid,tm,tp,now]+[flat.get(k) for k in all_keys]
            rows.append(vals)
        execute_batch(cur, sql, rows, page_size=len(rows))
        del rows[:]; gc.collect()
    return existing_cols

def jaccard_similarity(a,b):
    a,b=set(a),set(b)
    return len(a & b)/len(a|b) if a or b else 0

def flatten_keys(payload):
    try:
        js=json.loads(payload)
        if isinstance(js,list) and js: js=js[0]
    except Exception: return []
    flat=flatten_json(js)
    return sorted(flat.keys())

def merge_clusters(topic_keys):
    topics=list(topic_keys.keys())
    pairs=[]
    for a,b in itertools.combinations(topics,2):
        sim=jaccard_similarity(topic_keys[a],topic_keys[b])
        if sim>=SIMILARITY_THRESHOLD:
            pairs.append((a,b))
    adjacency=collections.defaultdict(set)
    for a,b in pairs:
        adjacency[a].add(b); adjacency[b].add(a)

    visited=set(); clusters=[]
    for node in topics:
        if node in visited: continue
        cluster=set(); stack=[node]
        while stack:
            n=stack.pop()
            if n in visited: continue
            visited.add(n); cluster.add(n)
            for neigh in adjacency.get(n,[]):
                if neigh not in visited:
                    stack.append(neigh)
        clusters.append(cluster)
    return clusters

def derive_table_name(topics):
    parts="/".join(topics).lower().split("/")
    core=[]
    for p in parts:
        if re.search(r"(energo|dcuk|camea|ttndata|bilina|cez|decin|mve)",p):
            core.append(p)
    if not core: core=topics[0].strip("/").split("/")[:2]
    return "stg_"+"_".join(core[:3]).lower()

def safe_execute_l(cur,sql,params=None):
    try: cur.execute(sql,params)
    except Exception as e:
        try: cur.connection.rollback()
        except Exception: pass
        raise e

# --- ZMĚNĚNÁ FUNKCE PRO MANUÁLNÍ CLUSTERING ---
def manual_clusters(topic_keys):
    """
    Rozděluje topicy do clusterů na základě opravených manuálních pravidel:
    - ORANŽOVÁ (Group ID 8 a 10) se SLOUČÍ do jednoho clusteru.
    - Ostatní topicy (ŽLUTÁ) zůstanou jako SAMOSTATNÉ clustery.
    """
    
    # Regulární výraz pro identifikaci ORANŽOVÉ skupiny (Group ID 8 a 10)
    orange_topics_re = re.compile(
        r"/Energo/DCUK/SML133/SML133-01/(act|har)" # Seskupení Group ID 8 a 10
    )
    
    clusters = []
    
    # A. Zpracování ORANŽOVÉ skupiny
    orange_cluster = set()
    all_topics = set(topic_keys.keys())
    remaining_topics = set(topic_keys.keys())
    
    for topic in list(remaining_topics):
        if orange_topics_re.search(topic):
            orange_cluster.add(topic)
            
    if orange_cluster:
        clusters.append(orange_cluster)
        remaining_topics -= orange_cluster
    
    # B. Zpracování ZBYLÝCH (ŽLUTÝCH) skupin
    # Každý zbývající topic je samostatný cluster, aby byla zachována
    # jejich separace podle požadavku.
    
    for topic in remaining_topics:
        clusters.append({topic}) # Každý zbývající topic je vlastní cluster

    log.info(f"Manual clustering applied. Orange cluster size: {len(orange_cluster)}. Separated clusters: {len(remaining_topics)}")
    
    return clusters
# --- KONEC ZMĚNĚNÉ FUNKCE ---


def main():
    conn_l=psycopg2.connect(**LANDING_CONN)
    conn_s=psycopg2.connect(**STAGING_CONN)
    conn_l.set_session(readonly=True,autocommit=True)
    conn_s.set_session(autocommit=False)
    cur_l=conn_l.cursor(cursor_factory=RealDictCursor)
    cur_s=conn_s.cursor()

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
    """); conn_s.commit()

    safe_execute_l(cur_l,"SELECT DISTINCT topic FROM mttgueries.mqttentries;")
    topics=[r["topic"] for r in cur_l.fetchall()]
    log.info(f"Loaded {len(topics)} topics.")
    topic_keys={}
    for i,t in enumerate(topics,1):
        cur_l.execute("SELECT payload FROM mttgueries.mqttentries WHERE topic=%s AND payload IS NOT NULL ORDER BY id DESC LIMIT 1;",(t,))
        row=cur_l.fetchone()
        if not row: continue
        keys=flatten_keys(try_utf8(row["payload"]))
        if keys: topic_keys[t]=keys
        if i%200==0: log.info(f"Scanned {i}/{len(topics)} topics...")

    # ZMĚNA: Používá se manuální clustering namísto fuzzy
    clusters=manual_clusters(topic_keys) 
    log.info(f"Formed {len(clusters)} manual clusters.")

    for gid,cluster in enumerate(clusters):
        tps=list(cluster)
        table=derive_table_name(tps)
        
        # ZMĚNA: Podmínka pro identifikaci ORANŽOVÉ skupiny (Group ID 8 a 10)
        is_orange_group = any(re.search(r"/Energo/DCUK/SML133/SML133-01/", t) for t in tps)
        
        if is_orange_group:
             # Použít fixní název pro sloučenou oranžovou skupinu
             virt_topic = "manual/oranze/energo_sml133_slouceno"
             table = "stg_manual_oranze_energo"
        else:
            # Ponechat původní logiku pro žluté (separátní) skupiny
            virt_topic="/".join(tps[0].strip("/").split("/")[:2]) + f"/virt_group_{gid}"
            
        log.info(f"→ {virt_topic} ({len(tps)} topics) → {table}")
        start=datetime.now(); rows_ins=0; status="RUNNING"; err=""
        try:
            safe_execute_l(cur_l,"SELECT id,time,topic,payload FROM mttgueries.mqttentries WHERE topic = ANY(%s) ORDER BY id;",(tps,))
            rows=cur_l.fetchmany(BATCH_SIZE)
            
            # --- Zbytek logiky ETL pro cluster zůstává stejný ---
            
            if not rows: continue
            first_payload=try_utf8(rows[0]["payload"])
            try:
                js=json.loads(first_payload)
                if isinstance(js,list) and js: js=js[0]
            except Exception: js={"value":first_payload}
            flat_sample=flatten_json(js)
            existing_cols=ensure_table_and_columns(cur_s,table,flat_sample)
            conn_s.commit()
            batch=[]
            
            # Cyklus pro načítání všech dat v batchích
            while rows: 
                for rrow in rows:
                    payload=try_utf8(rrow["payload"])
                    try: js=json.loads(payload)
                    except Exception: js={"value":payload}
                    if isinstance(js,list):
                        for el in js:
                            flat=flatten_json(el)
                            existing_cols=ensure_new_columns(cur_s,table,flat,existing_cols)
                            batch.append((rrow["id"],rrow["time"],rrow["topic"],flat))
                    else:
                        flat=flatten_json(js)
                        existing_cols=ensure_new_columns(cur_s,table,flat,existing_cols)
                        batch.append((rrow["id"],rrow["time"],rrow["topic"],flat))
                    if len(batch)>=BATCH_SIZE:
                        existing_cols=insert_batch(cur_s,table,batch,existing_cols)
                        conn_s.commit()
                        rows_ins+=len(batch); batch.clear()
                
                rows=cur_l.fetchmany(BATCH_SIZE)
            
            if batch:
                existing_cols=insert_batch(cur_s,table,batch,existing_cols)
                conn_s.commit(); rows_ins+=len(batch)
            status="SUCCESS"
            log.info(f"✅ {virt_topic} done | {rows_ins} rows")
        except Exception as e:
            try: conn_s.rollback()
            except Exception: pass
            status="ERROR"; err=str(e)
            log.exception(f"❌ Error {virt_topic}: {e}")
        finally:
            cur_s.execute(f"""
                INSERT INTO {TARGET_SCHEMA}.etl_run_log(topic,start_time,end_time,status,rows_inserted,error_message)
                VALUES(%s,%s,now(),%s,%s,%s);
            """,(virt_topic,start,status,rows_ins,err))
            conn_s.commit()

    cur_l.close();cur_s.close();conn_l.close();conn_s.close()
    log.info("🏁 ETL finished for all manual and fuzzy virtual topics.")

if __name__=="__main__":
    main()