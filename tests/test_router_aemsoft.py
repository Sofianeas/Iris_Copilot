# tests/test_router_aemsoft.py

from app.services.router_service import traiter_mail_complet

mail_aemsoft = """
Objet : BDC 7732 - Echange PC + transfert de données

Bonjour,

Nouvelle demande d'intervention sur le réseau AEM SOFT.

Site concerné par l'intervention :
Carrefour Market Vénissieux 4521
12 Avenue Jean Jaurès
69200 Vénissieux
France

Pers. A contacter :
M. Bernard
04 78 12 34 56

Type : Intervention J+1
Sous-Type : Intervention AVEC pièces expédiées par IRIS

Objet de l'intervention : Echange PC caisse + transfert de données

INSTRUCTION TECH :
Le PC caisse n°2 ne démarre plus depuis ce matin. Merci de procéder à
l'échange du poste et au transfert des données vers le nouveau PC.

Lien de suivi du colis UPS : 1Z999AA10123456784

Matériel envoyé par UPS : 1x PC caisse Dell OptiPlex

OUTILS A PREVOIR : Tournevis cruciforme

Merci de votre retour.
"""

ticket = traiter_mail_complet(mail_aemsoft)

print("=" * 70)
print("TICKET AEMSOFT COMPLET")
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