import { type ReactNode } from "react";

/**
 * Split layout: a quiet form on the left, and on the right the "signature" panel —
 * a dark ledger-ruled field evoking an archive's accession register.
 */
export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-paper">
      {/* Form side */}
      <div className="flex w-full flex-col justify-center px-6 py-12 lg:w-[46%] lg:px-16">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-10 flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ink font-serif text-xl font-semibold text-white">
              A
            </div>
            <span className="font-serif text-xl font-semibold text-ink">Athenaeum</span>
          </div>

          <h1 className="font-serif text-2xl font-semibold text-ink">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>

          <div className="mt-8">{children}</div>

          <div className="mt-6 text-sm text-slate-500">{footer}</div>
        </div>
      </div>

      {/* Signature side */}
      <div className="bg-ledger relative hidden overflow-hidden lg:block lg:w-[54%]">
        <div className="absolute inset-0 flex flex-col justify-between p-16 text-white">
          <p className="font-mono text-2xs uppercase tracking-[0.3em] text-white/50">
            Accession Register
          </p>
          <div className="max-w-lg">
            <p className="font-serif text-3xl font-medium leading-snug text-white/95">
              Every document, decision, and design — searchable, and answerable in plain
              language, with a citation back to the source.
            </p>
            <p className="mt-6 font-mono text-sm text-white/45">
              /ˌaθɪˈniːəm/ — a place for the collection and retrieval of knowledge.
            </p>
          </div>
          <p className="font-mono text-2xs text-white/40">Enterprise Memory Layer</p>
        </div>
      </div>
    </div>
  );
}
