import pandas as pd

from keycloak_sync.model.bmcsvfile import BMcsvfile
from keycloak_sync.model.kc import Keycloak

# b = BMcsvfile('/Users/kangyi/Dropbox/Polynom/keycloak_sync/test1.csv')
# users = b.readcsv2users()
# for u in users:
#     print(f'{u.username} ->{u.attributes}')

kc = Keycloak(server_url='https://keycloak.int-pripolis.polynom.io/auth/',
                         client_id='keycloak-api',
                         realm_name='test-kc-api',
                         client_secret_key='d7633839-7e69-483e-a30c-d8b8c4632d62')
# print(b.readcsv2users()[0].role)

# kc.delete_users()
# users = kc.get_users()
# BMcsvfile.users2csv(users, './myccc.csv')
