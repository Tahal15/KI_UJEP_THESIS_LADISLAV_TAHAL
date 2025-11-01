# MariaDB -> ClickHouse -> Cube.js -> Apache Superset

Tato složka obsahuje kompletní implementaci open-source řešení pro analýzu a vizualizaci dat. Tento stack využívá MariaDB jako data lake, ClickHouse jako datový sklad, Cube.js pro sémantickou vrstvu a Apache Superset pro vizualizaci.

## Struktura adresáře

*   `README.md`: Původní úvodní soubor k tomuto adresáři.
*   `AI_README.md`: Tento soubor, generovaný s pomocí AI pro lepší přehlednost.
*   `docker-compose.yml`: Konfigurační soubor pro spuštění všech služeb v Dockeru.
*   `cubejs/`: Adresář obsahující konfiguraci a datové modely pro Cube.js.
    *   `.env`: Proměnné prostředí pro Cube.js.
    *   `model/`: Datové modely pro jednotlivé dimenze a fakty.
    *   `schema/`: Schéma pro Cube.js.
*   `superset/`: Adresář obsahující konfiguraci pro Apache Superset.
    *   `requirements-local.txt`: Seznam Python závislostí pro Superset.
    *   `superset_config.py`: Konfigurační soubor pro Superset.
*   `*.tar.gz`: Archivy s daty a logy pro ClickHouse a Superset.
