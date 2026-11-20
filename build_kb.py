"""
Script de conversion de formations.csv vers knowledge_base.pl
Génère les faits Prolog pour le système expert d'orientation universitaire.
"""
import csv
import re
from pathlib import Path

def sanitize_atom(val: str) -> str:
    val = val.strip().lower()
    val = re.sub(r'[^a-z0-9_]', '_', val)
    val = re.sub(r'_+', '_', val).strip('_')
    return val

def parse_list(val: str) -> list[str]:
    if not val or not val.strip():
        return []
    items = [sanitize_atom(item) for item in val.split(';') if item.strip()]
    return items

def format_prolog_list(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"

def escape_prolog_string(val: str) -> str:
    escaped = val.replace("'", "\\'")
    return f"'{escaped}'"

def generate_knowledge_base():
    base_dir = Path(__file__).parent.resolve()
    csv_path = base_dir / "formations.csv"
    pl_path = base_dir / "knowledge_base.pl"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {csv_path}")

    facts = []
    
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = int(row["ID"].strip())
            name = escape_prolog_string(row["Name"].strip())
            ftype = sanitize_atom(row["Type"])
            city = sanitize_atom(row["City"])
            bacs = format_prolog_list(parse_list(row["AcceptedBacs"]))
            threshold = float(row["Threshold"].strip())
            key_subjects = format_prolog_list(parse_list(row["KeySubjects"]))
            selection = sanitize_atom(row["SelectionMode"])
            duration = int(row["Duration"].strip())
            debouches = format_prolog_list(parse_list(row["Debouches"]))
            status = sanitize_atom(row["Status"])
            annual_fees = int(float(row["AnnualFees"].strip()))
            
            fact = (
                f"formation({fid}, {name}, {ftype}, {city}, {bacs}, "
                f"{threshold:.1f}, {key_subjects}, {selection}, {duration}, "
                f"{debouches}, {status}, {annual_fees})."
            )
            facts.append(fact)

    header = """% ==============================================================================
% BASE DE CONNAISSANCES : FORMATIONS POST-BAC AU MAROC (100 FORMATIONS)
% Module : Fondements Avancés de l'IA (Master IA - S1)
% Pr. Hasna ELALAOUI
% Fichier généré automatiquement depuis formations.csv par build_kb.py
% ==============================================================================
% Structure du prédicat:
% formation(Id, Nom, Type, Ville, BacsAcceptes, Seuil, MatieresCles,
%           ModeSelection, DureeAnnees, Debouches, Statut, FraisAnnuels).
% ==============================================================================

:- dynamic formation/12.

"""
    
    with open(pl_path, mode="w", encoding="utf-8") as f:
        f.write(header)
        for fact in facts:
            f.write(fact + "\n")
            
    print(f"Base de connaissances Prolog générée avec succès : {len(facts)} formations dans {pl_path}")

if __name__ == "__main__":
    generate_knowledge_base()
