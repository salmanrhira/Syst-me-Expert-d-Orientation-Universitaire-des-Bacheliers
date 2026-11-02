% ==============================================================================
% MOTEUR D'INFÉRENCE : SYSTÈME EXPERT D'ORIENTATION (expert_system.pl)
% ==============================================================================

:- [knowledge_base].

% --- 1. Saisie du Profil Utilisateur (Exemple de structure) ---
% On utilisera des faits dynamiques pour stocker le profil de l'étudiant
:- dynamic profil/7.
% profil(Bac, Moyenne, NotesMatieres, Interets, VillePref, BudgetMax, StatutPref).
% NotesMatieres est une liste de paires [matiere, note]

% --- 2. Règles d'Éligibilité ---
est_eligible(Id, BacEleve, BudgetEleve) :-
    formation(Id, _, _, _, BacsAcceptes, _, _, _, _, _, _, Frais),
    (member(BacEleve, BacsAcceptes) ; member(toutes, BacsAcceptes)),
    BudgetEleve >= Frais.

% --- 3. Analyse des Risques ---
% Un risque existe si une matière clé a une note < 12
matiere_faible(Id, NotesEleve, Matiere) :-
    formation(Id, _, _, _, _, _, MatieresCles, _, _, _, _, _),
    member(Matiere, MatieresCles),
    member([Matiere, Note], NotesEleve),
    Note < 12.

% --- 4. Calcul du Score d'Adéquation (Simplifié) ---
calculer_adequation(Id, MoyenneEleve, InteretsEleve, Score) :-
    formation(Id, _, _, _, _, Seuil, _, _, _, Debouches, _, _),
    % Score de base sur la moyenne
    Diff is MoyenneEleve - Seuil,
    % Bonus pour les centres d'intérêt (nombre de correspondances avec les débouchés)
    intersection(InteretsEleve, Debouches, Communs),
    length(Communs, NbInterets),
    Score is Diff + (NbInterets * 0.5).

% --- 5. Classification des Recommandations ---
% Ambitieux : Moyenne proche du seuil (-0.5 à +0.8) pour formations sélectives
classer_formation(Id, MoyenneEleve, 'Ambitieux') :-
    formation(Id, _, _, _, _, Seuil, _, Mode, _, _, _, _),
    Mode \== ouvert,
    Diff is MoyenneEleve - Seuil,
    Diff >= -0.5, Diff < 0.8.

% Réaliste : Moyenne confortable (0.8 à 2.0 au-dessus du seuil) pour formations sélectives
classer_formation(Id, MoyenneEleve, 'Réaliste') :-
    formation(Id, _, _, _, _, Seuil, _, Mode, _, _, _, _),
    Mode \== ouvert,
    Diff is MoyenneEleve - Seuil,
    Diff >= 0.8, Diff < 2.0.

% Sûr : Moyenne très supérieure (>= 2.0) ou accès ouvert
classer_formation(Id, MoyenneEleve, 'Sûr') :-
    formation(Id, _, _, _, _, Seuil, _, Mode, _, _, _, _),
    (Mode == ouvert ; (Diff is MoyenneEleve - Seuil, Diff >= 2.0)).

% --- 6. Moteur d'Explication ---
expliquer(Id, BacEleve, MoyenneEleve, NotesEleve) :-
    formation(Id, Nom, _, _, _, Seuil, _, _, _, _, _, _),
    format('--- Justification pour ~w ---~n', [Nom]),
    format('- Votre Bac (~w) est accepté.~n', [BacEleve]),
    (MoyenneEleve >= Seuil -> 
        format('- Votre moyenne (~2f) dépasse le seuil indicatif (~2f).~n', [MoyenneEleve, Seuil]) ;
        format('- Attention: Votre moyenne (~2f) est légèrement en dessous du seuil (~2f).~n', [MoyenneEleve, Seuil])),
    forall(matiere_faible(Id, NotesEleve, M), 
           format('- Alerte: Votre niveau en ~w est considéré comme un risque pour cette filière.~n', [M])).

% --- Utilitaire ---
intersection([], _, []).
intersection([H|T], L, [H|Res]) :- member(H, L), !, intersection(T, L, Res).
intersection([_|T], L, Res) :- intersection(T, L, Res).
