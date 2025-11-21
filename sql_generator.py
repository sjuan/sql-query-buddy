"""
SQL Generator Module
Uses LangChain and RAG to generate SQL queries from natural language.
"""

from typing import Optional, Dict, Any, List
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError:
    # Fallback for older versions
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    try:
        from langchain.schema import HumanMessage, AIMessage, SystemMessage
    except ImportError:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from vector_store import VectorStoreManager


class SQLGenerator:
    """Generates SQL queries from natural language using RAG and LangChain."""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        api_key: str,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.1
    ):
        """
        Initialize SQL generator.
        
        Args:
            vector_store_manager: VectorStoreManager instance
            api_key: OpenAI API key (stored only in memory, not persisted)
            model_name: OpenAI model name
            temperature: LLM temperature
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key is required")
        
        self.vector_store = vector_store_manager
        self.api_key = api_key.strip()  # Store in instance, not environment
        
        # Try new parameter name first, fallback to old
        try:
            self.llm = ChatOpenAI(
                model=model_name, 
                temperature=temperature,
                openai_api_key=self.api_key  # Pass key directly, not via environment
            )
        except TypeError:
            self.llm = ChatOpenAI(
                model_name=model_name, 
                temperature=temperature,
                openai_api_key=self.api_key  # Pass key directly, not via environment
            )
        
        # Store system prompt for SQL generation
        self.sql_system_prompt = """You are an expert SQL query generator. Your task is to convert natural language questions into accurate, optimized SQL queries.

Guidelines:
1. Use the provided database schema information to understand table structures, columns, and relationships
2. Generate SQL that is syntactically correct and follows best practices
3. Use appropriate JOINs when querying multiple tables
4. Apply proper WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when needed
6. Include ORDER BY and LIMIT clauses when appropriate
7. Always use table aliases for clarity
8. Ensure column names match exactly with the schema

Generate ONLY the SQL query, without any explanation or markdown formatting. Just the raw SQL."""
        
        # Store system prompt for explanation
        self.explanation_system_prompt = """You are a SQL educator. Explain SQL queries in simple, beginner-friendly terms.

Explain the following SQL query in plain English, focusing on:
- What tables are being queried
- What columns are selected
- What filters or conditions are applied
- What aggregations or calculations are performed
- What sorting or limiting is done

Keep the explanation clear and accessible to non-technical users."""
    
    def generate_sql(
        self,
        question: str,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: Natural language question
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with SQL query and metadata
        """
        # Get relevant schema context using RAG
        schema_context = self.vector_store.get_relevant_context(question, k=5)
        
        # Build messages for the LLM
        messages = []
        
        # Add system message with schema context
        system_content = f"{self.sql_system_prompt}\n\nDatabase Schema Context:\n{schema_context}"
        if conversation_history:
            # Format conversation history as text
            history_text = "\n".join([
                f"Q: {msg.content}" if hasattr(msg, 'content') and isinstance(msg, HumanMessage) 
                else f"A: {msg.content}" if hasattr(msg, 'content') and isinstance(msg, AIMessage)
                else str(msg)
                for msg in conversation_history[-6:]  # Last 3 exchanges (6 messages)
            ])
            system_content += f"\n\nPrevious conversation context:\n{history_text}"
        
        messages.append(SystemMessage(content=system_content))
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 exchanges
        
        # Add current question
        messages.append(HumanMessage(content=question))
        
        # Get SQL from LLM
        response = self.llm.invoke(messages)
        sql_query = response.content.strip()
        
        # Clean up SQL (remove markdown code blocks if present)
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Generate explanation
        explanation = self.generate_explanation(sql_query)
        
        return {
            "sql": sql_query,
            "explanation": explanation,
            "schema_context": schema_context
        }
    
    def generate_explanation(self, sql_query: str) -> str:
        """
        Generate beginner-friendly explanation of SQL query.
        
        Args:
            sql_query: SQL query to explain
            
        Returns:
            Plain English explanation
        """
        messages = [
            SystemMessage(content=self.explanation_system_prompt),
            HumanMessage(content=f"Explain this SQL query in simple terms:\n\n{sql_query}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content.strip()
    
    def optimize_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Suggest optimizations for a SQL query.
        
        Args:
            sql_query: SQL query to optimize
            
        Returns:
            Dictionary with optimized query and suggestions
        """
        optimization_system_prompt = """You are a SQL performance expert. Analyze SQL queries and suggest optimizations.

Consider:
1. Missing indexes on WHERE/JOIN columns
2. Unnecessary columns in SELECT
3. Inefficient JOINs
4. Missing WHERE clause filters
5. Suboptimal aggregations
6. Missing LIMIT clauses on large result sets

Provide specific, actionable suggestions."""
        
        messages = [
            SystemMessage(content=optimization_system_prompt),
            HumanMessage(content=f"Analyze and suggest optimizations for this SQL query:\n\n{sql_query}")
        ]
        
        response = self.llm.invoke(messages)
        suggestions = response.content.strip()
        
        return {
            "original_query": sql_query,
            "suggestions": suggestions
        }

