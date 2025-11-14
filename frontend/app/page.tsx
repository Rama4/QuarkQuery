"use client";

import { useState } from "react";
import {
  SearchIcon,
  SparklesIcon,
  BookOpenIcon,
  ArrowRightIcon,
} from "./components/icons";
import { StatusPanel } from "./components/StatusPanel";
import { MarkdownRenderer } from "./components/MarkdownRenderer";

interface Source {
  arxiv_id: string;
  title: string;
  text: string;
  score: number;
}

interface QueryResponse {
  answer: string;
  sources: Source[];
  question: string;
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exampleQuestions = [
    "What is the AdS/CFT correspondence?",
    "Explain the KKLT construction for de Sitter vacua",
    "What are the main ideas behind extra dimensions at a millimeter?",
    "Describe the Randall-Sundrum model",
    "What is the swampland program in string theory?",
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to get response");
      }

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuestion: string) => {
    setQuestion(exampleQuestion);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative bg-[#0a0a0a] overflow-hidden">
        {/* Abstract Pattern Background */}
        <div className="absolute inset-0 opacity-40">
          <svg
            className="w-full h-full"
            viewBox="0 0 1200 600"
            preserveAspectRatio="xMidYMid slice"
            xmlns="http://www.w3.org/2000/svg"
          ></svg>
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-24">
          <h1 className="text-hero-h1 mb-4">
            QuarkQuery
          </h1>
          <div className="flex items-center gap-2">
            <p className="text-subtitle">
              RAG for answering questions related to theoretical physics
            </p>
          </div>
        </div>
      </section>

      {/* Query Interface Section */}
      <section className="bg-white py-16 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          {/* Search Section */}
          <div className="mb-8">
            <form onSubmit={handleSubmit} className="relative">
              <div className="relative">
                <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about physics..."
                  className="text-body w-full pl-12 pr-32 py-4 rounded-xl border border-gray-300 focus:border-black focus:ring-2 focus:ring-gray-200 outline-none transition-all text-black placeholder:text-gray-400 bg-white shadow-sm"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="btn-primary absolute right-2 top-1/2 -translate-y-1/2 gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <span>Ask</span>
                      <ArrowRightIcon className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Example Questions */}
            {!response && (
              <div className="mt-6">
                <p className="text-body text-sm mb-3 font-medium opacity-70">
                  Try these examples:
                </p>
                <div className="flex flex-wrap gap-2">
                  {exampleQuestions.map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleExampleClick(example)}
                      className="btn-primary text-body"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-800 font-medium">Error: {error}</p>
              <p className="text-red-600 text-sm mt-1">
                Please make sure your API keys are configured correctly.
              </p>
            </div>
          )}

          {/* Response Section */}
          {response && (
            <div className="space-y-6">
              {/* Answer */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center shrink-0">
                    <SparklesIcon className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-h3 mb-2">
                      Answer
                    </h2>
                    <div className="prose prose-slate max-w-none">
                      <MarkdownRenderer content={response.answer} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Sources */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <BookOpenIcon className="w-5 h-5 text-black" />
                  <h2 className="text-h3">
                    Sources ({response.sources.length})
                  </h2>
                </div>
                <div className="space-y-3">
                  {response.sources.map((source, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-400 transition-all"
                    >
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex-1">
                          <h3 className="text-h3 mb-1">
                            {source.title}
                          </h3>
                          <p className="text-body text-xs opacity-70">
                            arXiv: {source.arxiv_id} • Relevance:{" "}
                            {(source.score * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-body text-sm">
                        <MarkdownRenderer content={source.text} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Status Panel - Floating button in bottom-right */}
      <StatusPanel />
    </div>
  );
}
