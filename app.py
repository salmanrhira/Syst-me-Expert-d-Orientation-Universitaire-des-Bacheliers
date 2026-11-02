"""
Interface Utilisateur (IHM) : Système Expert d'Orientation Post-Bac au Maroc
Développé avec Streamlit et interconnecté en temps réel avec le moteur Prolog (expert_system.pl).
Module : Fondements Avancés de l'IA (Master IA - S1) - Pr. Hasna ELALAOUI
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
import streamlit as st
import pandas as pd

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Système Expert d'Orientation Post-Bac Maroc",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Répertoire de base du projet
BASE_DIR = Path(__file__).parent.resolve()
EXPERT_PL_PATH = str(BASE_DIR / "expert_system.pl")

# Recherche de l'exécutable swipl
def find_swipl_executable() -> str:
    candidate = shutil.which("swipl")
    if candidate:
        return candidate
    common_paths = [
        r"C:\Program Files\swipl\bin\swipl.exe",
        r"C:\Program Files (x86)\swipl\bin\swipl.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\swipl\bin\swipl.exe"),
    ]
    for p in common_paths:
        if Path(p).exists():
            return p
    return "swipl"

SWIPL_PATH = find_swipl_executable()

@st.cache_data(show_spinner=False)
def interroger_systeme_expert(bac: str, moyenne: float, notes_tuple: tuple,
                              interets_tuple: tuple, villes_tuple: tuple, budget: int,
                              statut: str, top_n: int = 5):
    """
    Appelle le moteur d'inférence SWI-Prolog et récupère les recommandations au format JSON.
    La fonction est mise en cache pour une réactivité instantanée dès qu'un paramètre change.
    """
    notes_prolog = "[" + ", ".join([f"[{m}, {float(n):.1f}]" for m, n in notes_tuple]) + "]"
    interets_prolog = "[" + ", ".join(interets_tuple) + "]"
    villes_prolog = "[" + ", ".join(villes_tuple) + "]"
    
    query = (
        f"recommander_json({bac}, {moyenne:.2f}, {notes_prolog}, {interets_prolog}, "
        f"{villes_prolog}, {budget}, {statut}, {top_n}), halt."
    )
    
    cmd = [
        SWIPL_PATH,
        "-q",
        "-s", EXPERT_PL_PATH,
        "-g", query
    ]
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10
        )
        if proc.returncode != 0 and not proc.stdout.strip():
            st.error(f"Erreur d'exécution Prolog : {proc.stderr}")
            return []
        
        raw_output = proc.stdout.strip()
        if not raw_output:
            return []
            
        # Extraction robuste du bloc JSON délimité par [ ... ]
        start = raw_output.find("[")
        end = raw_output.rfind("]")
        if start != -1 and end != -1 and end >= start:
            json_str = raw_output[start:end+1]
            return json.loads(json_str)
        else:
            return []
    except Exception as e:
        st.error(f"Exception lors de la communication avec le moteur Prolog : {e}")
        return []

# --- En-tête de l'application ---
st.title("🎓 Système Expert d'Orientation Post-Bac au Maroc")
st.markdown("""
**Module :** Fondements Avancés de l'IA (Master IA - S1) | **Enseignante :** Pr. Hasna ELALAOUI  
Ce système expert interactif interroge en temps réel un **moteur d'inférence en Prolog pur** relié à une base de **100 formations marocaines**.  
*Toute modification de vos critères ci-contre recalcule instantanément vos recommandations.*
""")
st.divider()

# --- Barre latérale : Saisie dynamique du Profil ---
with st.sidebar:
    st.header("👤 Profil du Bachelier")
    
    # 1. Série de Bac
    dict_bacs = {
        "sm": "Sciences Mathématiques (SM - A & B)",
        "spc": "Physique - Chimie (SPC)",
        "svt": "Sciences de la Vie et de la Terre (SVT)",
        "eco": "Sciences Économiques (ÉCO)",
        "tgc": "Techniques de Gestion et Comptabilité (TGC)",
        "ste": "Sciences et Technologies Électriques (STE)",
        "stm": "Sciences et Technologies Mécaniques (STM)",
        "lettres": "Lettres",
        "humaines": "Sciences Humaines",
        "arts_appliques": "Arts Appliqués"
    }
    
    bac_selection = st.selectbox(
        "1. Série du Baccalauréat :",
        options=list(dict_bacs.keys()),
        format_func=lambda k: dict_bacs[k],
        index=0,
        key="bac_input"
    )
    
    # 2. Moyenne générale
    moyenne_bac = st.slider(
        "2. Moyenne générale au Bac (/20) :",
        min_value=10.0,
        max_value=20.0,
        value=15.5,
        step=0.1,
        key="moyenne_input"
    )
    
    # 3. Notes clés adaptées selon la filière du Bac
    st.subheader("📝 3. Notes dans les Matières Clés")
    
    col_n1, col_n2 = st.columns(2)
    notes_dict = {}
    
    if bac_selection in ["sm", "spc", "svt"]:
        with col_n1:
            notes_dict["maths"] = st.number_input("Mathématiques :", 0.0, 20.0, 16.0, 0.5, key="n_maths")
            notes_dict["physique"] = st.number_input("Physique-Chimie :", 0.0, 20.0, 15.0, 0.5, key="n_phys")
            notes_dict["svt"] = st.number_input("SVT :", 0.0, 20.0, 14.0, 0.5, key="n_svt")
        with col_n2:
            notes_dict["francais"] = st.number_input("Français :", 0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes_dict["anglais"] = st.number_input("Anglais :", 0.0, 20.0, 15.0, 0.5, key="n_ang")
            notes_dict["philosophie"] = st.number_input("Philosophie :", 0.0, 20.0, 13.0, 0.5, key="n_philo")
            
    elif bac_selection in ["ste", "stm"]:
        with col_n1:
            notes_dict["maths"] = st.number_input("Mathématiques :", 0.0, 20.0, 15.0, 0.5, key="n_maths")
            notes_dict["physique"] = st.number_input("Physique :", 0.0, 20.0, 14.0, 0.5, key="n_phys")
            notes_dict["technologie"] = st.number_input("Sc. de l'Ingénieur :", 0.0, 20.0, 16.0, 0.5, key="n_tech")
        with col_n2:
            notes_dict["francais"] = st.number_input("Français :", 0.0, 20.0, 13.0, 0.5, key="n_fr")
            notes_dict["anglais"] = st.number_input("Anglais :", 0.0, 20.0, 14.0, 0.5, key="n_ang")
            notes_dict["philosophie"] = st.number_input("Philosophie :", 0.0, 20.0, 12.0, 0.5, key="n_philo")

    elif bac_selection in ["eco", "tgc"]:
        with col_n1:
            notes_dict["economie"] = st.number_input("Économie Générale :", 0.0, 20.0, 15.5, 0.5, key="n_eco")
            notes_dict["comptabilite"] = st.number_input("Comptabilité :", 0.0, 20.0, 15.0, 0.5, key="n_compta")
            notes_dict["maths"] = st.number_input("Mathématiques :", 0.0, 20.0, 13.5, 0.5, key="n_maths")
        with col_n2:
            notes_dict["francais"] = st.number_input("Français :", 0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes_dict["anglais"] = st.number_input("Anglais :", 0.0, 20.0, 14.5, 0.5, key="n_ang")
            notes_dict["philosophie"] = st.number_input("Philosophie :", 0.0, 20.0, 13.0, 0.5, key="n_philo")

    elif bac_selection in ["lettres", "humaines"]:
        with col_n1:
            notes_dict["francais"] = st.number_input("Français :", 0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes_dict["arabe"] = st.number_input("Arabe :", 0.0, 20.0, 15.0, 0.5, key="n_arabe")
            notes_dict["litterature"] = st.number_input("Littérature :", 0.0, 20.0, 14.5, 0.5, key="n_litt")
        with col_n2:
            notes_dict["histoire"] = st.number_input("Histoire-Géo :", 0.0, 20.0, 13.5, 0.5, key="n_hist")
            notes_dict["philosophie"] = st.number_input("Philosophie :", 0.0, 20.0, 14.0, 0.5, key="n_philo")
            notes_dict["anglais"] = st.number_input("Anglais :", 0.0, 20.0, 15.0, 0.5, key="n_ang")

    else: # arts_appliques
        with col_n1:
            notes_dict["dessin"] = st.number_input("Dessin & Arts :", 0.0, 20.0, 16.0, 0.5, key="n_dessin")
            notes_dict["creativite"] = st.number_input("Créativité :", 0.0, 20.0, 16.0, 0.5, key="n_crea")
            notes_dict["francais"] = st.number_input("Français :", 0.0, 20.0, 14.0, 0.5, key="n_fr")
        with col_n2:
            notes_dict["philosophie"] = st.number_input("Philosophie :", 0.0, 20.0, 13.0, 0.5, key="n_philo")
            notes_dict["anglais"] = st.number_input("Anglais :", 0.0, 20.0, 14.0, 0.5, key="n_ang")
            notes_dict["maths"] = st.number_input("Mathématiques :", 0.0, 20.0, 12.0, 0.5, key="n_maths")

    # 4. Centres d'intérêt professionnels
    st.subheader("🎯 4. Centres d'Intérêt")
    
    # Définition des intérêts suggérés selon la série
    if bac_selection in ["sm", "spc", "svt"]:
        def_interets = ["genie_logiciel", "intelligence_artificielle"]
    elif bac_selection in ["ste", "stm"]:
        def_interets = ["electronique", "mecanique"]
    elif bac_selection in ["eco", "tgc"]:
        def_interets = ["finance", "marketing"]
    elif bac_selection in ["lettres", "humaines"]:
        def_interets = ["droit_affaires", "communication"]
    else:
        def_interets = ["design", "architecture"]
        
    tous_interets = [
        "genie_logiciel", "intelligence_artificielle", "cybersecurite", "reseaux", 
        "data_science", "genie_civil", "genie_industriel", "mecanique", "electronique", "telecom",
        "medecine_generale", "chirurgie", "dentaire", "soins_infirmiers", "biologie",
        "finance", "audit", "marketing", "commerce_international", "gestion_entreprise", "comptabilite", "banque",
        "droit_affaires", "justice", "diplomatie", "journalisme", "communication", "traduction", 
        "relations_internationales", "enseignement_francais", "enseignement_anglais",
        "architecture", "urbanisme", "design", "arts_graphiques"
    ]
    
    interets_selectionnes = st.multiselect(
        "Domaines et métiers souhaités :",
        options=tous_interets,
        default=def_interets,
        key=f"interets_input_{bac_selection}"
    )
    
    # 5. Villes prioritaires
    st.subheader("📍 5. Villes & Mobilité")
    villes_possibles = [
        "casablanca", "rabat", "marrakech", "fes", "tanger", "agadir", "oujda",
        "kenitra", "settat", "meknes", "el_jadida", "tetouan", "benguerir", "ifrane",
        "safi", "sale", "berrechid", "khouribga", "al_hoceima", "dakhla"
    ]
    villes_selectionnees = st.multiselect(
        "Villes préférées (par ordre de priorité) :",
        options=villes_possibles,
        default=["casablanca", "rabat"],
        key="villes_input"
    )
    
    # 6. Budget et Statut
    st.subheader("💰 6. Budget & Statut")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        budget_annuel = st.number_input(
            "Budget max (DH) :",
            min_value=0,
            max_value=150000,
            value=0,
            step=5000,
            key="budget_input",
            help="0 DH pour cibler exclusivement les établissements publics gratuits."
        )
    with col_b2:
        statut_pref = st.selectbox(
            "Statut d'établissement :",
            options=["public", "prive", "indifferent"],
            format_func=lambda s: {"public": "Public uniquement", "prive": "Privé uniquement", "indifferent": "Indifférent"}[s],
            key="statut_input"
        )
        
    top_n = st.slider("Nombre de recommandations :", min_value=3, max_value=10, value=5, key="top_n_input")
    
    if st.button("🔄 Réinitialiser le cache / Recalculer", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Préparation des structures sérialisables en tuples pour le cache
notes_tuple = tuple((m, float(notes_dict[m])) for m in notes_dict)
interets_tuple = tuple(interets_selectionnes) if interets_selectionnes else tuple()
villes_tuple = tuple(villes_selectionnees) if villes_selectionnees else tuple()

# --- Calcul instantané et réactif des recommandations ---
resultats = interroger_systeme_expert(
    bac=bac_selection,
    moyenne=moyenne_bac,
    notes_tuple=notes_tuple,
    interets_tuple=interets_tuple,
    villes_tuple=villes_tuple,
    budget=budget_annuel,
    statut=statut_pref,
    top_n=top_n
)

# --- Zone Principale d'Affichage ---
tab_recommandations, tab_explications, tab_base = st.tabs([
    "🏆 Top Recommandations Personnalisées", 
    "💡 Comment fonctionne le Moteur d'Inférence ?", 
    "📚 Base de Connaissances (100 Formations)"
])

with tab_recommandations:
    # Bandeau d'état récapitulatif
    st.info(
        f"📋 **Profil analysé en direct :** Bac **{dict_bacs[bac_selection]}** | "
        f"Moyenne : **{moyenne_bac:.2f}/20** | "
        f"Budget max : **{budget_annuel:,} DH** | "
        f"Statut : **{statut_pref.capitalize()}** | "
        f"Intérêts : *{', '.join(interets_selectionnes) if interets_selectionnes else 'Aucun filtre'}*"
    )

    if not resultats:
        st.warning(
            "⚠️ **Aucune formation ne correspond strictement à cette combinaison de critères.**\n\n"
            "Conseils du conseiller expert :\n"
            "* Élargissez vos critères budgétaires si vous visez le privé.\n"
            "* Élargissez la sélection des villes acceptées.\n"
            "* Vérifiez que votre moyenne est suffisante pour les seuils de présélection."
        )
    else:
        st.subheader(f"✨ Top {len(resultats)} Recommandations Classées par Adéquation")
        
        for item in resultats:
            cat = item.get("categorie", "Réaliste")
            
            # Badge et style selon la catégorie
            if cat == "Ambitieux":
                cat_badge = "🟠 **Choix Ambitieux** (Filière d'excellence / Concours sélectif ou seuil proche)"
                badge_color = "#FF9800"
            elif cat == "Réaliste":
                cat_badge = "🔵 **Choix Réaliste** (Très bonne adéquation profil / Seuil confortable)"
                badge_color = "#2196F3"
            else: # Sûr
                cat_badge = "🟢 **Choix Sûr** (Accès ouvert garanti ou seuil largement dépassé)"
                badge_color = "#4CAF50"

            with st.container():
                col_gauche, col_droite = st.columns([3, 1])
                
                with col_gauche:
                    st.markdown(f"### Rang #{item['rang']} : {item['nom']}")
                    st.markdown(
                        f"{cat_badge} &nbsp;|&nbsp; 📍 **Ville :** {item['ville'].capitalize()} &nbsp;|&nbsp; "
                        f"⏱️ **Durée :** {item['duree']} ans &nbsp;|&nbsp; 🏛️ **Statut :** {item['statut'].capitalize()}"
                    )
                
                with col_droite:
                    score = item['score']
                    st.metric(label="Score d'adéquation", value=f"{score}/100")
                
                # Volet déroulant explicatif
                with st.expander("🔍 Justification détaillée & Conseils du Système Expert", expanded=(item['rang'] <= 2)):
                    col_det1, col_det2 = st.columns(2)
                    
                    with col_det1:
                        st.markdown("**Points Forts du Profil :**")
                        st.write(f"• **Baccalauréat :** Série `{bac_selection.upper()}` acceptée.")
                        
                        diff = item.get("diff", 0.0)
                        if item['mode_selection'] == 'ouvert':
                            st.write(f"• **Admission :** Accès ouvert garanti sans seuil éliminatoire.")
                        elif diff >= 0:
                            st.write(f"• **Moyenne :** Votre note (+{diff:.2f} pts) dépasse le seuil indicatif ({item['seuil']}/20).")
                        else:
                            st.write(f"• **Attention seuil :** Note légèrement en dessous du seuil indicatif ({diff:.2f} pts).")
                            
                        interets_c = item.get("interets_communs", [])
                        if interets_c:
                            st.write(f"• **Débouchés en phase :** `{', '.join(interets_c)}`.")
                            
                        points_f = item.get("points_forts", [])
                        if points_f:
                            st.write(f"• **Matières clés solides :** `{', '.join(points_f)}` (≥ 14/20).")

                    with col_det2:
                        st.markdown("**Alertes & Risques Potentiels :**")
                        alertes = item.get("alertes", [])
                        if alertes:
                            st.warning(f"⚠️ Matières clés fragiles : `{', '.join(alertes)}` (< 12/20).")
                        else:
                            st.success("✅ Aucune matière clé en dessous de 12/20.")
                            
                        if item['mode_selection'] == 'concours':
                            st.info("ℹ️ Filière soumise à un concours d'entrée éliminatoire.")
                        
                        if villes_selectionnees and item['ville'] not in villes_selectionnees:
                            st.warning(f"🚗 Mobilité : Située à {item['ville'].capitalize()}, en dehors de vos villes prioritaires.")
                            
                        st.markdown("**🛡️ Alternative de repli conseillée :**")
                        st.info(f"*{item.get('repli', 'Faculté des Sciences ou OFPPT')}*")

                st.divider()

with tab_explications:
    st.markdown("""
    ### Architecture et Logique d'Inférence du Système Expert
    
    Le système expert applique un modèle de raisonnement déductif structuré en 4 étapes :
    
    1. **Filtrage d'Éligibilité Stricte (`est_eligible_profil/5`) :**
       * Vérification de la compatibilité de la série de Baccalauréat (`AcceptedBacs`).
       * Respect du plafond budgétaire de l'élève (`BudgetMax >= AnnualFees`).
       * Filtre du statut juridique souhaité (Public / Privé / Indifférent).
       * Élimination des filières sélectives hors de portée ($Moyenne < Seuil - 1.5$).
    
    2. **Calcul du Score d'Adéquation Multi-Critères (sur 100 points) :**
       * **Affinité Débouchés / Intérêts (Max 35 pts) :** Calcul de l'intersection entre les centres d'intérêt de l'élève et les débouchés réels de la filière.
       * **Adéquation Académique (Max 40 pts) :** Marge par rapport au seuil indicatif de présélection, pondéré par les notes effectives dans les matières clés de la filière.
       * **Adéquation Géographique (Max 15 pts) :** Bonus prioritaire pour la ville préférée de l'élève.
       * **Adéquation Statut et Frais (Max 10 pts) :** Conformité avec les souhaits de coût et de statut juridique.
    
    3. **Catégorisation des Recommandations (`classer_formation/3`) :**
       * **Choix Sûr :** Formations à accès ouvert (FSJES, FLSH, FS) ou formations professionnalisantes courtes (BTS, OFPPT, EST) avec marge confortable.
       * **Choix Réaliste :** Profil académique solide au-dessus du seuil indicatif sans alerte critique sur les matières clés.
       * **Choix Ambitieux :** Filières d'excellence à fort concours sélectif (CPGE, Médecine, ENA) ou seuil indicatif très proche de la moyenne.
    
    4. **Moteur d'Explication et de Repli (`expliquer_detail/6`) :**
       * Pour chaque recommandation, le système justifie les raisons positives, signale les risques et préconise une **alternative de repli sécurisée** en cas d'imprévu.
    """)

with tab_base:
    st.markdown("### Exploration des 100 Formations Référencées au Maroc")
    csv_file = Path("formations.csv")
    if csv_file.exists():
        df = pd.read_csv(csv_file)
        
        col_filtre1, col_filtre2 = st.columns(2)
        with col_filtre1:
            ville_f = st.multiselect("Filtrer par ville :", options=sorted(df["City"].unique()), key="f_ville")
        with col_filtre2:
            type_f = st.multiselect("Filtrer par type :", options=sorted(df["Type"].unique()), key="f_type")
            
        df_display = df.copy()
        if ville_f:
            df_display = df_display[df_display["City"].isin(ville_f)]
        if type_f:
            df_display = df_display[df_display["Type"].isin(type_f)]
            
        st.dataframe(df_display, use_container_width=True, height=450)
        st.caption(f"Affichage de {len(df_display)} formation(s) sur {len(df)} au total.")
