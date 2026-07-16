import { api } from "./api";
import type { ChatResponse } from "./types";

export async function sendMessage(
  message: string,
  sessionId: number | null
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", {
    message,
    session_id: sessionId,
  });
  return data;
}
