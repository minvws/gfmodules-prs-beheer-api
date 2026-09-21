# Using the administration API.

## Summary

This document contains the documentation how organizations and clients are administrated in this Beheer API.


## Registration of new clients

An organization can be created using the following command:

```bash
curl 'https://pseudoniemendienst.beheer.test.gf.irealisatie.nl/organizations' \
  --cert client.crt \
  --key client.key \
  -H 'content-type: application/json' \
  --data-raw $'{
  "external_id": "00000009441528631000",
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

A certificate can be created using:

```bash
curl 'https://pseudoniemendienst.beheer.test.gf.irealisatie.nl/organizations/6054e0f0-7147-43db-816a-3a850c03b0ac/certificates' \
  --cert client.crt \
  --key client.key \
  -H 'content-type: application/json' \
  --data-raw $'{
  "organization_identifier": "00000009441528631000",
  "domain": "certificate-CN-or-SAN"
}
```

A client can be created using:

```bash
curl 'https://pseudoniemendienst.beheer.test.gf.irealisatie.nl/organizations/6054e0f0-7147-43db-816a-3a850c03b0ac/clients' \
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
