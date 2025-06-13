AI Knowledge Graph Agent Web Application

This repository contains the code for an AI agentic web application designed to query a Turtle knowledge graph using natural language prompts. The agent will interpret user queries, translate them into knowledge graph queries, execute them, and then provide human-understandable responses based on the results.
Project Overview

The Goal of this project is to create an intuitive interface for users to interact with structured knowledge without needing expertise in graph query languages (like SPARQL).
Key Features

    Natural Language Understanding: Agent understands user prompts.

    Knowledge Graph Querying: Agent generates and executes queries against a Turtle knowledge graph.

    Intelligent Response Generation: Agent synthesizes query results into human-readable answers.

    Responsive Web Interface: User-friendly web application accessible on various devices.

    Interactive Chat History: Displays a conversation flow between the user and the AI agent, with distinct styling for user queries and agent responses (including rounded bubbles and triangle tails).

    Modern UI/UX: Utilizes lucide-react for sleek icons, a multi-line input text area, and chatbot-style bubble messages for a modern, intuitive chat experience. The UI is constrained to a maximum width for a cleaner look.

    Suggested Questions: Provides initial clickable questions to guide the user and kickstart the conversation.

    Integrated Send Button: The send button is now visually integrated within the text input area.

    Knowledge Graph Visualization: Ability to dynamically generate and display a visual representation of the underlying knowledge graph using an AI image generation model, with a toggle to show/hide the visualization.

Technology Stack

    Frontend: React (JavaScript library for building user interfaces) with Vite and Tailwind CSS for styling, and lucide-react for icons.

    Backend: Python (for AI logic, API, and knowledge graph interaction).

    AI/LLM: Google Gemini API (gemini-2.0-flash) for natural language understanding and response generation.

    Image Generation: Google Imagen API (imagen-3.0-generate-002) for visualizing the knowledge graph.

    Knowledge Graph Processing: rdflib (Python library for RDF/Turtle parsing and querying).

    API Framework: Flask (Python micro-framework for backend API).

Getting Started

Follow these instructions to set up the project locally.
Prerequisites

    Node.js 18.x or 20.x (LTS version recommended) and npm/yarn

    Python 3.9+ (Important: google-generativeai>=0.3.0 requires Python 3.9 or higher)

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

3. Frontend Setup (Using Vite)

Navigate into the frontend directory to set up the React application with Vite.

cd frontend

# 3.1. Initialize a new React project with Vite
# When prompted for 'Package name', press Enter.
# When prompted for 'Install dependencies?', type 'y' and press Enter.
npm create vite@latest . -- --template react-ts

# 3.2. Install Tailwind CSS (pinned to a stable v3) and its Vite plugin, Autoprefixer, and Lucide React icons
npm install -D tailwindcss@3.4.4 @tailwindcss/vite autoprefixer
npm install lucide-react # Install lucide-react for icons

# 3.3. Update package.json to include tailwindcss init script
# Open frontend/package.json and ensure the "scripts" section includes:
# "scripts": {
#   "dev": "vite",
#   "build": "tsc && vite build",
#   "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
#   "preview": "vite preview",
#   "tailwind-init": "tailwindcss init"  # ADD THIS LINE IF NOT PRESENT
# },
# And ensure "tailwindcss": "3.4.4", "postcss", "autoprefixer" are in "devDependencies".

# 3.4. Initialize Tailwind CSS Configuration Files (if not already created)
# Run the newly added script:
npm run tailwind-init

# 3.5. Create/Update postcss.config.cjs
# Create a file named 'postcss.config.cjs' (note the .cjs extension)
# in the 'frontend' root directory with the following content:
# module.exports = {
#   plugins: {
#     tailwindcss: {},
#     autoprefixer: {},
#   },
# };

# 3.6. Configure tailwind.config.js
# Open frontend/tailwind.config.js and update the 'content' array:
# /** @type {import('tailwindcss').Config} */
# export default {
#   content: [
#     "./index.html",
#     "./src/**/*.{js,ts,jsx,tsx}",
#   ],
#   theme: {
#     extend: {},
#   },
#   plugins: [],
# }

# 3.7. Configure vite.config.ts
# Open frontend/vite.config.ts and add the tailwindcss plugin, and explicit PostCSS configuration:
# import { defineConfig } from 'vite'
# import react from '@vitejs/plugin-react-swc'
# import tailwindcss from '@tailwindcss/vite'
#
# export default defineConfig({
#   plugins: [
#     react(),
#     tailwindcss(),
#   ],
#   css: {
#     postcss: {
#       plugins: [
#         require('tailwindcss'),
#         require('autoprefixer'),
#       ],
#     },
#   },
# })

# 3.8. Import Tailwind CSS into src/index.css
# Open frontend/src/index.css and replace its content with:
# @import "tailwindcss/base";
# @import "tailwindcss/components";
# @import "tailwindcss/utilities";
#
# body {
#   font-family: 'Inter', sans-serif;
#   margin: 0;
#   padding: 0;
#   box-sizing: border-box;
#   -webkit-font-smoothing: antialiased;
#   -moz-osx-font-smoothing: grayscale;
# }

4. Backend Setup

Navigate into the backend directory, create a virtual environment, and install dependencies.

cd backend

# 4.1. Create Knowledge Graph Data File
# Create a file named 'presentation_data.ttl' in the 'backend' directory
# and populate it with your sample knowledge graph data.
# (The complete presentation_data.ttl content is provided separately in the project conversation flow.)

# 4.2. Create/Place Ontology File
# Ensure 'good_presentation_ontology.ttl' is in the 'backend' directory.
# (The complete good_presentation_ontology.ttl content is provided separately in the project conversation flow.)

# 4.3. Create and Activate a Python Virtual Environment
python3 -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows (Command Prompt):
# venv\Scripts\activate.bat
# On Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

# 4.4. Install Required Python Packages
# IMPORTANT: Ensure google-generativeai is version 0.3.0 or higher for GenerativeModel
pip install Flask Flask-Cors rdflib python-dotenv "google-generativeai>=0.3.0"

# 4.5. Generate requirements.txt
pip freeze > requirements.txt

# 4.6. Set up Gemini API Key
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

Interpreting Logs:

The console output from app.py will now include structured log messages with timestamps, the logger name (__main__), the log level (e.g., INFO, ERROR), and the message itself. Pay close attention to INFO messages, especially those containing Raw LLM response text: for both query generation and response synthesis, and messages about image generation, as this will show you exactly what the APIs are returning at each stage.

Testing the Backend Agent (Command Line/cURL/Postman):

You can still use curl or Postman to test the backend directly. The response will now include the user_prompt, the sparql_query generated by the LLM, the raw_query_results from the knowledge graph, and most importantly, the human-readable agent_response synthesized by the LLM. You can also test the new /generate_graph_image endpoint.
2. Run the Frontend Application

Important: Make sure your backend server is running in a separate terminal before starting the frontend.

cd frontend
npm run dev

The frontend application will typically open in your browser at http://localhost:5173 (Vite's default port). You can now type your natural language questions into the input field or click on the suggested questions to interact with your AI agent! The UI will now display a full chat history, and you'll have buttons to toggle the graph visualization.
Contributing

(Guidelines for contributions will be added here)
License

(License information will be added here)