import numpy as np
import matplotlib.pyplot as plt

print("--- GÉNÉRATION DE LA CALIBRATION COMPLÈTE (AMPLITUDE + PHASE) ---")

# ==========================================
# 1. PARAMÈTRES ET CHARGEMENT
# ==========================================
NB_FREQS = 201 
NB_VIRTUAL = 56
C = 3e8
N_fft_range = 1024 

data_vide = np.loadtxt('vide_3m_201pts.csv', delimiter=',')
data_cible = np.loadtxt('cible_3m_201pts.csv', delimiter=',')

f_start = data_cible[0, 2]
f_stop = data_cible[NB_FREQS-1, 2]
delta_f = (f_stop - f_start) / (NB_FREQS - 1)

S_vide = data_vide[:, 3] + 1j * data_vide[:, 4]
S_cible = data_cible[:, 3] + 1j * data_cible[:, 4]
S_matrix_net = (S_cible - S_vide).reshape((NB_VIRTUAL, NB_FREQS))

# ==========================================
# 2. VERROUILLAGE DE LA CIBLE
# ==========================================
S_windowed = S_matrix_net * np.hanning(NB_FREQS)
range_profile = np.fft.ifft(S_windowed, n=N_fft_range, axis=1)
distances = (C / 2) * np.linspace(0, 1/delta_f, N_fft_range, endpoint=False)

index_min, index_max = np.searchsorted(distances, 3.0), np.searchsorted(distances, 6.0)
tranche_cible_brute = np.abs(range_profile[28, index_min:index_max])
index_cible = index_min + np.argmax(tranche_cible_brute)

print(f"🎯 Cible verrouillée à : {distances[index_cible]:.2f} mètres")

# On extrait la tranche complexe (Phase et Amplitude)
tranche_spatiale = range_profile[:, index_cible]

# ==========================================
# 3. L'ÉGALISATION (LE SUPER-ANTIDOTE)
# ==========================================

# A. Correction d'Amplitude (Aplatir la courbe bleue)
amplitude_moyenne = np.mean(np.abs(tranche_spatiale))
correction_amplitude = amplitude_moyenne / np.abs(tranche_spatiale)

# B. Correction de Phase (Lisser la courbe violette sur l'antenne 0)
phase_reference = np.angle(tranche_spatiale[0])
ecarts_phase = np.angle(tranche_spatiale) - phase_reference
correction_phase = np.exp(-1j * ecarts_phase)

# C. Fusion (Gain réel * Vecteur de phase complexe)
vecteur_correction = correction_amplitude * correction_phase

np.save('vecteur_calibration.npy', vecteur_correction)
print("✅ Fichier 'vecteur_calibration.npy' (Amplitude + Phase) généré avec succès !")

# ==========================================
# 4. VÉRIFICATION DU RÉSULTAT (DIAGNOSTIC)
# ==========================================
tranche_caligree = tranche_spatiale * vecteur_correction

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

ax1.plot(np.abs(tranche_spatiale), marker='o', label="Avant (Motif en M)")
ax1.plot(np.abs(tranche_caligree), marker='x', linestyle='--', color='green', label="Après (Plate)")
ax1.set_title("Validation : Amplitude")
ax1.legend()

ax2.plot(np.unwrap(np.angle(tranche_spatiale)), marker='o', color='purple', label="Avant (Pente + Sauts)")
ax2.plot(np.unwrap(np.angle(tranche_caligree)), marker='x', linestyle='--', color='green', label="Après (0 Radian)")
ax2.set_title("Validation : Phase")
ax2.legend()

plt.tight_layout()
plt.show()