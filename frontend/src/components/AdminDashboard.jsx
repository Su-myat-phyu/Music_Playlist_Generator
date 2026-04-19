import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

const AdminDashboard = ({ adminPath }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [isProcessing, setIsProcessing] = useState('');
  const navigate = useNavigate();

  const adminToken = useMemo(() => localStorage.getItem('admin_token'), []);

  const getHeaders = useCallback(() => {
    const token = localStorage.getItem('admin_token');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }, []);

  const handleUnauthorized = useCallback(() => {
    localStorage.removeItem('admin_token');
    navigate(adminPath, { replace: true });
  }, [adminPath, navigate]);

  const loadDashboard = useCallback(async () => {
    const [dashboardRes, usersRes] = await Promise.all([
      fetch('/admin/dashboard', { headers: getHeaders() }),
      fetch('/admin/users', { headers: getHeaders() }),
    ]);

    if (dashboardRes.status === 401 || dashboardRes.status === 403 || usersRes.status === 401 || usersRes.status === 403) {
      handleUnauthorized();
      return;
    }

    if (!dashboardRes.ok || !usersRes.ok) {
      const errorData = await dashboardRes.json().catch(() => null);
      throw new Error(errorData?.detail || 'Failed to load admin dashboard');
    }

    const dashboardJson = await dashboardRes.json();
    const usersJson = await usersRes.json();
    setDashboardData(dashboardJson);
    setUsers(usersJson.users || []);
  }, [getHeaders, handleUnauthorized]);

  useEffect(() => {
    if (!adminToken) {
      navigate(adminPath, { replace: true });
      return;
    }

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        await loadDashboard();
      } catch (err) {
        setError(err.message || 'Failed to load admin data');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [adminPath, adminToken, loadDashboard, navigate]);

  const handleToggleUser = async (userId, userName, isActive) => {
    const action = isActive ? 'deactivate' : 'activate';
    const verb = isActive ? 'Deactivate' : 'Activate';
    if (!window.confirm(`${verb} ${userName}? This user will ${isActive ? 'lose' : 'gain'} access immediately.`)) {
      return;
    }

    setIsProcessing(userId);
    setError('');
    try {
      const response = await fetch(`/admin/users/${userId}/${action}`, {
        method: 'PATCH',
        headers: getHeaders(),
      });

      if (response.status === 401 || response.status === 403) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to ${action} user`);
      }

      await loadDashboard();
    } catch (err) {
      setError(err.message || `Failed to ${action} user`);
    } finally {
      setIsProcessing('');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate(adminPath, { replace: true });
  };

  // Prepare chart data
  const moodChartData = useMemo(() => dashboardData?.popular_moods || [], [dashboardData]);
  const genreChartData = useMemo(() => dashboardData?.popular_genres || [], [dashboardData]);
  const artistChartData = useMemo(() => dashboardData?.top_artists || [], [dashboardData]);
  const mlChartData = useMemo(() => {
    if (!dashboardData?.ml_metrics) return [];
    return [
      {
        name: 'Avg Accuracy',
        value: Number(dashboardData.ml_metrics.accuracy ?? 0) * 100,
        displayValue: `${(Number(dashboardData.ml_metrics.accuracy ?? 0) * 100).toFixed(1)}%`,
      },
      {
        name: 'High Confidence',
        value: Number(dashboardData.ml_metrics.precision_proxy ?? 0) * 100,
        displayValue: `${(Number(dashboardData.ml_metrics.precision_proxy ?? 0) * 100).toFixed(1)}%`,
      },
    ];
  }, [dashboardData]);

  const userStatusData = useMemo(() => {
    const active = users.filter(user => user.is_active).length;
    const inactive = users.filter(user => !user.is_active).length;
    return [
      { name: 'Active', value: active, color: '#4fd5a5' },
      { name: 'Inactive', value: inactive, color: '#ff6f7f' },
    ];
  }, [users]);

  if (loading) {
    return (
      <div className="admin-page">
        <div className="admin-card">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div>
          <p className="admin-auth-eyebrow">Admin Console</p>
          <h1>User & ML Monitoring Dashboard</h1>
        </div>
        <div className="admin-header-actions">
          <button className="btn btn-ghost" onClick={loadDashboard}>Refresh</button>
          <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {error && <div className="status-banner status-banner--error">{error}</div>}

      {dashboardData && (
        <>
          <section className="admin-summary-grid">
            <div className="admin-card"><span>Total users</span><strong>{dashboardData.summary.total_users}</strong></div>
            <div className="admin-card"><span>Playlists generated</span><strong>{dashboardData.summary.playlist_generation_count}</strong></div>
            <div className="admin-card"><span>Active users (30d)</span><strong>{dashboardData.summary.recent_active_users_30d}</strong></div>
            <div className="admin-card"><span>Engagement rate</span><strong>{dashboardData.summary.engagement_rate_percent}%</strong></div>
            <div className="admin-card"><span>Avg playlists per user</span><strong>{dashboardData.summary.avg_playlists_per_user}</strong></div>
            <div className="admin-card"><span>ML accuracy</span><strong>{dashboardData.ml_metrics ? `${(dashboardData.ml_metrics.accuracy * 100).toFixed(1)}%` : '0%'}</strong></div>
          </section>

          <section className="admin-chart-grid">
            <div className="admin-card admin-chart-card">
              <div className="admin-chart-header">
                <h2>Popular moods</h2>
              </div>
              {moodChartData.length ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={moodChartData} margin={{ top: 8, right: 6, left: -16, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="name" tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b203e', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#e2e8f0' }} />
                    <Bar dataKey="count" fill="#38bdf8" radius={[10, 10, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p>No mood data available.</p>
              )}
            </div>

            <div className="admin-card admin-chart-card">
              <div className="admin-chart-header">
                <h2>Popular genres</h2>
              </div>
              {genreChartData.length ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={genreChartData} margin={{ top: 8, right: 6, left: -16, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="name" tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b203e', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#e2e8f0' }} />
                    <Bar dataKey="count" fill="#a78bfa" radius={[10, 10, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p>No genre data available.</p>
              )}
            </div>

            <div className="admin-card admin-chart-card">
              <div className="admin-chart-header">
                <h2>Popular artists</h2>
              </div>
              {artistChartData.length ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={artistChartData} margin={{ top: 8, right: 6, left: -16, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: '#cbd5e1', fontSize: 12 }}
                      axisLine={false}
                      tickLine={false}
                      interval={0}
                      angle={-25}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b203e', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#e2e8f0' }} />
                    <Bar dataKey="count" fill="#f472b6" radius={[10, 10, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p>No artist data available.</p>
              )}
            </div>
          </section>

          <section className="admin-chart-grid">
            <div className="admin-card admin-chart-card">
              <div className="admin-chart-header">
                <h2>ML performance metrics</h2>
              </div>
              {mlChartData.length ? (
                <div style={{ width: '100%', height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={mlChartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tickFormatter={(value) => `${value.toFixed(1)}%`} tick={{ fill: '#cbd5e1', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#0b203e', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#e2e8f0' }} formatter={(value) => `${value.toFixed(1)}%`} />
                      <Bar dataKey="value" fill="#fbbf24" radius={[10, 10, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p>No ML metric data available.</p>
              )}
              <div className="admin-chart-footer">
                <p>Evaluated samples: {dashboardData.ml_metrics?.evaluated_samples ?? 0}</p>
                <p>{dashboardData.ml_metrics?.note || 'No model note available.'}</p>
              </div>
            </div>

            <div className="admin-card admin-chart-card">
              <div className="admin-chart-header">
                <h2>User status distribution</h2>
              </div>
              {userStatusData.some(item => item.value > 0) ? (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={userStatusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {userStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0b203e', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#e2e8f0' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p>No user data available.</p>
              )}
              <div className="admin-chart-legend">
                {userStatusData.map((item, index) => (
                  <div key={item.name} className="admin-legend-item">
                    <span className="admin-legend-color" style={{ backgroundColor: item.color }}></span>
                    <span>{item.name}: {item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="admin-card">
            <h2>Registered users</h2>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Playlists</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.name || '-'}</td>
                      <td>{user.email || '-'}</td>
                      <td>{user.is_active ? 'Active' : 'Inactive'}</td>
                      <td>{user.playlists_count || 0}</td>
                      <td>
                        <button
                          className={`btn btn-small ${user.is_active ? 'btn-danger' : 'btn-primary'}`}
                          disabled={isProcessing === user.id}
                          onClick={() => handleToggleUser(user.id, user.name || user.email || user.id, user.is_active)}
                        >
                          {isProcessing === user.id
                            ? user.is_active
                              ? 'Deactivating...'
                              : 'Activating...'
                            : user.is_active
                              ? 'Deactivate'
                              : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default AdminDashboard;
