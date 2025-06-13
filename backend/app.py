# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph, Literal, URIRef
from rdflib.query import ResultRow
from dotenv import load_dotenv
import google.generativeai as genai
import json
import logging
import re  # For regular expressions to extract topic from query

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error(
        "Error: GEMINI_API_KEY not found in .env file. Please set it.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel('gemini-2.0-flash')

kg_graph = Graph()
KG_FILE_PATH = 'presentation_data.ttl'  # This file will now be initially empty
ONTOLOGY_FILE_PATH = 'good_presentation_ontology.ttl'


def load_knowledge_graph():
    try:
        if not os.path.exists(KG_FILE_PATH):
            logger.error(
                f"Knowledge graph data file not found at {KG_FILE_PATH}")
            # Create an empty file if it doesn't exist
            with open(KG_FILE_PATH, 'w') as f:
                f.write("""@prefix ex: <http://example.org/presentation#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
""")
            logger.info(f"Created empty {KG_FILE_PATH} as it was not found.")

        kg_graph.parse(ONTOLOGY_FILE_PATH, format="turtle")
        kg_graph.parse(KG_FILE_PATH, format="turtle")
        logger.info(
            f"Knowledge graph (ontology + initial data) loaded successfully. Contains {len(kg_graph)} triples.")
        return True
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        return False


if not load_knowledge_graph():
    logger.error(
        "Failed to load knowledge graph. Application may not function as expected.")


def get_sparql_query_from_prompt(user_prompt: str) -> str | None:
    prefixes = """
    PREFIX ex: <http://example.org/presentation#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    ontology_schema = """
    Classes: ex:PresentationSection, ex:ScientificTopic, ex:ContentItem, ex:AudienceType, ex:PresentationPurpose, ex:NarrativeDevice, ex:TargetAudience, ex:ScientificDetail, ex:PresentationType
    Object Properties: ex:hasRecommendedSection, ex:hasLogicalPredecessor, ex:hasLogicalSuccessor, ex:AppliesToSection, ex:isRelevantFor
    Data Properties: ex:SectionName, ex:SectionPurpose, ex:sectionOrder, ex:sectionLength, ex:simplifyContentItem, ex:omitContentItem, ex:complexityLevel, ex:isEssential, ex:NarrativeFunction, ex:NarrativeEffectiveness, ex:detailImportanceLevel
    """

    llm_prompt = f"""
    You are an expert in SPARQL and RDF knowledge graphs.
    Your task is to convert a natural language question into a SPARQL query that can be executed against the provided knowledge graph.
    The knowledge graph has the following structure and prefixes:

    {prefixes}
    {ontology_schema}

    Here are some examples of how to convert natural language to SPARQL queries based on the provided schema:

    User: "Which standard presentation sections should be included for Artificial Intelligence?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?sectionName WHERE {{ ex:ArtificialIntelligence ex:hasRecommendedSection ?section . ?section ex:SectionName ?sectionName . }}"
    }}
    ```

    User: "What is the recommended order of sections for the 'Introduction to AI' section?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?order WHERE {{ ?section ex:SectionName "Introduction to AI" ; ex:sectionOrder ?order . }}"
    }}
    ```

    User: "Which content items should be simplified when discussing Deep Learning?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?contentItem WHERE {{ ?contentItem ex:simplifyContentItem "Explain in simple terms" . }}"
    }}
    ```

    User: "What narrative devices are applicable to enhance coherence across multiple sections, specifically for 'MethodologySection'?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?device ?function WHERE {{ ?device ex:AppliesToSection ex:A_Methodology ; ex:NarrativeFunction ?function . }}"
    }}
    ```

    User: "Which scientific details are most relevant for Domain Experts?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?detail WHERE {{ ?detail ex:isRelevantFor ex:DomainExperts ; ex:detailImportanceLevel "High" . }}"
    }}
    ```
    
    User: "What section has order 1?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?sectionName WHERE {{ ?section ex:sectionOrder \"1\"^^xsd:integer ; ex:SectionName ?sectionName . }}"
    }}
    ```

    Now, generate the SPARQL query for the following user question. Ensure the output is a valid JSON object with a single key 'sparql_query'. If you cannot formulate a suitable SPARQL query, return an empty string for 'sparql_query'.

    User: "{user_prompt}"
    SPARQL:
    """
    try:
        response = llm_model.generate_content(
            [llm_prompt],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "sparql_query": {"type": "STRING"}
                    }
                }
            )
        )
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            raw_llm_response_text = response.candidates[0].content.parts[0].text
            logger.info(
                f"Raw LLM (query generation) response text: {raw_llm_response_text}")
        else:
            logger.warning(
                "LLM (query generation) response did not contain expected content structure.")
            return None

        json_string = raw_llm_response_text
        parsed_json = json.loads(json_string)
        sparql_query = parsed_json.get("sparql_query")
        return sparql_query
    except json.JSONDecodeError as e:
        logger.error(
            f"JSON decoding error from LLM (query generation) response: {e}. Response was: {raw_llm_response_text}")
        return None
    except Exception as e:
        logger.error(f"Error generating SPARQL query with LLM: {e}")
        return None


def execute_sparql_query(query: str) -> list[dict]:
    results_list = []
    try:
        results = kg_graph.query(query)
        for row in results:
            row_dict = {}
            for var in results.vars:
                value = row[var]
                if isinstance(value, URIRef):
                    clean_value = str(value).split('/')[-1].replace('_', ' ')
                    row_dict[str(var)] = clean_value
                elif isinstance(value, Literal):
                    row_dict[str(var)] = str(value)
                else:
                    row_dict[str(var)] = value
            results_list.append(row_dict)
        logger.info(
            f"Successfully executed SPARQL query. Results count: {len(results_list)}")
        return results_list
    except Exception as e:
        logger.error(f"Error executing SPARQL query: {e}")
        return []


def synthesize_human_readable_response(user_prompt: str, query_results: list[dict], data_generated: bool = False) -> str:
    # Removed the data_generated_flag prefix from the user-facing response

    if not query_results:
        return "I couldn't find any information related to your request in the knowledge graph."

    # More nuanced response synthesis for clarity
    if "sectionName" in query_results[0]:
        sections = [res["sectionName"]
                    for res in query_results if "sectionName" in res]
        return f"The standard presentation sections are: {', '.join(sections)}."
    elif "order" in query_results[0]:
        orders = [res["order"] for res in query_results if "order" in res]
        return f"The recommended order of sections is: {', '.join(orders)}."
    elif "contentItem" in query_results[0]:
        items = [res["contentItem"]
                 for res in query_results if "contentItem" in res]
        return f"The content items are: {', '.join(items)}."
    elif "detail" in query_results[0]:
        details = [res["detail"] for res in query_results if "detail" in res]
        return f"The relevant scientific details are: {', '.join(details)}."
    elif "device" in query_results[0] and "function" in query_results[0]:
        devices = [
            f"{res['device']} (Function: {res['function']})" for res in query_results]
        return f"The applicable narrative devices are: {', '.join(devices)}."
    else:
        # Generic response for other query types
        results_string = ", ".join([
            f"{key}: {value}" for result_dict in query_results for key, value in result_dict.items()
        ])
        return f"Here's what I found: {results_string}"


def generate_data_for_topic(topic_name: str) -> str | None:
    prefixes = """
    PREFIX ex: <http://example.org/presentation#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    ontology_schema = """
    Classes: ex:PresentationSection, ex:ScientificTopic, ex:ContentItem, ex:AudienceType, ex:PresentationPurpose, ex:NarrativeDevice, ex:TargetAudience, ex:ScientificDetail, ex:PresentationType
    Object Properties: ex:hasRecommendedSection, ex:hasLogicalPredecessor, ex:hasLogicalSuccessor, ex:AppliesToSection, ex:isRelevantFor
    Data Properties: ex:SectionName, ex:SectionPurpose, ex:sectionOrder, ex:sectionLength, ex:simplifyContentItem, ex:omitContentItem, ex:complexityLevel, ex:isEssential, ex:NarrativeFunction, ex:NarrativeEffectiveness, ex:detailImportanceLevel
    """

    llm_prompt_data_gen = f"""
    You are an expert in RDF and Turtle syntax, and a domain expert in presentation structures for scientific topics.
    Your task is to generate realistic and schema-compliant RDF triples in Turtle format for a given scientific topic, based on the provided ontology.
    The generated data should describe a typical presentation structure for the topic, including:
    - The scientific topic itself (an instance of ex:ScientificTopic).
    - Recommended presentation sections for this topic (instances of ex:PresentationSection).
    - For each section: SectionName, SectionPurpose, sectionOrder (as xsd:integer), sectionLength (e.g., "5 slides").
    - Logical predecessors and successors between relevant sections.
    - At least one relevant content item (ex:ContentItem) with its complexity and essentiality.
    - At least one relevant narrative device (ex:NarrativeDevice) with its function and effectiveness.
    - At least one scientific detail (ex:ScientificDetail) with its relevance for an audience type and importance level.

    Ensure all URIs are unique and follow conventions (e.g., ex:TopicName for topics, ex:SectionName for sections).
    Do NOT generate any introductory or concluding text, explanations, or markdown fences (```turtle```). Output ONLY the Turtle triples.

    Ontology Schema and Prefixes:
    {prefixes}
    {ontology_schema}

    Scientific Topic for which to generate data: "{topic_name}"
    Generated Turtle:
    """
    try:
        response = llm_model.generate_content([llm_prompt_data_gen])
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            generated_turtle = response.candidates[0].content.parts[0].text.strip(
            )
            logger.info(f"LLM generated data (Turtle): \n{generated_turtle}")
            return generated_turtle
        else:
            logger.warning(
                "LLM (data generation) response did not contain expected content.")
            return None
    except Exception as e:
        logger.error(f"Error calling LLM for data generation: {e}")
        return None


def extract_scientific_topic_from_query(sparql_query: str) -> str | None:
    # Attempt to find a scientific topic URI in the SPARQL query
    # This is a heuristic and might need refinement based on query patterns
    match = re.search(
        r'ex:([A-Za-z0-9_]+)\s+ex:hasRecommendedSection', sparql_query)
    if match:
        # Return "Artificial Intelligence" from ex:ArtificialIntelligence
        return match.group(1).replace('_', ' ')
    return None


@app.route('/get_graph_data', methods=['POST'])
def get_graph_data():
    logger.info("Received request to get graph data.")
    try:
        nodes = []
        links = []
        node_ids = set()  # Use a set to track node IDs already added

        for s, p, o in kg_graph:
            # Process Subject (s)
            s_id = str(s)
            s_name = s_id.split('/')[-1].replace('_', ' ')
            if s_id not in node_ids:
                nodes.append({"id": s_id, "name": s_name})
                node_ids.add(s_id)

            # Process Object (o)
            o_id = None  # Initialize o_id for safety
            o_name = None

            if isinstance(o, URIRef):
                o_id = str(o)
                o_name = o_id.split('/')[-1].replace('_', ' ')
                if o_id not in node_ids:  # Add object node only if it's new
                    nodes.append({"id": o_id, "name": o_name})
                    node_ids.add(o_id)
            elif isinstance(o, Literal):
                # For literals, create a unique ID based on subject, predicate, and literal value
                o_id = f"literal_{s_id}_{p}_{o}"
                o_name = str(o)
                # Add literal node only if this unique ID is new
                if o_id not in node_ids:
                    nodes.append(
                        {"id": o_id, "name": o_name, "isLiteral": True})
                    node_ids.add(o_id)
            else:
                # Fallback for unexpected 'o' types, treat as URI string
                # This block should ideally not be hit for valid RDF, as 'o' is always a URIRef or a Literal.
                o_id = str(o)
                o_name = o_id.split('/')[-1].replace('_', ' ')
                if o_id not in node_ids:
                    nodes.append({"id": o_id, "name": o_name})
                    node_ids.add(o_id)

            # Process Predicate (p) and add Link
            p_label = str(p).split('/')[-1].replace('_', ' ')

            # Exclude rdf:type, rdfs:domain, rdfs:range from direct links for cleaner visualization
            if p != URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type") and \
               p != URIRef("http://www.w3.org/2000/01/rdf-schema#domain") and \
               p != URIRef("http://www.w3.org/2000/01/rdf-schema#range"):
                links.append(
                    {"source": s_id, "target": o_id, "label": p_label})

        logger.info(
            f"Successfully extracted graph data: {len(nodes)} nodes, {len(links)} links.")
        return jsonify({"nodes": nodes, "links": links})

    except Exception as e:
        logger.error(f"Error extracting graph data: {e}")
        return jsonify({"error": f"Failed to get graph data: {e}"}), 500


@app.route('/')
def home():
    logger.info("Home route accessed.")
    return "AI Knowledge Graph Agent Backend is running!"


@app.route('/query', methods=['POST'])
def query_kg():
    if not request.is_json:
        logger.warning("Received non-JSON request to /query endpoint.")
        return jsonify({"error": "Request must be JSON"}), 400

    user_prompt = request.json.get('prompt')
    if not user_prompt:
        logger.warning("No prompt provided in the request.")
        return jsonify({"error": "No prompt provided"}), 400

    logger.info(f"Received prompt: '{user_prompt}'")

    sparql_query = get_sparql_query_from_prompt(user_prompt)
    data_generated_flag = False
    generated_data_turtle = None

    if not sparql_query or not sparql_query.strip():
        logger.info(
            "LLM failed to generate a SPARQL query (returned None or empty).")
        return jsonify({
            "user_prompt": user_prompt,
            "agent_response": "I couldn't understand your request to form a query. Please try rephrasing.",
            "sparql_query": "",
            "raw_query_results": []
        })

    logger.info(f"Generated SPARQL query:\n{sparql_query}")
    query_results = execute_sparql_query(sparql_query)

    # If query results are empty, attempt to generate data
    if not query_results:
        logger.info(
            "Query returned no results. Attempting to generate data dynamically.")

        # Heuristic: Try to extract a scientific topic from the SPARQL query itself
        topic = extract_scientific_topic_from_query(sparql_query)

        if topic:
            logger.info(f"Detected topic for data generation: {topic}")
            generated_data_turtle = generate_data_for_topic(topic)
            if generated_data_turtle:
                try:
                    temp_graph = Graph()
                    temp_graph.parse(
                        data=generated_data_turtle, format="turtle")
                    for s, p, o in temp_graph:
                        kg_graph.add((s, p, o))
                    logger.info(
                        f"Dynamically added {len(temp_graph)} triples to the knowledge graph for topic '{topic}'.")
                    data_generated_flag = True
                    # Re-execute the original SPARQL query against the now-updated graph
                    query_results = execute_sparql_query(sparql_query)
                except Exception as parse_error:
                    logger.error(
                        f"Error parsing dynamically generated Turtle: {parse_error}. Generated Turtle: \n{generated_data_turtle}")
                    # Reset flag as data addition failed
                    data_generated_flag = False
                    # Keep generated_data_turtle for debugging in frontend if parsing failed
                    generated_data_turtle = f"Error parsing generated data: {parse_error}\nGenerated:\n{generated_data_turtle}"
            else:
                logger.warning(
                    f"LLM failed to generate data for topic: {topic}.")
        else:
            logger.info(
                "Could not extract a scientific topic from the query for dynamic data generation.")

    agent_final_response = synthesize_human_readable_response(
        user_prompt, query_results, data_generated_flag)

    logger.info(f"Query results: {query_results}")
    logger.info(f"Agent's final response: {agent_final_response}")

    response_payload = {
        "user_prompt": user_prompt,
        "sparql_query": sparql_query,
        "raw_query_results": query_results,
        "agent_response": agent_final_response
    }
    if generated_data_turtle:  # Only add if data was actually attempted to be generated
        response_payload["added_triples"] = generated_data_turtle

    return jsonify(response_payload)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
