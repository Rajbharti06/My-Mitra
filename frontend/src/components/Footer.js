import React from 'react';
import './Footer.css';

function Footer() {
  const handleDownloadData = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Please log in to download your data.');
      return;
    }

    try {
      const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/me/export`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download data.');
      }

      const data = await response.json();
      const encryptedData = data.encrypted_data;

      const blob = new Blob([encryptedData], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'mymitra_encrypted_data.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      alert('Your encrypted data has been downloaded.');

    } catch (error) {
      console.error('Error downloading data:', error);
      alert(error.message || 'An error occurred while downloading data.');
    }
  };

  return (
    <footer className="footer">
      <div className="footer-inner">
        <p className="footer-text">Built with care. Your privacy comes first.</p>
        <button onClick={handleDownloadData} className="primary">Download Your Encrypted Data</button>
      </div>
    </footer>
  );
}

export default Footer;


