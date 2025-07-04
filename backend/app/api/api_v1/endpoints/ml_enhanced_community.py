"""ML-Enhanced Smart Community API Endpoints.

This module provides API endpoints that showcase the ML-enhanced community features
and demonstrate the migration from heuristic to ML-based approaches.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.smart_community_ml_integration import (
    MLEnhancedSmartCommunityService,
    HeuristicToMLMigrationGuide,
    demonstrate_ml_migration
)
from app.services.vector_database_service import VectorDatabaseService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

router = APIRouter()

# Initialize services
embedding_service = EmbeddingService()
vector_service = VectorDatabaseService(embedding_service)
rag_service = RAGService()
ml_enhanced_service = MLEnhancedSmartCommunityService(vector_service, embedding_service, rag_service)


@router.get("/users/{user_id}/similar-ml", response_model=List[Dict[str, Any]])
async def find_similar_users_ml_enhanced(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    use_ml_scoring: bool = Query(True, description="Use ML-enhanced scoring instead of heuristic"),
    db: AsyncSession = Depends(get_db)
):
    """Find similar users using ML-enhanced analysis."""
    try:
        matches = await ml_enhanced_service.find_similar_users_ml_enhanced(
            db=db, user_id=user_id, limit=limit, use_ml_scoring=use_ml_scoring
        )
        
        return [
            {
                "user_id": match.user_id,
                "username": match.username,
                "similarity_score": match.similarity_score,
                "method_used": "ml_enhanced" if use_ml_scoring else "heuristic"
            }
            for match in matches
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/migration/roadmap", response_model=Dict[str, Any])
async def get_ml_migration_roadmap():
    """Get the roadmap for migrating from heuristic to ML methods."""
    try:
        migration_guide = HeuristicToMLMigrationGuide()
        roadmap = migration_guide.get_migration_roadmap()
        
        return {
            "title": "Heuristic to ML Migration Roadmap",
            "phases": roadmap,
            "total_phases": len(roadmap)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/migration/demonstrate", response_model=Dict[str, Any])
async def demonstrate_migration():
    """Demonstrate the ML migration process."""
    try:
        results = demonstrate_ml_migration()
        return {
            "title": "ML Migration Demonstration",
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
