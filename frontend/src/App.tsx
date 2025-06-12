import React, { useState, type FormEvent } from 'react';
// No need to import './App.css' if you're not using it.
// Vite React templates usually come with App.css, but we'll rely on index.css for global Tailwind.

// Define a type for the response structure from our Flask backend
interface AgentResponse {
  user_prompt: string;
  sparql_query: string;
  raw_query_results: any[]; // Using any[] for now as results can vary
  agent_response: string;
}

function App() {
  // State variables for managing user input, agent response, loading, and errors
  const [prompt, setPrompt] = useState<string>(''); // Stores the user's input
  const [response, setResponse] = useState<AgentResponse | null>(null); // Stores the agent's response
  const [isLoading, setIsLoading] = useState<boolean>(false); // Tracks loading state
  const [error, setError] = useState<string | null>(null); // Stores any error messages

  // Function to handle form submission
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault(); // Prevent default form submission behavior (page reload)
    setError(null); // Clear previous errors
    setResponse(null); // Clear previous responses
    setIsLoading(true); // Set loading state to true

    try {
      // Make a POST request to our Flask backend's /query endpoint
      const res = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Send the user's prompt in the request body as JSON
        body: JSON.stringify({ prompt }),
      });

      // Check if the request was successful (status code 2xx)
      if (!res.ok) {
        // If not successful, throw an Error with the status
        const errorData = await res.json(); // Try to parse error message from backend
        throw new Error(errorData.error || `HTTP error! Status: ${res.status}`);
      }

      // Parse the JSON response from the backend
      const data: AgentResponse = await res.json();
      setResponse(data); // Update the response state
    } catch (err: any) {
      // Catch any errors during the fetch or parsing process
      console.error("Failed to fetch from backend:", err);
      setError(err.message || "An unexpected error occurred. Please try again."); // Set the error state
    } finally {
      setIsLoading(false); // Set loading state back to false
    }
  };

  return (
    // Main container for the application, taking full screen height and using flex for centering
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100 p-4">
      {/* Card-like container for the chat interface */}
      <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-200 w-full max-w-2xl">
        <h1 className="text-4xl font-extrabold text-center text-indigo-800 mb-6">
          <span role="img" aria-label="brain" className="mr-2">🧠</span> AI Knowledge Graph Agent
        </h1>

        {/* Input form for user queries */}
        <form onSubmit={handleSubmit} className="flex gap-4 mb-6">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)} // Update prompt state on input change
            placeholder="e.g., Who wrote the book '1984'?"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-200"
            disabled={isLoading} // Disable input while loading
          />
          <button
            type="submit"
            className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading} // Disable button while loading
          >
            {isLoading ? 'Sending...' : 'Ask Agent'}
          </button>
        </form>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center justify-center space-x-2 text-indigo-600">
            <svg className="animate-spin h-5 w-5 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Processing your query...</span>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-4" role="alert">
            <strong className="font-bold">Error:</strong>
            <span className="block sm:inline ml-2">{error}</span>
          </div>
        )}

        {/* Response Display Area */}
        {response && (
          <div className="mt-6 p-6 bg-blue-50 rounded-lg shadow-inner border border-blue-200">
            <h2 className="text-xl font-semibold text-blue-800 mb-3">Agent's Response:</h2>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {response.agent_response}
            </p>

            {/* Optional: Show raw SPARQL and results for debugging/transparency */}
            <details className="mt-4 text-sm text-gray-600">
              <summary className="cursor-pointer font-medium text-blue-700 hover:text-blue-900">
                Show Raw Details (for debugging)
              </summary>
              <div className="mt-2 space-y-2 bg-blue-100 p-4 rounded-md">
                <p>
                  <strong className="text-blue-800">User Prompt:</strong> {response.user_prompt}
                </p>
                <p>
                  <strong className="text-blue-800">Generated SPARQL:</strong>
                  <pre className="bg-gray-100 p-2 rounded-md text-xs mt-1 whitespace-pre-wrap overflow-x-auto">
                    {response.sparql_query}
                  </pre>
                </p>
                <p>
                  <strong className="text-blue-800">Raw Results:</strong>
                  <pre className="bg-gray-100 p-2 rounded-md text-xs mt-1 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(response.raw_query_results, null, 2)}
                  </pre>
                </p>
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
