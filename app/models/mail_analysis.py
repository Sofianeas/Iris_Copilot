"""
app/models/mail_analysis.py

Contrats métier officiels du workflow "Analyse Mail" (P3-300).

Ces contrats décrivent UNIQUEMENT des données -- aucun traitement, aucune
dépendance UI/service/agent/Gemini/SQLite/ChromaDB. Ils composent les
modèles déjà existants (Ticket, RagDecision) plutôt que d'en dupliquer la
structure.

Pipeline officiel (défini par l'architecture, non modifié ici) :
    Page -> MailAnalysisService -> Agents IA -> MailAnalysisResult -> Page
"""

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.models.rag_decision import RagDecision
from app.models.ticket import Ticket


@dataclass(frozen=True)
class MailAnalysisRequest:
    """
    Requête d'entrée du workflow Analyse Mail.

    Attributs :
        texte_mail : contenu brut du mail à analyser. Toujours requis,
            même pour les clients dont la source de vérité est un fichier
            (le mail peut porter des informations complémentaires, cf.
            AXE E-SANTE/ETAM/DYNAMIZ PHARMA).
        fichier_attache : pièce jointe Excel éventuelle (chemin, Path, ou
            flux binaire) -- requise pour les clients "fichier" (AXE
            E-SANTE, ETAM), optionnelle sinon. Typage aligné sur ce
            qu'accepte réellement `openpyxl.load_workbook` dans le code
            existant (str | Path | flux binaire).
        client_force : permet d'imposer le client plutôt que de le
            laisser être détecté automatiquement (ex. correction manuelle
            d'une détection erronée depuis une page de validation).
    """

    texte_mail: str
    fichier_attache: str | Path | BinaryIO | None = None
    client_force: str | None = None


@dataclass(frozen=True)
class MailAnalysisResult:
    """
    Résultat du workflow Analyse Mail, retourné à la Page appelante.

    Attributs :
        succes : indique si l'analyse a abouti à un Ticket exploitable.
            Champ ajouté (n'existe dans aucun modèle réutilisé) car un
            contrat de résultat de workflow a structurellement besoin d'un
            signal de succès/échec explicite, que `Ticket` seul ne porte
            pas -- cf. docstring du module pour la justification de tout
            champ non directement réutilisé d'un modèle existant.
        ticket : le Ticket enrichi si succes=True, sinon None.
        client_detecte : le client identifié (ou imposé via
            `MailAnalysisRequest.client_force`), ou None si la détection a
            échoué.
        rag_decision : la RagDecision utilisée pour cette analyse, si le
            Rule Engine a été activé et qu'une décision a été calculée en
            amont. None si non applicable.
        erreur : message d'erreur lisible si succes=False (ex. "client non
            reconnu", "fichier requis manquant"). None si succes=True.
    """

    succes: bool
    ticket: Ticket | None
    client_detecte: str | None
    rag_decision: RagDecision | None = None
    erreur: str | None = None