# Benchmark Databází - Souběžná Zátěž

Tento skript slouží k porovnání výkonu databází (MSSQL, MariaDB, ClickHouse) pod zátěží.

## Požadavky

1. Python 3.x
2. Nainstalované knihovny:
   ```bash
   pip install -r requirements.txt
   ```
   (Obsahuje: `pymysql`, `clickhouse-driver`, `pyodbc`, `pandas`, `matplotlib`, `psycopg2`)

3. **ODBC Driver pro MSSQL**: Musí být nainstalován v systému (`ODBC Driver 17 for SQL Server`).

## Konfigurace

Otevřete soubor `concurrency_test.py` a upravte sekci `DB_CONFIG` podle vašich přihlašovacích údajů, pokud se liší od výchozích.

## Spuštění
### Testování všech databází najednou
```bash
python concurrency_test.py
```

### Testování jedné konkrétní databáze
Pokud nemůžete mít spuštěné všechny databáze najednou (např. kvůli konfliktům portů), můžete je testovat postupně. Výsledky se budou automaticky doplňovat do společného souboru.

```bash
python concurrency_test.py --db MSSQL
python concurrency_test.py --db MariaDB
python concurrency_test.py --db MariaDB_InnoDB
python concurrency_test.py --db ClickHouse
python concurrency_test.py --db PostgreSQL
```

## Výstupy

Skript vygeneruje:
1. **Konzolový výstup**: Průběžné výsledky testů.
2. **benchmark_results.csv**: Tabulka s podrobnými statistikami (TPS, Latency Avg/P95/Min/Max).
3. **benchmark_chart.png**: Graf porovnávající TPS (Transactions Per Second) pro různé úrovně zátěže.

## Metodika

Test simuluje souběžné uživatele pomocí vláken (`ThreadPoolExecutor`).
Každý "uživatel" provede sérii 5 analytických dotazů (od jednoduchých agregací po komplexní CTE).

Měří se:
- **TPS (Throughput)**: Počet dotazů vyřízených za sekundu.
- **Latency**: Doba trvání jednotlivých dotazů (průměr a 95. percentil).

## Interpretace Výsledků

### 1. TPS (Transactions Per Second)
*   **Co to je:** Počet dotazů, které databáze zvládne vyřídit za jednu sekundu.
*   **Interpretace:** **Čím vyšší, tím lepší.**
*   Ukazuje "hrubou sílu" a propustnost databáze. Pokud se TPS s rostoucím počtem uživatelů nezvyšuje (nebo klesá), znamená to, že databáze narazila na svůj limit (CPU, I/O, nebo zamykání).

### 2. Avg Latency (Průměrná odezva)
*   **Co to je:** Průměrný čas v sekundách, jak dlouho trvá vyřízení jednoho dotazu.
*   **Interpretace:** **Čím nižší, tím lepší.**
*   Při zvyšování počtu uživatelů je normální, že latence roste (dotazy čekají ve frontě). Důležité je, aby nerostla exponenciálně.

### 3. Chyby "No space left on device" (PostgreSQL)
Pokud se při testu PostgreSQL objeví chyba `could not resize shared memory segment`, znamená to, že operační systém (Windows) vyčerpal limit pro sdílenou paměť kvůli velkému množství paralelních procesů.
*   **Řešení:** Skript automaticky nastavuje `SET max_parallel_workers_per_gather = 0;`, aby se pro každý dotaz nepoužívaly další paralelní procesy, což šetří paměť a je pro concurrency testy férovější.
