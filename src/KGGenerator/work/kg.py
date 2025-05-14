from database import MongoDB
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import urllib.parse
from tqdm import tqdm
import re
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, SKOS, OWL, XSD
from rdflib import URIRef
from rdflib.term import URIRef as RDFURIRef
from rdflib.exceptions import Error

INCLUSION_PROP = URIRef(
    "http://id.who.int/icd/schema/inclusion")
EXCLUSION_PROP = URIRef(
    "http://id.who.int/icd/schema/exclusion")
HAS_DIAGNOSTIC_REQUIREMENTS_PROP = URIRef(
    "http://icd_kg/6/ontology/hasDiagnosticRequirements")
SCHEMA = Namespace("https://schema.org/")
ICD_SCHEMA = Namespace("http://id.who.int/icd/schema/")
ICD_KG = Namespace("http://icd_kg/6/ontology/")
ICD_KG_ENTITY = Namespace("http://icd_kg/6/entity/")

mongo_symptom = MongoDB(db_name="llmind", collection_name="symptom")
mongo_diagnosis = MongoDB(db_name="llmind", collection_name="diagnosis")
mongo_prescription = MongoDB(db_name="llmind", collection_name="prescription")


class HierarchicalRepresentation:

    def __init__(self):
        self.mongo = MongoDB(db_name="llmind", collection_name="llmind_kg")
        self.ontology_uri_base = "http://icd_kg/6/ontology"
        self.entity_uri_base = "http://icd_kg/6/entity"

    def get_all_docs(self):
        return self.mongo.find_many({})

    def get_all_codes(self):
        mongo = MongoDB(db_name="llmind", collection_name="codes")
        return mongo.find_many({"code": {"$regex": "^6"}})

    def get_entity_name(self, uri):
        response = self.mongo.find_one({"@id": uri})
        if response is not None:
            return response["title"]["@value"]
        else:
            return None

    def clean_name(self, name: str) -> str:
        if name == "Mental, behavioural or neurodevelopmental disorders":
            return name.replace(",", "")
        if name == "behavioural syndromes associated with":
            name = "behavioural syndromes"
        name = name.lower()
        patterns = [
            r'\bdevelopmental\b',
            r'\bdisorders\b',
            r'\bdisorders due to\b',
            r'\bdisorder due to\b',
            r'\bdisorders of\b',
            r'\bdisorders due to a\b',
            r'\bdisorder due to a\b',
            r'\bdisorder\b',
            r'\buse of\b',
            r'\bdue to\b',
            r'\b-\b',
            r','
        ]
        for pattern in patterns:
            name = re.sub(pattern, '', name)
        if "imposed on another" in name:
            name = name.replace("imposed on another",
                                "imposed on another person")
        # Clean up any resulting multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.replace("Of ", "")
        return name.capitalize()

    def check_if_children_exsist(self, uri):
        response = self.mongo.find_one({"@id": uri})
        return "child" in response

    def check_if_parent_exsist(self, uri):
        response = self.mongo.find_one({"@id": uri})
        return "parent" in response

    def check_if_node_exists(self, uri: str):
        response = self.mongo.find_one({"@id": uri})
        return response

    def check_severity(self, name: str):
        keywords = ["mild", "moderate", "severe", "antisocial", "dependent"]
        for keyword in keywords:
            if keyword in name.lower():
                return True

    def get_related_symptoms(self, code):
        return mongo_symptom.find_many({"code": code})

    def get_related_diagnosis(self, code):
        return mongo_diagnosis.find_many({"code": code})

    def get_related_prescription(self, code):
        return mongo_prescription.find_many({"code": code})

    def check_or(self, name: str):
        splitted = [part.strip() for part in name.split(" or ")
                    ]
        if len(splitted) > 1:
            return splitted, True
        return None, False

    def node_esxist(G: nx.DiGraph, name: str):
        return G.has_node(name)

    def create_taxonomy(self):
        G = nx.DiGraph()

        # create hierarchy
        all_nodes = self.get_all_docs()
        for node in tqdm(all_nodes):
            if "child" in node:
                children = node["child"]
                edges = []
                for child in children:
                    if not self.check_if_children_exsist(child):
                        continue
                    parent_name = self.clean_name(node["title"]["@value"])
                    child_name = self.clean_name(
                        self.get_entity_name(child))
                    if parent_name in child_name:
                        child_name = child_name.replace(
                            parent_name, "")

                G.add_edges_from(edges)

        nx.write_graphml(G, "./graph.graphml")

    def is_safe_uri(self, uri_str):
        try:
            # This will raise an error if the URI is invalid when serializing
            uri = RDFURIRef(uri_str)
            # Optional: check if serialization works (for n3 or turtle)
            _ = uri.n3()
            return True
        except Exception:
            return False

    def add_entities(self, graph: Graph):
        # Add Diseases
        all_nodes = self.get_all_docs()
        for node in tqdm(all_nodes):
            if "child" in node:
                continue
            current_entity_name = self.clean_name(node["title"]["@value"])
            current_entity_definition = node["definition"]["@value"] if "definition" in node else None
            current_entity_id = URIRef(
                f"{self.entity_uri_base}/{urllib.parse.quote(current_entity_name.replace(' ', '_'))}")
            # add label
            graph.add((current_entity_id,
                       SKOS.prefLabel, Literal(current_entity_name)))
            # add description
            current_entity_definition = node["definition"]["@value"] if "definition" in node else None
            if current_entity_definition is not None:
                graph.add((current_entity_id,
                           SKOS.definition, Literal(current_entity_definition)))
            if "inclusion" in node:
                for inclusion in node["inclusion"]:
                    inclusion_name = inclusion["label"]["@value"]
                    graph.add((current_entity_id,
                               INCLUSION_PROP,
                               Literal(inclusion_name, datatype=XSD.string)))
            parents = node["parent"]
            for parent in parents:
                parent_node = self.get_entity_name(parent)
                if parent_node is None:
                    continue
                parent_name = self.clean_name(self.get_entity_name(parent))
                parent_id = URIRef(
                    f"{self.ontology_uri_base}/{urllib.parse.quote(parent_name.replace(' ', '_'))}")
                if any(graph.triples((parent_id, None, None))):
                    graph.add((current_entity_id, RDF.type, parent_id))

        # Exclusion
        for node in tqdm(all_nodes):
            if "child" in node:
                continue
            if "exclusion" not in node:
                continue
            current_exclusions = node["exclusion"]
            current_class_name = self.clean_name(node["title"]["@value"])
            current_class_id = URIRef(
                f"{self.entity_uri_base}/{urllib.parse.quote(current_class_name.replace(' ', '_'))}")
            for exclusion in current_exclusions:
                uri = exclusion["foundationReference"]
                exclusion_node = self.check_if_node_exists(uri=uri)
                if exclusion_node is None:
                    if any(graph.triples((current_class_id, None, None))):
                        graph.add((current_class_id,
                                   EXCLUSION_PROP, URIRef(uri)))
                else:
                    exclusion_node_name = self.clean_name(
                        exclusion_node["title"]["@value"])
                    exclusion_node_id = URIRef(
                        f"{self.entity_uri_base}/{urllib.parse.quote(exclusion_node_name.replace(' ', '_'))}")
                    if any(graph.triples((current_class_id, None, None))):
                        graph.add((current_class_id,
                                  EXCLUSION_PROP, URIRef(exclusion_node_id)))

        all_entities = list(self.get_all_codes())
        for entity in tqdm(all_entities):
            current_code = entity["code"]
            entity_name = self.clean_name(entity["title"])
            entity_uri = URIRef(
                f"{self.entity_uri_base}/{urllib.parse.quote(entity_name.replace(' ', '_'))}")
            # Add Symptoms
            related_symptoms = self.get_related_symptoms(code=current_code)
            if any(graph.triples((entity_uri, None, None))):
                for symptom in related_symptoms:
                    symptom_name = self.clean_name(symptom["symptom_text"])
                    symptom_id = URIRef(
                        f"{self.entity_uri_base}/{urllib.parse.quote(entity_name.replace(' ', '_'))}")
                    if not self.is_safe_uri(symptom_id):
                        print("NOT SAFE")
                        continue
                    graph.add((symptom_id, SKOS.prefLabel,
                              Literal(symptom_name, datatype=XSD.string)))
                    graph.add((symptom_id, RDF.type, URIRef(
                        f"{self.ontology_uri_base}/MedicalSignOrSymptom")))
                    graph.add((entity_uri, SCHEMA.signOrSymptom, symptom_id))

            # Add Diagnostic Criteria
            related_diagnosis = self.get_related_diagnosis(code=current_code)
            if any(graph.triples((entity_uri, None, None))):
                for diagnosis in related_diagnosis:
                    diagnosis_name = self.clean_name(
                        diagnosis["criterion_text"])
                    diagnosis_id = URIRef(
                        f"{self.entity_uri_base}/{urllib.parse.quote(entity_name.replace(' ', '_'))}")
                    if not self.is_safe_uri(diagnosis_id):
                        print("NOT SAFE")
                        continue
                    graph.add((diagnosis_id, SKOS.prefLabel,
                              Literal(diagnosis_name, datatype=XSD.string)))
                    graph.add((diagnosis_id, RDF.type, URIRef(
                        f"{self.ontology_uri_base}/DiagnosticCriteria")))
                    graph.add(
                        (entity_uri, HAS_DIAGNOSTIC_REQUIREMENTS_PROP, diagnosis_id))

            # Prescription
            related_prescription = self.get_related_prescription(
                code=current_code)
            if any(graph.triples((entity_uri, None, None))):
                for prescription in related_prescription:
                    prescription_name = self.clean_name(
                        prescription["prescription_text"])
                    prescription_id = URIRef(
                        f"{self.entity_uri_base}/{urllib.parse.quote(entity_name.replace(' ', '_'))}")
                    if not self.is_safe_uri(prescription_id):
                        print("NOT SAFE")
                        continue
                    graph.add((prescription_id, SKOS.prefLabel,
                              Literal(prescription_name, datatype=XSD.string)))
                    graph.add((prescription_id, RDF.type, URIRef(
                        f"{self.ontology_uri_base}/DrugClass")))
                    graph.add(
                        (prescription_id, SCHEMA.drug, entity_uri))

    def create_ontology(self, add_entity: bool = False):
        graph = Graph()
        graph.bind("schema", SCHEMA)
        graph.bind("owl", OWL)
        graph.bind("icd-schema", ICD_SCHEMA)
        graph.bind("icd-kg", ICD_KG)
        graph.bind("icd-kg-entity", ICD_KG_ENTITY)

        # define properties
        graph.add((SCHEMA.drug, RDF.type, OWL.ObjectProperty))
        graph.add((EXCLUSION_PROP, RDF.type, OWL.ObjectProperty))
        graph.add((HAS_DIAGNOSTIC_REQUIREMENTS_PROP,
                  RDF.type, OWL.ObjectProperty))
        graph.add((SCHEMA.signOrSymptom, RDF.type, OWL.ObjectProperty))
        graph.add((INCLUSION_PROP, RDF.type, OWL.DatatypeProperty))
        graph.add((INCLUSION_PROP, RDFS.range, XSD.string))
        graph.add((INCLUSION_PROP, RDFS.domain, URIRef(
            f"{self.ontology_uri_base}/Disease")))
        # Range and domain
        graph.add((EXCLUSION_PROP, RDFS.domain, URIRef(
            f"{self.ontology_uri_base}/Disease")))
        graph.add((EXCLUSION_PROP, RDFS.range,
                  URIRef(f"{self.ontology_uri_base}/Disease")))
        graph.add((HAS_DIAGNOSTIC_REQUIREMENTS_PROP, RDFS.domain,
                  URIRef(f"{self.ontology_uri_base}/Disease")))
        graph.add((HAS_DIAGNOSTIC_REQUIREMENTS_PROP, RDFS.range,
                  URIRef(f"{self.ontology_uri_base}/DiagnosticCriteria")))
        graph.add((SCHEMA.drug, RDFS.domain,
                  URIRef(f"{self.ontology_uri_base}/Disease")))
        graph.add((SCHEMA.drug, RDFS.range,
                  URIRef(f"{self.ontology_uri_base}/DrugClass")))
        graph.add((SCHEMA.signOrSymptom, RDFS.domain,
                  URIRef(f"{self.ontology_uri_base}/Disease")))
        graph.add((SCHEMA.signOrSymptom, RDFS.range,
                  URIRef(f"{self.ontology_uri_base}/MedicalSignOrSymptom")))

        # add Disease
        disease_uri = f"{self.ontology_uri_base}/Disease"
        graph.add((URIRef(disease_uri), SKOS.prefLabel,
                  Literal("Disease", datatype=XSD.string)))
        disease_description = "A disorder with homogeneous therapeutic possibilities and an identified pathophysiological mechanism. Developmental anomalies are excluded."
        graph.add((URIRef(disease_uri), SKOS.definition,
                  Literal(disease_description, datatype=XSD.string)))
        graph.add((URIRef(disease_uri), RDF.type, OWL.Class))
        graph.add((URIRef(disease_uri),
                  OWL.equivalentClass, SCHEMA.Disease))

        # Add Drug
        drug_uri = f"{self.ontology_uri_base}/DrugClass"
        graph.add((URIRef(drug_uri), SKOS.prefLabel,
                  Literal("Drug", datatype=XSD.string)))
        drug_description = "A chemical or biologic substance, used as a medical therapy, that has a physiological effect on an organism. Here the term drug is used interchangeably with the term medicine although clinical knowledge makes a clear difference between them."
        graph.add((URIRef(drug_uri), SKOS.definition,
                  Literal(drug_description, datatype=XSD.string)))
        graph.add((URIRef(drug_uri), RDF.type, OWL.Class))
        graph.add((URIRef(drug_uri),
                  OWL.equivalentClass, SCHEMA.DrugClass))

        # Symptoms
        symptom_uri = f"{self.ontology_uri_base}/MedicalSignOrSymptom"
        graph.add((URIRef(symptom_uri), SKOS.prefLabel,
                  Literal("Medical Sign Or Symptom", datatype=XSD.string)))
        symptom_description = "Any feature associated or not with a medical condition. In medicine a symptom is generally subjective while a sign is objective."
        graph.add((URIRef(symptom_uri), SKOS.definition,
                  Literal(symptom_description, datatype=XSD.string)))
        graph.add((URIRef(symptom_uri), RDF.type, OWL.Class))
        graph.add((URIRef(symptom_uri), OWL.equivalentClass,
                  SCHEMA.MedicalSignOrSymptom))

        # Diagnostic Criteria
        diagnostic_criteria_uri = f"{self.ontology_uri_base}/DiagnosticCriteria"
        graph.add((URIRef(diagnostic_criteria_uri), SKOS.prefLabel,
                  Literal("Diagnostic Criteria", datatype=XSD.string)))
        diagnostic_criteria_description = "Any feature associated or not with a medical condition. In medicine a symptom is generally subjective while a sign is objective."
        graph.add((URIRef(diagnostic_criteria_uri), SKOS.definition,
                  Literal(diagnostic_criteria_description, datatype=XSD.string)))
        graph.add(
            (URIRef(diagnostic_criteria_uri), RDF.type, OWL.Class))

        # Add relations
        graph.add((URIRef(drug_uri), SCHEMA.drug,
                  URIRef(disease_uri)))
        graph.add((URIRef(disease_uri),
                  SCHEMA.signOrSymptom, URIRef(symptom_uri)))
        graph.add((URIRef(disease_uri), HAS_DIAGNOSTIC_REQUIREMENTS_PROP,
                  URIRef(diagnostic_criteria_uri)))

        # loop through nodes
        all_nodes = self.get_all_docs()
        for node in tqdm(all_nodes):
            if "child" not in node:
                continue

            current_class_name = self.clean_name(node["title"]["@value"])
            current_class_definition = node["definition"]["@value"] if "definition" in node else None
            current_class_id = f"{self.ontology_uri_base}/{urllib.parse.quote(current_class_name.replace(' ', '_'))}"
            if current_class_name == "Mental behavioural or neurodevelopmental disorders":
                # add subclass of for cap 6 and Disease class
                graph.add((URIRef(current_class_id), RDFS.subClassOf,
                          URIRef(disease_uri)))
            # add label
            graph.add((URIRef(current_class_id),
                      SKOS.prefLabel, Literal(current_class_name, datatype=XSD.string)))
            graph.add(
                (URIRef(current_class_id), RDF.type, OWL.Class))
            # add description
            if current_class_definition is not None:
                graph.add((URIRef(current_class_id),
                           SKOS.definition, Literal(current_class_definition, datatype=XSD.string)))
            if "inclusion" in node:
                for inclusion in node["inclusion"]:
                    inclusion_name = inclusion["label"]["@value"]
                    graph.add((URIRef(current_class_id),
                               INCLUSION_PROP,
                               Literal(inclusion_name, datatype=XSD.string)))
            for child in node["child"]:
                child_name = self.clean_name(self.get_entity_name(child))
                child_id = f"{self.ontology_uri_base}/{urllib.parse.quote(child_name.replace(' ', '_'))}"
                graph.add((URIRef(child_id), RDFS.subClassOf,
                          URIRef(current_class_id)))
        # Exclusion
        for node in tqdm(all_nodes):
            if "child" not in node:
                continue
            if "exclusion" not in node:
                continue
            current_exclusions = node["exclusion"]
            current_class_name = self.clean_name(node["title"]["@value"])
            current_class_id = f"{self.ontology_uri_base}/{urllib.parse.quote(current_class_name.replace(' ', '_'))}"
            for exclusion in current_exclusions:
                uri = exclusion["foundationReference"]
                exclusion_node = self.check_if_node_exists(uri=uri)
                if exclusion_node is None:
                    if any(URIRef(current_class_id)
                           in triple for triple in graph):
                        graph.add((URIRef(current_class_id),
                                   EXCLUSION_PROP, URIRef(uri)))
                else:
                    exclusion_node_name = self.clean_name(
                        exclusion_node["title"]["@value"])
                    exclusion_node_id = f"{self.ontology_uri_base}/{urllib.parse.quote(exclusion_node_name.replace(' ', '_'))}"
                    if any(URIRef(exclusion_node_id) in triple for triple in graph):
                        graph.add((URIRef(current_class_id),
                                  EXCLUSION_PROP, URIRef(exclusion_node_id)))
        if add_entity:
            self.add_entities(graph=graph)

        graph.serialize(destination=f"./icd_11_ontology.ttl", format="turtle")

        return graph

    def networkx_to_d3_json(self, G, root_node=None):
        if root_node is None:
            roots = [n for n in G.nodes() if G.in_degree(n) == 0]
            if len(roots) != 1:
                raise ValueError(
                    "Graph must have exactly one root node for tree conversion")
            root_node = roots[0]

        def build_subtree(node):
            children = list(G.successors(node))
            if not children:
                return {"name": str(node).strip().capitalize(), "size": 1}

            subtree = {"name": str(node).strip().capitalize()}
            subtree["children"] = [
                build_subtree(child) for child in children]
            return subtree

        return build_subtree(root_node)

    def extract_statistics(self, graph: Graph):
        stats = {}

        # 1. Classi definite localmente
        classes = set(graph.subjects(RDF.type, OWL.Class))
        stats["n_classes_local"] = len([
            cls for cls in classes if str(cls).startswith(self.ontology_uri_base)
        ])
        stats["n_classes_imported"] = len(classes) - stats["n_classes_local"]

        # ➕ Number of all classes matching 'http://icd_kg/6/ontology/'
        stats["n_classes"] = len([
            cls for cls in classes if str(cls).startswith("http://icd_kg/6/ontology/")
        ])

        # 2. Proprietà definite localmente
        properties = set(graph.predicates())
        properties = {p for p in properties if p != RDF.type}
        stats["n_properties_local"] = len([
            p for p in properties if str(p).startswith(self.ontology_uri_base) or str(p).startswith("http://icd_kg")
        ])
        stats["n_properties_imported"] = len(
            properties) - stats["n_properties_local"]

        # 🆕 Print all properties
        print("\n🔎 All Properties Found in Graph:")
        for p in sorted(properties):
            print(f" - {p}")

        # 3. EquivalentClass
        equivalent_classes = list(graph.triples(
            (None, OWL.equivalentClass, None)))
        stats["n_equivalent_classes"] = len(equivalent_classes)

        # 4. Profondità media della gerarchia (basata su RDFS.subClassOf)
        import networkx as nx

        G = nx.DiGraph()
        for s, _, o in graph.triples((None, RDFS.subClassOf, None)):
            G.add_edge(str(o), str(s))  # edge da parent a child

        roots = [n for n in G.nodes() if G.in_degree(n) == 0]
        all_depths = []

        def dfs(node, depth):
            children = list(G.successors(node))
            if not children:
                all_depths.append(depth)
            for child in children:
                dfs(child, depth + 1)

        for root in roots:
            dfs(root, 1)

        stats["avg_hierarchy_depth"] = sum(
            all_depths) / len(all_depths) if all_depths else 0
        stats["max_hierarchy_depth"] = max(all_depths) if all_depths else 0

        # ➕ Number of entities (individuals) from 'http://icd_kg/6/entity/'
        entities = set(graph.subjects(RDF.type, None))
        stats["n_entities"] = len([
            e for e in entities if str(e).startswith("http://icd_kg/6/entity/")
        ])

        print("\n📊 RDF Graph Statistics:")
        for k, v in stats.items():
            print(f"{k}: {v}")

        return stats


graph = HierarchicalRepresentation().create_ontology(add_entity=False)
print(HierarchicalRepresentation().extract_statistics(graph=graph))
