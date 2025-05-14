# User Guide for Fabio

## Step-by-Step Walkthrough

This guide provides a step-by-step walkthrough of how to use the Fabio tool to generate a knowledge graph for mental health diagnosis.

### Prerequisites

Before you begin, ensure you have the following installed:

-   Python 3.6 or later
-   MongoDB
-   Python libraries: `pymongo`, `rdflib`, `networkx`, `matplotlib`, `tqdm`, and `requests`

### Step 1: Set Up the Environment

1.  **Install Python Libraries:**

    ```bash
    pip install pymongo rdflib networkx matplotlib tqdm requests
    ```

2.  **Start MongoDB:**

    -   Make sure your MongoDB server is running. If it's a local installation, it usually runs on the default port.

### Step 2: Organize Your Files

1.  Create a directory (e.g., `Fabio`).
2.  Place all the provided files (`codes.csv`, `symptom.csv`, `diagnosisCriteria.csv`, `prescription.csv`, `icd_11_ontology.ttl`, `icd_11_kg.ttl`, `load_csv.py`, `database.py`, `kg.py`, `save_kg.py`, and `main.py`) into this directory.

### Step 3: Load CSV Data into MongoDB

1.  Open a terminal and navigate to the `Fabio` directory.
2.  Run the `load_csv.py` script:

    ```bash
    python load_csv.py
    ```

    -   This script will read the CSV files and import the data into your MongoDB database.

### Step 4: Generate the Knowledge Graph

1.  Execute the `main.py` script:

    ```bash
    python main.py
    ```

    -   This script will use the data in the MongoDB database to create the knowledge graph (`icd_11_kg.ttl`).

### Step 5: Explore the Knowledge Graph (Optional)

1.  The generated knowledge graph (`icd_11_kg.ttl`) can be further explored using graph database tools like Neo4j or by visualizing it with tools that support Turtle format.

### Important Considerations

-   Ensure that your MongoDB server is running and accessible.
-   The CSV files must be in the correct format for the scripts to work properly.
-   Adjust the script parameters (e.g., database name, collection names) if necessary to match your environment.

By following these steps, you can use Fabio to create a knowledge graph for mental health diagnosis, enabling powerful data analysis and integration.