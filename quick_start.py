"""
Quick Start Script
Simple example to get started with SQL Query Buddy.
"""

import os
from dotenv import load_dotenv
from app import SQLQueryBuddy

# Load environment variables
load_dotenv()

def main():
    """Quick start example."""
    
    # Configuration
    database_url = os.getenv("DATABASE_URL", "sqlite:///sample_database.db")
    vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_store")
    
    print("🚀 Initializing SQL Query Buddy...")
    print(f"Database: {database_url}")
    print(f"Vector Store: {vector_db_path}\n")
    
    # Initialize
    buddy = SQLQueryBuddy(
        database_url=database_url,
        vector_db_path=vector_db_path
    )
    
    # Example questions
    questions = [
        "Show me the top 5 customers by total sales",
        "What products are in the Electronics category?",
        "How many orders were placed in California?"
    ]
    
    print("=" * 80)
    print("Example Queries:")
    print("=" * 80)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)
        
        # Process query
        history = []
        history, sql, results, insights, explanation = buddy.process_query(question, history)
        
        print(f"\nSQL Query:\n{sql}")
        print(f"\nExplanation:\n{explanation}")
        print(f"\nResults:\n{results[:200]}..." if len(results) > 200 else f"\nResults:\n{results}")
        print(f"\nInsights:\n{insights[:200]}..." if len(insights) > 200 else f"\nInsights:\n{insights}")
        print("\n" + "=" * 80)
    
    print("\n✅ Quick start complete!")
    print("\nTo use the web interface, run: python app.py")
    print("To use in Jupyter, open: test_notebook.ipynb")


if __name__ == "__main__":
    main()

