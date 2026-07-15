"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Database, RefreshCw, Sparkles, Zap, Command } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

type IndexStatus = "idle" | "cloning" | "indexing" | "done" | "error";

export function Chat() {
  const { user } = useAuth();
  const [repo, setRepo] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [indexStatus, setIndexStatus] = useState<IndexStatus>("idle");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleIndexRepo = async (repoValue: string) => {
    if (!user) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "🔐 Please sign in with GitHub first." },
      ]);
      return;
    }

    const [owner, repoName] = repoValue.split("/");
    if (!owner || !repoName) return;

    setIndexStatus("cloning");

    try {
      const res = await fetch(`${API_URL}/api/chat/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ owner, repo: repoName }),
      });

      const data = await res.json();

      if (data.status === "success") {
        setIndexStatus("done");
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `✨ **${repoValue}** indexed successfully!\n\n• ${data.message || "Code + commit history ready"}\n\nAsk me anything about this repository.`,
          },
        ]);
      } else {
        setIndexStatus("error");
        setMessages((prev) => [
          ...prev,
          { role: "system", content: `❌ ${data.detail || "Failed to index"}` },
        ]);
      }
    } catch {
      setIndexStatus("error");
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const repoMatch = input.trim().match(/^([\w.-]+)\/([\w.-]+)$/);
    if (repoMatch && !repo) {
      const repoValue = input.trim();
      setRepo(repoValue);
      setInput("");
      setMessages((prev) => [...prev, { role: "user", content: repoValue }]);
      await handleIndexRepo(repoValue);
      return;
    }

    if (!repo) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "👋 **Welcome to RepoX!**\n\nEnter a GitHub repository to begin:\n`owner/repo-name`" },
      ]);
      setInput("");
      return;
    }

    const [owner, repoName] = repo.split("/");
    const question = input;

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
    setLoading(true);

    const assistantMessage: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const res = await fetch(`${API_URL}/api/chat/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ owner, repo: repoName, question }),
      });

      if (!res.ok) {
        const error = await res.json();
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "system",
            content: `❌ ${error.detail || "Failed to get response"}`,
          };
          return updated;
        });
        setLoading(false);
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value, { stream: true });
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, content: last.content + text };
            return updated;
          });
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "system",
          content: "❌ Connection error. Is the backend running?",
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getWelcomeMessage = () => {
    if (user) {
      return `Welcome, **${user.login}** 👋\n\nEnter a GitHub repo to analyze:\n\n\`tiangolo/fastapi\`\n\`donnemartin/system-design-primer\`\n\`kamranahmedse/developer-roadmap\``;
    }
    return "Welcome to **RepoX** 🚀\n\nSign in with GitHub to start analyzing repositories.";
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Repo badge */}
      {repo && (
        <div className="border-b border-zinc-800/50 bg-zinc-900/30 backdrop-blur-sm px-4 py-2">
          <div className="max-w-3xl mx-auto flex items-center gap-2.5 text-sm">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-zinc-400 font-medium">Repository</span>
            <span className="text-white font-semibold">{repo}</span>
            <button
              onClick={() => {
                setRepo("");
                setIndexStatus("idle");
                setMessages([]);
              }}
              className="ml-auto p-1 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 rounded-md transition-all"
              title="Change repository"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Indexing progress */}
      {(indexStatus === "cloning" || indexStatus === "indexing") && (
        <div className="bg-gradient-to-r from-emerald-500/5 via-emerald-500/10 to-emerald-500/5 border-b border-emerald-500/10 px-4 py-4">
          <div className="max-w-3xl mx-auto flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-emerald-300">
                {indexStatus === "cloning" ? "Cloning repository..." : "Indexing files..."}
              </p>
              <p className="text-xs text-emerald-400/50 mt-0.5">
                {indexStatus === "cloning"
                  ? "Downloading code and commit history"
                  : "Creating embeddings for search"}
              </p>
            </div>
            <div className="w-28 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 mb-6">
                <Zap className="w-8 h-8 text-emerald-400" />
              </div>
              <div className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap max-w-md mx-auto">
                {getWelcomeMessage()}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-gradient-to-br from-emerald-600 to-emerald-700 text-white shadow-lg shadow-emerald-900/20"
                    : msg.role === "system"
                    ? "bg-zinc-800/30 border border-zinc-700/30 text-zinc-300"
                    : `bg-zinc-800/50 border border-zinc-700/30 text-zinc-200 message-content ${
                        loading && i === messages.length - 1 ? "streaming-cursor" : ""
                      }`
                }`}
              >
                {/* Render markdown-like bold */}
                {msg.content.split(/(\*\*.*?\*\*)/).map((part, j) =>
                  part.startsWith("**") && part.endsWith("**") ? (
                    <strong key={j} className="text-white font-semibold">
                      {part.slice(2, -2)}
                    </strong>
                  ) : (
                    <span key={j}>{part}</span>
                  )
                )}
              </div>
            </div>
          ))}

          {loading && messages[messages.length - 1]?.content === "" && (
            <div className="flex justify-start">
              <div className="bg-zinc-800/50 border border-zinc-700/30 rounded-2xl px-5 py-3.5 flex items-center gap-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce" />
                </div>
                <span className="text-xs text-zinc-500">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  repo ? "Ask anything about this repo..." : "Enter a repo: owner/repo-name"
                }
                rows={1}
                className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-2xl px-5 py-3.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500/50 placeholder:text-zinc-500 transition-all"
                disabled={indexStatus === "cloning"}
              />
              {!input && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1 text-zinc-600">
                  <Command className="w-3 h-3" />
                  <span className="text-xs">Enter</span>
                </div>
              )}
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="p-3.5 bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 disabled:from-zinc-700 disabled:to-zinc-700 disabled:cursor-not-allowed rounded-2xl transition-all shadow-lg shadow-emerald-900/20 active:scale-95 flex-shrink-0"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-[11px] text-zinc-600 text-center mt-3">
            RepoX analyzes code & commit history · AI responses may vary
          </p>
        </div>
      </div>
    </div>
  );
}