import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

/**
 * The access token lives in module memory only — never in localStorage — so an XSS
 * payload can't read it. The long-lived refresh token is an httpOnly cookie the JS
 * never sees; `withCredentials` sends it on refresh calls.
 */
let accessToken: string | null = null;

export const setAccessToken = (token: string | null): void => {
  accessToken = token;
};
export const getAccessToken = (): string | null => accessToken;

export const api = axios.create({ baseURL, withCredentials: true });

// Attach the current access token to every request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

/** Bare client used only for the refresh call, to avoid interceptor recursion. */
const refreshClient = axios.create({ baseURL, withCredentials: true });

export async function refreshAccessToken(): Promise<string> {
  const { data } = await refreshClient.post<{ access_token: string }>("/auth/refresh");
  setAccessToken(data.access_token);
  return data.access_token;
}

// Coalesce concurrent refreshes into one in-flight request.
let refreshInFlight: Promise<string> | null = null;

type RetriableConfig = AxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;
    const isAuthRoute = original?.url?.includes("/auth/") ?? false;

    if (status === 401 && original && !original._retry && !isAuthRoute) {
      original._retry = true;
      try {
        refreshInFlight = refreshInFlight ?? refreshAccessToken();
        const token = await refreshInFlight;
        refreshInFlight = null;
        original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
        return api(original);
      } catch (refreshError) {
        refreshInFlight = null;
        setAccessToken(null);
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

/** Normalize an API error into a human-readable message for the UI. */
export function toErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      // FastAPI validation errors: [{ loc, msg, ... }]
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (error.code === "ERR_NETWORK") return "Can't reach the server. Is the API running?";
  }
  return fallback;
}
