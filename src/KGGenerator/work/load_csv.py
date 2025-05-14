import csv
from typing import List, Dict, Optional
from pymongo import MongoClient
from database import MongoDB


class CSVToMongoDBLoader:
    """
    A class to load CSV data into MongoDB, handling BOM and malformed data.
    """

    def __init__(
        self,
        db_name: str,
        collection_name: str,
        csv_path: str,
        encoding: str = 'utf-8-sig',  # Handles BOM automatically
        delimiter: str = ';'  # Default to semicolon (adjust if needed)
    ):
        self.mongodb = MongoDB(
            db_name=db_name,
            collection_name=collection_name,
        )
        self.csv_path = csv_path
        self.encoding = encoding
        self.delimiter = delimiter

    def read_csv(self) -> List[Dict]:
        """Read CSV and handle BOM, ensuring proper headers."""
        with open(self.csv_path, 'r', encoding=self.encoding) as csv_file:
            # Skip BOM if present (handled by 'utf-8-sig')
            csv_reader = csv.DictReader(csv_file, delimiter=self.delimiter)
            return [row for row in csv_reader]

    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """Ensure all keys are strings and remove None/empty values."""
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for key, value in row.items():
                # Ensure key is a string (MongoDB rejects None keys)
                if key is None:
                    continue  # Skip None keys
                key = str(key).strip()  # Remove BOM and whitespace
                if not key:  # Skip empty keys
                    continue
                # Clean value (strip whitespace, handle empty strings)
                if isinstance(value, str):
                    value = value.strip()
                    if not value:  # Skip empty strings
                        continue
                cleaned_row[key] = value
            if cleaned_row:  # Only add if row has valid data
                cleaned_data.append(cleaned_row)
        return cleaned_data

    def load_data(self, batch_size: int = 1000) -> List[str]:
        """Load cleaned CSV data into MongoDB in batches."""
        raw_data = self.read_csv()
        cleaned_data = self.clean_data(raw_data)

        inserted_ids = []
        for i in range(0, len(cleaned_data), batch_size):
            batch = cleaned_data[i:i + batch_size]
            inserted_ids.extend(self.mongodb.insert_many(batch))

        return inserted_ids

    def close_connection(self):
        """Close MongoDB connection."""
        self.mongodb.close()


if __name__ == "__main__":
    loader = CSVToMongoDBLoader(
        db_name="llmind",
        collection_name="symptom",
        csv_path="./symptom.csv",
        delimiter=";"
    )

    try:
        inserted_ids = loader.load_data(batch_size=500)
        print(f"Inserted {len(inserted_ids)} documents successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        loader.close_connection()
