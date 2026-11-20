# 🎓 Documentation Technique et Scientifique : Système Expert d'Orientation Universitaire Post-Bac au Maroc

**Module :** Fondements Avancés de l'Intelligence Artificielle (Master IA – S1)  
**Enseignante :** Pr. Hasna ELALAOUI  
**Année universitaire :** 2026-2027  

---

## Table des Matières
1. [Contexte et Problématique](#1-contexte-et-problématique)
2. [Fondements Théoriques des Systèmes Experts](#2-fondements-théoriques-des-systèmes-experts)
3. [Modélisation de la Base de Connaissances](#3-modélisation-de-la-base-de-connaissances)
4. [Moteur d'Inférence et Règles Métier (Prolog)](#4-moteur-dinférence-et-règles-métier-prolog)
5. [Architecture Logicielle Hybride](#5-architecture-logicielle-hybride)
6. [Validation Expérimentale et Plan de Tests](#6-validation-expérimentale-et-plan-de-tests)
7. [Guide d'Installation et d'Exécution](#7-guide-dinstallation-et-dexécution)
8. [Perspectives d'Amélioration](#8-perspectives-damélioration)

---

## 1. Contexte et Problématique

L'orientation post-baccalauréat au Maroc représente une étape critique et anxiogène pour plus de 350 000 bacheliers chaque année. Le paysage de l'enseignement supérieur marocain est caractérisé par :
- **Une forte hétérogénéité des modes d'admission :** Plateformes nationales (*Tawjihi*, *CursusSup*), concours écrits/oraux éliminatoires (Médecine, Architecture ENA, CPGE), sélection sur dossier, ou facultés à accès ouvert.
- **Une multiplicité de critères déterminants :** Séries de bac acceptées, seuils indicatifs de calcul de moyenne, notes spécifiques dans les matières clés de spécialité, contraintes géographiques régionales, budgets annuels et statuts (public vs privé).
- **Le syndrome du mauvais choix :** Le manque d'informations et l'absence de solutions de repli sécurisées conduisent souvent à des réorientations précoces ou des échecs universitaires.

**Objectif du projet :** Concevoir et implémenter un **système expert d'aide à la décision explicable**, capable d'analyser le profil complet d'un bachelier et de formuler des recommandations hiérarchisées, fiables et assorties d'une justification pédagogique claire.

---

## 2. Fondements Théoriques des Systèmes Experts

Un système expert (SE) est un programme d'intelligence artificielle symbolique conçu pour émuler le raisonnement d'un expert humain dans un domaine cognitif spécifique et restreint.

### 2.1 Composants Fondamentaux
1. **La Base de Faits (BF) :** Contient l'état courant du problème. Dans notre système, elle regroupe :
   - Les faits statiques : les caractéristiques des 100 formations universitaires du Maroc (`formation/12`).
   - Les faits dynamiques : le profil de l'élève saisi lors de la session (`profil_courant/7`).
2. **La Base de Règles (BR) :** Contient l'expertise formalisée sous forme de clauses de Horn ($A_1 \land A_2 \land \dots \land A_n \implies C$).
3. **Le Moteur d'Inférence (MI) :** Mécanisme d'exécution qui applique les règles aux faits par **unification**, **résolution SLD** et **retour sur trace (backtracking)**, implémenté nativement en **SWI-Prolog**.
4. **Le Module d'Explication :** Permet au système de justifier ses conclusions (*Pourquoi cette filière ? Quels sont les risques ? Quel est le plan de secours ?*).

### 2.2 Stratégie de Raisonnement (Chaînage Arrière)
Le moteur fonctionne principalement par **chaînage arrière (backward chaining)** guidé par les buts :
$$\text{Recommander}(\text{Profil}) \vdash \text{Filtrer}(\text{Éligibilité}) \land \text{Classer}(\text{Catégorie}) \land \text{Scorer}(\text{Score}) \land \text{TrierTopN}$$

---

## 3. Modélisation de la Base de Connaissances

La base de connaissances modélise **100 formations d'excellence et de référence** couvrant l'ensemble des 12 régions du Maroc.

### 3.1 Prédicat Fondamental `formation/12`
Dans `knowledge_base.pl`, chaque formation est formalisée par la structure unifiée suivante :
```prolog
formation(Id, Nom, Type, Ville, BacsAcceptes, Seuil, MatieresCles,
          ModeSelection, DureeAnnees, Debouches, Statut, FraisAnnuels).
```

### 3.2 Attributs et Domaines de Valeurs
| Attribut | Type | Description / Exemples |
| :--- | :--- | :--- |
| `Id` | Entier | Identifiant unique (1 à 100) |
| `Nom` | Chaîne | Libellé officiel (ex: `'ENSA Marrakech'`, `'FMP Casablanca'`) |
| `Type` | Atome | `ecole_ingenieur`, `prepa`, `medecine`, `commerce`, `technique`, etc. |
| `Ville` | Atome | `casablanca`, `rabat`, `marrakech`, `fes`, `tanger`, `agadir`, etc. |
| `BacsAcceptes` | Liste | `[sm, spc, svt]`, `[eco, tgc]`, `[toutes]`, etc. |
| `Seuil` | Flottant | Seuil indicatif de présélection sur 20 (ex: `16.5`, `14.5`, `10.0`) |
| `MatieresCles`| Liste | Matières déterminantes (`[maths, physique]`, `[economie, comptabilite]`) |
| `ModeSelection`| Atome | `concours`, `tawjihi`, `cursussup`, `dossier`, `ouvert` |
| `DureeAnnees` | Entier | Durée officielle du cursus (2, 3, 5, 6, 7 ans) |
| `Debouches` | Liste | Métiers cibles (`[genie_logiciel, cybersecurite, intelligence_artificielle]`) |
| `Statut` | Atome | `public` ou `prive` |
| `FraisAnnuels`| Entier | Frais de scolarité annuels en MAD (0 pour public, 25 000 à 105 000 pour privé) |

---

## 4. Moteur d'Inférence et Règles Métier (Prolog)

### 4.1 Éligibilité Stricte (`est_eligible_profil/5`)
Une formation $F$ est éligible pour un élève si et seulement si :
1. **Série du Bac :** La série du bachelier appartient à $F.BacsAcceptes$ ou la filière accepte $toutes$.
2. **Plafond Budgétaire :** Le budget déclaré par l'élève est supérieur ou égal aux frais annuels ($Budget \ge F.Frais$).
3. **Statut Juridique :** Le statut de $F$ correspond à la préférence de l'élève (`public`, `prive`, ou `indifferent`).
4. **Borne de Sélectivité :** Si la filière n'est pas à accès ouvert, la moyenne de l'élève ne doit pas être inférieure de plus de $1.5$ point au seuil indicatif ($Moyenne \ge F.Seuil - 1.5$).

### 4.2 Scoring Multi-Critères sur 100 Points (`calculer_score_complet/8`)
Le score agrégé combine 4 dimensions heuristiques :
$$\text{Score} = S_{\text{Intérêts}} + S_{\text{Académique}} + S_{\text{Géographique}} + S_{\text{Statut}}$$

* **Affinité Débouchés / Intérêts (Max 35 pts) :**
  $$\text{Communs} = \text{InteretsEleve} \cap F.\text{Debouches}$$
  $$S_{\text{Intérêts}} = \min(35, |\text{Communs}| \times 12)$$
* **Adéquation Académique (Max 40 pts) :**
  - Marge par rapport au seuil ($\text{Diff} = Moyenne - Seuil$) : jusqu'à 25 pts.
  - Bonus/malus basé sur la moyenne de l'élève dans les matières clés de la formation :
    $$\text{BonusCles} = \min(15, \max(-10, (MoyCles - 12.0) \times 3.75))$$
* **Adéquation Géographique (Max 15 pts) :**
  - 15 pts si la formation est située dans la ville préférée de l'élève.
  - 8 pts si située dans une autre ville acceptée.
  - 3 pts si en dehors de ses villes prioritaires (mobilité requise).
* **Adéquation Statut et Frais (Max 10 pts) :**
  - 10 pts si le statut correspond parfaitement au souhait de l'élève.

### 4.3 Classification Catégorielle Tripartite (`classer_formation/3`)
Le système classe chaque formation admissible selon son niveau de risque :
- 🟢 **Choix Sûr :**
  - Formations à accès ouvert garanti (ex: FSJES, FLSH, FS).
  - Filières courtes professionnalisantes (BTS, OFPPT, EST) avec marge confortable ($\ge +0.5$ pt).
  - Filières sélectives hors concours ultra-sélectif où la moyenne dépasse le seuil de plus de $+2.5$ pts.
- 🔵 **Choix Réaliste :**
  - Filière sélective où l'élève a une marge solide ($\text{Diff} \ge +0.8$ pt) sans risque majeur sur les matières clés.
- 🟠 **Choix Ambitieux :**
  - Filières d'excellence à concours éliminatoire (CPGE, Médecine, Architecture ENA).
  - Formations où la moyenne de l'élève est très proche du seuil indicatif ($[-0.5, +0.8[$ pt).

### 4.4 Moteur d'Explication et Alternatives de Repli (`suggerer_repli/2`)
Pour chaque recommandation, le système génère :
1. Les points forts (matières clés avec note $\ge 14/20$, marge positive).
2. Les alertes de vigilance (matières clés fragiles $< 12/20$, présence d'un concours écrit).
3. Une alternative de repli sécurisée en cas d'imprévu (ex: *FST MIPC ou EST pour les écoles d'ingénieurs* ; *ISPITS ou Licence Biologie pour Médecine*).

---

## 5. Architecture Logicielle Hybride

L'architecture est organisée selon un modèle découplé :

```
┌────────────────────────────────────────────────────────┐
│           Interface Utilisateur (app.py)               │
│          Streamlit réactif, multisélections,           │
│         curseurs, badges colorés, visualisations       │
└───────────────────────────┬────────────────────────────┘
                            │ Requête JSON structurée
                            │ (via subprocess SWI-Prolog)
┌───────────────────────────▼────────────────────────────┐
│         Moteur d'Inférence (expert_system.pl)          │
│       - Filtrage logique strict (est_eligible/5)       │
│       - Catégorisation heuristique (classer/3)         │
│       - Scoring multi-critères normalisé sur 100       │
│       - Sérialisation JSON native (library(json))      │
└───────────────────────────▲────────────────────────────┘
                            │ Chargement des faits
┌───────────────────────────┴────────────────────────────┐
│      Base de Faits Formations (knowledge_base.pl)      │
│     Générée automatiquement par build_kb.py depuis     │
│                     formations.csv                     │
└────────────────────────────────────────────────────────┘
```

---

## 6. Validation Expérimentale et Plan de Tests

Le projet intègre une suite de tests unitaires et d'intégration automatisés avec `pytest` (`tests/test_expert_system.py`) couvrant 11 scénarios critiques :
- **Intégrité des données :** 100 formations valides, aucune donnée manquante, cohérence des seuils (10 à 20) et durées (2 à 7 ans).
- **Compilation de la base de faits :** Exécution sans erreur de `build_kb.py` et présence des 100 clauses `formation/12`.
- **Syntaxe et moteur Prolog :** Chargement sans avertissement dans `swipl`.
- **Respect des contraintes budgétaires :** Garantie qu'un profil à budget 0 DH ne reçoit que des formations publiques gratuites.
- **Filtrage des séries du Bac :** Un profil Bac Lettres ne peut recevoir aucune recommandation pour des filières d'ingénieurs exclusives aux séries scientifiques.

Pour exécuter les tests automatisés :
```powershell
pytest tests/test_expert_system.py -v
```

---

## 7. Guide d'Installation et d'Exécution

### 7.1 Prérequis
1. **Python 3.10 ou supérieur**
2. **SWI-Prolog** (installé et ajouté au PATH, ex: `C:\Program Files\swipl\bin\swipl.exe`)

### 7.2 Installation des Dépendances
```powershell
pip install -r requirements.txt
```

### 7.3 Lancement Rapide (Windows)
Double-cliquez simplement sur le fichier `run.bat` à la racine du projet, ou exécutez :
```powershell
.\run.bat
```

### 7.4 Lancement Manuel
```powershell
# Option 1 : Interface Web Interactive Streamlit
streamlit run app.py

# Option 2 : Mode Console Prolog Interactif
swipl -s expert_system.pl -g "lancer_conseiller."
```

---

## 8. Perspectives d'Amélioration
- Intégration de la géolocalisation GPS précise pour le calcul automatique de distance kilométrique.
- Pondération dynamique des seuils en fonction des tendances d'admission annuelles (données historiques sur 3 ans).
- Exportation automatique du dossier d'orientation en rapport PDF officiel imprimable pour l'élève.
