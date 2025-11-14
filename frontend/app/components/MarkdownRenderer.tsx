"use client";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p: ({ node, ...props }) => <p className="text-body mb-4 last:mb-0" {...props} />,
          h1: ({ node, ...props }) => <h1 className="text-h2 mb-4 mt-6 first:mt-0" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-h2 mb-3 mt-5 first:mt-0" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-h3 mb-2 mt-4 first:mt-0" {...props} />,
          ul: ({ node, ...props }) => <ul className="text-body list-disc list-inside mb-4 space-y-1" {...props} />,
          ol: ({ node, ...props }) => <ol className="text-body list-decimal list-inside mb-4 space-y-1" {...props} />,
          li: ({ node, ...props }) => <li className="text-body" {...props} />,
          code: ({ node, inline, ...props }: any) => {
            if (inline) {
              return (
                <code className="text-body bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
              );
            }
            return (
              <code className="text-body block bg-gray-100 p-3 rounded overflow-x-auto mb-4" {...props} />
            );
          },
          blockquote: ({ node, ...props }) => (
            <blockquote className="text-body border-l-4 border-gray-300 pl-4 italic my-4" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

