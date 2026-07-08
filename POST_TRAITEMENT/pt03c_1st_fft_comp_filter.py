import numpy as np
import matplotlib.pyplot as plt
import os

print("--- ÉTAPE 3C : LABORATOIRE DE FENÊTRAGE (WINDOWING) ---")

# --- GESTION DES CHEMINS ---
dossier_courant = os.path.dirname(os.path.abspath(__file__))
DOSSIER_DATA = os.path.join(dossier_courant, "..", "DATA")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_VIRTUAL = 56
C = 3e8
N_fft_range = 1024*8 

print("Chargement de la matrice...")
CHEMIN_CIBLE = os.path.join(DOSSIER_DATA, 'cible_3m_201pts.csv')
CHEMIN_VIDE = os.path.join(DOSSIER_DATA, 'vide_3m_201pts.csv')

data_cible = np.loadtxt(CHEMIN_CIBLE, delimiter=',')
data_vide = np.loadtxt(CHEMIN_VIDE, delimiter=',')

# --- DÉTECTION DYNAMIQUE DU NOMBRE DE POINTS ---
NB_FREQS = len(data_vide) // NB_VIRTUAL
print(f"✅ Détection automatique : {NB_FREQS} points de fréquence par canal.")

f_start = data_cible[0, 2]
f_stop = data_cible[NB_FREQS-1, 2]
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_matrix = S_cible.reshape((NB_VIRTUAL, NB_FREQS)) - S_vide.reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. DÉFINITION DES FENÊTRES À TESTER
# ==========================================
# On crée un dictionnaire avec 4 fenêtres mathématiques classiques
fenetres = {
    "Rectangulaire (Brut)": np.ones(NB_FREQS),
    "Hanning (Standard)": np.hanning(NB_FREQS),
    "Hamming": np.hamming(NB_FREQS),
    "Blackman (Agressif)": np.blackman(NB_FREQS)
}

# Création de l'axe X (Distances)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 3. TRAITEMENT ET AFFICHAGE
# ==========================================
plt.figure(figsize=(12, 7))

# On boucle sur chaque fenêtre pour la calculer et la tracer
for nom_fenetre, fenetre_array in fenetres.items():
    
    # Application de la fenêtre sur la matrice
    # Numpy multiplie intelligemment notre ligne de 201 points sur les 56 antennes
    S_windowed = S_matrix * fenetre_array
    
    # IFFT sur l'axe des fréquences
    range_profile = np.fft.ifft(S_windowed, n=N_fft_range, axis=1)
    
    # Calcul de la magnitude en dB pour l'antenne centrale (Index 28)
    profil_db = 20 * np.log10(np.abs(range_profile[28, :]) + 1e-12)
    
    # Normalisation : on met le pic principal artificiellement à 0 dB pour pouvoir 
    # comparer uniquement la forme des courbes (et non leur perte d'énergie brute)
    profil_db -= np.max(profil_db)
    
    # Tracé de la courbe
    plt.plot(distances, profil_db, linewidth=2, label=nom_fenetre)

# ==============================talement ============
# 4. FINITIONS DU GRAPHIQUE
# ==========================================
plt.title("Comparaison des Fenêtres DSP (Cible à 3m)")
plt.xlabel("Distance apparente (Mètres)")
plt.ylabel("Puissance Relative normalisée (dB)")

# On zoome très fort autour de la cible (ex: de 1m à 5m) pour voir l'anatomie du pic
plt.xlim(1, 5) 

# On limite le bas du graphique pour voir le plancher de bruit
plt.ylim(-60, 5)

plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()