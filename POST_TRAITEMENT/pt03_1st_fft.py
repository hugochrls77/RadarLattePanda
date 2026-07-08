import os
import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 3 : PROFIL DE DISTANCE (RANGE IFFT) ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_51pts.csv')
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_51pts.csv')

# 1. Paramètres physiques
NB_VIRTUAL = 56
C = 3e8

# 2. Chargement et Nettoyage
print(f"Chargement de {CHEMIN_VIDE}...")
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
S_vide_reshape = S_vide.reshape((NB_VIRTUAL, NB_FREQS))
S_cible_reshape = S_cible.reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 3. LE CŒUR DU TRAITEMENT : LA PREMIÈRE FFT
# ==========================================
print("Calcul de la Transformée (IFFT)...")

# A. Zero-padding : On "gonfle" artificiellement le vecteur avec des zéros
# Cela n'améliore pas la résolution physique, mais "lisse" la courbe d'interpolation
N_fft_range = 1024 # Puissance de 2 pour la rapidité de la FFT

# B. Application d'une fenêtre (Windowing) pour réduire les rebonds (lobes secondaires)
# On utilise une fenêtre de Blackman qui est excellente pour les signaux radar
fenetre = np.blackman(NB_FREQS)

# C. La Transformée IFFT (sur l'axe des fréquences, axis=1)
# On multiplie chaque ligne (antenne) par la fenêtre avant de faire l'IFFT
range_profile = np.fft.ifft(S_matrix_net * fenetre, n=N_fft_range, axis=1)
range_profile_raw = np.fft.ifft(S_matrix_net, n=N_fft_range, axis=1)
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
plt.plot(distances, np.real(range_profile_raw[28, :]), color='orange', linewidth=2, label="Signal sans Windowing")
plt.plot(distances, np.real(range_profile[28, :]), color='blue', linewidth=2, label="Antenne Centrale (Cible Nette)")

plt.title(f"Profil de Distance Radar (IFFT) - {NB_FREQS} pts de fréquence")
plt.xlabel("Distance (mètres)")
plt.ylabel("Amplitude S21")
plt.xlim(0, 10) # On zoome sur les 10 premiers mètres
#plt.ylim(-110, -50)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()