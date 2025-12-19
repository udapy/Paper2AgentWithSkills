import chromadb
from chromadb.config import Settings
import uuid

class SkillRegistry:
    def __init__(self, persist_directory="./skills_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="skills")

    def retrieve(self, query, n_results=1):
        """
        Semantic search for existing tools/skills.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Unpack results if any found
        if results['documents'] and results['documents'][0]:
            return results['documents'][0][0] # Return the best match code
        return None

    def store(self, function_code, description, verification_log):
        """
        Store a skill only if it has passed verification.
        """
        if not verification_log.get("success", False):
            # Do not store failed skills
            return False

        self.collection.add(
            documents=[function_code],
            metadatas=[{"description": description, "verified": True}],
            ids=[str(uuid.uuid4())]
        )
        return True
