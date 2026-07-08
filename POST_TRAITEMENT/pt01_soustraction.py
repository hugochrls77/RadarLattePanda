import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 1 : CONTRÔLE DE LA SOUSTRACTION ---")

# 1. Paramètres
NB_FREQS = 51
NB_VIRTUAL = 56

# 2. Chargement des données brutes
data_vide = np.loadtxt('matrice_vide.csv', delimiter=',')
data_cible = np.loadtxt('matrice_cible.csv', delimiter=',')

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]

# 3. Extraction des fréquences
f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
freqs = np.linspace(f_start, f_stop, NB_FREQS)

# 4. Mathématiques de base
S_matrix_vide = S_vide.reshape((NB_VIRTUAL, NB_FREQS))
S_matrix_cible = S_cible.reshape((NB_VIRTUAL, NB_FREQS))
S_matrix_net = S_matrix_cible - S_matrix_vide

# 5. Affichage pour l'antenne centrale (Index 28)
plt.figure(figsize=(10, 4))
plt.plot(freqs/1e9, 20*np.log10(np.abs(S_matrix_cible[28, :])), label="Brut (Cible + Pièce)")
plt.plot(freqs/1e9, 20*np.log10(np.abs(S_matrix_net[28, :])), label="Nettoyé (Cible isolée)")
plt.title("Réponse en Fréquence S21 - Antenne Virtuelle 28")
plt.xlabel("Fréquence (GHz)")
plt.ylabel("Magnitude (dB)")
plt.legend()
plt.grid(True)
plt.show()
