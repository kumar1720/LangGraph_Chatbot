from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore

from app.core.config import settings
from app.utils.logger import setup_logger
from app.utils.qdrant import format_chat_results

logger = setup_logger(__name__)


class GoogleGenerativeAIEmbeddings768(GoogleGenerativeAIEmbeddings):
    """Custom wrapper for GoogleGenerativeAIEmbeddings to enforce 768 output dimensions with gemini-embedding-2."""
    def embed_documents(self, texts: List[str], **kwargs) -> List[List[float]]:
        kwargs.setdefault("output_dimensionality", 768)
        return super().embed_documents(texts, **kwargs)

    def embed_query(self, text: str, **kwargs) -> List[float]:
        kwargs.setdefault("output_dimensionality", 768)
        return super().embed_query(text, **kwargs)


class MultiTenantVectorStore:
    """A multi-tenant vector store using Qdrant for efficient semantic search with tenant isolation.
    
    This class implements the approach from the tutorial on building multi-tenant chatbots
    with Qdrant. It uses payload partitioning with tenant_id for data isolation.
    """
    _instances = {}

    def __new__(cls, collection_name: str = "multi_tenant_chat_history", *args, **kwargs):
        # Extract collection_name if passed as kwargs or positional argument
        if "collection_name" in kwargs:
            col_name = kwargs["collection_name"]
        else:
            col_name = collection_name

        if col_name not in cls._instances:
            instance = super(MultiTenantVectorStore, cls).__new__(cls)
            instance._initialized = False
            cls._instances[col_name] = instance
        return cls._instances[col_name]
    
    def __init__(
        self,
        collection_name: str = "multi_tenant_chat_history",
        embedding: Optional[Embeddings] = None
    ):
        """Initialize the multi-tenant vector store pointing to Qdrant Cloud and using Gemini Embeddings."""
        if self._initialized:
            return
            
        # Establish connection to secure Qdrant Cloud Cluster
        qdrant_url = settings.QDRANT_HOST
        if not qdrant_url.startswith(("http://", "https://")):
            qdrant_url = f"https://{qdrant_url}"
            
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = collection_name
        self.embedding_size = 768
        
        # Instantiate Gemini gemini-embedding-2 with forced 768 dimension output
        self.embedding = embedding or GoogleGenerativeAIEmbeddings768(
            model="models/gemini-embedding-2",
            google_api_key=settings.GEMINI_API_KEY
        )

        self._ensure_collection_exists()
        self._initialized = True
        
    def _ensure_collection_exists(self) -> None:
        """Create the collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            logger.info(f"Creating new collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_size,
                    distance=models.Distance.COSINE
                )
            )
        else:
            logger.info(f"Collection {self.collection_name} already exists")

        # Create payload keyword indexes for tenant isolation to avoid "Index required but not found" error in Qdrant Cloud
        for field in ["metadata.tenant_id", "metadata.user_id", "metadata.chat_id"]:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.info(f"Payload keyword index created on '{field}' in collection '{self.collection_name}'")
            except Exception as e:
                # If index already exists or another minor issue, we log it and continue
                logger.debug(f"Payload index on '{field}' in '{self.collection_name}' already exists or failed to create: {e}")
    
    def store_conversation(
        self, 
        question: str, 
        answer: str, 
        tenant_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Store a conversation in the vector store with tenant isolation"""
        doc = Document(
            page_content=f"User: {question}\nAssistant: {answer}",
            metadata=metadata or {}
        )

        doc.metadata["tenant_id"] = tenant_id

        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding
        )

        return vector_store.add_documents([doc])
        
    def get_chats_by_user_id(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all chat messages for a specific user, with pagination"""
        response = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.tenant_id",
                        match=models.MatchValue(value=tenant_id)
                    ),
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=str(user_id))
                    )
            ]),
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        results = format_chat_results(response[0])
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results
        
    def get_chat_by_id(
        self,
        chat_id: str,
        tenant_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all messages for a specific chat ID belonging to a user"""
        response = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.tenant_id",
                        match=models.MatchValue(value=tenant_id)
                    ),
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=str(user_id))
                    ),
                    models.FieldCondition(
                        key="metadata.chat_id",
                        match=models.MatchValue(value=chat_id)
                    )
            ]),
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        results = format_chat_results(response[0])
        results.sort(key=lambda x: x.get("timestamp", ""))
        return results
