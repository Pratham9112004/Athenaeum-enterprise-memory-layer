import { type ReactNode } from "react";

import { FileText, LayoutGrid, LogOut, MessagesSquare, Search } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { clsx } from "clsx";

import { useAuth } from "../../hooks/useAuth";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutGrid;
  ready: boolean;
}

// Feature routes light up as they're built. Items marked not-ready are shown but
// disabled, so the shell communicates the product's shape without dead links.
const NAV: NavItem[] = [
  { to: "/", label: "Overview", icon: LayoutGrid, ready: true },
  { to: "/documents", label: "Documents", icon: FileText, ready: true },
  { to: "/search", label: "Search", icon: Search, ready: true },
  { to: "/chat", label: "Chat", icon: MessagesSquare, ready: true },
];

function initials(user: { full_name: string | null; email: string }): string {
  const source = user.full_name?.trim() || user.email;
  return source
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex min-h-screen bg-paper">
      {/* Sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-line bg-surface md:flex">
        <div className="flex h-16 items-center gap-2.5 border-b border-line px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-ink font-serif text-lg font-semibold text-white">
            A
          </div>
          <span className="font-serif text-lg font-semibold text-ink">Athenaeum</span>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          <p className="px-3 pb-1 pt-3 text-2xs font-semibold uppercase tracking-wider text-slate-400">
            Knowledge
          </p>
          {NAV.map(({ to, label, icon: Icon, ready }) =>
            ready ? (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand/10 text-brand-700"
                      : "text-slate-500 hover:bg-paper hover:text-ink"
                  )
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ) : (
              <span
                key={to}
                title="Coming soon"
                className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300"
              >
                <Icon className="h-4 w-4" />
                {label}
                <span className="ml-auto text-2xs uppercase tracking-wide text-slate-300">
                  Soon
                </span>
              </span>
            )
          )}
        </nav>

        <div className="border-t border-line p-3">
          <div className="flex items-center gap-3 rounded-md px-3 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand/15 text-sm font-semibold text-brand-700">
              {user ? initials(user) : "?"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-ink">
                {user?.full_name || "Signed in"}
              </p>
              <p className="truncate text-2xs text-slate-400">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:bg-paper hover:text-status-failed"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-line bg-surface px-6">
          <div className="flex items-center gap-2 md:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-ink font-serif text-sm font-semibold text-white">
              A
            </div>
            <span className="font-serif text-base font-semibold text-ink">Athenaeum</span>
          </div>
          <div className="hidden text-sm text-slate-400 md:block">
            Enterprise Memory Layer
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-ink md:hidden"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
