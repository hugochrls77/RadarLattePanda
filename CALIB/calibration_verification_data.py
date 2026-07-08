import os
import numpy as np
import matplotlib.pyplot as plt

print("--- VÉRIFICATION DES MESURES DE CALIBRATION (S21) ---")

DOSSIER_CALIB = "Calibration_Dataset"

# Configuration de la fenêtre d'affichage (Grille 2 lignes x 4 colonnes = 8 cases)
# On partagera les axes X et Y pour faciliter la comparaison visuelle entre les Tx
fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=True, sharey=True)
axes = axes.flatten() # Permet d'itérer facilement sur les axes en 1D

fichiers_manquants = 0

# Boucle sur les 7 Émetteurs (Tx)
for tx in range(1, 8):
    ax = axes[tx - 1]
    
    # Boucle sur les 8 Récepteurs (Rx) pour superposer les courbes
    for rx in range(1, 9):
        nom_fichier = f"calib_master_Tx{tx}_Rx{rx}.csv"
        chemin_complet = os.path.join(DOSSIER_CALIB, nom_fichier)
        
        if os.path.exists(chemin_complet):
            # Chargement des données
            data = np.loadtxt(chemin_complet, delimiter=',')
            
            # Extraction des colonnes (Fréquence en MHz pour l'affichage)
            freqs_mhz = data[:, 2] / 1e6 
            reels = data[:, 3]
            imags = data[:, 4]
            
            # Calcul du module (Amplitude S21) en dB
            S21_complexe = reels + 1j * imags
            S21_dB = 20 * np.log10(np.abs(S21_complexe) + 1e-12)
            
            # Tracé de la courbe
            ax.plot(freqs_mhz, S21_dB, label=f'Rx{rx}')
        else:
            print(f"⚠️ Fichier introuvable : {nom_fichier}")
            fichiers_manquants += 1
            
    # Habillage de chaque sous-graphique
    ax.set_title(f"Émetteur Tx{tx}", fontweight='bold')
    ax.grid(color='gray', linestyle='--', alpha=0.5)
    
    # On ajoute la légende uniquement sur le premier graphique pour ne pas surcharger
    if tx == 1:
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), 
                  ncol=4, fontsize='small')

# Ajout des labels sur les axes externes uniquement
for ax in axes[4:7]:
    ax.set_xlabel("Fréquence (MHz)", fontweight='bold')
for ax in [axes[0], axes[4]]:
    ax.set_ylabel("Amplitude S21 (dB)", fontweight='bold')

# Masquage de la 8ème case (car on a que 7 Tx)
axes[7].axis('off')

# Titre global et ajustement des marges
plt.suptitle("Contrôle Qualité : Amplitude S21 de la Matrice de Calibration", fontsize=16, y=0.98)
plt.tight_layout()
plt.subplots_adjust(bottom=0.15) # Laisse de la place pour la légende du Tx1

if fichiers_manquants == 0:
    print("✅ Les 56 fichiers ont été trouvés et traités avec succès.")
else:
    print(f"❌ Impossible d'afficher correctement, il manque {fichiers_manquants} fichiers.")

print("📊 Affichage des courbes en cours...")
plt.show()
