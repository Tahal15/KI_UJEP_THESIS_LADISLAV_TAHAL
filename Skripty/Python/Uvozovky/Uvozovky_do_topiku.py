#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Přidá uvozovky ke všem topicům ve slovníku manual_groups = { ... }
a zapíše každou skupinu (např. 1:, 5:, 7:) na nový řádek.
Každá skupina je v jednom řádku, položky uvnitř ní jsou odděleny čárkami.
"""

import os
import re

# Cesty k souborům (ve stejné složce jako skript)
base_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(base_dir, "manual_groups.txt")
OUTPUT_FILE = os.path.join(base_dir, "manual_groups_formatted.txt")

# Načti původní obsah
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = f.read()

# Najde každou skupinu (např. "1: [ ... ]")
pattern = re.compile(r"(\d+)\s*:\s*\[(.*?)\]", re.DOTALL)

output_lines = ["manual_groups = {"]

for match in pattern.finditer(data):
    gid = match.group(1)
    content = match.group(2)

    # Rozdělí jednotlivé topicy
    items = [i.strip() for i in content.split(",") if i.strip()]
    quoted = [f'"{i}"' if not (i.startswith('"') and i.endswith('"')) else i for i in items]
    line = f"    {gid}: [{', '.join(quoted)}],"
    output_lines.append(line)

output_lines.append("}")

# Zápis výstupu
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("✅ Hotovo!")
print(f"📥 Vstup: {INPUT_FILE}")
print(f"📤 Výstup: {OUTPUT_FILE}")
