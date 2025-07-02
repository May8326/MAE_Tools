import requests
import json
import os

# Définir le dossier de sortie pour les fichiers JSON
OUTPUT_DIR = './data/output'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)  # Crée le dossier s'il n'existe pas

search_term = input("Entrez le terme de recherche pour les entités Wikidata: ").strip()
if not search_term:
    print("Aucun terme de recherche fourni. Veuillez réessayer.")
    exit(1)
else:
    print(f"Recherche des entités Wikidata pour le terme: {search_term}")

def fetch_all_entities(search_term, limit=200):
    """
    Recherche les entités Wikidata correspondant à un terme donné,
    puis enregistre les résultats simplifiés dans un fichier JSON.
    """
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "opensearch",
        "format": "json",
        "search": search_term,
        "namespace": "0",
        "limit": limit,
        "formatversion": "2"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        data = response.json()

        if not data or len(data) < 3:
            print("Aucune entité trouvée pour ce terme.")
            return

        entities = []
        for item in data[1]:  # Les résultats sont dans le deuxième élément de la liste
            entities.append({
                "label": item,
                "url": f"https://www.wikidata.org/wiki/{item.replace(' ', '_')}"
            })

        # Enregistrer les résultats dans un fichier JSON
        output_file = os.path.join(OUTPUT_DIR, f"{search_term.replace(' ', '_')}_entities.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=4)

        print(f"Résultats enregistrés dans {output_file}")

    except requests.RequestException as e:
        print(f"Erreur lors de la requête à l'API Wikidata: {e}")

# Exécuter la fonction de recherche
fetch_all_entities(search_term) 

