import re

# Cesty k souborům
input_file = "mariadb_dump.sql"  # Změň na svůj vstupní soubor
output_file = "mssql_converted.sql"

# Přepínače pro režimy
inside_insert = False

# Otevření souborů
with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        # Převod CREATE TABLE
        if "CREATE TABLE `mqttentries`" in line:
            outfile.write("CREATE TABLE mqttentries (\n")
            continue
        elif "ENGINE=InnoDB" in line:
            outfile.write(");\n")  # Ukončení CREATE TABLE
            continue
        elif "AUTO_INCREMENT" in line:
            line = re.sub(r"AUTO_INCREMENT", "IDENTITY(1,1)", line)
        elif "timestamp NOT NULL DEFAULT current_timestamp()" in line:
            line = re.sub(r"timestamp NOT NULL DEFAULT current_timestamp\(\)", "DATETIME2 NOT NULL DEFAULT GETDATE()", line)
        elif "tinytext NOT NULL" in line or "text NOT NULL" in line:
            line = re.sub(r"tinytext NOT NULL", "NVARCHAR(255) NOT NULL", line)
            line = re.sub(r"text NOT NULL", "NVARCHAR(MAX) NOT NULL", line)
        elif "KEY " in line:
            continue  # MS SQL definuje indexy jinak, přeskočíme

        # Převod INSERT INTO
        if "INSERT INTO `mqttentries` VALUES" in line:
            if not inside_insert:
                outfile.write("SET IDENTITY_INSERT mqttentries ON;\n")
                inside_insert = True
            line = line.replace("INSERT INTO `mqttentries` VALUES", "INSERT INTO mqttentries (id, time, topic, payload) VALUES")
        
        # Převod JSON stringů do NVARCHAR (N'...')
        line = re.sub(r"'(\{.*\})'", r"N'\1'", line)

        # Převod uzávorkování u JSON textu
        line = line.replace("\\'", "''")  # Escape apostrofů pro MS SQL

        outfile.write(line)

    # Ukončení IDENTITY_INSERT
    if inside_insert:
        outfile.write("SET IDENTITY_INSERT mqttentries OFF;\n")

print(f"Konverze dokončena! Upravený soubor: {output_file}")
