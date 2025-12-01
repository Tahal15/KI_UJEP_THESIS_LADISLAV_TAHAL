import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_chart():
    csv_file = "benchmark_results.csv"
    if not os.path.exists(csv_file):
        print(f"❌ Soubor {csv_file} neexistuje.")
        return

    df = pd.read_csv(csv_file)
    
    # Nastavení stylu pro akademický vzhled
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 7))

    # Definice barev podle zadání uživatele (nejefektivnější verze)
    custom_colors = {
        "ClickHouse": "#4BC0C0",  # Teal
        "MSSQL": "#A0A2A8",       # Grey (MSSQL Col)
        "PostgreSQL": "#FF9F40",  # Orange
        "MariaDB": "#FF6384",     # Pink/Red (MariaDB Col)
        "TimescaleDB": "#FFCD56"  # Yellow
    }
    
    # Pokud by v CSV byly jiné názvy, fallback na default paletu
    palette = custom_colors if all(db in custom_colors for db in df['Database'].unique()) else "viridis"

    # Vytvoření barplotu
    chart = sns.barplot(
        data=df, 
        x="Concurrency", 
        y="TPS", 
        hue="Database", 
        palette=palette,
        edgecolor="black",
        linewidth=1
    )

    # Popisky a titulek
    plt.title("Propustnost databází při souběžné zátěži (TPS)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Počet souběžných uživatelů", fontsize=12, labelpad=10)
    plt.ylabel("Transakce za sekundu (TPS) - Vyšší je lepší", fontsize=12, labelpad=10)
    
    # Legenda
    plt.legend(title="Databáze", title_fontsize='12', fontsize='11', loc='upper right')

    # Přidání hodnot nad sloupce
    for container in chart.containers:
        chart.bar_label(container, fmt='%.2f', padding=3, fontsize=11, fontweight='bold')

    # Jemné doladění
    plt.tight_layout()
    
    # Uložení
    output_file = "benchmark_chart_pretty.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Graf uložen do {output_file}")

if __name__ == "__main__":
    generate_chart()
