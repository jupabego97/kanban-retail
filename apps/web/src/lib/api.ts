/**
 * Cliente HTTP tipado hacia la API FastAPI.
 * Usa cookies de sesión (credentials: include).
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(status: number, message: string, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  searchParams?: Record<string, string | number | boolean | undefined | null>;
  formData?: FormData;
  signal?: AbortSignal;
};

function buildUrl(path: string, searchParams?: RequestOptions["searchParams"]) {
  const url = new URL(path.startsWith("http") ? path : `${API_URL}${path}`);
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, searchParams, formData, signal } = options;
  const headers: HeadersInit = {};
  let payload: BodyInit | undefined;

  if (formData) {
    payload = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(buildUrl(path, searchParams), {
    method,
    headers,
    body: payload,
    credentials: "include",
    signal,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const contentType = res.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json")
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    let message = "Error de API";
    let code: string | undefined;
    if (typeof data === "string") {
      message = data;
    } else if (typeof data === "object" && data) {
      if ("message" in data && typeof data.message === "string") {
        message = data.message;
        code = "code" in data && typeof data.code === "string" ? data.code : undefined;
      } else if ("detail" in data) {
        if (typeof data.detail === "string") message = data.detail;
        else if (typeof data.detail === "object" && data.detail?.message) {
          message = data.detail.message;
          code = data.detail.code;
        }
      }
    }
    throw new ApiError(res.status, message, code, data);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string, searchParams?: RequestOptions["searchParams"]) =>
    apiFetch<T>(path, { searchParams }),
  post: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => apiFetch<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) =>
    apiFetch<T>(path, { method: "POST", formData }),
};
