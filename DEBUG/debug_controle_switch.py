import serial
import time

# --- CONFIGURATION ---
PORT_ARDUINO = '/dev/ttyACM0'  # Adapte si besoin (ex: 'COM3' sous Windows)
BAUD_RATE    = 115200

print("--- OUTIL DE CONTRÔLE MANUEL DES SWITCHS ---")

# --- INITIALISATION DE LA CONNEXION ---
try:
    print(f"Tentative de connexion à l'Arduino sur {PORT_ARDUINO}...")
    ser = serial.Serial(PORT_ARDUINO, BAUD_RATE, timeout=2)
    time.sleep(2)  # Le temps que l'Arduino redémarre après la connexion série
    ser.reset_input_buffer()
    print("✅ Connexion réussie !\n")
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    print("Vérifie que le port est correct et qu'aucun autre programme n'utilise l'Arduino.")
    exit()

# --- BOUCLE INTERACTIVE ---
try:
    while True:
        print("-" * 40)
        entree_tx = input("🔌 Entrez le port TX (1 à 8) [ou 'q' pour quitter] : ")
        
        if entree_tx.lower() == 'q':
            break
            
        entree_rx = input("🔌 Entrez le port RX (1 à 8) : ")
        
        try:
            # Conversion des entrées en entiers
            port_tx = int(entree_tx)
            port_rx = int(entree_rx)
            
            # Vérification des limites
            if not (1 <= port_tx <= 8 and 1 <= port_rx <= 8):
                print("⚠️ Erreur : Les ports doivent être compris entre 1 et 8.")
                continue
                
            # Conversion en index (0 à 7) pour la logique mathématique
            tx_index = port_tx - 1
            rx_index = port_rx - 1
            
            # Calcul de l'octet à envoyer (exactement comme dans ton code Arduino)
            # combinaison = (tx_index * 8) + rx_index
            code_combinaison = (tx_index * 8) + rx_index
            
            # Envoi à l'Arduino
            ser.write(bytes([code_combinaison]))
            
            # Attente de l'accusé de réception 'K'
            reponse = ser.read(1)
            
            if reponse == b'K':
                print(f"✅ SUCCÈS : Switchs alignés sur Tx{port_tx} ➔ Rx{port_rx}")
            else:
                print("❌ ERREUR : Pas de réponse 'K' de l'Arduino. (Timeout ou mauvais câblage)")
                
        except ValueError:
            print("⚠️ Erreur : Veuillez entrer un chiffre valide.")

except KeyboardInterrupt:
    # Permet de quitter proprement avec Ctrl+C
    print("\nArrêt forcé par l'utilisateur.")

# --- FERMETURE PROPRE ---
finally:
    # On remet tout à zéro (Port 1 / Port 1) par sécurité avant de quitter
    if 'ser' in locals() and ser.is_open:
        ser.write(bytes([0]))
        ser.close()
        print("🔒 Connexion série fermée. Switchs réinitialisés sur Tx1-Rx1.")