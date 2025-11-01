# 🧠 Analýza topiků MQTT podle podobnosti JSON struktury

Tento projekt slouží k **automatické analýze a seskupování MQTT témat (topics)** podle podobnosti jejich **JSON payloadů**.  
Cílem je identifikovat témata, která mají **stejnou nebo podobnou datovou strukturu**, a usnadnit tak návrh **datového skladu** a **ETL pipeline**.

---

## 📄 Popis

MQTT témata mohou mít různé formáty dat (payloadů).  
Pro účely datové integrace (např. v datové platformě **Portabo**) je vhodné seskupit podobné datové toky dohromady.

Tento nástroj porovnává struktury JSON zpráv podle **Jaccardovy podobnosti** klíčů v jejich rozbalené (flatten) podobě:

**J(A, B) = |A ∩ B| / |A ∪ B|**

- **100 % podobnost (J = 1)** → témata mají **identickou strukturu**  
- **50 % podobnost (J ≥ 0.5)** → témata mají **částečně podobnou strukturu**

---

## ⚙️ Jak to funguje

1. Skript `analyze_json.py` se připojí k databázi PostgreSQL (datové jezero).
2. Načte vzorky MQTT zpráv (JSON payloadů).
3. Každý JSON rozbalí (rekurzivně včetně vnořených objektů).
4. Vypočítá Jaccardovu podobnost mezi všemi dvojicemi témat.
5. Seskupí témata do **klastrů** podle prahové hodnoty podobnosti.
6. Výsledek uloží do **Excel/CSV souboru**.

---

## 📁 Struktura adresáře

| Soubor | Popis |
|:---------------------------|:---------------------------------------------------------------|
| **`README.md`** | Tento soubor. |
| **`README_BACKUP.md`** | Záloha původního `README.md`. |
| **`AI_README.md`** | Rozšířený `README.md` generovaný s pomocí AI pro lepší přehlednost. |
| **`Topik100.xlsx`** | Seskupení témat s **100 % Jaccardovou podobností** (identická struktura JSON) |
| **`Topik50.xlsx`** | Seskupení témat s **≥ 50 % podobností** (částečně podobná struktura) |
