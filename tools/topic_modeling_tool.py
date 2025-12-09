import logging
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

logger = logging.getLogger(__name__)

class TopicModelingTool(BaseTool):
    """
    A tool for performing topic modeling on a collection of documents using Latent Dirichlet Allocation (LDA).
    """
    def __init__(self, tool_name: str = "topic_modeling_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Identifies topics from a list of documents using Latent Dirichlet Allocation (LDA)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of documents (strings) to analyze."
                },
                "num_topics": {
                    "type": "integer",
                    "description": "The number of topics to identify.",
                    "default": 5
                },
                "num_words_per_topic": {
                    "type": "integer",
                    "description": "The number of top words to display for each topic.",
                    "default": 10
                }
            },
            "required": ["documents"]
        }

    def execute(self, documents: List[str], num_topics: int = 5, num_words_per_topic: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Performs LDA topic modeling on a list of documents.
        """
        if not documents or not isinstance(documents, list) or not all(isinstance(doc, str) for doc in documents):
            return {"error": "'documents' must be a non-empty list of strings."}
        
        if len(documents) < num_topics:
            return {"error": "The number of documents must be greater than or equal to the number of topics."}

        try:
            # Vectorize the text data
            vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
            dtm = vectorizer.fit_transform(documents)
            
            # Fit the LDA model
            lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
            lda.fit(dtm)
            
            # Get the topics and their top words
            feature_names = vectorizer.get_feature_names_out()
            topics = {}
            for topic_idx, topic in enumerate(lda.components_):
                top_words_indices = topic.argsort()[:-num_words_per_topic - 1:-1]
                top_words = [feature_names[i] for i in top_words_indices]
                topics[f"Topic {topic_idx + 1}"] = top_words
            
            return {"topics": topics}

        except ValueError as e:
            # Catch errors from CountVectorizer (e.g., empty vocabulary)
            logger.error(f"A ValueError occurred during topic modeling: {e}")
            return {"error": f"Could not process documents. Ensure they contain enough meaningful content. Details: {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during topic modeling: {e}")
            return {"error": f"An unexpected error occurred: {e}"}