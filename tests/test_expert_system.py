"""
Tests automatisés pour le Système Expert d'Orientation Post-Bac au Maroc.
Valide l'intégrité de la base de données, la génération de la base Prolog,
et le bon fonctionnement du moteur d'inférence.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
CSV_PATH = BASE_DIR / "formations.csv"
KB_PL_PATH = BASE_DIR / "knowledge_base.pl"
EXPERT_PL_PATH = BASE_DIR / "expert_system.pl"

def find_swipl():
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

SWIPL_PATH = find_swipl()


class TestDataIntegrity:
    """Vérification de la base de données source (formations.csv)"""

    def test_csv_exists_and_not_empty(self):
        assert CSV_PATH.exists(), "Le fichier formations.csv est introuvable."
        df = pd.read_csv(CSV_PATH)
        assert len(df) >= 100, f"Attendu au moins 100 formations, trouvé : {len(df)}"

    def test_required_columns_present(self):
        required_cols = [
            "ID", "Name", "Type", "City", "AcceptedBacs", "Threshold",
            "KeySubjects", "SelectionMode", "Duration", "Debouches", "Status", "AnnualFees"
        ]
        df = pd.read_csv(CSV_PATH)
        for col in required_cols:
            assert col in df.columns, f"Colonne manquante : {col}"

    def test_no_null_values(self):
        df = pd.read_csv(CSV_PATH)
        null_counts = df.isnull().sum()
        assert null_counts.sum() == 0, f"Valeurs nulles détectées :\n{null_counts[null_counts > 0]}"

    def test_thresholds_valid_range(self):
        df = pd.read_csv(CSV_PATH)
        assert (df["Threshold"] >= 10.0).all(), "Certains seuils sont inférieurs à 10.0"
        assert (df["Threshold"] <= 20.0).all(), "Certains seuils sont supérieurs à 20.0"

    def test_durations_valid(self):
        df = pd.read_csv(CSV_PATH)
        assert (df["Duration"] >= 2).all(), "Durée minimale attendue >= 2 ans"
        assert (df["Duration"] <= 7).all(), "Durée maximale attendue <= 7 ans"

    def test_statuses_valid(self):
        df = pd.read_csv(CSV_PATH)
        valid_statuses = {"public", "prive"}
        unique_statuses = set(df["Status"].str.strip().str.lower().unique())
        assert unique_statuses.issubset(valid_statuses), f"Statuts invalides : {unique_statuses - valid_statuses}"


class TestKnowledgeBaseGeneration:
    """Validation du script de build de la base de faits Prolog"""

    def test_build_kb_execution(self):
        from build_kb import generate_knowledge_base
        generate_knowledge_base()
        assert KB_PL_PATH.exists(), "knowledge_base.pl n'a pas été généré."
        
        with open(KB_PL_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Vérifie qu'il y a 100 faits formation/12
        occurrences = content.count("formation(")
        assert occurrences >= 100, f"Moins de 100 faits formation/12 trouvés ({occurrences})"


class TestPrologInferenceEngine:
    """Validation du moteur d'inférence SWI-Prolog"""

    @pytest.fixture(autouse=True)
    def check_swipl(self):
        result = shutil.which(SWIPL_PATH)
        if not result and not Path(SWIPL_PATH).exists():
            pytest.skip("SWI-Prolog n'est pas installé ou accessible dans le PATH.")

    def test_prolog_syntax(self):
        """Vérifie que expert_system.pl se charge sans erreur de syntaxe."""
        cmd = [SWIPL_PATH, "-q", "-s", str(EXPERT_PL_PATH), "-g", "halt."]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, f"Erreur de syntaxe Prolog :\n{proc.stderr}"

    def test_recommander_json_structure(self):
        """Vérifie que la requête JSON renvoie des données bien formées avec toutes les clés."""
        query = (
            "recommander_json(sm, 16.5, [[maths, 17], [physique, 16]], "
            "[genie_logiciel, intelligence_artificielle], [casablanca, rabat], 0, public, 3), halt."
        )
        cmd = [SWIPL_PATH, "-q", "-s", str(EXPERT_PL_PATH), "-g", query]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0, f"Erreur d'exécution Prolog : {proc.stderr}"

        output = proc.stdout.strip()
        start = output.find("[")
        end = output.rfind("]")
        assert start != -1 and end != -1, f"Pas de JSON valide dans la sortie :\n{output}"

        data = json.loads(output[start:end+1])
        assert len(data) > 0, "Aucune recommandation renvoyée pour un profil SM 16.5"
        
        expected_keys = {
            "rang", "id", "nom", "score", "categorie", "ville", "type",
            "duree", "statut", "frais", "seuil", "diff", "mode_selection",
            "interets_communs", "points_forts", "alertes", "repli"
        }
        for item in data:
            assert expected_keys.issubset(item.keys()), f"Clés manquantes dans l'élément : {expected_keys - item.keys()}"
            assert item["categorie"] in ["Sûr", "Réaliste", "Ambitieux"]
            assert 0 <= item["score"] <= 100

    def test_budget_zero_only_returns_public(self):
        """Vérifie qu'un budget de 0 DH n'inclut aucune formation payante privée."""
        query = (
            "recommander_json(spc, 15.0, [[maths, 14], [physique, 15]], "
            "[genie_civil], [casablanca], 0, public, 5), halt."
        )
        cmd = [SWIPL_PATH, "-q", "-s", str(EXPERT_PL_PATH), "-g", query]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0

        output = proc.stdout.strip()
        start = output.find("[")
        end = output.rfind("]")
        data = json.loads(output[start:end+1])

        for item in data:
            assert item["statut"] == "public", f"Formation non publique avec budget 0 : {item['nom']}"
            assert item["frais"] == 0, f"Frais > 0 avec budget 0 : {item['frais']} pour {item['nom']}"

    def test_bac_lettres_filtering(self):
        """Vérifie qu'un élève de Bac Lettres n'a pas accès à des écoles d'ingénieurs exclusives aux séries scientifiques."""
        query = (
            "recommander_json(lettres, 14.5, [[francais, 16], [arabe, 15], [litterature, 15]], "
            "[droit_affaires, communication], [rabat, casablanca], 0, public, 5), halt."
        )
        cmd = [SWIPL_PATH, "-q", "-s", str(EXPERT_PL_PATH), "-g", query]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        assert proc.returncode == 0

        output = proc.stdout.strip()
        start = output.find("[")
        end = output.rfind("]")
        data = json.loads(output[start:end+1])

        for item in data:
            assert item["type"] not in ["ecole_ingenieur", "prepa", "medecine"], (
                f"Formation scientifique/médicale incompatible recommandée pour Bac Lettres : {item['nom']}"
            )
