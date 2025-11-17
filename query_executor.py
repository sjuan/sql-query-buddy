"""
Query Executor Module
Executes SQL queries and handles database connections.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
from sql_generator import SQLGenerator


class QueryExecutor:
    """Executes SQL queries and returns results."""
    
    def __init__(self, database_url: str, sql_generator: Optional[SQLGenerator] = None):
        """
        Initialize query executor.
        
        Args:
            database_url: SQLAlchemy database URL
            sql_generator: Optional SQLGenerator for optimization
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.sql_generator = sql_generator
    
    def execute_query(
        self,
        sql_query: str,
        return_dataframe: bool = True,
        limit_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: SQL query to execute
            return_dataframe: Whether to return pandas DataFrame
            limit_rows: Maximum number of rows to return
            
        Returns:
            Dictionary with results and metadata
        """
        try:
            # Add safety limit if not present (for SELECT queries)
            if sql_query.strip().upper().startswith("SELECT") and "LIMIT" not in sql_query.upper():
                # Try to add LIMIT safely
                if not sql_query.rstrip().endswith(";"):
                    sql_query = f"{sql_query} LIMIT {limit_rows}"
                else:
                    sql_query = sql_query.rstrip()[:-1] + f" LIMIT {limit_rows};"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                
                if return_dataframe:
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    row_count = len(df)
                    
                    return {
                        "success": True,
                        "data": df,
                        "row_count": row_count,
                        "columns": list(df.columns),
                        "query": sql_query
                    }
                else:
                    rows = result.fetchall()
                    columns = list(result.keys())
                    
                    return {
                        "success": True,
                        "data": rows,
                        "row_count": len(rows),
                        "columns": columns,
                        "query": sql_query
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": sql_query,
                "data": None
            }
    
    def execute_safe_query(
        self,
        sql_query: str,
        return_dataframe: bool = True
    ) -> Dict[str, Any]:
        """
        Execute query with additional safety checks.
        
        Args:
            sql_query: SQL query to execute
            return_dataframe: Whether to return pandas DataFrame
            
        Returns:
            Dictionary with results and metadata
        """
        # Check for dangerous operations
        query_upper = sql_query.upper().strip()
        
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        
        # Allow SELECT queries and safe operations
        if not query_upper.startswith("SELECT"):
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return {
                        "success": False,
                        "error": f"Operation '{keyword}' is not allowed for safety reasons. Only SELECT queries are permitted.",
                        "query": sql_query,
                        "data": None
                    }
        
        return self.execute_query(sql_query, return_dataframe)
    
    def get_optimization_suggestions(self, sql_query: str) -> Dict[str, Any]:
        """
        Get optimization suggestions for a query.
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            Dictionary with optimization suggestions
        """
        if self.sql_generator:
            return self.sql_generator.optimize_query(sql_query)
        else:
            return {
                "original_query": sql_query,
                "suggestions": "SQL generator not available for optimization analysis."
            }
    
    def format_results_for_display(self, results: Dict[str, Any]) -> str:
        """
        Format query results as a readable string.
        
        Args:
            results: Results dictionary from execute_query
            
        Returns:
            Formatted string representation
        """
        if not results.get("success"):
            return f"Error: {results.get('error', 'Unknown error')}"
        
        if results.get("data") is None:
            return "No data returned."
        
        df = results["data"]
        if isinstance(df, pd.DataFrame):
            if len(df) == 0:
                return "Query executed successfully but returned no rows."
            
            # Format as markdown table
            return df.to_markdown(index=False)
        else:
            return str(results["data"])

