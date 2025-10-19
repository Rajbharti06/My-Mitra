import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
import encryption_utils

class LongTermMemory:
    def __init__(self, collection_name="mymitra_memory", persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using a default Sentence Transformer embedding function optimized for emotional context
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Encrypted user conversations and emotional context"}
        )
        # Ensure memory directory exists and is secure
        os.makedirs(persist_directory, mode=0o700, exist_ok=True)

    def add_memory(self, text, metadata=None):
        # ChromaDB requires ids to be strings
        import uuid
        
        # Encrypt memory before storage
        encrypted_text = encryption_utils.encrypt_data(text)
        
        unique_id = str(uuid.uuid4())
        metadata = metadata if metadata else {}
        metadata.update({"encrypted": True, "timestamp": str(datetime.datetime.now())})
        
        self.collection.add(
            documents=[encrypted_text],
            metadatas=[metadata],
            ids=[unique_id]
        )
        return unique_id

    def retrieve_memory(self, query_text, n_results=1):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Decrypt memories before returning
        documents = results.get('documents', [])
        decrypted_docs = []
        for doc_list in documents:
            decrypted_list = []
            for doc in doc_list:
                try:
                    decrypted = encryption_utils.decrypt_data(doc)
                    decrypted_list.append(decrypted)
                except Exception:
                    # Skip corrupted or unencrypted entries
                    continue
            decrypted_docs.append(decrypted_list)
        return decrypted_docs

    def list_all_memories(self):
        # Note: This might be slow for very large collections
        return self.collection.get(ids=self.collection.get()['ids'])['documents']

    def delete_memory(self, memory_id):
        self.collection.delete(ids=[memory_id])


def retrieve_memories(user_id: str, query: str, top_k: int = 4):
    """
    Retrieves memories for a user based on a query.
    NOTE: user_id is not used yet, but will be used for multi-user support.
    """
    memory = LongTermMemory()
    results = memory.retrieve_memory(query_text=query, n_results=top_k)
    # The pipeline expects a flat list of strings
    if results and len(results) > 0:
        return results[0]
    return []
