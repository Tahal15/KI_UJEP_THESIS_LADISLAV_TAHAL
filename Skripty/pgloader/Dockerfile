FROM dimitri/pgloader:latest
WORKDIR /data
COPY mariadb_to_pg.load /data/mariadb_to_pg.load
ENTRYPOINT ["pgloader", "/data/mariadb_to_pg.load"]
