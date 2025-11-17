"""
Schema Loader Module
Loads and processes database schema information for RAG-based SQL generation.
"""

from typing import List, Dict, Any
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.engine import Engine
import json


class SchemaLoader:
    """Loads database schema and converts it to text format for vector storage."""
    
    def __init__(self, database_url: str):
        """
        Initialize schema loader with database connection.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.inspector = inspect(self.engine)
    
    def get_all_tables(self) -> List[str]:
        """Get list of all table names in the database."""
        return self.inspector.get_table_names()
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing schema information
        """
        columns = self.inspector.get_columns(table_name)
        
        # SQLAlchemy 2.0+ uses get_pk_constraint() instead of get_primary_keys()
        try:
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get('constrained_columns', []) if pk_constraint else []
        except AttributeError:
            # Fallback for older SQLAlchemy versions
            try:
                primary_keys = self.inspector.get_primary_keys(table_name)
            except AttributeError:
                primary_keys = []
        
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        indexes = self.inspector.get_indexes(table_name)
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'indexes': indexes
        }
    
    def schema_to_text(self, schema: Dict[str, Any]) -> str:
        """
        Convert schema dictionary to human-readable text format.
        
        Args:
            schema: Schema dictionary from get_table_schema
            
        Returns:
            Formatted text string describing the schema
        """
        table_name = schema['table_name']
        lines = [f"Table: {table_name}", "=" * 50]
        
        # Columns
        lines.append("\nColumns:")
        for col in schema['columns']:
            col_info = f"  - {col['name']}: {col['type']}"
            if col.get('nullable') is False:
                col_info += " (NOT NULL)"
            if col.get('default') is not None:
                col_info += f" DEFAULT {col['default']}"
            lines.append(col_info)
        
        # Primary Keys
        if schema['primary_keys']:
            lines.append(f"\nPrimary Keys: {', '.join(schema['primary_keys'])}")
        
        # Foreign Keys
        if schema['foreign_keys']:
            lines.append("\nForeign Keys:")
            for fk in schema['foreign_keys']:
                # Handle both SQLAlchemy 1.x and 2.x formats
                constrained_cols = fk.get('constrained_columns', [])
                if isinstance(constrained_cols, list):
                    constrained_cols = ', '.join(constrained_cols) if constrained_cols else 'N/A'
                referred_cols = fk.get('referred_columns', [])
                if isinstance(referred_cols, list):
                    referred_cols = ', '.join(referred_cols) if referred_cols else 'N/A'
                fk_str = f"  - {constrained_cols} -> {fk.get('referred_table', 'N/A')}.{referred_cols}"
                lines.append(fk_str)
        
        # Indexes
        if schema['indexes']:
            lines.append("\nIndexes:")
            for idx in schema['indexes']:
                idx_str = f"  - {idx['name']}: {idx['column_names']}"
                if idx.get('unique'):
                    idx_str += " (UNIQUE)"
                lines.append(idx_str)
        
        return "\n".join(lines)
    
    def get_all_schemas_text(self) -> List[str]:
        """
        Get text representation of all table schemas.
        
        Returns:
            List of schema text strings
        """
        tables = self.get_all_tables()
        schemas = []
        
        for table in tables:
            schema_dict = self.get_table_schema(table)
            schema_text = self.schema_to_text(schema_dict)
            schemas.append(schema_text)
        
        return schemas
    
    def get_relationships_text(self) -> str:
        """
        Get text description of table relationships.
        
        Returns:
            Text describing relationships between tables
        """
        tables = self.get_all_tables()
        relationships = []
        
        for table in tables:
            schema = self.get_table_schema(table)
            if schema['foreign_keys']:
                for fk in schema['foreign_keys']:
                    # Handle both SQLAlchemy 1.x and 2.x formats
                    constrained_cols = fk.get('constrained_columns', [])
                    if isinstance(constrained_cols, list):
                        constrained_cols = ', '.join(constrained_cols) if constrained_cols else 'N/A'
                    referred_cols = fk.get('referred_columns', [])
                    if isinstance(referred_cols, list):
                        referred_cols = ', '.join(referred_cols) if referred_cols else 'N/A'
                    rel = (
                        f"{table}.{constrained_cols} "
                        f"references {fk.get('referred_table', 'N/A')}.{referred_cols}"
                    )
                    relationships.append(rel)
        
        if relationships:
            return "Table Relationships:\n" + "\n".join(f"  - {rel}" for rel in relationships)
        return "No foreign key relationships found."
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> str:
        """
        Get sample data from a table for context.
        
        Args:
            table_name: Name of the table
            limit: Number of sample rows to retrieve
            
        Returns:
            Text representation of sample data
        """
        try:
            with self.engine.connect() as conn:
                # Use SQLAlchemy 2.0 text() for raw SQL
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = conn.execute(query)
                rows = result.fetchall()
                columns = result.keys()
                
                if not rows:
                    return f"No data found in {table_name}"
                
                lines = [f"Sample data from {table_name}:"]
                lines.append(" | ".join(str(col) for col in columns))
                lines.append("-" * 80)
                
                for row in rows:
                    lines.append(" | ".join(str(val) if val is not None else "NULL" for val in row))
                
                return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving sample data: {str(e)}"

