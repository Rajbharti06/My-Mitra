import { useState } from 'react';
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

function ChatBox() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  const handleSend = async () => {
    if (!input.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: input }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { user: input, bot: data.response }]);
      setInput('');
    } catch (e) {
      setMessages((prev) => [...prev, { user: input, bot: 'Error contacting server' }]);
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div className="mb-4">
        {messages.map((m, idx) => (
          <div key={idx} style={{ marginBottom: 12 }}>
            <p><b>You:</b> {m.user}</p>
            <p><b>MyMitra:</b> {m.bot}</p>
          </div>
        ))}
      </div>
      <input
        type="text"
        className="border p-2 w-full"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your message..."
      />
      <button className="bg-blue-500 text-white p-2 mt-2" onClick={handleSend}>
        Send
      </button>
    </div>
  );
}

export default ChatBox;