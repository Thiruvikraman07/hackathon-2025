"""Vector memory for long-term storage of strategic themes and context."""
from typing import Dict, List, Optional, Any
import chromadb
from chromadb.config import Settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from ..config import settings, logger


class VectorMemory:
    """
    Long-term memory using vector store for strategic themes and context.
    Stores information that persists across sessions and can be retrieved semantically.
    """

    def __init__(
        self,
        collection_name: str = "strategic_context",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize vector memory.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_directory

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )

        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        logger.info(f"Initialized VectorMemory with collection: {collection_name}")

    def store(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Store information in vector memory.

        Args:
            text: Text to store
            metadata: Optional metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        try:
            ids = self.vectorstore.add_texts(
                texts=[text],
                metadatas=[metadata] if metadata else None,
                ids=[doc_id] if doc_id else None
            )
            logger.info(f"Stored document with ID: {ids[0]}")
            return ids[0]
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            raise

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from memory.

        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of relevant documents with metadata
        """
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )

            formatted_results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]

            logger.info(f"Retrieved {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise

    def update(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update a document in memory.

        Args:
            doc_id: Document ID to update
            text: New text
            metadata: New metadata
        """
        try:
            # Delete old document
            self.vectorstore._collection.delete(ids=[doc_id])

            # Add updated document
            self.store(text=text, metadata=metadata, doc_id=doc_id)

            logger.info(f"Updated document: {doc_id}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise

    def delete(self, doc_id: str) -> None:
        """
        Delete a document from memory.

        Args:
            doc_id: Document ID to delete
        """
        try:
            self.vectorstore._collection.delete(ids=[doc_id])
            logger.info(f"Deleted document: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    def clear(self) -> None:
        """Clear all documents from memory."""
        try:
            self.vectorstore._collection.delete()
            logger.warning(f"Cleared all documents from collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def persist(self) -> None:
        """Persist the vector store to disk."""
        try:
            self.vectorstore.persist()
            logger.info(f"Persisted vector store to: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Error persisting vector store: {e}")
            raise
