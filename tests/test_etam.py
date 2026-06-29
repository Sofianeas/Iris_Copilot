# tests/test_etam.py
#
# NOTE : contrairement aux clients texte-seul (ADOPT/AEMSOFT/AMPLIFON/BUT/
# INNOVORDER/POS SERVICE), ETAM ne passe PAS par
# router_service.traiter_mail_complet() -- pas d'extraction Gemini, lecture
# directe et déterministe du fichier (même décision que pour AXE E-SANTE).
# Remplace CHEMIN_FICHIER_ETAM par le chemin d'un vrai fichier "demande
# ETAM" reçu par mail.

from app.models.ticket import Ticket
from app.agents.etam_agent import enrich_ticket_depuis_fichier

CHEMIN_FICHIER_ETAM = "C:/Users/SofianeAOUESExterne/Downloads/Etam.xlsx"  # <-- à adapter

ticket = Ticket()
ticket = enrich_ticket_depuis_fichier(ticket, CHEMIN_FICHIER_ETAM)

print("=" * 70)
print("TICKET ETAM COMPLET")
print("=" * 70)

print("\n--- CUSTOMER ---")
print(ticket.customer)

print("\n--- INTERVENTION ---")
print(ticket.intervention)

print("\n--- LOGISTICS ---")
print(ticket.logistics)

print("\n--- PROCEDURE ---")
print(ticket.procedure)

print("\n--- VALIDATION ---")
print(ticket.validation)