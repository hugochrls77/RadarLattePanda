import os
import numpy as np
import matplotlib.pyplot as plt

print("--- ETAPE 2 : 56 ANTENNES VIRTUELLES ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_51pts.csv')
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_51pts.csv')

# 1. Paramètres fixes
NB_VIRTUAL = 56

# 2. Chargement et Soustraction
print(f"Chargement de {CHEMIN_VIDE}...")
data_vide = np.loadtxt(CHEMIN_VIDE, delimiter=',')
data_cible = np.loadtxt(CHEMIN_CIBLE, delimiter=',')

# --- DÉTECTION DYNAMIQUE DU NOMBRE DE POINTS ---
NB_FREQS = len(data_vide) // NB_VIRTUAL
print(f"✅ Détection automatique : {NB_FREQS} points de fréquence par canal.")

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]

# Matrice nettoyée (Cible seule)
S_net = S_cible - S_vide
S_matrix_net = S_net.reshape((NB_VIRTUAL, NB_FREQS))

# 3. Extraction des données pour l'affichage
magnitude_db = 20 * np.log10(np.abs(S_matrix_net) + 1e-12)
phase_rad = np.angle(S_matrix_net)

# Axes pour l'affichage
f_start = data_cible[0, 2] / 1e9       
f_stop = data_cible[NB_FREQS-1, 2] / 1e9 

# ==========================================
# 4. AFFICHAGE DE LA CARTE DE CHALEUR (HEATMAP)
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Graphique 1 : La Magnitude (Force du signal)
im1 = ax1.imshow(magnitude_db, aspect='auto', origin='lower', cmap='jet',
                 extent=[f_start, f_stop, 0, NB_VIRTUAL-1],
                 vmin=-70, vmax=-40)
ax1.set_title("Magnitude S21 (dB) Nette (Cible seule)")
ax1.set_ylabel("Indice Antenne Virtuelle")
fig.colorbar(im1, ax=ax1, label="dB")

# Graphique 2 : La Phase (Retard du signal)
im2 = ax2.imshow(phase_rad, aspect='auto', origin='lower', cmap='hsv',
                 extent=[f_start, f_stop, 0, NB_VIRTUAL-1])
ax2.set_title("Phase S21 (Radians)")
ax2.set_xlabel("Fréquence (GHz)")
ax2.set_ylabel("Indice Antenne Virtuelle")
fig.colorbar(im2, ax=ax2, label="Radians")

plt.tight_layout()
plt.show()