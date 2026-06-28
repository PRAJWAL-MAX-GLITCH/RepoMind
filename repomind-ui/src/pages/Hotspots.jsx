import { useState } from 'react';
import { useRepos } from '../context/RepoContext';
import { getRepoHotspots } from '../services/api';
import {
  LoadingState, ErrorAlert, EmptyState, RepoSelector, Badge,
} from '../components/ui';

const PRIORITY_META = {
  high:   { badge: 'red',   icon: '🔴', label: 'HIGH' },
  medium: { badge: 'amber', icon: '🟡', label: 'MED'  },
  low:    { badge: 'green', icon: '🟢', label: 'LOW'  },
};

function HotspotCard({ item, index }) {
  const p = PRIORITY_META[item.priority?.toLowerCase()] || PRIORITY_META.medium;
  return (
    <div style={{
      background: '#111113',
      border: '1px solid #27272a',
      borderLeft: `3px solid ${item.priority?.toLowerCase() === 'high' ? '#ef4444' : item.priority?.toLowerCase() === 'low' ? '#22c55e' : '#f59e0b'}`,
      borderRadius: 8,
      padding: '14px 16px',
      display: 'flex', alignItems: 'flex-start', gap: 14,
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 6, flexShrink: 0,
        background: 'rgba(255,255,255,0.04)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.7rem', fontWeight: 700, color: '#52525b',
      }}>
        {index + 1}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
          <span className="mono" style={{ fontSize: '0.82rem', color: '#60a5fa', wordBreak: 'break-all' }}>
            {item.file_path || item.path || '—'}
          </span>
          {item.category && <Badge variant="zinc">{item.category}</Badge>}
        </div>
        <p style={{ fontSize: '0.8rem', color: '#71717a', lineHeight: 1.5 }}>{item.reason || '—'}</p>
      </div>
      <div style={{ flexShrink: 0 }}>
        <Badge variant={p.badge}>{p.icon} {p.label}</Badge>
      </div>
    </div>
  );
}

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };

export default function Hotspots() {
  const { repos } = useRepos();
  const [repoName, setRepoName] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  async function handleFetch() {
    if (!repoName.trim()) { setError('Please enter a repository name.'); return; }
    setError(''); setData(null); setLoading(true);
    try {
      const result = await getRepoHotspots(repoName.trim(), repoPath.trim() || undefined);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const hotspots = (data?.hotspots || [])
    .filter(h => filter === 'all' || h.priority?.toLowerCase() === filter)
    .sort((a, b) => (PRIORITY_ORDER[a.priority?.toLowerCase()] ?? 9) - (PRIORITY_ORDER[b.priority?.toLowerCase()] ?? 9));

  const counts = data?.hotspots?.reduce((acc, h) => {
    const p = h.priority?.toLowerCase() || 'unknown';
    acc[p] = (acc[p] || 0) + 1;
    return acc;
  }, {}) || {};

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Code Hotspots</h1>
        <p className="page-subtitle">Risky, complex, or security-sensitive files flagged by heuristic analysis — centrality, size, secret patterns, and keyword density.</p>
      </div>

      <div className="card" style={{ padding: '22px 24px', marginBottom: 20 }}>
        <RepoSelector
          repos={repos}
          value={repoName}
          onChange={setRepoName}
          onPathChange={setRepoPath}
          repoPath={repoPath}
        />
        <button
          className="btn-primary"
          onClick={handleFetch}
          disabled={loading || !repoName.trim()}
          style={{ marginTop: 14 }}
        >
          {loading ? '⏳' : '🔥'} {loading ? 'Scanning…' : 'Find Hotspots'}
        </button>
      </div>

      <ErrorAlert message={error} />
      {loading && <LoadingState message="Running hotspot analysis…" />}

      {data && !loading && (
        <>
          {/* Summary strip */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
            {[
              { label: 'Total', value: data.hotspots?.length || 0, color: '#a1a1aa' },
              { label: 'High', value: counts.high || 0, color: '#f87171' },
              { label: 'Medium', value: counts.medium || 0, color: '#fbbf24' },
              { label: 'Low', value: counts.low || 0, color: '#4ade80' },
            ].map(s => (
              <div key={s.label} className="card" style={{ padding: '10px 16px', textAlign: 'center', minWidth: 90 }}>
                <p style={{ fontSize: '1.3rem', fontWeight: 700, color: s.color }}>{s.value}</p>
                <p style={{ fontSize: '0.68rem', color: '#52525b', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 2 }}>{s.label}</p>
              </div>
            ))}
          </div>

          {/* Filters */}
          {data.hotspots?.length > 0 && (
            <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
              {['all', 'high', 'medium', 'low'].map(f => (
                <button
                  key={f}
                  className={filter === f ? 'btn-primary' : 'btn-secondary'}
                  onClick={() => setFilter(f)}
                  style={{ padding: '5px 12px', fontSize: '0.78rem' }}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          )}

          {hotspots.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {hotspots.map((item, i) => (
                <HotspotCard key={i} item={item} index={i} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon="🟢"
              title={filter === 'all' ? 'No hotspots detected' : `No ${filter}-priority hotspots`}
              subtitle="The repository looks clean or try a different filter."
            />
          )}
        </>
      )}

      {!data && !loading && !error && (
        <EmptyState icon="🔥" title="Select a repository to find hotspots" />
      )}
    </div>
  );
}
