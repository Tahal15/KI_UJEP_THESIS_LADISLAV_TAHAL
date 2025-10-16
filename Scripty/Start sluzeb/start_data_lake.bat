@echo off
echo Spousteni SQL Server sluzeb...

net start "SQL Server Agent (DATA_LAKE)"
net start "SQL Server (DATA_LAKE)"
net start "SQL Server Integration Services 16.0"
net start "SQL Server Launchpad (DATA_LAKE)"
net start "SQL Full-text Filter Daemon Launcher (DATA_LAKE)"
net start "SQL Server Browser"

echo Vsechny sluzby byly spusteny.
pause
