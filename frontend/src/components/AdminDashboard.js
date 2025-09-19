import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';

function AdminDashboard() {
  const [file, setFile] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState('');
  const { logout } = useAuth();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleRecipientsChange = (userId) => {
    setRecipients(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId) 
        : [...prev, userId]
    );
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file');
      return;
    }
    if (recipients.length === 0) {
      setMessage('Please select recipients');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('recipients', JSON.stringify(recipients));

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(response.data.message);
      setFile(null);
      setRecipients([]);
    } catch (error) {
      setMessage('Upload failed');
    }
  };

  return (
    <div>
      <h1>Admin Dashboard</h1>
      <button onClick={logout}>Logout</button>
      
      <h2>Upload Document</h2>
      <input type="file" onChange={handleFileChange} />
      
      <h3>Select Recipients</h3>
      {users.map(user => (
        <div key={user.id}>
          <input
            type="checkbox"
            checked={recipients.includes(user.id)}
            onChange={() => handleRecipientsChange(user.id)}
          />
          {user.username} ({user.email})
        </div>
      ))}
      
      <button onClick={handleUpload}>Upload and Process</button>
      {message && <p>{message}</p>}
    </div>
  );
}

export default AdminDashboard;