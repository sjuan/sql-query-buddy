---
title: SQL Query Buddy
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
---

# SQL Query Buddy 🤖

**Conversational AI for Smart Data Insights** - A RAG-powered system that converts natural language questions into SQL queries, executes them, and provides AI-driven insights.

## 🚀 Hugging Face Spaces

This app is ready to deploy on Hugging Face Spaces! 

### Deployment Steps:

1. **Create a new Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `sql-query-buddy`
   - SDK: Select **Gradio**
   - Hardware: CPU basic (free) or upgrade

2. **Push your code**
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/sql-query-buddy
   git push hf main
   ```

3. **⚠️ IMPORTANT: Set OpenAI API Key**
   - Go to your Space Settings (⚙️ icon)
   - Click **"Variables and secrets"** tab
   - Under **"Repository secrets"**, click **"+ New secret"**
   - Name: `OPENAI_API_KEY` (must be exact, case-sensitive!)
   - Value: Your OpenAI API key (starts with `sk-`)
   - Click **"Save secret"**
   - **Restart your Space** (click restart button)

4. **Verify Setup**
   - Check the **Logs** tab - you should see: `✅ OpenAI API key found: sk-xxxxx...xxxx`
   - If you see an error, check `HF_SPACES_API_KEY_TROUBLESHOOTING.md`

5. **Use the App**
   - The app will automatically create a sample database on first run
   - Vector store will be built automatically
   - Ask questions in natural language!

### 🔑 API Key Troubleshooting

If your API key is not being accepted, see: **`HF_SPACES_API_KEY_TROUBLESHOOTING.md`**

Common issues:
- ❌ Secret name not exact: `OPENAI_API_KEY` (must match exactly)
- ❌ Not in "Repository secrets" section (must be secrets, not variables)
- ❌ Space not restarted after adding secret
- ❌ Extra spaces or quotes in the key value

## 🌟 Features

### Core Capabilities

- **🗣️ Conversational Querying**: Ask complex questions in natural language
  - "Show top 5 customers by total sales"
  - "Now filter them to California only"
  - "What's the total revenue from them this year?"

- **🧠 RAG-Powered SQL Generation**: Uses LangChain + VectorDB to semantically search table schemas before generating SQL, ensuring accuracy across multiple tables

- **⚡ Query Optimization**: Suggests faster JOINs, indexing strategies, and optimized aggregations

- **💡 AI-Driven Insights**: After executing queries, provides contextual insights like:
  - "Sales in California grew 15% month-over-month"
  - "Customer Alice Chen contributed 22% of total Q1 revenue"
  - "Product category Electronics accounts for 40% of total sales"

- **📝 Explainable SQL**: Each query includes beginner-friendly explanations

- **🔄 Context Retention**: Maintains conversation history for smooth follow-up questions

- **💻 Interactive Chat Interface**: Clean Gradio interface displaying queries, results, and insights

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- (Optional) Database connection (SQLite, PostgreSQL, MySQL)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sql-query-buddy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Create sample database** (optional, for testing)
   ```bash
   python setup_sample_database.py
   ```

### Usage

#### Option 1: Jupyter Notebook (Recommended for Testing)

1. Start Jupyter:
   ```bash
   jupyter notebook
   ```

2. Open `test_notebook.ipynb` and run the cells

#### Option 2: Gradio Web Interface

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your browser to `http://localhost:7860`

## 📁 Project Structure

```
sql-query-buddy/
├── app.py                      # Main Gradio application
├── schema_loader.py            # Database schema loading
├── vector_store.py             # Vector database for RAG
├── sql_generator.py            # SQL generation with LangChain
├── query_executor.py           # Query execution
├── insight_generator.py        # AI insight generation
├── context_manager.py          # Conversation context management
├── setup_sample_database.py    # Sample database creation
├── test_notebook.ipynb         # Jupyter testing notebook
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Database (default: SQLite)
DATABASE_URL=sqlite:///sample_database.db

# For PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# For MySQL
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname

# Vector Database
VECTOR_DB_PATH=./vector_store
EMBEDDING_MODEL=text-embedding-3-small

# LLM Settings
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.1
```

## 📊 Sample Database Schema

The included sample database contains:

- **customers**: Customer information (100 records)
- **products**: Product catalog (12 products)
- **orders**: Order records (500 orders)
- **order_items**: Order line items

### Example Queries

```python
# Simple query
question = "Show me the top 5 customers by total sales"

# Context-aware follow-up
question = "Now filter them to California only"

# Complex multi-table query
question = "What's the total revenue from product sales by category this year?"
```

## 🧪 Testing

### Using Jupyter Notebook

1. Open `test_notebook.ipynb`
2. Run cells sequentially
3. Test different query types and observe:
   - SQL generation
   - Query execution
   - Insight generation
   - Context retention

### Example Test Flow

```python
from app import SQLQueryBuddy

# Initialize
buddy = SQLQueryBuddy(
    database_url="sqlite:///sample_database.db",
    vector_db_path="./vector_store"
)

# Ask questions
response = buddy.process_query("Show top 5 customers by sales")
```

## 🏗️ Architecture

### Components

1. **Schema Loader**: Extracts database schema and metadata
2. **Vector Store**: Stores schema information in vector database for semantic search
3. **SQL Generator**: Uses RAG + LangChain to generate SQL from natural language
4. **Query Executor**: Safely executes SQL queries and returns results
5. **Insight Generator**: Analyzes results and provides AI-driven insights
6. **Context Manager**: Maintains conversation history and context

### RAG Flow

1. User asks natural language question
2. Vector store searches for relevant schema information
3. SQL generator uses schema context + conversation history
4. Query executor runs the SQL
5. Insight generator analyzes results
6. Context manager updates conversation history

## 🔒 Security

- Only SELECT queries are allowed by default
- Dangerous operations (DROP, DELETE, etc.) are blocked
- Query results are limited to prevent memory issues
- Database credentials should be stored securely in `.env`

## 🛠️ Customization

### Using Your Own Database

1. Update `DATABASE_URL` in `.env`
2. Run the application - schema will be automatically loaded
3. Vector store will be built on first run

### Adjusting LLM Settings

Modify in `app.py` or when initializing:

```python
buddy = SQLQueryBuddy(
    database_url="...",
    model_name="gpt-3.5-turbo",  # Use different model
    temperature=0.2  # Adjust creativity
)
```

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

## 🙏 Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Vector database powered by [Chroma](https://www.trychroma.com/)
- UI built with [Gradio](https://www.gradio.app/)
- LLM powered by [OpenAI](https://openai.com/)

---

**Happy Querying! 🚀**