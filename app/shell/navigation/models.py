"""
Modèles de navigation.

Ce module définit les structures de données utilisées par le
système de navigation de l'application.

Responsabilités
----------------
- Définir les modèles de navigation.
- Fournir des objets immuables représentant les pages.
- Ne contenir aucune logique métier.

Ce module est volontairement indépendant du reste de
l'application. Il ne dépend ni du Shell, ni de la Session,
ni de Streamlit.

Les modèles définis ici constituent la base sur laquelle
s'appuient le registre des pages et le navigateur.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class Page:
    """
    Représente une page de l'application.

    Une page contient uniquement les métadonnées nécessaires à son
    identification et à son affichage dans le système de navigation.

    Attributes
    ----------
    id : str
        Identifiant technique unique de la page.

    title : str
        Titre affiché dans l'interface utilisateur.

    icon : str
        Nom de l'icône associée à la page.

    render : Callable[[], None]
        Fonction responsable du rendu de la page.

    category : str, optional
        Catégorie de navigation à laquelle appartient la page.

    description : str, optional
        Description courte affichable dans l'interface.

    visible : bool, optional
        Indique si la page doit être visible dans la navigation.
    """

    id: str
    title: str
    icon: str
    render: Callable[[], None]

    category: str = "General"
    description: str = ""
    visible: bool = True