FROM postgres:16
COPY --chmod=0644 infra/init.sql /docker-entrypoint-initdb.d/10-klowb.sql
