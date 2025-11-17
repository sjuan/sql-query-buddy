"""
Context Manager Module
Manages conversation context and history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
try:
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
except ImportError:
    # Fallback for older versions
    from langchain.schema import HumanMessage, AIMessage, BaseMessage


class ContextManager:
    """Manages conversation context and history."""
    
    def __init__(self, max_history: int = 20):
        """
        Initialize context manager.
        
        Args:
            max_history: Maximum number of conversation turns to keep
        """
        self.max_history = max_history
        self.conversation_history: List[BaseMessage] = []
        self.query_history: List[Dict[str, Any]] = []
    
    def add_exchange(
        self,
        question: str,
        sql_query: str,
        results: Optional[Dict[str, Any]] = None,
        explanation: Optional[str] = None,
        insights: Optional[str] = None
    ):
        """
        Add a conversation exchange to history.
        
        Args:
            question: User's natural language question
            sql_query: Generated SQL query
            results: Query execution results
            explanation: SQL explanation
            insights: Generated insights
        """
        # Add to LangChain message history
        self.conversation_history.append(HumanMessage(content=question))
        
        # Create response message
        response_parts = []
        if sql_query:
            response_parts.append(f"Generated SQL:\n{sql_query}")
        if explanation:
            response_parts.append(f"Explanation:\n{explanation}")
        if results and results.get("success"):
            response_parts.append(f"Results: {results.get('row_count', 0)} rows returned")
        if insights:
            response_parts.append(f"Insights:\n{insights}")
        
        response = "\n\n".join(response_parts)
        self.conversation_history.append(AIMessage(content=response))
        
        # Add to query history
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "sql_query": sql_query,
            "explanation": explanation,
            "row_count": results.get("row_count", 0) if results else 0,
            "success": results.get("success", False) if results else False,
            "insights": insights
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
        
        if len(self.query_history) > self.max_history:
            self.query_history = self.query_history[-self.max_history:]
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """Get LangChain conversation history."""
        return self.conversation_history
    
    def get_query_history(self) -> List[Dict[str, Any]]:
        """Get detailed query history."""
        return self.query_history
    
    def get_recent_context(self, n: int = 3) -> str:
        """
        Get recent conversation context as formatted string.
        
        Args:
            n: Number of recent exchanges to include
            
        Returns:
            Formatted context string
        """
        recent = self.query_history[-n:] if len(self.query_history) > n else self.query_history
        
        if not recent:
            return "No previous conversation context."
        
        context_lines = ["Recent Conversation Context:"]
        for i, exchange in enumerate(recent, 1):
            context_lines.append(f"\n{i}. Q: {exchange['question']}")
            context_lines.append(f"   SQL: {exchange['sql_query']}")
            if exchange.get('row_count', 0) > 0:
                context_lines.append(f"   Results: {exchange['row_count']} rows")
        
        return "\n".join(context_lines)
    
    def clear_history(self):
        """Clear all conversation history."""
        self.conversation_history = []
        self.query_history = []
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of conversation.
        
        Returns:
            Dictionary with conversation summary
        """
        total_queries = len(self.query_history)
        successful_queries = sum(1 for q in self.query_history if q.get("success", False))
        total_rows = sum(q.get("row_count", 0) for q in self.query_history)
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "total_rows_returned": total_rows,
            "conversation_turns": len(self.conversation_history) // 2
        }

