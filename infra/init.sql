-- Local socket initialization by the PostgreSQL image on a new volume.
\getenv app_password KLOWB_DB_PASSWORD
\getenv migration_password KLOWB_MIGRATION_PASSWORD
CREATE ROLE klowb LOGIN PASSWORD :'app_password';
CREATE ROLE klowb_migrate LOGIN PASSWORD :'migration_password';
ALTER DATABASE klowb OWNER TO klowb_migrate;
REVOKE ALL ON DATABASE klowb FROM PUBLIC;
GRANT CONNECT ON DATABASE klowb TO klowb;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO klowb;
ALTER DEFAULT PRIVILEGES FOR ROLE klowb_migrate IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO klowb;
ALTER DEFAULT PRIVILEGES FOR ROLE klowb_migrate IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO klowb;
