from pymongo import MongoClient
from typing import Dict, List, Optional


class MongoDB:
    """
    A MongoDB database handler class for CRUD operations.

    Attributes:
        client (MongoClient): MongoDB client connection.
        db_name (str): Database name.
        collection_name (str): Collection name.
    """

    def __init__(
        self,
        db_name: str,
        collection_name: str,
        host: str = "mongo",
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize MongoDB connection and set database/collection.

        Args:
            db_name (str): Database name.
            collection_name (str): Collection name.
            host (str): MongoDB host (default: "localhost").
            port (int): MongoDB port (default: 27017).
            username (str, optional): MongoDB username.
            password (str, optional): MongoDB password.
        """
        self.client = MongoClient(
            host=host,
            port=port,
            username=username,
            password=password,
            connectTimeoutMS=20000
        )
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_one(self, document: Dict) -> str:
        """
        Insert a single document into the collection.

        Args:
            document (Dict): Document to insert.

        Returns:
            str: Inserted document's _id.
        """
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def insert_many(self, documents: List[Dict]) -> List[str]:
        """
        Insert multiple documents into the collection.

        Args:
            documents (List[Dict]): List of documents to insert.

        Returns:
            List[str]: List of inserted _ids.
        """
        result = self.collection.insert_many(documents)
        return [str(_id) for _id in result.inserted_ids]

    def find_one(self, query: Dict) -> Optional[Dict]:
        """
        Find a single document matching the query.

        Args:
            query (Dict): Query filter.

        Returns:
            Optional[Dict]: The found document (or None if not found).
        """
        document = self.collection.find_one(query)
        if document:
            document["_id"] = str(document["_id"])  # Convert ObjectId to str
        return document

    def find_many(self, query: Dict = None, limit: int = 100000) -> List[Dict]:
        """
        Find multiple documents matching the query.

        Args:
            query (Dict, optional): Query filter (default: None → find all).
            limit (int, optional): Max documents to return (default: 10).

        Returns:
            List[Dict]: List of matching documents.
        """
        if query is None:
            query = {}
        documents = self.collection.find(query).limit(limit)
        return [{**doc, "_id": str(doc["_id"])} for doc in documents]

    def update_one(self, query: Dict, update_data: Dict) -> bool:
        """
        Update a single document matching the query.

        Args:
            query (Dict): Query filter.
            update_data (Dict): New data (use MongoDB operators like $set).

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.collection.update_one(query, update_data)
        return result.modified_count > 0

    def update_many(self, query: Dict, update_data: Dict) -> int:
        """
        Update multiple documents matching the query.

        Args:
            query (Dict): Query filter.
            update_data (Dict): New data (use MongoDB operators like $set).

        Returns:
            int: Number of documents modified.
        """
        result = self.collection.update_many(query, update_data)
        return result.modified_count

    def delete_one(self, query: Dict) -> bool:
        """
        Delete a single document matching the query.

        Args:
            query (Dict): Query filter.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.collection.delete_one(query)
        return result.deleted_count > 0

    def delete_many(self, query: Dict) -> int:
        """
        Delete multiple documents matching the query.

        Args:
            query (Dict): Query filter.

        Returns:
            int: Number of documents deleted.
        """
        result = self.collection.delete_many(query)
        return result.deleted_count

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
