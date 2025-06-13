import React, { useState, type FormEvent, useRef, useEffect, type KeyboardEvent, useCallback } from 'react';
import { Send, Loader2, Network, MessageSquareText, Search } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

// Define types for the messages in the chat history
interface ChatMessage {
  type: 'user' | 'agent' | 'error';
  text: string;
  timestamp: string;
  isSuggested?: boolean;
  sparqlQuery?: string;
  rawQueryResults?: any[];
  addedTriples?: string; // Still useful to show the triples added by the agent
}

// Define the response structure from our Flask backend for query
interface AgentQueryResponse {
  user_prompt: string;
  sparql_query: string;
  raw_query_results: any[];
  agent_response: string;
  added_triples?: string; // Backend now sends this if data was generated
}

// Define types for graph data
interface GraphNode {
  id: string;
  name: string;
  isLiteral?: boolean;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

function App() {
  const [prompt, setPrompt] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showGraph, setShowGraph] = useState<boolean>(false);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [graphDataLoading, setGraphDataLoading] = useState<boolean>(false);
  const [graphDataError, setGraphDataError] = useState<string | null>(null);

  const suggestedQuestions = [
    "Which standard presentation sections should be included for Artificial Intelligence?",
    "What is the recommended order of sections for the 'Methodology of our biochemical engineering system' section?",
    "Which quality indicators demonstrate scientific accuracy in data presentation and interpretation?"
  ];

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const fgRef = useRef<any>();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const nodeCanvasCallback = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    // Defensive check: Ensure ctx is a valid rendering context
    if (!ctx || typeof ctx.fillRect !== 'function') {
      console.warn("Invalid CanvasRenderingContext2D received in nodeCanvasCallback.");
      return;
    }

    const label = node.name;
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Inter`;
    const textWidth = ctx.measureText(label).width;
    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.4);

    ctx.fillStyle = node.isLiteral ? '#A9A9A9' : '#007bff';
    ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = node.isLiteral ? '#000000' : '#FFFFFF';
    ctx.fillText(label, node.x, node.y);

    node.__bckgDimensions = bckgDimensions;
  }, []);

  const nodePointerAreaPaint = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    // Defensive check: Ensure ctx is a valid rendering context
    if (!ctx || typeof ctx.fillRect !== 'function') {
      console.warn("Invalid CanvasRenderingContext2D received in nodePointerAreaPaint.");
      return;
    }

    ctx.fillStyle = 'rgba(0, 0, 0, 0.0)';
    const bckgDimensions = node.__bckgDimensions;
    bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
  }, []);

  const handleSubmit = async (event?: FormEvent, suggestedText?: string) => {
    event?.preventDefault();

    const currentPrompt = suggestedText || prompt;
    if (!currentPrompt.trim()) return;

    const userMessage: ChatMessage = {
      type: 'user',
      text: currentPrompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSuggested: !!suggestedText
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setPrompt('');

    setIsLoading(true);

    try {
      const res = await fetch('http://127.0.0.1:5000/query', { // Always call /query
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: currentPrompt }), // Send full prompt
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `HTTP error! Status: ${res.status}`);
      }

      const data: AgentQueryResponse = await res.json();
      setMessages(prevMessages => [...prevMessages, {
        type: 'agent',
        text: data.agent_response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sparqlQuery: data.sparql_query,
        rawQueryResults: data.raw_query_results,
        addedTriples: data.added_triples // Capture added triples if present
      }]);

    } catch (err: any) {
      console.error("Failed to communicate with backend:", err);
      setMessages(prevMessages => [...prevMessages, {
        type: 'error',
        text: err.message || "An unexpected error occurred. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    if (!isLoading) {
      setPrompt(question);
      handleSubmit(undefined, question);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  const fetchGraphDataAndShow = async () => {
    setGraphDataError(null);
    setGraphDataLoading(true);
    setShowGraph(true);

    try {
      const res = await fetch('http://127.0.0.1:5000/get_graph_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `HTTP error! Status: ${res.status}`);
      }

      const data: GraphData = await res.json();
      setGraphData(data);
    } catch (err: any) {
      console.error("Failed to fetch graph data:", err);
      setGraphDataError(err.message || "Could not load graph data. Please try again.");
      setGraphData(null);
    } finally {
      setGraphDataLoading(false);
    }
  };

  const handleHideGraph = () => {
    setShowGraph(false);
    setGraphData(null);
    setGraphDataError(null);
    setGraphDataLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100 p-4 font-inter">
      <div className={`bg-white p-6 rounded-2xl shadow-xl border border-gray-200 w-full flex ${showGraph ? 'max-w-screen-xl grid grid-cols-2 gap-6' : 'max-w-3xl flex-col h-[85vh] min-h-[500px]'}`}>
        {messages.length === 0 && (
          <div className="flex justify-center flex-shrink-0">
            <img
              src="/public/presontology.png"
              alt="Presontology Agent Logo"
              className="h-[300px] w-auto rounded-lg"
            />
          </div>
        )}

        {showGraph && (
          <div className="flex flex-col items-center justify-center bg-gray-50 rounded-xl p-4 border border-gray-200 h-full overflow-hidden">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex-shrink-0">Knowledge Graph Visualization</h2>
            {graphDataLoading && (
              <div className="flex items-center justify-center flex-grow text-indigo-600">
                <Loader2 className="animate-spin h-8 w-8 mr-2" />
                <span>Loading graph data...</span>
              </div>
            )}
            {graphDataError && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-4 flex-grow flex items-center justify-center text-center">
                <Search className="h-5 w-5 mr-2" />
                <span>{graphDataError}</span>
              </div>
            )}
            {graphData && !graphDataLoading && !graphDataError && (
              <div className="flex-grow w-full">
                <ForceGraph2D
                  ref={fgRef}
                  graphData={graphData}
                  nodeId="id"
                  nodeLabel="name"
                  linkSource="source"
                  linkTarget="target"
                  linkLabel="label"
                  linkDirectionalArrowLength={3.5}
                  linkDirectionalArrowRelPos={1}
                  nodeCanvasObject={nodeCanvasCallback}
                  nodeCanvasObjectMode={() => 'after'}
                  nodePointerAreaPaint={nodePointerAreaPaint}
                  width={showGraph ? window.innerWidth * 0.45 : 0}
                  height={showGraph ? window.innerHeight * 0.7 : 0}
                  enableZoomPan={true}
                  d3AlphaDecay={0.04}
                  d3VelocityDecay={0.2}
                  onNodeClick={(node: any) => {
                    const distance = 100;
                    const distRatio = 1 + distance / Math.hypot(node.x, node.y);
                    fgRef.current.cameraPosition(
                      { x: node.x * distRatio, y: node.y * distRatio, z: fgRef.current.cameraPosition().z },
                      node,
                      1000
                    );
                  }}
                />
              </div>
            )}
            <button
              onClick={handleHideGraph}
              className="mt-4 px-6 py-3 bg-black text-white font-semibold rounded-lg shadow-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 transition duration-200"
            >
              <MessageSquareText className="inline-block h-5 w-5 mr-2" /> Hide Graph & Show Chat
            </button>
          </div>
        )}

        <div className={`flex flex-col h-[85vh] min-h-[500px]`}>
          {messages.length > 0 && (
            <h1 className="text-4xl font-extrabold text-center text-indigo-800 mb-6 flex-shrink-0">
              <span role="img" aria-label="brain" className="mr-2">🧠</span> Presontology Agent
            </h1>
          )}

          {messages.length === 0 && !isLoading && !showGraph && (
            <div className="flex-shrink-0 mb-6 px-4 py-3 border border-gray-300 rounded-xl bg-transparent space-y-3">
              <p className="text-gray-700 font-semibold text-sm">Suggested questions:</p>
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestionClick(question)}
                  className="w-full text-left p-2 rounded-md bg-white hover:bg-gray-200 transition duration-150 text-gray-800 text-sm border border-gray-200"
                  disabled={isLoading}
                >
                  {question}
                </button>
              ))}
            </div>
          )}

          <div className="flex-grow overflow-y-auto px-4 mb-4 space-y-4 py-2">
            {messages.length === 0 && !isLoading && !showGraph ? null : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] p-3 rounded-lg shadow-md relative ${msg.type === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-xl'
                      : 'bg-gray-200 text-gray-800 rounded-bl-xl' // Agent and error messages now share default gray
                      }`}
                  >
                    <p className="whitespace-pre-wrap pb-4">{msg.text}</p>
                    <span className={`absolute bottom-1 text-xs ${msg.type === 'user' ? 'right-2 text-indigo-200' : 'left-2 text-gray-500'
                      }`}>
                      {msg.timestamp}
                    </span>
                    {msg.type === 'user' && (
                      <div className="absolute bottom-0 right-[-10px] w-0 h-0 border-solid border-transparent border-t-[10px] border-l-[10px] border-b-[10px] border-t-indigo-600"></div>
                    )}
                    {(msg.type !== 'user') && (
                      <div className={`absolute bottom-0 left-[-10px] w-0 h-0 border-solid border-transparent border-t-[10px] border-r-[10px] border-b-[10px] border-t-gray-200`}></div>
                    )}
                    {/* Display query path for agent messages */}
                    {msg.type === 'agent' && (msg.sparqlQuery || msg.rawQueryResults || msg.addedTriples) && (
                      <details className="mb-4 text-sm text-gray-600">
                        <summary className="cursor-pointer font-medium text-blue-700 hover:text-blue-900">
                          Details
                        </summary>
                        <div className="mt-2 space-y-2 bg-blue-100 p-4 rounded-md">
                          {msg.sparqlQuery && (
                            <div className="block"> {/* Changed <p> to <div> */}
                              <strong className="text-blue-800">Generated SPARQL:</strong>
                              <pre className="bg-gray-100 p-2 rounded-md text-xs mt-1 whitespace-pre-wrap overflow-x-auto">
                                {msg.sparqlQuery}
                              </pre>
                            </div>
                          )}
                          {msg.rawQueryResults && (
                            <div className="block"> {/* Changed <p> to <div> */}
                              <strong className="text-blue-800">Raw Results:</strong>
                              <pre className="bg-gray-100 p-2 rounded-md text-xs mt-1 whitespace-pre-wrap overflow-x-auto">
                                {JSON.stringify(msg.rawQueryResults, null, 2)}
                              </pre>
                            </div>
                          )}
                          {msg.addedTriples && (
                            <div className="block"> {/* Changed <p> to <div> */}
                              <strong className="text-blue-800">Dynamically Added RDF (Turtle):</strong>
                              <pre className="bg-gray-100 p-2 rounded-md text-xs mt-1 whitespace-pre-wrap overflow-x-auto">
                                {msg.addedTriples}
                              </pre>
                            </div>
                          )}
                          {/* New button to trigger graph visualization if data was added */}
                          {msg.addedTriples && (
                            <button
                              onClick={fetchGraphDataAndShow}
                              className="mt-2 px-4 py-2 bg-indigo-700 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 transition duration-200 text-sm"
                            >
                              <Network className="inline-block h-4 w-4 mr-1" /> Show Graph
                            </button>
                          )}
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 p-3 rounded-lg rounded-bl-xl shadow-md flex items-center space-x-2">
                  <Loader2 className="animate-spin h-5 w-5 text-indigo-600" />
                  <span>Agent is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="flex gap-4 flex-shrink-0 px-4 relative">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              rows={3}
              className="flex-1 p-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-200 resize-none overflow-hidden"
              disabled={isLoading}
              style={{ minHeight: '80px' }}
            />
            <button
              type="submit"
              className="absolute right-7 bottom-7 w-8 h-8 flex items-center justify-center bg-black text-white rounded-full shadow-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading || !prompt.trim()}
              aria-label="Send message"
            >
              {isLoading ? <Loader2 className="animate-spin h-4 w-4" /> : <Send className="h-4 w-4" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
