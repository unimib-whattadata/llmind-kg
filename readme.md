# LLMind: Psychiatric Diagnosis Assistant

## Overview

This repository provides a system to assist with psychiatric diagnosis, leveraging large language models and knowledge graphs. The system uses a Docker Compose setup for easy deployment, automating the database population.

## Key Features

* **Automated Database Population:** The database is automatically populated during the Docker Compose setup, eliminating manual data entry.
* **LLM Integration:** The system integrates with large language models (LLMs) to provide diagnostic suggestions based on case descriptions.
* **Knowledge Graph:** A knowledge graph of medical concepts (specifically ICD-11) is utilized to enhance the accuracy and relevance of the LLM's output.
* **API:** A Flask API is included to provide a convenient interface for querying the LLM and retrieving relevant information.

## Docker Compose Setup

The core functionality of this project is designed to be run using Docker Compose. This simplifies the setup process and ensures that all necessary components (database, application, etc.) work together seamlessly.

### Prerequisites

* Docker
* Docker Compose

### Installation and Usage

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Ensure that docker compose is up:**
    ```bash
    docker compose up
    ```
    * This command will build and start the services defined in the `docker-compose.yml` file. This includes setting up the database and populating it with the necessary data.
3.  **Access the API:**
    * Once the services are running, you can access the API at `http://localhost:<port>`, where `<port>` is the port specified in your `docker-compose.yml` (e.g., 5000).

## Code Description (Key Files)

* `src/3. DBdsmsplit.py`:  Splits and processes input text files containing clinical case data, preparing it for database insertion.
* `src/4. DBlangchainbuilder.py`:  Builds and persists Chroma vector stores using Ollama embeddings for efficient retrieval of information by the LLM.
* `src/6. KGFileHandler.py`:  Handles processing and insertion of data from a knowledge graph CSV file into the database.
* `src/7. ICDGraph.py`:  Retrieves ICD-11 code data, processes it, and inserts it into the database.  Also includes functionality to generate a knowledge graph representation (TTL).
* `src/api.py`:  Defines the Flask API endpoints for interacting with the LLM and retrieving information.
* `src/app.py`:  The main application script that orchestrates the data processing and LLM interaction.
* `src/db_config.py`:  Contains database connection configuration and logic to create the database if it doesn't exist.
* `src/LangchainRDFBuilder.py`:  Builds Chroma vector stores from RDF (TTL) data.

## Important Notes

* **Database Credentials:** Ensure that the database connection details in `src/db_config.py` are correctly configured for your environment.  It is highly recommended to use environment variables to store sensitive information like passwords.
* **Model Selection:** The LLM model used can be configured within the code (e.g., in `src/app.py` and `src/api.py`).  Ensure that the specified model is available in your Ollama setup.
* **Data Sources:** The system relies on external data sources (e.g., text files, CSV files, APIs) for clinical case data and knowledge graph information.  Make sure these sources are accessible and properly formatted.

## Disclaimer

This system is intended to be used as a supportive tool for trained medical professionals. It should not be used as a substitute for professional medical judgment. The diagnostic suggestions provided by the system are for informational purposes only.