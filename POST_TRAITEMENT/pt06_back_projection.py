import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

print("--- ÉTAPE 6 : IMAGERIE RADAR 2D (BACKPROJECTION GÉOMÉTRIQUE) ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_VIRTUAL = 56
C = 3e8
CONTRASTE_MIN = -30
CONTRASTE_MAX = 0

# Chargement de la calibration (Amplitude + Phase)
CHEMIN_CALIB = os.path.join(dossier_courant, "vecteur_calibration.npy")
if os.path.exists(CHEMIN_CALIB):
    vecteur_correction = np.load(CHEMIN_CALIB)
    print("✅ Fichier de calibration détecté et chargé.")
else:
    vecteur_correction = np.ones(NB_VIRTUAL, dtype=complex)
    print("⚠️ Aucun fichier de calibration trouvé. Mode brut activé.")

# Chargement des données
CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_201pts.csv')
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_201pts.csv')

print("Chargement des données brutes...")
data_vide = np.loadtxt(CHEMIN_VIDE, delimiter=',')
data_cible = np.loadtxt(CHEMIN_CIBLE, delimiter=',')

# --- DÉTECTION DYNAMIQUE ---
NB_FREQS = len(data_vide) // NB_VIRTUAL
print(f"✅ Détection automatique : {NB_FREQS} points de fréquence par canal.")

f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

# Soustraction du vide
S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# Application de la calibration
S_calib = S_matrix_net * vecteur_correction[:, np.newaxis]

# FFT Range
N_fft_range = 1024
range_profile = np.fft.ifft(S_calib * np.hanning(NB_FREQS), n=N_fft_range, axis=1)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 2. DÉFINITION DE LA GRILLE IMAGE
# ==========================================
x_grid = np.linspace(-2, 2, 200) # Zone X (m)
y_grid = np.linspace(0, 5, 200)  # Zone Y (m)
image_2d = np.zeros((len(y_grid), len(x_grid)), dtype=complex)

# Positions antennes (x=0, y=0 pour simplifier)
antennes_x = np.linspace(-0.5, 0.5, NB_VIRTUAL)
antennes_y = np.zeros(NB_VIRTUAL)

print("Calcul de la Backprojection (cela peut prendre un moment)...")
for p in range(NB_VIRTUAL):
    for i, x in enumerate(x_grid):
        for j, y in enumerate(y_grid):
            # Distance antenne-pixel
            R_total = np.sqrt((x - antennes_x[p])**2 + y**2)
            
            # Interpolation
            interp_func = interp1d(distances, range_profile[p, :], kind='linear', bounds_error=False, fill_value=0)
            val = interp_func(R_total)
            
            # Phase
            phase_comp = np.exp(1j * 2 * np.pi * f_start * (R_total / C))
            image_2d[j, i] += val * phase_comp

# ==========================================
# 3. AFFICHAGE
# ==========================================
power_db = 20 * np.log10(np.abs(image_2d) + 1e-12)
power_db -= np.max(power_db)

plt.figure(figsize=(8, 6))
plt.imshow(power_db, extent=[x_grid[0], x_grid[-1], y_grid[0], y_grid[-1]],
           origin='lower', cmap='jet', vmin=CONTRASTE_MIN, vmax=CONTRASTE_MAX)
plt.colorbar(label="Puissance relative (dB)")
plt.title("Imagerie par Backprojection")
plt.xlabel("X (m)")
plt.ylabel("Y (m)")
plt.show()