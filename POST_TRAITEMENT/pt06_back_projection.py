import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

print("--- ÉTAPE 5 : IMAGERIE RADAR 2D (BACKPROJECTION GÉOMÉTRIQUE) ---")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_FREQS = 101
NB_VIRTUAL = 56
C = 3e8

CONTRASTE_MIN = -30
CONTRASTE_MAX = 0

# Chargement de la calibration (Amplitude + Phase)
if os.path.exists('vecteur_calibration.npy'):
    vecteur_correction = np.load('vecteur_calibration.npy')
    print("✅ Fichier de calibration détecté et chargé.")
else:
    vecteur_correction = np.ones(NB_VIRTUAL, dtype=complex)
    print("⚠️ Aucun fichier de calibration trouvé. Mode brut activé.")

print("Chargement des données brutes...")
data_vide = np.loadtxt('set3_vide1.csv', delimiter=',')
data_cible = np.loadtxt('set3_human_d6.csv', delimiter=',')

f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

# Soustraction du vide
S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. PREMIÈRE ÉTAPE : PROFIL EN DISTANCE (RANGE IFFT)
# ==========================================
N_fft_range = 1024
window_range = np.hanning(NB_FREQS)
S_windowed_range = S_matrix_net * window_range

# Calcul du profil de distance par IFFT
range_profile = np.fft.ifft(S_windowed_range, n=N_fft_range, axis=1)

# Application de la calibration matérielle
range_profile_calibre = range_profile #* vecteur_correction[:, np.newaxis]

# Axe théorique des distances monodirectionnelles (uniquement pour l'interpolation)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 3. MOTEUR DE BACKPROJECTION GÉOMÉTRIQUE 2D
# ==========================================
print("Initialisation de la grille cartésienne (Vue du dessus)...")

# Définition de la zone de la pièce à imager (en mètres)
# X : Gauche (-3m) à Droite (+3m) | Y : Profondeur devant le radar (0.5m à 8m)
Nx, Ny = 200, 200
x_grid = np.linspace(-5, 5, Nx)
y_grid = np.linspace(0.5, 10, Ny)
X, Y = np.meshgrid(x_grid, y_grid)

# Matrice complexe qui va recevoir l'image focalisée
image_2d = np.zeros((Ny, Nx), dtype=complex)

# Définition géométrique réelle du PCB
espacement_rx = 0.031  # 3.1 cm
espacement_tx = 0.240  # 24.0 cm

# Cartographie exacte de quel Tx et quel Rx correspondent à chacune des 56 lignes
tx_indices = np.arange(NB_VIRTUAL) // 8
rx_indices = np.arange(NB_VIRTUAL) % 8

x_tx = tx_indices * espacement_tx
x_rx = rx_indices * espacement_rx

print("Calcul de la rétroprojection cohérente (Force brute optimisée)...")

# On boucle sur les 56 canaux physiques
for p in range(NB_VIRTUAL):
    pos_tx = x_tx[p]
    pos_rx = x_rx[p]
    
    # 1. Calcul du trajet géométrique réel pour chaque pixel de la grille
    dist_aller = np.sqrt((X - pos_tx)**2 + Y**2)
    dist_retour = np.sqrt((X - pos_rx)**2 + Y**2)
    R_total = dist_aller + dist_retour
    
    # Distance monodirectionnelle équivalente pour interroger le profil radar
    R_one_way = R_total / 2
    
    # 2. Interpolation linéaire pour extraire la valeur exacte entre deux bins de la FFT
    interp_func = interp1d(distances, range_profile_calibre[p, :], kind='linear', 
                           bounds_error=False, fill_value=0)
    valeurs_interpolees = interp_func(R_one_way)
    
    # 3. Compensation de la phase de la porteuse haute fréquence (f_start)
    # L'IFFT décale le spectre à 0Hz, il faut restituer la phase de propagation réelle
    tau = R_total / C
    phase_compensation = np.exp(1j * 2 * np.pi * f_start * tau)
    
    # 4. Accumulation dans la matrice image
    image_2d += valeurs_interpolees * phase_compensation

# ==========================================
# 4. TRAITEMENT ET AFFICHAGE CARTÉSIEN (X, Y)
# ==========================================
print("Génération de la carte cartésienne...")
power_db = 20 * np.log10(np.abs(image_2d) + 1e-12)
power_db -= np.max(power_db)

plt.figure(figsize=(10, 8))
# L'affichage utilise l'étendue réelle des axes X et Y en mètres
im = plt.imshow(power_db, aspect='auto', origin='lower',
                extent=[x_grid[0], x_grid[-1], y_grid[0], y_grid[-1]],
                cmap='jet', vmin=CONTRASTE_MIN, vmax=CONTRASTE_MAX)

plt.colorbar(im, label='Puissance Relative normalisée (dB)')
plt.title('Carte Radar MIMO 2D par Rétroprojection Spatiale (Backprojection)')
plt.xlabel('Position Horizontale X (Mètres) - Gauche / Droite')
plt.ylabel('Profondeur Y (Mètres) - Face au radar')

plt.grid(color='white', linestyle='--', alpha=0.3)
plt.show()