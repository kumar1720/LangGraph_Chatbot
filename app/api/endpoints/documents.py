# app/api/endpoints/documents.py
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from typing import Annotated
from app.api.deps import get_current_user
from app.models.user import User
from app.services.vector_store import MultiTenantVectorStore
from app.services.rag_service import RAGService

router = APIRouter()
vector_store = MultiTenantVectorStore(collection_name="multi_tenant_rag_docs")
rag_service = RAGService(vector_store)

@router.post("/upload")
async def upload_document(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        content = await file.read()
        await rag_service.ingest_document(
            file_content=content,
            filename=file.filename,
            tenant_id=current_user.tenant_id,
            user_id=str(current_user.id)
        )
        return {"status": "success", "message": f"Successfully ingested {file.filename}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
