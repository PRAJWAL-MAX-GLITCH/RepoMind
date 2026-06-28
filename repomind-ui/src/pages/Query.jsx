import { useState } from 'react';
import { useRepos } from '../context/RepoContext';
import { queryRepository } from '../services/api';
import {
  LoadingSpinner, ErrorAlert, EmptyState,
  SectionCard, SourceChunkCard, RepoSelector,
} from '../components/ui';

export default function Query() {
  const { repos } = useRepos();
  const [repoName, setRepoName] = useState('');
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  async function handleQuery() {
    if (!repoName.trim() || !question.trim()) {
      setError('Please enter both a repository name and a question.');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const data = await queryRepository(repoName.trim(), question.trim(), topK);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Ask Repository</h1>
        <p className="page-subtitle">Ask a natural-language question — answers include file paths and line citations from your indexed code.</p>
      </div>

      {/* Query form */}
      <div className="card" style={{ padding: '22px 24px', marginBottom: 20 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <RepoSelector repos={repos} value={repoName} onChange={setRepoName} />

          <div>
            <label className="section-label" style={{ display: 'block', marginBottom: 6 }}>Question</label>
            <textarea
              className="input-base"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) handleQuery(); }}
              placeholder="e.g. How does authentication work? Where is the database connection setup?"
              rows={3}
              disabled={loading}
              style={{ resize: 'vertical' }}
            />
            <p style={{ fontSize: '0.72rem', color: '#52525b', marginTop: 4 }}>Ctrl+Enter to submit</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div>
              <label className="section-label" style={{ display: 'block', marginBottom: 6 }}>Top-K Chunks</label>
              <input
                type="number" min={1} max={20}
                className="input-base"
                value={topK}
                onChange={e => setTopK(Number(e.target.value))}
                style={{ width: 80 }}
              />
            </div>
            <div style={{ flex: 1 }} />
            <button
              className="btn-primary"
              onClick={handleQuery}
              disabled={loading || !repoName.trim() || !question.trim()}
              style={{ alignSelf: 'flex-end' }}
            >
              {loading ? <LoadingSpinner size={15} color="#fff" /> : '🔍'}
              {loading ? 'Searching…' : 'Search & Answer'}
            </button>
          </div>
        </div>
      </div>

      <ErrorAlert message={error} />

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '24px 0', color: '#52525b' }}>
          <LoadingSpinner />
          <span style={{ fontSize: '0.875rem' }}>Running semantic search and generating answer…</span>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* Answer */}
          <div style={{
            background: 'rgba(59,130,246,0.05)',
            border: '1px solid rgba(59,130,246,0.18)',
            borderRadius: 10, padding: '20px 22px', marginBottom: 20,
          }}>
            <p style={{
              fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em',
              textTransform: 'uppercase', color: '#60a5fa', marginBottom: 12,
            }}>
              Answer · {result.repo_name}
            </p>
            <p style={{ fontSize: '0.925rem', lineHeight: 1.75, color: '#e4e4e7', whiteSpace: 'pre-wrap' }}>
              {result.answer || '(No answer returned)'}
            </p>
          </div>

          {/* Source chunks */}
          {result.source_chunks?.length > 0 ? (
            <SectionCard title={`Source Citations · ${result.source_chunks.length} chunk${result.source_chunks.length !== 1 ? 's' : ''}`} accent="#8b5cf6">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {result.source_chunks.map((chunk, i) => (
                  <SourceChunkCard key={i} chunk={chunk} index={i} />
                ))}
              </div>
            </SectionCard>
          ) : (
            <EmptyState icon="📎" title="No source chunks returned" subtitle="The model answered from its context without direct chunk references." />
          )}
        </>
      )}

      {/* Initial empty */}
      {!result && !loading && !error && (
        <EmptyState
          icon="💬"
          title="Ask your first question"
          subtitle="Enter a repo name and question above. Results will show the answer plus the exact file lines used."
        />
      )}
    </div>
  );
}
