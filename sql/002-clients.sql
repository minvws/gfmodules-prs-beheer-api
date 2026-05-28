CREATE TABLE clients (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    oin VARCHAR NOT NULL,
    common_name VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_clients_org_oin_active ON clients (organization_id, oin) WHERE deleted_at IS NULL;
