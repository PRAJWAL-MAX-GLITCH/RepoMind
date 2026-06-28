import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { RepoProvider } from './context/RepoContext';
import PageLayout from './components/PageLayout';
import Dashboard from './pages/Dashboard';
import IndexRepo from './pages/IndexRepo';
import Query from './pages/Query';
import Summary from './pages/Summary';
import Architecture from './pages/Architecture';
import Hotspots from './pages/Hotspots';

export default function App() {
  return (
    <RepoProvider>
      <BrowserRouter>
        <PageLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/index-repo" element={<IndexRepo />} />
            <Route path="/query" element={<Query />} />
            <Route path="/summary" element={<Summary />} />
            <Route path="/architecture" element={<Architecture />} />
            <Route path="/hotspots" element={<Hotspots />} />
          </Routes>
        </PageLayout>
      </BrowserRouter>
    </RepoProvider>
  );
}
