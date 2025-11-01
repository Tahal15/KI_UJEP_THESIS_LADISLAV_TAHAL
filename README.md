# Využití open-source a komerčních nástrojů pro vizualizaci a analýzu dat na datové platformě Portabo

| Informace | Detaily |
| :--- | :--- |
| **Název práce (česky)** | Využití open-source a komerčních nástrojů pro vizualizaci a analýzu dat na datové platformě Portabo |
| **Název práce (anglicky)** | Utilization of Open-Source and Commercial Tools for Data Visualization and Analysis on the Portabo Data Platform |
| **Typ práce** | Bakalářská (Bc.) |
| **Akademický rok** | 2024/2025 |
| **Pracoviště** | KI - Katedra informatiky |
| **Vedoucí práce** | Ing. Roman Vaibar, Ph.D., MBA |

---

## Úvod

Tato bakalářská práce se zabývá problematikou efektivního zpracování, ukládání a vizualizace dat v organizacích, s cílem zpřístupnit data i uživatelům bez technického vzdělání. Práce porovnává moderní open-source a komerční nástroje pro vizualizaci, datové sklady a technologie pro online analytické zpracování (OLAP). Datový sklad je navržen dle metodiky pana Kimballa s využitím hvězdicového schématu.

---

## 🎯 Cíl práce

Cílem této bakalářské práce je provést **komplexní srovnání** open-source a komerčních nástrojů pro **vizualizaci a analýzu dat**, včetně souvisejících technologií pro **datové sklady** a **OLAP (Online Analytical Processing)**.

Srovnání bude probíhat na **reálných datech** generovaných v datové platformě **Portabo** a zaměří se na klíčové aspekty, jako jsou:

*   **Technické požadavky:** Analýza nároků na infrastrukturu.
*   **Nároky na provoz:** Požadavky na dovednosti uživatelů a tvorbu reportů.
*   **Ekonomické aspekty:** Porovnání licenčních modelů a **TCO (Total Cost of Ownership)**.
*   **Implementace OLAP:** Návrh a vytvoření datového skladu/OLAP.
*   **Výkonové porovnání:** Měření výkonu při sběru dat, tvorbě výstupů a zátěžové testování.
*   **Grafické možnosti:** Srovnání vizualizačních prvků, tvorba vlastních vizualizací a práce s mapovými daty.

Výstupem práce bude **komplexní přehled výhod a nevýhod** obou přístupů a **doporučení** vhodného systému pro organizace zvažující implementaci.

---

## 📁 Struktura repozitáře

Tento repozitář obsahuje veškeré podklady, skripty a implementace vytvořené v rámci této bakalářské práce.

### Kořenové soubory

*   `README.md`: Původní úvodní soubor k projektu.
*   `AI_README.md`: Tento soubor, generovaný s pomocí AI pro lepší přehlednost.
*   `project_manifest.xml`: Komplexní manifest všech souborů v projektu, generovaný pro účely analýzy a správy.

### Adresáře

| Adresář | Popis |
| :--- | :--- |
| **Analýza topiků** | Obsahuje analýzu MQTT témat (topics) ve formátu Excel, rozdělenou podle 100% a 50% shody struktur JSON payloadů. |
| **Architektura** | Grafické znázornění architektury navrženého řešení. |
| **Bakalářská práce PDF** | Zdrojové kódy a výsledné PDF bakalářské práce ve formátu LaTeX. |
| **MariaDB_Clickhouse_CubeJS_Superset** | Implementace open-source řešení s využitím MariaDB jako data lake, ClickHouse jako datového skladu, Cube.js pro sémantickou vrstvu a Apache Superset pro vizualizaci. |
| **MariaDB_MariaDB_CubeJS_Superset** | Hybridní implementace, kde MariaDB slouží jako data lake i datový sklad. Analytická část (Cube.js, Superset) je kontejnerizována. |
| **MSSQL_MSSQL_SSAS_PowerBI** | Implementace komerčního řešení s využitím MS SQL Serveru pro data lake i datový sklad, SSAS pro sémantickou vrstvu a Power BI pro vizualizaci. |
| **PostgreSQL_PostgreSQL_CubeJS_Superset** | Implementace open-source řešení s využitím PostgreSQL a TimescaleDB, Cube.js a Apache Superset. |
| **Předloha** | Oficiální předloha pro bakalářskou práci na KI UJEP. |
| **Scripty** | Veškeré pomocné skripty pro ETL procesy, databázové operace a další. |
| **Zdroje** | Seznam použitých zdrojů. |
