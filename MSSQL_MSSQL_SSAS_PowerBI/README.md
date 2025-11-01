# MSSQL -> MSSQL -> SSAS -> PowerBI

Tato složka obsahuje implementaci komerčního řešení s využitím MS SQL Serveru pro data lake i datový sklad, SSAS pro sémantickou vrstvu a Power BI pro vizualizaci.

## Struktura adresáře

*   `README.md`: Původní úvodní soubor k tomuto adresáři.
*   `AI_README.md`: Tento soubor, generovaný s pomocí AI pro lepší přehlednost.
*   `Portabo - kamery Bílina.pbix`: Power BI report.
*   `OlapTabular/`: Adresář obsahující projekt pro SSAS Tabular model.
    *   `OlapTabular.sln`: Visual Studio solution file.
    *   `OlapTabular/`: Adresář s vlastním projektem.
        *   `OlapTabular.smproj`: Projektový soubor pro SSAS Tabular model.
        *   `Model.bim`: Soubor s definicí tabulárního modelu.
