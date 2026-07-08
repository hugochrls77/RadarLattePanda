import numpy as np
import matplotlib.pyplot as plt
import os

print("--- ÉTAPE 3 FINALE : IMAGERIE RADAR 2D CALIBRÉE ---")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_FREQS = 51
NB_VIRTUAL = 56
C = 3e8

print("Chargement des données...")
data_vide = np.loadtxt('matrice_vide.csv', delimiter=',')
data_cible = np.loadtxt('matrice_cible.csv', delimiter=',')

# Chargement du correctif matériel !
if not os.path.exists('vecteur_calibration.npy'):
    print("❌ ERREUR : Fichier 'vecteur_calibration.npy' introuvable.")
    exit()
vecteur_correction = np.load('vecteur_calibration.npy')

f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

lambda_c = C / (f_start + B/2)
d_virtuel = lambda_c / 2 

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. PREMIÈRE FFT : DISTANCE (RANGE)
# ==========================================
N_fft_range = 512
window_range = np.hanning(NB_FREQS)
S_windowed_range = S_matrix_net * window_range
range_profile = np.fft.ifft(S_windowed_range, n=N_fft_range, axis=1)

distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 3. L'APPLICATION DE LA CALIBRATION STATIQUE
# ==========================================
# On multiplie chaque antenne virtuelle par son correctif de phase complexe
range_profile_calibre = range_profile * vecteur_correction[:, np.newaxis]

# ==========================================
# 4. DEUXIÈME FFT : ANGLE (AZIMUT)
# ==========================================
print("Calcul du Beamforming spatial corrigé...")
N_fft_angle = 256 
window_angle = np.hanning(NB_VIRTUAL) 

range_profile_windowed = range_profile_calibre * window_angle[:, np.newaxis]
angle_profile = np.fft.fftshift(np.fft.fft(range_profile_windowed, n=N_fft_angle, axis=0), axes=0)

spatial_freqs = np.linspace(-0.5, 0.5, N_fft_angle, endpoint=False)
angles_rad = np.arcsin(np.clip(spatial_freqs * (lambda_c / d_virtuel), -1.0, 1.0))
angles_deg = np.degrees(angles_rad)

# ==========================================
# 5. NORMALISATION ET AFFICHAGE
# ==========================================
power_db = 20 * np.log10(np.abs(angle_profile) + 1e-12)
power_db -= np.max(power_db)

CONTRASTE_MIN = -30 
CONTRASTE_MAX = 0   

plt.figure(figsize=(10, 8))
im = plt.imshow(power_db.T, aspect='auto', origin='lower',
                extent=[angles_deg[0], angles_deg[-1], distances[0], distances[-1]],
                cmap='jet', vmin=CONTRASTE_MIN, vmax=CONTRASTE_MAX)

plt.colorbar(im, label='Puissance Relative normalisée (dB)')
plt.title('Carte Radar MIMO 2D (Calibrée)')
plt.xlabel('Angle (Degrés)')
plt.ylabel('Distance apparente (Mètres)')

plt.ylim(0, 8) 
plt.xlim(-60, 60) 
plt.grid(color='white', linestyle='--', alpha=0.3)
plt.show()