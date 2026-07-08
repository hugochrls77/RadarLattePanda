import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 3B : COMPARAISON DES PROFILS DE DISTANCE (CIBLES SEULES) ---")

# ==========================================
# 1. PARAMÈTRES GLOBAUX
# ==========================================
NB_VIRTUAL = 56
C = 3e8
N_fft_range = 1024 # Monté à 1024 pour bien lisser les 401 points

# Dictionnaire pour automatiser le traitement des 4 résolutions
resolutions = [51, 101, 201, 401]

plt.figure(figsize=(12, 6))

for nb_pts in resolutions:
    print(f"Traitement des données pour {nb_pts} points...")
    
    # ==========================================
    # 2. CHARGEMENT ET PRÉPARATION
    # ==========================================
    # Chargement de la cible uniquement
    fichier_cible = f'cible_3m_{nb_pts}pts.csv'
    data_cible = np.loadtxt(fichier_cible, delimiter=',')
    
    # --- POUR PLUS TARD : Chargement du vide ---
    fichier_vide = f'vide_3m_{nb_pts}pts.csv'
    data_vide = np.loadtxt(fichier_vide, delimiter=',')
    S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
    S_vide_reshape = S_vide.reshape((NB_VIRTUAL, nb_pts))
    # ------------------------------------------

    # Calcul des paramètres de fréquence spécifiques à cette résolution
    f_start = data_cible[0, 2]
    f_stop = data_cible[nb_pts-1, 2]
    B = f_stop - f_start
    delta_f = B / (nb_pts - 1)

    # Création de la matrice complexe cible
    S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
    S_cible_reshape = S_cible.reshape((NB_VIRTUAL, nb_pts))

    # --- POUR PLUS TARD : Soustraction du fond ---
    S_matrix_net = S_cible_reshape - S_vide_reshape
    # ---------------------------------------------
    
    # Pour l'instant, on travaille directement sur la cible brute
    S_matrix_work = S_vide_reshape 

    # ==========================================
    # 3. TRAITEMENT IFFT (CŒUR DU CODE)
    # ==========================================
    
    # --- POUR PLUS TARD : Fenêtrage (Hanning) ---
    # window_range = np.hanning(nb_pts)
    # S_matrix_work = S_matrix_work * window_range
    # --------------------------------------------

    # Transformée de Fourier Inverse (sans fenêtrage pour l'instant)
    range_profile = np.fft.ifft(S_matrix_work, n=N_fft_range, axis=1)

    # Création de l'axe X (Distances) qui est unique pour chaque résolution
    distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

    # Extraction de l'antenne centrale (Index 28) en Magnitude Absolue (dB)
    profil_db = 20 * np.log10(np.abs(range_profile[28, :]) + 1e-12)
    profil_ampl = np.abs(range_profile[28, :])
    profil_real = np.real(range_profile[28, :])

    # Ajout de la courbe au graphique
    plt.plot(distances, profil_ampl, linewidth=2, label=f"Cible brute ({nb_pts} pts)")


# ==========================================
# 4. AFFICHAGE DU GRAPHIQUE FINAL
# ==========================================
plt.title("Comparaison des Profils de Distance (Différentes résolutions de points)")
plt.xlabel("Distance apparente (Mètres)")
plt.ylabel("Partie réelle")

# On limite l'affichage à 25m pour bien superposer les zones de test
plt.xlim(0, 25) 
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()