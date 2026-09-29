# Using the administration API

This document describes how to register organizations, certificates,
and clients in the Beheer API. It provides step-by-step instructions for
setting up a new client so it can connect to the PRS.

To connect to the PRS, a client must be registered in the Beheer API.
This involves creating an organization, generating a certificate, and
registering the client with the required scopes and personal ID types.

The following scopes are available for use in the Beheer API:

- **prs:administration**: Grants administrative access to manage organization
  keys and secrets
- **prs:pseudonym**: Allows requesting and receiving pseudonyms
- **prs:oprf-pseudonym**: Enables OPRF (Oblivious Pseudorandom Function)
  pseudonym operations
- **prs:saml-pseudonym**: Permits SAML-based pseudonym operations

Choose the appropriate scopes based on your organization's requirements and the
services you need to access.

Follow the steps below to complete the registration process.

## Registration

Complete the following steps in order:

1. **Create an organization** — Register the organization that will
   own the clients and certificates.
2. **Generate a certificate** — Create a client certificate used
   for authentication with the Beheer API.
3. **Register a client** — Create the client with the required
   scopes and link it to the certificate for access.

### Step 1: Create an organization

Use the following **example** command to register a new organization. Replace
the relevant example values with your actual organization-specific values:

```shell
curl 'https://example.com/organizations' \
  --cert client.crt \
  --key client.key \
  -H 'content-type: application/json' \
  --data-raw $'{
  "external_id": "00000099441528631000",
  "name": "Org name",
  "scopes": [
    "prs:administration",
    "prs:pseudonym",
    "prs:oprf-pseudonym",
    "prs:saml-pseudonym"
  ],
  "receive_personal_id_types": [
    "oprf", "reversible_pseudonym", "irreversible_pseudonym"
  ],
  "request_personal_id_types": [
    "oprf", "reversible_pseudonym", "irreversible_pseudonym"
  ]
}'
```

### Step 2: Generate a certificate

Use the following **example** command once the organization is created to
register a new certificate using the organization's unique identifier. Replace the
relevant example values with your actual organization-specific values:

```shell
curl 'https://example.com/organizations/6054e0f0-7147-43db-816a-3a850c03b0ac/certificates' \
  --cert client.crt \
  --key client.key \
  -H 'content-type: application/json' \
  --data-raw $'{
  "organization_identifier": "00000099441528631000",
  "domain": "certificate-CN-or-SAN"
}'
```

### Step 3: Register a client

Use the following **example** command once the organization is created to
register a new client using the organization's and certificate's unique
identifier. Replace the relevant example values with your actual
organization-specific values:

```shell
curl 'https://example.com/organizations/6054e0f0-7147-43db-816a-3a850c03b0ac/clients' \
  --cert client.crt \
  --key client.key \
  -H 'content-type: application/json' \
  --data-raw $'{
  "scopes": [
    "prs:administration",
    "prs:pseudonym",
    "prs:oprf-pseudonym",
    "prs:saml-pseudonym"
  ],
  "request_personal_id_types": [
    "oprf", "reversible_pseudonym", "irreversible_pseudonym"
  ],
  "certificates": ["84e343df-a42d-4866-accc-43e37d212288"]
}'
```
