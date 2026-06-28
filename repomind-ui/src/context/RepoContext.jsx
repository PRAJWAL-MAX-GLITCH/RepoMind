import { createContext, useContext, useState, useCallback } from 'react';

const RepoContext = createContext(null);

export function RepoProvider({ children }) {
  // List of recently indexed repositories: [{ name, path, indexedAt }]
  const [repos, setRepos] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('repomind_repos') || '[]');
    } catch {
      return [];
    }
  });

  const addRepo = useCallback((name, path) => {
    setRepos(prev => {
      const next = [
        { name, path, indexedAt: new Date().toISOString() },
        ...prev.filter(r => r.name !== name),
      ].slice(0, 20);
      localStorage.setItem('repomind_repos', JSON.stringify(next));
      return next;
    });
  }, []);

  return (
    <RepoContext.Provider value={{ repos, addRepo }}>
      {children}
    </RepoContext.Provider>
  );
}

export function useRepos() {
  return useContext(RepoContext);
}
