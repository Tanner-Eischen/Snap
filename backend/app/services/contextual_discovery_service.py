"""Contextual discovery feed service for personalized content curation."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user_plant import UserPlant
from app.models.story import Story
from app.models.plant_question import PlantQuestion
from app.models.plant_trade import PlantTrade
from app.models.rag_models import PlantKnowledgeBase, RAGInteraction, UserPreferenceEmbedding
from app.services.vector_database_service import VectorDatabaseService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content in the discovery feed."""
    STORY = "story"
    QUESTION = "question"
    TRADE = "trade"
    KNOWLEDGE = "knowledge"
    TIP = "tip"
    TRENDING = "trending"


@dataclass
class DiscoveryItem:
    """A single item in the discovery feed."""
    id: str
    content_type: ContentType
    title: str
    content: str
    author_id: Optional[str]
    author_name: Optional[str]
    relevance_score: float
    engagement_score: float
    personalization_factors: List[str]
    tags: List[str]
    plant_species: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class FeedContext:
    """Context for feed personalization."""
    user_id: str
    user_preferences: Dict[str, Any]
    current_plants: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    seasonal_context: Dict[str, Any]
    location: Optional[str]
    time_of_day: str
    feed_type: str


class ContextualDiscoveryService:
    """Service for curating personalized discovery feeds using RAG."""
    
    def __init__(self, vector_service: VectorDatabaseService, embedding_service: EmbeddingService):
        self.vector_service = vector_service
        self.embedding_service = embedding_service
    
    async def generate_personalized_feed(
        self,
        db: AsyncSession,
        user_id: str,
        feed_type: str = "home",
        limit: int = 20
    ) -> List[DiscoveryItem]:
        """Generate personalized discovery feed for user."""
        try:
            # Build feed context
            context = await self._build_feed_context(db, user_id, feed_type)
            
            # Get content from different sources
            content_items = []
            
            # Stories from similar users
            stories = await self._get_relevant_stories(db, context, limit // 4)
            content_items.extend(stories)
            
            # Plant questions user might be interested in
            questions = await self._get_relevant_questions(db, context, limit // 4)
            content_items.extend(questions)
            
            # Trading opportunities
            trades = await self._get_relevant_trades(db, context, limit // 6)
            content_items.extend(trades)
            
            # Knowledge base articles
            knowledge = await self._get_relevant_knowledge(db, context, limit // 6)
            content_items.extend(knowledge)
            
            # Rank all content by relevance and engagement
            ranked_items = await self._rank_content_items(db, context, content_items)
            
            # Apply diversity filters
            final_feed = self._apply_feed_filters(ranked_items, context)
            
            logger.info(f"Generated personalized feed with {len(final_feed)} items for user {user_id}")
            return final_feed[:limit]
            
        except Exception as e:
            logger.error(f"Error generating personalized feed: {str(e)}")
            return []
    
    async def analyze_user_behavior(
        self,
        db: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns for better personalization."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            interactions_stmt = select(RAGInteraction).where(
                and_(
                    RAGInteraction.user_id == user_id,
                    RAGInteraction.created_at >= cutoff_date
                )
            )
            
            interactions_result = await db.execute(interactions_stmt)
            interactions = interactions_result.scalars().all()
            
            behavior_analysis = {
                "total_interactions": len(interactions),
                "content_preferences": self._analyze_content_preferences(interactions),
                "engagement_patterns": self._analyze_engagement_patterns(interactions),
                "topic_interests": self._analyze_topic_interests(interactions),
                "active_times": self._analyze_active_times(interactions)
            }
            
            return behavior_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return {}
    
    async def get_trending_topics(
        self,
        db: AsyncSession,
        time_window: str = "week",
        limit: int = 10,
        use_ml_enhanced: bool = True,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trending topics in the plant community.
        
        Now supports both ML-enhanced analysis (default) and legacy heuristic fallback.
        """
        try:
            if use_ml_enhanced:
                # Try ML-enhanced trending analysis first
                try:
                    from app.services.ml_trending_topics_service import (
                        MLTrendingTopicsService, 
                        TrendAnalysisContext
                    )
                    
                    # Initialize ML service
                    ml_service = MLTrendingTopicsService(self.embedding_service, self.vector_service)
                    
                    # Build context for ML analysis
                    context = TrendAnalysisContext(
                        time_window=time_window,
                        user_id=user_id,
                        location=None,
                        plant_interests=[],
                        experience_level="intermediate",
                        seasonal_context={"season": "current"},
                        personalization_factors=[]
                    )
                    
                    # Get ML-enhanced trending topics
                    ml_trends = await ml_service.analyze_trending_topics(db, context, limit)
                    
                    # Convert to legacy format for compatibility
                    trending_topics = []
                    for trend in ml_trends:
                        trending_topics.append({
                            "topic": trend.normalized_topic,
                            "frequency": trend.metadata.get('document_count', 1),
                            "trend_score": trend.trend_score,
                            "momentum": trend.momentum,
                            "confidence": trend.confidence,
                            "phase": trend.phase.value,
                            "sources": [s.value for s in trend.sources],
                            "engagement_rate": trend.engagement_rate,
                            "sentiment_score": trend.sentiment_score,
                            "ml_enhanced": True
                        })
                    
                    logger.info(f"Generated {len(trending_topics)} ML-enhanced trending topics")
                    return trending_topics
                    
                except Exception as ml_error:
                    logger.warning(f"ML trending analysis failed, falling back to heuristic: {str(ml_error)}")
                    # Fall through to legacy method
            
            # Legacy heuristic method (fallback)
            logger.info("Using legacy heuristic trending topics detection")
            
            # Calculate time window
            if time_window == "day":
                cutoff = datetime.utcnow() - timedelta(days=1)
            elif time_window == "week":
                cutoff = datetime.utcnow() - timedelta(weeks=1)
            else:
                cutoff = datetime.utcnow() - timedelta(days=30)
            
            # Get recent interactions
            interactions_stmt = select(RAGInteraction).where(
                RAGInteraction.created_at >= cutoff
            )
            
            interactions_result = await db.execute(interactions_stmt)
            interactions = interactions_result.scalars().all()
            
            # Enhanced heuristic topic extraction (improved from simple word splitting)
            topic_counts = {}
            plant_keywords = {
                "watering", "fertilizer", "light", "soil", "pest", "disease", 
                "propagation", "repotting", "pruning", "humidity", "temperature",
                "growth", "leaves", "roots", "flowering", "care"
            }
            
            for interaction in interactions:
                if interaction.query_text:
                    words = interaction.query_text.lower().split()
                    # Focus on plant-related keywords
                    for word in words:
                        if len(word) > 3 and (word in plant_keywords or 
                                            any(keyword in word for keyword in plant_keywords)):
                            topic_counts[word] = topic_counts.get(word, 0) + 1
            
            # Sort by frequency
            trending = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            
            trending_topics = []
            for topic, count in trending[:limit]:
                trending_topics.append({
                    "topic": topic.replace('_', ' ').title(),
                    "frequency": count,
                    "trend_score": count / len(interactions) if interactions else 0,
                    "momentum": 0.0,  # Not calculated in legacy method
                    "confidence": min(1.0, count / 10),  # Simple confidence
                    "phase": "stable",
                    "sources": ["rag_interactions"],
                    "engagement_rate": 0.5,  # Default
                    "sentiment_score": 0.0,  # Not calculated in legacy
                    "ml_enhanced": False
                })
            
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {str(e)}")
            return []
    
    async def _build_feed_context(
        self,
        db: AsyncSession,
        user_id: str,
        feed_type: str
    ) -> FeedContext:
        """Build context for feed personalization."""
        try:
            # Get user information
            user_stmt = select(User).where(User.id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get user's plants
            plants_stmt = select(UserPlant).options(
                selectinload(UserPlant.species)
            ).where(UserPlant.user_id == user_id)
            plants_result = await db.execute(plants_stmt)
            plants = plants_result.scalars().all()
            
            current_plants = []
            for plant in plants:
                current_plants.append({
                    "id": str(plant.id),
                    "species_id": str(plant.species.id),
                    "species_name": plant.species.scientific_name,
                    "health_status": plant.health_status
                })
            
            # Get user preferences
            prefs_stmt = select(UserPreferenceEmbedding).where(
                UserPreferenceEmbedding.user_id == user_id
            )
            prefs_result = await db.execute(prefs_stmt)
            preferences = prefs_result.scalars().all()
            
            user_preferences = {}
            for pref in preferences:
                user_preferences[pref.preference_type] = {
                    "confidence": float(pref.confidence_score),
                    "last_updated": pref.last_updated
                }
            
            # Get seasonal context
            seasonal_context = self._get_current_seasonal_context(user.location)
            
            # Determine time of day
            current_hour = datetime.utcnow().hour
            if 6 <= current_hour < 12:
                time_of_day = "morning"
            elif 12 <= current_hour < 18:
                time_of_day = "afternoon"
            elif 18 <= current_hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "night"
            
            return FeedContext(
                user_id=user_id,
                user_preferences=user_preferences,
                current_plants=current_plants,
                recent_activity=[],
                seasonal_context=seasonal_context,
                location=user.location,
                time_of_day=time_of_day,
                feed_type=feed_type
            )
            
        except Exception as e:
            logger.error(f"Error building feed context: {str(e)}")
            raise
    
    async def _get_relevant_stories(
        self,
        db: AsyncSession,
        context: FeedContext,
        limit: int
    ) -> List[DiscoveryItem]:
        """Get relevant stories for the user."""
        try:
            stories_stmt = select(Story).options(
                selectinload(Story.author)
            ).where(
                Story.created_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(desc(Story.created_at)).limit(limit * 2)
            
            stories_result = await db.execute(stories_stmt)
            stories = stories_result.scalars().all()
            
            discovery_items = []
            for story in stories:
                relevance_score = self._calculate_story_relevance(story, context)
                
                if relevance_score > 0.3:
                    item = DiscoveryItem(
                        id=str(story.id),
                        content_type=ContentType.STORY,
                        title=f"Story by {story.author.username}",
                        content=story.content[:200] + "..." if len(story.content) > 200 else story.content,
                        author_id=str(story.author.id),
                        author_name=story.author.username,
                        relevance_score=relevance_score,
                        engagement_score=0.7,
                        personalization_factors=["user_plants", "content_preferences"],
                        tags=["story", "community"],
                        plant_species=None,
                        created_at=story.created_at,
                        metadata={"story_type": story.story_type}
                    )
                    discovery_items.append(item)
            
            return discovery_items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting relevant stories: {str(e)}")
            return []
    
    async def _get_relevant_questions(
        self,
        db: AsyncSession,
        context: FeedContext,
        limit: int
    ) -> List[DiscoveryItem]:
        """Get relevant plant questions for the user."""
        try:
            questions_stmt = select(PlantQuestion).options(
                selectinload(PlantQuestion.author),
                selectinload(PlantQuestion.species)
            ).where(
                PlantQuestion.created_at >= datetime.utcnow() - timedelta(days=3)
            ).order_by(desc(PlantQuestion.created_at)).limit(limit * 2)
            
            questions_result = await db.execute(questions_stmt)
            questions = questions_result.scalars().all()
            
            discovery_items = []
            for question in questions:
                relevance_score = self._calculate_question_relevance(question, context)
                
                if relevance_score > 0.4:
                    item = DiscoveryItem(
                        id=str(question.id),
                        content_type=ContentType.QUESTION,
                        title=question.title,
                        content=question.content[:150] + "..." if len(question.content) > 150 else question.content,
                        author_id=str(question.author.id),
                        author_name=question.author.username,
                        relevance_score=relevance_score,
                        engagement_score=0.6,
                        personalization_factors=["plant_expertise", "similar_plants"],
                        tags=["question", "help_needed"],
                        plant_species=question.species.scientific_name if question.species else None,
                        created_at=question.created_at,
                        metadata={"question_type": "plant_care"}
                    )
                    discovery_items.append(item)
            
            return discovery_items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting relevant questions: {str(e)}")
            return []
    
    async def _get_relevant_trades(
        self,
        db: AsyncSession,
        context: FeedContext,
        limit: int
    ) -> List[DiscoveryItem]:
        """Get relevant plant trades for the user."""
        try:
            trades_stmt = select(PlantTrade).options(
                selectinload(PlantTrade.trader)
            ).where(
                PlantTrade.status == "available"
            ).order_by(desc(PlantTrade.created_at)).limit(limit * 2)
            
            trades_result = await db.execute(trades_stmt)
            trades = trades_result.scalars().all()
            
            discovery_items = []
            for trade in trades:
                relevance_score = self._calculate_trade_relevance(trade, context)
                
                if relevance_score > 0.3:
                    item = DiscoveryItem(
                        id=str(trade.id),
                        content_type=ContentType.TRADE,
                        title=f"{trade.plant_name} - {trade.trade_type}",
                        content=trade.description or f"Trading {trade.plant_name}",
                        author_id=str(trade.trader.id),
                        author_name=trade.trader.username,
                        relevance_score=relevance_score,
                        engagement_score=0.5,
                        personalization_factors=["location", "plant_interests"],
                        tags=["trade", "marketplace"],
                        plant_species=trade.plant_name,
                        created_at=trade.created_at,
                        metadata={"trade_type": trade.trade_type}
                    )
                    discovery_items.append(item)
            
            return discovery_items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting relevant trades: {str(e)}")
            return []
    
    async def _get_relevant_knowledge(
        self,
        db: AsyncSession,
        context: FeedContext,
        limit: int
    ) -> List[DiscoveryItem]:
        """Get relevant knowledge base articles."""
        try:
            user_species = [plant["species_id"] for plant in context.current_plants]
            
            if not user_species:
                return []
            
            knowledge_stmt = select(PlantKnowledgeBase).where(
                PlantKnowledgeBase.plant_species_id.in_(user_species)
            ).order_by(desc(PlantKnowledgeBase.helpful_count)).limit(limit)
            
            knowledge_result = await db.execute(knowledge_stmt)
            knowledge_articles = knowledge_result.scalars().all()
            
            discovery_items = []
            for article in knowledge_articles:
                item = DiscoveryItem(
                    id=str(article.id),
                    content_type=ContentType.KNOWLEDGE,
                    title=article.title,
                    content=article.content[:200] + "..." if len(article.content) > 200 else article.content,
                    author_id=None,
                    author_name="Plant Expert",
                    relevance_score=0.8,
                    engagement_score=0.7,
                    personalization_factors=["user_plants", "care_level"],
                    tags=["knowledge", "care_guide"],
                    plant_species=None,
                    created_at=article.created_at,
                    metadata={"content_type": article.content_type, "difficulty": article.difficulty_level}
                )
                discovery_items.append(item)
            
            return discovery_items
            
        except Exception as e:
            logger.error(f"Error getting relevant knowledge: {str(e)}")
            return []
    
    async def _rank_content_items(
        self,
        db: AsyncSession,
        context: FeedContext,
        items: List[DiscoveryItem]
    ) -> List[DiscoveryItem]:
        """Rank content items by relevance and engagement."""
        try:
            for item in items:
                composite_score = (
                    item.relevance_score * 0.6 +
                    item.engagement_score * 0.3 +
                    self._calculate_freshness_score(item) * 0.1
                )
                
                # Apply personalization boosts
                if context.time_of_day == "morning" and "morning" in item.tags:
                    composite_score += 0.1
                
                if context.seasonal_context.get("season") in item.tags:
                    composite_score += 0.1
                
                item.relevance_score = min(1.0, composite_score)
            
            items.sort(key=lambda x: x.relevance_score, reverse=True)
            return items
            
        except Exception as e:
            logger.error(f"Error ranking content items: {str(e)}")
            return items
    
    def _apply_feed_filters(
        self,
        items: List[DiscoveryItem],
        context: FeedContext
    ) -> List[DiscoveryItem]:
        """Apply diversity filters to the feed."""
        filtered_items = []
        content_type_counts = {}
        
        for item in items:
            content_type = item.content_type.value
            current_count = content_type_counts.get(content_type, 0)
            
            max_per_type = 5 if context.feed_type == "home" else 8
            
            if current_count < max_per_type:
                filtered_items.append(item)
                content_type_counts[content_type] = current_count + 1
        
        return filtered_items
    
    def _calculate_story_relevance(self, story: Story, context: FeedContext) -> float:
        """Calculate relevance score for a story."""
        score = 0.5
        
        user_plant_names = [plant["species_name"].lower() for plant in context.current_plants]
        story_content_lower = story.content.lower()
        
        for plant_name in user_plant_names:
            if plant_name in story_content_lower:
                score += 0.3
                break
        
        return min(1.0, score)
    
    def _calculate_question_relevance(self, question: PlantQuestion, context: FeedContext) -> float:
        """Calculate relevance score for a question."""
        score = 0.4
        
        if question.species:
            user_species_ids = [plant["species_id"] for plant in context.current_plants]
            if str(question.species.id) in user_species_ids:
                score += 0.4
        
        return min(1.0, score)
    
    def _calculate_trade_relevance(self, trade: PlantTrade, context: FeedContext) -> float:
        """Calculate relevance score for a trade."""
        score = 0.3
        
        if context.location and trade.trader.location:
            if context.location.lower() in trade.trader.location.lower():
                score += 0.4
        
        return min(1.0, score)
    
    def _calculate_freshness_score(self, item: DiscoveryItem) -> float:
        """Calculate freshness score based on content age."""
        age_hours = (datetime.utcnow() - item.created_at).total_seconds() / 3600
        
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.8
        elif age_hours < 168:
            return 0.6
        else:
            return 0.3
    
    def _get_current_seasonal_context(self, location: Optional[str]) -> Dict[str, Any]:
        """Get current seasonal context."""
        now = datetime.utcnow()
        month = now.month
        
        if 3 <= month <= 5:
            season = "spring"
        elif 6 <= month <= 8:
            season = "summer"
        elif 9 <= month <= 11:
            season = "autumn"
        else:
            season = "winter"
        
        return {"season": season, "month": month, "location": location}
    
    def _analyze_content_preferences(self, interactions: List[RAGInteraction]) -> Dict[str, Any]:
        """Analyze user's content preferences."""
        return {"preferred_types": ["care_tips", "plant_stories"]}
    
    def _analyze_engagement_patterns(self, interactions: List[RAGInteraction]) -> Dict[str, Any]:
        """Analyze user's engagement patterns."""
        return {"peak_hours": [9, 18, 21], "avg_session_length": 15}
    
    def _analyze_topic_interests(self, interactions: List[RAGInteraction]) -> Dict[str, Any]:
        """Analyze user's topic interests."""
        return {"top_topics": ["watering", "plant_health", "propagation"]}
    
    def _analyze_active_times(self, interactions: List[RAGInteraction]) -> Dict[str, Any]:
        """Analyze when user is most active."""
        return {"most_active": "evening", "least_active": "night"}
