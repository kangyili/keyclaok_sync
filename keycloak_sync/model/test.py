from keycloak import KeycloakAdmin
import pandas as pd
from datetime import datetime
# import pandas as pd

# data = pd.read_csv(filepath_or_buffer='/Users/kangyi/Polynom/keycloak_sync/test1.csv',
#                    sep=';', header=0)
# print(list(data.columns.values[0:9]))

kc_admin = KeycloakAdmin(server_url='https://keycloak.int-pripolis.polynom.io/auth/',
                         client_id='keycloak-api',
                         realm_name='test-kc-api',
                         client_secret_key='d7633839-7e69-483e-a30c-d8b8c4632d62',
                         verify=True)
# if kc_admin.get_user_id('example@example.com'):
#     print(id)
# new_user = kc_admin.create_user({"email": "example@essssxample.com",
#                                  "username": "example@essxample.com",
#                                  "enabled": True,
#                                  "emailVerified": True,
#                                  "firstName": "Exasssmple",
#                                  "lastName": "Example",
#                                  "attributes": {
#                                      "usage": "test",
#                                      "name": "idk"
#                                  },
#                                  "credentials": [{"value": "secret", "type": "password", }],
#                                  "realmRoles": ['admin', ]
#                                  })
# print(kc_admin.get_user_id("example@example.com")
# print(kc_admin.get_realm_role('admin')['id'])
# kc_admin.assign_realm_roles(user_id='8c309568-5347-42e9-9447-2b5c891596b3',
#                             client_id='keycloak-api',
#                             roles=[{'id': 'afe8abb4-57af-4b8c-8d95-41bf645cb926', 'name': 'VALIDATION_DA'}])
# print(kc_admin.get_users()[0]['username'])
x = ['Date activation de compte', 'Date désactivation de compte',
     'Code(s) agence(s)', 'Libellé(s) agence(s)', 'Profil', 'Prénom',
     'Nom', 'Mail', 'Mot de passe']
# data = {}
# for column in x:
#     data[column] = []
# users = kc_admin.get_users()
# for user in users:
#     data['']

# print(datetime.fromtimestamp(
#     int(str(users['createdTimestamp'])[:10])).strftime('%d/%m/%y'))
# print(kc_admin.get_user('ab19229d-bc71-40f7-a220-c111d9757745'))
# print(kc_admin.get_realm_role_members('VALIDATION_DA'))
print(kc_admin.get_user('hhhhh'))
# print(user)
