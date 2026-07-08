import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 5 : IMAGERIE RADAR 2D (RANGE-ANGLE) ---")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_FREQS = 201
NB_VIRTUAL = 56
C = 3e8
OFFSET_CABLES = 0

data_vide = np.loadtxt('vide_3m_201pts.csv', delimiter=',')
data_cible = np.loadtxt('cible_3m_201pts.csv', delimiter=',')

f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

# Calcul de la longueur d'onde centrale pour l'espacement des antennes
lambda_c = C / (f_start + B/2)
d_virtuel = lambda_c / 2 # On suppose un espacement lambda/2 idéal

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. PREMIÈRE FFT : DISTANCE (RANGE)
# ==========================================
N_fft_range = 512*8
window_range = np.hanning(NB_FREQS)
S_windowed_range = S_matrix_net * window_range
range_profile = np.fft.ifft(S_windowed_range, n=N_fft_range, axis=1)

distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)
distances = distances - OFFSET_CABLES


# ==========================================
# 3. DEUXIÈME FFT : ANGLE (AZIMUT)
# ==========================================
print("Calcul du Beamforming spatial...")
N_fft_angle = 256 
window_angle = np.hanning(NB_VIRTUAL) 

# On applique la fenêtre verticalement sur l'axe des 56 antennes
range_profile_windowed = range_profile * window_angle[:, np.newaxis]

# FFT sur l'axe des antennes (axis=0) + Recentrage pour avoir 0° au milieu
angle_profile = np.fft.fftshift(np.fft.fft(range_profile_windowed, n=N_fft_angle, axis=0), axes=0)

# Création de l'axe des angles
spatial_freqs = np.linspace(-0.5, 0.5, N_fft_angle, endpoint=False)
angles_rad = np.arcsin(np.clip(spatial_freqs * (lambda_c / d_virtuel), -1.0, 1.0))
angles_deg = np.degrees(angles_rad)

# ==========================================
# 4. NORMALISATION ET AFFICHAGE
# ==========================================
# On passe en décibels
power_db = 20 * np.log10(np.abs(angle_profile) + 1e-12)

# NORMALISATION : Le point le plus fort devient 0 dB
power_db -= np.max(power_db)

# REGLAGE DU CONTRASTE VISUEL
CONTRASTE_MIN = -30 # Affiche tout ce qui est à moins de 30 dB sous le pic max
CONTRASTE_MAX = 0   

plt.figure(figsize=(10, 8))

# Affichage de la matrice transposée (.T) pour avoir Distance en Y et Angle en X
im = plt.imshow(power_db.T, aspect='auto', origin='lower',
                extent=[angles_deg[0], angles_deg[-1], distances[0], distances[-1]],
                cmap='jet', vmin=CONTRASTE_MIN, vmax=CONTRASTE_MAX)

plt.colorbar(im, label='Puissance Relative normalisée (dB)')
plt.title('Carte Radar MIMO 2D (Vue de dessus)')
plt.xlabel('Angle (Degrés)')
plt.ylabel('Distance apparente (Mètres)')

# Limitation de la fenêtre de tir
plt.ylim(0, 8) 
plt.xlim(-60, 60) # Le radar ne "voit" généralement pas bien au-delà de +/- 60°

plt.grid(color='white', linestyle='--', alpha=0.3)
plt.show()