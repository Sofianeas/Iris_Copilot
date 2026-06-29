from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.intervention import Intervention
from app.agents.barron_agent import enrich_ticket

# Cas 1 : Primark (groupe Pricing FR)
ticket1 = Ticket(customer=Customer(enseigne="Primark", pays="FR"))
ticket1 = enrich_ticket(ticket1)
print("--- Cas Primark ---")
print(ticket1.intervention.contrat)
print(ticket1.intervention.type, "/", ticket1.intervention.sous_type)
print("Anglophone:", ticket1.procedure.technicien_anglophone)

# Cas 2 : Smyths Toys, sous-type déduit du mail = "installation"
ticket2 = Ticket(
    customer=Customer(enseigne="Smyths Toys", pays="FR"),
    intervention=Intervention(sous_type="installation magasin")
)
ticket2 = enrich_ticket(ticket2)
print("\n--- Cas Smyths Toys ---")
print(ticket2.intervention.contrat)
print(ticket2.intervention.type, "/", ticket2.intervention.sous_type)

# Cas 3 : Claire's, hors France, sous-type déduit = "démontage"
ticket3 = Ticket(
    customer=Customer(enseigne="Claire's", pays="BE"),
    intervention=Intervention(sous_type="démontage")
)
ticket3 = enrich_ticket(ticket3)
print("\n--- Cas Claire's Belgique ---")
print(ticket3.intervention.contrat)
print(ticket3.intervention.type, "/", ticket3.intervention.sous_type)
print("Anglophone:", ticket3.procedure.technicien_anglophone)

# Cas 4 : Claire's en Belgique → doit rester anglophone=False
ticket4 = Ticket(
    customer=Customer(enseigne="Claire's", pays="Belgique"),
    intervention=Intervention(sous_type="installation")
)
ticket4 = enrich_ticket(ticket4)
print("\n--- Cas Claire's Belgique (francophone) ---")
print("Anglophone:", ticket4.procedure.technicien_anglophone)

