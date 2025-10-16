# MariaDB DL -> Clickhouse DW -> Cube.js -> Apache superset


## 🛠️ Architektura a Komponenty Stacku

Celé prostředí kromě MariaDB DL je kontejnerizováno pomocí **Docker Compose** a zahrnuje tři hlavní vrstvy:

| Služba | Technologie | Role v projektu | Port |
| :--- | :--- | :--- | :--- |
| **Datový Sklad** | **ClickHouse** | Sloupcová databáze optimalizovaná pro **OLAP** a extrémně rychlé analytické dotazy. Uchovává repliku dat z Portabo. | `8123` |
| **OLAP Layer** | **Cube.js** | Analytická vrstva (*Headless BI*), která definuje **datový model** (metriky, dimenze) a vystavuje data přes standardizované **SQL API** (*PostgreSQL Wire Protocol*). | `4000` (REST) |
| **Vizualizace** | **Apache Superset** | Open-source nástroj pro **Business Intelligence** a tvorbu dynamických dashboardů. Připojuje se k datům přes SQL API od Cube.js. | `8088` |

---

## 🚀 První spuštění (Návod)

Pozor. Data Lake MariaDB zde není obsažena, ale není nutná ke spuštění tohoto projektu.
Pokud byste chtěli replikovat celý projekt, tak stačí doinstalovat jednu lokální instanci MariaDB. Poté načíst SQL Dump a použít ETL script zde na Githubu na nahrání do DW.
Pokud tak provedete, tak není ani potřeba importu databáze v dalším kroku.

Projekt totiž obsahuje předkonfigurované svazky (volumes) s daty a nastavením.  
Pro spuštění je nutné nejprve dekomprimovat přiložené archivy.

### 1. Inicializace a obnova datových svazků

V adresáři, kde se nachází soubor `docker-compose.yml`, proveďte následující kroky pro vytvoření a naplnění datových svazků:

```bash
# Vytvoření prázdných volumes
docker volume create superset_clickhouse_clickhouse_data
docker volume create superset_clickhouse_clickhouse_logs
docker volume create superset_clickhouse_superset_data

# Obnovení obsahu

# ClickHouse data
docker run --rm -v superset_clickhouse_clickhouse_data:/to -v "${PWD}:/from" alpine sh -c "cd /to && tar xzf /from/clickhouse_data.tar.gz"

# ClickHouse logy
docker run --rm -v superset_clickhouse_clickhouse_logs:/to -v "${PWD}:/from" alpine sh -c "cd /to && tar xzf /from/clickhouse_logs.tar.gz"

# Superset data
docker run --rm -v superset_clickhouse_superset_data:/to -v "${PWD}:/from" alpine sh -c "cd /to && tar xzf /from/superset_data.tar.gz"
```

### 3. Spuštění kontejnerů

Spusťte všechny služby v pozadí pomocí konfiguračního souboru `docker-compose.yml`:

```bash
docker compose up -d
```

> **Poznámka:** První spuštění trvá déle, protože Apache Superset provádí inicializační skripty (migrace databáze a vytvoření administrátorského účtu).

---

### 4. Kontrola stavu

Ověřte, že všechny kontejnery běží:

```bash
docker compose ps
```

Očekávaný stav:  
Všechny služby (`cube`, `superset`, `clickhouse`) by měly být ve stavu **running**.

---

## 🌐 Přístup a přihlašovací údaje

Jakmile jsou služby spuštěny, můžete k nim přistupovat přes prohlížeč nebo databázové klienty:

| Služba | Adresa pro přístup | Přístupové údaje / Role |
| :--- | :--- | :--- |
| **Apache Superset (BI)** | http://localhost:8088 | **Uživatel:** `admin` **Heslo:** `tohlejeroothesloprobakalarku2025` |
| **Cube.js (Developer Playground)** | http://localhost:4000| Rozhraní pro ověřování a práci s datovým modelem Cube.js |
| **ClickHouse (Databáze)** | http://localhost:8123 | **Uživatel:** `tahal` **Heslo:**  `tohlejeroothesloprobakalarku2025` |

---

## ⚙️ Nastavení v Supersetu

Superset je již předkonfigurován s připojením k databázi.  
Připojuje se k **Cube.js SQL API** (`port 15432`), které slouží jako brána k datům v ClickHouse.

---

## 🛑 Ukončení a vyčištění

### Zastavení služeb

Pro pozastavení chodu kontejnerů (data na disku zůstanou):

```bash
ctrl + c
docker compose down
```

---

### Úplné odstranění projektu a dat

Pro odstranění kontejnerů, sítí a perzistentních svazků (volumes):

```bash
docker compose down -v
```

> ⚠️ Tento příkaz odstraní veškerá data uložená uvnitř Docker volumes, která byla vytvořena při spuštění.

---


