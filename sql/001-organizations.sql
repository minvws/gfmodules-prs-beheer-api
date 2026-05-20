CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    oin VARCHAR NOT NULL,
    common_name VARCHAR NOT NULL,
    client_certificate TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP
);

ALTER TABLE organizations OWNER TO prs_beheer_api_dba;
GRANT SELECT, INSERT, UPDATE ON organizations TO prs_beheer_api;

CREATE UNIQUE INDEX uq_organizations_oin_active ON organizations (oin) WHERE deleted_at IS NULL;
