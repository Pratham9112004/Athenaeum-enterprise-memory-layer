export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: number;
  filename: string;
  content_type: string;
  extension: string;
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  chunk_count: number;
  created_at: string;
}

export interface SearchResult {
  chunk_id: number;
  document_id: number;
  document_name: string;
  page: number | null;
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export interface Citation {
  index: number;
  chunk_id: number;
  document_id: number;
  document_name: string;
  page: number | null;
  snippet: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface ChatResponse {
  session_id: number;
  message: ChatMessage;
}

export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}
