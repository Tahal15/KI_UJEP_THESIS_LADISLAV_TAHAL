/*
=================================================
 SKRIPT PRO VYMAZÁNÍ DAT PŘED ETL TESTY
 Cílová databáze: datovy_sklad (PostgreSQL/TimescaleDB)
 Poznámka: DimTime se NEVYMAZÁVÁ.
=================================================
*/

-- 1. Zastavení TimescaleDB automatického indexování pro Hypertable (FactCameraDetection)
-- I když by TRUNCATE měl fungovat bez tohoto kroku, je to dobrý bezpečnostní zvyk.
SELECT mttgueries.set_chunk_time_interval('FactCameraDetection', NULL::interval);


-- 2. Rychlé vymazání dat (TRUNCATE) ze všech dimenzí a faktů.
-- Používáme RESTART IDENTITY, aby se auto-inkrementální čítače (klíče) vynulovaly,
-- a WITH CONTINUITY, aby se zachovaly speciální záznamy (např. klíč -1 'Unknown').

TRUNCATE TABLE mttgueries.DimCity RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.DimSensor RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.DimLP RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.DimDetectionType RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.DimVehicleClass RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.DimCountry RESTART IDENTITY CASCADE;
TRUNCATE TABLE mttgueries.FactCameraDetection RESTART IDENTITY CASCADE;


-- 3. Obnovení klíče -1 ('Unknown') do vymazaných dimenzí
-- TRUNCATE RESTART IDENTITY vynuluje čítače, ale neobnoví ty naše ručně vložené záznamy s klíčem -1.
-- Musíme je vložit zpět.

INSERT INTO mttgueries.DimCity (CityKey, CityName) VALUES (-1, 'Unknown');
INSERT INTO mttgueries.DimSensor (SensorKey, SensorCode) VALUES (-1, 'Unknown');
INSERT INTO mttgueries.DimLP (LPKey, LicensePlate) VALUES (-1, 'Unknown');
INSERT INTO mttgueries.DimDetectionType (DetectionTypeKey, DetectionType) VALUES (-1, 'Unknown');
INSERT INTO mttgueries.DimVehicleClass (VehicleClassKey, VehicleClass) VALUES (-1, 'Unknown');
INSERT INTO mttgueries.DimCountry (CountryKey, CountryCode) VALUES (-1, 'Unknown');


-- 4. Resetování ETL kontrolní tabulky (pro plný re-run ETL)
-- Tímto zajistíme, že ETL skript začne načítat data od začátku (od ID 0).
TRUNCATE TABLE ETL_IncrementalControl;


-- 5. Nastavení časového indexování Hypertable zpět na 7 dní
SELECT mttgueries.set_chunk_time_interval('factcameradetection', INTERVAL '7 days');


/*
=================================================
 TABULKY VYMAZÁNY A PŘIPRAVENY PRO NOVÝ TEST.
=================================================
*/