const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const message = (data && data.error) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body || {}),
    }),
  patch: (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body || {}) }),
  put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body || {}) }),
  del: (path) => request(path, { method: "DELETE" }),
};
