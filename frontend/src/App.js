import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Chat from './Chat';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
// import Home from './pages/Home';
import Journals from './pages/Journals';
import Habits from './pages/Habits';
import NotFound from './pages/NotFound';
import Insights from './pages/Insights';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [darkMode]);

  return (
    <Router>
      <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
        <Navbar darkMode={darkMode} setDarkMode={setDarkMode} />
        <main style={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/chat" element={<Chat />} />
            <Route path="/journals" element={<Journals />} />
            <Route path="/habits" element={<Habits />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
