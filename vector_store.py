"""
Vector Store Module
Manages vector database for RAG-based schema retrieval.
"""

import os
from typing import List, Optional
try:
    # Try new langchain-chroma package first
    from langchain_chroma import Chroma
except ImportError:
    try:
        # Fallback to langchain_community
        from langchain_community.vectorstores import Chroma
    except ImportError:
        # Last resort fallback
        from langchain.vectorstores import Chroma

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain.embeddings import OpenAIEmbeddings

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document
from schema_loader import SchemaLoader


class VectorStoreManager:
    """Manages vector database for schema information retrieval."""
    
    def __init__(
        self,
        database_url: str,
        api_key: str,
        vector_db_path: str = "./vector_store",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize vector store manager.
        
        Args:
            database_url: SQLAlchemy database URL
            api_key: OpenAI API key (stored only in memory, not persisted)
            vector_db_path: Path to store vector database
            embedding_model: OpenAI embedding model name
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key is required")
        
        self.database_url = database_url
        self.vector_db_path = vector_db_path
        self.embedding_model = embedding_model
        self.api_key = api_key.strip()  # Store in instance, not environment
        
        # Try new parameter name first, fallback to old
        try:
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                openai_api_key=self.api_key  # Pass key directly, not via environment
            )
        except TypeError:
            self.embeddings = OpenAIEmbeddings(
                model_name=embedding_model,
                openai_api_key=self.api_key  # Pass key directly, not via environment
            )
        self.schema_loader = SchemaLoader(database_url)
        self.vectorstore: Optional[Chroma] = None
        
        # Create directory if it doesn't exist
        os.makedirs(vector_db_path, exist_ok=True)
    
    def build_vector_store(self, include_samples: bool = True):
        """
        Build vector store from database schema.
        
        Args:
            include_samples: Whether to include sample data in the store
        """
        print("Loading database schema...")
        schemas_text = self.schema_loader.get_all_schemas_text()
        relationships_text = self.schema_loader.get_relationships_text()
        
        # Create documents
        documents = []
        
        # Add schema documents
        for schema_text in schemas_text:
            documents.append(Document(page_content=schema_text))
        
        # Add relationships document
        documents.append(Document(page_content=relationships_text))
        
        # Add sample data if requested
        if include_samples:
            print("Loading sample data...")
            tables = self.schema_loader.get_all_tables()
            for table in tables:
                sample_data = self.schema_loader.get_sample_data(table, limit=3)
                documents.append(Document(
                    page_content=f"Sample Data:\n{sample_data}",
                    metadata={"type": "sample_data", "table": table}
                ))
        
        # Split documents if needed (for very large schemas)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        split_documents = text_splitter.split_documents(documents)
        
        print(f"Creating vector store with {len(split_documents)} documents...")
        
        # Create or load vector store
        if os.path.exists(self.vector_db_path) and os.listdir(self.vector_db_path):
            # Load existing
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            print("Loaded existing vector store.")
        else:
            # Create new
            self.vectorstore = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                persist_directory=self.vector_db_path
            )
            print("Created new vector store.")
    
    def search_relevant_schemas(self, query: str, k: int = 5) -> List[str]:
        """
        Search for relevant schema information based on query.
        
        Args:
            query: Natural language query
            k: Number of results to return
            
        Returns:
            List of relevant schema text chunks
        """
        if self.vectorstore is None:
            self.build_vector_store()
        
        results = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    
    def get_relevant_context(self, query: str, k: int = 5) -> str:
        """
        Get formatted context string from relevant schemas.
        
        Args:
            query: Natural language query
            k: Number of results to return
            
        Returns:
            Formatted context string
        """
        relevant_schemas = self.search_relevant_schemas(query, k)
        context = "\n\n---\n\n".join(relevant_schemas)
        return f"Relevant Database Schema Information:\n\n{context}"

