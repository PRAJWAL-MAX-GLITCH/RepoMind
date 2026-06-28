import Sidebar from './Sidebar';
import Header from './Header';

export default function PageLayout({ children }) {
  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: '#09090b',
    }}>
      <Sidebar />
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        overflow: 'hidden',
      }}>
        <Header />
        <main style={{
          flex: 1,
          padding: '24px 32px',
          overflowY: 'auto',
          overflowX: 'hidden',
          width: '100%',
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
