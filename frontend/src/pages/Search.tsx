import { useState } from "react";

import { FileText, Search as SearchIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { search } from "../lib/search";
import { toErrorMessage } from "../lib/api";
import type { SearchResult } from "../lib/types";

export function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    try {
      const response = await search(trimmed);
      setResults(response.results);
    } catch (err) {
      setError(toErrorMessage(err, "Search failed. Please try again."));
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-6">
        <p className="font-mono text-2xs uppercase tracking-wider text-slate-400">
          Knowledge
        </p>
        <h1 className="mt-1 font-serif text-3xl font-semibold text-ink">Search</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          Search your documents by meaning, not keywords. Results are ranked by
          relevance and link back to their source.
        </p>
      </header>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void runSearch()}
            placeholder="e.g. What is our refund policy?"
            className="pl-9"
            autoFocus
          />
        </div>
        <Button onClick={() => void runSearch()} loading={loading} disabled={!query.trim()}>
          Search
        </Button>
      </div>

      {error && (
        <div className="mt-4">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="mt-6">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <Spinner className="h-6 w-6" />
          </div>
        ) : results === null ? null : results.length === 0 ? (
          <div className="rounded-card border border-dashed border-line bg-surface/50 px-6 py-12 text-center">
            <p className="text-sm text-slate-500">No results found.</p>
            <p className="text-2xs text-slate-400">
              Try rephrasing, or make sure your documents have finished processing.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-2xs uppercase tracking-wide text-slate-400">
              {results.length} result{results.length === 1 ? "" : "s"}
            </p>
            {results.map((r) => (
              <article
                key={r.chunk_id}
                className="rounded-card border border-line bg-surface p-4 shadow-card"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <button
                    onClick={() => navigate("/documents")}
                    className="flex min-w-0 items-center gap-2 text-sm font-medium text-brand-700 hover:underline"
                  >
                    <FileText className="h-4 w-4 shrink-0" />
                    <span className="truncate">{r.document_name}</span>
                    {r.page !== null && (
                      <span className="shrink-0 text-2xs text-slate-400">
                        p.{r.page}
                      </span>
                    )}
                  </button>
                  <span className="shrink-0 font-mono text-2xs text-slate-400">
                    {(r.score * 100).toFixed(0)}% match
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-slate-600">{r.snippet}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
