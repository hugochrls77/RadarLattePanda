import os
import numpy as np
import matplotlib.pyplot as plt

print("--- ÉTAPE 1 : CONTRÔLE DE LA SOUSTRACTION ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

# Modifie les noms ici pour correspondre aux fichiers que tu veux analyser
CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_51pts.csv')
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_51pts.csv')

# 1. Paramètres fixes
NB_VIRTUAL = 56

# 2. Chargement des données brutes
print(f"Chargement de {CHEMIN_VIDE}...")
data_vide = np.loadtxt(CHEMIN_VIDE, delimiter=',')
data_cible = np.loadtxt(CHEMIN_CIBLE, delimiter=',')

# --- DÉTECTION DYNAMIQUE DU NOMBRE DE POINTS ---
NB_FREQS = len(data_vide) // NB_VIRTUAL
print(f"✅ Détection automatique : {NB_FREQS} points de fréquence par canal.")

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
plt.plot(freqs/1e9, 20*np.log10(np.abs(S_matrix_net[28, :])), label="Net (Soustraction)")
plt.xlabel("Fréquence (GHz)")
plt.ylabel("Amplitude S21 (dB)")
plt.title(f"Efficacité de la soustraction du fond (Antenne virtuelle 28 - {NB_FREQS} pts)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()