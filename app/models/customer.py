from dataclasses import dataclass

@dataclass
class Customer:

    client: str = ""
    numero_client: str = ""

    site_intervention: str = ""

    enseigne: str = ""

    adresse: str = ""
    complement_adresse: str = ""

    code_postal: str = ""
    ville: str = ""
    pays: str = ""

    code_site: str = ""

    commentaire: str = ""

    prenom: str = ""
    nom: str = ""

    portable: str = ""
    fixe: str = ""

    email: str = ""

    departement: str = ""