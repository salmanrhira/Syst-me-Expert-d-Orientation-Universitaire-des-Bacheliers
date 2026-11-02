# Système Expert d'Orientation Universitaire Post-Bac (Maroc)

> **Module :** Fondements Avancés de l'Intelligence Artificielle (Master IA – S1)  
> **Enseignante :** Pr. Hasna ELALAOUI  
> **Année universitaire :** 2026-2027  

---

## 📌 Présentation du Projet

Chaque année au Maroc, les bacheliers font face à un choix crucial parmi une multitude d'établissements et de filières (Grandes écoles d'ingénieurs, management, médecine, instituts techniques, prépas CPGE, BTS, OFPPT, universités...).

Ce projet consiste à concevoir un **système expert d'orientation post-bac explicable et interactif en Prolog**, capable d'analyser le profil scolaire et les préférences d'un bachelier pour lui recommander des orientations ciblées, réalistes et justifiées.

### Fonctionnalités principales :
* **Filtrage d'éligibilité :** Vérification de la compatibilité du type de baccalauréat (SM, SPC, SVT, Économie, etc.) et des frais de scolarité par rapport au budget max.
* **Analyse des risques académiques :** Détection préventive des notes fragiles (< 12/20) dans les matières clés de la filière cible.
* **Calcul d'adéquation :** Score d'affinité combinant l'écart par rapport au seuil indicatif et la correspondance avec les centres d'intérêt / débouchés professionnels.
* **Classification tripartite :** Catégorisation claire des formations recommandées :
  * 🎯 **Ambitieux :** Filières sélectives dont le seuil est très proche de la moyenne de l'élève.
  * ⚖️ **Réaliste :** Formations en adéquation confortable avec le niveau académique.
  * 🛡️ **Sûr :** Filières à admission garantie (accès ouvert) ou marge de note très sécurisante.
* **Moteur d'explication :** Restitution en langage naturel des justifications (« Pourquoi ce choix ? », points forts, alertes de risque).

---

## 🏗️ Architecture du Projet

```
Système-Expert-d-Orientation/
├── formations.csv        # Données sources : 100 formations réelles au Maroc (12 attributs)
├── build_kb.py           # Script Python de conversion et génération automatique de la KB
├── knowledge_base.pl     # Base de faits Prolog (prédicat formation/12)
├── expert_system.pl      # Moteur d'inférence, règles d'éligibilité, scoring et explication
└── README.md             # Documentation générale du projet
```

---

## 📊 Base de Connaissances (`formations.csv` & `knowledge_base.pl`)

La base regroupe **100 formations marocaines réelles** avec 12 attributs détaillés pour chaque filière :
1. `Id` : Identifiant numérique unique (1 à 100).
2. `Nom` : Nom de l'établissement et de la filière (ex. *ENSA Marrakech*, *ENCG Casablanca*, *FST Settat*...).
3. `Type` : Type d'institution (`ecole_ingenieur`, `commerce`, `prepa`, `medecine`, `technique`, etc.).
4. `Ville` : Ville d'implantation (`casablanca`, `rabat`, `marrakech`, `agadir`, `tanger`...).
5. `BacsAcceptes` : Séries de bac éligibles (`sm`, `spc`, `svt`, `eco`, `tgc`, `ste`, `stm`, `lettres`, etc.).
6. `Seuil` : Seuil indicatif de sélection sur 20.
7. `MatieresCles` : Matières décisives pour réussir (`maths`, `physique`, `francais`, `svt`...).
8. `ModeSelection` : Modalité d'accès (`tawjihi`, `concours`, `cursussup`, `dossier`, `ouvert`).
9. `DureeAnnees` : Durée des études (2 ans pour BTS/OFPPT, 3 ans pour Licence/EST, 5 ans pour ENSA/ENCG, etc.).
10. `Debouches` : Métiers cibles pour le calcul d'affinité.
11. `Statut` : Établissement `public` ou `prive`.
12. `FraisAnnuels` : Frais de scolarité annuels en MAD (0 DH pour le public).

---

## ⚙️ Installation & Utilisation

### Prérequis
* [SWI-Prolog](https://www.swi-prolog.org/) (version 9.0 ou supérieure)
* [Python 3.10+](https://www.python.org/)

### 1. Régénérer la base de faits Prolog (optionnel)
Si `formations.csv` est mis à jour :
```bash
python build_kb.py
```

### 2. Lancer le Système Expert sous SWI-Prolog
Ouvrez un terminal et démarrez la session Prolog :
```bash
swipl expert_system.pl
```

### 3. Exemples de Requêtes Prolog

* **Tester l'éligibilité d'une formation (ex: ID 1 - ENSA Marrakech pour un Bac SPC avec budget 0 DH) :**
  ```prolog
  ?- est_eligible(1, spc, 0).
  % true.
  ```

* **Détecter les matières à risque :**
  ```prolog
  ?- matiere_faible(1, [[maths, 11], [physique, 15]], Matiere).
  % Matiere = maths.
  ```

* **Classer une formation selon une moyenne :**
  ```prolog
  ?- classer_formation(1, 14.5, Categorie).
  % Categorie = 'Ambitieux'.

  ?- classer_formation(1, 16.0, Categorie).
  % Categorie = 'Réaliste'.
  ```

* **Obtenir une explication détaillée :**
  ```prolog
  ?- expliquer(1, spc, 15.0, [[maths, 10], [physique, 16]]).
  % --- Justification pour ENSA Marrakech ---
  % - Votre Bac (spc) est accepté.
  % - Votre moyenne (15.00) dépasse le seuil indicatif (14.50).
  % - Alerte: Votre niveau en maths est considéré comme un risque pour cette filière.
  ```

---

## 🚀 Prochaines Étapes
- [ ] Déploiement d'une interface graphique interactive (Streamlit en Python reliée à SWI-Prolog).
- [ ] Intégration du prédicat d'orchestration global `recommander/2` (Top 5 pondéré).
- [ ] Rédaction du rapport théorique final (Logique des prédicats & validation des cas de test).
