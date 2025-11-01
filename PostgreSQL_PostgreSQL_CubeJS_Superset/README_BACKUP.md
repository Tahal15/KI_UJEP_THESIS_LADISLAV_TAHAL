# ⚠️  NENÍ  HOTOVÉ: PostgreSQL DL -> PostgreSQL DW -> Cube.js -> Apache superset
 
Tento projekt implementuje kompletní analytický zásobník v Dockeru, zaměřený na **zpracování a dynamické parsování JSON dat** (typicky z IoT/MQTT zpráv). Využívá PostgreSQL/TimescaleDB pro efektivní ukládání časových řad a Cube.js/Superset pro vizualizaci.

**Důležité:** Toto je rozpracovaný (nehotový) projekt. Schéma datového skladu a ETL procesy vyžadují dokončení.

---

## 🚀 I. Architektura a Technologie

Řešení je postaveno na kontejnerizaci a je rozděleno na dvě databázové vrstvy pro čistý ETL proces:

1. **Data Lake (`pg-lake`):** PostgreSQL 16. Slouží k surovému uložení JSON dat.  
2. **Data Warehouse (`pg-warehouse`):** TimescaleDB (PostgreSQL s rozšířením pro časové řady). Zde probíhá ETL a dynamické parsování JSON do strukturovaných tabulek (staging).  
3. **Semantická vrstva (`cube`):** Cube.js. Připojuje se k DW a definuje měřítka a dimenze.  
4. **Vizualizace (`superset`):** Apache Superset. Vizualizuje data získaná přes Cube.js SQL API.

---

## 🐳 II. Spuštění Prostředí

Projekt se spouští pomocí souboru `docker-compose.yml`.

### 1. První spuštění

Spuštění všech kontejnerů na pozadí:

```bash
docker compose up -d
```

---

### 2. Důležité porty

| Služba | Kontejnerový port | Host port | Popis |
| :--- | :--- | :--- | :--- |
| **Data Lake (PG)** | `5432` | `5433` | Surová data |
| **Data Warehouse (TSDB)** | `5432` | `5434` | Strukturovaná data, Data Warehouse |
| **Cube.js API** | `4000` | `4000` | API pro vývoj modelů |
| **Cube.js SQL API** | `15432` | `15432` | Přístup k Cube modelům přes PostgreSQL protokol |
| **Superset** | `8088` | `8088` | Vizualizační rozhraní |

---

## 🛠️ III. Konfigurace a Inicializace

### 1. Inicializace databází

**pg-lake (5433):**  
- Automaticky se vytvoří databáze `datove_jezero`.  
- Data: Surové MQTT/IoT záznamy by měly být nahrány (např. pomocí SQL skriptů ve složce `./lake/init`).

**pg-warehouse (5434):**  
- Automaticky se vytvoří databáze `datovy_sklad`.  
- Schéma: Zde se nasazují DDL skripty pro staging tabulky, které jsou dynamicky vytvářeny ETL procesem.

---

### 2. Spuštění ETL pro dynamické parsování JSON

Jako middleware se používá **Python skript**, který zajišťuje dynamické vytváření schématu ve *Staging* zóně (TimescaleDB) na základě JSON payloadů ze surového jezera.

- **Skript:** `pg_timescale_lake_to_staging.py`  
  (musí běžet mimo Docker a připojovat se k portům `5433` a `5434`)  
- **Logika:**  
  Skript čte JSON data z `pg-lake:5433`, analyzuje strukturu klíčů a dynamicky vytváří/upravuje tabulky v `pg-warehouse:5434` (schéma *Stagingu*).

---

### 3. Přístup k analytickým nástrojům

**Superset**  
- Adresa: [http://localhost:8088](http://localhost:8088)  
- Přihlášení:  
  - Uživatel: `admin`  
  - Heslo: `tohlejeroothesloprobakalarku2025`  
- Konfigurace DB: Superset je již nakonfigurován pro připojení k **Cube.js SQL API** (`port 15432`).

**Cube.js**  
- API: [http://localhost:4000](http://localhost:4000)  
- Modely: Definovány ve složce `./cubejs`, odkazují na tabulky v kontejneru `pg-warehouse`.

---

