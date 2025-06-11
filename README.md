AI Knowledge Graph Agent Web Application

This repository contains the code for an AI agentic web application designed to query a Turtle knowledge graph using natural language prompts. The agent will interpret user queries, translate them into knowledge graph queries, execute them, and then provide human-understandable responses based on the results.
Project Overview

The goal of this project is to create an intuitive interface for users to interact with structured knowledge without needing expertise in graph query languages (like SPARQL).
Key Features (Planned)

    Natural Language Understanding: Agent understands user prompts.

    Knowledge Graph Querying: Agent generates and executes queries against a Turtle knowledge graph.

    Intelligent Response Generation: Agent synthesizes query results into human-readable answers.

    Responsive Web Interface: User-friendly web application accessible on various devices.

Technology Stack

    Frontend: React (JavaScript library for building user interfaces) with Tailwind CSS for styling.

    Backend: Python (for AI logic, API, and knowledge graph interaction).

    AI/LLM: Google Gemini API (gemini-2.0-flash) for natural language understanding and response generation.

    Knowledge Graph Processing: rdflib (Python library for RDF/Turtle parsing and querying).

    API Framework: Flask (Python micro-framework for backend API).

Getting Started

Follow these instructions to set up the project locally.
Prerequisites

    Node.js (LTS version recommended) and npm/yarn

    Python 3.8+

    Git

1. Clone the Repository

git clone <repository-url> # Replace with your actual repository URL
cd ai-kg-agent-app

2. Project Structure

ai-kg-agent-app/
├── frontend/             # React web application
├── backend/              # Python backend API and AI agent logic
├── .gitignore            # Specifies intentionally untracked files to ignore
└── README.md             # Project documentation

3. Frontend Setup

Navigate into the frontend directory and install dependencies.

cd frontend
# Instructions will be added here soon for React setup

4. Backend Setup

Navigate into the backend directory, create a virtual environment, and install dependencies.

cd backend

# 4.1. Create a Sample Knowledge Graph
# Create a file named 'knowledge_graph.ttl' inside the backend directory
# and populate it with your Turtle data.
# Example content for knowledge_graph.ttl (to be saved in backend/knowledge_graph.ttl):
# (Content for knowledge_graph.ttl is provided separately in the project conversation flow.)

# 4.2. Create and Activate a Python Virtual Environment
python3 -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (Command Prompt):
# venv\Scripts\activate.bat
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# 4.3. Install Required Python Packages
pip install Flask Flask-Cors rdflib python-dotenv google-generativeai

# 4.4. Generate requirements.txt
pip freeze > requirements.txt

# 4.5. Set up Gemini API Key
# Create a file named '.env' in the 'backend' directory (same level as knowledge_graph.ttl)
# and add your Gemini API key:
# GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
# Remember to replace "YOUR_GEMINI_API_KEY_HERE" with your actual API key.

Usage
1. Run the Backend Server

Ensure you are in the backend directory and your virtual environment is active.

cd backend
source venv/bin/activate # or your platform's equivalent activation command
python app.py

The backend server will start on http://127.0.0.1:5000/ (or localhost:5000). You should see output indicating the Flask server is running and the knowledge graph has been loaded.
2. Run the Frontend Application

(Instructions on how to run the frontend will be added here)
Contributing

(Guidelines for contributions will be added here)
License

(License information will be added here)