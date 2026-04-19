import React from 'react';
import { GoogleLogin } from '@react-oauth/google';

const AuthShell = ({ 
  error, 
  onLoginSuccess, 
  onLoginError 
}) => {
  return (
    <div className="app-shell auth-shell modern-landing">
      <div className="bg-orb bg-orb--one" />
      <div className="bg-orb bg-orb--two" />
      <div className="bg-orb bg-orb--three" />
      <div className="bg-waveform" />
      <div className="bg-particles" />

      <main className="auth-layout-modern">
        <section className="auth-hero reveal-hero">
          <div className="hero-badge">AI-Powered</div>
          <span className="eyebrow reveal-item" data-delay="200">Next-Gen Music Curation</span>
          <h1 className="hero-title reveal-item" data-delay="400">
            Create <span className="gradient-text">VibeFlow</span> Playlists Instantly
          </h1>
          <p className="hero-desc reveal-item" data-delay="600">
            AI crafts perfect playlists by mood, genre, and artists. Preview, save, and organize your music in a sleek workspace.
          </p>

          <div className="hero-metrics-modern reveal-item" data-delay="800">
            <div className="metric-card-modern">
              <div className="metric-icon">🎵</div>
              <strong>15+</strong>
              <span>Genres Available</span>
            </div>
            <div className="metric-card-modern">
              <div className="metric-icon">😌</div>
              <strong>12</strong>
              <span>Moods Mapped</span>
            </div>
            <div className="metric-card-modern">
              <div className="metric-icon">⏱️</div>
              <strong>3s</strong>
              <span>Generation Time</span>
            </div>
          </div>

          <div className="hero-scroll-hint reveal-item" data-delay="1000">
            <span>↓</span> Scroll to sign in
          </div>
        </section>

        <section className="auth-card-modern reveal-card" role="region" aria-label="Sign in section">
          <div className="auth-card-header">
            <div className="auth-icon-floating">🎧</div>
            <div className="auth-welcome">
              <span className="eyebrow">Continue your session</span>
              <h2 className="auth-title">Welcome to your Music Studio</h2>
            </div>
          </div>
          <p className="auth-desc">
            Personalize your mixes, save favorites, and discover new tracks powered by advanced music AI.
          </p>

          <div className="auth-login-modern" aria-live="polite">
            <GoogleLogin
              onSuccess={onLoginSuccess}
              onError={onLoginError}
              theme="filled_blue"
              size="large"
              text="signin_with"
              shape="pill"
              width="360"
              aria-label="Sign in with Google"
            />
          </div>
          

          {error && (
            <div className="status-banner status-banner--error-modern" role="alert">
              <span className="status-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="auth-features-modern">
            <div className="feature-item">
              <span className="feature-icon">✨</span>
              <span>AI Recommendations</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">💾</span>
              <span>Unlimited Storage</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">▶️</span>
              <span>30s Previews</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default AuthShell;

