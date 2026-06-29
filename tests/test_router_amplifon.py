# tests/test_router_amplifon.py

from app.services.router_service import traiter_mail_complet

mail_amplifon = """
Objet : BDC 4715 - installation Epson avec reprise

Bonjour,

Demande d'intervention pour le centre Amplifon Lille.

Adresse de livraison :
Centre Amplifon Lille
25 Rue Nationale
59800 Lille
France
Code site : 187

Contact sur site :
Mme Caron
03 20 11 22 33

Merci de procéder à l'installation d'une imprimante neuve Epson, avec
reprise de l'ancienne imprimante Ricoh 305 (plus de 30 kg) à retourner.

Consigne CDS : vérifier le stock avant expédition.

Merci de votre retour.
"""

ticket = traiter_mail_complet(mail_amplifon)

print("=" * 70)
print("TICKET AMPLIFON COMPLET (modèle D - imprimante)")
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