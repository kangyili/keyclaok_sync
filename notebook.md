# Add users

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='d7633839-7e69-483e-a30c-d8b8c4632d62' \
CSV_FILE='/Users/kangyi/Dropbox/Polynom/keycloak_sync/test1.csv' \
poetry run python3 entrypoint.py  sync
```

```shell
poetry run python3 entrypoint.py  sync --kc-url 'https://keycloak.int-pripolis.polynom.io/auth/' --kc-realm 'test-kc-api' --kc-clt 'keycloak-api' --kc-clt-sct 'd7633839-7e69-483e-a30c-d8b8c4632d62' -f '/Users/kangyi/Dropbox/Polynom/keycloak_sync/test1.csv'
```

# Purge users

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='d7633839-7e69-483e-a30c-d8b8c4632d62' \
poetry run python3 entrypoint.py  purge
```

# Export users

```shell
KEYCLOAK_SERVER_URL='https://keycloak.int-pripolis.polynom.io/auth/' \
KEYCLOAK_REALM_NAME='test-kc-api' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='d7633839-7e69-483e-a30c-d8b8c4632d62' \
poetry run python3 entrypoint.py  export -d './example.csv'
```
