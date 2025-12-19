import chromadb
import uuid

class KnowledgeRetriever:
    def __init__(self, persist_directory="./knowledge_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="paper_knowledge")

    def add_document(self, text, source_name):
        """
        Chunks the text and adds it to the database.
        """
        # Simple recursive chunking (mocked for simplicity, or we can import LangChain)
        # minimal implementation:
        chunk_size = 1000
        overlap = 100
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)

        if not chunks:
            return

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(chunks)} chunks from {source_name} to knowledge base.")

    def query(self, query_text, n_results=3):
        """
        Retrieves relevant chunks.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        if results['documents']:
            return results['documents'][0]
        return []
