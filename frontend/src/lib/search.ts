import { api } from "./api";
import type { SearchResponse } from "./types";

export async function search(query: string, topK = 5): Promise<SearchResponse> {
  const { data } = await api.post<SearchResponse>("/search", {
    query,
    top_k: topK,
  });
  return data;
}
