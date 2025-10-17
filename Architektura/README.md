\# 📊 Struktura projektu



Tento projekt popisuje architekturu \*\*on-premise systému pro zpracování a vizualizaci výrobních a provozních dat\*\*.  

Cílem je vytvořit kompletní reportingové řešení postavené na datových vrstvách \*\*Data Lake → Data Warehouse → OLAP → Reporting\*\*, které umožňuje analytické zpracování a vizualizaci dat bez nutnosti cloudových služeb. Následující část popisuje architekturu systému využívanou v projektu. Pro znázornění datových toků a funkcionality jsou použity fiktivní systémy, které slouží k plnohodnotné ilustraci řešení.



---



\## 🏗️ Architektura systému



Celý systém je rozdělen do čtyř hlavních vrstev:



!\[Reporting Structure](./reporting\_structure.png)



---



\### 1. \*\*Data Sources (Zdrojová data)\*\*

Základní vstupní úroveň systému mohou tvořit různé podnikové systémy a databáze:

\- \*\*MES\*\* – výrobní systém (Manufacturing Execution System)  

\- \*\*TIS\*\* – technologický informační systém  

\- \*\*SAP\*\* – ekonomický a účetní systém  

\- \*\*NEP\*\* – systém trasování dřeva



Datové přenosy mohou být realizovány pomocí:

\- \*\*Oracle SQL\*\*

\- \*\*PI Archive\*\*

\- \*\*CSV exportů\*\*

\- \*\*PostgreSQL připojení\*\*



Tyto zdroje poskytují \*\*různorodá nestrukturovaná data\*\*, která jsou dále ukládána do datového jezera.



---



\### 2. \*\*Data Lake (Datové jezero) – Raw unstructured data\*\*



Datové jezero slouží jako \*\*úložiště všech nestrukturovaných a surových dat\*\* do jednoho centrálního bodu.  

V této vrstvě se provádí:

\- Ukládání dat z různých systémů (MES, TIS, SAP, NEP)

\- \*\*Analytická a prediktivní práce\*\* datových analytiků

\- Využití pro \*\*machine learning\*\*, \*\*statistiku\*\*, \*\*matematické analýzy\*\* a \*\*predikce\*\*



Data jsou v této vrstvě ukládána beze změn, aby bylo možné kdykoliv provést nové zpracování nebo kontrolu historických dat.

Případně zde lze kontrolovat i efektivitu a chybovost ETL procesů.



---



\### 3. \*\*Data Warehouse (Datový sklad) – Clean structured data\*\*



Z datového jezera jsou data \*\*čištěna, transformována a strukturována\*\* do datového skladu.

V první fázi jsou data kopírována do \*\*staging vrstvy\*\* datového skladu.

V rámci projektu to znamená rozparsování formátu JSON na jednotlivé sloupce a jejich přiřazení do tabulek podle logické struktury a významu dat.



Ze staging vrstvy jsou následně pomocí dalšího ETL procesu vytvářeny \*\*dimenze\*\* a \*\*faktové tabulky\*\*, které společně tvoří hvězdicové schéma \*\*(star schema)\*\* datového modelu.

Datový sklad představuje \*\*centrální zdroj pravdy („one truth“) pro celý podnik\*\*.



Kromě dimenzí a faktů se ve větších společnostech dělí na logická odvětví např:

\- `\_Production` – výrobní data  

\- `\_Finance` – ekonomická a účetní data  

\- `\_Quality` – kontrolní a jakostní data  



Všechna data jsou uložená v relačním SQL formátu a propojená klíči pro snadnou integraci s OLAP kostkami.



---



\### 4. \*\*OLAP (Analytická vrstva) – Presentation layer\*\*



Vrstva OLAP (Online Analytical Processing) je navržena pro zpracování dotazů typu DQL (Data Query Language), které jsou určeny pro čtení, agregaci a analýzu dat.

Systém je optimalizován na rychlé provádění dotazovacích příkazů (využívá columnar storage a denormalizaci), zatímco operace typu DML (INSERT, UPDATE, DELETE) nebo DDL (CREATE, ALTER, DROP) se v této vrstvě běžně nevykonávají.



V některých implementacích OLAP model obsahuje i sémantickou vrstvu, která uživatelům umožňuje vytvářet dotazy a analýzy prostřednictvím přehledného rozhraní, bez nutnosti přímé znalosti SQL jazyka.



Funkce OLAP vrstvy:

\- Možnost \*\*drag \& drop\*\* vytváření pohledů  

\- Předpřipravené výpočty a metriky  

\- Práce s daty pomocí jazyků \*\*DAX, MDX, a dalších\*\*



Tato vrstva umožňuje vytvářet pohledy pro reportingové nástroje jako Power BI nebo Excel, Apache superset.



---



\### 5. \*\*Reporting (Datová vizualizace)\*\*



Finální vrstva systému zajišťuje vizualizaci a sdílení výsledků analýz.



Používané nástroje:

\- \*\*Power BI\*\*

&nbsp; - Napojení přes \*\*Power BI Gateway (PB GW)\*\* pro reporty v cloudu

&nbsp; - Publikace na \*\*report server\*\* pro lokální sdílení on premise

\- \*\*Excel\*\*

&nbsp; - Přímé připojení na OLAP kostku (např. přes OLE DB)

\- \*\*Apache superset\*\*

&nbsp; - Napojení přes PostgreSQL konektor



---



\*Autor: Ladislav Tahal\*  

\*Bakalářská práce – 2025\*



