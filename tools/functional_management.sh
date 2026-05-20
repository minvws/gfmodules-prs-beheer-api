#!/usr/bin/env bash

set -euo pipefail

GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
BOLD="\033[1m"
DIM="\033[2m"
RED="\033[31m"
NC="\033[0m"

APP_URL="${FUNCTIONAL_MANAGEMENT_APP_URL:-http://localhost:8512}"
ORGANIZATIONS_ENDPOINT="$APP_URL/organizations"
OUTPUT_FORMAT="json"

function usage() {
    echo -e "Usage: ./functional_management.sh <command> [options]\n"
    echo -e "Commands:"
    echo -e "  help                        Show this help message"
    echo -e "  list                        List all Organisaties"
    echo -e "  add    [options]            Add a new Organisatie"
    echo -e "  get    <id>                 Get an Organisatie by UUID"
    echo -e "  update <id> [options]       Update an Organisatie"
    echo -e "  remove <id> [-y|--yes]      Remove an Organisatie (skip confirmation)"
    echo -e "  set-url <url>               Print the export command to set the app URL"
    echo -e ""
    echo -e "Output format (for commands that return data):"
    echo -e "  --pretty-json               Pretty-print JSON output (default)"
    echo -e "  --table                     Render output as a table (if supported tools (jq and column, or miller, or python3) are available)"
    echo -e ""
    echo -e "Options for add / update:"
    echo -e "  --oin                <value>  OIN number"
    echo -e "  --common-name        <value>  Common name"
    echo -e "  --client-certificate <value>  Client certificate for mTLS (optional)"
    echo -e ""
    echo -e "App URL (current: ${CYAN}${APP_URL}${NC}):"
    echo -e "  Set via env var : ${DIM}export FUNCTIONAL_MANAGEMENT_APP_URL=<url>${NC}"
    echo -e "  Or run          : ${DIM}eval \$(./functional_management.sh set-url <url>)${NC}"
}

function die() {
    echo -e "${RED}Error: $*${NC}" >&2
    exit 1
}

MISSING_ARGS=()

function require_arg() {
    local flag="$1"
    local value="$2"
    if [[ -z "$value" ]]; then
        MISSING_ARGS+=("--${flag}")
    fi
}

function assert_no_missing_args() {
    if [[ ${#MISSING_ARGS[@]} -gt 0 ]]; then
        for arg in "${MISSING_ARGS[@]}"; do
            echo -e "${RED}Error: Missing required option: ${arg}${NC}" >&2
        done
        exit 1
    fi
}

function pretty_json() {
    if command -v python3 &>/dev/null; then
        python3 -m json.tool
    else
        cat
    fi
}

function render_output() {
    local json="$1"
    echo
    if [[ "$OUTPUT_FORMAT" == "table" ]]; then
        if command -v mlr &>/dev/null; then
            echo "$json" | mlr --ijson --opprint --barred cat
            return
        fi
        if command -v jq &>/dev/null && command -v column &>/dev/null; then
            echo "$json" | jq -r 'if type == "object" then [.] else . end | (.[0] | keys), (.[] | [.[] | tostring]) | @tsv' | column -t -s $'\t'
        elif command -v python3 &>/dev/null; then
            echo "$json" | python3 -c "
import json, sys

data = json.load(sys.stdin)
if isinstance(data, dict):
    data = [data]

if not data:
    print('(no results)')
    sys.exit(0)

keys = list(data[0].keys())
widths = {k: len(k) for k in keys}
for row in data:
    for k in keys:
        widths[k] = max(widths[k], len(str(row.get(k, ''))))

header = '  '.join(k.ljust(widths[k]) for k in keys)
sep    = '  '.join('-' * widths[k] for k in keys)
print(header)
print(sep)
for row in data:
    print('  '.join(str(row.get(k, '')).ljust(widths[k]) for k in keys))
"
        else
            echo -e "${YELLOW}Warning: No suitable tool found for table output. \n I tried miller, jq with column and python3. Falling back to pretty JSON.${NC}\n" >&2
            echo "$json" | pretty_json
        fi
    else
        echo "$json" | pretty_json
    fi
}

function http_request() {
    local method="$1"
    local url="$2"
    local data="${3:-}"

    if [[ -n "$data" ]]; then
        curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -w "\n%{http_code}" -X "$method" "$url"
    fi
}

function split_response() {
    local raw="$1"
    HTTP_CODE=$(echo "$raw" | tail -1)
    BODY=$(echo "$raw" | sed '$d')
}

function health_check() {
    echo -e "${GREEN}Performing health check...${NC}"
    if curl -s -f "$APP_URL/health" >/dev/null; then
        echo -e "${GREEN}App is healthy!${NC}"
    else
        echo -e "${YELLOW}App is not responding. Check if the app is running at ${APP_URL}${NC}"
        exit 1
    fi
}

function parse_organization_args() {
    OIN="" COMMON_NAME="" CLIENT_CERTIFICATE=""
    MISSING_ARGS=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --oin)                OIN="$2";                shift 2 ;;
            --common-name)        COMMON_NAME="$2";        shift 2 ;;
            --client-certificate) CLIENT_CERTIFICATE="$2"; shift 2 ;;
            *) die "Unknown option: $1" ;;
        esac
    done

    require_arg "oin"         "$OIN"
    require_arg "common-name" "$COMMON_NAME"
    assert_no_missing_args
}

function build_payload() {
    if [[ -n "$CLIENT_CERTIFICATE" ]]; then
        cat <<EOF
{
  "oin": "$OIN",
  "common_name": "$COMMON_NAME",
  "client_certificate": "$CLIENT_CERTIFICATE"
}
EOF
    else
        cat <<EOF
{
  "oin": "$OIN",
  "common_name": "$COMMON_NAME"
}
EOF
    fi
}

function cmd_list() {
    echo -e "${GREEN}Getting all Organisaties...${NC}"
    local raw
    raw=$(http_request GET "$ORGANIZATIONS_ENDPOINT")
    split_response "$raw"

    case "$HTTP_CODE" in
        200) render_output "$BODY" ;;
        *)   echo -e "${RED}Failed (HTTP $HTTP_CODE):${NC}"; echo "$BODY"; exit 1 ;;
    esac
}

function cmd_add() {
    parse_organization_args "$@"

    echo -e "${GREEN}Adding a new Organisatie...${NC}"
    local raw
    raw=$(http_request POST "$ORGANIZATIONS_ENDPOINT" "$(build_payload)")
    split_response "$raw"

    if [[ "$HTTP_CODE" -eq 200 || "$HTTP_CODE" -eq 201 ]]; then
        echo -e "${GREEN}Organisatie added successfully:${NC}"
        render_output "$BODY"
    else
        echo -e "${RED}Failed (HTTP $HTTP_CODE):${NC}"
        render_output "$BODY"
        exit 1
    fi
}

function cmd_get() {
    local id="${1:-}"
    if [[ -z "$id" ]]; then die "Usage: $0 get <id>"; fi

    echo -e "${GREEN}Getting Organisatie ${id}...${NC}"
    local raw
    raw=$(http_request GET "$ORGANIZATIONS_ENDPOINT/$id")
    split_response "$raw"

    case "$HTTP_CODE" in
        200) render_output "$BODY" ;;
        404) echo -e "${YELLOW}Organisatie not found.${NC}"; exit 1 ;;
        *)   echo -e "${RED}Failed (HTTP $HTTP_CODE):${NC}"; echo "$BODY"; exit 1 ;;
    esac
}

function cmd_update() {
    local id="${1:-}"
    if [[ -z "$id" ]]; then die "Usage: $0 update <id> [options]"; fi
    shift

    parse_organization_args "$@"

    echo -e "${GREEN}Updating Organisatie ${id}...${NC}"
    local raw
    raw=$(http_request PUT "$ORGANIZATIONS_ENDPOINT/$id" "$(build_payload)")
    split_response "$raw"

    case "$HTTP_CODE" in
        200) echo -e "${GREEN}Organisatie updated successfully:${NC}"; render_output "$BODY" ;;
        404) echo -e "${YELLOW}Organisatie not found.${NC}"; exit 1 ;;
        *)   echo -e "${RED}Failed (HTTP $HTTP_CODE):${NC}"; render_output "$BODY"; exit 1 ;;
    esac
}

function cmd_remove() {
    local id="${1:-}"
    if [[ -z "$id" ]]; then die "Usage: $0 remove <id> [-y]"; fi

    local skip_confirm=false
    if [[ "${2:-}" == "-y" || "${2:-}" == "--yes" ]]; then
        skip_confirm=true
    fi

    echo -e "${YELLOW}Removing Organisatie ${id}...${NC}"
    if [[ "$skip_confirm" == false ]]; then
        read -rp "Are you sure? [y/N] " confirm
        [[ "$confirm" =~ ^[yY]$ ]] || { echo -e "${YELLOW}Aborted.${NC}"; exit 0; }
    fi

    local raw
    raw=$(http_request DELETE "$ORGANIZATIONS_ENDPOINT/$id")
    split_response "$raw"

    case "$HTTP_CODE" in
        204) echo -e "${GREEN}Organisatie removed successfully.${NC}" ;;
        404) echo -e "${YELLOW}Organisatie not found.${NC}"; exit 1 ;;
        *)   echo -e "${RED}Failed (HTTP $HTTP_CODE):${NC}"; echo "$BODY"; exit 1 ;;
    esac
}

function cmd_set_url() {
    local url="${1:-}"
    if [[ -z "$url" ]]; then die "Usage: $0 set-url <url>"; fi
    echo "export FUNCTIONAL_MANAGEMENT_APP_URL=$url"
}

function main() {
    local cmd="${1:-}"
    if [[ -z "$cmd" ]]; then
        echo -e "${YELLOW}No command given.${NC}  Run with 'help' to see available commands."
        exit 1
    fi
    shift || true

    local filtered_args=()
    for arg in "$@"; do
        case "$arg" in
            --pretty-json) OUTPUT_FORMAT="json" ;;
            --table)       OUTPUT_FORMAT="table" ;;
            *)             filtered_args+=("$arg") ;;
        esac
    done
    set -- "${filtered_args[@]+"${filtered_args[@]}"}"

    case "$cmd" in
        help | --help | -h) usage ;;
        list)    cmd_list    "$@" ;;
        add)     cmd_add     "$@" ;;
        get)     cmd_get     "$@" ;;
        update)  cmd_update  "$@" ;;
        remove)  cmd_remove  "$@" ;;
        set-url) cmd_set_url "$@" ;;
        *)
            echo -e "${RED}Unknown command: ${cmd}${NC}  (run 'help' for usage)"
            exit 1
            ;;
    esac
}

cmd="${1:-}"
if [[ -z "$cmd" || "$cmd" == "help" || "$cmd" == "--help" || "$cmd" == "-h" ]]; then
    echo -e "${BOLD}${CYAN}"
    echo -e "  ██████╗ ██████╗ ███████╗    ██████╗ ███████╗██╗  ██╗███████╗███████╗██████╗ "
    echo -e "  ██╔══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║  ██║██╔════╝██╔════╝██╔══██╗"
    echo -e "  ██████╔╝██████╔╝███████╗    ██████╔╝█████╗  ███████║█████╗  █████╗  ██████╔╝"
    echo -e "  ██╔═══╝ ██╔══██╗╚════██║    ██╔══██╗██╔══╝  ██╔══██║██╔══╝  ██╔══╝  ██╔══██╗"
    echo -e "  ██║     ██║  ██║███████║    ██████╔╝███████╗██║  ██║███████╗███████╗██║  ██║"
    echo -e "  ╚═╝     ╚═╝  ╚═╝╚══════╝    ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "  ${BOLD}Organisatie Management CLI${NC}  ${DIM}│  ${APP_URL}${NC}"
    echo -e ""
fi
if [[ "$cmd" != "set-url" && "$cmd" != "help" && "$cmd" != "--help" && "$cmd" != "-h" && -n "$cmd" ]]; then
    health_check
    echo -e ""
fi
main "$@"
