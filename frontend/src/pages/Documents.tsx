import { useCallback, useEffect, useRef, useState } from "react";

import {
  AlertCircle,
  FileText,
  Trash2,
  Upload,
  UploadCloud,
} from "lucide-react";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "../lib/documents";
import { toErrorMessage } from "../lib/api";
import type { Document } from "../lib/types";

const ACCEPT = ".pdf,.docx,.txt,.md";
const POLL_MS = 3000;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Document | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
      setError(null);
    } catch (err) {
      setError(toErrorMessage(err, "Couldn't load your documents."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Poll while any document is still working its way through the pipeline.
  const hasPending = documents.some(
    (d) => d.status === "uploaded" || d.status === "processing"
  );
  useEffect(() => {
    if (!hasPending) return;
    const timer = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(timer);
  }, [hasPending, refresh]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadError(null);
    for (const file of Array.from(files)) {
      try {
        setProgress(0);
        await uploadDocument(file, setProgress);
      } catch (err) {
        setUploadError(toErrorMessage(err, `Couldn't upload ${file.name}.`));
      }
    }
    setProgress(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    await refresh();
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    const target = pendingDelete;
    setPendingDelete(null);
    setDocuments((docs) => docs.filter((d) => d.id !== target.id));
    try {
      await deleteDocument(target.id);
    } catch (err) {
      setError(toErrorMessage(err, "Couldn't delete that document."));
      await refresh();
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <header className="mb-6">
        <p className="font-mono text-2xs uppercase tracking-wider text-slate-400">
          Knowledge
        </p>
        <h1 className="mt-1 font-serif text-3xl font-semibold text-ink">Documents</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
          Upload PDFs, Word files, Markdown, or plain text. Each file is parsed,
          chunked, and embedded automatically — watch the status move to ready.
        </p>
      </header>

      {/* Dropzone */}
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void handleFiles(e.dataTransfer.files);
        }}
        className={`mb-4 flex cursor-pointer flex-col items-center justify-center rounded-card border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragOver
            ? "border-brand bg-brand/5"
            : "border-line bg-surface hover:border-brand/50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          onChange={(e) => void handleFiles(e.target.files)}
        />
        <UploadCloud className="mb-2 h-8 w-8 text-brand" />
        <p className="text-sm font-medium text-ink">
          Drag &amp; drop files here, or click to browse
        </p>
        <p className="mt-1 text-2xs uppercase tracking-wide text-slate-400">
          PDF · DOCX · TXT · MD · up to 25 MB
        </p>
        {progress !== null && (
          <div className="mt-4 w-full max-w-xs">
            <div className="h-1.5 overflow-hidden rounded-full bg-line">
              <div
                className="h-full rounded-full bg-brand transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-1.5 text-2xs text-slate-400">Uploading… {progress}%</p>
          </div>
        )}
      </label>

      {uploadError && (
        <div className="mb-4">
          <Alert tone="error">{uploadError}</Alert>
        </div>
      )}
      {error && (
        <div className="mb-4">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Spinner className="h-6 w-6" />
        </div>
      ) : documents.length === 0 ? (
        <div className="rounded-card border border-dashed border-line bg-surface/50 px-6 py-12 text-center">
          <FileText className="mx-auto mb-2 h-8 w-8 text-slate-300" />
          <p className="text-sm text-slate-500">No documents yet.</p>
          <p className="text-2xs text-slate-400">Upload your first file above.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-card border border-line bg-surface shadow-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-2xs uppercase tracking-wide text-slate-400">
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">Size</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="hidden px-4 py-3 font-semibold sm:table-cell">Added</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-line last:border-0">
                  <td className="max-w-0 px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <FileText className="h-4 w-4 shrink-0 text-slate-400" />
                      <div className="min-w-0">
                        <p className="truncate font-medium text-ink">{doc.filename}</p>
                        <p className="text-2xs uppercase text-slate-400">
                          {doc.extension}
                          {doc.status === "ready" && ` · ${doc.chunk_count} chunks`}
                        </p>
                        {doc.status === "failed" && doc.error && (
                          <p className="mt-0.5 flex items-center gap-1 text-2xs text-status-failed">
                            <AlertCircle className="h-3 w-3 shrink-0" />
                            {doc.error}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                    {formatBytes(doc.size_bytes)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="hidden whitespace-nowrap px-4 py-3 text-slate-500 sm:table-cell">
                    {formatDate(doc.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setPendingDelete(doc)}
                      aria-label={`Delete ${doc.filename}`}
                      className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-status-failed/10 hover:text-status-failed"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete confirmation */}
      {pendingDelete && (
        <div
          className="fixed inset-0 z-20 flex items-center justify-center bg-ink/40 p-4"
          onClick={() => setPendingDelete(null)}
        >
          <div
            className="w-full max-w-sm rounded-card border border-line bg-surface p-5 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-serif text-lg font-semibold text-ink">
              Delete document?
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
              <span className="font-medium text-ink">{pendingDelete.filename}</span> and
              its indexed chunks will be permanently removed. This can't be undone.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setPendingDelete(null)}>
                Cancel
              </Button>
              <Button
                onClick={() => void confirmDelete()}
                className="bg-status-failed text-white hover:bg-status-failed/90"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}

      <label className="mt-4 flex cursor-pointer items-center justify-center gap-2 text-2xs text-slate-400 hover:text-slate-500">
        <input
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          onChange={(e) => void handleFiles(e.target.files)}
        />
        <Upload className="h-3 w-3" />
        Add more files
      </label>
    </div>
  );
}
