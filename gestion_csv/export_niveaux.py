import csv

# Fichier source et résultat
CSV_FILE = "20250710_BIB.csv"
OUT_FILE = "arbo_niveaux.csv"

# Lecture du CSV et construction des relations
id_to_label = {}
child_to_parent = {}

with open(CSV_FILE, encoding="cp1252", newline='') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if row["ID_TG"]:
            id_to_label[row["ID_TG"]] = row["TermeGen"]
        if row["ID_TS"]:
            id_to_label[row["ID_TS"]] = row["TermeSpe"]
        if row["ID_TS"] and row["ID_TG"]:
            child_to_parent[row["ID_TS"]] = row["ID_TG"]

# Fonction pour construire le chemin des niveaux (de la racine à la feuille)
def get_niveaux(concept_id):
    chemin = []
    while concept_id in id_to_label:
        chemin.insert(0, id_to_label[concept_id])
        if concept_id in child_to_parent:
            concept_id = child_to_parent[concept_id]
        else:
            break
    return chemin

# Récupération de tous les concepts spécifiques
chemins = []
with open(CSV_FILE, encoding="cp1252", newline='') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        if row["ID_TS"]:
            niveaux = get_niveaux(row["ID_TS"])
            chemins.append(niveaux)

# Calcul du nombre maximal de niveaux pour l'en-tête
max_niveaux = max(len(chemin) for chemin in chemins)

# Écriture du nouveau CSV
with open(OUT_FILE, "w", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    writer.writerow([f"niveau {i+1}" for i in range(max_niveaux)])
    for chemin in chemins:
        row = [""] * (max_niveaux - len(chemin)) + chemin
        writer.writerow(row)

print(f"Export terminé : {OUT_FILE}")