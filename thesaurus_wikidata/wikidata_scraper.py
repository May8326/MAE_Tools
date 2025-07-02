import requests
import time
import json
import csv
from urllib.parse import quote

LANGUAGE = "en"  # Langue par défaut pour la recherche
LIMIT = 50  # Nombre de résultats par page
OFFSET = 0  # Offset pour la pagination

search_terme = input("Entrez le terme de recherche (par exemple, 'aero'): ")
search_term = quote(search_terme)  # Encoder le terme de recherche pour l'URL
if not search_term:
    print("❌ Le terme de recherche ne peut pas être vide.")
    exit(1)

class WikidataAeroScraper:
    def __init__(self):
        self.endpoint = "https://query.wikidata.org/sparql"
        self.headers = {
            'User-Agent': 'WikidataAeroBot/1.0 (https://github.com/May8326/wikidata-scraper)',
            'Accept': 'application/sparql-results+json'
        }
        self.results = []

    def build_query(self, search_term, language, limit, offset):
        """Construit la requête SPARQL avec l'offset donné"""
        query = f"""
        SELECT ?item ?itemLabel WHERE {{
          SERVICE wikibase:mwapi {{
            bd:serviceParam wikibase:endpoint "www.wikidata.org";
                            wikibase:api "EntitySearch";
                            mwapi:search "{search_term}";
                            mwapi:language "{language}";
                            mwapi:limit "{limit}";
                            mwapi:continue "{offset}".
            ?item wikibase:apiOutputItem mwapi:item.
          }}
          
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en". 
          }}
        }}
        """
        return query
    
    def execute_query(self, query):
        """Exécute une requête SPARQL et retourne les résultats"""
        try:
            response = requests.get(
                self.endpoint,
                params={'query': query, 'format': 'json'},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête: {e}")
            return None
    
    def extract_results(self, data):
        """Extrait les résultats du JSON retourné"""
        if not data or 'results' not in data:
            return []
        
        results = []
        for binding in data['results']['bindings']:
            item_uri = binding.get('item', {}).get('value', '')
            item_label = binding.get('itemLabel', {}).get('value', '')
            
            # Extraire l'ID Wikidata de l'URI
            item_id = item_uri.split('/')[-1] if item_uri else ''
            
            results.append({
                'wikidata_id': item_id,
                'label': item_label,
                'uri': item_uri
            })
        
        return results
    
    def scrape_all_results(self):
        """Scrape tous les résultats en paginant automatiquement"""
        offset = 0
        page = 1
        total_results = 0
        
        print("🚀 Début du scraping des entités contenant 'aero'...")
        print("=" * 60)
        
        while True:
            print(f"📄 Page {page} (offset: {offset})...")
            
            # Construire et exécuter la requête
            query = self.build_query(search_term, LANGUAGE, LIMIT, offset)
            data = self.execute_query(query)
            
            if not data:
                print("❌ Erreur lors de l'exécution de la requête")
                break
            
            # Extraire les résultats
            page_results = self.extract_results(data)
            
            if not page_results:
                print(f"✅ Fin des résultats atteinte (page {page})")
                break
            
            # Ajouter aux résultats totaux
            self.results.extend(page_results)
            total_results += len(page_results)
            
            print(f"   → {len(page_results)} résultats trouvés")
            print(f"   → Total cumulé: {total_results}")
            
            # Vérifier si on a moins de 50 résultats (dernière page)
            if len(page_results) < 50:
                print(f"✅ Dernière page atteinte ({len(page_results)} < 50 résultats)")
                break
            
            # Préparer la page suivante
            offset += 50
            page += 1
            
            # Pause pour être respectueux envers l'API
            time.sleep(1)
        
        print("=" * 60)
        print(f"🎉 Scraping terminé! Total: {total_results} résultats")
        return self.results
    
    def save_to_csv(self, filename="wikidata_aero_results.csv"):
        """Sauvegarde les résultats en CSV"""
        if not self.results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['wikidata_id', 'label', 'uri']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        print(f"💾 Résultats sauvegardés dans: {filename}")
    
    def save_to_json(self, filename="wikidata_aero_results.json"):
        """Sauvegarde les résultats en JSON"""
        if not self.results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.results, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"💾 Résultats sauvegardés dans: {filename}")
    
    def print_sample_results(self, limit=10):
        """Affiche un échantillon des résultats"""
        if not self.results:
            print("❌ Aucun résultat à afficher")
            return
        
        print(f"\n📋 Échantillon des résultats (premiers {limit}):")
        print("-" * 80)
        
        for i, result in enumerate(self.results[:limit]):
            print(f"{i+1:2d}. {result['wikidata_id']:12s} | {result['label']}")
        
        if len(self.results) > limit:
            print(f"... et {len(self.results) - limit} autres résultats")

def main():
    """Fonction principale"""
    scraper = WikidataAeroScraper()
    
    try:
        # Scraper tous les résultats
        results = scraper.scrape_all_results()
        
        if results:
            # Afficher un échantillon
            scraper.print_sample_results()
            
            # Sauvegarder
            scraper.save_to_csv()
            scraper.save_to_json()
            
            print(f"\n🎯 Mission accomplie! {len(results)} entités 'aero' récupérées.")
        else:
            print("❌ Aucun résultat trouvé")
            
    except KeyboardInterrupt:
        print("\n⛔ Arrêt demandé par l'utilisateur")
        if scraper.results:
            print(f"💾 Sauvegarde des {len(scraper.results)} résultats partiels...")
            scraper.save_to_csv("wikidata_aero_partial.csv")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()