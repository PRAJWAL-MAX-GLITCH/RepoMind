import { useState } from 'react';
import { useRepos } from '../context/RepoContext';
import { getRepoSummary } from '../services/api';
import {
  LoadingState, ErrorAlert, EmptyState, SectionCard,
  TagList, PathLine, RepoSelector,
} from '../components/ui';

function FileGroup({ title, files, color }) {
  if (!files?.length) return null;
  return (
    <div>
      <p style={{
        fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em',
        textTransform: 'uppercase', color, marginBottom: 8,
      }}>{title}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {files.map((f, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <PathLine path={f} color="#a1a1aa" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Summary() {
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
      const result = await getRepoSummary(repoName.trim(), repoPath.trim() || undefined);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Repository Summary</h1>
        <p className="page-subtitle">Auto-generated developer onboarding overview — what the project does, its tech stack, and key files.</p>
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
          {loading ? '⏳' : '📋'} {loading ? 'Generating…' : 'Generate Summary'}
        </button>
      </div>

      <ErrorAlert message={error} />
      {loading && <LoadingState message="Analyzing repository and generating summary…" />}

      {data && !loading && (
        <>
          {/* What it does */}
          <div style={{
            background: 'rgba(59,130,246,0.05)',
            border: '1px solid rgba(59,130,246,0.15)',
            borderRadius: 10, padding: '20px 22px', marginBottom: 16,
          }}>
            <p style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#60a5fa', marginBottom: 10 }}>
              What it does · {data.repo_name}
            </p>
            <p style={{ fontSize: '0.925rem', lineHeight: 1.75, color: '#e4e4e7' }}>
              {data.what_it_does || '—'}
            </p>
          </div>

          {/* Tech stack + modules */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            <SectionCard title="Tech Stack" accent="#8b5cf6">
              <TagList items={data.tech_stack} variant="violet" />
            </SectionCard>
            <SectionCard title="Major Modules" accent="#22c55e">
              <TagList items={data.major_modules} variant="green" />
            </SectionCard>
          </div>

          {/* Entry files */}
          {data.entry_files?.length > 0 && (
            <SectionCard title="Entry Points" accent="#f59e0b">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {data.entry_files.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#fbbf24', fontSize: '0.7rem' }}>→</span>
                    <PathLine path={f} color="#a1a1aa" />
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {/* Important file groups */}
          {data.important_files && Object.keys(data.important_files).some(k => data.important_files[k]?.length) && (
            <SectionCard title="Important Files by Category" accent="#ef4444">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                <FileGroup title="Auth" files={data.important_files.auth} color="#f87171" />
                <FileGroup title="Database" files={data.important_files.database} color="#60a5fa" />
                <FileGroup title="API / Routes" files={data.important_files.api} color="#34d399" />
                <FileGroup title="ML / AI" files={data.important_files.ml} color="#a78bfa" />
                <FileGroup title="Config" files={data.important_files.config} color="#fbbf24" />
              </div>
            </SectionCard>
          )}

          {/* Architecture notes */}
          {data.architecture_notes && (
            <SectionCard title="Architecture Notes" accent="#06b6d4">
              <p style={{ fontSize: '0.875rem', color: '#a1a1aa', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
                {data.architecture_notes}
              </p>
            </SectionCard>
          )}

          {/* Needs review */}
          {data.needs_review?.length > 0 && (
            <div style={{
              background: 'rgba(245,158,11,0.06)',
              border: '1px solid rgba(245,158,11,0.18)',
              borderRadius: 10, padding: '18px 20px',
            }}>
              <p style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#fbbf24', marginBottom: 12 }}>
                ⚠ Needs Review
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {data.needs_review.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#fbbf24', fontSize: '0.7rem' }}>!</span>
                    <PathLine path={f} color="#a1a1aa" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!data && !loading && !error && (
        <EmptyState icon="📋" title="Select a repository to generate its summary" />
      )}
    </div>
  );
}
