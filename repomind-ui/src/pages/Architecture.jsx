import { useState } from 'react';
import { useRepos } from '../context/RepoContext';
import { getRepoArchitecture } from '../services/api';
import {
  LoadingState, ErrorAlert, EmptyState, SectionCard,
  TagList, PathLine, RepoSelector,
} from '../components/ui';

function FileSection({ title, files, icon, color }) {
  if (!files?.length) return null;
  return (
    <div style={{
      background: '#111113',
      border: '1px solid #27272a',
      borderRadius: 8, padding: '14px 16px',
    }}>
      <p style={{
        fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em',
        textTransform: 'uppercase', color, marginBottom: 10,
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <span>{icon}</span>{title}
        <span style={{ color: '#52525b', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
          ({files.length})
        </span>
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {files.map((f, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 4, height: 4, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <PathLine path={f} color="#a1a1aa" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Architecture() {
  const { repos } = useRepos();
  const [repoName, setRepoName] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  async function handleFetch() {
    if (!repoName.trim()) { setError('Please enter a repository name.'); return; }
    setError(''); setData(null); setLoading(true);
    try {
      const result = await getRepoArchitecture(repoName.trim(), repoPath.trim() || undefined);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Flatten important_files if present
  const ifiles = data?.important_files || {};

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Architecture View</h1>
        <p className="page-subtitle">Structural analysis — languages, entry points, critical file categories, and key design observations.</p>
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
          {loading ? '⏳' : '🏗️'} {loading ? 'Analyzing…' : 'Analyze Architecture'}
        </button>
      </div>

      <ErrorAlert message={error} />
      {loading && <LoadingState message="Running architecture analysis…" />}

      {data && !loading && (
        <>
          {/* Overview */}
          <div style={{
            background: 'rgba(139,92,246,0.05)',
            border: '1px solid rgba(139,92,246,0.15)',
            borderRadius: 10, padding: '20px 22px', marginBottom: 16,
          }}>
            <p style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#a78bfa', marginBottom: 10 }}>
              Project Summary · {data.repo_name}
            </p>
            <p style={{ fontSize: '0.9rem', lineHeight: 1.75, color: '#e4e4e7' }}>
              {data.project_summary || '—'}
            </p>
          </div>

          {/* Languages + modules */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            <SectionCard title="Languages" accent="#3b82f6">
              <TagList items={data.languages} variant="blue" />
            </SectionCard>
            <SectionCard title="Main Modules" accent="#22c55e">
              <TagList items={data.main_modules} variant="green" />
            </SectionCard>
          </div>

          {/* Entry points */}
          {data.entry_points?.length > 0 && (
            <SectionCard title="Entry Points" accent="#f59e0b">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {data.entry_points.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#fbbf24', fontSize: '0.72rem', fontFamily: 'monospace' }}>→</span>
                    <PathLine path={f} color="#a1a1aa" />
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {/* File groups */}
          {Object.keys(ifiles).length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p className="section-label" style={{ marginBottom: 12 }}>Important File Groups</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                <FileSection title="Auth / Security" files={ifiles.auth} icon="🔑" color="#f87171" />
                <FileSection title="Database" files={ifiles.database} icon="🗄️" color="#60a5fa" />
                <FileSection title="API / Routes" files={ifiles.api} icon="🌐" color="#34d399" />
                <FileSection title="Config" files={ifiles.config} icon="⚙️" color="#fbbf24" />
                <FileSection title="ML / AI" files={ifiles.ml} icon="🤖" color="#a78bfa" />
                <FileSection title="Tests" files={ifiles.tests} icon="🧪" color="#22d3ee" />
              </div>
            </div>
          )}

          {/* Architecture notes */}
          {data.architecture_notes?.length > 0 && (
            <SectionCard title="Architecture Notes" accent="#06b6d4">
              {Array.isArray(data.architecture_notes) ? (
                <ul style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingLeft: 0, listStyle: 'none' }}>
                  {data.architecture_notes.map((n, i) => (
                    <li key={i} style={{ display: 'flex', gap: 10, fontSize: '0.875rem', color: '#a1a1aa', lineHeight: 1.6 }}>
                      <span style={{ color: '#22d3ee', flexShrink: 0 }}>›</span>
                      {n}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: '0.875rem', color: '#a1a1aa', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
                  {data.architecture_notes}
                </p>
              )}
            </SectionCard>
          )}
        </>
      )}

      {!data && !loading && !error && (
        <EmptyState icon="🏗️" title="Select a repository to analyze its architecture" />
      )}
    </div>
  );
}
