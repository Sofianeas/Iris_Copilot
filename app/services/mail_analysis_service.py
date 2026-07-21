"""
app/services/mail_analysis_service.py

Point d'entrée officiel du workflow "Analyse Mail" (P3-410).

Responsabilité unique : orchestrer le pipeline officiel en coordonnant des
composants déjà existants et certifiés (parser_service, router_service,
Agents, rule_engine) -- ne contient aucune logique métier propre, aucune
règle métier propre, aucune dépendance UI/Streamlit.

Pipeline interne (visible ci-dessous, même quand une étape délègue encore
au code existant) :

    MailAnalysisRequest
            │
            ▼
    _validate_request        (validation du contrat)
            │
            ▼
    _detect_client            (détection du client)
            │
            ▼
    _extract_ticket           (extraction du Ticket)
            │
            ▼
    _load_agent               (chargement de l'agent)
            │
            ▼
    _execute_agent            (exécution de l'agent)
            │
            ▼
    _apply_rules              (application des Rules)
            │
            ▼
    _build_result             (construction du MailAnalysisResult)
            │
            ▼
    Retour

⚠️ Pour cette première implémentation (P3-410), les points suivants sont
volontairement NON traités (dette technique déjà enregistrée lors de
l'audit P3-400, cf. échanges précédents) :
  - Aucun producteur de RagDecision n'existe encore -> `_apply_rules`
    appelle systématiquement `rule_engine.executer(ticket, rag_decision=None)`.
  - Les 12 agents ne sont PAS harmonisés : `_execute_agent` s'adapte à
    leurs signatures existantes (dispatch explicite par groupe), plutôt
    que d'imposer une interface commune.
  - Aucun retry/backoff, aucun logging structuré n'est ajouté ici (dette
    déjà identifiée dans `parser_service.py`, hors périmètre de cette
    mission).
  - `router_service.py` et `parser_service.py` ne sont pas modifiés --
    ce service les appelle tels quels.
"""

from app.agents import axe_esante_agent, etam_agent, dynamiz_pharma_agent
from app.models.mail_analysis import MailAnalysisRequest, MailAnalysisResult
from app.models.ticket import Ticket
from app.services import parser_service, router_service, rule_engine


class MailAnalysisService:
    """
    Service d'orchestration du workflow Analyse Mail. Seule méthode
    publique : `analyze`. Toutes les autres méthodes sont des étapes
    internes du pipeline, jamais destinées à être appelées depuis
    l'extérieur (Pages, autres services).
    """

    # ----------------------------------------------------------------
    # Méthode publique
    # ----------------------------------------------------------------

    def analyze(self, request: MailAnalysisRequest) -> MailAnalysisResult:
        """
        Point d'entrée unique du workflow Analyse Mail.

        Ne laisse JAMAIS remonter d'exception technique : toute erreur,
        attendue ou non, est convertie en `MailAnalysisResult(succes=False,
        ...)`. Les exceptions ne sont pas journalisées ici (aucun système
        de logging n'est reconstruit dans cette mission).
        """
        try:
            erreur_validation = self._validate_request(request)
            if erreur_validation:
                return self._build_result(succes=False, ticket=None, client_detecte=None, erreur=erreur_validation)

            client = self._detect_client(request)
            if not client:
                return self._build_result(
                    succes=False, ticket=None, client_detecte=None,
                    erreur="Client non reconnu dans ce mail (aucune signature connue détectée).",
                )

            if client in router_service.CLIENTS_NON_AUTOMATISES:
                return self._build_result(
                    succes=False, ticket=None, client_detecte=client,
                    erreur=(
                        f"Client '{client}' détecté mais non pris en charge par ce service : "
                        f"nécessite une navigation web non automatisée (V3)."
                    ),
                )

            ticket = self._extract_ticket(request, client)

            agent_fn = self._load_agent(client)
            if agent_fn is None:
                return self._build_result(
                    succes=False, ticket=None, client_detecte=client,
                    erreur=f"Client '{client}' détecté mais aucun agent connu ne peut le traiter.",
                )

            ticket = self._execute_agent(agent_fn, request, client, ticket)
            ticket = self._apply_rules(ticket)

            return self._build_result(succes=True, ticket=ticket, client_detecte=client)

        except Exception as exc:  # jamais de fuite d'exception technique vers la Page
            return self._build_result(
                succes=False, ticket=None, client_detecte=None,
                erreur=f"Erreur technique lors de l'analyse du mail : {exc!r}",
            )

    # ----------------------------------------------------------------
    # Étapes internes du pipeline (privées)
    # ----------------------------------------------------------------

    def _validate_request(self, request: MailAnalysisRequest) -> str | None:
        """Validation minimale du contrat. Retourne un message d'erreur, ou None si valide."""
        if not request.texte_mail or not request.texte_mail.strip():
            return "MailAnalysisRequest invalide : texte_mail vide ou manquant."
        return None

    def _detect_client(self, request: MailAnalysisRequest) -> str | None:
        """Détection du client -- réutilise router_service.detecter_client, ou l'override manuel si fourni."""
        if request.client_force:
            return request.client_force
        return router_service.detecter_client(request.texte_mail) or None

    def _extract_ticket(self, request: MailAnalysisRequest, client: str) -> Ticket:
        """
        Extraction du Ticket.

        Clients texte-seul : délègue à parser_service.traiter_mail (appel
        Gemini existant, non modifié).
        Clients fichier (Groupe B) : retourne un Ticket vierge -- ces
        agents effectuent eux-mêmes l'extraction depuis le fichier, il n'y
        a pas de phase Gemini séparée pour ce groupe (cf. audit P3-400).
        """
        if client in router_service.CLIENTS_FICHIER:
            return Ticket()
        return parser_service.traiter_mail(request.texte_mail, nom_client=client)

    def _load_agent(self, client: str):
        """
        Chargement de l'agent. Retourne la fonction d'enrichissement à
        appeler, ou None si le client n'est pris en charge par aucun
        groupe connu. Ne réimplémente aucune logique d'agent -- se
        contente de sélectionner la bonne fonction déjà existante.
        """
        if client in router_service.AGENTS_DISPONIBLES:
            return router_service.AGENTS_DISPONIBLES[client]
        if client == "AXE_ESANTE":
            return axe_esante_agent.enrich_ticket_depuis_excel
        if client == "ETAM":
            return etam_agent.enrich_ticket_depuis_fichier
        if client == "DYNAMIZ_PHARMA":
            return dynamiz_pharma_agent.enrich_ticket
        return None

    def _execute_agent(self, agent_fn, request: MailAnalysisRequest, client: str, ticket: Ticket) -> Ticket:
        """
        Exécution de l'agent -- s'adapte aux signatures existantes,
        volontairement NON harmonisées (cf. docstring du module). Chaque
        branche appelle l'agent avec exactement sa signature réelle.

        `activer_rule_engine` n'est jamais transmis ici (reste à son
        défaut False côté agent) : l'application des Rules est gérée
        séparément par `_apply_rules`, pour respecter le pipeline officiel
        (2 étapes distinctes), et éviter un double déclenchement du Rule
        Engine.
        """
        if client in router_service.AGENTS_DISPONIBLES:
            return agent_fn(ticket, texte_mail=request.texte_mail)
        if client == "AXE_ESANTE":
            return agent_fn(ticket, request.fichier_attache, texte_mail=request.texte_mail)
        if client == "ETAM":
            return agent_fn(ticket, request.fichier_attache, texte_mail=request.texte_mail)
        if client == "DYNAMIZ_PHARMA":
            return agent_fn(ticket, texte_source=request.texte_mail, fichier_excel=request.fichier_attache)
        raise ValueError(f"Client '{client}' non pris en charge par _execute_agent (incohérence avec _load_agent).")

    def _apply_rules(self, ticket: Ticket) -> Ticket:
        """
        Application des Rules -- appelle le Rule Engine déjà existant et
        certifié. `rag_decision=None` systématiquement : aucun producteur
        officiel de RagDecision n'est encore défini (cf. audit P3-400,
        point 3) -- ne pas anticiper cette décision architecturale ici.
        """
        recommandations = rule_engine.executer(ticket, rag_decision=None)
        bloc = self._formater_recommandations_rule_engine(recommandations)
        if bloc:
            ticket.intervention.commentaire_interne = self._ajouter_si_absent(
                ticket.intervention.commentaire_interne, bloc
            )
        return ticket

    def _build_result(
        self,
        succes: bool,
        ticket: Ticket | None,
        client_detecte: str | None,
        erreur: str | None = None,
    ) -> MailAnalysisResult:
        """Construction du MailAnalysisResult -- point de sortie unique du pipeline."""
        return MailAnalysisResult(
            succes=succes,
            ticket=ticket,
            client_detecte=client_detecte,
            rag_decision=None,  # aucun producteur de RagDecision pour l'instant
            erreur=erreur,
        )

    # ----------------------------------------------------------------
    # Helpers privés (même convention que les 12 agents -- pas de
    # nouvelle abstraction, réutilisation du même pattern déjà établi)
    # ----------------------------------------------------------------

    def _formater_recommandations_rule_engine(self, recommandations) -> str:
        if not recommandations:
            return ""
        lignes = ["🧩 Recommandations du Rule Engine (à vérifier, jamais appliquées automatiquement) :"]
        for reco in recommandations:
            lignes.append(
                f"- Champ '{reco.field}' -> '{reco.value}' "
                f"(confiance={reco.confidence:.2f}, source={reco.source}) : {reco.reason}"
            )
        return "\n".join(lignes)

    def _ajouter_si_absent(self, texte_existant: str, bloc: str) -> str:
        if not bloc:
            return texte_existant
        if texte_existant and bloc in texte_existant:
            return texte_existant
        if texte_existant:
            return f"{texte_existant.strip()}\n\n{bloc}"
        return bloc