from dataclasses import dataclass

@dataclass
class Procedure:

    intervention_sur_site: bool = False

    prise_rdv: bool = False

    date_limite: str = ""

    contrainte: str = ""

    consignes_mission: str = ""

    nombre_techniciens: int = 1

    duree: str = ""

    consignes_planification: str = ""

    travail_attendu: str = ""

    technicien_anglophone: bool = False

    outillage_specifique: str = ""

    autre_outillage: str = ""

    procedure: bool = False

    lien_procedure: str = ""