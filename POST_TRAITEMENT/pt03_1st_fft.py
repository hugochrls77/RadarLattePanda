import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 3 : PROFIL DE DISTANCE (RANGE IFFT) ---")

# 1. Paramètres physiques
NB_FREQS = 51
NB_VIRTUAL = 56
C = 3e8

# 2. Chargement et Nettoyage
print("Chargement des matrices...")
data_vide = np.loadtxt('vide_3m_51pts.csv', delimiter=',')
data_cible = np.loadtxt('cible_3m_51pts.csv', delimiter=',')

f_start = data_cible[0, 2]
f_stop = data_cible[NB_FREQS-1, 2]
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))
S_vide_reshape = S_vide.reshape((NB_VIRTUAL, NB_FREQS))
S_cible_reshape = S_cible.reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 3. LE CŒUR DU TRAITEMENT : LA PREMIÈRE FFT
# ==========================================
print("Calcul de la Transformée (IFFT)...")

# A. Zero-padding : On "gonfle" artificiellement le vecteur avec des zéros
# Cela ne crée pas de résolution physique, mais ça lisse la courbe (interpolation temporelle)
N_fft_range = 512 

# B. Fenêtrage (Windowing) : On atténue les bords de la bande passante 
# pour éviter que les "lobes secondaires" du signal ne masquent d'autres cibles.
window_range = np.hanning(NB_FREQS) 

# Application de la fenêtre sur chaque ligne (antenne virtuelle)
S_windowed = S_matrix_net * window_range

# C. Transformée de Fourier Inverse (IFFT) sur l'axe des fréquences (axis=1)
#range_profile = np.fft.ifft(S_windowed, n=N_fft_range, axis=1)
range_profile_raw = np.fft.ifft(S_matrix_net, n=N_fft_range, axis=1)
range_profile_cible = np.fft.ifft(S_cible_reshape, n=N_fft_range, axis=1)
range_profile_vide = np.fft.ifft(S_vide_reshape, n=N_fft_range, axis=1)

# D. Création de l'axe X (Distances en mètres)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 4. AFFICHAGE DU RÉSULTAT
# ==========================================
plt.figure(figsize=(10, 5))

# On affiche le profil de l'antenne centrale (Index 28)
#profil_db = 20 * np.log10(np.abs(range_profile[28, :]) + 1e-12)

# Pour s'assurer que le signal est homogène, on trace aussi la première et la dernière antenne en pointillé
#profil_0_db = 20 * np.log10(np.abs(range_profile[0, :]) + 1e-12)
#profil_55_db = 20 * np.log10(np.abs(range_profile[55, :]) + 1e-12)

#plt.plot(distances, profil_0_db, color='gray', linestyle=':', alpha=0.5, label="Antenne Virtuelle 0")
#plt.plot(distances, profil_55_db, color='gray', linestyle=':', alpha=0.5, label="Antenne Virtuelle 55")
plt.plot(distances, np.real(range_profile_raw[28, :]), color='orange', linewidth=2, label="Signal différence")
plt.plot(distances, np.real(range_profile_cible[28, :]), color='green', linewidth=2, label="Signal cible")
plt.plot(distances, np.real(range_profile_vide[28, :]), color='red', linewidth=2, label="Signal vide")

plt.title("Profil de Distance 1D (Après Range IFFT)")
plt.xlabel("Distance apparente (Mètres)")
plt.ylabel("Puissance (dB)")

# On limite l'affichage aux 8 premiers mètres pour bien voir la pièce
plt.xlim(0, 25) 
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.show()