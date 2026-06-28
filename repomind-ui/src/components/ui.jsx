// Reusable UI primitives

// ── LoadingSpinner ─────────────────────────────────────────────────
export function LoadingSpinner({ size = 18, color = '#3b82f6' }) {
  return (
    <div style={{
      width: size, height: size,
      border: `2px solid rgba(255,255,255,0.08)`,
      borderTopColor: color,
      borderRadius: '50%',
      animation: 'spin 0.65s linear infinite',
      display: 'inline-block',
      flexShrink: 0,
    }} />
  );
}

// ── LoadingState ───────────────────────────────────────────────────
export function LoadingState({ message = 'Loading…' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '40px 0', color: '#52525b' }}>
      <LoadingSpinner />
      <span style={{ fontSize: '0.875rem' }}>{message}</span>
    </div>
  );
}

// ── EmptyState ─────────────────────────────────────────────────────
export function EmptyState({ icon = '📂', title, subtitle }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '60px 20px', gap: 10,
      border: '1px dashed #27272a', borderRadius: 12,
    }}>
      <div style={{ fontSize: 32, opacity: 0.4 }}>{icon}</div>
      <p style={{ fontWeight: 600, color: '#71717a', fontSize: '0.9rem' }}>{title}</p>
      {subtitle && <p style={{ fontSize: '0.8rem', color: '#52525b', textAlign: 'center', maxWidth: 320 }}>{subtitle}</p>}
    </div>
  );
}

// ── ErrorAlert ─────────────────────────────────────────────────────
export function ErrorAlert({ message }) {
  if (!message) return null;
  return (
    <div style={{
      background: 'rgba(239,68,68,0.07)',
      border: '1px solid rgba(239,68,68,0.2)',
      borderRadius: 8, padding: '12px 16px',
      display: 'flex', gap: 10, alignItems: 'flex-start',
      marginBottom: 16,
    }}>
      <span style={{ fontSize: '0.85rem', flexShrink: 0 }}>⚠️</span>
      <p style={{ fontSize: '0.85rem', color: '#fca5a5', lineHeight: 1.5, fontFamily: 'inherit' }}>{message}</p>
    </div>
  );
}

// ── SuccessAlert ───────────────────────────────────────────────────
export function SuccessAlert({ message }) {
  if (!message) return null;
  return (
    <div style={{
      background: 'rgba(34,197,94,0.07)',
      border: '1px solid rgba(34,197,94,0.2)',
      borderRadius: 8, padding: '12px 16px',
      display: 'flex', gap: 10, alignItems: 'flex-start',
      marginBottom: 16,
    }}>
      <span style={{ fontSize: '0.85rem', flexShrink: 0 }}>✓</span>
      <p style={{ fontSize: '0.85rem', color: '#86efac', lineHeight: 1.5 }}>{message}</p>
    </div>
  );
}

// ── StatCard ───────────────────────────────────────────────────────
export function StatCard({ icon, label, value, color = '#3b82f6' }) {
  return (
    <div className="card" style={{ padding: '20px 22px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <p className="section-label" style={{ marginBottom: 8 }}>{label}</p>
          <p style={{ fontSize: '1.6rem', fontWeight: 700, color, letterSpacing: '-0.03em' }}>{value}</p>
        </div>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: `${color}18`,
          border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 17,
        }}>{icon}</div>
      </div>
    </div>
  );
}

// ── SectionCard ────────────────────────────────────────────────────
export function SectionCard({ title, children, accent = '#3b82f6' }) {
  return (
    <div className="card" style={{ padding: '20px 22px', marginBottom: 16 }}>
      <div style={{
        fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: accent, marginBottom: 14,
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {title}
      </div>
      {children}
    </div>
  );
}

// ── Badge ──────────────────────────────────────────────────────────
export function Badge({ children, variant = 'zinc' }) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}

// ── TagList ────────────────────────────────────────────────────────
export function TagList({ items = [], variant = 'zinc' }) {
  if (!items?.length) return <span style={{ fontSize: '0.8rem', color: '#52525b' }}>—</span>;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {items.map((item, i) => <Badge key={i} variant={variant}>{item}</Badge>)}
    </div>
  );
}

// ── PathLine ───────────────────────────────────────────────────────
export function PathLine({ path, color = '#60a5fa' }) {
  return (
    <span className="mono" style={{ fontSize: '0.78rem', color, wordBreak: 'break-all' }}>{path}</span>
  );
}

// ── RepoSelector ───────────────────────────────────────────────────
export function RepoSelector({ repos = [], value, onChange, onPathChange, repoPath }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <label className="section-label" style={{ display: 'block', marginBottom: 6 }}>Repository Name</label>
        <input
          type="text"
          className="input-base"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder="e.g. my-repo"
          list="repo-datalist"
        />
        {repos.length > 0 && (
          <datalist id="repo-datalist">
            {repos.map(r => <option key={r.name} value={r.name} />)}
          </datalist>
        )}
      </div>
      {onPathChange !== undefined && (
        <div>
          <label className="section-label" style={{ display: 'block', marginBottom: 6 }}>
            Repository Path <span style={{ color: '#52525b', textTransform: 'none', letterSpacing: 0 }}>(optional — for richer analysis)</span>
          </label>
          <input
            type="text"
            className="input-base mono"
            value={repoPath}
            onChange={e => onPathChange(e.target.value)}
            placeholder="e.g. D:\Projects\my-repo"
          />
        </div>
      )}
    </div>
  );
}

// ── SourceChunkCard ────────────────────────────────────────────────
export function SourceChunkCard({ chunk, index }) {
  return (
    <div style={{
      background: '#111113',
      border: '1px solid #27272a',
      borderRadius: 8,
      overflow: 'hidden',
    }}>
      {/* header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
        padding: '10px 14px',
        borderBottom: '1px solid #1c1c1f',
        background: '#0c0c0e',
      }}>
        <Badge variant="zinc">#{index + 1}</Badge>
        <PathLine path={chunk.file_path || chunk.file_name || '?'} />
        {chunk.start_line != null && (
          <span style={{ fontSize: '0.72rem', color: '#52525b', fontFamily: 'monospace' }}>
            L{chunk.start_line}–{chunk.end_line ?? chunk.start_line}
          </span>
        )}
        {chunk.language && chunk.language !== 'unknown' && (
          <Badge variant="blue">{chunk.language}</Badge>
        )}
        {chunk.chunk_type && chunk.chunk_type !== 'block' && (
          <Badge variant="violet">{chunk.chunk_type}</Badge>
        )}
        {chunk.symbol_name && (
          <span className="mono" style={{ fontSize: '0.72rem', color: '#71717a' }}>{chunk.symbol_name}</span>
        )}
      </div>
      {/* content */}
      {chunk.content && (
        <pre style={{
          padding: '12px 14px', margin: 0,
          fontSize: '0.78rem', lineHeight: 1.7,
          color: '#a1a1aa',
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          overflowX: 'auto',
          maxHeight: 220,
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {chunk.content}
        </pre>
      )}
    </div>
  );
}
