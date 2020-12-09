# Install

Create a account on https://nexus.polynom.io

```shell
pip install --extra-index-url=https://<Your login name>:<Your Password>@nexus.polynom.io/repository/polynom-pypi-all/simple keycloak_sync
```

# Run

```shell
# kcctl = keycloak control
kcctl --version
kcctl --help
kcctl sync --help
kcctl export --help
kcctl delete --help
kcctl dropall --help
```

# Example

## Export

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/bm-template.yaml' \
OUTPUT_FILE_PATH='~/output.csv' \
kcctl export
```

## Delete

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/bm-template.yaml' \
kcctl delete
```

## Sync

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/bm-template.yaml' \
CSV_FILE_NAME='~/test.csv' \
kcctl sync
```

## Drop all

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
kcctl dropall
```
