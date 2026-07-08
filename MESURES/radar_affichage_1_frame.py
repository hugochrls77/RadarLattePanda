import numpy as np
import matplotlib.pyplot as plt

print("--- ANALYSE ET VISUALISATION DE LA MATRICE MIMO ---")

FICHIER_DATA = 'matrice_mimo_lattepanda.csv'

try:
    # 1. Chargement des données brutes
    donnees = np.loadtxt(FICHIER_DATA, delimiter=',')
    print(f"✅ Fichier '{FICHIER_DATA}' chargé avec succès.")
except FileNotFoundError:
    print(f"❌ Impossible de trouver le fichier '{FICHIER_DATA}'.")
    exit()

# Extraction des colonnes de la matrice
tx_col  = donnees[:, 0]
rx_col  = donnees[:, 1]
freq_col = donnees[:, 2]
reels    = donnees[:, 3]
imags    = donnees[:, 4]

# 2. Calcul de la magnitude linéaire et conversion en Décibels (dB)
# |S21| = sqrt(Re^2 + Im^2)
magnitude_lineaire = np.sqrt(reels**2 + imags**2)
# On ajoute 1e-12 pour éviter la division par zéro ou le log(0) dans le bruit
magnitude_db = 20 * np.log10(magnitude_lineaire + 1e-12)

# 3. Reconstruction de la matrice 8x8 (Moyenne de puissance sur la bande)
matrice_8x8_db = np.zeros((8, 8))

for t in range(1, 9):
    for r in range(1, 9):
        # Masque booléen pour isoler le couple (TX, RX) en cours
        masque = (tx_col == t) & (rx_col == r)
        
        if np.any(masque):
            # On fait la moyenne des dB sur les 51 points de fréquence pour ce canal
            matrice_8x8_db[t-1, r-1] = np.mean(magnitude_db[masque])
        else:
            matrice_8x8_db[t-1, r-1] = -90 # Valeur de bruit par défaut si non mesuré

# ==========================================
# 4. CONSTRUCTION DES GRAPHIQUE (MATPLOTLIB)
# ==========================================
fig = plt.figure(figsize=(15, 6))
fig.canvas.manager.set_window_title("Analyseur Radar MIMO 8x8 - MUGORC")

# --- GRAPHIQUE 1 : CARTE DE CHALEUR TRIDIMENSIONNELLE (HEATMAP) ---
ax1 = fig.add_subplot(121)
# 'viridis' ou 'plasma' sont d'excellents choix de colormaps radar
im = ax1.imshow(matrice_8x8_db, cmap='viridis', aspect='equal', origin='upper', vmin=-60, vmax=0)

ax1.set_title("Carte de Couplage MIMO 8x8\n(Puissance moyenne du canal)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Canaux de Réception (RX)", fontsize=10)
ax1.set_ylabel("Canaux d'Émission (TX)", fontsize=10)

# Configuration propre des axes de 1 à 8
ax1.set_xticks(range(8))
ax1.set_xticklabels([f"RX{i}" for i in range(1, 9)])
ax1.set_yticks(range(8))
ax1.set_yticklabels([f"TX{i}" for i in range(1, 9)])

# Ajout de la barre d'échelle des dB
cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label("Niveau du Signal $S_{21}$ (dB)", fontsize=10)

# --- GRAPHIQUE 2 : SPECTRE S21 DE LA DIAGONALE ACTIVE ---
ax2 = fig.add_subplot(122)

couleurs = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

trace_active = False
for i in range(1, 9):
    masque_diag = (tx_col == i) & (rx_col == i)
    
    if np.any(masque_diag):
        trace_active = True
        # Conversion de l'axe X en MHz pour une lecture plus simple
        frequences_mhz = freq_col[masque_diag] / 1e6
        spectre_db = magnitude_db[masque_diag]
        
        ax2.plot(frequences_mhz, spectre_db, label=f"Voie {i} (TX{i}➔RX{i})", color=couleurs[i-1], linewidth=2)

ax2.set_title("Spectre Réel $S_{21}$ des Canaux Actifs\n(Réponse fréquentielle)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Fréquence (MHz)", fontsize=10)
ax2.set_ylabel("Gain de Transmission (dB)", fontsize=10)
ax2.set_ylim([-20, 5]) # Centré sur tes -5 dB attendus
ax2.grid(True, linestyle='--', alpha=0.6)

if trace_active:
    ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)
else:
    ax2.text(0.5, 0.5, "Aucune donnée sur la diagonale\n(Vérifie tes indices TX == RX)", 
             ha='center', va='center', transform=ax2.transAxes, color='red', fontsize=12)

# Optimisation de l'affichage de la fenêtre
plt.tight_layout()

# Sauvegarde automatique de l'image sur ton bureau/dossier courant
plt.savefig('rendu_radar_mimo.png', dpi=300)
print("💾 Graphique haute définition sauvegardé sous le nom 'rendu_radar_mimo.png'.")

# Affichage de la fenêtre interactive à l'écran
plt.show()