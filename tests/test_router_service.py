from app.services.router_service import traiter_mail_complet

mail_barron = """
Store Name: PRIMARK NICE ETOILE
Store Address: 12 Avenue Jean Médecin, 06000 Nice, FR
Store Number: 0142
Site Contact: M. Dupont
Site Phone No.: 612345678
Barron McCann Reference: WOT0018102
Customer Ref: INC0531200
Serial Number: TPE-4521
Required Parts: 1x Lane 3000
Required Actions: Replace faulty PED, return defective unit to depot
"""

ticket = traiter_mail_complet(mail_barron)

print("=" * 70)
print("TICKET COMPLET - TOUS LES CHAMPS")
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