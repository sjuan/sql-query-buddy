"""
Insight Generator Module
Generates AI-driven insights from query results.
"""

from typing import Dict, Any, Optional
import os
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    # Fallback for older versions
    try:
        from langchain.schema import HumanMessage, SystemMessage
    except ImportError:
        from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd


class InsightGenerator:
    """Generates contextual insights from SQL query results."""
    
    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.3
    ):
        """
        Initialize insight generator.
        
        Args:
            model_name: OpenAI model name
            temperature: LLM temperature (higher for more creative insights)
        """
        # Verify and get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found! Please set it in Space secrets.")
        api_key = api_key.strip()
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Try new parameter name first, fallback to old
        try:
            self.llm = ChatOpenAI(
                model=model_name, 
                temperature=temperature,
                openai_api_key=api_key  # Explicitly pass the key
            )
        except TypeError:
            self.llm = ChatOpenAI(
                model_name=model_name, 
                temperature=temperature,
                openai_api_key=api_key  # Explicitly pass the key
            )
        
        # Store system prompt for insights
        self.insight_system_prompt = """You are a data analyst AI that provides insightful interpretations of query results.

Your task is to analyze the SQL query and its results, then provide:
1. Key findings and patterns
2. Notable statistics (percentages, growth rates, comparisons)
3. Anomalies or outliers
4. Business implications
5. Actionable insights

Be specific, use numbers from the data, and make the insights actionable and decision-supportive.
Keep insights concise but meaningful (2-4 bullet points)."""
    
    def generate_insights(
        self,
        query: str,
        results: Dict[str, Any],
        original_question: str,
        max_rows_for_analysis: int = 20
    ) -> str:
        """
        Generate insights from query results.
        
        Args:
            query: SQL query that was executed
            results: Results dictionary from QueryExecutor
            original_question: Original natural language question
            max_rows_for_analysis: Maximum rows to include in analysis
            
        Returns:
            Formatted insights string
        """
        if not results.get("success") or results.get("data") is None:
            return "Unable to generate insights: Query execution failed or returned no data."
        
        df = results["data"]
        
        if not isinstance(df, pd.DataFrame):
            # Convert to DataFrame if needed
            try:
                df = pd.DataFrame(df)
            except:
                return "Unable to generate insights: Data format not supported."
        
        if len(df) == 0:
            return "No insights available: Query returned no rows."
        
        # Prepare results summary
        results_summary = self._prepare_results_summary(df, max_rows_for_analysis)
        
        # Build the prompt for insights
        human_content = f"""SQL Query:
{query}

Query Results (first 20 rows):
{results_summary}

Original Question:
{original_question}

Provide insightful analysis of these results."""
        
        # Generate insights using direct LLM invocation
        try:
            messages = [
                SystemMessage(content=self.insight_system_prompt),
                HumanMessage(content=human_content)
            ]
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    def _prepare_results_summary(self, df: pd.DataFrame, max_rows: int = 20) -> str:
        """
        Prepare a text summary of results for LLM analysis.
        
        Args:
            df: DataFrame with results
            max_rows: Maximum rows to include
            
        Returns:
            Formatted string summary
        """
        # Get basic statistics
        summary_lines = []
        
        # Data shape
        summary_lines.append(f"Total rows: {len(df)}")
        summary_lines.append(f"Total columns: {len(df.columns)}")
        summary_lines.append("\nColumn names: " + ", ".join(df.columns.tolist()))
        
        # Sample data
        sample_df = df.head(max_rows)
        summary_lines.append(f"\nSample data (first {len(sample_df)} rows):")
        summary_lines.append(sample_df.to_string(index=False))
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_lines.append("\nNumeric column statistics:")
            for col in numeric_cols:
                summary_lines.append(
                    f"  {col}: min={df[col].min()}, max={df[col].max()}, "
                    f"mean={df[col].mean():.2f}, sum={df[col].sum():.2f}"
                )
        
        return "\n".join(summary_lines)
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> str:
        """
        Generate summary statistics for a DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Formatted statistics string
        """
        if len(df) == 0:
            return "No data to summarize."
        
        stats_lines = []
        stats_lines.append("Summary Statistics:")
        stats_lines.append("=" * 50)
        
        # Basic info
        stats_lines.append(f"Total Records: {len(df)}")
        stats_lines.append(f"Total Columns: {len(df.columns)}")
        
        # Numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats_lines.append("\nNumeric Columns:")
            for col in numeric_cols:
                stats_lines.append(f"  {col}:")
                stats_lines.append(f"    Sum: {df[col].sum():,.2f}")
                stats_lines.append(f"    Average: {df[col].mean():,.2f}")
                stats_lines.append(f"    Min: {df[col].min():,.2f}")
                stats_lines.append(f"    Max: {df[col].max():,.2f}")
        
        return "\n".join(stats_lines)

