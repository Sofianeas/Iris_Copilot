# tests/test_adopt_agent.py

from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.logistics import Logistics
from app.agents.adopt_agent import enrich_ticket

# Cas 1 : France, avec câble réseau
ticket1 = Ticket(
    customer=Customer(pays="France"),
    logistics=Logistics(besoin_materiel=True, pieces="câble réseau 5m")
)
ticket1 = enrich_ticket(ticket1, texte_mail="Demande standard, intervention en France.")
print("--- Cas France ---")
print("Contrat:", ticket1.intervention.contrat)
print("Type:", ticket1.intervention.type)
print("Anglophone:", ticket1.procedure.technicien_anglophone)
print("Commentaire logistique:", ticket1.logistics.commentaire_logistique)

# Cas 2 : Belgique
ticket2 = Ticket(customer=Customer(pays="Belgique"))
ticket2 = enrich_ticket(ticket2, texte_mail="Demande pour la Belgique.")
print("\n--- Cas Belgique ---")
print("Contrat:", ticket2.intervention.contrat)
print("Commentaire logistique:", ticket2.logistics.commentaire_logistique)

# Cas 3 : CATO détecté
ticket3 = Ticket(customer=Customer(pays="France"))
ticket3 = enrich_ticket(ticket3, texte_mail="Bonjour, demande d'installation du boîtier CATO sur le site X.")
print("\n--- Cas CATO ---")
print("Commentaire interne:", ticket3.intervention.commentaire_interne)
print("Contrat (devrait être vide, pas traité):", ticket3.intervention.contrat)