const BASE = '';  // proxied via vite to http://localhost:8080

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(BASE + path, opts);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// POST /repos/scan
export function scanRepository(repo_path) {
  return request('POST', '/repos/scan', { repo_path });
}

// POST /repos/index
export function indexRepository(repo_path) {
  return request('POST', '/repos/index', { repo_path });
}

// POST /repos/query
export function queryRepository(repo_name, question, top_k = 5) {
  return request('POST', '/repos/query', { repo_name, question, top_k });
}

// GET /repos/{repo_name}/summary
export function getRepoSummary(repo_name, repo_path) {
  const qs = repo_path ? `?repo_path=${encodeURIComponent(repo_path)}` : '';
  return request('GET', `/repos/${encodeURIComponent(repo_name)}/summary${qs}`);
}

// GET /repos/{repo_name}/architecture
export function getRepoArchitecture(repo_name, repo_path) {
  const qs = repo_path ? `?repo_path=${encodeURIComponent(repo_path)}` : '';
  return request('GET', `/repos/${encodeURIComponent(repo_name)}/architecture${qs}`);
}

// GET /repos/{repo_name}/hotspots
export function getRepoHotspots(repo_name, repo_path) {
  const qs = repo_path ? `?repo_path=${encodeURIComponent(repo_path)}` : '';
  return request('GET', `/repos/${encodeURIComponent(repo_name)}/hotspots${qs}`);
}

// GET /health
export function getHealth() {
  return request('GET', '/health');
}
