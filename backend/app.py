# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph, Literal, URIRef
from rdflib.query import ResultRow
from dotenv import load_dotenv
import google.generativeai as genai
import json
import logging # Import the logging module

# Load environment variables from .env file
load_dotenv()

# --- Logging Configuration ---
# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set the minimum logging level to INFO

# Create console handler and set level to INFO
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)

# --- Configuration ---
# Flask app initialization
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) for all routes.
# In a production environment, you would restrict this to specific origins.
CORS(app)

# Load Gemini API Key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # Use logger.error instead of print
    logger.error("Error: GEMINI_API_KEY not found in .env file. Please set it.")
    exit(1)

# Configure the Google Generative AI with the API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model for conversational purposes
model = genai.GenerativeModel('gemini-2.0-flash')

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
        if not os.path.exists(KG_FILE_PATH):
            logger.error(f"Knowledge graph file not found at {KG_FILE_PATH}")
            return False
        kg_graph.parse(KG_FILE_PATH, format="turtle")
        logger.info(f"Knowledge graph loaded successfully from {KG_FILE_PATH}. Contains {len(kg_graph)} triples.")
        return True
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        return False

# Load the knowledge graph when the application starts
if not load_knowledge_graph():
    logger.error("Failed to load knowledge graph. Application may not function as expected.")

# --- Helper Functions for Agent Logic ---

def get_sparql_query_from_prompt(user_prompt: str) -> str | None:
    """
    Uses the Gemini LLM to generate a SPARQL query based on the user's natural language prompt.
    The LLM is prompted to output a JSON object containing the SPARQL query.
    """
    prefixes = """
    PREFIX : <http://example.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    llm_prompt = f"""
    You are an expert in SPARQL and RDF knowledge graphs.
    Your task is to convert a natural language question into a SPARQL query that can be executed against the provided knowledge graph.
    The knowledge graph has the following structure and prefixes:

    {prefixes}

    Classes: :Book, :Author
    Properties: :title, :author, :genre, :publicationYear, :name, :birthYear, :nationality

    Here are some examples of how to convert natural language to SPARQL queries based on the provided schema:

    User: "What is the title of the book by J.K. Rowling?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?title WHERE {{ ?book a :Book ; :author ?author ; :title ?title . ?author :name 'J.K. Rowling' . }}"
    }}
    ```

    User: "Who wrote the book '1984'?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?authorName WHERE {{ ?book a :Book ; :title '1984' ; :author ?author . ?author :name ?authorName . }}"
    }}
    ```

    User: "What are the genres of books published in 1945?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT DISTINCT ?genre WHERE {{ ?book a :Book ; :publicationYear '1945'^^xsd:gYear ; :genre ?genre . }}"
    }}
    ```

    User: "List all authors and their nationalities."
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?authorName ?nationality WHERE {{ ?author a :Author ; :name ?authorName ; :nationality ?nationality . }}"
    }}
    ```

    User: "Which books were written by British authors?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?bookTitle WHERE {{ ?book a :Book ; :title ?bookTitle ; :author ?author . ?author :nationality 'British' . }}"
    }}
    ```

    User: "Who was born in 1903?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?authorName WHERE {{ ?author a :Author ; :name ?authorName ; :birthYear '1903'^^xsd:gYear . }}"
    }}
    ```

    Now, generate the SPARQL query for the following user question. Ensure the output is a valid JSON object with a single key 'sparql_query'. If you cannot formulate a suitable SPARQL query, return an empty string for 'sparql_query'.

    User: "{user_prompt}"
    SPARQL:
    """
    try:
        response = model.generate_content(
            [llm_prompt],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "sparql_query": {"type": "STRING"}
                    }
                    # Removed "propertyOrdering": ["sparql_query"]
                }
            )
        )
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            raw_llm_response_text = response.candidates[0].content.parts[0].text
            logger.info(f"Raw LLM response text: {raw_llm_response_text}")
        else:
            logger.warning("LLM response did not contain expected content structure.")
            return None

        json_string = raw_llm_response_text
        parsed_json = json.loads(json_string)
        sparql_query = parsed_json.get("sparql_query")
        return sparql_query
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error from LLM response: {e}. Response was: {raw_llm_response_text}")
        return None
    except Exception as e:
        logger.error(f"Error generating SPARQL query with LLM: {e}")
        return None

def execute_sparql_query(query: str) -> list[dict]:
    """
    Executes a SPARQL query against the loaded knowledge graph and returns results as a list of dictionaries.
    """
    results_list = []
    try:
        results = kg_graph.query(query)
        for row in results:
            row_dict = {}
            for var in results.vars:
                value = row[var]
                if isinstance(value, URIRef):
                    row_dict[str(var)] = str(value)
                elif isinstance(value, Literal):
                    row_dict[str(var)] = str(value)
                else:
                    row_dict[str(var)] = value
            results_list.append(row_dict)
        logger.info(f"Successfully executed SPARQL query. Results count: {len(results_list)}")
        return results_list
    except Exception as e:
        logger.error(f"Error executing SPARQL query: {e}")
        return []

# --- API Endpoints ---

@app.route('/')
def home():
    """
    A simple home route to confirm the server is running.
    """
    logger.info("Home route accessed.")
    return "AI Knowledge Graph Agent Backend is running!"

@app.route('/query', methods=['POST'])
def query_kg():
    """
    Endpoint for querying the knowledge graph with a natural language prompt.
    This is where the core AI agent logic is implemented.
    """
    if not request.is_json:
        logger.warning("Received non-JSON request to /query endpoint.")
        return jsonify({"error": "Request must be JSON"}), 400

    user_prompt = request.json.get('prompt')
    if not user_prompt:
        logger.warning("No prompt provided in the request.")
        return jsonify({"error": "No prompt provided"}), 400

    logger.info(f"Received prompt: '{user_prompt}'")

    # Step 1: Use LLM to get SPARQL query from user prompt
    sparql_query = get_sparql_query_from_prompt(user_prompt)

    if not sparql_query:
        logger.info("LLM failed to generate a SPARQL query (returned None).")
        return jsonify({
            "user_prompt": user_prompt,
            "agent_response": "I couldn't understand your request to form a query. Please try rephrasing."
        })
    elif not sparql_query.strip():
        logger.info("LLM generated an empty or whitespace-only SPARQL query.")
        return jsonify({
            "user_prompt": user_prompt,
            "agent_response": "I couldn't formulate a relevant query based on your request. Please try rephrasing."
        })

    logger.info(f"Generated SPARQL query:\n{sparql_query}")

    # Step 2: Execute the generated SPARQL query
    query_results = execute_sparql_query(sparql_query)

    if not query_results:
        logger.info("No results found for the generated SPARQL query.")
        return jsonify({
            "user_prompt": user_prompt,
            "agent_response": f"I found no information related to '{user_prompt}' in the knowledge graph. "
                              f"Perhaps try a different query or check the knowledge graph content."
        })

    logger.info(f"Query results: {query_results}")
    return jsonify({
        "user_prompt": user_prompt,
        "sparql_query": sparql_query,
        "raw_query_results": query_results,
        "agent_response": "Raw query results are displayed. Next, I will synthesize this into a human-readable response."
    })

# --- Main entry point for running the Flask app ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
