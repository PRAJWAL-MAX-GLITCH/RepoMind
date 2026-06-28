import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FolderInput, MessageSquare,
  FileText, GitBranch, Flame, ChevronRight
} from 'lucide-react';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/index-repo', icon: FolderInput, label: 'Index Repository' },
  { to: '/query', icon: MessageSquare, label: 'Ask Repo' },
  { to: '/summary', icon: FileText, label: 'Summary' },
  { to: '/architecture', icon: GitBranch, label: 'Architecture' },
  { to: '/hotspots', icon: Flame, label: 'Hotspots' },
];

export default function Sidebar() {
  return (
    <aside
      style={{
        width: 220,
        minHeight: '100vh',
        background: '#0c0c0e',
        borderRight: '1px solid #1c1c1f',
        display: 'flex',
        flexDirection: 'column',
        padding: '12px 10px',
        gap: 2,
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: '12px 10px 20px', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 30, height: 30,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 15, fontWeight: 700, color: '#fff',
            flexShrink: 0,
            boxShadow: '0 0 16px rgba(59,130,246,0.3)',
          }}>
            R
          </div>
          <span style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.02em', color: '#fafafa' }}>
            RepoMind
          </span>
        </div>
      </div>

      <p className="section-label" style={{ paddingLeft: 10, marginBottom: 6 }}>Navigation</p>

      {NAV.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 10px',
            borderRadius: 7,
            fontSize: '0.875rem',
            fontWeight: isActive ? 600 : 400,
            color: isActive ? '#fff' : '#71717a',
            background: isActive ? 'rgba(59,130,246,0.12)' : 'transparent',
            border: isActive ? '1px solid rgba(59,130,246,0.2)' : '1px solid transparent',
            textDecoration: 'none',
            transition: 'all 0.12s',
          })}
        >
          {({ isActive }) => (
            <>
              <Icon size={15} style={{ color: isActive ? '#60a5fa' : '#52525b', flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{label}</span>
              {isActive && <ChevronRight size={13} style={{ color: '#60a5fa', opacity: 0.6 }} />}
            </>
          )}
        </NavLink>
      ))}

      <div style={{ flex: 1 }} />

      <div style={{
        padding: '10px',
        borderRadius: 8,
        background: '#111113',
        border: '1px solid #1c1c1f',
        marginTop: 8,
      }}>
        <p style={{ fontSize: '0.7rem', color: '#52525b', marginBottom: 4 }}>Backend API</p>
        <p className="mono" style={{ fontSize: '0.7rem', color: '#3f3f46' }}>localhost:8080</p>
      </div>
    </aside>
  );
}
