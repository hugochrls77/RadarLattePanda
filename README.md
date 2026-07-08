# **📡 Projet Radar MIMO 7x8 \- Système d'Acquisition et Traitement**

Ce répertoire contient l'ensemble des codes sources pour piloter, calibrer et analyser les données d'un radar MIMO (Multiple-Input Multiple-Output) composé de 7 antennes émettrices (Tx) et 8 antennes réceptrices (Rx). Le système est architecturé autour d'un ordinateur LattePanda, contrôlant un VNA, un synthétiseur de fréquence (ADF4351) et un Arduino pour la commutation RF.

## **📂 Architecture du Dossier et Description des Fichiers**

L'architecture est structurée autour de l'acquisition matérielle, du contrôle, et du traitement des données hors-ligne.

### **1\. Code Embarqué (Microcontrôleur)**

* **switch\_config.ino**  
  * **Rôle :** Code C++ à téléverser sur l'Arduino (Leonardo intégré au LattePanda).  
  * **Fonctionnement :** Écoute le port série à 115200 bauds. Reçoit un octet envoyé par Python, le décode (Tx \* 8\) \+ Rx et bascule instantanément les 6 broches numériques (D8-D13) pour contrôler les deux switchs RF HMC321. Renvoie un caractère K (Handshake) une fois la commutation stabilisée.

### **2\. Outils de Débogage et Maintenance**

* **debug\_controle\_switch.py**  
  * **Rôle :** Outil interactif en ligne de commande pour contrôler manuellement le matériel.  
  * **Utilisation :** Permet de taper un port Tx et un port Rx directement dans la console. Idéal pour vérifier les tensions au multimètre sur les broches de l'Arduino ou pour identifier une panne matérielle (fil coupé, soudure sèche).

### **3\. Acquisition et Mesure Radar**

* **radar\_mesure\_1\_frame.py**  
  * **Rôle :** Script d'acquisition principal (Opérations courantes).  
  * **Fonctionnement :** Initialise l'ADF4351 et le VNA, puis lance un balayage complet et automatisé des 56 combinaisons Tx/Rx. Il génère le fichier de matrice .csv (101 points de fréquence par défaut).  
  * **Note matérielle :** Ce script gère nativement le fait que le port Tx8 physique n'existe pas, en limitant la boucle aux 7 antennes réelles.  
* **calibration\_loopback\_56\_combinaison.py**  
  * **Rôle :** Script d'acquisition de la "Calibration Maître" en boucle fermée (Master Loopback).  
  * **Fonctionnement :** Mesure la réponse interne du système sur une large bande (300 MHz \- 1.3 GHz, 201 points). Le script est résilient et assisté : il sauvegarde les données câble par câble, indique à l'utilisateur où se brancher par diagonales, et peut reprendre là où il s'est arrêté en cas de crash.  
* **calibration\_verification\_data.py**  
  * **Rôle :** Contrôle qualité visuel de la calibration.  
  * **Utilisation :** Lit les fichiers .csv générés par le loopback et trace des graphiques superposant les courbes (Amplitude S21) pour détecter visuellement d'éventuelles pannes avant fusion.

### **4\. Visualisation Rapide (Dashboard)**

* **radar\_affichage\_1\_frame.py**  
  * **Rôle :** Vue rapide et basique. Affiche la matrice 8x8 de couplage en dB (Heatmap) et le spectre de la diagonale active.  
* **radar\_affichage\_1\_frame\_v2.py**  
  * **Rôle :** Dashboard avancé de diagnostic RF. Génère 4 graphiques : Matrice de couplage, Magnitude S21, Phase déroulée S21, et un profil de distance 1D (IFFT) rudimentaire.

### **5\. Algorithmes de Post-Traitement (Dossier Post\_Traitement/)**

Ce dossier contient l'historique des développements analytiques (série ptXX), permettant de traiter mathématiquement les données pas à pas :

* **pt01\_soustraction.py** : Démonstration basique de la soustraction vectorielle du signal de fond (vide) par rapport à une cible.  
* **pt02\_soustraction\_matrice.py** : Extension de la soustraction du bruit de fond à l'intégralité de la matrice MIMO (56 canaux).  
* **pt03\_1st\_fft.py** : Application de la Transformée de Fourier Inverse (IFFT) pour convertir les fréquences balayées en un profil de distance 1D.  
* **pt03b\_1st\_fft\_comp\_pts.py** : Étude comparative de la résolution IFFT en fonction du nombre de points d'acquisition matérielle (51, 101, 201, 401 pts).  
* **pt03c\_1st\_fft\_comp\_filter.py** : Application et comparaison des fenêtrages de pondération (Hanning, Hamming, Blackman) pour atténuer les lobes secondaires dans le profil de distance.  
* **pt03d\_phase\_check.py** : Outil d'analyse pour vérifier la linéarité de la phase du signal S21 et détecter des sauts de phase (wrapping).  
* **pt04\_1st\_fft\_matrice.py** : Calcul systématique du profil de distance 1D généralisé sur l'ensemble de l'antenne virtuelle (56 voies).  
* **pt05\_heatmap.py** : Implémentation du *Beamforming* (Formation de Faisceau) par Double Transformée de Fourier pour obtenir l'imagerie spatiale radar (Angle vs Distance).  
* **pt06\_calcul\_calib.py** : Script d'extraction de "l'antidote" (vecteur de compensation phase/amplitude) calculé à partir d'une cible de référence centrée.  
* **pt06\_back\_projection.py** : Algorithme avancé de *Rétroprojection Temporelle* en espace cartésien (X/Y). Remplace la FFT pour corriger les effets de courbure d'onde en champ proche (Near-Field).  
* **pt07\_using\_calib.py** : Script final appliquant le vecteur de calibration généré sur de nouveaux sets de mesure pour redresser numériquement le front d'onde.

### **6\. Jeux de Données (Dossier Mesures/)**

Dossier servant de base de données contenant les fichiers .csv bruts issus des différentes campagnes de mesures :

* **Vides (vide\_3m..., set2\_vide...)** : Signaux de référence de l'environnement (Background) nécessaires pour la soustraction.  
* **Cibles (cible\_3m..., set3\_human..., set2\_tube...)** : Réflexions radar sur divers objets métalliques, humains, ou géométries de référence acquis avec différentes résolutions spectrales.

## **🚀 Guide d'Utilisation Typique (Workflow)**

**1\. Préparation Matérielle :**

* Téléverser switch\_config.ino sur l'Arduino via l'IDE.  
* Vérifier le bon fonctionnement des commutateurs avec debug\_controle\_switch.py.

**2\. Acquisition Quotidienne :**

* Placer la zone de test vide et lancer radar\_mesure\_1\_frame.py (renommer en vide.csv).  
* Placer la cible et relancer radar\_mesure\_1\_frame.py (renommer en cible.csv).  
* Utiliser radar\_affichage\_1\_frame\_v2.py pour valider que la donnée est saine.

**3\. Imagerie & Post-Traitement :**

* Placer les .csv dans Mesures/.  
* Lancer pt05\_heatmap.py ou pt06\_back\_projection.py dans le dossier Post\_Traitement/ pour reconstruire l'image spatiale de la scène.