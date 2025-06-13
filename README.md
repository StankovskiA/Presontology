![image](https://github.com/user-attachments/assets/17233e7c-4d5b-482f-a13c-4cf305475ed3)# 🧠 Presentology Agent: An AI-Powered Knowledge Graph Assistant
## Project Overview

The Presentology Agent is an interactive web application designed to assist researchers in developing and refining scientific presentations. It operates on a dynamic knowledge graph, built upon a specialized ontology, to provide intelligent responses to natural language queries. A key feature is its ability to dynamically extend its knowledge base by generating new RDF triples when it encounters a query that cannot be answered by existing data.
<details><summary>Images of the web app</summary>
![image](https://github.com/user-attachments/assets/c09eb385-b794-4962-94ef-ecf210909e3b)
![image](https://github.com/user-attachments/assets/9235151f-edeb-4dec-b8e7-b24fc54ba2a1)
![image](https://github.com/user-attachments/assets/37022ae0-d49f-4b8f-b201-0722ce308925)
![image](https://github.com/user-attachments/assets/d865de2f-135c-44e0-a61e-b2a8c11e3ed2)

</details>

## Features

-  **Natural Language Understanding**: Interact with the agent using everyday language to ask questions about presentation sections, content, audience, and more.

-  **SPARQL Query Generation**: The agent intelligently translates your natural language queries into formal SPARQL queries.

-  **Dynamic Data Generation**: If the existing knowledge graph lacks information to answer a specific query (especially for new scientific topics), the agent can dynamically generate relevant RDF triples and add them to its knowledge base.

-  **Knowledge Graph Visualization**: A built-in interactive graph viewer allows you to visualize the ontology's entities and their relationships, including newly generated data.

- **Real-time Persistence**: Dynamically generated data is saved to new .ttl files on the backend for future reference and analysis.

- Transparent Operation: Agent responses include details like the generated SPARQL query, raw query results, and the dynamically added RDF triples (if any), ensuring transparency in its reasoning.

## Prerequisites

Before running the application, ensure you have the following installed:

    Python 3.8+ (for the backend)

    Node.js (LTS recommended, for the frontend)

    pip (Python package installer)

    npm or yarn (Node.js package managers)

    Git (for cloning the repository)

## Setup and Installation

Follow these steps to set up and run the application locally:
### 1. Clone the Repository

```bash
git clone https://github.com/StankovskiA/Presontology
cd Presontology
```


### 2. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```


#### a. Create a Python Virtual Environment:
```bash
python -m venv venv
```


#### b. Activate the Virtual Environment:
```bash
    Windows: .\venv\Scripts\activate
```
```bash
    macOS/Linux: source venv/bin/activate
```

#### c. Install Python Dependencies:

```bash
pip install -r requirements.txt
```



#### d. Set up Environment Variables:

Create a .env file in the backend directory and add your API keys:

```
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
```

### 3. Frontend Setup

Open a new terminal or command prompt, navigate to the frontend directory:

```bash
cd ../frontend
```


#### a. Install Node.js Dependencies:

```bash
npm install
```
or 
```bash
yarn install
```

### 4. Run the Application
#### a. Run the Backend

In your backend terminal (where the virtual environment is activated):
```bash
python app.py
```

The Flask backend will start, usually on http://127.0.0.1:5000.

#### b. Run the Frontend

In your frontend terminal:

```bash
npm run dev
```
or
```bash
yarn dev
```


The React development server will start, usually on http://localhost:5173 (or another available port). Open this URL in your web browser.
Usage

Once both the backend and frontend servers are running, open your browser to the frontend URL.

- **Ask a Question**: Type your query into the input field at the bottom of the chat interface (e.g., "Which standard presentation sections should be included for Artificial Intelligence?").

- **View Agent Response**: The agent will process your query and display a human-readable answer.

- **Explore Details**: Click on the "Details" section within the agent's message bubble to see the generated SPARQL query, raw query results, and any dynamically added RDF triples.

- **Visualize Knowledge Graph**: If new data was generated and added, a "Show Updated Graph" button will appear within the agent's message bubble. Click this to visualize the current state of the knowledge graph.

- **Dynamic Persistence**: Check your backend directory for new .ttl files (e.g., generated_data_Artificial_Intelligence_YYYYMMDD_HHMMSS.ttl). These files represent the knowledge graph state after dynamic data generation.

## Key Technologies

    Backend: Python, Flask

    Knowledge Graph: rdflib

    Large Language Models: Google Gemini API, OpenAI API (GPT), Anthropic API (Claude)

    Frontend: React, Vite, Tailwind CSS

    Ontology: Custom scientific_presentation_ontology.ttl (OWL/RDF)

Enjoy using the Presentology Agent!
