import { useNavigate } from 'react-router-dom';
import { useRepos } from '../context/RepoContext';
import { StatCard, EmptyState, PathLine, Badge } from '../components/ui';
import { FolderInput, MessageSquare, FileText, GitBranch, Flame } from 'lucide-react';

const QUICK_ACTIONS = [
  { icon: '📂', label: 'Index Repository', sub: 'Scan, chunk & embed a local repo', to: '/index-repo', color: '#3b82f6' },
  { icon: '💬', label: 'Ask Repo', sub: 'Natural-language Q&A with citations', to: '/query', color: '#8b5cf6' },
  { icon: '🏗️', label: 'Architecture', sub: 'Structural overview of your codebase', to: '/architecture', color: '#22c55e' },
  { icon: '📋', label: 'Summary', sub: 'Developer onboarding summary', to: '/summary', color: '#f59e0b' },
  { icon: '🔥', label: 'Hotspots', sub: 'Flag risky or complex files', to: '/hotspots', color: '#ef4444' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { repos } = useRepos();

  return (
    <div style={{ width: '100%' }}>
      {/* Hero */}
      <div style={{ marginBottom: 32 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: 99, padding: '4px 12px', marginBottom: 16,
        }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#3b82f6', boxShadow: '0 0 8px #3b82f6' }} />
          <span style={{ fontSize: '0.72rem', color: '#60a5fa', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Local · Private · AI-Powered
          </span>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1.2, marginBottom: 10 }}>
          Local Code Intelligence<br />
          <span style={{ color: '#3b82f6' }}>Platform</span>
        </h1>
        <p style={{ fontSize: '0.9rem', color: '#71717a', maxWidth: 600, lineHeight: 1.6 }}>
          Index any local repository, ask developer questions, analyze architecture,
          and find risky files — all running on your machine.
        </p>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
        <StatCard icon="📦" label="Repos Indexed" value={repos.length} color="#3b82f6" />
        <StatCard icon="⚡" label="RAG Pipeline" value="Active" color="#22c55e" />
        <StatCard icon="🔒" label="Privacy" value="100%" color="#8b5cf6" />
        <StatCard icon="🌐" label="API Port" value=":8080" color="#f59e0b" />
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: 28 }}>
        <p className="section-label" style={{ marginBottom: 12 }}>Quick Actions</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
          {QUICK_ACTIONS.map(({ icon, label, sub, to, color }) => (
            <button
              key={to}
              onClick={() => navigate(to)}
              style={{
                background: '#111113',
                border: '1px solid #27272a',
                borderRadius: 10, padding: '16px 18px',
                textAlign: 'left', cursor: 'pointer',
                transition: 'border-color 0.15s, background 0.15s',
                display: 'flex', flexDirection: 'column', gap: 6,
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = `${color}40`;
                e.currentTarget.style.background = `${color}08`;
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = '#27272a';
                e.currentTarget.style.background = '#111113';
              }}
            >
              <span style={{ fontSize: 20 }}>{icon}</span>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fafafa' }}>{label}</span>
              <span style={{ fontSize: '0.78rem', color: '#71717a', lineHeight: 1.4 }}>{sub}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Repos */}
      <div>
        <p className="section-label" style={{ marginBottom: 12 }}>Recent Repositories</p>
        {repos.length === 0 ? (
          <EmptyState
            icon="📂"
            title="No repositories indexed yet"
            subtitle="Go to Index Repository to scan your first codebase"
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {repos.slice(0, 8).map(repo => (
              <div
                key={repo.name}
                className="card"
                style={{
                  padding: '12px 16px',
                  display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer',
                  transition: 'border-color 0.12s',
                }}
                onClick={() => navigate('/query')}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#27272a'}
              >
                <div style={{
                  width: 32, height: 32, borderRadius: 7,
                  background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, flexShrink: 0,
                }}>📦</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#fafafa' }}>{repo.name}</p>
                  <PathLine path={repo.path} color="#52525b" />
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: '0.7rem', color: '#52525b' }}>
                    {new Date(repo.indexedAt).toLocaleDateString()}
                  </p>
                  <Badge variant="green">indexed</Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
