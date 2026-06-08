CREATE TABLE scopes (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_scopes_name UNIQUE (name)
);

CREATE TABLE organization_scopes (
    organization_id UUID NOT NULL REFERENCES organizations(id),
    scope_id UUID NOT NULL REFERENCES scopes(id),
    PRIMARY KEY (organization_id, scope_id)
);

CREATE TABLE client_scopes (
    client_id UUID NOT NULL REFERENCES clients(id),
    scope_id UUID NOT NULL REFERENCES scopes(id),
    PRIMARY KEY (client_id, scope_id)
);
