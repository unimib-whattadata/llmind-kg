from rdflib import Graph, URIRef, Literal
from neo4j import GraphDatabase
import os

def import_turtle_to_neo4j(turtle_file_path, neo4j_uri, neo4j_user, neo4j_password):
    """
    Imports a Turtle file into a Neo4j graph database.

    Args:
        turtle_file_path (str): The path to the Turtle file.
        neo4j_uri (str): The URI of the Neo4j database (e.g., "bolt://localhost:7687").
        neo4j_user (str): The Neo4j username.
        neo4j_password (str): The Neo4j password.
    """
    try:
        # 1. Load the Turtle file using rdflib
        g = Graph()
        g.parse(turtle_file_path, format="turtle")
        print(f"Successfully parsed Turtle file: {turtle_file_path}")

        # 2. Connect to Neo4j
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        def _create_nodes_and_relationships(tx, graph):
            """
            Internal function to create nodes and relationships in Neo4j within a transaction.

            Args:
                tx: The Neo4j transaction object.
                graph (rdflib.Graph): The parsed RDF graph.
            """
            node_count = 0
            relationship_count = 0
            literal_nodes_count = 0  # Keep track of literal nodes.

            for s, p, o in graph:
                subject_uri = str(s)
                predicate_uri = str(p)

                # 3. Handle different object types (URIRef and Literal)
                if isinstance(o, URIRef):
                    object_uri = str(o)
                    # Create or merge nodes for subject and object
                    tx.run("MERGE (s:Resource {uri: $subject_uri})", subject_uri=subject_uri)
                    tx.run("MERGE (o:Resource {uri: $object_uri})", object_uri=object_uri)
                    # Create the relationship
                    tx.run(
                        "MATCH (s:Resource {uri: $subject_uri}), (o:Resource {uri: $object_uri})"
                        " MERGE (s)-[r:`" + predicate_uri + "`]->(o)",
                        subject_uri=subject_uri,
                        object_uri=object_uri,
                    )
                    relationship_count += 1
                elif isinstance(o, Literal):
                    literal_value = str(o)
                    #  Create subject node if it does not exist.
                    tx.run("MERGE (s:Resource {uri: $subject_uri})", subject_uri=subject_uri)
                    # Create a node for the literal and connect to it.  This is good because
                    #  it allows you to query the literals, and avoids massive property bloat
                    #  on the non-literal nodes.
                    tx.run("MERGE (l:Literal {value: $literal_value})", literal_value=literal_value)
                    tx.run(
                        "MATCH (s:Resource {uri: $subject_uri}), (l:Literal {value: $literal_value})"
                        " MERGE (s)-[r:`" + predicate_uri + "`]->(l)",
                        subject_uri=subject_uri,
                        literal_value=literal_value
                    )
                    relationship_count += 1
                    literal_nodes_count += 1

                node_count += 1 #  Count subjects, and objects that are URIs

            return node_count, relationship_count, literal_nodes_count # Return counts

        # 4. Execute the import within a transaction
        with driver.session() as session:
            nodes_created, relationships_created, literals_created = session.execute_write(_create_nodes_and_relationships, g)
            print(f"Created {nodes_created} nodes (excluding literals), {relationships_created} relationships, and {literals_created} literal nodes.")

        # 5. Close the driver
        driver.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        return False  # Indicate failure
    return True #Indicate Success

if __name__ == "__main__":
    # Get user inputs.  Important to get these at runtime.
    turtle_file_path = "icd_11_ontology.ttl"#input("Enter the path to the Turtle file: ")
    neo4j_uri = "bolt://localhost:7687"#input("Enter the Neo4j URI (e.g., bolt://localhost:7687): ")
    neo4j_user = "neo4j"#input("Enter the Neo4j username: ")
    neo4j_password = "12345678"#input("Enter the Neo4j password: ")

    # Basic file existence check
    if not os.path.exists(turtle_file_path):
        print(f"Error: Turtle file not found at {turtle_file_path}")
    else:
        # Call the import function
        if import_turtle_to_neo4j(turtle_file_path, neo4j_uri, neo4j_user, neo4j_password):
            print("Turtle data successfully imported into Neo4j.")
        else:
            print("Import failed.")
