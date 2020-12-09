FROM python:3.8-slim

CMD pip install --extra-index-url='https://$NEXUS_LOGIN:$NEXUS_PASSWORD/repository/polynom-pypi-all/simple keycloak_sync' && \
    kcctl sync  