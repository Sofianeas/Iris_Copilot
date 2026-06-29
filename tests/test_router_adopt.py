# tests/test_router_adopt.py

from app.services.router_service import traiter_mail_complet

mail_adopt = """
Bonjour,

Voici une nouvelle demande d'intervention ADOPT.

Adresse d'intervention :
45 Rue de la République
69002 Lyon
France

Pays : France

Contacts :
Mme Lefevre
06 12 34 56 78

Type de demande : Maintenance

Intitulé de la demande : Le scanner du poste de réception ne fonctionne plus, 
écran d'erreur affiché en continu.

Besoin de matériel spécifique : un câble réseau de 3 mètres si possible

Date et heure / période d'intervention souhaitée : 
Vendredi 27 juin entre 9h et 12h

Durée d'intervention : 1h

Description de l'intervention :
Remplacer le câble réseau du scanner et vérifier la connexion au serveur.

Téléphone : 06 12 34 56 78

Merci de votre retour.
"""

ticket = traiter_mail_complet(mail_adopt)

print("=" * 70)
print("TICKET ADOPT COMPLET")
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