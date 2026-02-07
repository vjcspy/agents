import type { Debate, ApiResponse } from './types';

const SERVER_URL = process.env.NEXT_PUBLIC_DEBATE_SERVER_URL || 'http://127.0.0.1:3456';

export function getServerUrl(): string {
  return SERVER_URL;
}

export function getWsUrl(): string {
  return SERVER_URL.replace(/^http/, 'ws');
}

export async function fetchDebates(): Promise<Debate[]> {
  const res = await fetch(`${SERVER_URL}/debates`);
  const json: ApiResponse<{ debates: Debate[]; total: number }> = await res.json();
  
  if (!json.success) {
    throw new Error(json.error.message);
  }
  
  return json.data.debates;
}

export async function fetchDebate(id: string): Promise<{ debate: Debate }> {
  const res = await fetch(`${SERVER_URL}/debates/${id}`);
  const json: ApiResponse<{ debate: Debate }> = await res.json();
  
  if (!json.success) {
    throw new Error(json.error.message);
  }
  
  return json.data;
}

export async function deleteDebate(id: string): Promise<void> {
  const res = await fetch(`${SERVER_URL}/debates/${id}`, {
    method: 'DELETE',
  });
  const json: ApiResponse<{ deleted: boolean }> = await res.json();
  
  if (!json.success) {
    throw new Error(json.error.message);
  }
}
