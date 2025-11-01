# MariaDB -> MariaDB -> Cube.js -> Apache Superset

Tato složka obsahuje hybridní implementaci, kde MariaDB slouží jako data lake i datový sklad. Analytická část (Cube.js, Superset) je kontejnerizována.

## Struktura adresáře

*   `README.md`: Původní úvodní soubor k tomuto adresáři.
*   `AI_README.md`: Tento soubor, generovaný s pomocí AI pro lepší přehlednost.
*   `docker-compose.yml`: Konfigurační soubor pro spuštění analytických služeb v Dockeru.
*   `cubejs/`: Adresář obsahující konfiguraci a datové modely pro Cube.js.
    *   `.env`: Proměnné prostředí pro Cube.js.
    *   `model/`: Datové modely pro jednotlivé dimenze a fakty.
    *   `schema/`: Schéma pro Cube.js.
*   `superset/`: Adresář obsahující konfiguraci pro Apache Superset.
    *   `superset_config.py`: Konfigurační soubor pro Superset.
