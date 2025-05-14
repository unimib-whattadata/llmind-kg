from database import MongoDB
import requests
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import FOAF, XSD, RDF, RDFS


class LLMindKG:

    def __init__(self):
        self.mongo = MongoDB(db_name="llmind", collection_name="llmind_kg")
        self.client_id = "03e71bf1-a067-4a66-826e-1d22ed36e13d_808df701-1568-40ac-bd30-a156880be598"
        self.client_secret = "v0LUnXLrRU9PNnc4CIEfh0TdlkoRYk0fMX7x8b51/Zw="
        self.scope = 'icdapi_access'
        self.grant_type = 'client_credentials'
        self.token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'
        self.payload = {'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'scope': self.scope,
                        'grant_type': self.grant_type}
        r = requests.post(self.token_endpoint,
                          data=self.payload, verify=True).json()
        self.token = r['access_token']
        self.node_inserted: set[str] = set()

    def make_request(self, uri: str):

        headers = {'Authorization':  'Bearer '+self.token,
                   'Accept': 'application/json',
                   'Accept-Language': 'en',
                   'API-Version': 'v2'}
        response = requests.get(uri, headers=headers, verify=True)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception()

    def save_kg(self, uri: str):
        if uri in self.node_inserted:
            return
        print("PROCESS", uri)
        request_result = self.make_request(uri=uri)
        self.node_inserted.add(request_result["@id"])
        print("INSERTED", self.mongo.insert_one(request_result))
        if "child" not in request_result:
            return
        children: list = request_result["child"]
        for child in children:
            self.save_kg(uri=child)

    def build_kg(self, ):
        return
