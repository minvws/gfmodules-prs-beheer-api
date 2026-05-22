CREATE TABLE clients (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    oin VARCHAR NOT NULL,
    common_name VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP
);

ALTER TABLE clients OWNER TO prs_beheer_api_dba;
GRANT SELECT, INSERT, UPDATE ON clients TO prs_beheer_api;

CREATE UNIQUE INDEX uq_clients_org_oin_active ON clients (organization_id, oin) WHERE deleted_at IS NULL;
