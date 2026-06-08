-- organizations: replace oin/common_name/client_certificate with register_id/name
ALTER TABLE organizations
    DROP COLUMN oin,
    DROP COLUMN common_name,
    DROP COLUMN client_certificate,
    ADD COLUMN register_id VARCHAR NOT NULL,
    ADD COLUMN name VARCHAR NOT NULL;

CREATE UNIQUE INDEX uq_organizations_register_id_active
    ON organizations (register_id)
    WHERE deleted_at IS NULL;

-- clients: add mandate_id and replace unique index
ALTER TABLE clients
    ADD COLUMN mandate_id VARCHAR NOT NULL;

DROP INDEX uq_clients_org_oin_active;

CREATE UNIQUE INDEX uq_clients_org_mandate_active
    ON clients (organization_id, mandate_id)
    WHERE deleted_at IS NULL;
