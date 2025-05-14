# Fabio: A Knowledge Graph for Mental Health Diagnosis

## Overview

Fabio is a tool designed to construct and utilize a knowledge graph for mental health diagnosis, leveraging the ICD-11 ontology. It processes data from various sources, including:

-   `codes.csv`: Contains ICD-11 codes, titles, definitions, and diagnostic criteria.
-   `symptom.csv`: Lists symptoms associated with various conditions.
-   `diagnosisCriteria.csv`: Provides detailed diagnostic criteria for specific disorders.
-   `prescription.csv`: Includes prescription texts linked to ICD-11 codes.
-   `icd_11_ontology.ttl` and `icd_11_kg.ttl`:  RDF Turtle files containing the ICD-11 ontology and a knowledge graph of mental health concepts.

The system uses Python scripts to load, clean, and integrate this data into a MongoDB database and to generate a knowledge graph.

## Key Components

-   `load_csv.py`:  Script to efficiently load CSV data into MongoDB.
-   `database.py`:  Defines the MongoDB class for database interactions.
-   `kg.py`:  Handles the creation of the knowledge graph, including ontology management.
-   `save_kg.py`: Saves the generated knowledge graph.
-   `main.py`:  The main execution script.

## Setup

1.  Ensure you have MongoDB installed and running.
2.  Install the required Python libraries: `pymongo`, `rdflib`, `networkx`, `matplotlib`, `tqdm`, and `requests`.
3.  Place all the provided files in a single directory.
4.  Run `main.py` to execute the data loading and knowledge graph generation process.

## Data Files

-   `codes.csv`:  Defines the core ICD-11 codes and their attributes.
-   `symptom.csv`:  Lists symptoms.
-   `diagnosisCriteria.csv`: Details diagnostic criteria.
-   `prescription.csv`:  Prescription information.
-   `icd_11_ontology.ttl`:  ICD-11 ontology in Turtle format.
-   `icd_11_kg.ttl`:  Knowledge graph in Turtle format.

## Scripts

-   `load_csv.py`:  Loads CSV data into MongoDB.
-   `database.py`:  Manages MongoDB connections.
-   `kg.py`:  Creates and manipulates the knowledge graph.
-   `save_kg.py`:  Saves the knowledge graph.
-   `main.py`:  The main execution script.

## Important Notes

-   The scripts assume a running MongoDB instance on the default port.
-   The `codes.csv` file is crucial for mapping and linking various data elements.
-   The knowledge graph is generated based on the relationships defined in the data files and the ICD-11 ontology.