from dataclasses import dataclass

@dataclass
class Logistics:

    besoin_materiel: bool = False

    commentaire_logistique: str = ""

    pieces: str = ""

    date_expedition_souhaitee: str = ""

    envoi_piece_par: str = ""

    consigne_livraison: str = ""

    tracking: str = ""

    integration_a_faire: bool = False

    retour_piece: str = ""