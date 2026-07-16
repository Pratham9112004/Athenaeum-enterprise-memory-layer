import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { Spinner } from "./ui/Spinner";

export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <Spinner className="h-6 w-6 text-brand" />
          <p className="text-sm">Restoring your session…</p>
        </div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    // Remember where the user was headed so we can return them after login.
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
