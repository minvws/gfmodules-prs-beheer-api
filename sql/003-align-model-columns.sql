ALTER TABLE organizations DROP COLUMN common_name;
ALTER TABLE organizations DROP COLUMN client_certificate;

ALTER TABLE organizations ADD COLUMN name VARCHAR NOT NULL DEFAULT '';
ALTER TABLE organizations ALTER COLUMN name DROP DEFAULT;
ALTER TABLE organizations ADD COLUMN authorizations VARCHAR;

ALTER TABLE clients ADD COLUMN certificate TEXT;
ALTER TABLE clients ADD COLUMN allowed_scopes VARCHAR;
