import numpy as np
import matplotlib.pyplot as plt

print("--- ANALYSE ET VISUALISATION AVANCÉE DE LA MATRICE MIMO ---")

FICHIER_DATA = 'test.csv'

try:
    donnees = np.loadtxt(FICHIER_DATA, delimiter=',')
    print(f"✅ Fichier '{FICHIER_DATA}' chargé avec succès.")
except FileNotFoundError:
    print(f"❌ Impossible de trouver le fichier '{FICHIER_DATA}'.")
    exit()

# Extraction des colonnes
tx_col   = donnees[:, 0]
rx_col   = donnees[:, 1]
freq_col = donnees[:, 2]
reels    = donnees[:, 3]
imags    = donnees[:, 4]

# Signal Complexe S21 = Re + j*Im
signal_complexe = reels + 1j * imags

# Calculs de base
magnitude_lineaire = np.abs(signal_complexe)
magnitude_db = 20 * np.log10(magnitude_lineaire + 1e-12)

# Construction de la Heatmap 8x8
matrice_8x8_db = np.zeros((8, 8))
for t in range(1, 9):
    for r in range(1, 9):
        masque = (tx_col == t) & (rx_col == r)
        if np.any(masque):
            matrice_8x8_db[t-1, r-1] = np.mean(magnitude_db[masque])
        else:
            matrice_8x8_db[t-1, r-1] = -90

# ==========================================
# PRÉPARATION DU DASHBOARD MATPLOTLIB (2x2)
# ==========================================
fig = plt.figure(figsize=(18, 10))
fig.canvas.manager.set_window_title("Tableau de Bord Radar MIMO - Diagnostic Matériel")
couleurs = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

# ---------------------------------------------------------
# GRAPH 1 (Haut-Gauche) : CARTE DE COUPLAGE (HEATMAP)
# ---------------------------------------------------------
ax1 = fig.add_subplot(221)
im = ax1.imshow(matrice_8x8_db, cmap='plasma', aspect='equal', origin='upper', vmin=-60, vmax=0)
ax1.set_title("Carte de Couplage (Moyenne dB)", fontweight='bold')
ax1.set_xticks(range(8)); ax1.set_xticklabels([f"RX{i}" for i in range(1, 9)])
ax1.set_yticks(range(8)); ax1.set_yticklabels([f"TX{i}" for i in range(1, 9)])
fig.colorbar(im, ax=ax1, label="Signal $S_{21}$ (dB)")

# Variables pour le traitement IFFT (Graph 2)
bande_passante_hz = np.max(freq_col) - np.min(freq_col)
nb_points = 51
vitesse_lumiere = 3e8
dt = 1 / bande_passante_hz if bande_passante_hz > 0 else 1
axe_distance = np.arange(nb_points) * (dt * vitesse_lumiere / 2)

ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223)
ax4 = fig.add_subplot(224)

trace_active = False

# Analyse détaillée de la Diagonale (TX = RX)
for i in range(1, 9):
    masque_diag = (tx_col == i) & (rx_col == i)
    
    if np.any(masque_diag):
        trace_active = True
        freqs_mhz = freq_col[masque_diag] / 1e6
        mag_db = magnitude_db[masque_diag]
        sig_cplx = signal_complexe[masque_diag]
        
        # ---------------------------------------------------------
        # GRAPH 3 (Bas-Gauche) : MAGNITUDE (Réponse en Fréquence)
        # ---------------------------------------------------------
        ax3.plot(freqs_mhz, mag_db, label=f"Voie {i}", color=couleurs[i-1], linewidth=1.5)
        
        # ---------------------------------------------------------
        # GRAPH 4 (Bas-Droite) : PHASE (Enroulée, en Degrés)
        # ---------------------------------------------------------
        # np.angle donne la phase brute entre -Pi et +Pi. On convertit directement en degrés.
        phase_degres = np.degrees(np.angle(sig_cplx))
        ax4.plot(freqs_mhz, phase_degres, color=couleurs[i-1], linewidth=1.5)
        
        # ---------------------------------------------------------
        # GRAPH 2 (Haut-Droite) : IFFT (Profil de Distance 1D)
        # ---------------------------------------------------------
        fenetre = np.blackman(len(sig_cplx))
        reponse_impulsionnelle = np.fft.ifft(sig_cplx * fenetre)
        reponse_db = 20 * np.log10(np.abs(reponse_impulsionnelle) + 1e-12)
        
        reponse_db -= np.max(reponse_db)
        ax2.plot(axe_distance, reponse_db, color=couleurs[i-1], linewidth=1.5)

# Finition Graph 2 (Distance)
ax2.set_title("Profil de Distance 1D (Test IFFT)", fontweight='bold')
ax2.set_xlabel("Distance apparente (Mètres)")
ax2.set_ylabel("Amplitude Normalisée (dB)")
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_xlim([0, np.max(axe_distance) / 2]) 

# Finition Graph 3 (Magnitude)
ax3.set_title("Spectre de Magnitude", fontweight='bold')
ax3.set_xlabel("Fréquence (MHz)")
ax3.set_ylabel("Gain $S_{21}$ (dB)")
ax3.grid(True, linestyle='--', alpha=0.6)
if trace_active: ax3.legend(loc='lower right', fontsize=8)

# Finition Graph 4 (Phase)
ax4.set_title("Phase Brute ($S_{21}$)", fontweight='bold')
ax4.set_xlabel("Fréquence (MHz)")
ax4.set_ylabel("Phase (Degrés)")
# Forcer les graduations typiques des analyseurs de réseau (-180, -90, 0, 90, 180)
ax4.set_yticks(np.arange(-180, 181, 90))
ax4.set_ylim([-190, 190]) # Légère marge pour ne pas coller la courbe aux bords
ax4.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('dashboard_radar_mimo.png', dpi=300)
print("💾 Dashboard haute définition sauvegardé sous le nom 'dashboard_radar_mimo.png'.")
plt.show()
