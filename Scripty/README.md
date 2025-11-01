# 📚 Skripty pro datový sklad (Bakalářská práce)

Tento adresář obsahuje kompletní sadu skriptů a SQL souborů pro implementaci a správu datového skladu v rámci bakalářské práce. Řešení je navrženo pro multi-platformní prostředí a zahrnuje skripty pro **MS SQL Server**, **MariaDB**, **ClickHouse**, a **PostgreSQL/TimescaleDB**.

---

## 📁 Struktura adresáře

| Adresář/Soubor | Popis |
|:---|:---|
| **`Python/`** | Adresář s Python skripty pro ETL procesy, analýzu a další pomocné úkoly. |
| **`SQL/`** | Adresář s SQL skripty pro definici databázových schémat, údržbu a testování. |
| **`pgloader/`** | Konfigurační soubory pro nástroj `pgloader` pro migraci dat. |
| **`Start sluzeb/`** | Batch skripty pro snadné spouštění a zastavování databázových služeb ve Windows. |

---

## 🐍 Python skripty

Adresář `Python/` obsahuje následující podadresáře a skripty:

### `ETL/` - Skripty pro ETL procesy

| Skript | Zdroj | Cíl | Popis |
|:---|:---|:---|:---|
| `bilina_kamery_lake_to_staging.py` | MSSQL | MSSQL | Načítá data z datového jezera (landing zóny) do staging tabulky v datovém skladu pro data z kamer v Bílině. |
| `bilina_kamery_staging_to_fact.py` | MSSQL | MSSQL | Zpracovává data ze staging tabulky a plní dimenze a faktovou tabulku v datovém skladu. |
| `maria_bilina_kamery_lake_to_staging.py` | MariaDB | MariaDB | Ekvivalent ETL skriptu pro MariaDB; načítá data z data lake do stagingu. |
| `maria_bilina_kamery_staging_to_fact.py` | MariaDB | MariaDB | Ekvivalent ETL skriptu pro MariaDB; plní dimenze a fakty ze stagingu. |
| `maria_click_bilina_kamery_lake_to_staging.py` | MariaDB | ClickHouse | Načítá data z MariaDB data lake do staging tabulky v ClickHouse. |
| `maria_click_kamery_staging_to_fact.py` | ClickHouse | ClickHouse | Zpracovává data ve stagingu v ClickHouse a plní dimenze a fakty. |
| `pg_timescale_lake_to_staging.py` | PostgreSQL | TimescaleDB | Dynamický ETL skript, který načítá data z PostgreSQL data lake, provádí fuzzy clustering MQTT témat a dynamicky vytváří staging tabulky v TimescaleDB. |
| `pg_timescale_staging_to_fact.py` | TimescaleDB | TimescaleDB | Plní dimenze a fakty v TimescaleDB ze staging tabulek. |
| `analyze_json.py` | PostgreSQL | CSV | Nástroj pro analýzu JSON dat z MQTT zpráv. Seskupuje MQTT témata podle podobnosti struktury jejich JSON payloadů a exportuje výsledek do CSV. |

### `MariaDB to MSSQL conversion/`

| Skript | Popis |
|:---|:---|
| `SQLconvert.py` | Nástroj pro konverzi SQL dumpů z MariaDB/MySQL na syntaxi kompatibilní s MS SQL Server. |

### `Uvozovky/`

| Skript | Popis |
|:---|:---|
| `Uvozovky_do_topiku.py` | Pomocný skript pro práci s uvozovkami v textech. |

---

## 💾 SQL skripty

Adresář `SQL/` obsahuje skripty pro jednotlivé databázové platformy:

### `ClickHouse_DWH/`

| Soubor | Popis |
|:---|:---|
| `Dimensions.sql`, `Fact.sql` | DDL skripty pro vytvoření dimenzí a faktové tabulky. |
| `Stg_CameraCamea.sql` | DDL pro vytvoření staging tabulky. |
| `ETL_IncrementalControl.sql`, `ETL_RunLog.sql` | DDL pro vytvoření řídících a logovacích tabulek pro ETL. |
| `Dodelavky.sql` | Skript pro naplnění časové dimenze a další úpravy. |
| `Unknown.sql` | Vkládá `UNKNOWN` záznamy do dimenzí. |
| `TruncateAll.sql` | Vyprázdní všechny tabulky v datovém skladu. |

### `DWH/` (pro MS SQL Server)

| Soubor | Popis |
|:---|:---|
| `DWH_kamery_priprava.sql` | Kompletní DDL pro vytvoření schématu datového skladu. |
| `dbo.*.sql` | Jednotlivé DDL skripty pro vytvoření tabulek. |
| `DimIndex.sql`, `StgIndexes.sql`, `IX_*.sql` | Skripty pro vytvoření indexů. |
| `dimTime - naplneni.sql` | T-SQL skript pro naplnění časové dimenze. |
| `ResetDimenziAfaktu.sql` | Skript pro kompletní reset datového skladu. |
| `Structure.sql` | Skript pro získání informací o struktuře databáze. |
| `UnknownHodnoty.sql`, `UnknownTime.sql` | Skripty pro vložení `UNKNOWN` záznamů. |

### `Maria_DWH/` (pro MariaDB)

| Soubor | Popis |
|:---|:---|
| `Dim*.sql`, `Fact*.sql`, `Stg*.sql` | DDL skripty pro vytvoření tabulek. |
| `DimTime - naplneni.sql` | Stored procedura pro naplnění časové dimenze. |
| `ETL_*.sql` | DDL pro řídící a logovací tabulky. |
| `FactCameraDetection - indexes.sql`, `Stg_CameraCamea_indexes.sql` | Skripty pro vytvoření indexů. |
| `ResetDimenziaFaktu.sql` | Skript pro kompletní reset datového skladu. |
| `unknown.sql` | Skript pro vložení `UNKNOWN` záznamů. |

### `PostgreSQLTDB_DWH/` (pro PostgreSQL/TimescaleDB)

| Soubor | Popis |
|:---|:---|
| `Dimenze_fakta_indexy_hypertable.sql` | Kompletní DDL pro vytvoření schématu, včetně TimescaleDB hypertables. |
| `Truncate_all.sql` | Skript pro vymazání všech dat. |

---

## 🚀 Ostatní skripty

### `pgloader/`

| Soubor | Popis |
|:---|:---|
| `Dockerfile` | Dockerfile pro vytvoření image s nástrojem `pgloader`. |
| `mariadb_to_pg.load` | Konfigurační soubor pro `pgloader` pro migraci dat z MariaDB do PostgreSQL. |

### `Start sluzeb/`

| Soubor | Popis |
|:---|:---|
| `*.bat` | Batch skripty pro spouštění a zastavování databázových služeb (MariaDB, MSSQL) ve Windows. |