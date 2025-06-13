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
import re
from datetime import datetime

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
KG_FILE_PATH = 'presentation_data.ttl'
ONTOLOGY_FILE_PATH = 'good_presentation_ontology.ttl'


def load_knowledge_graph():
    try:
        if not os.path.exists(KG_FILE_PATH):
            logger.error(
                f"Knowledge graph data file not found at {KG_FILE_PATH}")
            # Create an empty file with the new prefixes if it doesn't exist
            with open(KG_FILE_PATH, 'w') as f:
                f.write("""@prefix : <http://example.org/scientific-presentation-ontology#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
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
    # Updated prefixes to match the new ontology
    prefixes = """
    PREFIX : <http://example.org/scientific-presentation-ontology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    """

    # Updated ontology schema description
    ontology_schema = """
    Classes: ScientificPresentation, PresentationSection, ScientificTopic, ConferencePresentation, KeynotePresentation, WorkshopPresentation, Introduction, Methods, Results, Discussion, Conclusion, LiteratureReview, FutureWork, ProblemStatement, Roadmap, Audience, InterdisciplinaryAudience, SpecializedAudience, MixedExpertiseAudience, GeneralAudience, ContentElement, ScientificClaim, DataVisualization, Methodology, Citation, Limitation, Evidence, BackgroundInformation, Hook, TakeawayMessage, Transition, ScientificDetail, QualityMetric, ScientificRigor, AudienceEngagement, NarrativeCoherence, LinguisticQuality, TechnicalAccuracy, NarrativeDevice, Analogy, RhetoricalQuestion, RealWorldExample, StorytellingTechnique, Humor, EngagementStrategy, InteractivePoll, ThoughtExperiment, CallToAction, QuestionAndAnswer, LiveDemonstration, PresentationPurpose

    Object Properties: hasSection, hasRecommendedSection, followedBy, hasLogicalSuccessor, hasLogicalPredecessor, contains, targetedAt, uses, appliesTo, employs, evaluatedBy, requires, supports, acknowledges, adaptedFor, appropriateFor, effectiveFor, isRelevantFor, simplifyContentItem, omitContentItem

    Data Properties: sectionName, sectionPurpose, sequenceOrder, sectionLength, timeAllocation, textualContentAmount, presentationType, duration, complexityLevel, technicalDepth, isEssential, accuracyScore, grammarCorrectness, coherenceScore, engagementLevel, rigorLevel, detailImportanceLevel, noveltyLevel, expertiseLevel, culturalContext, expectedSize, attentionSpan, citationFormat, evidenceType, narrativeFunction, narrativeEffectiveness
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
      "sparql_query": "SELECT ?sectionName WHERE {{ :ArtificialIntelligence :hasRecommendedSection ?section . ?section :sectionName ?sectionName . }}"
    }}
    ```

    User: "What is the recommended order of sections for the 'Introduction to AI' section?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?order WHERE {{ ?section :sectionName "Introduction to AI" ; :sequenceOrder ?order . }}"
    }}
    ```

    User: "Which content items should be simplified when discussing Deep Learning?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?contentItem WHERE {{ ?contentItem :simplifyContentItem ?simplifiedVersion . }}"
    }}
    ```

    User: "What narrative devices are applicable to enhance coherence across multiple sections, specifically for 'Methods'?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?device ?function WHERE {{ ?device :appliesTo :Methods ; :narrativeFunction ?function . }}"
    }}
    ```

    User: "Which scientific details are most relevant for Domain Experts?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?detail WHERE {{ ?detail :isRelevantFor :SpecializedAudience ; :detailImportanceLevel "4"^^xsd:integer . }}"
    }}
    ```
    
    User: "What section has order 1?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?sectionName WHERE {{ ?section :sequenceOrder \"1\"^^xsd:integer ; :sectionName ?sectionName . }}"
    }}
    ```
    User: "What are the recommended sections for Semantic Reasoning?"
    SPARQL:
    ```json
    {{
      "sparql_query": "SELECT ?sectionName WHERE {{ :SemanticReasoning :hasRecommendedSection ?section . ?section :sectionName ?sectionName . }}"
    }}

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
                    # Keep full URI if it's not part of the default namespace
                    if str(value).startswith("[http://example.org/scientific-presentation-ontology#](http://example.org/scientific-presentation-ontology#)"):
                        clean_value = str(value).split(
                            '#')[-1].replace('_', ' ')
                    else:
                        # Keep full URI for external resources
                        clean_value = str(value)
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
    if not query_results:
        return "I couldn't find any information related to your request in the knowledge graph."

    # Convert query_results to a string format suitable for the LLM
    query_results_str = json.dumps(query_results, indent=2)

    llm_prompt_synthesis = f"""
    You are an AI assistant designed to provide clear and concise answers based on structured data.
    The user asked the following question: "{user_prompt}"

    A SPARQL query was executed, and the following raw results were obtained from the knowledge graph:
    {query_results_str}

    Based ONLY on the provided query results, synthesize a human-readable answer to the user's question.
    Do not add any information that is not directly supported by the results.
    Keep the response concise and to the point. If the results are empty, state that no information was found.
    If the results contain information, summarize it clearly.

    Synthesized Answer:
    """
    try:
        response = llm_model.generate_content([llm_prompt_synthesis])
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            synthesized_answer = response.candidates[0].content.parts[0].text.strip(
            )
            logger.info(f"LLM synthesized response: {synthesized_answer}")
            return synthesized_answer
        else:
            logger.warning(
                "LLM (response synthesis) response did not contain expected content.")
            return "I couldn't synthesize a clear answer based on the query results."
    except Exception as e:
        logger.error(
            f"Error synthesizing human-readable response with LLM: {e}")
        return "An error occurred while trying to synthesize the answer."


def generate_data_for_prompt(user_prompt: str, sparql_query: str) -> str | None:
    prefixes = """
    PREFIX : [http://example.org/scientific-presentation-ontology#](http://example.org/scientific-presentation-ontology#)
    PREFIX owl: [http://www.w3.org/2002/07/owl#](http://www.w3.org/2002/07/owl#)
    PREFIX rdf: [http://www.w3.org/1999/02/22-rdf-syntax-ns#](http://www.w3.org/1999/02/22-rdf-syntax-ns#)
    PREFIX rdfs: [http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#)
    PREFIX xsd: [http://www.w3.org/2001/XMLSchema#](http://www.w3.org/2001/XMLSchema#)
    PREFIX dc: [http://purl.org/dc/elements/1.1/](http://purl.org/dc/elements/1.1/)
    """

    # Updated ontology schema description for data generation prompt
    ontology_schema = """
    Classes: ScientificPresentation, PresentationSection, ScientificTopic, ConferencePresentation, KeynotePresentation, WorkshopPresentation, Introduction, Methods, Results, Discussion, Conclusion, LiteratureReview, FutureWork, ProblemStatement, Roadmap, Audience, InterdisciplinaryAudience, SpecializedAudience, MixedExpertiseAudience, GeneralAudience, ContentElement, ScientificClaim, DataVisualization, Methodology, Citation, Limitation, Evidence, BackgroundInformation, Hook, TakeawayMessage, Transition, ScientificDetail, QualityMetric, ScientificRigor, AudienceEngagement, NarrativeCoherence, LinguisticQuality, TechnicalAccuracy, NarrativeDevice, Analogy, RhetoricalQuestion, RealWorldExample, StorytellingTechnique, Humor, EngagementStrategy, InteractivePoll, ThoughtExperiment, CallToAction, QuestionAndAnswer, LiveDemonstration, PresentationPurpose

    Object Properties: hasSection, hasRecommendedSection, followedBy, hasLogicalSuccessor, hasLogicalPredecessor, contains, targetedAt, uses, appliesTo, employs, evaluatedBy, requires, supports, acknowledges, adaptedFor, appropriateFor, effectiveFor, isRelevantFor, simplifyContentItem, omitContentItem

    Data Properties: sectionName, sectionPurpose, sequenceOrder, sectionLength, timeAllocation, textualContentAmount, presentationType, duration, complexityLevel, technicalDepth, isEssential, accuracyScore, grammarCorrectness, coherenceScore, engagementLevel, rigorLevel, detailImportanceLevel, noveltyLevel, expertiseLevel, culturalContext, expectedSize, attentionSpan, citationFormat, evidenceType, narrativeFunction, narrativeEffectiveness
    """

    llm_prompt_data_gen = f"""
    You are an expert in RDF and Turtle syntax, and a domain expert in presentation structures for scientific topics.
    Your task is to generate realistic and schema-compliant RDF triples in Turtle format for a given scientific topic, based on the provided ontology.

    Ensure all URIs are unique and follow conventions (e.g., :TopicName for topics, :SectionName for sections).
    Return only the Turtle data without any additional text or explanations.

    The user is asking: "{user_prompt}"
    To answer this question, a SPARQL query has been generated: "{sparql_query}"
    Please generate data that would allow this SPARQL query to return meaningful results related to the user's question.

    Ontology Schema and Prefixes:
    {prefixes}
    {ontology_schema}

    Generated Turtle:
    """
    try:
        response = llm_model.generate_content([llm_prompt_data_gen])
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            generated_turtle = response.candidates[0].content.parts[0].text.strip(
            )
            if "```turtle" in generated_turtle:
                # Extract the Turtle content if wrapped in ```turtle
                generated_turtle = re.search(
                    r'```turtle\s*(.*?)\s*```', generated_turtle, re.DOTALL)
                if generated_turtle:
                    generated_turtle = generated_turtle.group(1).strip()
            logger.info(f"LLM generated data (Turtle): \n{generated_turtle}")
            return generated_turtle
        else:
            logger.warning(
                "LLM (data generation) response did not contain expected content.")
            return None
    except Exception as e:
        logger.error(f"Error calling LLM for data generation: {e}")
        return None


@app.route('/get_graph_data', methods=['POST'])
def get_graph_data():
    logger.info("Received request to get graph data.")
    try:
        nodes = []
        links = []
        node_ids = set()

        for s, p, o in kg_graph:
            # Process Subject (s)
            s_id = str(s)
            # Split by # for new ontology prefix
            s_name = s_id.split('#')[-1].replace('_', ' ')
            if s_id not in node_ids:
                nodes.append({"id": s_id, "name": s_name})
                node_ids.add(s_id)

            # Process Object (o)
            o_id = None
            o_name = None

            if isinstance(o, URIRef):
                o_id = str(o)
                # Split by # for new ontology prefix
                o_name = o_id.split('#')[-1].replace('_', ' ')
                if o_id not in node_ids:
                    nodes.append({"id": o_id, "name": o_name})
                    node_ids.add(o_id)
            elif isinstance(o, Literal):
                o_id = f"literal_{s_id}_{p}_{o}"
                o_name = str(o)
                if o_id not in node_ids:
                    nodes.append(
                        {"id": o_id, "name": o_name, "isLiteral": True})
                    node_ids.add(o_id)
            else:
                o_id = str(o)
                # Split by # for new ontology prefix
                o_name = o_id.split('#')[-1].replace('_', ' ')
                if o_id not in node_ids:
                    nodes.append({"id": o_id, "name": o_name})
                    node_ids.add(o_id)

            # Process Predicate (p) and add Link
            # Split by # for new ontology prefix
            p_label = str(p).split('#')[-1].replace('_', ' ')

            # Exclude rdf:type, rdfs:domain, rdfs:range, and owl:Class from direct links
            if p != URIRef("[http://www.w3.org/1999/02/22-rdf-syntax-ns#type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type)") and \
               p != URIRef("[http://www.w3.org/2000/01/rdf-schema#domain](http://www.w3.org/2000/01/rdf-schema#domain)") and \
               p != URIRef("[http://www.w3.org/2002/07/owl#Class](http://www.w3.org/2002/07/owl#Class)") and \
               p != URIRef("[http://www.w3.org/2000/01/rdf-schema#range](http://www.w3.org/2000/01/rdf-schema#range)"):  # Also exclude owl:Class and range
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

    generated_data_turtle = generate_data_for_prompt(user_prompt, sparql_query)
    if generated_data_turtle:
        try:
            temp_graph = Graph()
            temp_graph.parse(
                data=generated_data_turtle, format="turtle")
            for s, p, o in temp_graph:
                kg_graph.add((s, p, o))
            logger.info(
                f"Dynamically added {len(temp_graph)} triples to the knowledge graph.")
            data_generated_flag = True

            # Persist the entire current kg_graph to a new file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"generated_data_{timestamp}.ttl"
            output_filepath = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), output_filename)
            kg_graph.serialize(
                destination=output_filepath, format="turtle")
            logger.info(
                f"Current knowledge graph saved to: {output_filepath}")

            # Re-execute the original SPARQL query against the now-updated graph
            query_results = execute_sparql_query(sparql_query)
        except Exception as parse_error:
            logger.error(
                f"Error parsing dynamically generated Turtle: {parse_error}. Generated Turtle: \n{generated_data_turtle}")
            data_generated_flag = False
            generated_data_turtle = f"Error parsing generated data: {parse_error}\nGenerated:\n{generated_data_turtle}"
    else:
        logger.warning(
            f"LLM failed to generate data.")
        return jsonify({
            "user_prompt": user_prompt,
            "agent_response": "I couldn't generate any data based on your request.",
            "sparql_query": sparql_query,
            "raw_query_results": []
        })

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
    if generated_data_turtle:
        response_payload["added_triples"] = generated_data_turtle

    return jsonify(response_payload)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
