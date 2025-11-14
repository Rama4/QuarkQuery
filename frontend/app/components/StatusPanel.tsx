"use client";

import { useState, useEffect } from "react";

// Simple SVG icons
const CheckCircle2 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XCircle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const AlertCircle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const RefreshCw = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

interface ServiceStatus {
  status: string;
  message?: string;
  [key: string]: any;
}

interface StatusData {
  timestamp: string;
  services: {
    pinecone: ServiceStatus;
    huggingface: ServiceStatus;
    groq: ServiceStatus;
  };
}

export function StatusPanel() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error("Failed to fetch status");
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !status) {
      fetchStatus();
    }
  }, [isOpen]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case "error":
      case "not_configured":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "rate_limited":
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-50 border-green-200";
      case "error":
      case "not_configured":
        return "text-red-600 bg-red-50 border-red-200";
      case "rate_limited":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="mb-2 px-4 py-2 bg-indigo-600 text-white rounded-lg shadow-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
      >
        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        API Status
      </button>

      {/* Status Panel */}
      {isOpen && (
        <div className="bg-white rounded-lg shadow-2xl border border-gray-200 p-6 w-96 max-h-[80vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">Service Status</h2>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {status && (
            <>
              <div className="text-xs text-gray-500 mb-4">
                Last updated: {new Date(status.timestamp).toLocaleTimeString()}
              </div>

              {/* Pinecone Status */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(status.services.pinecone.status)}
                  <h3 className="font-semibold text-gray-900">
                    Pinecone (Vector DB)
                  </h3>
                </div>
                <div
                  className={`p-3 rounded-lg border text-sm ${getStatusColor(
                    status.services.pinecone.status
                  )}`}
                >
                  {status.services.pinecone.status === "active" ? (
                    <>
                      <div className="font-medium mb-1">✓ Connected</div>
                      <div className="text-xs opacity-75">
                        Index: {status.services.pinecone.index}
                      </div>
                      <div className="text-xs opacity-75">
                        Vectors: {status.services.pinecone.totalVectors?.toLocaleString()}
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        {status.services.pinecone.message}
                      </div>
                    </>
                  ) : (
                    <div>{status.services.pinecone.message}</div>
                  )}
                </div>
              </div>

              {/* HuggingFace Status */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(status.services.huggingface.status)}
                  <h3 className="font-semibold text-gray-900">
                    HuggingFace (Embeddings)
                  </h3>
                </div>
                <div
                  className={`p-3 rounded-lg border text-sm ${getStatusColor(
                    status.services.huggingface.status
                  )}`}
                >
                  {status.services.huggingface.status === "active" ? (
                    <>
                      <div className="font-medium mb-1">✓ Active</div>
                      <div className="text-xs opacity-75">
                        Model: {status.services.huggingface.model}
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        {status.services.huggingface.message}
                      </div>
                      {status.services.huggingface.rateLimits && (
                        <div className="text-xs opacity-75 mt-1">
                          {status.services.huggingface.rateLimits.typical}
                        </div>
                      )}
                    </>
                  ) : (
                    <div>{status.services.huggingface.message}</div>
                  )}
                </div>
              </div>

              {/* Groq Status */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(status.services.groq.status)}
                  <h3 className="font-semibold text-gray-900">Groq (LLM)</h3>
                </div>
                <div
                  className={`p-3 rounded-lg border text-sm ${getStatusColor(
                    status.services.groq.status
                  )}`}
                >
                  {status.services.groq.status === "active" ? (
                    <>
                      <div className="font-medium mb-1">✓ Active</div>
                      <div className="text-xs opacity-75">
                        Model: {status.services.groq.model}
                      </div>
                      <div className="text-xs opacity-75 mt-1">
                        {status.services.groq.message}
                      </div>
                      {status.services.groq.rateLimits && (
                        <div className="text-xs opacity-75 mt-1 space-y-0.5">
                          <div>• {status.services.groq.rateLimits.daily}</div>
                          <div>
                            • {status.services.groq.rateLimits.perMinute}
                          </div>
                          <div>• {status.services.groq.rateLimits.tokens}</div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div>{status.services.groq.message}</div>
                  )}
                </div>
              </div>

              {/* Overall Summary */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500">
                  <strong>Free Tier Limits:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Pinecone: 1 index, 100K vectors</li>
                    <li>HuggingFace: ~1K requests/hour</li>
                    <li>Groq: 14.4K requests/day</li>
                  </ul>
                </div>
              </div>
            </>
          )}

          {!status && !loading && !error && (
            <div className="text-center text-gray-500 py-8">
              Click refresh to check status
            </div>
          )}
        </div>
      )}
    </div>
  );
}

