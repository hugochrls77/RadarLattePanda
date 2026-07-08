import numpy as np
import matplotlib.pyplot as plt

print("--- CRÉATION DU PROFIL DE CALIBRATION STATIQUE (SÉCURITÉ INTÉRIEUR) ---")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_FREQS = 51
NB_VIRTUAL = 56
C = 3e8

print("Chargement des fichiers de calibration...")
data_vide = np.loadtxt('calib_vide.csv', delimiter=',')
data_cible = np.loadtxt('calib_cible.csv', delimiter=',')

f_start = data_cible[0, 2]       
f_stop = data_cible[NB_FREQS-1, 2] 
B = f_stop - f_start
delta_f = B / (NB_FREQS - 1)

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. IFFT : PASSAGE EN DISTANCE
# ==========================================
N_fft_range = 512
window_range = np.hanning(NB_FREQS)
range_profile = np.fft.ifft(S_matrix_net * window_range, n=N_fft_range, axis=1)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

# ==========================================
# 3. VERROUILLAGE DE LA CIBLE (BRIDÉ À 4 MÈTRES)
# ==========================================
# On trouve l'index du tableau correspondant à 4 mètres
LIMITE_MURS = 4.0
index_limite = np.searchsorted(distances, LIMITE_MURS)

# L'algorithme cherche l'énergie max UNIQUEMENT dans la zone autorisée
index_cible = np.argmax(np.abs(range_profile[28, :index_limite]))
dist_cible = distances[index_cible]

print(f"🎯 Verrouillage confirmé sur l'obstacle à : {dist_cible:.2f} mètres")

# ==========================================
# 4. CALCUL DU CORRECTIF DE PHASE
# ==========================================
coupe_spatiale = range_profile[:, index_cible]
phases_mesurees = np.angle(coupe_spatiale)

# On force la phase de toutes les antennes à s'aligner sur 0°
phase_ref = phases_mesurees[0]
vecteur_correction = np.exp(-1j * (phases_mesurees - phase_ref))

np.save('vecteur_calibration.npy', vecteur_correction)
print("✅ Fichier 'vecteur_calibration.npy' généré avec succès !")

# ==========================================
# 5. AFFICHAGE DE CONTRÔLE SÉCURISÉ
# ==========================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9))

# --- Graphique 1 : Vérification du verrouillage (Distance) ---
profil_db = 20 * np.log10(np.abs(range_profile[28, :]) + 1e-12)
ax1.plot(distances, profil_db, color='orange', linewidth=2, label="Profil de Distance")

# Ligne rouge pointillée sur la cible choisie par l'algorithme
ax1.axvline(x=dist_cible, color='red', linestyle='--', linewidth=2, label=f"CIBLE VERROUILLÉE ({dist_cible:.2f}m)")

# Zone grisée pour montrer ce que l'algorithme a reçu l'ordre d'ignorer
ax1.axvspan(LIMITE_MURS, 8.0, color='gray', alpha=0.3, label="Zone Murs (Ignorée par la recherche)")

ax1.set_title("Étape 1 : Validation du verrouillage de la cible (Antenne centrale)")
ax1.set_xlabel("Distance (m)")
ax1.set_ylabel("Puissance (dB)")
ax1.set_xlim(0, 8)
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.6)

# --- Graphique 2 : Vérification du redressement (Phase) ---
ax2.plot(phases_mesurees, label="Phase Brute (Avec câbles + géométrie)", marker='o', color='blue', alpha=0.6)
ax2.plot(np.angle(coupe_spatiale * vecteur_correction), label="Phase Corrigée (Forcée à 0°)", marker='x', color='green', markersize=8, linewidth=2)

ax2.set_title("Étape 2 : Validation du redressement spatial")
ax2.set_xlabel("Index Antenne Virtuelle (0 à 55)")
ax2.set_ylabel("Phase (Radians)")
ax2.set_ylim(-3.5, 3.5)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()