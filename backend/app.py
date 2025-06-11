import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph
from dotenv import load_dotenv
import google.generativeai as genai  # Import the Google Generative AI library

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Flask app initialization
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for all routes.
# In a production environment, you would restrict this to specific origins.
CORS(app)

# Load Gemini API Key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Print an error if the API key is not found
    print("Error: GEMINI_API_KEY not found in .env file. Please set it.")
    exit(1)  # Exit the application if the API key is critical for startup

# Configure the Google Generative AI with the API key
genai.configure(api_key=GEMINI_API_KEY)

# --- Knowledge Graph Loading ---
# Initialize an RDF graph
kg_graph = Graph()
# Define the path to our sample knowledge graph file
KG_FILE_PATH = 'knowledge_graph.ttl'


def load_knowledge_graph():
    """
    Loads the Turtle knowledge graph from the specified file path.
    """
    try:
        # Check if the knowledge graph file exists
        if not os.path.exists(KG_FILE_PATH):
            print(f"Error: Knowledge graph file not found at {KG_FILE_PATH}")
            return False
        # Parse the Turtle file into the rdflib Graph object
        kg_graph.parse(KG_FILE_PATH, format="turtle")
        print(
            f"Knowledge graph loaded successfully from {KG_FILE_PATH}. Contains {len(kg_graph)} triples.")
        return True
    except Exception as e:
        # Log any errors during loading
        print(f"Error loading knowledge graph: {e}")
        return False


# Load the knowledge graph when the application starts
if not load_knowledge_graph():
    print("Failed to load knowledge graph. Application may not function as expected.")

# --- API Endpoints ---


@app.route('/')
def home():
    """
    A simple home route to confirm the server is running.
    """
    return "AI Knowledge Graph Agent Backend is running!"


@app.route('/query', methods=['POST'])
def query_kg():
    """
    Endpoint for querying the knowledge graph with a natural language prompt.
    This is where the core AI agent logic will be implemented.
    """
    # Ensure the request body is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Get the user prompt from the request
    user_prompt = request.json.get('prompt')

    # Basic validation for the prompt
    if not user_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # --- Agent Logic Placeholder ---
    # In future steps, this section will:
    # 1. Use LLM (Gemini) to understand the prompt and extract entities/intent.
    # 2. Construct a SPARQL query based on the extracted information.
    # 3. Execute the SPARQL query against `kg_graph`.
    # 4. Use LLM (Gemini) to synthesize a human-readable response from query results.

    # For now, let's return a dummy response
    print(f"Received prompt: '{user_prompt}'")
    dummy_response = {
        "user_prompt": user_prompt,
        "agent_response": f"Thank you for your query about '{user_prompt}'. "
                          f"The agent is currently under development and will process this soon!"
    }
    return jsonify(dummy_response)


# --- Main entry point for running the Flask app ---
if __name__ == '__main__':
    # Run the Flask app in debug mode.
    # In production, you would use a production-ready WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=5000)
