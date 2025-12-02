@echo off
echo Spousteni SQL Server sluzeb pro instanci DATA_WAREHOUSE...

net start "SQL Server Agent (DATA_WAREHOUSE)"
net start "SQL Server (DATA_WAREHOUSE)"
net start "SQL Server Analysis Services (DATA_WAREHOUSE)"
net start "SQL Server Launchpad (DATA_WAREHOUSE)"
net start "SQL Full-text Filter Daemon Launcher (DATA_WAREHOUSE)"
net start "SQL Server Browser"

echo Vsechny sluzby byly spusteny.
pause
