from keycloak_sync.model.kcuser import KCUser
from datetime import datetime
import pandas as pd
import yaml
import cerberus
import numpy as np
from keycloak_sync.model.csvloader import CSVLoader
from keycloak_sync.model.kc import Keycloak
csl = CSVLoader('/Users/kangyi/Dropbox/Polynom/keycloak_sync/bm-values.yaml',
                '/Users/kangyi/Dropbox/Polynom/keycloak_sync/test1.csv')
#print(csl.data['Date activation de compte'])
list_users = KCUser.create_list_users(csl)
kc = Keycloak(server_url='https://keycloak.int-pripolis.polynom.io/auth/',
                         client_id='keycloak-api',
                         realm_name='test-kc-api',
                         client_secret_key='d7633839-7e69-483e-a30c-d8b8c4632d62')
# kc.add_users(list_users)
print(kc.get_users())
