# 📚 MariaDB DL -> MariaDB DW -> Cube.js -> Apache superset

Tento repozitář obsahuje komplexní skripty pro správu datového skladu (DW) na více platformách. Implementace je hybridní: **ETL a databáze běží lokálně na Windows** , zatímco **analytický stack** (Cube.js a Superset) běží v **Dockeru**.

---

## ⚙️ I. První kroky a ruční instalace

Pro správné fungování celého systému je nutné mít lokálně nainstalovány dvě instance MariaDB a spustit je na specifických portech.

### 1. Nastavení databází

Musíte mít spuštěné **dvě nezávislé instance** databáze MariaDB, které slouží jako **Data Lake** a **Data Warehouse**.

| Komponenta | Host | Port | Databáze | Uživatel | Heslo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Lake (Landing)** | localhost | 3306 (standard) | `mttgueries` | tahal | tohlejeroothesloprobakalarku2025 |
| **Data Warehouse (Staging)** | localhost | 3307 | `datovy_sklad` | tahal | tohlejeroothesloprobakalarku2025 |

* **Instalace:** Nainstalujte MariaDB.
* **Druhá instance:** Vytvořte druhou instanci MariaDB (např. jako službu `MariaDB2`) a ujistěte se, že poslouchá na portu **3307**.
* **Spuštění:** Použijte skripty: `maria_start_data_lake.bat` a `maria_start_dw.bat`.

### 2. Inicializace schématu a dat

1.  **Vytvořte databáze:** V obou instancích (3306, 3307) vytvořte databáze `mttgueries` a `datovy_sklad`.
2.  **Načtěte dump:** Načtěte surový SQL dump do databáze **Data Lake** (`mttgueries` na portu 3306).
3.  **Vytvořte schémata DW:** Spusťte příslušné skripty pro **Data Warehouse** (port 3307).

    * `Stg_CameraCamea.sql`
    * `DimCity.sql`, `DimSensor.sql`, `DimLP.sql`, atd.
    * `FactCameraDetection.sql`
    * `DimTime - naplneni.sql` (pro naplnění časové dimenze)

### 3. Spuštění ETL

Po inicializaci databází můžete spustit ETL skripty v Pythonu.

* **ETL 1 (MQTT Lake → Staging):** Spusťte skript pro dynamické zpracování JSON dat:
    ```bash
    maria_bilina_kamery_lake_to_staging.py
    ```
* **ETL 2 (Staging → Facts):** Spusťte hlavní ETL proces pro kamery (vyžaduje předchozí ETL do Stagingu):
    ```bash
    python maria_click_kamery_staging_to_fact.py
    ```

---

## 🐳 II. Spuštění Analytického Prostředí (Docker)

Analytická vrstva je spuštěna pomocí `docker-compose` a zpřístupňuje data z vaší lokální MariaDB (port 3307).

### 1. Docker Compose

Služby:
* **`cubestore`**: Úložiště pro data cachovaná Cube.js.
* **`cube`**: **Cube API** (logická datová vrstva). Připojuje se k vaší lokální DW databázi na portu **3307** pomocí DNS **`host.docker.internal`**. Zpřístupňuje data na **PostgreSQL wire-protocol** (port 15432).
* **`superset`**: **Apache Superset** pro vizualizaci. Připojuje se k Cube API na portu 15432.

### 2. Spuštění

1.  Ujistěte se, že je spuštěn Docker a lokální MariaDB DW (port 3307).
2.  V adresáři s `docker-compose.yml` spusťte:

    ```bash
    docker-compose up -d
    ```

### 3. Přístup k aplikacím

| Služba | Adresa | Použití |
| :--- | :--- | :--- |
| **Cube API** | http://localhost:4000 | Definice datových modelů (schéma `cubejs/`) |
| **SQL API (pro Superset)** | `host.docker.internal:15432` | SQL rozhraní pro dotazování modelů |
| **Superset** | http://localhost:8088 | Vizualizace a Dashboards |

**Poznámka k připojení:** Kontejner `cube` používá `host.docker.internal:3307` k dosažení vaší lokální MariaDB. Pokud toto DNS nefunguje, může být nutné upravit proměnnou `CUBEJS_DB_HOST` na IP adresu hostitelského počítače.

---
