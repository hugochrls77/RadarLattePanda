import pyvisa
import numpy as np
import time
import serial
import subprocess
import os

print("--- RADAR MIMO : ACQUISITION CALIBRATION MAÎTRE (BOUCLE FERMÉE) ---")

# ==========================================
# 1. PARAMÈTRES MATÉRIELS ET RF (MODE CALIBRATION)
# ==========================================
PORT_ARDUINO = '/dev/ttyACM0'  
BAUD_RATE    = 115200    
FREQ_START   = 300e6     # 300 MHz
FREQ_STOP    = 1.3e9     # 1.3 GHz
NB_POINTS    = 201       # Pour avoir un Delta F de 5 MHz
IF_BAND      = 30000    
PUISSANCE    = 0         

FREQ_ADF_LO  = 4000e6    
DOSSIER_ADF  = "/home/hc/Bureau/LattePandaLinux/ADF4351/pyadf435x" 

# Matériel corrigé : Les ports sont maintenant séquentiels de 1 à 7
PORTS_TX_PHYSIQUES = [1, 2, 3, 4, 5, 6, 7] 
DOSSIER_CALIB = "Calibration_Master_201pts"

if not os.path.exists(DOSSIER_CALIB):
    os.makedirs(DOSSIER_CALIB)

print(f"📁 Dossier de sauvegarde : {DOSSIER_CALIB}")
print("🛡️ Mode Résilient activé : Vous pouvez interrompre le script à tout moment.\n")

# ==========================================
# 2. INITIALISATION DU MATÉRIEL (ADF + ARDUINO + VNA)
# ==========================================
print("[INIT] Démarrage du synthétiseur ADF435x...")
try:
    subprocess.run(["cycfx2prog", "-id=0456.b40d", "prg:firmware/fx2/fx2adf435xfw.ihx", "run"], 
                   cwd=DOSSIER_ADF, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    freq_mhz = str(int(FREQ_ADF_LO / 1e6))
    subprocess.run(["python3", "adf435xctl", "--freq", freq_mhz, "--ref-freq", "10", 
                    "--output-enable", "1", "--output-power", "5", "--ld-pin-mode", "1"], 
                   cwd=DOSSIER_ADF, check=True, stdout=subprocess.DEVNULL)
    print(f"✅ PLL ADF435x verrouillée sur {freq_mhz} MHz.")
except Exception as e:
    print(f"❌ Erreur critique ADF : {e}")
    exit()

try:
    print(f"Connexion à l'Arduino sur {PORT_ARDUINO}...")
    ser = serial.Serial(PORT_ARDUINO, BAUD_RATE, timeout=2) 
    time.sleep(2)  
    ser.reset_input_buffer()
    print("✅ Liaison Arduino opérationnelle.")
except Exception as e:
    print(f"❌ Erreur port série : {e}")
    exit()

rm = pyvisa.ResourceManager('@py')
try:
    vna = rm.open_resource('TCPIP0::127.0.0.1::5025::SOCKET')
    vna.read_termination = '\n'
    vna.write_termination = '\n'
    vna.timeout = 10000  
    vna.write('*CLS')    
    print("✅ VNA connecté :", vna.query('*IDN?'))
except pyvisa.errors.VisaIOError:
    print("❌ VNA introuvable.")
    exit()

print("[INIT] Configuration du VNA pour la calibration...")
vna.write(f'SENS1:FREQ:STAR {FREQ_START}')
vna.write(f'SENS1:FREQ:STOP {FREQ_STOP}')
vna.write(f'SENS1:SWE:POIN {NB_POINTS}')
vna.write(f'SENS1:BWID {IF_BAND}')
vna.write(f'SOUR1:POW {PUISSANCE}')
vna.write('SOUR1:POW:STAT ON')

vna.write('CALC1:PAR1:DEF S21')
vna.write('CALC1:CORR:STAT OFF')   
vna.write('DISPLAY:ENAB OFF')    
vna.write('SYST:HIDE')    
vna.write('TRIG:DELAY 0')          
vna.write('INIT:CONT ON')  
vna.write('TRIG:SOUR BUS') 

frequences_if = np.fromstring(vna.query('SENS1:FREQ:DATA?'), sep=',')
frequences_rf_reelles = frequences_if + FREQ_ADF_LO

vna.query('TRIG:SING;*OPC?')
_ = vna.query('CALC1:TRAC1:DATA:SDAT?')

# ==========================================
# 3. ACQUISITION PAR DIAGONALES (8 SALVES DE 7 CÂBLES)
# ==========================================
print("\n🚀 Lancement de l'acquisition assistée par diagonales...")

for decalage in range(8):
    # 1. Calcul des couples pour cette salve
    couples_salve = []
    for index_tx in range(len(PORTS_TX_PHYSIQUES)):  # 0 à 6 (soit 7 émetteurs)
        tx_logique = index_tx + 1
        port_tx_physique = PORTS_TX_PHYSIQUES[index_tx]
        
        # Mathématique du décalage circulaire pour trouver le bon port RX (1 à 8)
        rx = ((tx_logique - 1 + decalage) % 8) + 1
        couples_salve.append((tx_logique, rx, port_tx_physique))
        
    # 2. Vérification Anti-Crash globale pour cette salve
    fichiers_existants = 0
    for tx_logique, rx, _ in couples_salve:
        if os.path.exists(os.path.join(DOSSIER_CALIB, f"calib_master_Tx{tx_logique}_Rx{rx}.csv")):
            fichiers_existants += 1
            
    if fichiers_existants == 7:
        print(f"✅ ÉTAPE {decalage + 1}/8 : Diagonale {decalage} déjà complète. On passe à la suivante.")
        continue
        
    print("\n" + "="*55)
    print(f"🔧 ÉTAPE {decalage + 1}/8 : DIAGONALE DÉCALÉE DE {decalage} ({fichiers_existants}/7 déjà faits)")
    print("="*55)
    print("Veuillez brancher vos 7 câbles coaxiaux simultanément ainsi :")
    
    for tx_logique, rx, port_tx_physique in couples_salve:
        print(f"  🔹 Câble {tx_logique} : Port TX{port_tx_physique} ➔ Port RX{rx}")
        
    input("\n🟢 Appuyez sur ENTRÉE une fois les 7 câbles branchés pour lancer la mesure...")
    
    # 3. Mesures VNA
    for tx_logique, rx, port_tx_physique in couples_salve:
        nom_fichier = f"calib_master_Tx{tx_logique}_Rx{rx}.csv"
        chemin_complet = os.path.join(DOSSIER_CALIB, nom_fichier)
        
        if os.path.exists(chemin_complet):
            print(f"   ⏩ Fichier existant : Tx{tx_logique} -> Rx{rx} ignoré.")
            continue
            
        try:
            print(f"   ⏳ Mesure : Tx{tx_logique} -> Rx{rx}...")
            
            # Commande Arduino (Désormais purement séquentielle)
            index_tx_arduino = port_tx_physique - 1 
            index_rx_arduino = rx - 1
            code_combinaison = (index_tx_arduino * 8) + index_rx_arduino
            ser.write(bytes([code_combinaison]))
            
            if ser.read(1) != b'K':
                print(f"❌ Erreur de synchronisation Arduino sur TX{tx_logique}-RX{rx} !")
                exit()
                
            # Mesure VNA
            vna.query('TRIG:SING;*OPC?')
            sdata_raw = vna.query('CALC1:TRAC1:DATA:SDAT?')
            valeurs_brutes = np.fromstring(sdata_raw, sep=',')
            
            reels = valeurs_brutes[0::2]
            imags = valeurs_brutes[1::2]
            
            # Structuration des colonnes
            col_tx = np.full(NB_POINTS, tx_logique)
            col_rx = np.full(NB_POINTS, rx)
            
            # Sauvegarde formatée (Anti-crash file-by-file)
            bloc = np.column_stack((col_tx, col_rx, frequences_rf_reelles, reels, imags))
            np.savetxt(chemin_complet, bloc, delimiter=',', fmt=['%d', '%d', '%.2f', '%.6e', '%.6e'])
            
            print(f"      💾 OK -> {nom_fichier}")
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DE L'ACQUISITION : {e}")
            print("Le matériel a peut-être été déconnecté. Relancez le script pour reprendre.")
            exit()

# ==========================================
# 4. FERMETURE PROPRE
# ==========================================
print("\n🎉 ACQUISITION TERMINÉE AVEC SUCCÈS !")
vna.write('SYST:SHOW')
vna.write('DISPLAY:ENAB ON')
vna.write('TRIG:SOUR INT')
vna.write('SOUR1:POW:STAT OFF')
vna.close()
ser.write(bytes([0])) 
ser.close()
print("🔒 Matériel mis en sécurité.")
