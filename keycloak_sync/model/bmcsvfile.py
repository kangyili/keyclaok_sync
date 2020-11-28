"""Define BM style CSV file"""
from keycloak_sync.model.bmuser import BMuser
from keycloak_sync.abstract.csvfile import CSVfile
from keycloak_sync.model.log import logging
import pandas as pd
logger = logging.getLogger(__name__)


class BMcsvfile(CSVfile):
    HEADER = ['Date activation de compte', 'Date désactivation de compte',
              'Code(s) agence(s)', 'Libellé(s) agence(s)', 'Profil', 'Prénom',
              'Nom', 'Mail', 'Mot de passe']

    @CSVfile.readdata
    def readcsv2users(self) -> list:
        list_rows = [list(row) for row in self.data.values]
        list_users = []
        for row in list_rows:
            user = BMcsvfile.readrow2user(row)
            list_users.append(user)
        return list_users

    @CSVfile.readdata
    def isformat(self) -> bool:
        header = list(self.data.columns.values[0:9])
        try:
            assert header == BMcsvfile.HEADER
            logger.info('Passed CSV Format Test')
            return True
        except AssertionError:
            logger.error(
                f'Invalid CSV Format. The header should be {BMcsvfile.HEADER}')
            return False

    @classmethod
    def readrow2user(cls, row: list) -> BMuser:
        """read one row of the csv file and trun it in to bm user instance

        Args:
            row (list): one row of user's infomation

        Returns:
            BMuser: class BMuser
        """
        userinfo = dict(zip(BMcsvfile.HEADER, row))
        userattri = {}
        userattri['Client Full Name'] = BMuser.ATTRIBUTES['Client Full Name']
        userattri['Client Short Name'] = BMuser.ATTRIBUTES['Client Short Name']
        userattri['Subsidiary Code'] = userinfo['Code(s) agence(s)']
        userattri['Subsidiary Name'] = userinfo['Libellé(s) agence(s)']
        bmuser = BMuser(email=userinfo['Mail'], username=userinfo['Mail'],
                        firstname=userinfo['Prénom'], lastname=userinfo['Nom'],
                        role=userinfo['Profil'], attributes=userattri,
                        password=userinfo['Mot de passe'])
        return bmuser

    @classmethod
    def users2csv(cls, list_users: list, file_path: str, separator: str = ";"):
        dataframe = {}
        for column in BMcsvfile.HEADER:
            dataframe[column] = []
        for column in BMcsvfile.HEADER:
            for user in list_users:
                dataframe[column].append(user.mapper()[column])

        pd.DataFrame(data=dataframe).to_csv(
            path_or_buf=file_path, sep=separator, index=False)
