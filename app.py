"""
Système Expert d'Orientation Post-Bac au Maroc
Module : Fondements Avancés de l'IA (Master IA - S1) — Pr. Hasna ELALAOUI
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Orientation Post-Bac — Maroc",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS minimaliste
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-size: 1.6rem !important; font-weight: 600; }
    h3 { font-size: 1.1rem !important; font-weight: 600; margin-bottom: 0.2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; }
    .card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        background: #fafafa;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-right: 6px;
    }
    .badge-sur    { background: #e8f5e9; color: #2e7d32; }
    .badge-real   { background: #e3f2fd; color: #1565c0; }
    .badge-ambi   { background: #fff3e0; color: #e65100; }
    .meta-row     { color: #555; font-size: 0.85rem; margin-top: 0.3rem; }
    .score-label  { font-size: 2rem; font-weight: 700; color: #333; }
    .score-sub    { font-size: 0.75rem; color: #888; }
    hr.thin       { border: none; border-top: 1px solid #eee; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Utilitaires ────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.resolve()
EXPERT_PL_PATH = str(BASE_DIR / "expert_system.pl")

def find_swipl() -> str:
    candidate = shutil.which("swipl")
    if candidate:
        return candidate
    for p in [
        r"C:\Program Files\swipl\bin\swipl.exe",
        r"C:\Program Files (x86)\swipl\bin\swipl.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\swipl\bin\swipl.exe"),
    ]:
        if Path(p).exists():
            return p
    return "swipl"

SWIPL = find_swipl()

@st.cache_data(show_spinner=False)
def recommander(bac, moyenne, notes_t, interets_t, villes_t, budget, statut, top_n):
    notes_pl    = "[" + ", ".join(f"[{m}, {float(n):.1f}]" for m, n in notes_t) + "]"
    interets_pl = "[" + ", ".join(interets_t) + "]"
    villes_pl   = "[" + ", ".join(villes_t) + "]"
    query = (
        f"recommander_json({bac}, {moyenne:.2f}, {notes_pl}, {interets_pl}, "
        f"{villes_pl}, {budget}, {statut}, {top_n}), halt."
    )
    try:
        proc = subprocess.run(
            [SWIPL, "-q", "-s", EXPERT_PL_PATH, "-g", query],
            cwd=str(BASE_DIR), capture_output=True,
            text=True, encoding="utf-8", timeout=10
        )
        raw = proc.stdout.strip()
        s, e = raw.find("["), raw.rfind("]")
        if s != -1 and e >= s:
            return json.loads(raw[s:e+1])
        return []
    except FileNotFoundError:
        st.error(
            "SWI-Prolog est introuvable. "
            "Installez-le depuis [swi-prolog.org](https://www.swi-prolog.org/download/stable) "
            "et ajoutez-le au PATH."
        )
        return []
    except Exception as e:
        st.error(f"Erreur moteur Prolog : {e}")
        return []

def badge_html(cat):
    cls  = {"Sûr": "badge-sur", "Réaliste": "badge-real", "Ambitieux": "badge-ambi"}.get(cat, "badge-real")
    return f'<span class="badge {cls}">{cat}</span>'

def export_md(resultats, bac_nom, moyenne, interets, villes, budget, statut):
    lines = [
        "# Fiche d'orientation post-bac",
        f"**Bac :** {bac_nom}  |  **Moyenne :** {moyenne:.2f}/20  |  "
        f"**Budget :** {budget:,} DH  |  **Statut :** {statut}",
        f"**Villes :** {', '.join(villes) or 'toutes'}  |  "
        f"**Intérêts :** {', '.join(interets) or '—'}",
        "",
    ]
    for r in resultats:
        lines.append(f"## {r['rang']}. {r['nom']} — {r['categorie']} ({r['score']}/100)")
        lines.append(
            f"- Ville : {r['ville'].capitalize()}  |  Durée : {r['duree']} ans  |  "
            f"Statut : {r['statut'].capitalize()}  |  Frais : {r['frais']:,} DH/an"
        )
        if r.get("points_forts"):
            lines.append(f"- Points forts : {', '.join(r['points_forts'])}")
        if r.get("alertes"):
            lines.append(f"- À surveiller : {', '.join(r['alertes'])}")
        lines.append(f"- Repli conseillé : {r.get('repli', '—')}")
        lines.append("")
    return "\n".join(lines)


# ── Sidebar ────────────────────────────────────────────────────────────────────

BACS = {
    "sm":           "Sciences Mathématiques (SM)",
    "spc":          "Physique-Chimie (SPC)",
    "svt":          "Sciences de la Vie et de la Terre (SVT)",
    "eco":          "Sciences Économiques",
    "tgc":          "Techniques de Gestion et Comptabilité",
    "ste":          "Sciences et Technologies Électriques",
    "stm":          "Sciences et Technologies Mécaniques",
    "lettres":      "Lettres",
    "humaines":     "Sciences Humaines",
    "arts_appliques": "Arts Appliqués",
}

with st.sidebar:
    st.markdown("### Votre profil")
    st.caption("Les résultats se mettent à jour automatiquement.")

    bac = st.selectbox("Série du bac", list(BACS.keys()),
                       format_func=lambda k: BACS[k], key="bac_input")

    moyenne = st.slider("Moyenne générale (/20)", 10.0, 20.0, 15.5, 0.1, key="moy")

    st.markdown("**Notes par matière**")
    col1, col2 = st.columns(2)
    notes = {}

    if bac in ("sm", "spc", "svt"):
        with col1:
            notes["maths"]      = st.number_input("Maths",     0.0, 20.0, 16.0, 0.5, key="n_maths")
            notes["physique"]   = st.number_input("Physique",  0.0, 20.0, 15.0, 0.5, key="n_phys")
            notes["svt"]        = st.number_input("SVT",       0.0, 20.0, 14.0, 0.5, key="n_svt")
        with col2:
            notes["francais"]   = st.number_input("Français",  0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes["anglais"]    = st.number_input("Anglais",   0.0, 20.0, 15.0, 0.5, key="n_ang")
            notes["philosophie"]= st.number_input("Philo",     0.0, 20.0, 13.0, 0.5, key="n_philo")

    elif bac in ("ste", "stm"):
        with col1:
            notes["maths"]      = st.number_input("Maths",         0.0, 20.0, 15.0, 0.5, key="n_maths")
            notes["physique"]   = st.number_input("Physique",      0.0, 20.0, 14.0, 0.5, key="n_phys")
            notes["technologie"]= st.number_input("Sc. Ingénieur", 0.0, 20.0, 16.0, 0.5, key="n_tech")
        with col2:
            notes["francais"]   = st.number_input("Français",  0.0, 20.0, 13.0, 0.5, key="n_fr")
            notes["anglais"]    = st.number_input("Anglais",   0.0, 20.0, 14.0, 0.5, key="n_ang")
            notes["philosophie"]= st.number_input("Philo",     0.0, 20.0, 12.0, 0.5, key="n_philo")

    elif bac in ("eco", "tgc"):
        with col1:
            notes["economie"]     = st.number_input("Économie",     0.0, 20.0, 15.5, 0.5, key="n_eco")
            notes["comptabilite"] = st.number_input("Comptabilité", 0.0, 20.0, 15.0, 0.5, key="n_compta")
            notes["maths"]        = st.number_input("Maths",        0.0, 20.0, 13.5, 0.5, key="n_maths")
        with col2:
            notes["francais"]     = st.number_input("Français",     0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes["anglais"]      = st.number_input("Anglais",      0.0, 20.0, 14.5, 0.5, key="n_ang")
            notes["philosophie"]  = st.number_input("Philo",        0.0, 20.0, 13.0, 0.5, key="n_philo")

    elif bac in ("lettres", "humaines"):
        with col1:
            notes["francais"]   = st.number_input("Français",    0.0, 20.0, 14.0, 0.5, key="n_fr")
            notes["arabe"]      = st.number_input("Arabe",       0.0, 20.0, 15.0, 0.5, key="n_arabe")
            notes["litterature"]= st.number_input("Littérature", 0.0, 20.0, 14.5, 0.5, key="n_litt")
        with col2:
            notes["histoire"]    = st.number_input("Histoire-Géo", 0.0, 20.0, 13.5, 0.5, key="n_hist")
            notes["philosophie"] = st.number_input("Philo",        0.0, 20.0, 14.0, 0.5, key="n_philo")
            notes["anglais"]     = st.number_input("Anglais",      0.0, 20.0, 15.0, 0.5, key="n_ang")

    else:  # arts_appliques
        with col1:
            notes["dessin"]     = st.number_input("Dessin & Arts", 0.0, 20.0, 16.0, 0.5, key="n_dessin")
            notes["creativite"] = st.number_input("Créativité",    0.0, 20.0, 16.0, 0.5, key="n_crea")
            notes["francais"]   = st.number_input("Français",      0.0, 20.0, 14.0, 0.5, key="n_fr")
        with col2:
            notes["philosophie"]= st.number_input("Philo",  0.0, 20.0, 13.0, 0.5, key="n_philo")
            notes["anglais"]    = st.number_input("Anglais",0.0, 20.0, 14.0, 0.5, key="n_ang")
            notes["maths"]      = st.number_input("Maths",  0.0, 20.0, 12.0, 0.5, key="n_maths")

    st.markdown("**Centres d'intérêt**")
    defaults = {
        ("sm","spc","svt"):       ["genie_logiciel", "intelligence_artificielle"],
        ("ste","stm"):            ["electronique", "mecanique"],
        ("eco","tgc"):            ["finance", "marketing"],
        ("lettres","humaines"):   ["droit_affaires", "communication"],
    }
    def_int = next((v for k, v in defaults.items() if bac in k), ["design", "architecture"])

    tous_interets = [
        "genie_logiciel", "intelligence_artificielle", "cybersecurite", "reseaux",
        "data_science", "genie_civil", "genie_industriel", "mecanique", "electronique", "telecom",
        "medecine_generale", "chirurgie", "dentaire", "soins_infirmiers", "biologie",
        "finance", "audit", "marketing", "commerce_international", "gestion_entreprise",
        "comptabilite", "banque", "droit_affaires", "justice", "diplomatie",
        "journalisme", "communication", "traduction", "relations_internationales",
        "enseignement_francais", "enseignement_anglais", "architecture", "urbanisme",
        "design", "arts_graphiques",
    ]
    interets = st.multiselect("", tous_interets, default=def_int,
                              key=f"int_{bac}", label_visibility="collapsed")

    st.markdown("**Villes acceptées**")
    villes_dispo = [
        "casablanca","rabat","marrakech","fes","tanger","agadir","oujda",
        "kenitra","settat","meknes","el_jadida","tetouan","benguerir","ifrane",
        "safi","sale","berrechid","khouribga","al_hoceima","dakhla",
    ]
    villes = st.multiselect("", villes_dispo, default=["casablanca","rabat"],
                            key="villes", label_visibility="collapsed")

    st.markdown("**Budget & statut**")
    c1, c2 = st.columns(2)
    with c1:
        budget = st.number_input("Budget max (DH)", 0, 150000, 0, 5000, key="budget",
                                 help="0 DH = public uniquement")
    with c2:
        statut = st.selectbox("Statut", ["public","prive","indifferent"],
                              format_func=lambda s: {"public":"Public","prive":"Privé",
                                                     "indifferent":"Indifférent"}[s],
                              key="statut")

    top_n = st.slider("Nombre de résultats", 3, 10, 5, key="top_n")

    if st.button("Recalculer", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Calcul ─────────────────────────────────────────────────────────────────────

notes_t   = tuple((m, float(notes[m])) for m in notes)
interets_t = tuple(interets)
villes_t   = tuple(villes)

resultats = recommander(bac, moyenne, notes_t, interets_t, villes_t, budget, statut, top_n)


# ── En-tête ────────────────────────────────────────────────────────────────────

st.markdown("## Orientation post-bac au Maroc")
st.caption(
    f"Bac **{BACS[bac]}** · moyenne **{moyenne:.2f}/20** · "
    f"budget **{budget:,} DH** · statut **{statut}**"
)
st.markdown('<hr class="thin">', unsafe_allow_html=True)


# ── Onglets ────────────────────────────────────────────────────────────────────

tab_res, tab_comment, tab_data = st.tabs(
    ["Recommandations", "Comment ça marche ?", "Toutes les formations"]
)


# ── Tab 1 : Recommandations ────────────────────────────────────────────────────

with tab_res:
    if not resultats:
        st.warning(
            "Aucune formation ne correspond à ces critères. "
            "Essayez d'élargir les villes, le budget, ou de baisser légèrement le filtre de statut."
        )
    else:
        col_titre, col_dl = st.columns([4, 1])
        with col_titre:
            st.markdown(f"**{len(resultats)} formation(s) recommandée(s)**")
        with col_dl:
            st.download_button(
                "Télécharger la fiche",
                data=export_md(resultats, BACS[bac], moyenne, interets, villes, budget, statut),
                file_name="orientation.md",
                mime="text/markdown",
                use_container_width=True,
            )

        for item in resultats:
            cat  = item.get("categorie", "Réaliste")
            diff = item.get("diff", 0.0)

            with st.container():
                left, right = st.columns([5, 1])

                with left:
                    st.markdown(
                        f"### {item['rang']}. {item['nom']} "
                        f"{badge_html(cat)}",
                        unsafe_allow_html=True,
                    )
                    frais_txt = "gratuit" if item["frais"] == 0 else f"{item['frais']:,} DH/an"
                    st.markdown(
                        f'<div class="meta-row">'
                        f"{item['ville'].capitalize()} · "
                        f"{item['duree']} ans · "
                        f"{item['statut'].capitalize()} · "
                        f"{frais_txt}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with right:
                    st.markdown(
                        f'<div style="text-align:center">'
                        f'<div class="score-label">{item["score"]}</div>'
                        f'<div class="score-sub">/ 100</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with st.expander("Détails", expanded=(item["rang"] <= 2)):
                    c1, c2 = st.columns(2)

                    with c1:
                        st.markdown("**Pourquoi cette formation ?**")
                        # Accès
                        if item["mode_selection"] == "ouvert":
                            st.write("Accès ouvert — aucun seuil éliminatoire.")
                        elif diff >= 0:
                            st.write(f"Moyenne au-dessus du seuil de {item['seuil']}/20 (+{diff:.2f} pt).")
                        else:
                            st.write(f"Moyenne légèrement en dessous du seuil ({diff:+.2f} pt).")
                        # Intérêts communs
                        if item.get("interets_communs"):
                            st.write("Débouchés en phase : " + ", ".join(item["interets_communs"]) + ".")
                        # Points forts
                        if item.get("points_forts"):
                            st.write("Bonnes notes en : " + ", ".join(item["points_forts"]) + " (≥ 14/20).")

                    with c2:
                        st.markdown("**Points de vigilance**")
                        if item.get("alertes"):
                            st.warning("Note faible en : " + ", ".join(item["alertes"]) + " (< 12/20).")
                        else:
                            st.write("Aucune matière clé en difficulté.")

                        if item["mode_selection"] == "concours":
                            st.write("Concours d'entrée éliminatoire.")

                        if villes and item["ville"] not in villes:
                            st.write(f"Hors de vos villes prioritaires ({item['ville'].capitalize()}).")

                        if item.get("repli"):
                            st.caption(f"Repli conseillé : {item['repli']}")

                st.markdown('<hr class="thin">', unsafe_allow_html=True)


# ── Tab 2 : Comment ça marche ──────────────────────────────────────────────────

with tab_comment:
    st.markdown("""
Le moteur d'inférence est écrit en **Prolog pur** (SWI-Prolog). Il raisonne en quatre étapes :

1. **Éligibilité** — Seules les formations compatibles avec votre bac, votre budget et votre
   préférence public/privé sont retenues. Les filières très sélectives sont écartées si votre
   moyenne est inférieure de plus de 1,5 point au seuil indicatif.

2. **Score d'adéquation (sur 100)** — Quatre critères sont pondérés :
   - Correspondance entre vos centres d'intérêt et les débouchés de la filière (35 pts)
   - Marge par rapport au seuil et niveau dans les matières clés (40 pts)
   - Localisation dans vos villes préférées (15 pts)
   - Conformité avec votre préférence public / privé (10 pts)

3. **Catégorisation** —
   - **Sûr** : accès ouvert ou marge confortable (> 2,5 pts).
   - **Réaliste** : profil solide au-dessus du seuil.
   - **Ambitieux** : filière sélective à concours, ou seuil très proche de votre moyenne.

4. **Explication** — Pour chaque résultat, le système identifie vos points forts,
   signale les matières à risque et propose une alternative de repli.
""")


# ── Tab 3 : Toutes les formations ──────────────────────────────────────────────

with tab_data:
    csv_file = BASE_DIR / "formations.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Formations", len(df))
        c2.metric("Villes", df["City"].nunique())
        c3.metric("Publiques", (df["Status"].str.lower() == "public").sum())
        c4.metric("Privées",   (df["Status"].str.lower() == "prive").sum())

        f1, f2 = st.columns(2)
        with f1:
            vf = st.multiselect("Ville", sorted(df["City"].unique()), key="f_ville")
        with f2:
            tf = st.multiselect("Type",  sorted(df["Type"].unique()),  key="f_type")

        df_view = df.copy()
        if vf: df_view = df_view[df_view["City"].isin(vf)]
        if tf: df_view = df_view[df_view["Type"].isin(tf)]

        st.dataframe(df_view, use_container_width=True, height=440)
        st.caption(f"{len(df_view)} formation(s) affichée(s) sur {len(df)}.")
    else:
        st.error("Fichier formations.csv introuvable.")
