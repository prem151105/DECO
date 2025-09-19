import React, { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';

function EmployeeDashboard() {
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const { logout } = useAuth();

  useEffect(() => {
    fetchMyDocuments();
  }, []);

  const fetchMyDocuments = async () => {
    try {
      const response = await api.get('/my-documents');
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await api.post('/search', {
        query: searchQuery,
        search_type: 'hybrid'
      });
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  return (
    <div>
      <h1>Employee Dashboard</h1>
      <button onClick={logout}>Logout</button>
      
      <h2>Search Documents</h2>
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Enter search terms..."
      />
      <button onClick={handleSearch}>Search</button>
      
      <h3>Search Results</h3>
      {searchResults.map(doc => (
        <div key={doc.id}>
          <h4>{doc.filename}</h4>
          <p>{doc.quick?.summary || 'No summary available'}</p>
        </div>
      ))}
      
      <h3>My Documents</h3>
      {documents.map(doc => (
        <div key={doc.id}>
          <h4>{doc.filename}</h4>
          <p>{doc.quick?.summary || 'No summary available'}</p>
        </div>
      ))}
    </div>
  );
}

export default EmployeeDashboard;