import time
import concurrent.futures
import statistics
import pandas as pd
import matplotlib.pyplot as plt
import pymysql
import pyodbc
import psycopg2
from clickhouse_driver import Client
from datetime import datetime

# ==============================================================================
# 🔧 KONFIGURACE PŘIPOJENÍ
# ==============================================================================

DB_CONFIG = {
    "MSSQL": {
        "driver": "{ODBC Driver 17 for SQL Server}",
        "server": "TAHAL\\DATA_WAREHOUSE",
        "database": "DWH",
        "uid": "sa",
        "pwd": "HesloProBakalarku2025*"
    },
    "MariaDB": {
        "host": "localhost",
        "port": 3308, # DWH port
        "user": "admin",
        "password": "C0lumnStore!",
        "database": "mttgueries"
    },
    "MariaDB_InnoDB": {
        "host": "localhost",
        "port": 3308, # DWH port
        "user": "admin",
        "password": "C0lumnStore!",
        "database": "mttgueries"
    },
    "ClickHouse": {
        "host": "localhost",
        "port": 9000,
        "user": "tahal",
        "password": "tohlejeroothesloprobakalarku2025",
        "database": "default"
    },
    "PostgreSQL": {
        "host": "localhost",
        "port": 5434, # DWH port
        "user": "tahal",
        "password": "tohlejeroothesloprobakalarku2025",
        "database": "datovy_sklad"
    }
}

# ==============================================================================
# 📝 SQL DOTAZY (Dialekty)
# ==============================================================================

QUERIES = {
    "MSSQL": [
        # Q1: Jednoduchá agregace
        """
        SELECT vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY vc.VehicleClass;
        """,
        # Q2: Agregace přes čas
        """
        SELECT t.FullDate, COUNT(*) AS NumberOfDetections
        FROM FactCameraDetection f
        JOIN DimTime t ON f.TimeKey = t.TimeKey
        GROUP BY t.FullDate
        ORDER BY t.FullDate;
        """,
        # Q3: Top 10 Města
        """
        SELECT TOP 10 c.CityName, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimCity c ON f.CityKey = c.CityKey
        JOIN DimCountry co ON f.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        WHERE co.CountryCode = 'CZ' AND vc.VehicleClass = '2'
        GROUP BY c.CityName
        ORDER BY AverageVelocity DESC;
        """,
        # Q4: 2 Dimenze
        """
        SELECT dt.DetectionType, vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimDetectionType dt ON f.DetectionTypeKey = dt.DetectionTypeKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY dt.DetectionType, vc.VehicleClass
        ORDER BY dt.DetectionType, vc.VehicleClass;
        """,
        # Q5: Komplexní (Víkendy)
        """
        WITH WeekendDetections AS (
            SELECT f.CityKey, f.CountryKey, f.VehicleClassKey, f.Velocity
            FROM FactCameraDetection f
            JOIN DimTime t ON f.TimeKey = t.TimeKey
            WHERE DATEPART(weekday, t.FullDate) IN (1, 7) -- Neděle=1, Sobota=7 (default US)
        )
        SELECT co.CountryCode, c.CityName, vc.VehicleClass, 
               AVG(wd.Velocity) AS AverageVelocity,
               DENSE_RANK() OVER(PARTITION BY co.CountryCode ORDER BY COUNT(*) DESC) AS CityRankByDetections
        FROM WeekendDetections wd
        JOIN DimCity c ON wd.CityKey = c.CityKey
        JOIN DimCountry co ON wd.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON wd.VehicleClassKey = vc.VehicleClassKey
        GROUP BY co.CountryCode, c.CityName, vc.VehicleClass
        ORDER BY co.CountryCode, CityRankByDetections;
        """
    ],
    "MariaDB": [
        # Q1
        """
        SELECT vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY vc.VehicleClass;
        """,
        # Q2
        """
        SELECT t.FullDate, COUNT(*) AS NumberOfDetections
        FROM FactCameraDetection f
        JOIN DimTime t ON f.TimeKey = t.TimeKey
        GROUP BY t.FullDate
        ORDER BY t.FullDate;
        """,
        # Q3 (LIMIT místo TOP)
        """
        SELECT c.CityName, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimCity c ON f.CityKey = c.CityKey
        JOIN DimCountry co ON f.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        WHERE co.CountryCode = 'CZ' AND vc.VehicleClass = '2'
        GROUP BY c.CityName
        ORDER BY AverageVelocity DESC
        LIMIT 10;
        """,
        # Q4
        """
        SELECT dt.DetectionType, vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimDetectionType dt ON f.DetectionTypeKey = dt.DetectionTypeKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY dt.DetectionType, vc.VehicleClass
        ORDER BY dt.DetectionType, vc.VehicleClass;
        """,
        # Q5 (DAYOFWEEK: 1=Sun, 7=Sat)
        """
        WITH WeekendDetections AS (
            SELECT f.CityKey, f.CountryKey, f.VehicleClassKey, f.Velocity
            FROM FactCameraDetection f
            JOIN DimTime t ON f.TimeKey = t.TimeKey
            WHERE DAYOFWEEK(t.FullDate) IN (1, 7)
        )
        SELECT co.CountryCode, c.CityName, vc.VehicleClass, 
               AVG(wd.Velocity) AS AverageVelocity,
               DENSE_RANK() OVER(PARTITION BY co.CountryCode ORDER BY COUNT(*) DESC) AS CityRankByDetections
        FROM WeekendDetections wd
        JOIN DimCity c ON wd.CityKey = c.CityKey
        JOIN DimCountry co ON wd.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON wd.VehicleClassKey = vc.VehicleClassKey
        GROUP BY co.CountryCode, c.CityName, vc.VehicleClass
        ORDER BY co.CountryCode, CityRankByDetections;
        """
    ],
    "MariaDB_InnoDB": [
        # Q1
        """
        SELECT vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection_innodb_old f
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY vc.VehicleClass;
        """,
        # Q2
        """
        SELECT t.FullDate, COUNT(*) AS NumberOfDetections
        FROM FactCameraDetection_innodb_old f
        JOIN DimTime t ON f.TimeKey = t.TimeKey
        GROUP BY t.FullDate
        ORDER BY t.FullDate;
        """,
        # Q3 (LIMIT místo TOP)
        """
        SELECT c.CityName, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection_innodb_old f
        JOIN DimCity c ON f.CityKey = c.CityKey
        JOIN DimCountry co ON f.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        WHERE co.CountryCode = 'CZ' AND vc.VehicleClass = '2'
        GROUP BY c.CityName
        ORDER BY AverageVelocity DESC
        LIMIT 10;
        """,
        # Q4
        """
        SELECT dt.DetectionType, vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection_innodb_old f
        JOIN DimDetectionType dt ON f.DetectionTypeKey = dt.DetectionTypeKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY dt.DetectionType, vc.VehicleClass
        ORDER BY dt.DetectionType, vc.VehicleClass;
        """,
        # Q5 (DAYOFWEEK: 1=Sun, 7=Sat)
        """
        WITH WeekendDetections AS (
            SELECT f.CityKey, f.CountryKey, f.VehicleClassKey, f.Velocity
            FROM FactCameraDetection_innodb_old f
            JOIN DimTime t ON f.TimeKey = t.TimeKey
            WHERE DAYOFWEEK(t.FullDate) IN (1, 7)
        )
        SELECT co.CountryCode, c.CityName, vc.VehicleClass, 
               AVG(wd.Velocity) AS AverageVelocity,
               DENSE_RANK() OVER(PARTITION BY co.CountryCode ORDER BY COUNT(*) DESC) AS CityRankByDetections
        FROM WeekendDetections wd
        JOIN DimCity c ON wd.CityKey = c.CityKey
        JOIN DimCountry co ON wd.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON wd.VehicleClassKey = vc.VehicleClassKey
        GROUP BY co.CountryCode, c.CityName, vc.VehicleClass
        ORDER BY co.CountryCode, CityRankByDetections;
        """
    ],
    "ClickHouse": [
        # Q1
        """
        SELECT vc.VehicleClass, avg(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY vc.VehicleClass;
        """,
        # Q2
        """
        SELECT t.FullDate, count(*) AS NumberOfDetections
        FROM FactCameraDetection f
        JOIN DimTime t ON f.TimeKey = t.TimeKey
        GROUP BY t.FullDate
        ORDER BY t.FullDate;
        """,
        # Q3
        """
        SELECT c.CityName, avg(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimCity c ON f.CityKey = c.CityKey
        JOIN DimCountry co ON f.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        WHERE co.CountryCode = 'CZ' AND vc.VehicleClass = '2'
        GROUP BY c.CityName
        ORDER BY AverageVelocity DESC
        LIMIT 10;
        """,
        # Q4
        """
        SELECT dt.DetectionType, vc.VehicleClass, avg(f.Velocity) AS AverageVelocity
        FROM FactCameraDetection f
        JOIN DimDetectionType dt ON f.DetectionTypeKey = dt.DetectionTypeKey
        JOIN DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY dt.DetectionType, vc.VehicleClass
        ORDER BY dt.DetectionType, vc.VehicleClass;
        """,
        # Q5 (toDayOfWeek: 1=Mon, 7=Sun -> So(6), Ne(7))
        """
        WITH WeekendDetections AS (
            SELECT f.CityKey, f.CountryKey, f.VehicleClassKey, f.Velocity
            FROM FactCameraDetection f
            JOIN DimTime t ON f.TimeKey = t.TimeKey
            WHERE toDayOfWeek(t.FullDate) IN (6, 7)
        )
        SELECT co.CountryCode, c.CityName, vc.VehicleClass, 
               avg(wd.Velocity) AS AverageVelocity,
               dense_rank() OVER(PARTITION BY co.CountryCode ORDER BY count(*) DESC) AS CityRankByDetections
        FROM WeekendDetections wd
        JOIN DimCity c ON wd.CityKey = c.CityKey
        JOIN DimCountry co ON wd.CountryKey = co.CountryKey
        JOIN DimVehicleClass vc ON wd.VehicleClassKey = vc.VehicleClassKey
        GROUP BY co.CountryCode, c.CityName, vc.VehicleClass
        ORDER BY co.CountryCode, CityRankByDetections;
        """
    ],
    "PostgreSQL": [
        # Q1
        """
        SELECT vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM mttgueries.FactCameraDetection f
        JOIN mttgueries.DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY vc.VehicleClass;
        """,
        # Q2
        """
        SELECT t.FullDate, COUNT(*) AS NumberOfDetections
        FROM mttgueries.FactCameraDetection f
        JOIN mttgueries.DimTime t ON f.TimeKey = t.TimeKey
        GROUP BY t.FullDate
        ORDER BY t.FullDate;
        """,
        # Q3
        """
        SELECT c.CityName, AVG(f.Velocity) AS AverageVelocity
        FROM mttgueries.FactCameraDetection f
        JOIN mttgueries.DimCity c ON f.CityKey = c.CityKey
        JOIN mttgueries.DimCountry co ON f.CountryKey = co.CountryKey
        JOIN mttgueries.DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        WHERE co.CountryCode = 'CZ' AND vc.VehicleClass = '2'
        GROUP BY c.CityName
        ORDER BY AverageVelocity DESC
        LIMIT 10;
        """,
        # Q4
        """
        SELECT dt.DetectionType, vc.VehicleClass, AVG(f.Velocity) AS AverageVelocity
        FROM mttgueries.FactCameraDetection f
        JOIN mttgueries.DimDetectionType dt ON f.DetectionTypeKey = dt.DetectionTypeKey
        JOIN mttgueries.DimVehicleClass vc ON f.VehicleClassKey = vc.VehicleClassKey
        GROUP BY dt.DetectionType, vc.VehicleClass
        ORDER BY dt.DetectionType, vc.VehicleClass;
        """,
        # Q5 (ISODOW: 1=Mon, 7=Sun -> So(6), Ne(7))
        """
        WITH WeekendDetections AS (
            SELECT f.CityKey, f.CountryKey, f.VehicleClassKey, f.Velocity
            FROM mttgueries.FactCameraDetection f
            JOIN mttgueries.DimTime t ON f.TimeKey = t.TimeKey
            WHERE EXTRACT(ISODOW FROM t.FullDate) IN (6, 7)
        )
        SELECT co.CountryCode, c.CityName, vc.VehicleClass, 
               AVG(wd.Velocity) AS AverageVelocity,
               DENSE_RANK() OVER(PARTITION BY co.CountryCode ORDER BY COUNT(*) DESC) AS CityRankByDetections
        FROM WeekendDetections wd
        JOIN mttgueries.DimCity c ON wd.CityKey = c.CityKey
        JOIN mttgueries.DimCountry co ON wd.CountryKey = co.CountryKey
        JOIN mttgueries.DimVehicleClass vc ON wd.VehicleClassKey = vc.VehicleClassKey
        GROUP BY co.CountryCode, c.CityName, vc.VehicleClass
        ORDER BY co.CountryCode, CityRankByDetections;
        """
    ]
}

# ==============================================================================
# 🏃‍♂️ BENCHMARK ENGINE
# ==============================================================================

def get_connection(db_type):
    """Vrátí connection objekt pro daný typ databáze."""
    cfg = DB_CONFIG[db_type]
    
    if db_type == "MSSQL":
        conn_str = (
            f"Driver={cfg['driver']};"
            f"Server={cfg['server']};"
            f"Database={cfg['database']};"
            f"UID={cfg['uid']};"
            f"PWD={cfg['pwd']};"
        )
        return pyodbc.connect(conn_str)
    
    elif db_type == "MariaDB" or db_type == "MariaDB_InnoDB":
        return pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database']
        )
    
    elif db_type == "ClickHouse":
        # ClickHouse driver používá Client objekt, ne standardní DB-API 2.0 connection
        return Client(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database']
        )

    elif db_type == "PostgreSQL":
        conn = psycopg2.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            dbname=cfg['database']
        )
        # 🔧 FIX: Vypnutí paralelních workerů pro tento session.
        # Na Windows při vysoké konkurenci (20+ users) dochází k vyčerpání sdílené paměti ("No space left on device"),
        # pokud se každý dotaz snaží spustit více paralelních procesů.
        try:
            with conn.cursor() as cur:
                cur.execute("SET max_parallel_workers_per_gather = 0;")
            conn.commit()
        except Exception as e:
            print(f"⚠️ Nepodařilo se nastavit max_parallel_workers_per_gather: {e}")
        
        return conn
    
    raise ValueError(f"Neznámý typ databáze: {db_type}")

def execute_query(db_type, query):
    """Provede jeden dotaz a vrátí dobu trvání v sekundách."""
    conn = None
    start_time = time.time()
    
    try:
        conn = get_connection(db_type)
        
        if db_type == "ClickHouse":
            # ClickHouse driver
            conn.execute(query)
        else:
            # Standardní DB-API (MSSQL, MariaDB, PostgreSQL)
            cursor = conn.cursor()
            cursor.execute(query)
            # Fetch all data to ensure query is fully processed
            cursor.fetchall()
            cursor.close()
            
    except Exception as e:
        print(f"❌ Chyba ({db_type}): {e}")
        return None
    finally:
        if conn:
            if db_type == "ClickHouse":
                conn.disconnect()
            else:
                conn.close()
                
    end_time = time.time()
    return end_time - start_time

def run_benchmark(db_type, concurrency, num_queries=5):
    """Spustí benchmark pro danou databázi a úroveň konkurence."""
    print(f"🚀 Spouštím test: {db_type} | Uživatelů: {concurrency}")
    
    queries = QUERIES[db_type]
    latencies = []
    
    # Pool vláken simuluje souběžné uživatele
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        
        # Každý "uživatel" spustí sadu dotazů
        for _ in range(concurrency):
            for q in queries:
                futures.append(executor.submit(execute_query, db_type, q))
        
        # Sběr výsledků
        for future in concurrent.futures.as_completed(futures):
            duration = future.result()
            if duration is not None:
                latencies.append(duration)
                
    if not latencies:
        print("⚠️ Žádné úspěšné dotazy.")
        return None

    # Statistiky
    avg_lat = statistics.mean(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    total_time = sum(latencies) # Toto je součet časů vláken, ne wall-clock time
    # Pro throughput potřebujeme wall-clock time celého testu, ale tady to zjednodušíme
    # Lepší by bylo měřit čas vně ThreadPoolExecutoru
    
    return {
        "Database": db_type,
        "Concurrency": concurrency,
        "Avg_Latency_s": round(avg_lat, 4),
        "P95_Latency_s": round(p95_lat, 4),
        "Min_Latency_s": round(min(latencies), 4),
        "Max_Latency_s": round(max(latencies), 4),
        "Total_Queries": len(latencies)
    }

# ==============================================================================
# 📊 HLAVNÍ SMYČKA
# ==============================================================================

import argparse
import os

# ... (imports remain the same, ensuring argparse and os are available)

# ==============================================================================
# 📊 HLAVNÍ SMYČKA
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Benchmark databází - souběžná zátěž")
    parser.add_argument("--db", type=str, help="Specifikujte databázi k testování (MSSQL, MariaDB, ClickHouse, PostgreSQL). Pokud neuvedeno, testují se všechny.", default=None)
    args = parser.parse_args()

    # Nastavení testu
    available_dbs = ["MSSQL", "MariaDB", "MariaDB_InnoDB", "ClickHouse", "PostgreSQL"]
    
    if args.db:
        if args.db not in available_dbs:
            print(f"❌ Neznámá databáze: {args.db}. Dostupné: {', '.join(available_dbs)}")
            return
        databases_to_test = [args.db]
    else:
        databases_to_test = available_dbs

    concurrency_levels = [1, 5, 10, 20]
    results = []
    csv_file = "benchmark_results.csv"
    
    print("==================================================")
    print("   BENCHMARK DATABÁZÍ - SOUBĚŽNÁ ZÁTĚŽ")
    print("==================================================")
    print(f"Testované databáze: {', '.join(databases_to_test)}")
    
    for db in databases_to_test:
        for users in concurrency_levels:
            start_wall_clock = time.time()
            
            stats = run_benchmark(db, users)
            
            end_wall_clock = time.time()
            total_duration = end_wall_clock - start_wall_clock
            
            if stats:
                # Přidáme throughput (Queries Per Second)
                stats["TPS"] = round(stats["Total_Queries"] / total_duration, 2)
                results.append(stats)
                print(f"   👉 TPS: {stats['TPS']} | Avg Latency: {stats['Avg_Latency_s']}s\n")
            
            # Pauza mezi testy
            time.sleep(2)

    # Načtení existujících výsledků, pokud existují, pro kombinovaný graf
    if os.path.exists(csv_file):
        try:
            existing_df = pd.read_csv(csv_file)
            # Odstraníme staré výsledky pro právě testované databáze, abychom je nahradili novými
            if not existing_df.empty:
                existing_df = existing_df[~existing_df['Database'].isin(databases_to_test)]
            
            # Spojíme staré a nové výsledky
            new_df = pd.DataFrame(results)
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            print(f"⚠️ Chyba při čtení existujícího CSV: {e}. Vytvářím nové.")
            final_df = pd.DataFrame(results)
    else:
        final_df = pd.DataFrame(results)

    print("\n📊 VÝSLEDKY (Aktualizované):")
    print(final_df)
    
        )
        return pyodbc.connect(conn_str)
    
    elif db_type == "MariaDB" or db_type == "MariaDB_InnoDB":
        return pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database']
        )
    
    elif db_type == "ClickHouse":
        # ClickHouse driver používá Client objekt, ne standardní DB-API 2.0 connection
        return Client(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database']
        )

    elif db_type == "PostgreSQL":
        conn = psycopg2.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            dbname=cfg['database']
        )
        # 🔧 FIX: Vypnutí paralelních workerů pro tento session.
        # Na Windows při vysoké konkurenci (20+ users) dochází k vyčerpání sdílené paměti ("No space left on device"),
        # pokud se každý dotaz snaží spustit více paralelních procesů.
        try:
            with conn.cursor() as cur:
                cur.execute("SET max_parallel_workers_per_gather = 0;")
            conn.commit()
        except Exception as e:
            print(f"⚠️ Nepodařilo se nastavit max_parallel_workers_per_gather: {e}")
        
        return conn
    
    raise ValueError(f"Neznámý typ databáze: {db_type}")

def execute_query(db_type, query):
    """Provede jeden dotaz a vrátí dobu trvání v sekundách."""
    conn = None
    start_time = time.time()
    
    try:
        conn = get_connection(db_type)
        
        if db_type == "ClickHouse":
            # ClickHouse driver
            conn.execute(query)
        else:
            # Standardní DB-API (MSSQL, MariaDB, PostgreSQL)
            cursor = conn.cursor()
            cursor.execute(query)
            # Fetch all data to ensure query is fully processed
            cursor.fetchall()
            cursor.close()
            
    except Exception as e:
        print(f"❌ Chyba ({db_type}): {e}")
        return None
    finally:
        if conn:
            if db_type == "ClickHouse":
                conn.disconnect()
            else:
                conn.close()
                
    end_time = time.time()
    return end_time - start_time

def run_benchmark(db_type, concurrency, num_queries=5):
    """Spustí benchmark pro danou databázi a úroveň konkurence."""
    print(f"🚀 Spouštím test: {db_type} | Uživatelů: {concurrency}")
    
    queries = QUERIES[db_type]
    latencies = []
    
    # Pool vláken simuluje souběžné uživatele
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        
        # Každý "uživatel" spustí sadu dotazů
        for _ in range(concurrency):
            for q in queries:
                futures.append(executor.submit(execute_query, db_type, q))
        
        # Sběr výsledků
        for future in concurrent.futures.as_completed(futures):
            duration = future.result()
            if duration is not None:
                latencies.append(duration)
                
    if not latencies:
        print("⚠️ Žádné úspěšné dotazy.")
        return None

    # Statistiky
    avg_lat = statistics.mean(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    total_time = sum(latencies) # Toto je součet časů vláken, ne wall-clock time
    # Pro throughput potřebujeme wall-clock time celého testu, ale tady to zjednodušíme
    # Lepší by bylo měřit čas vně ThreadPoolExecutoru
    
    return {
        "Database": db_type,
        "Concurrency": concurrency,
        "Avg_Latency_s": round(avg_lat, 4),
        "P95_Latency_s": round(p95_lat, 4),
        "Min_Latency_s": round(min(latencies), 4),
        "Max_Latency_s": round(max(latencies), 4),
        "Total_Queries": len(latencies)
    }

# ==============================================================================
# 📊 HLAVNÍ SMYČKA
# ==============================================================================

import argparse
import os
import seaborn as sns

# ... (imports remain the same, ensuring argparse and os are available)

# ==============================================================================
# 📊 HLAVNÍ SMYČKA
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Benchmark databází - souběžná zátěž")
    parser.add_argument("--db", type=str, help="Specifikujte databázi k testování (MSSQL, MariaDB, ClickHouse, PostgreSQL). Pokud neuvedeno, testují se všechny.", default=None)
    args = parser.parse_args()

    # Nastavení testu
    available_dbs = ["MSSQL", "MariaDB", "MariaDB_InnoDB", "ClickHouse", "PostgreSQL"]
    
    if args.db:
        if args.db not in available_dbs:
            print(f"❌ Neznámá databáze: {args.db}. Dostupné: {', '.join(available_dbs)}")
            return
        databases_to_test = [args.db]
    else:
        databases_to_test = available_dbs

    concurrency_levels = [1, 5, 10, 20]
    results = []
    csv_file = "benchmark_results.csv"
    
    print("==================================================")
    print("   BENCHMARK DATABÁZÍ - SOUBĚŽNÁ ZÁTĚŽ")
    print("==================================================")
    print(f"Testované databáze: {', '.join(databases_to_test)}")
    
    for db in databases_to_test:
        for users in concurrency_levels:
            start_wall_clock = time.time()
            
            stats = run_benchmark(db, users)
            
            end_wall_clock = time.time()
            total_duration = end_wall_clock - start_wall_clock
            
            if stats:
                # Přidáme throughput (Queries Per Second)
                stats["TPS"] = round(stats["Total_Queries"] / total_duration, 2)
                results.append(stats)
                print(f"   👉 TPS: {stats['TPS']} | Avg Latency: {stats['Avg_Latency_s']}s\n")
            
            # Pauza mezi testy
            time.sleep(2)

    # Načtení existujících výsledků, pokud existují, pro kombinovaný graf
    if os.path.exists(csv_file):
        try:
            existing_df = pd.read_csv(csv_file)
            # Odstraníme staré výsledky pro právě testované databáze, abychom je nahradili novými
            if not existing_df.empty:
                existing_df = existing_df[~existing_df['Database'].isin(databases_to_test)]
            
            # Spojíme staré a nové výsledky
            new_df = pd.DataFrame(results)
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            print(f"⚠️ Chyba při čtení existujícího CSV: {e}. Vytvářím nové.")
            final_df = pd.DataFrame(results)
    else:
        final_df = pd.DataFrame(results)

    print("\n📊 VÝSLEDKY (Aktualizované):")
    print(final_df)
    
    final_df.to_csv(csv_file, index=False)
    print(f"\n✅ Uloženo do {csv_file}")
    
    # Vykreslení grafu ze všech dat (i těch z předchozích běhů)
    if not final_df.empty:
      # Vykreslení grafu
    try:
        
        # Nastavení stylu
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
        palette = custom_colors if all(db in custom_colors for db in final_df['Database'].unique()) else "viridis"

        # Vytvoření barplotu
        chart = sns.barplot(
            data=final_df, 
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
        
        plt.savefig("benchmark_chart.png", dpi=300, bbox_inches='tight')
        print("✅ Graf uložen do benchmark_chart.png")
        
    except ImportError:
        print("⚠️ Knihovna seaborn není nainstalována. Generuji základní graf.")
        try:
            pivot_df = final_df.pivot(index="Concurrency", columns="Database", values="TPS")
            pivot_df.plot(kind='bar', figsize=(10, 6))
            plt.title("Porovnání propustnosti (TPS) při zátěži")
            plt.ylabel("Transakce za sekundu (TPS)")
            plt.xlabel("Počet souběžných uživatelů")
            plt.grid(axis='y')
            plt.tight_layout()
            plt.savefig("benchmark_chart.png")
            print("✅ Graf uložen do benchmark_chart.png")
        except Exception as e:
            print(f"⚠️ Nepodařilo se vykreslit graf: {e}")
    except Exception as e:
        print(f"⚠️ Chyba při generování grafu: {e}")

if __name__ == "__main__":
    main()
