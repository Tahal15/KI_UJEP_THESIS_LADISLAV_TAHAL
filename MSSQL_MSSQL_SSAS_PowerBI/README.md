# 📚 MSSQL DL -> MSSQL DW -> SSAS -> PowerBI 

Tento repozitář obsahuje jen výsledný PowerBI report, SSAS projekt a návod k instalaci. Instalační scripty naleznete ve složce scripty. Řešení je prozatím navrženo pouze pro lokální prostředí bez Dockeru, kde **Data Lake (DL)**, **Data Warehouse (DW)**, **SQL Server Analysis Services (SSAS)** a **Power BI** běží na jediném hostitelském stroji.

---

## ⚙️ I. Požadavky a Instalace Softwaru

Pro spuštění celého řešení je nutné mít nainstalovány následující komponenty:

1.  **MS SQL Server:** Je nutné mít nainstalovány **dvě samostatné instance** MS SQL Serveru.
    * **Instance 1 (DL):** Pro surová data (Data Lake). Název: `DATA_LAKE`.
    * **Instance 2 (DW):** Pro strukturovaný datový sklad (Data Warehouse). Název: `DATA_WAREHOUSE`.
2.  **SQL Server Analysis Services (SSAS):** Nainstalována instance v **Tabular módu**.
3.  **Visual Studio:** S rozšířením **Analysis Services Projects** pro vývoj SSAS modelu.
4.  **Power BI Desktop:** Pro vizualizaci dat.

---

## 💾 II. Inicializace Databází (DL → DW)

Po instalaci je potřeba inicializovat obě instance a naplnit je daty.

### 1. Spuštění Služeb

* **Data Lake (DL):** Spusťte služby pro instanci `DATA_LAKE` pomocí:
    ```bash
    start_data_lake.bat
    ```
* **Data Warehouse (DW):** Spusťte služby pro instanci `DATA_WAREHOUSE` pomocí:
    ```bash
    start_dw.bat
    ```

### 2. Načtení a Transformace Dat

1.  **Načtení Surových Dat (DL):**
    * Vytvořte databázi (např. `DataLakeDB`) v instanci `DATA_LAKE`.
    * Načtěte **surový SQL dump** (např. `mqttentries.sql`, není součástí tohoto archivu) do této databáze.

2.  **Inicializace DW Schématu:**
    * V instanci `DATA_WAREHOUSE` vytvořte databázi (např. `DWH`).
    * Spusťte následující skripty pro vytvoření celého schématu datového skladu (v tomto pořadí):
        * `DWH_kamery_priprava.sql` (vytvoří Staging, DimTime, DimCity, DimCamera, FactCameraDetection)
        * `dbo.Dim*.sql` (vytvoří zbývající dimenze: `DimLP`, `DimCountry`, atd.)
        * `UnknownHodnoty.sql` (vloží záznamy `-1`/`UNKNOWN` do dimenzí)
        * `StgIndexes.sql`, `DimIndex.sql` (vytvoří neklastrované indexy)

3.  **Naplnění Dimenze Času:**
    * Spusťte TSQL skript pro vygenerování záznamů do `DimTime` (2024–2025):
        ```sql
        -- Spusťte obsah souboru:
        dimTime - naplneni.sql
        ```

4.  **Spuštění ETL:**
    * Po nahrání SQL dumpu do datového jezera spusťte ETL script (musí být spuštěn datový sklad)
     ```bash
    bilina_kamery_lake_to_staging.py
    ```
    * Po dokončení ETL by měla být naplněna tabulka `[Stg].[CameraCamea]` v instanci `DATA_WAREHOUSE`.
    * Poté spusťte skripty pro inkrementální načítání do dimenzí a faktů.
    ```bash
    bilina_kamery_staging_to_fact.py
    ```


## 📐 III. Nasazení SSAS Modelu (Tabular)

Analytická nadstavba je implementována v SSAS (Tabular Model).

1.  **Otevření Projektu:** Otevřete soubor projektu SSAS (přiložen v této složce) ve Visual Studiu.
2.  **Připojení k DW:** Upravte datové připojení v projektu tak, aby směřovalo na vaši lokální instanci **`DATA_WAREHOUSE`**.
3.  **Deployment:** Vytvořte model a nasuňte jej (Deploy) na vaši lokální instanci **SSAS** (např. `localhost\SSASTABULAR`). Během deploymentu proběhne i proces dat (Process All).
4.  **Ověření:** Připojte se k SSAS modelu pomocí SQL Server Management Studia (SSMS) a ověřte, že jsou data načtena a měřítka fungují.

---

## 📈 IV. Vizualizace v Power BI

Finální report je vytvořen v Power BI Desktop.

1.  **Otevření Reportu:** Otevřete ukázkový soubor:
    ```
    Portabo - kamery Bílina.pbix 
    ```
2.  **Aktualizace Zdroje Dat:** V nastavení zdroje dat v Power BI:
    * **Změňte připojení** z původního SSAS serveru na vaši lokálně nasazenou SSAS instanci.
    * **Ověřte přihlašovací údaje.**
3.  **Obnovení Dat:** Klikněte na **Obnovit (Refresh)**. Report by měl načíst data přímo z vašeho SSAS modelu a zobrazit měřítka a vizuály.

---

## 📁 Struktura adresáře

| Soubor/Adresář | Popis |
|:---------------------------|:---------------------------------------------------------------|
| **`README.md`** | Tento soubor. |
| **`README_BACKUP.md`** | Záloha původního `README.md`. |
| **`AI_README.md`** | Rozšířený `README.md` generovaný s pomocí AI pro lepší přehlednost. |
| **`Portabo - kamery Bílina.pbix`** | Power BI report. |
| **`OlapTabular/`** | Adresář obsahující projekt pro SSAS Tabular model. |
