# 📚 Bakalářská práce: Skripty pro datový sklad (Multi-platformní)

Tento archiv obsahuje **kompletní sadu skriptů a SQL souborů** pro implementaci datového skladu (Data Warehouse) pro bakalářskou práci. Řešení je navrženo pro **multi-platformní prostředí**, primárně využívající **ClickHouse** (analytika), **PostgreSQL/TimescaleDB** (IoT data/ETL) a **MySQL/MariaDB / MS SQL Server** (produkční DW prostředí).

---

## 🚀 ETL a Konverzní Nástroje (Python & Batch)

| Soubor | Typ | Popis | Technologie |
| :--- | :--- | :--- | :--- |
| `pg_timescale_lake_to_staging.py` | Python skript | **Dynamický ETL pro Timescale/PostgreSQL.** Načítá data z Landing Zone, provádí **fuzzy clustering MQTT témat** (Jaccardova podobnost) a dynamicky vytváří Staging tabulky. | PostgreSQL, TimescaleDB, Python, JSON |
| `maria_click_kamery_staging_to_fact.py` | Python skript | **Hlavní ETL proces pro Data Mart (ClickHouse).** Dávkově načítá data z mezitabulky (`Stg_CameraCamea`) do dimenzí a faktové tabulky. Zajišťuje **Surrogate Keys**. | ClickHouse, Python |
| `analyze_json.py` | Python skript | **Nástroj pro analýzu JSON dat z MQTT zpráv.** Seskupuje MQTT témata podle podobnosti struktury jejich JSON payloadů. Navrženo pro **PostgreSQL**. | PostgreSQL, Python, JSON |
| `SQLconvert.py` | Python skript | **Nástroj pro konverzi SQL dumpů.** Převede SQL dump z **MariaDB/MySQL** na kompatibilní syntaxi pro **MS SQL Server**. | MariaDB/MySQL → MS SQL, Python |

---

## ⚙️ Nástroje pro Správu Prostředí (Windows Batch)

Tato sekce obsahuje skripty pro rychlé spouštění klíčových databázových služeb.

| Soubor | Platforma | Popis |
| :--- | :--- | :--- |
| `start_data_lake.bat` | MS SQL Server | Spouští služby **MS SQL Serveru** pro instanci **DATA\_LAKE** (včetně Agent, Integration Services a Launchpad). |
| `start_dw.bat` | MS SQL Server | Spouští služby **MS SQL Serveru** pro instanci **DATA\_WAREHOUSE** (včetně Agent a Analysis Services). |
| `maria_start_data_lake.bat` | MariaDB | Spouští službu **MariaDB** (primární instance) pro Data Lake. |
| `maria_start_dw.bat` | MariaDB | Spouští službu **MariaDB2** (sekundární instance) pro Data Warehouse. |

---

## 💾 Schéma MySQL / MariaDB (DW)

Tato sekce obsahuje definice schématu pro implementaci Hvězdice na platformě MySQL/MariaDB (motor InnoDB).

### 1. **DDL a Schéma**
| Soubor | Popis |
| :--- | :--- |
| `FactCameraDetection.sql` | **Definice Faktové tabulky** s `AUTO_INCREMENT` klíčem a **FOREIGN KEYs** na všechny dimenze. |
| `DimCity.sql`, `DimCountry.sql`, `DimDetectionType.sql`, `DimLP.sql`, `DimSensor.sql`, `DimVehicleClass.sql` | **DDL pro dimenzní tabulky** s `AUTO_INCREMENT` primárním klíčem a **UNIQUE KEY** na obchodních klíčích. |
| `DimTime.sql` | **DDL pro dimenzi Čas** s indexy pro rychlý lookup (`FullDate`, `HourNum`, `MinuteNum`). |
| `Stg_CameraCamea.sql` | **Definice Staging tabulky** pro data z IoT senzorů s `AUTO_INCREMENT` primárním klíčem. |
| `ETL_RunLog.sql` | **Logovací tabulka** pro monitorování stavu a výsledků ETL procesů. |
| `ETL_IncrementalControl.sql` | **Řídicí tabulka** pro sledování posledního zpracovaného ID (`LastLoadedID`) pro inkrementální načítání. |

### 2. **Indexy a Údržba**
| Soubor | Popis |
| :--- | :--- |
| `DimAutoIncrement.sql` | **Doplňkový skript** pro vynucení `AUTO_INCREMENT` u dimenzí. |
| `UniqueKeys.sql` | Dodatečný skript pro **přidání UNIQUE indexů** na obchodní klíče dimenzí. |
| `FactCameraDetection - indexes.sql` | Vytvoření **neklastrovaných indexů** na všech cizích klíčích faktové tabulky pro optimalizaci dotazů. |
| `Stg_CameraCamea_indexes.sql` | **Indexy pro Staging tabulku** pro zrychlení ETL operací (`LandingID`, `OriginalTime`, `Sensor`, `LP` atd.). |
| `DimTime - naplneni.sql` | **Stored Procedure** (`FillDimTime`) pro generování dat do `DimTime` (každou minutu) pro období **2024-01-01 až 2025-12-31**. |
| `unknown.sql` / `UnknownHodnoty.sql` | Skripty pro **vložení Fallback (UNKNOWN) záznamů** s klíčem **-1** do dimenzí a do `DimTime`. Zajišťuje integritu pro chybějící data. |
| `ResetDimenziaFaktu.sql` | **Úplný reset DW.** Provádí `DELETE` záznamů, **resetuje `AUTO_INCREMENT` klíče** a **vkládá Fallback záznamy** s `Key = -1`. (Kompletní verze pro MySQL/MariaDB). |

---

## 💻 Schéma MS SQL Server Data Warehouse (DW)

### 1. **DDL a Schéma**
| Soubor | Popis |
| :--- | :--- |
| `DWH_kamery_priprava.sql` | **Kompletní DDL pro MS SQL.** Vytváří schémata `Stg`, `dbo` a definuje `[Stg].[CameraCamea]`, `[dbo].[DimTime]` a `[dbo].[FactCameraDetection]` s **IDENTITY** klíči a **FOREIGN KEYs**. |
| `dbo.DimCity.sql`, `dbo.DimSensor.sql`, `dbo.DimLP.sql`, atd. | **DDL pro dimenze** s klíčem `INT IDENTITY(1,1) PRIMARY KEY`. |
| `dbo.ETL_RunLog.sql`, `dbo.ETL_IncrementalControl.sql` | **Řídicí a logovací tabulky** pro MS SQL. |
| `Stg.CameraCamea_smazani_duplicit.sql` | Skript pro odstranění duplicitních řádků ve Staging tabulce pomocí `ROW_NUMBER()`. |

### 2. **Indexy a Údržba**
| Soubor | Popis |
| :--- | :--- |
| `DimIndex.sql` | Vytvoření **UNIQUE NONCLUSTERED INDEXŮ** na klíčových atributech dimenzí (např. `SensorCode`, `CityName`) pro zajištění unikátnosti. |
| `IX_DimTime_FullDate.sql`, `IX_DimTime_FullDate_Hour_Minute.sql` | **Indexy pro DimTime** pro efektivní vyhledávání podle data a času. |
| `IX_ETLIncrementalControl_topic.sql` | **Index pro řídicí tabulku** pro rychlý lookup podle `Topic`. |
| `StgIndexes.sql` | **Indexy pro Staging tabulku** pro urychlení ETL procesu v MS SQL (např. `LandingID`, `OriginalTime`). |
| `dimTime - naplneni.sql` | **TSQL skript** pro generování dat do `DimTime` (každou minutu) pro období 2024-01-01 až 2025-12-31. |
| `ResetDimenziAfaktu.sql` | **Úplný reset DW.** `DELETE` záznamů, **resetování `IDENTITY` klíčů** (`DBCC CHECKIDENT`) a **vkládání Fallback záznamů** s `Key = -1`. (Kompletní verze pro MS SQL). |
| `Structure.sql` | **Selektovací skript** pro získání kompletní struktury tabulek (včetně constraintů a indexů) z databáze MS SQL Serveru. |

---

## 💠 Schéma ClickHouse

| Soubor | Popis |
| :--- | :--- |
| `Dimensions.sql`, `Fact.sql` | **Standardní DDL** pro dimenzní a faktovou tabulku v ClickHouse. V dimenzích používá `ReplacingMergeTree`. |
| `Stg_CameraCamea.sql` | **Definice Staging tabulky** pro data z kamer. |
| `Dodelavky.sql` | Generuje data pro **časovou dimenzi** (`DimTime`) a přidává sloupec **`CameraDetectionKey UUID`** do faktové tabulky. |
| `Unknown.sql` | **Vkládání Fallback (UNKNOWN) Záznamů** s klíčem **`4294967295`** do dimenzí pro ošetření chybějících hodnot. |
| `ETL_IncrementalControl.sql`, `ETL_RunLog.sql` | **Řídicí a logovací tabulky** pro ClickHouse. |
| `TruncateAll.sql` | Skript pro rychlé **vyprázdnění (TRUNCATE)** všech faktových a dimenzních tabulek. |