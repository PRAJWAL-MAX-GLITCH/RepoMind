import { useState, useRef, useCallback, useEffect } from 'react';
import { useRepos } from '../context/RepoContext';
import { scanRepository, indexRepository } from '../services/api';
import { PathLine, ErrorAlert, SuccessAlert, TagList, SectionCard } from '../components/ui';
import {
  FolderOpen, ScanLine, FileText, Code2, Layers,
  CheckCircle2, ArrowRight, RotateCcw, ChevronRight,
} from 'lucide-react';

// ── Step constants ────────────────────────────────────────────────────────
const STEP = { IDLE: 0, SCANNING: 1, SCANNED: 2, INDEXING: 3, DONE: 4 };

// ── Language colour map ───────────────────────────────────────────────────
const LANG_COLOR = {
  Python: '#3b82f6', JavaScript: '#f59e0b', 'JavaScript (JSX)': '#f59e0b',
  TypeScript: '#06b6d4', 'TypeScript (TSX)': '#06b6d4',
  Java: '#ef4444', 'C++': '#8b5cf6', C: '#6b7280', 'C/C++ Header': '#6b7280',
  Markdown: '#a1a1aa', JSON: '#22c55e', YAML: '#fbbf24',
};
const langColor = (l) => LANG_COLOR[l] || '#60a5fa';

// ── Animated progress bar ─────────────────────────────────────────────────
function ProgressBar({ percent, label, sublabel }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>{label}</span>
        <span style={{ fontSize: '0.8rem', color: '#60a5fa', fontWeight: 700 }}>{percent}%</span>
      </div>
      <div style={{ height: 8, background: '#1c1c1f', borderRadius: 99, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${percent}%`,
          background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
          borderRadius: 99,
          transition: 'width 0.4s ease',
          boxShadow: '0 0 12px rgba(59,130,246,0.4)',
        }} />
      </div>
      {sublabel && <p style={{ fontSize: '0.72rem', color: '#52525b', marginTop: 5 }}>{sublabel}</p>}
    </div>
  );
}

// ── Stat tile ─────────────────────────────────────────────────────────────
function StatTile({ icon: Icon, iconColor, bgColor, borderColor, label, value, sub }) {
  return (
    <div style={{
      background: '#0c0c0e', border: `1px solid ${borderColor}`,
      borderRadius: 12, padding: '18px 20px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 8,
          background: bgColor, border: `1px solid ${borderColor}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <Icon size={16} color={iconColor} />
        </div>
        <span className="section-label">{label}</span>
      </div>
      <div>
        <p style={{ fontSize: '2rem', fontWeight: 800, color: iconColor, letterSpacing: '-0.04em', lineHeight: 1 }}>
          {value}
        </p>
        {sub && <p style={{ fontSize: '0.72rem', color: '#52525b', marginTop: 5 }}>{sub}</p>}
      </div>
    </div>
  );
}

// ── Step indicator ────────────────────────────────────────────────────────
function StepIndicator({ current }) {
  const steps = ['Browse', 'Scan', 'Review', 'Index', 'Done'];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 28 }}>
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={s} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: done ? '#22c55e' : active ? '#3b82f6' : '#1c1c1f',
                border: `2px solid ${done ? '#22c55e' : active ? '#3b82f6' : '#27272a'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, transition: 'all 0.2s',
              }}>
                {done
                  ? <CheckCircle2 size={14} color="#fff" />
                  : <span style={{ fontSize: '0.65rem', fontWeight: 700, color: active ? '#fff' : '#52525b' }}>{i + 1}</span>
                }
              </div>
              <span style={{
                fontSize: '0.75rem', fontWeight: active ? 700 : 500,
                color: done ? '#4ade80' : active ? '#60a5fa' : '#52525b',
              }}>{s}</span>
            </div>
            {i < steps.length - 1 && (
              <div style={{ width: 32, height: 1, background: done ? '#22c55e40' : '#27272a', margin: '0 6px', flexShrink: 0 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
export default function IndexRepo() {
  const { repos, addRepo } = useRepos();
  const [step, setStep] = useState(STEP.IDLE);
  const [path, setPath] = useState('');
  const [scanData, setScanData] = useState(null);
  const [indexResult, setIndexResult] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const folderInputRef = useRef(null);
  const progressTimerRef = useRef(null);

  // ── Cleanup on unmount ──────────────────────────────────────────────────
  useEffect(() => () => clearInterval(progressTimerRef.current), []);

  // ── Folder picker handler ───────────────────────────────────────────────
  function handleFolderPick(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const root = files[0].webkitRelativePath.split('/')[0];
    setPath(root);
    setError('');
    setStep(STEP.IDLE);
    setScanData(null);
    setIndexResult(null);
  }

  // ── Drag & drop ─────────────────────────────────────────────────────────
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const items = e.dataTransfer.items;
    for (let i = 0; i < (items?.length || 0); i++) {
      const entry = items[i].webkitGetAsEntry?.();
      if (entry?.isDirectory) {
        setPath(entry.name);
        setError('');
        setScanData(null);
        setIndexResult(null);
        setStep(STEP.IDLE);
        return;
      }
    }
    setError('Drop a project folder, not individual files.');
  }, []);

  // ── Scan ────────────────────────────────────────────────────────────────
  async function handleScan() {
    const p = path.trim();
    if (!p) { setError('Enter or select a repository path first.'); return; }
    setError('');
    setStep(STEP.SCANNING);
    try {
      const data = await scanRepository(p);
      setScanData(data);
      setStep(STEP.SCANNED);
    } catch (e) {
      setError(e.message);
      setStep(STEP.IDLE);
    }
  }

  // ── Animated progress during indexing ──────────────────────────────────
  function startProgressAnimation(estimatedChunks) {
    setProgress(0);
    // Estimate ~0.5s per chunk capped at 3min total
    const totalMs = Math.min(estimatedChunks * 500, 180_000);
    const intervalMs = 300;
    const increment = (intervalMs / totalMs) * 92; // go to ~92% then stop
    const stages = [
      [0,  15,  'Scanning files…'],
      [15, 40,  'Chunking source code…'],
      [40, 75,  'Generating embeddings…'],
      [75, 92,  'Storing vectors…'],
    ];
    let current = 0;
    progressTimerRef.current = setInterval(() => {
      current = Math.min(current + increment, 92);
      setProgress(Math.round(current));
      const stage = stages.find(([lo, hi]) => current >= lo && current < hi);
      if (stage) setProgressLabel(stage[2]);
    }, intervalMs);
  }

  // ── Index ───────────────────────────────────────────────────────────────
  async function handleIndex() {
    const p = path.trim();
    setError('');
    setStep(STEP.INDEXING);
    startProgressAnimation(scanData?.estimated_chunks || 200);
    try {
      const data = await indexRepository(p);
      clearInterval(progressTimerRef.current);
      setProgress(100);
      setProgressLabel('Done!');
      setIndexResult(data);
      addRepo(data.repo_name || p.replace(/\\/g, '/').split('/').filter(Boolean).pop(), p);
      setTimeout(() => setStep(STEP.DONE), 400);
    } catch (e) {
      clearInterval(progressTimerRef.current);
      setError(e.message);
      setStep(STEP.SCANNED);
      setProgress(0);
    }
  }

  // ── Reset ───────────────────────────────────────────────────────────────
  function handleReset() {
    setStep(STEP.IDLE);
    setPath('');
    setScanData(null);
    setIndexResult(null);
    setError('');
    setProgress(0);
    if (folderInputRef.current) folderInputRef.current.value = '';
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ width: '100%', maxWidth: 920, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 className="page-title">Index Repository</h1>
        <p className="page-subtitle">Scan a local project folder, preview what will be indexed, then embed it into the vector store.</p>
      </div>

      <StepIndicator current={step} />

      {/* ── STEP 0 + 1: Browse & Scan ─────────────────────────────────── */}
      {step <= STEP.SCANNING && (
        <div
          className="card"
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            padding: '32px 28px',
            outline: dragOver ? '2px solid #3b82f6' : '2px solid transparent',
            transition: 'outline 0.15s', marginBottom: 16,
          }}
        >
          <p className="section-label" style={{ marginBottom: 10 }}>Repository Path</p>

          {/* Path row */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <input
              className="input-base mono"
              type="text"
              value={path}
              onChange={e => { setPath(e.target.value); setError(''); }}
              onKeyDown={e => e.key === 'Enter' && path.trim() && step === STEP.IDLE && handleScan()}
              placeholder="e.g.  D:\Projects\my-repo   or   /home/user/project"
              disabled={step === STEP.SCANNING}
              style={{ flex: 1 }}
            />
            <button
              className="btn-secondary"
              onClick={() => folderInputRef.current?.click()}
              disabled={step === STEP.SCANNING}
              style={{ gap: 7, whiteSpace: 'nowrap' }}
            >
              <FolderOpen size={15} /> Browse Folder
            </button>
            <input
              ref={folderInputRef}
              type="file"
              webkitdirectory=""
              directory=""
              multiple
              style={{ display: 'none' }}
              onChange={handleFolderPick}
            />
          </div>

          <p style={{ fontSize: '0.72rem', color: '#3f3f46', marginBottom: 24 }}>
            You can also drag & drop a project folder onto this card.
          </p>

          <button
            className="btn-primary"
            onClick={handleScan}
            disabled={!path.trim() || step === STEP.SCANNING}
            style={{ width: '100%', justifyContent: 'center', padding: '13px', fontSize: '0.95rem' }}
          >
            {step === STEP.SCANNING ? (
              <>
                <span style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.65s linear infinite', display: 'inline-block' }} />
                Scanning Repository…
              </>
            ) : (
              <><ScanLine size={16} /> Scan Repository</>
            )}
          </button>
        </div>
      )}

      {/* ── STEP 2: Scanned — show preview + Index button ─────────────── */}
      {step === STEP.SCANNED && scanData && (
        <>
          {/* Stats row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 16 }}>
            <StatTile
              icon={FileText} iconColor="#60a5fa"
              bgColor="rgba(59,130,246,0.1)" borderColor="rgba(59,130,246,0.2)"
              label="Detected Files"
              value={scanData.total_files}
              sub="Source files found (ignoring node_modules, .git, dist…)"
            />
            <StatTile
              icon={Code2} iconColor="#a78bfa"
              bgColor="rgba(139,92,246,0.1)" borderColor="rgba(139,92,246,0.2)"
              label="Detected Languages"
              value={Object.keys(scanData.languages).length}
              sub={Object.keys(scanData.languages).join(', ') || '—'}
            />
            <StatTile
              icon={Layers} iconColor="#4ade80"
              bgColor="rgba(34,197,94,0.1)" borderColor="rgba(34,197,94,0.2)"
              label="Estimated Chunks"
              value={scanData.estimated_chunks.toLocaleString()}
              sub="Based on line count ÷ 40 lines/chunk"
            />
          </div>

          {/* Language breakdown */}
          <div className="card" style={{ padding: '20px 22px', marginBottom: 16 }}>
            <p className="section-label" style={{ marginBottom: 14 }}>Language Breakdown</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {Object.entries(scanData.languages)
                .sort((a, b) => b[1] - a[1])
                .map(([lang, count]) => {
                  const total = Object.values(scanData.languages).reduce((s, v) => s + v, 0);
                  const pct = Math.round((count / total) * 100);
                  const color = langColor(lang);
                  return (
                    <div key={lang}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: '0.8rem', color: '#e4e4e7' }}>{lang}</span>
                        <span style={{ fontSize: '0.75rem', color: '#71717a' }}>{count} file{count !== 1 ? 's' : ''} · {pct}%</span>
                      </div>
                      <div style={{ height: 5, background: '#1c1c1f', borderRadius: 99 }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 99, minWidth: 4 }} />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Sample files */}
          {scanData.sample_files?.length > 0 && (
            <div className="card" style={{ padding: '20px 22px', marginBottom: 16 }}>
              <p className="section-label" style={{ marginBottom: 12 }}>Sample Files (first 20)</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 180, overflowY: 'auto' }}>
                {scanData.sample_files.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ChevronRight size={11} color="#3f3f46" />
                    <PathLine path={f} color="#71717a" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Repo strip */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
            borderRadius: 10, padding: '12px 16px', marginBottom: 16,
          }}>
            <span style={{ fontSize: 18 }}>📁</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontWeight: 700, fontSize: '0.9rem', color: '#fafafa' }}>{scanData.repo_name}</p>
              <p className="mono" style={{ fontSize: '0.72rem', color: '#52525b', wordBreak: 'break-all' }}>{path.trim()}</p>
            </div>
            <button className="btn-secondary" onClick={handleReset} style={{ gap: 6, fontSize: '0.78rem', padding: '6px 12px' }}>
              <RotateCcw size={12} /> Change
            </button>
          </div>

          <ErrorAlert message={error} />

          {/* Index button */}
          <button
            className="btn-primary"
            onClick={handleIndex}
            style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '0.95rem' }}
          >
            <ArrowRight size={16} /> Index Repository
          </button>
        </>
      )}

      {/* ── STEP 3: Indexing — progress bar ───────────────────────────── */}
      {step === STEP.INDEXING && (
        <div className="card" style={{ padding: '36px 32px', marginBottom: 16 }}>
          <div style={{ marginBottom: 28 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <div style={{ width: 36, height: 36, borderRadius: 9, background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ width: 16, height: 16, border: '2.5px solid rgba(96,165,250,0.2)', borderTopColor: '#60a5fa', borderRadius: '50%', animation: 'spin 0.65s linear infinite', display: 'inline-block' }} />
              </div>
              <div>
                <p style={{ fontWeight: 700, color: '#fafafa', fontSize: '0.95rem' }}>Indexing {scanData?.repo_name}</p>
                <p style={{ fontSize: '0.75rem', color: '#52525b' }}>Scanning · Chunking · Embedding · Storing</p>
              </div>
            </div>
            <ProgressBar
              percent={progress}
              label={progressLabel || 'Initialising…'}
              sublabel={`${scanData?.total_files || '?'} files · ~${scanData?.estimated_chunks || '?'} chunks estimated`}
            />
          </div>

          {/* Mini stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {[
              { label: 'Files', value: scanData?.total_files ?? '—', color: '#60a5fa' },
              { label: 'Languages', value: Object.keys(scanData?.languages || {}).length, color: '#a78bfa' },
              { label: 'Est. Chunks', value: scanData?.estimated_chunks?.toLocaleString() ?? '—', color: '#4ade80' },
            ].map(item => (
              <div key={item.label} style={{ background: '#0c0c0e', border: '1px solid #1c1c1f', borderRadius: 8, padding: '12px 14px', textAlign: 'center' }}>
                <p style={{ fontSize: '1.2rem', fontWeight: 700, color: item.color }}>{item.value}</p>
                <p className="section-label" style={{ marginTop: 4 }}>{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── STEP 4: Done — success report ─────────────────────────────── */}
      {step === STEP.DONE && indexResult && (
        <>
          {/* Success banner */}
          <div style={{
            background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)',
            borderRadius: 12, padding: '20px 24px', marginBottom: 20,
            display: 'flex', alignItems: 'center', gap: 14,
          }}>
            <CheckCircle2 size={28} color="#22c55e" />
            <div>
              <p style={{ fontWeight: 700, color: '#4ade80', fontSize: '1rem' }}>
                Successfully indexed "{indexResult.repo_name}"
              </p>
              <p style={{ fontSize: '0.8rem', color: '#52525b', marginTop: 3 }}>
                Stored at: <span className="mono" style={{ color: '#3f3f46' }}>{indexResult.index_location}</span>
              </p>
            </div>
            <button className="btn-secondary" onClick={handleReset} style={{ marginLeft: 'auto', gap: 6, whiteSpace: 'nowrap' }}>
              <RotateCcw size={13} /> Index Another
            </button>
          </div>

          {/* Report cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              { label: 'Repo Name', value: indexResult.repo_name, mono: true, color: '#fafafa' },
              { label: 'Chunks Created', value: indexResult.chunks_created ?? 0, color: '#3b82f6' },
              { label: 'Files Indexed', value: indexResult.files_indexed?.length ?? 0, color: '#22c55e' },
              { label: 'Files Skipped', value: indexResult.skipped_files?.length ?? 0, color: '#f59e0b' },
            ].map(item => (
              <div key={item.label} className="card" style={{ padding: '16px 18px' }}>
                <p className="section-label" style={{ marginBottom: 8 }}>{item.label}</p>
                <p className={item.mono ? 'mono' : ''} style={{
                  fontSize: item.mono ? '0.85rem' : '1.5rem', fontWeight: 700,
                  color: item.color, letterSpacing: item.mono ? undefined : '-0.03em',
                  wordBreak: 'break-all',
                }}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>

          {indexResult.languages_detected?.length > 0 && (
            <SectionCard title="Languages Detected" accent="#8b5cf6">
              <TagList items={indexResult.languages_detected} variant="violet" />
            </SectionCard>
          )}

          {indexResult.files_indexed?.length > 0 && (
            <SectionCard title={`Indexed Files (${indexResult.files_indexed.length})`} accent="#22c55e">
              <div style={{ maxHeight: 260, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {indexResult.files_indexed.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#4ade80', fontSize: '0.7rem', flexShrink: 0 }}>✓</span>
                    <PathLine path={f} color="#a1a1aa" />
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {indexResult.skipped_files?.length > 0 && (
            <SectionCard title={`Skipped Files (${indexResult.skipped_files.length})`} accent="#f59e0b">
              <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {indexResult.skipped_files.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#fbbf24', fontSize: '0.7rem', flexShrink: 0 }}>–</span>
                    <PathLine path={f} color="#71717a" />
                  </div>
                ))}
              </div>
            </SectionCard>
          )}
        </>
      )}

      {/* Global error (for steps 0–1) */}
      {step <= STEP.IDLE && <ErrorAlert message={error} />}

      {/* ── Recently Indexed ──────────────────────────────────────────── */}
      {repos.length > 0 && step !== STEP.INDEXING && (
        <div style={{ marginTop: 36 }}>
          <p className="section-label" style={{ marginBottom: 12 }}>Recently Indexed</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {repos.slice(0, 6).map(r => (
              <div
                key={r.name}
                className="card"
                style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', transition: 'border-color 0.12s' }}
                onClick={() => { setPath(r.path); setStep(STEP.IDLE); setScanData(null); setIndexResult(null); setError(''); }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#27272a'}
              >
                <span style={{ fontSize: 15 }}>📦</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fafafa' }}>{r.name}</p>
                  <PathLine path={r.path} color="#52525b" />
                </div>
                <span style={{ fontSize: '0.7rem', color: '#3f3f46', flexShrink: 0 }}>
                  {new Date(r.indexedAt).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
