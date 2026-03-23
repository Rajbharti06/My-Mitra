import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
import encryption_utils
from typing import Optional, List

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
    
    def retrieve_memories(
        self,
        query_text: str,
        user_id: Optional[int] = None,
        top_k: int = 4,
        allowed_categories: Optional[List[str]] = None,
    ) -> List[str]:
        """Retrieve relevant memories scoped to user and (optionally) categories."""
        candidates = self.retrieve_memory(
            query_text=query_text,
            n_results=max(top_k * 5, top_k),
            user_id=user_id,
            allowed_categories=allowed_categories,
        )
        return candidates[:top_k]
        
    def store_memory(self, user_id, content, memory_type="conversation"):
        """Backward-compatible wrapper for category-less storage."""
        return self.store_memory_with_category(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            memory_category=memory_type,
        )

    def store_memory_with_category(
        self,
        user_id,
        content: str,
        memory_type: str = "conversation",
        memory_category: str = "conversation",
    ):
        """
        Store a memory with explicit category for consent-based retrieval.
        """
        metadata = {
            "user_id": str(user_id),
            "type": memory_type,
            "category": memory_category,
            "timestamp": str(datetime.datetime.now()),
        }
        return self.add_memory(content, metadata)

    def retrieve_memory(
        self,
        query_text: str,
        n_results: int = 1,
        *,
        user_id: Optional[int] = None,
        allowed_categories: Optional[List[str]] = None,
    ) -> List[str]:
        """Retrieve and decrypt memories scoped to a user and categories."""
        where = {"user_id": str(user_id)} if user_id is not None else None

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas"],
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        decrypted_docs: List[str] = []

        # One query_text => one result list. Keep code resilient to Chroma shape.
        for doc_list, meta_list in zip(documents, metadatas):
            for doc, meta in zip(doc_list, meta_list or []):
                cat = (meta or {}).get("category") or (meta or {}).get("type")
                if allowed_categories is not None and cat not in allowed_categories:
                    continue
                try:
                    decrypted = encryption_utils.decrypt_data(doc)
                    decrypted_docs.append(decrypted)
                except Exception:
                    continue
            break

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
    try:
        global _long_term_memory_instance
        if _long_term_memory_instance is None:
            _long_term_memory_instance = LongTermMemory()
        return _long_term_memory_instance.retrieve_memories(
            query_text=query,
            user_id=int(user_id),
            top_k=top_k,
            allowed_categories=None,
        )
    except Exception:
        return []


_long_term_memory_instance: Optional[LongTermMemory] = None
