import numpy as np
import matplotlib.pyplot as plt
import os

print("--- ÉTAPE 4 : VUE GLOBALE DISTANCE-ANTENNES (RANGE IFFT) ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

# 1. Paramètres physiques
NB_VIRTUAL = 56
C = 3e8

CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_51pts.csv')
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_51pts.csv')

# 2. Chargement et Nettoyage
data_vide = np.loadtxt(CHEMIN_VIDE, delimiter=',')
data_cible = np.loadtxt(CHEMIN_CIBLE, delimiter=',')

# --- DÉTECTION DYNAMIQUE DU NOMBRE DE POINTS ---
NB_FREQS = len(data_vide) // NB_VIRTUAL
print(f"✅ Détection automatique : {NB_FREQS} points de fréquence par canal.")

f_start = data_cible[0, 2]
f_stop = data_cible[NB_FREQS-1, 2]
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# 3. Transformée IFFT (Range)
N_fft_range = 512
window_range = np.hanning(NB_FREQS) 
S_windowed = S_matrix_net * window_range
range_profile = np.fft.ifft(S_windowed, n=N_fft_range, axis=1)

distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# 4. Conversion en Puissance (dB) pour l'affichage
magnitude_db = 20 * np.log10(np.abs(range_profile) + 1e-12)
magnitude_real = np.real(range_profile)
# ==========================================
# 5. AFFICHAGE DE LA MATRICE COMPLÈTE
# ==========================================
plt.figure(figsize=(12, 6))

# Affichage avec imshow (l'axe des distances est en X, les antennes en Y)
im = plt.imshow(magnitude_db, aspect='auto', origin='lower', cmap='jet',
                extent=[distances[0], distances[-1], 0, NB_VIRTUAL-1])

plt.colorbar(im, label="Puissance Relative (dB)")
plt.title("Matrice Distance-Antennes après la 1ère FFT")
plt.xlabel("Distance (Mètres)")
plt.ylabel("Index Antenne Virtuelle (0 à 55)")

# On limite l'axe X pour zoomer sur la zone d'intérêt de la pièce
plt.xlim(0, 8) 

# Ajout d'une grille légère pour la lisibilité
plt.grid(color='white', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.show()