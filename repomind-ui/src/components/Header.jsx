import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Circle } from 'lucide-react';
import { getHealth } from '../services/api';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/index-repo': 'Index Repository',
  '/query': 'Ask Repository',
  '/summary': 'Repository Summary',
  '/architecture': 'Architecture View',
  '/hotspots': 'Code Hotspots',
};

export default function Header() {
  const { pathname } = useLocation();
  const [health, setHealth] = useState(null); // null = checking, true = ok, false = down

  useEffect(() => {
    let alive = true;
    getHealth()
      .then(() => alive && setHealth(true))
      .catch(() => alive && setHealth(false));
    return () => { alive = false; };
  }, []);

  const title = PAGE_TITLES[pathname] || 'RepoMind';

  return (
    <header style={{
      height: 52,
      borderBottom: '1px solid #1c1c1f',
      background: 'rgba(9,9,11,0.8)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: 12,
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <h1 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fafafa', letterSpacing: '-0.01em' }}>
        {title}
      </h1>

      <div style={{ flex: 1 }} />

      {/* API health dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{
          width: 7, height: 7, borderRadius: '50%',
          background: health === null ? '#52525b' : health ? '#22c55e' : '#ef4444',
          boxShadow: health ? '0 0 8px rgba(34,197,94,0.5)' : undefined,
          transition: 'background 0.3s',
        }} />
        <span style={{ fontSize: '0.75rem', color: '#52525b' }}>
          {health === null ? 'checking…' : health ? 'API online' : 'API offline'}
        </span>
      </div>
    </header>
  );
}
