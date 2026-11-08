import { Navigate, Route, Routes } from 'react-router-dom';
import DesignPage from './DesignPage';

export default function App() {
  return <Routes>
    {import.meta.env.DEV && <Route path="/design" element={<DesignPage/>}/>}
    <Route path="/" element={<Navigate to={import.meta.env.DEV ? '/design' : '/not-found'} replace/>}/>
    <Route path="*" element={<main className="design-page"><h1>Page not found</h1></main>}/>
  </Routes>;
}
