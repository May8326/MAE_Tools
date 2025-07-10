# -*- coding: utf-8 -*-
"""
Lecture d'un thésaurus CSV, conversion en SKOS (RDFLib), visualisation arbre et graphe.
Données d'entrée : fichier CSV fourni.
Sortie : fichier SKOS (Turtle) + visualisations (matplotlib/graphviz).
"""

import csv
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import SKOS, RDF
import networkx as nx
import matplotlib.pyplot as plt

# Constantes pour les namespaces
EX = Namespace("http://example.org/mae/")
THESAURUS = Namespace("http://example.org/mae/thesaurus/")

# Fichier d'entrée
DATA_DIR = "data"
CSV_FILE = f"{DATA_DIR}/20250710_BIB.csv"  # à adapter au nom du fichier réel
SKOS_FILE = "thesaurus.ttl"

def clean_label(label):
    """Nettoie un label (strip, supprime parenthèses inutiles)."""
    if label is None:
        return ""
    return label.strip()

def make_uri(prefix, id):
    """Construit une URI à partir d'un préfixe et d'un identifiant."""
    return URIRef(f"{prefix}{id}")

def read_thesaurus_csv(csv_file):
    """
    Lit un fichier CSV de thésaurus au format point-virgule, gère l'encodage Windows,
    et retourne une liste de concepts.
    """
    print("Lecture du CSV...")
    concepts = []
    # Essaye d'abord l'encodage cp1252 (Windows), puis utf-8-sig en secours
    for encoding in ('cp1252', 'utf-8-sig'):
        try:
            with open(csv_file, newline='', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=';')
                for i, row in enumerate(reader):
                    # Nettoie chaque valeur si c'est une chaîne, sinon laisse vide
                    clean_row = {k: (v.strip() if isinstance(v, str) else "") for k, v in row.items()}
                    concepts.append(clean_row)
                    if i % 1000 == 0 and i > 0:
                        print(f"  {i} lignes lues...")
            print(f"  {len(concepts)} concepts lus au total.")
            break
        except UnicodeDecodeError:
            concepts = []
            continue
    if not concepts:
        raise UnicodeDecodeError("Impossible de lire le fichier avec cp1252 ni utf-8-sig.")
    print("Lecture du CSV terminée.")
    return concepts

def build_skos_graph(concepts):
    """
    Construit un graphe SKOS à partir des concepts.
    Chaque ligne représente une relation générique : TermeGen (générique) > TermeSpe (spécifique).
    TermeSpe peut avoir des TA (termes associés), des notes, des EP (équivalents).
    """
    print("Construction du graphe SKOS...")
    g = Graph()
    g.bind("skos", SKOS)
    g.bind("ex", EX)
    g.bind("th", THESAURUS)

    # index rapide par ID pour retrouver les concepts
    id_to_uri = {}

    n_gen, n_spe, n_ta = 0, 0, 0

    # 1ère passe : créer tous les concepts et leurs labels
    for i, c in enumerate(concepts):
        # Concept générique
        gen_id = c["ID_TG"]
        gen_label = clean_label(c["TermeGen"])
        if gen_id and gen_label:
            gen_uri = make_uri(THESAURUS, gen_id)
            id_to_uri[gen_id] = gen_uri
            g.add((gen_uri, RDF.type, SKOS.Concept))
            g.add((gen_uri, SKOS.prefLabel, Literal(gen_label, lang="fr")))
            n_gen += 1

        # Concept spécifique
        spe_id = c["ID_TS"]
        spe_label = clean_label(c["TermeSpe"])
        if spe_id and spe_label:
            spe_uri = make_uri(THESAURUS, spe_id)
            id_to_uri[spe_id] = spe_uri
            g.add((spe_uri, RDF.type, SKOS.Concept))
            g.add((spe_uri, SKOS.prefLabel, Literal(spe_label, lang="fr")))
            # Relation générique/spécifique
            if gen_id and gen_label:
                g.add((spe_uri, SKOS.broader, gen_uri))
                g.add((gen_uri, SKOS.narrower, spe_uri))
            n_spe += 1

            # Notes
            note = c.get("Note", "")
            if note:
                g.add((spe_uri, SKOS.note, Literal(note, lang="fr")))

            # EP (équivalents)
            ep = c.get("EP", "")
            if ep:
                for alt in ep.split("|"):
                    alt = alt.strip()
                    if alt:
                        g.add((spe_uri, SKOS.altLabel, Literal(alt, lang="fr")))

            # TA (termes associés)
            ta = c.get("TA", "")
            id_ta = c.get("ID_TA", "")
            if ta and id_ta:
                ta_labels = [x.strip() for x in ta.split("|")]
                ta_ids = [x.strip() for x in id_ta.split("|")]
                for tlabel, tid in zip(ta_labels, ta_ids):
                    if tid:
                        ta_uri = make_uri(THESAURUS, tid)
                        # Créez la ressource si elle n'existe pas déjà
                        if (ta_uri, RDF.type, SKOS.Concept) not in g:
                            g.add((ta_uri, RDF.type, SKOS.Concept))
                            g.add((ta_uri, SKOS.prefLabel, Literal(tlabel, lang="fr")))
                        g.add((spe_uri, SKOS.related, ta_uri))
                        g.add((ta_uri, SKOS.related, spe_uri))
                        n_ta += 1
        if i % 1000 == 0 and i > 0:
            print(f"  {i} concepts traités dans SKOS...")

    print(f"Graphe SKOS construit ({n_gen} génériques, {n_spe} spécifiques, {n_ta} relations associées).")
    return g, id_to_uri

def export_skos(g, filename):
    """Exporte le graphe SKOS au format Turtle."""
    print(f"Export du graphe SKOS au format Turtle dans {filename} ...")
    g.serialize(destination=filename, format="turtle")
    print("Export SKOS terminé.")

def build_networkx_graph(concepts, id_to_uri):
    """
    Construit un graphe orienté pour visualisation (générique > spécifique, associé, etc).
    Les noeuds sont les labels, les arêtes sont typées.
    """
    print("Construction du graphe de visualisation avec networkx...")
    G = nx.DiGraph()
    id_to_label = {}

    # 1ère passe : index labels
    for c in concepts:
        if c["ID_TG"]:
            id_to_label[c["ID_TG"]] = c["TermeGen"]
        if c["ID_TS"]:
            id_to_label[c["ID_TS"]] = c["TermeSpe"]

    # 2ème passe : arêtes
    for c in concepts:
        gen_id = c["ID_TG"]
        spe_id = c["ID_TS"]
        if gen_id and spe_id:
            G.add_edge(id_to_label[gen_id], id_to_label[spe_id], relation="broader")
        # TA
        ta = c.get("TA", "")
        id_ta = c.get("ID_TA", "")
        if ta and id_ta and spe_id:
            ta_labels = [x.strip() for x in ta.split("|")]
            ta_ids = [x.strip() for x in id_ta.split("|")]
            for tlabel, tid in zip(ta_labels, ta_ids):
                if tid and tid in id_to_label:
                    G.add_edge(id_to_label[spe_id], id_to_label[tid], relation="related")
    print(f"Graphe networkx construit avec {G.number_of_nodes()} noeuds et {G.number_of_edges()} arêtes.")
    return G

def plot_tree(G):
    """
    Affiche un arbre générique > spécifique à partir du graphe.
    (On ne montre que les relations broader pour la structure arborescente)
    """
    print("Affichage de l'arbre hiérarchique (générique > spécifique)...")
    # Extraire les relations "broader" (inversées pour faire de la racine vers feuilles)
    T = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        if d["relation"] == "broader":
            T.add_edge(u, v)
    # Trouver les racines (noeuds sans prédécesseur)
    roots = [n for n in T.nodes if T.in_degree(n) == 0]
    print(f"  Nombre de racines de l'arbre : {len(roots)}")
    plt.figure(figsize=(13, 6))
    pos = nx.shell_layout(T)
    nx.draw(T, pos, with_labels=True, arrows=True, node_color='lightblue', node_size=1600, font_size=9)
    plt.title("Hiérarchie générique/spécifique (arbre)")
    plt.show()
    print("Arbre affiché.")

def plot_graph(G):
    """
    Affiche le graphe complet (relations broader et related).
    """
    print("Affichage du graphe global (génériques et associés)...")
    plt.figure(figsize=(15, 8))
    pos = nx.spring_layout(G, seed=42, k=0.25)
    edge_colors = []
    for u, v, d in G.edges(data=True):
        if d["relation"] == "broader":
            edge_colors.append("blue")
        else:
            edge_colors.append("orange")
    nx.draw(G, pos, with_labels=True, arrows=True, node_color='lightgreen',
            edge_color=edge_colors, node_size=1600, font_size=9)
    plt.title("Thésaurus : relations génériques et associées")
    plt.show()
    print("Graphe global affiché.")

if __name__ == "__main__":
    print("=== DEBUT DU TRAITEMENT ===")
    # 1. Lecture des données
    concepts = read_thesaurus_csv(CSV_FILE)
    # 2. Conversion SKOS
    skos_graph, id_to_uri = build_skos_graph(concepts)
    export_skos(skos_graph, SKOS_FILE)
    print(f"Graphe SKOS exporté vers {SKOS_FILE}")
    # 3. Visualisation
    G = build_networkx_graph(concepts, id_to_uri)
    plot_tree(G)
    plot_graph(G)
    print("=== FIN DU TRAITEMENT ===")