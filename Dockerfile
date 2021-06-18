FROM python:3.8-slim
RUN pip keycloak_sync
CMD kcctl bksync -vvv