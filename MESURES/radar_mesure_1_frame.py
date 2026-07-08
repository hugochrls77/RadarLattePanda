import pyvisa
import numpy as np
import time
import serial
import subprocess
import os

print("--- RADAR MIMO 7x8 : SYSTÈME COMPLET (VNA + SWITCHS + ADF435x) ---")

# ==========================================
# 1. PARAMÈTRES MATÉRIELS ET RF
# ==========================================
PORT_ARDUINO = '/dev/ttyACM0'  
BAUD_RATE    = 115200    
FREQ_START   = 700e6     
FREQ_STOP    = 1e9       
NB_POINTS    = 101        
IF_BAND      = 30000    
PUISSANCE    = 0         

FREQ_ADF_LO  = 4000e6    
DOSSIER_ADF  = "/home/hc/Bureau/LattePandaLinux/ADF4351/pyadf435x" 

# --- PATCH MATÉRIEL : MAPPING DES PORTS TX ---
# L'antenne Tx8 n'existe pas physiquement. 
# L'antenne Tx7 est branchée sur le port 8 du switch.
# Le port 7 du switch est laissé vide/déconnecté.
PORTS_TX_PHYSIQUES = [1, 2, 3, 4, 5, 6, 8] 

# ==========================================
# 2. INITIALISATION DE L'ADF435x
# ==========================================
print("\n[INIT] Démarrage du synthétiseur ADF435x...")
try:
    # A. Flashage du firmware FX2
    subprocess.run(
        ["cycfx2prog", "-id=0456.b40d", "prg:firmware/fx2/fx2adf435xfw.ihx", "run"], 
        cwd=DOSSIER_ADF, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    
    print("⏳ Attente du redémarrage USB de la carte (2s)...")
    time.sleep(2) # <--- LE CORRECTIF EST ICI
    
    # B. Verrouillage de la PLL
    freq_mhz = str(int(FREQ_ADF_LO / 1e6))
    subprocess.run(
        ["python3", "adf435xctl", "--freq", freq_mhz, "--ref-freq", "10", 
         "--output-enable", "1", "--output-power", "5", "--ld-pin-mode", "1"], 
        cwd=DOSSIER_ADF, check=True, stdout=subprocess.DEVNULL
    )
    print(f"✅ PLL ADF435x verrouillée avec succès sur {freq_mhz} MHz.")
except Exception as e:
    print(f"❌ Erreur critique ADF : {e}")
    exit()

# ==========================================
# 3. CONNEXION ARDUINO
# ==========================================
try:
    print(f"\nConnexion à l'Arduino sur {PORT_ARDUINO}...")
    ser = serial.Serial(PORT_ARDUINO, BAUD_RATE, timeout=2) 
    time.sleep(2)  
    ser.reset_input_buffer()
    print("✅ Liaison Arduino opérationnelle.")
except Exception as e:
    print(f"❌ Erreur port série : {e}")
    exit()

# ==========================================
# 4. CONNEXION ET CONFIGURATION VNA
# ==========================================
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

# ==========================================
# 5. TRANSLATION DU VECTEUR DE FRÉQUENCE
# ==========================================
frequences_if = np.fromstring(vna.query('SENS1:FREQ:DATA?'), sep=',')
frequences_rf_reelles = frequences_if + FREQ_ADF_LO

vna.query('TRIG:SING;*OPC?')
_ = vna.query('CALC1:TRAC1:DATA:SDAT?')

# ==========================================
# 6. BOUCLE D'ACQUISITION MIMO (7x8)
# ==========================================
print(f"\n🚀 Lancement du balayage (Fréq. Rayonnée : {frequences_rf_reelles[0]/1e9:.2f} GHz à {frequences_rf_reelles[-1]/1e9:.2f} GHz)...")
liste_blocs_numpy = []
temps_debut = time.time()

# num_antenne_tx servira pour le CSV (1 à 7) pour une matrice propre
# port_physique_tx servira pour commander le switch via l'Arduino (1,2,3,4,5,6,8)
for num_antenne_tx, port_physique_tx in enumerate(PORTS_TX_PHYSIQUES, start=1):
    col_tx = np.full(NB_POINTS, num_antenne_tx)
    index_tx_arduino = port_physique_tx - 1 # Conversion en index (0 à 7) pour le bit-shift
    
    for rx in range(1, 9):
        col_rx = np.full(NB_POINTS, rx)
        index_rx_arduino = rx - 1
        
        # A. Commutation des switchs
        code_combinaison = (index_tx_arduino * 8) + index_rx_arduino
        ser.write(bytes([code_combinaison]))
        
        # B. Verrou Matériel Arduino
        if ser.read(1) != b'K':
            print(f"⚠️ Erreur de synchronisation Arduino sur Antenne Tx{num_antenne_tx} (Port {port_physique_tx}), Rx{rx}")
            continue
            
        # C. Verrou Logiciel VNA
        vna.query('TRIG:SING;*OPC?')
        
        # D. Extraction des données
        sdata_raw = vna.query('CALC1:TRAC1:DATA:SDAT?')
        valeurs_brutes = np.fromstring(sdata_raw, sep=',')
        
        reels = valeurs_brutes[0::2]
        imags = valeurs_brutes[1::2]
        
        # Structuration de la matrice avec le numéro d'antenne logique (1 à 7)
        bloc = np.column_stack((col_tx, col_rx, frequences_rf_reelles, reels, imags))
        liste_blocs_numpy.append(bloc)

temps_fin = time.time()
print(f"\n⏱️ Matrice complète acquise en : {temps_fin - temps_debut:.3f} secondes.")

# ==========================================
# 7. SAUVEGARDE ET RESTAURATION
# ==========================================
tableau_final = np.vstack(liste_blocs_numpy)
np.savetxt('set3_vide3.csv', tableau_final, delimiter=',', fmt='%g')
print("💾 Fichier 'matrice_mimo_lattepanda.csv' généré (Format 7 émetteurs x 8 récepteurs).")

vna.write('SYST:SHOW')
vna.write('DISPLAY:ENAB ON')
vna.write('TRIG:SOUR INT')
vna.write('SOUR1:POW:STAT OFF')
vna.close()

ser.write(bytes([0])) 
ser.close()
print("🔒 Système mis en sécurité.")
