import os
import numpy as np

print("--- FUSION DES DONNÉES DE CALIBRATION ---")

# Détermine le dossier courant (CALIB) où est lancé le script
dossier_courant = os.path.dirname(os.path.abspath(__file__))

# On pointe vers le sous-dossier contenant les 56 fichiers
DOSSIER_CALIB = os.path.join(dossier_courant, "Calibration_Dataset")
# On prépare le chemin d'enregistrement final (dans CALIB)
FICHIER_FINAL = os.path.join(dossier_courant, "matrice_calibration.csv")

# Paramètres logiques matériels
TX_START, TX_END = 1, 7
RX_START, RX_END = 1, 8
NB_FREQS = 201

donnees_globales = []

print(f"Recherche des fichiers dans : {DOSSIER_CALIB}...")

# On boucle selon tes index logiques (de 1 à 7 et de 1 à 8)
for num_antenne_tx in range(TX_START, TX_END + 1):
    for rx in range(RX_START, RX_END + 1):
        nom_fichier = f"calib_master_Tx{num_antenne_tx}_Rx{rx}.csv"
        chemin_complet = os.path.join(DOSSIER_CALIB, nom_fichier)
        
        if os.path.exists(chemin_complet):
            # On charge le fichier de 201 lignes
            donnees_locales = np.loadtxt(chemin_complet, delimiter=',')
            donnees_globales.append(donnees_locales)
        else:
            print(f"❌ ERREUR FATALE : Il manque le fichier {nom_fichier} ! Fusion annulée.")
            exit()

# Concaténation verticale (empilement des données)
matrice_finale = np.vstack(donnees_globales)

lignes, colonnes = matrice_finale.shape
print(f"📊 Dimension de la matrice finale : {lignes} lignes x {colonnes} colonnes.")

# Vérification : 56 combinaisons * 201 points = 11256 lignes
if lignes == 56 * NB_FREQS and colonnes == 5:
    np.savetxt(FICHIER_FINAL, matrice_finale, delimiter=',', 
               fmt=['%d', '%d', '%.2f', '%.6e', '%.6e'])
    print(f"🎉 SUCCÈS ! Fichier maître généré.")
    print(f"➡️ Sauvegardé ici : {FICHIER_FINAL}")
    print("\n💡 NOTE : Si cette calibration est validée, déplacez ce fichier dans le dossier '../DATA/' pour l'utiliser dans le POST-TRAITEMENT.")
else:
    print("⚠️ Attention, les dimensions ne correspondent pas à ce qui était attendu.")