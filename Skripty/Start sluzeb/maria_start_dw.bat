@echo off
echo Spoustim sluzbu MariaDB2...

net start MariaDB2

if %errorlevel% equ 0 (
    echo Služba MariaDB2 byla úspěšně spuštěna.
) else (
    echo Nastala chyba při spouštění služby MariaDB2.
)

pause
