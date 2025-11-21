"""
Main Application
Gradio interface for SQL Query Buddy.
"""

import os
import gradio as gr
from dotenv import load_dotenv
from vector_store import VectorStoreManager
from sql_generator import SQLGenerator
from query_executor import QueryExecutor
from insight_generator import InsightGenerator
from context_manager import ContextManager

# Load environment variables
load_dotenv()

# Verify OpenAI API key is set
def verify_openai_api_key():
    """Verify that OpenAI API key is properly configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        error_msg = """
        ❌ ERROR: OPENAI_API_KEY not found!
        
        For Hugging Face Spaces:
        1. Go to your Space Settings
        2. Click "Variables and secrets"
        3. Add a new secret:
           - Name: OPENAI_API_KEY
           - Value: your OpenAI API key (starts with 'sk-')
        4. Restart your Space
        
        For local development:
        - Create a .env file with: OPENAI_API_KEY=your_key_here
        - Or set environment variable: export OPENAI_API_KEY=your_key_here
        
        Get your API key from: https://platform.openai.com/api-keys
        """
        raise ValueError(error_msg)
    
    # Clean the API key (remove whitespace)
    api_key = api_key.strip()
    
    # Check format
    if not api_key.startswith("sk-"):
        error_msg = f"""
        ❌ ERROR: Invalid API key format!
        
        API key must start with 'sk-'
        Got: {api_key[:20]}...
        
        Common issues:
        - Extra spaces before/after the key
        - Quotes around the key (remove them)
        - Wrong key copied
        
        In Hugging Face Spaces:
        - Make sure there are NO spaces before or after the key value
        - Do NOT include quotes around the key
        - The full key should be about 51 characters long
        """
        raise ValueError(error_msg)
    
    # Check length (OpenAI keys are typically 51 characters)
    if len(api_key) < 40:
        error_msg = f"""
        ❌ ERROR: API key appears to be incomplete!
        
        API key length: {len(api_key)} characters
        Expected: ~51 characters
        
        The key might be truncated. Make sure you copied the FULL key.
        """
        raise ValueError(error_msg)
    
    # Set the cleaned key back to environment
    os.environ["OPENAI_API_KEY"] = api_key
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
    return api_key


class SQLQueryBuddy:
    """Main application class for SQL Query Buddy."""
    
    def __init__(
        self,
        database_url: str,
        api_key: str,
        vector_db_path: str = "./vector_store",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.1
    ):
        """
        Initialize SQL Query Buddy.
        
        Args:
            database_url: SQLAlchemy database URL
            api_key: OpenAI API key (stored only in memory, not persisted)
            vector_db_path: Path to vector database
            model_name: OpenAI model name
            temperature: LLM temperature
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key is required")
        
        self.database_url = database_url
        self.api_key = api_key.strip()  # Store in instance only, NOT in environment
        
        # SECURITY: API key is passed directly to components as parameters
        # Components are updated to accept api_key parameter and use it directly
        # This ensures the key is never persisted in environment variables
        
        self.vector_store_manager = VectorStoreManager(
            database_url=database_url,
            api_key=self.api_key,  # Pass directly, not via environment
            vector_db_path=vector_db_path
        )
        self.sql_generator = SQLGenerator(
            vector_store_manager=self.vector_store_manager,
            api_key=self.api_key,  # Pass directly, not via environment
            model_name=model_name,
            temperature=temperature
        )
        self.query_executor = QueryExecutor(
            database_url=database_url,
            sql_generator=self.sql_generator
        )
        self.insight_generator = InsightGenerator(
            api_key=self.api_key,  # Pass directly, not via environment
            model_name=model_name,
            temperature=0.3
        )
        self.context_manager = ContextManager(max_history=20)
        
        # Ensure vector store directory exists
        if vector_db_path:
            os.makedirs(vector_db_path, exist_ok=True)
        
        # Build vector store on initialization
        # Wrap in try-except to provide better error messages
        try:
            print("Initializing vector store...")
            self.vector_store_manager.build_vector_store(include_samples=True)
            print("Vector store ready!")
        except Exception as e:
            error_msg = f"Error building vector store: {str(e)}"
            print(f"⚠️ Warning: {error_msg}")
            # Don't fail initialization - vector store can be built lazily
            # But log the error for debugging
            raise ValueError(f"Failed to initialize vector store. This may be due to database connection issues or insufficient permissions. Error: {str(e)}")
    
    def process_query(self, question: str, history: list) -> tuple:
        """
        Process a user question and return response.
        
        Args:
            question: User's natural language question
            history: Chat history (Gradio format)
            
        Returns:
            Tuple of (updated history, SQL query, results, insights, explanation)
        """
        if not question.strip():
            return history, "", "", "", ""
        
        try:
            # Get conversation history for context
            conversation_history = self.context_manager.get_conversation_history()
            
            # Generate SQL
            print(f"Generating SQL for: {question}")
            sql_result = self.sql_generator.generate_sql(
                question=question,
                conversation_history=conversation_history
            )
            
            sql_query = sql_result["sql"]
            explanation = sql_result["explanation"]
            
            # Execute query
            print("Executing SQL query...")
            results = self.query_executor.execute_safe_query(sql_query, return_dataframe=True)
            
            # Format results
            if results.get("success"):
                results_text = self.query_executor.format_results_for_display(results)
                row_count = results.get("row_count", 0)
                results_summary = f"✅ Query executed successfully!\n\nRows returned: {row_count}\n\n{results_text}"
            else:
                results_text = f"❌ Error: {results.get('error', 'Unknown error')}"
                results_summary = results_text
                results["data"] = None
            
            # Generate insights
            insights = ""
            if results.get("success") and results.get("data") is not None:
                print("Generating insights...")
                insights = self.insight_generator.generate_insights(
                    query=sql_query,
                    results=results,
                    original_question=question
                )
            
            # Update conversation history
            self.context_manager.add_exchange(
                question=question,
                sql_query=sql_query,
                results=results,
                explanation=explanation,
                insights=insights
            )
            
            # Update Gradio chat history (new messages format)
            history.append({"role": "user", "content": question})
            history.append({
                "role": "assistant", 
                "content": f"**SQL Query:**\n```sql\n{sql_query}\n```\n\n**Explanation:**\n{explanation}\n\n**Results:**\n{results_summary}\n\n**Insights:**\n{insights}"
            })
            
            return history, sql_query, results_summary, insights, explanation
        
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": f"❌ {error_msg}"})
            return history, "", error_msg, "", ""
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.context_manager.clear_history()
        return gr.update(value=[]), "", "", "", ""
    
    def get_optimization_suggestions(self, sql_query: str) -> str:
        """
        Get optimization suggestions for a SQL query.
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            Optimization suggestions
        """
        if not sql_query.strip():
            return "Please provide a SQL query to analyze."
        
        try:
            result = self.sql_generator.optimize_query(sql_query)
            return result.get("suggestions", "No suggestions available.")
        except Exception as e:
            return f"Error generating suggestions: {str(e)}"


def create_interface(database_url: str, vector_db_path: str = "./vector_store"):
    """Create and launch Gradio interface."""
    
    # For public deployment, always require user to enter API key
    # Don't auto-initialize from environment - let users enter their own key
    initial_buddy = None
    initial_api_key = ""
    
    # Store for session (will be initialized when API key is provided)
    buddy_state = gr.State(value=initial_buddy)
    api_key_state = gr.State(value=initial_api_key)
    
    # Create Gradio interface with dark mode support
    with gr.Blocks(title="SQL Query Buddy", theme=gr.themes.Soft()) as demo:
        # Add custom CSS for dark mode and improved contrast
        demo.css = """
        /* Light mode - improved contrast for text areas */
        .chatbot {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }
        .chatbot .message {
            background-color: #f8f9fa !important;
            color: #212529 !important;
            padding: 12px !important;
            margin: 8px 0 !important;
            border-radius: 8px !important;
        }
        .chatbot .user-message {
            background-color: #e3f2fd !important;
            color: #1565c0 !important;
        }
        .chatbot .assistant-message {
            background-color: #f5f5f5 !important;
            color: #1a1a1a !important;
        }
        textarea, input[type="text"] {
            background-color: #ffffff !important;
            color: #212529 !important;
            border: 1px solid #ced4da !important;
        }
        .output-text, .textbox {
            background-color: #ffffff !important;
            color: #212529 !important;
        }
        
        /* Dark mode - high contrast */
        .dark-mode-active {
            --background-fill-primary: #0d1117 !important;
            --background-fill-secondary: #161b22 !important;
            --body-text-color: #f0f6fc !important;
            --body-text-color-subdued: #c9d1d9 !important;
            --border-color-primary: #30363d !important;
            --input-background-fill: #0d1117 !important;
            --input-border-color: #30363d !important;
            --input-text-color: #f0f6fc !important;
            --panel-background-fill: #161b22 !important;
            --block-background-fill: #0d1117 !important;
            --block-label-text-color: #f0f6fc !important;
            --block-title-text-color: #f0f6fc !important;
        }
        .dark-mode-active .gradio-container {
            background: #0d1117 !important;
            color: #f0f6fc !important;
        }
        .dark-mode-active .markdown {
            color: #f0f6fc !important;
        }
        .dark-mode-active .markdown h1,
        .dark-mode-active .markdown h2,
        .dark-mode-active .markdown h3 {
            color: #f0f6fc !important;
        }
        .dark-mode-active textarea,
        .dark-mode-active input[type="text"] {
            background-color: #161b22 !important;
            color: #f0f6fc !important;
            border-color: #30363d !important;
        }
        .dark-mode-active .chatbot {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
        }
        .dark-mode-active .chatbot .message {
            background-color: #21262d !important;
            color: #f0f6fc !important;
            padding: 12px !important;
            margin: 8px 0 !important;
            border-radius: 8px !important;
        }
        .dark-mode-active .chatbot .user-message {
            background-color: #1f6feb !important;
            color: #ffffff !important;
        }
        .dark-mode-active .chatbot .assistant-message {
            background-color: #21262d !important;
            color: #f0f6fc !important;
            border: 1px solid #30363d !important;
        }
        .dark-mode-active .output-text,
        .dark-mode-active .textbox {
            background-color: #161b22 !important;
            color: #f0f6fc !important;
            border: 1px solid #30363d !important;
        }
        .dark-mode-active .code {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
            border: 1px solid #30363d !important;
        }
        /* Ensure all text has good contrast */
        .dark-mode-active p, .dark-mode-active div, .dark-mode-active span {
            color: #f0f6fc !important;
        }
        """
        
        # API Key Input Section (always visible initially)
        with gr.Row():
            with gr.Column():
                api_key_input = gr.Textbox(
                    label="🔑 OpenAI API Key",
                    placeholder="Enter your OpenAI API key (starts with sk-)",
                    type="password",
                    visible=True,  # Always visible initially
                    info="🔒 **Security**: Your API key is stored only in this session's memory and will be cleared when you close the app. Get your key from https://platform.openai.com/api-keys"
                )
                with gr.Row():
                    api_key_submit = gr.Button("Set API Key", variant="primary", visible=True)  # Always visible initially
                    api_key_clear = gr.Button("Clear API Key", variant="stop", visible=False)  # Hidden initially
                api_key_status = gr.Markdown(
                    value="⚠️ **API Key Required**: Please enter your OpenAI API key to use this app. Your key will NOT be saved or persisted.",
                    visible=True
                )
        
        # Header with title and dark mode toggle
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown("""
                # 🤖 SQL Query Buddy
                ### Conversational AI for Smart Data Insights
                
                Ask questions in natural language and get SQL queries, results, and AI-driven insights!
                
                **Features:**
                - 🗣️ Natural language to SQL conversion
                - 📊 Query execution and results
                - 💡 AI-powered insights
                - 📝 Beginner-friendly explanations
                - 🔄 Context-aware conversations
                """)
            with gr.Column(scale=1, min_width=150):
                dark_mode_toggle = gr.Checkbox(
                    label="🌙 Dark Mode",
                    value=False,
                    elem_classes="dark-mode-toggle"
                )
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_copy_button=True,
                    type="messages"
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="e.g., Show me the top 5 customers by total sales",
                        scale=4
                    )
                    submit_btn = gr.Button("Submit", variant="primary", scale=1)
                    clear_btn = gr.Button("Clear", scale=1)
            
            with gr.Column(scale=1):
                gr.Markdown("### Query Details")
                
                sql_output = gr.Code(
                    label="Generated SQL",
                    language="sql",
                    lines=10
                )
                
                explanation_output = gr.Textbox(
                    label="Explanation",
                    lines=5,
                    interactive=False
                )
                
                insights_output = gr.Textbox(
                    label="AI Insights",
                    lines=10,
                    interactive=False
                )
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Query Optimization")
                optimization_input = gr.Textbox(
                    label="SQL Query to Optimize",
                    placeholder="Paste SQL query here",
                    lines=5
                )
                optimize_btn = gr.Button("Get Optimization Suggestions")
                optimization_output = gr.Textbox(
                    label="Suggestions",
                    lines=10,
                    interactive=False
                )
        
        # Function to initialize app with API key
        def initialize_app(api_key: str, current_buddy):
            """Initialize SQLQueryBuddy with provided API key."""
            if current_buddy is not None:
                return (current_buddy, api_key, gr.update(visible=False), gr.update(visible=False), 
                       "✅ API key already set!", gr.update(visible=False), gr.update(visible=True))
            
            if not api_key or not api_key.strip():
                return (None, "", gr.update(visible=True), gr.update(visible=True), 
                       "❌ Please enter a valid API key.", gr.update(visible=True), gr.update(visible=False))
            
            api_key = api_key.strip()
            
            # Validate key format
            if not api_key.startswith("sk-"):
                return (None, "", gr.update(visible=True), gr.update(visible=True), 
                       "❌ Invalid API key format. Must start with 'sk-'", gr.update(visible=True), gr.update(visible=False))
            
            if len(api_key) < 40:
                return (None, "", gr.update(visible=True), gr.update(visible=True), 
                       "❌ API key appears incomplete. Please check and try again.", gr.update(visible=True), gr.update(visible=False))
            
            try:
                # Ensure database exists before initialization
                if database_url.startswith("sqlite:///"):
                    db_path = database_url.replace("sqlite:///", "")
                    if not os.path.exists(db_path):
                        try:
                            from setup_sample_database import create_sample_database
                            create_sample_database(db_path)
                        except Exception as db_error:
                            error_msg = f"❌ Error creating database: {str(db_error)}\n\nPlease check the logs for details."
                            return (None, "", gr.update(visible=True), gr.update(visible=True), error_msg,
                                   gr.update(visible=True), gr.update(visible=False))
                
                # Initialize SQLQueryBuddy with API key as parameter
                # Key is stored only in memory (session state), not persisted
                new_buddy = SQLQueryBuddy(
                    database_url=database_url,
                    api_key=api_key,  # Pass directly, not via environment
                    vector_db_path=vector_db_path
                )
                
                return (new_buddy, api_key, gr.update(visible=False), gr.update(visible=False), 
                       "✅ API key set! App initialized successfully. **Note:** Your API key is stored only in this session and will be cleared when you close the app.",
                       gr.update(visible=False), gr.update(visible=True))
            except ValueError as ve:
                # Handle validation errors
                error_msg = f"❌ Validation Error: {str(ve)}"
                return (None, "", gr.update(visible=True), gr.update(visible=True), error_msg,
                       gr.update(visible=True), gr.update(visible=False))
            except Exception as e:
                # Handle other errors with detailed message
                import traceback
                error_details = str(e)
                error_type = type(e).__name__
                
                # Provide user-friendly error messages
                if "AuthenticationError" in error_type or "401" in error_details:
                    error_msg = f"""❌ **API Key Authentication Failed**

The API key you provided was rejected by OpenAI. This usually means:
- The key is invalid or expired
- The key has been revoked
- There are extra spaces or characters in the key

**Please check:**
1. Copy the key exactly from https://platform.openai.com/api-keys
2. Make sure there are no spaces before or after the key
3. Verify the key starts with `sk-` and is about 51 characters long
4. Check if the key has usage limits or restrictions

**Error details:** {error_details[:200]}"""
                elif "RateLimitError" in error_type or "429" in error_details:
                    error_msg = f"""❌ **Rate Limit Exceeded**

OpenAI API rate limit reached. Please:
- Wait a few minutes and try again
- Check your OpenAI account usage limits
- Consider upgrading your OpenAI plan

**Error details:** {error_details[:200]}"""
                elif "database" in error_details.lower() or "connection" in error_details.lower():
                    error_msg = f"""❌ **Database Error**

Could not connect to or initialize the database:
{error_details[:300]}

**Please check:**
- Database file permissions
- Database path is correct
- Sufficient disk space available"""
                else:
                    error_msg = f"""❌ **Initialization Error**

An error occurred while initializing the app:
**Error Type:** {error_type}
**Error Message:** {error_details[:300]}

**Troubleshooting:**
1. Check the Hugging Face Space logs for more details
2. Verify your API key is correct
3. Try refreshing the page and entering the key again

If the problem persists, please check the Space logs."""
                
                return (None, "", gr.update(visible=True), gr.update(visible=True), error_msg,
                       gr.update(visible=True), gr.update(visible=False))
        
        # Function to process query (with API key check)
        def process_query_with_check(question: str, history: list, current_buddy, api_key):
            """Process query, checking if app is initialized."""
            if current_buddy is None:
                error_msg = "⚠️ Please set your API key first using the input field above."
                if not history:
                    history = []
                history.append({"role": "user", "content": question})
                history.append({"role": "assistant", "content": error_msg})
                return history, "", error_msg, "", ""
            
            return current_buddy.process_query(question, history)
        
        # Function to clear conversation
        def clear_conversation_with_check(current_buddy):
            """Clear conversation if app is initialized."""
            if current_buddy:
                return current_buddy.clear_conversation()
            return gr.update(value=[]), "", "", "", ""
        
        # Function to clear/reset API key
        def clear_api_key(current_buddy, current_api_key):
            """Clear API key and reset app state."""
            # Clear the buddy instance (which contains the API key)
            # This ensures the key is removed from memory
            return (
                None,  # Clear buddy state
                "",  # Clear API key state
                gr.update(visible=True, value=""),  # Show input field
                gr.update(visible=True),  # Show submit button
                gr.update(visible=False),  # Hide clear button
                "🔒 **API key cleared from memory.** Please enter a new key to continue. Your previous key has been completely removed and is not stored anywhere."
            )
        
        # Function to get optimization suggestions
        def get_optimization_with_check(sql_query: str, current_buddy):
            """Get optimization suggestions if app is initialized."""
            if current_buddy is None:
                return "⚠️ Please set your API key first to use this feature."
            return current_buddy.get_optimization_suggestions(sql_query)
        
        # API key submit handler
        api_key_submit.click(
            fn=initialize_app,
            inputs=[api_key_input, buddy_state],
            outputs=[buddy_state, api_key_state, api_key_input, api_key_submit, api_key_status, api_key_clear]
        )
        
        # API key clear handler
        api_key_clear.click(
            fn=clear_api_key,
            inputs=[buddy_state, api_key_state],
            outputs=[buddy_state, api_key_state, api_key_input, api_key_submit, api_key_clear, api_key_status]
        )
        
        # Event handlers (with API key check)
        submit_btn.click(
            fn=process_query_with_check,
            inputs=[question_input, chatbot, buddy_state, api_key_state],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        question_input.submit(
            fn=process_query_with_check,
            inputs=[question_input, chatbot, buddy_state, api_key_state],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        clear_btn.click(
            fn=clear_conversation_with_check,
            inputs=[buddy_state],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        optimize_btn.click(
            fn=get_optimization_with_check,
            inputs=[optimization_input, buddy_state],
            outputs=[optimization_output]
        )
        
        # Dark mode toggle handler
        def toggle_dark_mode(is_dark):
            """Toggle dark mode on/off."""
            return gr.update()
        
        dark_mode_toggle.change(
            fn=toggle_dark_mode,
            inputs=[dark_mode_toggle],
            outputs=[],
            js="""
            (isDark) => {
                const gradioApp = document.querySelector('gradio-app') || document.querySelector('#root') || document.body;
                const container = document.querySelector('.gradio-container') || gradioApp;
                
                if (isDark) {
                    container.classList.add('dark-mode-active');
                    // Apply to body and html for full coverage
                    document.body.classList.add('dark-mode-active');
                    document.documentElement.classList.add('dark-mode-active');
                } else {
                    container.classList.remove('dark-mode-active');
                    document.body.classList.remove('dark-mode-active');
                    document.documentElement.classList.remove('dark-mode-active');
                }
            }
            """
        )
    
    return demo


if __name__ == "__main__":
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///sample_database.db")
    vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_store")
    
    # If API key is set, verify it (but don't fail - let user enter it in UI)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            verify_openai_api_key()
        except ValueError as e:
            print(f"Warning: {str(e)}")
            print("User can enter API key in the interface.")
    
    # Create sample database if it doesn't exist (for HF Spaces)
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            print("Creating sample database...")
            try:
                from setup_sample_database import create_sample_database
                create_sample_database(db_path)
                print(f"Sample database created at {db_path}")
            except Exception as e:
                print(f"Warning: Could not create sample database: {e}")
    
    print(f"Connecting to database: {database_url}")
    print(f"Vector store path: {vector_db_path}")
    
    # Create and launch interface
    demo = create_interface(database_url, vector_db_path)
    
    # For Hugging Face Spaces, use simple launch (HF handles server settings)
    # For local development, you can specify custom settings
    if os.getenv("SPACE_ID"):  # Running on HF Spaces
        demo.launch()
    else:
        demo.launch(share=False, server_name="0.0.0.0", server_port=7860)

