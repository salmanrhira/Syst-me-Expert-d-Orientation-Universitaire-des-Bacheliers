% ==============================================================================
% MOTEUR D'INFÉRENCE : SYSTÈME EXPERT D'ORIENTATION POST-BAC MAROC (expert_system.pl)
% Module : Fondements Avancés de l'IA (Master IA - S1) - Pr. Hasna ELALAOUI
% ==============================================================================

:- use_module(library(lists)).
:- use_module(library(json)).
:- [knowledge_base].

% --- 1. Base Dynamique du Profil Utilisateur ---
% profil(Bac, Moyenne, NotesMatieres, Interets, VillesPref, BudgetMax, StatutPref).
% NotesMatieres : liste de paires [Matiere, Note] (ex: [[maths, 16], [physique, 14]])
:- dynamic profil/7.
:- dynamic profil_courant/7.

% Enregistrer ou réinitialiser le profil
definir_profil(Bac, Moyenne, NotesMatieres, Interets, VillesPref, BudgetMax, StatutPref) :-
    retractall(profil_courant(_, _, _, _, _, _, _)),
    assertz(profil_courant(Bac, Moyenne, NotesMatieres, Interets, VillesPref, BudgetMax, StatutPref)).

effacer_profil :-
    retractall(profil_courant(_, _, _, _, _, _, _)).

% --- 2. Règles d'Éligibilité Stricte ---
% Structure de formation/12 dans knowledge_base.pl :
% formation(Id, Nom, Type, Ville, BacsAcceptes, Seuil, MatieresCles,
%           ModeSelection, DureeAnnees, Debouches, Statut, FraisAnnuels).

% Vérification Bac et Budget (compatibilité descendante)
est_eligible(Id, BacEleve, BudgetEleve) :-
    formation(Id, _, _, _, BacsAcceptes, _, _, _, _, _, _, Frais),
    (member(BacEleve, BacsAcceptes) -> true ; member(toutes, BacsAcceptes)),
    BudgetEleve >= Frais.

% Vérification complète du profil
est_eligible_profil(Id, BacEleve, MoyenneEleve, BudgetEleve, StatutPref) :-
    formation(Id, _, _, _, BacsAcceptes, Seuil, _, ModeSelection, _, _, Statut, Frais),
    % 1. Bac accepté (déterministe : évite les doublons si 'toutes' figure aussi)
    (member(BacEleve, BacsAcceptes) -> true ; member(toutes, BacsAcceptes)),
    % 2. Budget suffisant
    BudgetEleve >= Frais,
    % 3. Statut juridique accepté (public, prive ou indifférent)
    (StatutPref == indifferent ; StatutPref == tout ; Statut == StatutPref),
    % 4. Seuil minimal de présélection : pour les filières sélectives,
    % une moyenne inférieure de plus de 1.5 point au seuil est éliminatoire
    (ModeSelection == ouvert -> true ; MoyenneEleve >= (Seuil - 1.5)).

% --- 3. Analyse des Matières Clés et Risques ---
% Matière clé considérée comme fragile / à risque si note < 12/20
matiere_faible(Id, NotesEleve, Matiere, Note) :-
    formation(Id, _, _, _, _, _, MatieresCles, _, _, _, _, _),
    member(Matiere, MatieresCles),
    member([Matiere, Note], NotesEleve),
    Note < 12.

% Matière clé considérée comme point fort si note >= 14/20
matiere_forte(Id, NotesEleve, Matiere, Note) :-
    formation(Id, _, _, _, _, _, MatieresCles, _, _, _, _, _),
    member(Matiere, MatieresCles),
    member([Matiere, Note], NotesEleve),
    Note >= 14.

% Calcul de la note moyenne de l'élève sur les matières clés de la formation
moyenne_matieres_cles(Id, NotesEleve, MoyenneCles) :-
    formation(Id, _, _, _, _, _, MatieresCles, _, _, _, _, _),
    findall(N, (member(M, MatieresCles), member([M, N], NotesEleve)), NotesTrouvees),
    (NotesTrouvees \= [] ->
        sum_list(NotesTrouvees, Somme),
        length(NotesTrouvees, Nb),
        MoyenneCles is Somme / Nb
    ;
        MoyenneCles is 12.0
    ).

% --- 4. Calcul du Score d'Adéquation Multi-Critères ---
% Le score d'adéquation (sur 100) combine :
% - Affinité débouchés / intérêts (max 35 pts)
% - Adéquation académique & seuil (max 40 pts)
% - Préférence géographique (max 15 pts)
% - Adéquation statut et frais (max 10 pts)

calculer_score_complet(Id, _BacEleve, MoyenneEleve, NotesEleve, InteretsEleve, VillesPref, StatutPref, ScoreFinal) :-
    formation(Id, _, _, Ville, _, Seuil, _, ModeSelection, _, Debouches, Statut, _),
    
    % A. Affinité des centres d'intérêt avec les débouchés (0 à 35 pts)
    intersection(InteretsEleve, Debouches, Communs),
    length(Communs, NbInterets),
    ScoreInterets is min(35.0, NbInterets * 12.0),
    
    % B. Adéquation Académique (0 à 40 pts)
    Diff is MoyenneEleve - Seuil,
    (ModeSelection == ouvert ->
        ScoreSeuil is 25.0
    ; Diff >= 2.0 ->
        ScoreSeuil is 25.0
    ; Diff >= 0.5 ->
        ScoreSeuil is 20.0
    ; Diff >= 0.0 ->
        ScoreSeuil is 15.0
    ; Diff >= -0.5 ->
        ScoreSeuil is 8.0
    ;
        ScoreSeuil is 0.0
    ),
    % Bonus/malus matières clés (max 15 pts)
    moyenne_matieres_cles(Id, NotesEleve, MoyCles),
    BonusCles is min(15.0, max(-10.0, (MoyCles - 12.0) * 3.75)),
    ScoreAcademique is max(0.0, min(40.0, ScoreSeuil + BonusCles)),

    % C. Adéquation Géographique (0 à 15 pts)
    (VillesPref = [] ->
        ScoreVille is 10.0
    ; VillesPref = [VillePrincipale|_], Ville == VillePrincipale ->
        ScoreVille is 15.0
    ; member(Ville, VillesPref) ->
        ScoreVille is 8.0
    ;
        ScoreVille is 3.0
    ),

    % D. Adéquation Statut (0 à 10 pts)
    ((StatutPref == indifferent ; StatutPref == tout ; Statut == StatutPref) ->
        ScoreStatut is 10.0
    ;
        ScoreStatut is 0.0
    ),

    % Score total normalisé sur 100
    ScoreBrut is ScoreInterets + ScoreAcademique + ScoreVille + ScoreStatut,
    ScoreFinal is max(0.0, min(100.0, ScoreBrut)).

% Prédicat simplifié compatible avec les tests précédents
calculer_adequation(Id, MoyenneEleve, InteretsEleve, Score) :-
    formation(Id, _, _, _, _, Seuil, _, ModeSelection, _, Debouches, _, _),
    intersection(InteretsEleve, Debouches, Communs),
    length(Communs, NbInterets),
    Diff is MoyenneEleve - Seuil,
    % Correction : la sélectivité de la formation valorise le choix si l'élève est admissible
    (ModeSelection == ouvert ->
        BonusNiveau is 4.0
    ;
        BonusNiveau is Seuil * 0.5
    ),
    (Diff >= 0.0 ->
        BonusMarge is min(3.0, Diff)
    ;
        BonusMarge is Diff * 2.0
    ),
    Score is BonusNiveau + BonusMarge + (NbInterets * 4.0).

% --- 5. Classification des Recommandations ---
% Les catégories sont mutuellement exclusives : 'Sûr', 'Réaliste', 'Ambitieux'

classer_formation(Id, MoyenneEleve, Categorie) :-
    formation(Id, _, Type, _, _, Seuil, _, ModeSelection, _, _, _, _),
    evaluer_categorie(ModeSelection, Type, MoyenneEleve, Seuil, Categorie).

% 1. Choix SÛR :
% - Toutes les filières à accès ouvert (FSJES, FLSH, FS ouvertes)
% - OU filières professionnalisantes courtes (OFPPT, BTS, EST) avec moyenne >= seuil + 0.5
% - OU filières sélectives hors concours ultra-sélectif avec une moyenne très supérieure (Diff >= 2.5)
evaluer_categorie(ouvert, _, _, _, 'Sûr') :- !.

evaluer_categorie(ModeSelection, Type, MoyenneEleve, Seuil, 'Sûr') :-
    ModeSelection \== concours,
    member(Type, [formation_professionnelle, technique, education]),
    MoyenneEleve >= (Seuil + 0.5), !.

evaluer_categorie(ModeSelection, Type, MoyenneEleve, Seuil, 'Sûr') :-
    ModeSelection \== concours,
    \+ member(Type, [prepa, medecine, dentaire, architecture, militaire]),
    Diff is MoyenneEleve - Seuil,
    Diff >= 2.5, !.

% 2. Choix AMBITIEUX :
% - Filières ultra-sélectives (CPGE, Médecine, Dentaire, Architecture ENA) ou filières sur concours
% - OU moyenne très proche du seuil indicatif (entre Seuil - 0.5 et Seuil + 0.8)
evaluer_categorie(ModeSelection, Type, MoyenneEleve, Seuil, 'Ambitieux') :-
    (ModeSelection == concours ; member(Type, [prepa, medecine, dentaire, architecture, militaire, polytechnique])),
    MoyenneEleve >= (Seuil - 0.5),
    ModeSelection \== ouvert, !.

evaluer_categorie(_, _, MoyenneEleve, Seuil, 'Ambitieux') :-
    Diff is MoyenneEleve - Seuil,
    Diff >= -0.5,
    Diff < 0.8, !.

% 3. Choix RÉALISTE :
% - Moyenne confortable par rapport au seuil (Diff >= 0.8) sans être classé d'office en sûr
evaluer_categorie(_, _, MoyenneEleve, Seuil, 'Réaliste') :-
    Diff is MoyenneEleve - Seuil,
    Diff >= 0.8, !.

% 4. Cas où la moyenne est insuffisante
evaluer_categorie(_, _, MoyenneEleve, Seuil, 'Hors portée') :-
    Diff is MoyenneEleve - Seuil,
    Diff < -0.5.

% --- 6. Alternatives de Repli Pédagogiques ---
% Si échec ou difficulté d'admission dans une formation de rêve, proposer une filière de repli sûre
suggerer_repli(Type, Alternative) :-
    (member(Type, [medecine, dentaire]) ->
        Alternative = 'ISPITS Paramédical ou Faculté des Sciences (Filière SVI Biologie)'
    ; member(Type, [ecole_ingenieur, prepa, polytechnique, telecom, aeronautique]) ->
        Alternative = 'Faculté des Sciences et Techniques (FST MIPC/GEGM) ou EST Génie Informatique/Électrique'
    ; member(Type, [commerce, economie]) ->
        Alternative = 'EST Gestion / Techniques de Management ou FSJES Économie-Gestion'
    ; member(Type, [architecture, design, arts_plastiques]) ->
        Alternative = 'ENSAD Casablanca, BTS Bâtiment ou Génie Civil en FST'
    ; member(Type, [journalisme, lettres_sciences_humaines]) ->
        Alternative = 'Faculté des Lettres et Sciences Humaines (FLSH - Études Françaises ou Anglaises)'
    ; member(Type, [droit]) ->
        Alternative = 'Faculté des Sciences Juridiques, Économiques et Sociales (FSJES Droit)'
    ;
        Alternative = 'Filière spécialisée OFPPT / ISTA ou Faculté des Sciences / Lettres'
    ).

% --- 7. Moteur d'Explication Détaillé ---
% Justifie la recommandation avec les points forts, risques, villes et alternatives
expliquer_detail(Id, BacEleve, MoyenneEleve, NotesEleve, InteretsEleve, VillesPref) :-
    formation(Id, Nom, Type, Ville, _, Seuil, _, ModeSelection, Duree, Debouches, Statut, Frais),
    classer_formation(Id, MoyenneEleve, Cat),
    format('======================================================================~n'),
    format('  RECOMMANDATION : ~w [Statut: ~w | ~w ans | Frais: ~w DH]~n', [Nom, Statut, Duree, Frais]),
    format('  Profil de sélection : Catégorie [~w] | Mode d\'admission : ~w~n', [Cat, ModeSelection]),
    format('======================================================================~n'),
    % 1. Bac
    format('  [+] Baccalauréat : Votre série (~w) est parfaitement éligible.~n', [BacEleve]),
    % 2. Moyenne et seuil
    Diff is MoyenneEleve - Seuil,
    (ModeSelection == ouvert ->
        format('  [+] Admission : Accès ouvert sans seuil éliminatoire (Seuil indicatif : ~1f/20).~n', [Seuil])
    ; Diff >= 0.0 ->
        format('  [+] Moyenne générale : ~2f/20 dépasse le seuil indicatif (~1f/20) de +~2f pts.~n', [MoyenneEleve, Seuil, Diff])
    ;
        format('  [!] Attention seuil : Moyenne (~2f/20) légèrement inférieure au seuil indicatif (~1f/20, écart: ~2f pts).~n', [MoyenneEleve, Seuil, Diff])
    ),
    % 3. Centres d'intérêt
    intersection(InteretsEleve, Debouches, InteretsCommuns),
    (InteretsCommuns \= [] ->
        format('  [+] Débouchés & Passion : En phase avec vos centres d\'intérêt : ~w.~n', [InteretsCommuns])
    ;
        format('  [*] Débouchés : Filière offrant des perspectives en : ~w.~n', [Debouches])
    ),
    % 4. Points forts dans les matières clés
    findall(M-N, matiere_forte(Id, NotesEleve, M, N), Fortes),
    (Fortes \= [] ->
        format('  [+] Points forts : Excellentes notes dans les matières clés : ~w.~n', [Fortes])
    ; true),
    % 5. Alertes sur les matières clés faibles (< 12)
    findall(M-N, matiere_faible(Id, NotesEleve, M, N), Faibles),
    (Faibles \= [] ->
        format('  [!] Alerte risque : Notes fragiles dans des matières clés de la filière : ~w.~n', [Faibles])
    ; true),
    % 6. Ville
    (VillesPref \= [] ->
        (VillesPref = [Ville1|_], Ville == Ville1 ->
            format('  [+] Ville : Située dans votre ville prioritaire (~w).~n', [Ville])
        ; member(Ville, VillesPref) ->
            format('  [+] Ville : Située dans l\'une de vos villes acceptées (~w).~n', [Ville])
        ;
            format('  [!] Mobilité : Établissement situé à ~w (en dehors de vos villes prioritaires).~n', [Ville])
        )
    ;
        format('  [*] Localisation : ~w.~n', [Ville])
    ),
    % 7. Concours / Sélectivité
    (ModeSelection == concours ->
        format('  [!] Épreuve : Présélection + Concours écrit/oral éliminatoire.~n', [])
    ; true),
    % 8. Alternative de repli
    suggerer_repli(Type, Repli),
    format('  [->] Option de repli conseillée en cas d\'imprévu : ~w.~n~n', [Repli]).

% Compatibilité avec l'ancien prédicat expliquer/4
expliquer(Id, BacEleve, MoyenneEleve, NotesEleve) :-
    expliquer_detail(Id, BacEleve, MoyenneEleve, NotesEleve, [], []).

% --- 8. Prédicat de Recommandation TOP N ---
% Calcule et classe toutes les formations admissibles pour le profil courant ou donné

obtenir_recommandations(Bac, Moyenne, Notes, Interets, Villes, Budget, Statut, TopN, Resultats) :-
    findall(
        score_formation(Score, Id, Nom, Categorie),
        (
            formation(Id, Nom, _, _, _, _, _, _, _, _, _, _),
            est_eligible_profil(Id, Bac, Moyenne, Budget, Statut),
            classer_formation(Id, Moyenne, Categorie),
            Categorie \== 'Hors portée',
            calculer_score_complet(Id, Bac, Moyenne, Notes, Interets, Villes, Statut, Score)
        ),
        ListeScores
    ),
    % Trier par score décroissant
    sort(1, @>=, ListeScores, ScoresTries),
    % Extraire les TopN
    prendre_premiers(TopN, ScoresTries, Resultats).

prendre_premiers(0, _, []) :- !.
prendre_premiers(_, [], []) :- !.
prendre_premiers(N, [H|T], [H|Reste]) :-
    N > 0,
    N1 is N - 1,
    prendre_premiers(N1, T, Reste).

% Afficher le Top N avec explications complètes
recommander_profil(Bac, Moyenne, Notes, Interets, Villes, Budget, Statut, TopN) :-
    format('~n==============================================================================~n'),
    format('   SYSTÈME EXPERT D\'ORIENTATION POST-BAC : TOP ~w RECOMMANDATIONS~n', [TopN]),
    format('==============================================================================~n'),
    obtenir_recommandations(Bac, Moyenne, Notes, Interets, Villes, Budget, Statut, TopN, Recommandations),
    (Recommandations == [] ->
        format('Aucune formation ne correspond exactement à vos critères. Essayez d\'élargir votre budget ou vos villes.~n')
    ;
        afficher_liste_recommandations(Recommandations, 1, Bac, Moyenne, Notes, Interets, Villes)
    ).

afficher_liste_recommandations([], _, _, _, _, _, _).
afficher_liste_recommandations([score_formation(Score, Id, _Nom, Cat)|Reste], Rang, Bac, Moyenne, Notes, Interets, Villes) :-
    format('~n>>> RANG #~w | Score d\'adéquation : ~1f/100 | Catégorie : [~w] <<<~n', [Rang, Score, Cat]),
    expliquer_detail(Id, Bac, Moyenne, Notes, Interets, Villes),
    RangSuivant is Rang + 1,
    afficher_liste_recommandations(Reste, RangSuivant, Bac, Moyenne, Notes, Interets, Villes).

% Recommandation basée sur le profil dynamique enregistré
recommander(TopN) :-
    profil_courant(Bac, Moyenne, Notes, Interets, Villes, Budget, Statut), !,
    recommander_profil(Bac, Moyenne, Notes, Interets, Villes, Budget, Statut, TopN).
recommander(_) :-
    format('Erreur : Aucun profil utilisateur n\'a été défini. Utilisez definir_profil/7 ou lancer_conseiller.~n').

% --- 9. Mode Interactif Console (Questionnaire Dynamique) ---
lancer_conseiller :-
    format('~n==============================================================================~n'),
    format(' BIENVENUE DANS LE SYSTEME EXPERT D\'ORIENTATION UNIVERSITAIRE (POST-BAC MAROC)~n'),
    format(' Module : Fondements Avancés de l\'IA | Master IA - S1~n'),
    format('==============================================================================~n~n'),
    
    % Saisie du type de bac
    format('Quel est votre type de baccalauréat ?~n'),
    format('(sm, spc, svt, eco, tgc, ste, stm, lettres, humaines, arts_appliques)~n> '),
    read(Bac),
    
    % Saisie de la moyenne
    format('~nQuelle est votre moyenne générale estimée ou obtenue au Bac (ex: 15.5) ?~n> '),
    read(Moyenne),
    
    % Saisie des notes clés
    format('~nSaisissez vos notes par matière clé sous forme de liste :~n'),
    format('Exemple : [[maths, 16], [physique, 14], [francais, 13], [anglais, 15]]~n> '),
    read(NotesMatieres),
    
    % Saisie des centres d\'intérêt
    format('~nQuels sont vos centres d\'intérêt professionnels ?~n'),
    format('Exemple : [genie_logiciel, cybersecurite, intelligence_artificielle, finance]~n> '),
    read(Interets),
    
    % Saisie des villes préférées
    format('~nQuelles sont vos villes préférées par ordre de préférence ?~n'),
    format('Exemple : [casablanca, rabat, marrakech] ou [] si indifférent~n> '),
    read(Villes),
    
    % Saisie du budget
    format('~nQuel est votre budget annuel maximal en Dirhams (ex: 0 pour public seul, 50000) ?~n> '),
    read(Budget),
    
    % Saisie de la préférence statut
    format('~nPréférence d\'établissement (public, prive, ou indifferent) ?~n> '),
    read(Statut),
    
    % Enregistrement et génération des recommandations
    definir_profil(Bac, Moyenne, NotesMatieres, Interets, Villes, Budget, Statut),
    recommander(5).

% --- 10. Export JSON pour Intégration IHM / Web ---
recommander_json(Bac, Moyenne, NotesMatieres, Interets, Villes, Budget, Statut, TopN) :-
    obtenir_recommandations(Bac, Moyenne, NotesMatieres, Interets, Villes, Budget, Statut, TopN, Recs),
    findall(
        _{
            rang: Rang,
            id: Id,
            nom: Nom,
            score: ScoreArrondi,
            categorie: Cat,
            ville: Ville,
            type: Type,
            duree: Duree,
            statut: StatutEtab,
            frais: Frais,
            seuil: Seuil,
            diff: Diff,
            mode_selection: Mode,
            interets_communs: InteretsCommuns,
            points_forts: PointsFortsNoms,
            alertes: AlertesNoms,
            repli: Repli
        },
        (
            nth1(Rang, Recs, score_formation(Score, Id, Nom, Cat)),
            formation(Id, Nom, Type, Ville, _, Seuil, _, Mode, Duree, Debouches, StatutEtab, Frais),
            intersection(Interets, Debouches, InteretsCommuns),
            findall(M, (matiere_forte(Id, NotesMatieres, M, _)), PointsFortsNoms),
            findall(M, (matiere_faible(Id, NotesMatieres, M, _)), AlertesNoms),
            Diff is Moyenne - Seuil,
            suggerer_repli(Type, Repli),
            ScoreArrondi is round(Score * 10) / 10
        ),
        Dicts
    ),
    json_write_dict(current_output, Dicts).
