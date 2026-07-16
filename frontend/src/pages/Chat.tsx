import { type ReactNode, useEffect, useRef, useState } from "react";

import { FileText, MessagesSquare, SendHorizonal, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Spinner } from "../components/ui/Spinner";
import { sendMessage } from "../lib/chat";
import { toErrorMessage } from "../lib/api";
import type { ChatMessage, Citation } from "../lib/types";

const CITATION_RE = /\[(\d+)\]/g;

/** Render assistant text with [n] markers turned into clickable citation chips. */
function renderContent(
  content: string,
  citations: Citation[] | null,
  onCite: (c: Citation) => void
) {
  if (!citations || citations.length === 0) return content;
  const byIndex = new Map(citations.map((c) => [c.index, c]));
  const parts: ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  CITATION_RE.lastIndex = 0;
  let key = 0;
  while ((match = CITATION_RE.exec(content)) !== null) {
    const citation = byIndex.get(Number(match[1]));
    if (!citation) continue;
    if (match.index > last) parts.push(content.slice(last, match.index));
    parts.push(
      <button
        key={`c${key++}`}
        onClick={() => onCite(citation)}
        className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-brand/15 px-1 align-super text-2xs font-semibold text-brand-700 hover:bg-brand/25"
        title={citation.document_name}
      >
        {match[1]}
      </button>
    );
    last = match.index + match[0].length;
  }
  if (last < content.length) parts.push(content.slice(last));
  return parts;
}

export function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError(null);
    const optimistic: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: text,
      citations: null,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimistic]);
    setLoading(true);
    try {
      const response = await sendMessage(text, sessionId);
      setSessionId(response.session_id);
      setMessages((m) => [...m, response.message]);
    } catch (err) {
      setError(toErrorMessage(err, "The assistant couldn't respond."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col">
      <header className="mb-4 shrink-0">
        <p className="font-mono text-2xs uppercase tracking-wider text-slate-400">
          Knowledge
        </p>
        <h1 className="mt-1 font-serif text-3xl font-semibold text-ink">Chat</h1>
      </header>

      {/* Thread */}
      <div
        ref={threadRef}
        className="flex-1 space-y-4 overflow-y-auto rounded-card border border-line bg-surface p-5 shadow-card"
      >
        {messages.length === 0 && !loading ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <MessagesSquare className="mb-2 h-8 w-8 text-slate-300" />
            <p className="text-sm text-slate-500">
              Ask a question about your documents.
            </p>
            <p className="mt-1 max-w-sm text-2xs text-slate-400">
              Answers are grounded in your uploaded files and cite the sources they
              draw from.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={
                  msg.role === "user"
                    ? "max-w-[80%] rounded-2xl rounded-br-sm bg-brand px-4 py-2.5 text-sm text-white"
                    : "max-w-[85%] rounded-2xl rounded-bl-sm bg-paper px-4 py-3 text-sm leading-relaxed text-ink"
                }
              >
                <div className="whitespace-pre-wrap">
                  {msg.role === "assistant"
                    ? renderContent(msg.content, msg.citations, setActiveCitation)
                    : msg.content}
                </div>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 border-t border-line pt-2.5">
                    {msg.citations.map((c) => (
                      <button
                        key={c.index}
                        onClick={() => setActiveCitation(c)}
                        className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-0.5 text-2xs text-slate-500 hover:border-brand/40 hover:text-brand-700"
                      >
                        <FileText className="h-3 w-3" />
                        <span className="max-w-[10rem] truncate">
                          {c.index}. {c.document_name}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm bg-paper px-4 py-3 text-sm text-slate-400">
              <Spinner className="h-4 w-4" />
              Thinking…
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 shrink-0">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      {/* Composer */}
      <div className="mt-3 flex shrink-0 items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          rows={1}
          placeholder="Ask about your documents…"
          className="max-h-32 flex-1 resize-none rounded-md border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-slate-400 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30"
        />
        <button
          onClick={() => void send()}
          disabled={!input.trim() || loading}
          aria-label="Send message"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-brand text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-brand/50"
        >
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>

      {/* Citation source panel */}
      {activeCitation && (
        <div
          className="fixed inset-0 z-20 flex justify-end bg-ink/40"
          onClick={() => setActiveCitation(null)}
        >
          <div
            className="h-full w-full max-w-md overflow-y-auto border-l border-line bg-surface p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between">
              <div>
                <p className="font-mono text-2xs uppercase tracking-wider text-slate-400">
                  Source [{activeCitation.index}]
                </p>
                <h2 className="mt-1 flex items-center gap-2 font-serif text-lg font-semibold text-ink">
                  <FileText className="h-4 w-4 text-slate-400" />
                  {activeCitation.document_name}
                </h2>
                {activeCitation.page !== null && (
                  <p className="mt-0.5 text-2xs text-slate-400">
                    Page {activeCitation.page}
                  </p>
                )}
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                aria-label="Close"
                className="rounded-md p-1 text-slate-400 hover:bg-paper hover:text-ink"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <blockquote className="rounded-md border-l-2 border-brand/40 bg-paper px-4 py-3 text-sm leading-relaxed text-slate-600">
              {activeCitation.snippet}
            </blockquote>
            <button
              onClick={() => navigate("/documents")}
              className="mt-4 text-sm font-medium text-brand-700 hover:underline"
            >
              View in Documents →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
