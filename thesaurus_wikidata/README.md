# Outil de récupération des données relatives à l'aéronautique sur Wikidata

## Données attendues

- ID Wikidata
- Termes (fr,en)
- Termes parents
- Définition (fr, sinon en)

En format JSON, CSV, SKOS

## Type de données relatives à l'aéronautique

- Industrie et économie :
    - Constructeurs
    - Modèles d'avions
    - Métiers de l'aéronautique et vocabulaire métier
    - Equipement 
    - Matériaux utilisés en aéronautique (?)
- Histoire :
    - Evénements de l'histoire de l'aviation
    - Personnalités liées à l'aviation
- Science :
    - Concepts liés à l'aéronautique
- Evénements :
    - Salons, congrès, ...

## Méthode

```mermaid
flowchart TD
    %% Nodes
        
        Start(["fa:fa-code Python Notebook"])
        B{"fa:fa-search Requête des id relatifs<br>à l'aéronautique ou à<br>un concept lié"}
        C["fa:fa-database Base de donnée json"]
        E{"fa:fa-search Requête SPARQL<br>boucle sur les id"}
        E1("labels français")
        E2("définitions")
        E3("parents")
        F["fa:fa-database Base de donnée enrichie"]
        G{"⚒️ Vérification des données<br>sur OpenRefine"}
        End(["fa:fa-arrow-down Enregistrement des données<br>en csv exploitable"])

    %% Edge connections between nodes
        Start --> B
        B --> C
        C --> E
        E --> E1
        E --> E2
        E --> E3
        E1 --> F
        E2 --> F
        E3 --> F
        F --> G
        G --> End  
        
         %% Color palette
        classDef main color:#fff, fill:#1565c0, stroke:#1565c0, font-weight:bold
        classDef data color:#fff, fill:#263238, stroke:#263238
        classDef process color:#fff, fill:#00897b, stroke:#00897b
        classDef endNode color:#fff, fill:#37474f, stroke:#37474f

        class Start,End endNode;
        class B,E,G process;
        class C,F data;
        class E1,E2,E3 main;
```
