import { ArrowRight, FileText, MessagesSquare, Search, Upload } from "lucide-react";

import { StatusBadge } from "../components/ui/Badge";
import { useAuth } from "../hooks/useAuth";

const PIPELINE = [
  {
    icon: Upload,
    title: "Add documents",
    body: "Upload PDFs, Word files, Markdown, or plain text. Each one is stored with its metadata and queued for processing.",
    step: "01",
  },
  {
    icon: FileText,
    title: "Automatic processing",
    body: "Documents are parsed, split into chunks, embedded, and indexed — you watch the status move from processing to ready.",
    step: "02",
  },
  {
    icon: Search,
    title: "Semantic search",
    body: "Search by meaning, not keywords. Results come back ranked, with a snippet and a link to the exact source.",
    step: "03",
  },
  {
    icon: MessagesSquare,
    title: "Ask in plain language",
    body: "Chat with your knowledge base and get answers grounded in your documents, each citing the source it came from.",
    step: "04",
  },
];

function firstName(user: { full_name: string | null; email: string }): string {
  return user.full_name?.trim().split(" ")[0] || user.email.split("@")[0];
}

export function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-8">
        <p className="font-mono text-2xs uppercase tracking-wider text-slate-400">
          Overview
        </p>
        <h1 className="mt-1 font-serif text-3xl font-semibold text-ink">
          Welcome{user ? `, ${firstName(user)}` : ""}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          Athenaeum turns your organization's documents into an answerable memory layer.
          Here's how a question travels from a raw file to a cited answer.
        </p>
      </header>

      {/* System status */}
      <section className="mb-8 rounded-card border border-line bg-surface p-5 shadow-card">
        <h2 className="mb-4 text-sm font-semibold text-ink">System status</h2>
        <dl className="grid gap-4 sm:grid-cols-3">
          <div className="flex items-center justify-between">
            <dt className="text-sm text-slate-500">Authentication</dt>
            <dd>
              <StatusBadge status="ready" />
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-sm text-slate-500">Ingestion pipeline</dt>
            <dd>
              <StatusBadge status="uploaded" />
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-sm text-slate-500">Retrieval &amp; chat</dt>
            <dd>
              <StatusBadge status="uploaded" />
            </dd>
          </div>
        </dl>
      </section>

      {/* Pipeline — a real sequence, so numbered markers earn their place */}
      <section>
        <h2 className="mb-4 text-sm font-semibold text-ink">How it works</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {PIPELINE.map(({ icon: Icon, title, body, step }) => (
            <article
              key={step}
              className="rounded-card border border-line bg-surface p-5 shadow-card"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-brand/10 text-brand-700">
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <span className="font-mono text-sm text-slate-300">{step}</span>
              </div>
              <h3 className="text-sm font-semibold text-ink">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{body}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="mt-8 flex items-center gap-2 rounded-card border border-dashed border-line bg-surface/50 px-5 py-4 text-sm text-slate-500">
        <span>Document upload arrives next — you'll add your first file here.</span>
        <ArrowRight className="h-4 w-4 text-slate-300" />
      </div>
    </div>
  );
}
