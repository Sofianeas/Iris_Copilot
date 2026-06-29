from dataclasses import dataclass

@dataclass
class Intervention:

    type_intervention: str = ""

    contrat: str = ""

    type: str = ""

    sous_type: str = ""

    categorie: str = ""

    numero_serie: str = ""

    reference_materiel_client: str = ""

    type_ticket: str = ""

    intitule: str = ""

    numero_incident_client: str = ""

    code_projet: str = ""

    problematique: str = ""

    commentaire_interne: str = ""

    origine: str = ""

    niveau_priorite: str = ""