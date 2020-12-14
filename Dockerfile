FROM python:3.8-slim

ARG NEXUS_USER
ARG NEXUS_PASSWORD
RUN pip install --extra-index-url=https://$NEXUS_USER:$NEXUS_PASSWORD@nexus.polynom.io/repository/polynom-pypi-all/simple keycloak_sync
CMD kcctl bksync -vvv