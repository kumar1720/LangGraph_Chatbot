# app/services/rag_service.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
from io import BytesIO
from app.services.vector_store import MultiTenantVectorStore
from qdrant_client import models

class RAGService:
    def __init__(self, vector_store: MultiTenantVectorStore):
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def extract_text(self, file_content: bytes, filename: str) -> str:
        if filename.endswith(".pdf"):
            reader = PdfReader(BytesIO(file_content))
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif filename.endswith((".txt", ".md")):
            return file_content.decode("utf-8", errors="ignore")
        else:
            raise ValueError("Unsupported file format. Please upload PDF, TXT, or MD.")

    async def ingest_document(self, file_content: bytes, filename: str, tenant_id: str, user_id: str):
        text = self.extract_text(file_content, filename)
        if not text.strip():
            raise ValueError("No extractable text content found in the document.")
            
        chunks = self.text_splitter.split_text(text)
        
        docs = []
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "filename": filename,
                    "chunk_id": i
                }
            ))
        
        # Add documents to Qdrant Cloud using the free embedding model
        from langchain_qdrant import QdrantVectorStore
        vector_db = QdrantVectorStore(
            client=self.vector_store.client,
            collection_name="multi_tenant_rag_docs",
            embedding=self.vector_store.embedding
        )
        vector_db.add_documents(docs)

    def retrieve_context(self, query: str, tenant_id: str, user_id: str, limit: int = 4) -> str:
        # Perform similarity search with strict payload isolation filters
        query_vector = self.vector_store.embedding.embed_query(query)
        
        response = self.vector_store.client.query_points(
            collection_name="multi_tenant_rag_docs",
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.tenant_id",
                        match=models.MatchValue(value=tenant_id)
                    ),
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        )
        
        contexts = [hit.payload.get("page_content", "") for hit in response.points if hit.payload]
        return "\n\n".join(contexts)
