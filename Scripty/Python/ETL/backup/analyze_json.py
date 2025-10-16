#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic fuzzy grouping of MQTT topics by JSON structure similarity.
---------------------------------------------------------------
Skript dynamicky seskupuje MQTT témata (topics) podle podobnosti
struktury jejich JSON payloadů. Používá Jaccardovu podobnost (poměr
společných a všech unikátních klíčů) a slučuje témata, která mají téměř
stejnou strukturu. Výsledek exportuje do CSV.
"""

import psycopg2, json, hashlib, csv, os
from psycopg2.extras import RealDictCursor
from datetime import datetime

# =========================================================
# 🔧 KONFIGURACE DATABÁZE
# =========================================================
DB_CONN = {
    "host": "localhost", "port": 5433,
    "dbname": "datove_jezero",
    "user": "tahal", "password": "tohlejeroothesloprobakalarku2025"
}

# Výstupní cesta k CSV souboru (uloží se vedle skriptu)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR, f"fuzzy_json_groups_{datetime.now():%Y-%m-%d}.csv"
)

# =========================================================
# 🔢 PARAMETRY
# =========================================================
# Prahová hodnota podobnosti (1 = 100% shoda → stejné struktury)
SIMILARITY_THRESHOLD = 1

# =========================================================
# 🧩 POMOCNÉ FUNKCE
# =========================================================

def looks_like_json(s: str) -> bool:
    """Zkontroluje, zda řetězec vypadá jako JSON (začíná { nebo [)."""
    return isinstance(s, str) and s.strip().startswith(("{", "[")) and s.strip().endswith(("}", "]"))


def flatten_json(y):
    """
    Rekurzivně rozbalí (flatten) vnořený JSON do množiny klíčů typu `path:type`.
    Příklad:
        {"a": {"b": 3}} → {"a:object_b:value"}
    Detekuje i JSON řetězce uvnitř hodnot (např. vnořené JSON uložené jako stringy).
    """
    out = {}

    # Pomocná funkce, která opraví apostrofy v JSONu (když jsou místo uvozovek)
    def fix_quotes(s):
        if isinstance(s, str) and s.strip().startswith("{") and "'" in s and '"' not in s:
            return s.replace("'", '"')
        return s

    # Hlavní rekurzivní funkce pro rozbalení JSONu
    def flatten(x, name=""):
        if isinstance(x, dict):
            # Pokud je hodnota objekt → rekurze do hloubky
            for k, v in x.items():
                flatten(v, f"{name}{k}:object_")
        elif isinstance(x, list):
            # Pokud je hodnota pole → vezmi první prvek jako reprezentanta
            if x:
                flatten(x[0], f"{name}array:")
        elif isinstance(x, str) and looks_like_json(x):
            # Pokud hodnota vypadá jako JSON string → zkus ji rozparsovat
            try:
                inner = json.loads(fix_quotes(x))
                flatten(inner, f"{name}subjson:object_")
            except Exception:
                # Když se nepodaří, ber to jako skalární hodnotu
                out[f"{name[:-1] or 'value'}:scalar"] = None
        else:
            # Konečný prvek (skalární hodnota)
            out[f"{name[:-1] or 'value'}:value"] = None

    # Spuštění rozbalení
    flatten(y)
    # Normalizace názvů klíčů (malá písmena, bez pomlček a teček)
    return set(k.lower().replace("-", "_").replace(".", "_") for k in out.keys())


def jaccard_similarity(a, b):
    """Vrátí Jaccardovu podobnost mezi dvěma množinami klíčů."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

# =========================================================
# 🚀 HLAVNÍ FUNKCE
# =========================================================

def main():
    print("🔗 Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONN)
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # --- KROK 1: Načti seznam unikátních MQTT témat ---
    print("📥 Loading topics...")
    cur.execute("SELECT DISTINCT topic FROM mttgueries.mqttentries;")
    topics = [r["topic"] for r in cur.fetchall()]
    print(f"→ Found {len(topics)} topics.")

    # --- KROK 2: Z každého tématu načti poslední JSON payload a rozbal strukturu ---
    topic_structures = {}   # topic -> set of flattened keys

    for i, topic in enumerate(topics, 1):
        cur.execute("""
            SELECT payload FROM mttgueries.mqttentries
            WHERE topic=%s AND payload IS NOT NULL
            ORDER BY id DESC LIMIT 1;
        """, (topic,))
        row = cur.fetchone()
        if not row:
            continue

        # Pokus o parsování JSONu
        try:
            js = json.loads(row["payload"])
            # Pokud je JSON pole → vezmeme první objekt
            if isinstance(js, list) and js:
                js = js[0]
            keys = flatten_json(js)
            if keys:
                topic_structures[topic] = keys
        except Exception:
            # Přeskoč nevalidní nebo neparsovatelné payloady
            continue

        # Průběžná hláška každých 200 záznamů
        if i % 200 == 0:
            print(f"  → Processed {i}/{len(topics)} topics...")

    conn.close()
    print("✅ JSON flattening complete.")
    print(f"→ {len(topic_structures)} valid JSON topics processed.")

    # --- KROK 3: Fuzzy clustering podle podobnosti struktur ---
    print("🤝 Performing fuzzy clustering...")
    groups = []              # seznam množin klíčů reprezentujících skupiny
    topic_to_group = {}      # mapování group_id → seznam témat

    for topic, keys in topic_structures.items():
        assigned = False
        # Porovnej s existujícími skupinami
        for gid, ref_keys in enumerate(groups):
            sim = jaccard_similarity(keys, ref_keys)
            if sim >= SIMILARITY_THRESHOLD:
                # Pokud je podobnost dostatečně vysoká → spoj
                groups[gid] |= keys
                topic_to_group.setdefault(gid, []).append(topic)
                assigned = True
                break
        # Pokud téma nepatří do žádné skupiny → vytvoř novou
        if not assigned:
            groups.append(set(keys))
            topic_to_group[len(groups) - 1] = [topic]

    print(f"✅ Fuzzy grouping complete → {len(groups)} groups formed.")

    # --- KROK 4: Ulož výsledek do CSV ---
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["GroupID", "NumTopics", "Topics", "Keys"])
        for gid, tlist in sorted(topic_to_group.items(), key=lambda x: len(x[1]), reverse=True):
            writer.writerow([
                gid,
                len(tlist),
                ", ".join(sorted(tlist)),
                ", ".join(sorted(groups[gid]))
            ])

    # --- KROK 5: Shrnutí ---
    print(f"\nSummary:")
    print(f"  • Fuzzy groups: {len(groups)}")
    print(f"  • Output file: {OUTPUT_FILE}")

# =========================================================
# 🧠 SPUŠTĚNÍ SKRIPTU
# =========================================================
if __name__ == "__main__":
    main()
