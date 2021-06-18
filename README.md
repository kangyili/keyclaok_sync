# Keycloak_sync

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

Sync users with keycloak by providing a csv file.

## Features

- Sync users with csv files
- Export users to csv files
- Delete users from csv files
- Sync users from Google Object Stroage

## Tech

Keycloak_sync uses a number of open source projects to work properly:

- [python-keycloak]
- [pandas]
- [numpy]
- [PyYAML]
- [Cerberus]
- [coloredlogs]
- [click]
- [colorama]
- [google-cloud-storage]

And of course Keycloak_sync itself is open source with a [public repository](https://github.com/NOLANKANGYI/keyclaok_sync)
on GitHub.

## Installation

Keycloak_sync requires [python](https://python.org/) v3.8+ to run.

Install the dependencies and devDependencies and start the cli.

```sh
cd keycloak_sync
poetry install
poetry run entrypoint.py --help
```

## CLI

```sh
pip install keycloak_sync

kcctl --version
kcctl --help
kcctl sync --help
kcctl export --help
kcctl delete --help
```

### Sync

```shell
KEYCLOAK_SERVER_URL='https://keycloak.com/auth/' \
KEYCLOAK_REALM_NAME='keycloak-realm' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/template.yaml' \
CSV_FILE_NAME='~/users.csv' \
kcctl sync
```

### Delete

```shell
KEYCLOAK_SERVER_URL='https://keycloak.com/auth/' \
KEYCLOAK_REALM_NAME='keycloak-realm' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/template.yaml' \
kcctl delete
```

### Export

```shell
KEYCLOAK_SERVER_URL='https://keycloak.com/auth/' \
KEYCLOAK_REALM_NAME='keycloak-realm' \
KEYCLOAK_CLIENT_ID='keycloak-api' \
KEYCLOAK_CLIENT_SECRET='**********' \
CSV_FILE_TEMPLATE='~/template.yaml' \
CSV_FILE_NAME='~/users.csv' \
kcctl export
```

## Docker

Keycloak_sync is very easy to install and deploy in a Docker container.

By default, the Docker will expose port 8080, so change this within the
Dockerfile if necessary. When ready, simply use the Dockerfile to
build the image.

```sh
cd keycloak_sync
docker build -t <youruser>/Keycloak_sync:${package.version} .
```
