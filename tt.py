import sys

import click
from keycloak import KeycloakAdmin

kc_admin = KeycloakAdmin(server_url='https://keycloak.int-pripolis.polynom.io/auth/',
                         client_id='keycloak-api',
                         realm_name='test-kc-api',
                         client_secret_key='d7633839-7e69-483e-a30c-d8b8c4632d62',
                         verify=True)

l = list(map(lambda x: x['name'], kc_admin.get_realm_roles()))
user = kc_admin.get_user(user_id='0041a29f-d541-4e1a-ac8b-cdbf781cc6c7')
print(
    dict(map(lambda item: (item[0], ''.join(item[1])), user['attributes'].items())))
