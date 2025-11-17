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


class SQLQueryBuddy:
    """Main application class for SQL Query Buddy."""
    
    def __init__(
        self,
        database_url: str,
        vector_db_path: str = "./vector_store",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.1
    ):
        """
        Initialize SQL Query Buddy.
        
        Args:
            database_url: SQLAlchemy database URL
            vector_db_path: Path to vector database
            model_name: OpenAI model name
            temperature: LLM temperature
        """
        self.database_url = database_url
        self.vector_store_manager = VectorStoreManager(
            database_url=database_url,
            vector_db_path=vector_db_path
        )
        self.sql_generator = SQLGenerator(
            vector_store_manager=self.vector_store_manager,
            model_name=model_name,
            temperature=temperature
        )
        self.query_executor = QueryExecutor(
            database_url=database_url,
            sql_generator=self.sql_generator
        )
        self.insight_generator = InsightGenerator(
            model_name=model_name,
            temperature=0.3
        )
        self.context_manager = ContextManager(max_history=20)
        
        # Build vector store on initialization
        print("Initializing vector store...")
        self.vector_store_manager.build_vector_store(include_samples=True)
        print("Vector store ready!")
    
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
    
    # Initialize SQL Query Buddy
    buddy = SQLQueryBuddy(
        database_url=database_url,
        vector_db_path=vector_db_path
    )
    
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
        
        # Event handlers
        submit_btn.click(
            fn=buddy.process_query,
            inputs=[question_input, chatbot],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        question_input.submit(
            fn=buddy.process_query,
            inputs=[question_input, chatbot],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        clear_btn.click(
            fn=buddy.clear_conversation,
            inputs=[],
            outputs=[chatbot, sql_output, gr.Textbox(visible=False), insights_output, explanation_output]
        )
        
        optimize_btn.click(
            fn=buddy.get_optimization_suggestions,
            inputs=[optimization_input],
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
    
    print(f"Connecting to database: {database_url}")
    print(f"Vector store path: {vector_db_path}")
    
    # Create and launch interface
    demo = create_interface(database_url, vector_db_path)
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)

