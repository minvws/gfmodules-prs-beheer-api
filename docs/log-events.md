# Log events

<!-- markdownlint-disable MD013 -->

Generated from `app.logging.events:Log` by `gfmodules.logging.event_overview`.
Do not edit by hand.

Each stream lists the events that reach it and the fields they carry there besides the context fields.
*any* means the event has no allow-list, so every field it is logged with reaches the stream.
*none* means the event carries only the context fields there.

## Context fields

Every event carries these on every stream, whenever the request context holds a value for them.

- `request_id`
- `ip`
- `user_agent`
- `client_trace_id`
- `correlation_id`
- `endpoint`
- `method`
- `scope`

The request context also holds these, but an event carries them only on the streams whose fields name them.

- `actor_cn`
- `organization_id`

## Stream `app`

| Event | Id | Level | Fields |
| --- | --- | --- | --- |
| `ORGANIZATION_REGISTERED` | 260400 | INFO | `actor_cn`, `organization_id`, `organization_identifier`, `scopes` |
| `ORGANIZATION_WITHDRAWN` | 260401 | WARNING | `actor_cn`, `organization_id`, `organization_identifier` |
| `CLIENT_REGISTERED` | 260402 | INFO | `actor_cn`, `organization_id`, `organization_identifier`, `acting_organization_identifiers`, `common_name`, `scopes` |
| `CLIENT_WITHDRAWN` | 260403 | WARNING | `actor_cn`, `organization_id`, `acting_organization_identifiers`, `organization_identifier` |
| `SCOPES_CHANGED` | 260404 | WARNING | `actor_cn`, `organization_id`, `organization_identifier`, `acting_organization_identifiers`, `changed_scopes` |
| `ONBOARDING_VALIDATION_FAILED` | 260405 | WARNING | `actor_cn`, `organization_id`, `error_reason` |
| `HEALTH_UNHEALTHY` | 270400 | ERROR | `component`, `status`, `error_detail` |
| `SYS_APP_STARTED` | 270401 | INFO | `version`, `config_path` |
| `SYS_APP_STOPPED` | 270402 | INFO | `shutdown_reason`, `last_exception_type` |
| `SYS_APP_CRASHED` | 270402 | CRITICAL | `shutdown_reason`, `last_exception_type` |
| `SYS_DB_CONNECTION_FAILED` | 270403 | ERROR | `error_type`, `retry_attempt`, `backoff_seconds` |
| `SYS_UNHANDLED_EXCEPTION` | 270404 | ERROR | `exception_type`, `endpoint`, `method`, `actor_cn`, `organization_id` |
| `SYS_MISSING_CORRELATION_ID` | 270428 | ERROR | `endpoint`, `method` |
| `ACCESS_REQUEST` | 100 | INFO | `endpoint`, `method`, `status_code`, `status_code_missing`, `duration_ms`, `body`, `body_truncated`, `actor_cn`, `organization_id` |

## Stream `siem`

| Event | Id | Level | Fields |
| --- | --- | --- | --- |
| `ORGANIZATION_REGISTERED` | 260400 | INFO | `actor_cn`, `organization_id`, `organization_identifier` |
| `ORGANIZATION_WITHDRAWN` | 260401 | WARNING | `actor_cn`, `organization_id`, `organization_identifier` |
| `CLIENT_REGISTERED` | 260402 | INFO | `actor_cn`, `organization_id`, `acting_organization_identifiers`, `organization_identifier`, `scopes` |
| `CLIENT_WITHDRAWN` | 260403 | WARNING | `actor_cn`, `organization_id`, `acting_organization_identifiers` |
| `SCOPES_CHANGED` | 260404 | WARNING | `actor_cn`, `organization_id`, `organization_identifier`, `acting_organization_identifiers` |
| `ONBOARDING_VALIDATION_FAILED` | 260405 | WARNING | `actor_cn`, `organization_id`, `error_reason` |
| `HEALTH_UNHEALTHY` | 270400 | ERROR | `component`, `status` |
| `SYS_APP_STOPPED` | 270402 | INFO | `shutdown_reason` |
| `SYS_APP_CRASHED` | 270402 | CRITICAL | `shutdown_reason` |
| `SYS_DB_CONNECTION_FAILED` | 270403 | ERROR | `error_type` |
| `SYS_UNHANDLED_EXCEPTION` | 270404 | ERROR | `exception_type`, `endpoint`, `method`, `actor_cn`, `organization_id` |

## Access event ids per route

`ACCESS_REQUEST` carries these ids instead of its own on these routes.

| Method | Route | Id |
| --- | --- | --- |
| POST | `/organizations` | 260700 |
| PUT | `/organizations/{id}` | 260701 |
| DELETE | `/organizations/{id}` | 260702 |
| POST | `/organizations/{organization_id}/clients` | 260703 |
| PUT | `/organizations/{organization_id}/clients/{id}` | 260704 |
| DELETE | `/organizations/{organization_id}/clients/{id}` | 260705 |
