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

Mnohé organizace čelí problému, jak efektivně zpracovávat, ukládat a vizualizovat data, aby byla snadno přístupná i uživatelům bez IT vzdělání. V dnešní době lze využít mnoha nástrojů, ať už **open-source** či **komerčních řešení**, která zahrnují nejen nástroje pro vizualizaci, ale i nástroje pro **datové sklady** a technologie pro **online analytické zpracování (OLAP)**. Tato práce se zaměřuje na jejich komplexní srovnání.
Datový sklad je navržen dle metodiky **pana Kimballa**. Hvězdicové schéma.

---

## 🎯 Cíl práce

Cílem této bakalářské práce je provést **komplexní srovnání** open-source a komerčních nástrojů pro **vizualizaci a analýzu dat**, včetně souvisejících technologií pro **datové sklady** a **OLAP (Online Analytical Processing)**.

Srovnání bude probíhat na **reálných datech** generovaných v datové platformě **Portabo** a zaměří se na klíčové aspekty, jako jsou:

* **Technické požadavky:** Analýza nároků na infrastrukturu.
* **Nároky na provoz:** Požadavky na dovednosti uživatelů a tvorbu reportů.
* **Ekonomické aspekty:** Porovnání licenčních modelů a **TCO (Total Cost of Ownership)**.
* **Implementace OLAP:** Návrh a vytvoření datového skladu/OLAP.
* **Výkonové porovnání:** Měření výkonu při sběru dat, tvorbě výstupů a zátěžové testování.
* **Grafické možnosti:** Srovnání vizualizačních prvků, tvorba vlastních vizualizací a práce s mapovými daty.

Výstupem práce bude **komplexní přehled výhod a nevýhod** obou přístupů a **doporučení** vhodného systému pro organizace zvažující implementaci.

---

## 📁 Struktura repozitáře

Tento repozitář obsahuje podklady a implementační skripty pro práci. Klíčové složky a soubory jsou:

* **Analýza topíků:** Excel report obsahující group by topíků dle JSON struktury s 100% a 50% shodou.
* **Bakalářská práce PDF:** Text práce ve formátu PDF a TEX.
* **MSSQL_MSSQL_SSAS_PowerBI:** Implementace s komerčními nástroji **MS SQL Server, SSAS (SQL Server Analysis Services)** a **Power BI**.
* **MariaDB_Clickhouse_CubeJS_Superset:** Implementace a docker compose s open-source nástroji **MariaDB, ClickHouse, Cube.js** a **Apache Superset**.
* **MariaDB_MariaDB_CubeJS_Superset:** Hybridní implementace lokální jezero **MariaDB** a datový sklad **MariaDB**. Analytická část v docker.
* **PostgreSQL_PostgreSQL_CubeJS_Superset:** Implementace a podklady pro řešení s **PostgreSQL** a open-source nástroji **Cube.js** a **Apache Superset**.
* **Scripty:** Různé pomocné skripty (ETL, SQL).
* **README.md:** Tento úvodní soubor.