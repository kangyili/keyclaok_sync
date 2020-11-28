from keycloak_sync.abstract.user import User


class BMuser(User):
    ATTRIBUTES = {
        'Client Full Name': 'Bois & Materiaux',
        'Client Short Name': 'bm',
    }
    AVAILABLE_ROLES = ['VALIDATION_ADMIN',
                       'VALIDATION_DA', 'VALIDATION_RMP', 'VALIDATION_VIEWER']

    def mapper(self) -> dict:
        header_user_mapper = {
            'Date activation de compte': self.createdtime,
            'Date désactivation de compte': self.deactivetime,
            'Code(s) agence(s)': self.attributes['Subsidiary Code'],
            'Libellé(s) agence(s)': self.attributes['Subsidiary Name'],
            'Profil': self.role,
            'Prénom': self.firstname,
            'Nom': self.lastname,
            'Mail': self.email,
            'Mot de passe': self.password}
        return header_user_mapper
