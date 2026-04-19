import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AdminLogin = ({ adminPath }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const existingToken = localStorage.getItem('admin_token');
    if (existingToken) {
      navigate(`${adminPath}/dashboard`, { replace: true });
    }
  }, [adminPath, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Admin login failed');
      }

      const data = await response.json();
      localStorage.setItem('admin_token', data.access_token);
      navigate(`${adminPath}/dashboard`, { replace: true });
    } catch (err) {
      setError(err.message || 'Admin login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-auth-page">
      <div className="admin-auth-card">
        <p className="admin-auth-eyebrow">Secure Access</p>
        <h1>Administrative Login</h1>
        <p className="admin-auth-copy">
          Sign in with your configured administrator credentials.
        </p>

        <form className="admin-auth-form" onSubmit={handleSubmit}>
          <label htmlFor="admin-username">Username</label>
          <input
            id="admin-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="admin-password">Password</label>
          <input
            id="admin-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in to dashboard'}
          </button>
        </form>

        {error && <div className="status-banner status-banner--error">{error}</div>}
      </div>
    </div>
  );
};

export default AdminLogin;
