import React from 'react';

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
    <footer style={{
      borderTop: '1px solid #e6e9ef',
      padding: '24px 20px',
      background: '#ffffff',
      color: '#5f6b7a',
      textAlign: 'center'
    }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <p style={{ margin: 0 }}>Built with care. Your privacy comes first.</p>
        <button 
          onClick={handleDownloadData}
          style={{
            marginTop: '10px',
            padding: '8px 15px',
            backgroundColor: '#3a6ea5',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.9em',
            transition: 'background-color 0.2s ease'
          }}
        >
          Download Your Encrypted Data
        </button>
      </div>
    </footer>
  );
}

export default Footer;


