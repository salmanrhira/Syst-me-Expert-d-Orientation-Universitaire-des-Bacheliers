# Système Expert d'Orientation Universitaire Post-Bac (Maroc) 🎓

**Module :** Fondements Avancés de l'Intelligence Artificielle (Master IA – S1)  
**Enseignante :** Pr. Hasna ELALAOUI  
**Année universitaire :** 2026-2027  

---

## 🌟 Présentation du Projet

Ce projet implémente un **système expert d'aide à l'orientation post-baccalauréat au Maroc**, conçu pour délivrer des conseils d'orientation **personnalisés**, **explicables** et **hiérarchisés**.

Le système analyse le profil complet de l'élève (série de bac, moyenne générale, notes par matière clé, centres d'intérêt professionnels, contraintes de ville, budget annuel, préférence public/privé) et interroge une base de connaissances de **100 formations post-bac réelles au Maroc**.

Il classe les recommandations en trois catégories de risque et d'adéquation :
* 🟢 **Sûr :** Accès ouvert garanti (FSJES, FLSH, FS) ou formations professionnalisantes courtes assurées (BTS, OFPPT, EST) avec marge confortable.
* 🔵 **Réaliste :** Profil académique solide au-dessus du seuil indicatif avec équilibre entre matières clés et débouchés.
* 🟠 **Ambitieux :** Filières sélectives d'excellence à concours éliminatoire (CPGE, Médecine, Architecture ENA) ou seuil indicatif très proche de la moyenne de l'élève.

Chaque suggestion s'accompagne d'une **justification pédagogique transparente** (points forts, alertes sur les matières fragiles, mobilité de ville et alternative de repli sécurisée en cas d'échec).

---

## 📂 Structure du Répertoire

```
.
├── formations.csv              # Base de données source (100 formations avec 12 attributs)
├── build_kb.py                 # Script de conversion CSV vers faits Prolog
├── knowledge_base.pl           # Base de faits Prolog générée automatiquement
├── expert_system.pl            # Moteur d'inférence, règles d'éligibilité, scoring et explication
├── app.py                      # Interface Utilisateur moderne (IHM Streamlit)
├── DOCUMENTATION_PROJET.md     # Documentation détaillée de l'architecture
├── Mini-projet - Proposition 2.pdf # Énoncé officiel du projet
└── README.md                   # Guide d'installation et d'utilisation
```

---

## 🚀 Guide d'Utilisation

### Prérequis
1. **SWI-Prolog** (installé et accessible, ex: `C:\Program Files\swipl\bin\swipl.exe`)
2. **Python 3.10+** avec `streamlit` et `pandas`

### Option 1 : Utilisation en Console Pure Prolog

Lancez directement le conseiller interactif dans SWI-Prolog :

```powershell
swipl -s expert_system.pl -g "lancer_conseiller."
```

Le système vous posera des questions interactives sur votre Bac, votre moyenne, vos notes clés, centres d'intérêt, budget et villes, puis affichera le **Top 5 des recommandations** avec leurs explications détaillées.

Vous pouvez aussi tester des requêtes directement dans le terminal Prolog :
```prolog
?- [expert_system].
?- recommander_profil(sm, 16.5, [[maths, 17], [physique, 16]], [genie_logiciel, intelligence_artificielle], [casablanca, rabat], 0, public, 5).
```

### Option 2 : Lancer l'Interface Graphique (IHM Web Streamlit)

Pour lancer l'application web conviviale et interactive :

```powershell
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur (sur `http://localhost:8501`) avec :
* Saisie intuitive du profil (curseurs, listes déroulantes, filtres par ville et budget).
* Affichage des recommandations avec badges de statut colorés (Ambitieux / Réaliste / Sûr).
* Justifications explicatives déroulantes (points forts, alertes, solutions de repli).
* Explorateur de données pour parcourir les 100 formations du Maroc.

---

## 🧪 Régénération de la Base de Faits Prolog

Si vous modifiez ou enrichissez `formations.csv`, exécutez :

```powershell
python build_kb.py
```
Cela met à jour automatiquement `knowledge_base.pl`.
