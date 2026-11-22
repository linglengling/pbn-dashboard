import React, { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import {
    Globe, Wifi, WifiOff, Activity, Link2, FileText, Search,
    Trash2, Plus, Send, AlertTriangle, Clock, Server, Zap,
    RefreshCw, ExternalLink, Shield, X, ChevronDown, Sliders, Sparkles, Cpu, BookOpen, UserCheck, LogOut, User, ChevronLeft, ChevronRight, Filter, Calendar, Check,
} from 'lucide-react';
import { getTranslation } from './i18n';
import ServersTab from './ServersTab';
import WpUsersTab from './WpUsersTab';
import './App.css';

const API_BASE = window.location.port === '5173' ? 'http://localhost:3000' : window.location.origin;
const socket = io(API_BASE);

// Helper fetch kèm Token 7 ngày
const authFetch = (url, options = {}) => {
    const token = localStorage.getItem('pbn_token');
    const headers = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    return fetch(url, { ...options, headers });
};

// ============================================================
// LOGIN SCREEN COMPONENT (7-Day Session Persistence)
// ============================================================
function LoginScreen({ onLoginSuccess, lang, setLang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [remember, setRemember] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!username.trim() || !password.trim()) {
            return setError(t('usernameLabel') + ' & ' + t('passwordLabel') + ' required');
        }

        setLoading(true);
        setError('');

        try {
            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();

            if (data.success && data.token) {
                localStorage.setItem('pbn_token', data.token);
                localStorage.setItem('pbn_user', JSON.stringify(data.user));
                onLoginSuccess(data.user, data.token);
            } else {
                setError(data.error || 'Login failed');
            }
        } catch (err) {
            setError('Cannot connect to Dashboard server');
        }
        setLoading(false);
    };

    return (
        <div className="login-wrapper">
            <div className="login-card">
                {/* Language Switcher */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', padding: '4px 8px', borderRadius: 8 }}>
                        <Globe size={14} color="#38bdf8" />
                        <select
                            value={lang}
                            onChange={e => {
                                const newLang = e.target.value;
                                setLang(newLang);
                                localStorage.setItem('pbn_lang', newLang);
                            }}
                            style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: 13, fontWeight: 600, cursor: 'pointer', outline: 'none' }}
                        >
                            <option value="vi" style={{ background: '#0f172a' }}>🇻🇳 Tiếng Việt</option>
                            <option value="en" style={{ background: '#0f172a' }}>🇺🇸 English</option>
                            <option value="zh" style={{ background: '#0f172a' }}>🇨🇳 简体中文</option>
                        </select>
                    </div>
                </div>

                <div className="login-header">
                    <div className="login-logo">
                        <Shield size={32} color="#38bdf8" />
                    </div>
                    <h2>{t('loginTitle')}</h2>
                    <p>{t('loginSubtitle')}</p>
                </div>

                {error && <div className="login-error">{error}</div>}

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label">{t('usernameLabel')}</label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Username..."
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            autoFocus
                        />
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label">{t('passwordLabel')}</label>
                        <input
                            type="password"
                            className="form-input"
                            placeholder="Password..."
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#94a3b8', margin: '4px 0 6px 0' }}>
                        <input
                            type="checkbox"
                            id="remember"
                            checked={remember}
                            onChange={e => setRemember(e.target.checked)}
                            style={{ cursor: 'pointer' }}
                        />
                        <label htmlFor="remember" style={{ cursor: 'pointer' }}>{t('rememberMe')}</label>
                    </div>

                    <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', marginTop: 6 }}>
                        {loading ? t('authenticating') : t('loginBtn')}
                    </button>
                </form>
            </div>
        </div>
    );
}

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error("Uncaught Error Boundary:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0f172a', color: '#f8fafc', padding: 20, textAlign: 'center' }}>
                    <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', padding: 30, borderRadius: 16, maxWidth: 500 }}>
                        <h2 style={{ color: '#f87171', margin: '0 0 10px 0' }}>⚠️ Đã xảy ra lỗi hiển thị giao diện</h2>
                        <p style={{ color: '#cbd5e1', fontSize: 14 }}>{this.state.error?.message || 'Có lỗi bất ngờ xảy ra khi tải trang.'}</p>
                        <button className="btn btn-primary" onClick={() => window.location.reload()} style={{ marginTop: 15 }}>
                            🔄 Tải lại trang (Reload)
                        </button>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

// ============================================================
// MAIN APP
// ============================================================
function MainApp() {
    const [connected, setConnected] = useState(socket.connected);
    const [activeTab, setActiveTab] = useState('sites');
    const [sites, setSites] = useState([]);
    const [servers, setServers] = useState([]);
    const [pendingSites, setPendingSites] = useState([]);
    const [stats, setStats] = useState({});
    const [backlinks, setBacklinks] = useState([]);
    const [posts, setPosts] = useState([]);
    const [activityLog, setActivityLog] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [toasts, setToasts] = useState([]);
    const [modal, setModal] = useState(null);

    // i18n Multi-Language State (vi, en, zh)
    const [lang, setLang] = useState(localStorage.getItem('pbn_lang') || 'vi');
    const t = (key, vars) => getTranslation(key, lang, vars);

    // Authentication State (7-Day Token Persistence)
    const [currentUser, setCurrentUser] = useState(null);
    const [authChecking, setAuthChecking] = useState(true);

    useEffect(() => {
        const verifyToken = async () => {
            const token = localStorage.getItem('pbn_token');
            if (!token) {
                setAuthChecking(false);
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/auth/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (data.success && data.user) {
                    setCurrentUser(data.user);
                } else {
                    localStorage.removeItem('pbn_token');
                    localStorage.removeItem('pbn_user');
                }
            } catch (e) {
                console.error(e);
            }
            setAuthChecking(false);
        };
        verifyToken();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('pbn_token');
        localStorage.removeItem('pbn_user');
        setCurrentUser(null);
        addToast('Đã đăng xuất tài khoản', 'info');
    };

    const handleLoginSuccess = (user, token) => {
        setCurrentUser(user);
        addToast(`Xin chào ${user.username}! Đăng nhập thành công (Phiên 7 ngày).`, 'success');
        refreshAll();
    };

    const navigateTo = (tab) => {
        setActiveTab(tab);
        window.history.pushState(null, '', `/${tab === 'sites' ? '' : tab}`);
    };

    useEffect(() => {
        const path = window.location.pathname.substring(1) || 'sites';
        const cleanPath = path === 'wp-users' ? 'users' : path;
        if (['sites', 'servers', 'users', 'backlinks', 'posts', 'log', 'control', 'ai-writer'].includes(cleanPath)) {
            setActiveTab(cleanPath);
        }
        
        const handlePopState = () => {
            const newPath = window.location.pathname.substring(1) || 'sites';
            const cleanNewPath = newPath === 'wp-users' ? 'users' : newPath;
            setActiveTab(cleanNewPath);
        };
        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    // Toast notification
    const addToast = useCallback((message, type = 'info') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
    }, []);

    // Fetch data with 7-Day Auth Token
    const fetchSites = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/sites`);
            const data = await res.json();
            if (data.success) setSites(data.data);
            else if (res.status === 401) setCurrentUser(null);
        } catch (e) { console.error('Failed to fetch sites', e); }
    };

    const fetchStats = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/stats`);
            const data = await res.json();
            if (data.success) setStats(data.data);
        } catch (e) { console.error('Failed to fetch stats', e); }
    };

    const fetchBacklinks = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/backlinks`);
            const data = await res.json();
            if (data.success) setBacklinks(data.data);
        } catch (e) { console.error('Failed to fetch backlinks', e); }
    };

    const fetchPosts = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/posts`);
            const data = await res.json();
            if (data.success) setPosts(data.data);
        } catch (e) { console.error('Failed to fetch posts', e); }
    };

    const fetchPendingSites = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/sites/pending`);
            const data = await res.json();
            if (data.success) setPendingSites(data.data);
        } catch (e) { console.error('Failed to fetch pending sites', e); }
    };

    const fetchLog = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/log?limit=100`);
            const data = await res.json();
            if (data.success) setActivityLog(data.data);
        } catch (e) { console.error('Failed to fetch log', e); }
    };

    const fetchServers = async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/servers`);
            const data = await res.json();
            if (data.success) setServers(data.data || []);
        } catch (e) { console.error('Failed to fetch servers', e); }
    };

    const refreshAll = () => {
        fetchSites();
        fetchServers();
        fetchPendingSites();
        fetchStats();
        fetchBacklinks();
        fetchPosts();
        fetchLog();
    };

    // Socket.IO events
    useEffect(() => {
        if (!currentUser) return;
        if (socket.connected) setConnected(true);
        const onConnect = () => setConnected(true);
        const onDisconnect = () => setConnected(false);
        socket.on('connect', onConnect);
        socket.on('disconnect', onDisconnect);

        socket.on('site:update', (data) => {
            setSites(prev => {
                const idx = prev.findIndex(s => s.domain === data.domain);
                if (idx >= 0) {
                    const next = [...prev];
                    next[idx] = { ...next[idx], ...data };
                    return next;
                }
                return [data, ...prev];
            });
            fetchStats();
        });

        socket.on('site:pending', (data) => {
            setPendingSites(prev => {
                const idx = prev.findIndex(s => s.domain === data.domain);
                if (idx >= 0) {
                    const next = [...prev];
                    next[idx] = { ...next[idx], ...data };
                    return next;
                }
                return [data, ...prev];
            });
            fetchStats();
            addToast(`[Yêu cầu duyệt] Site ${data.domain} (IP: ${data.server_ip || data.ip}) vừa ping đến Dashboard!`, 'info');
        });

        socket.on('sites:approved', () => {
            fetchSites();
            fetchPendingSites();
            fetchStats();
        });

        socket.on('sites:rejected', () => {
            fetchPendingSites();
            fetchStats();
        });

        socket.on('site:registered', () => refreshAll());
        socket.on('backlink:added', () => refreshAll());
        socket.on('backlink:removed', () => refreshAll());

        return () => {
            socket.off('connect');
            socket.off('disconnect');
            socket.off('site:update');
            socket.off('site:pending');
            socket.off('sites:approved');
            socket.off('sites:rejected');
            socket.off('site:registered');
            socket.off('backlink:added');
            socket.off('backlink:removed');
        };
    }, [currentUser]);

    // Initial load when logged in
    useEffect(() => {
        if (currentUser) {
            refreshAll();
        }
    }, [currentUser]);

    if (authChecking) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0f172a', color: '#38bdf8', fontSize: 16, fontWeight: 600 }}>
                <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', marginRight: 10 }} />
                Đang xác thực phiên đăng nhập PBN Dashboard...
            </div>
        );
    }

    if (!currentUser) {
        return <LoginScreen onLoginSuccess={handleLoginSuccess} lang={lang} setLang={setLang} />;
    }

    // Filter sites
    const filteredSites = sites.filter(s =>
        s.domain?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.cluster?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.ip?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Get unique clusters
    const clusters = [...new Set(sites.map(s => s.cluster).filter(Boolean))];

    return (
        <div className="app-container">
            {/* TOASTS */}
            <div className="toast-container">
                {toasts.map(t => (
                    <div key={t.id} className={`toast ${t.type}`}>
                        {t.type === 'success' ? <Zap size={16} /> : t.type === 'error' ? <AlertTriangle size={16} /> : <Activity size={16} />}
                        {t.message}
                    </div>
                ))}
            </div>

            {/* HEADER */}
            <header className="header">
                <div className="header-left">
                    <div className="header-logo">P</div>
                    <div>
                        <div className="header-title">{t('title')}</div>
                        <div className="header-subtitle">{t('subtitle')}</div>
                    </div>
                </div>
                <div className="header-right">
                    {/* Language Switcher */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', padding: '4px 8px', borderRadius: 8 }}>
                        <Globe size={14} color="#38bdf8" />
                        <select
                            value={lang}
                            onChange={e => {
                                const newLang = e.target.value;
                                setLang(newLang);
                                localStorage.setItem('pbn_lang', newLang);
                            }}
                            style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: 13, fontWeight: 600, cursor: 'pointer', outline: 'none' }}
                        >
                            <option value="vi" style={{ background: '#0f172a' }}>🇻🇳 Tiếng Việt</option>
                            <option value="en" style={{ background: '#0f172a' }}>🇺🇸 English</option>
                            <option value="zh" style={{ background: '#0f172a' }}>🇨🇳 简体中文</option>
                        </select>
                    </div>

                    <button className="btn" onClick={refreshAll}>
                        <RefreshCw size={14} /> {t('refresh')}
                    </button>
                    <div className={`connection-status ${connected ? '' : 'disconnected'}`}>
                        <span className="status-dot"></span>
                        {connected ? t('connected') : t('disconnected')}
                    </div>

                    {/* Logged in User Profile & Logout */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.25)', padding: '4px 12px', borderRadius: 8 }}>
                        <span style={{ fontSize: 13, color: '#38bdf8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                            <User size={14} /> {currentUser.username}
                        </span>
                        <button className="btn btn-sm btn-danger" onClick={handleLogout} title={t('logout')} style={{ padding: '4px 8px' }}>
                            <LogOut size={12} /> {t('logout')}
                        </button>
                    </div>
                </div>
            </header>

            {/* STATS */}
            <div className="stats-grid">
                <div className="stat-card" style={{ borderLeft: '4px solid #818cf8', cursor: 'pointer' }} onClick={() => navigateTo('servers')}>
                    <div className="stat-label">{t('totalServers')}</div>
                    <div className="stat-value" style={{ color: '#818cf8' }}>{stats.totalServers || servers.length || 0}</div>
                </div>
                <div className="stat-card total">
                    <div className="stat-label">{t('totalSites')}</div>
                    <div className="stat-value">{stats.totalSites || 0}</div>
                </div>
                <div className="stat-card online">
                    <div className="stat-label">{t('onlineSites')}</div>
                    <div className="stat-value">{stats.onlineSites || 0}</div>
                </div>
                <div className="stat-card offline">
                    <div className="stat-label">{t('offlineSites')}</div>
                    <div className="stat-value">{stats.offlineSites || 0}</div>
                </div>
                <div className="stat-card links">
                    <div className="stat-label">{t('activeLinks')}</div>
                    <div className="stat-value">{stats.activeBacklinks || 0}</div>
                </div>
                <div className="stat-card posts">
                    <div className="stat-label">{t('totalPosts')}</div>
                    <div className="stat-value">{stats.totalPosts || 0}</div>
                </div>
            </div>

            {/* TABS */}
            <div className="tabs">
                <button className={`tab ${activeTab === 'sites' ? 'active' : ''}`} onClick={() => navigateTo('sites')}>
                    <Globe size={14} /> {t('sites')} ({sites.length})
                    {pendingSites.length > 0 && (
                        <span style={{
                            marginLeft: 6,
                            background: '#f59e0b',
                            color: '#0f172a',
                            fontSize: 11,
                            fontWeight: 700,
                            padding: '1px 6px',
                            borderRadius: 10
                        }}>
                            {pendingSites.length} {t('pendingSitesTab')}
                        </span>
                    )}
                </button>
                <button className={`tab ${activeTab === 'servers' ? 'active' : ''}`} onClick={() => navigateTo('servers')}>
                    <Server size={14} /> {t('servers')} ({servers.length})
                </button>
                <button className={`tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => navigateTo('users')}>
                    <UserCheck size={14} /> Quản lý User WP
                </button>
                <button className={`tab ${activeTab === 'backlinks' ? 'active' : ''}`} onClick={() => navigateTo('backlinks')}>
                    <Link2 size={14} /> {t('backlinks')} ({backlinks.length})
                </button>
                <button className={`tab ${activeTab === 'posts' ? 'active' : ''}`} onClick={() => navigateTo('posts')}>
                    <FileText size={14} /> {t('posts')} ({posts.length})
                </button>
                <button className={`tab ${activeTab === 'ai-writer' ? 'active' : ''}`} onClick={() => navigateTo('ai-writer')}>
                    <Zap size={14} /> {t('aiWriter')}
                </button>
                <button className={`tab ${activeTab === 'log' ? 'active' : ''}`} onClick={() => navigateTo('log')}>
                    <Activity size={14} /> {t('log')}
                </button>
                <button className={`tab ${activeTab === 'control' ? 'active' : ''}`} onClick={() => navigateTo('control')}>
                    <Shield size={14} /> {t('controlPanel')}
                </button>
            </div>

            {/* TAB CONTENT */}
            {activeTab === 'sites' && (
                <SitesTab
                    sites={sites}
                    servers={servers}
                    backlinks={backlinks}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    addToast={addToast}
                    setModal={setModal}
                    lang={lang}
                    pendingSites={pendingSites}
                    refreshPendingSites={fetchPendingSites}
                    refreshSites={fetchSites}
                    refreshStats={fetchStats}
                />
            )}
            {activeTab === 'servers' && (
                <ServersTab
                    servers={servers}
                    refreshServers={fetchServers}
                    refreshSites={fetchSites}
                    refreshStats={fetchStats}
                    addToast={addToast}
                    setModal={setModal}
                    lang={lang}
                />
            )}
            {activeTab === 'users' && (
                <WpUsersTab
                    addToast={addToast}
                    lang={lang}
                />
            )}
            {activeTab === 'backlinks' && (
                <BacklinksTab
                    backlinks={backlinks}
                    sites={sites}
                    addToast={addToast}
                    refreshBacklinks={fetchBacklinks}
                    setModal={setModal}
                    lang={lang}
                />
            )}
            {activeTab === 'posts' && (
                <PostsTab
                    posts={posts}
                    sites={sites}
                    addToast={addToast}
                    refreshPosts={fetchPosts}
                    setModal={setModal}
                    lang={lang}
                />
            )}
            {activeTab === 'ai-writer' && (
                <AIWriterTab
                    sites={sites}
                    addToast={addToast}
                    lang={lang}
                />
            )}
            {activeTab === 'log' && <LogTab addToast={addToast} lang={lang} />}
            {activeTab === 'control' && (
                <ControlPanel
                    sites={sites}
                    clusters={clusters}
                    addToast={addToast}
                    refreshAll={refreshAll}
                    currentUser={currentUser}
                    lang={lang}
                />
            )}

            {/* MODAL */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <div className="modal-title">{modal.title}</div>
                            <button className="btn btn-sm" onClick={() => setModal(null)}><X size={14} /></button>
                        </div>
                        {modal.content}
                    </div>
                </div>
            )}
        </div>
    );
}

// ============================================================
// FLOATING POPOVER (Position Fixed - Never Clipped)
// ============================================================
function FloatingPopover({ popover, onClose }) {
    if (!popover || !popover.rect) return null;

    const { title, items, rect, type, domain } = popover;
    const isTopHalf = rect.top < window.innerHeight / 2;

    const rightOffset = window.innerWidth - rect.right;
    const leftPos = rect.left < 300 ? Math.max(10, rect.left) : 'auto';
    const rightPos = rect.left < 300 ? 'auto' : Math.max(10, rightOffset);

    const style = {
        position: 'fixed',
        zIndex: 999999,
        minWidth: 550,
        maxWidth: 780,
        maxHeight: 440,
        overflowY: 'auto',
        background: '#0f172a',
        border: '1px solid #38bdf8',
        borderRadius: 14,
        padding: '18px 22px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.95), 0 0 25px rgba(56, 189, 248, 0.3)',
        backdropFilter: 'blur(16px)',
        pointerEvents: 'auto'
    };

    if (isTopHalf) {
        style.top = rect.bottom + 8;
    } else {
        style.bottom = window.innerHeight - rect.top + 8;
    }

    if (leftPos !== 'auto') style.left = leftPos;
    if (rightPos !== 'auto') style.right = rightPos;

    return (
        <div 
            className="floating-popover" 
            style={style}
            onMouseEnter={popover.onKeepOpen}
            onMouseLeave={onClose}
        >
            <div style={{ 
                fontWeight: 'bold', 
                color: '#22d3ee', 
                paddingBottom: 10, 
                borderBottom: '1px solid #334155', 
                marginBottom: 12, 
                fontSize: 15, 
                display: 'flex', 
                justify: 'space-between', 
                alignItems: 'center' 
            }}>
                <span>{title} ({items.length})</span>
                <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 'normal' }}>Click badge để mở cửa sổ lớn</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {items.map((item, idx) => {
                    const isPbnInlinks = type === 'pbn_inlinks';
                    const anchor = isPbnInlinks ? item.anchor : (type === 'backlinks' ? item.anchor_text : (item.anchor || '[No Anchor]'));
                    const targetUrl = isPbnInlinks ? item.targetUrl : (type === 'backlinks' ? item.target_url : item.url);
                    
                    let sourceUrl = isPbnInlinks 
                        ? (item.postId ? `http://${item.sourceDomain}/?p=${item.postId}` : `http://${item.sourceDomain}`)
                        : `http://${domain}`;
                    
                    let sourceLabel = isPbnInlinks 
                        ? (item.postId ? `${item.sourceDomain} (#${item.postId})` : `${item.sourceDomain}`)
                        : (type === 'backlinks' && item.post_id ? `Bài viết #${item.post_id}` : `Trang chủ (${domain})`);

                    if (!isPbnInlinks && type === 'backlinks' && item.post_id) {
                        sourceUrl = `http://${domain}/?p=${item.post_id}`;
                    }

                    return (
                        <div key={idx} style={{ 
                            padding: '12px 14px', 
                            borderRadius: 10, 
                            background: 'rgba(30, 41, 59, 0.85)', 
                            fontSize: 13, 
                            border: '1px solid #334155', 
                            display: 'flex', 
                            flexDirection: 'column', 
                            gap: 6 
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                                <span style={{ color: isPbnInlinks ? '#c084fc' : '#38bdf8', fontWeight: 700, fontSize: 14 }}>
                                    {anchor}
                                </span>
                                <a 
                                    href={sourceUrl} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    style={{ 
                                        color: isPbnInlinks ? '#c084fc' : '#34d399', 
                                        background: isPbnInlinks ? 'rgba(168, 85, 247, 0.15)' : 'rgba(52, 211, 153, 0.12)', 
                                        border: isPbnInlinks ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid rgba(52, 211, 153, 0.3)', 
                                        padding: '3px 10px', 
                                        borderRadius: 6, 
                                        fontSize: 11, 
                                        fontWeight: 600, 
                                        display: 'inline-flex', 
                                        alignItems: 'center', 
                                        gap: 4, 
                                        textDecoration: 'none' 
                                    }}
                                    title={`Mở bài viết/trang nguồn trên site vệ tinh: ${sourceUrl}`}
                                >
                                    <ExternalLink size={11} /> Nguồn: {sourceLabel}
                                </a>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#94a3b8' }}>
                                <span style={{ fontWeight: 600, color: '#64748b' }}>Target URL:</span>
                                <a href={targetUrl} target="_blank" rel="noreferrer" style={{ color: '#cbd5e1', wordBreak: 'break-all', textDecoration: 'none' }} title={targetUrl}>
                                    {targetUrl}
                                </a>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// Helper: Tính số lượng & thông tin link từ các site KHÁC TRONG HỆ THỐNG trỏ về targetDomain
function getNetworkInboundLinks(targetDomain, sites, backlinks) {
    if (!targetDomain) return [];
    
    const cleanTarget = targetDomain.toLowerCase().replace(/^www\./, '').split('/')[0];
    const inlinks = [];

    // 1. Quét từ bảng backlinks (những backlink được tạo qua Tool)
    (backlinks || []).forEach(b => {
        if (b.status === 'active' && b.site_domain) {
            const srcDomainClean = b.site_domain.toLowerCase().replace(/^www\./, '').split('/')[0];
            if (srcDomainClean !== cleanTarget) {
                try {
                    if (b.target_url) {
                        const targetHost = new URL(b.target_url).hostname.toLowerCase().replace(/^www\./, '');
                        if (targetHost === cleanTarget) {
                            inlinks.push({
                                sourceDomain: b.site_domain,
                                anchor: b.anchor_text || '[No Anchor]',
                                targetUrl: b.target_url,
                                sourceType: 'Backlinks Tool',
                                postId: b.post_id
                            });
                        }
                    }
                } catch (e) {
                    if (b.target_url && b.target_url.toLowerCase().includes(cleanTarget)) {
                        inlinks.push({
                            sourceDomain: b.site_domain,
                            anchor: b.anchor_text || '[No Anchor]',
                            targetUrl: b.target_url,
                            sourceType: 'Backlinks Tool',
                            postId: b.post_id
                        });
                    }
                }
            }
        }
    });

    // 2. Quét từ homepage_outbound_links của tất cả các site khác trong hệ thống
    (sites || []).forEach(s => {
        if (!s.domain) return;
        const sourceDomainClean = s.domain.toLowerCase().replace(/^www\./, '').split('/')[0];
        if (sourceDomainClean === cleanTarget) return;

        let outboundLinks = [];
        try {
            if (s.homepage_outbound_links) {
                outboundLinks = typeof s.homepage_outbound_links === 'string'
                    ? JSON.parse(s.homepage_outbound_links)
                    : s.homepage_outbound_links;
            }
        } catch (e) {
            console.error(e);
        }

        outboundLinks.forEach(link => {
            if (!link || !link.url) return;
            try {
                const targetHost = new URL(link.url).hostname.toLowerCase().replace(/^www\./, '');
                if (targetHost === cleanTarget) {
                    inlinks.push({
                        sourceDomain: s.domain,
                        anchor: link.anchor || '[No Anchor]',
                        targetUrl: link.url,
                        sourceType: 'Outbound Links Trang Chủ'
                    });
                }
            } catch (e) {
                if (link.url.toLowerCase().includes(cleanTarget)) {
                    inlinks.push({
                        sourceDomain: s.domain,
                        anchor: link.anchor || '[No Anchor]',
                        targetUrl: link.url,
                        sourceType: 'Outbound Links Trang Chủ'
                    });
                }
            }
        });
    });

    return inlinks;
}

// ============================================================
// SITES TAB
// ============================================================
function SitesTab({
    sites,
    servers = [],
    backlinks,
    searchQuery,
    setSearchQuery,
    addToast,
    setModal,
    lang,
    pendingSites = [],
    refreshPendingSites,
    refreshSites,
    refreshStats
}) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [subTab, setSubTab] = useState('active'); // 'active' | 'pending'
    const [selectedDomains, setSelectedDomains] = useState([]);
    const [selectedPendingDomains, setSelectedPendingDomains] = useState([]);
    const [pendingSearch, setPendingSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    const [clusterFilter, setClusterFilter] = useState('ALL');
    const [backlinkFilter, setBacklinkFilter] = useState('ALL');
    const [serverFilter, setServerFilter] = useState('ALL');
    const [redirectFilter, setRedirectFilter] = useState('ALL'); // 'ALL' | 'REDIRECT' | 'DIRECT'
    const [scanningRedirects, setScanningRedirects] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(100);
    const [hoveredPopover, setHoveredPopover] = useState(null);

    let closeTimer = null;

    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, statusFilter, clusterFilter, backlinkFilter, serverFilter, redirectFilter, pageSize]);

    const handleScanRedirects = async () => {
        setScanningRedirects(true);
        addToast('Đang quét kiểm tra 301 Redirect cho tất cả domain...', 'info');
        try {
            const res = await authFetch(`${API_BASE}/api/sites/check-redirects`, {
                method: 'POST'
            });
            const d = await res.json();
            if (d.success) {
                addToast(`Hoàn tất quét: Phát hiện ${d.total_redirects} domain có 301 Redirect trên tổng số ${d.total_checked} domain!`, 'success');
                if (refreshSites) refreshSites();
            } else {
                addToast(d.detail || d.error || 'Quét redirect thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ khi quét redirect', 'error');
        }
        setScanningRedirects(false);
    };

    const handleApproveSite = async (domain) => {
        try {
            const res = await authFetch(`${API_BASE}/api/sites/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain })
            });
            const d = await res.json();
            if (d.success) {
                addToast(`Đã duyệt site ${domain} thành công!`, 'success');
                if (refreshSites) refreshSites();
                if (refreshPendingSites) refreshPendingSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(d.error || 'Duyệt site thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
    };

    const handleBulkApprove = async (domains) => {
        if (!domains || !domains.length) return;
        try {
            const res = await authFetch(`${API_BASE}/api/sites/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains })
            });
            const d = await res.json();
            if (d.success) {
                addToast(`Đã duyệt ${domains.length} site thành công!`, 'success');
                setSelectedPendingDomains([]);
                if (refreshSites) refreshSites();
                if (refreshPendingSites) refreshPendingSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(d.error || 'Duyệt site thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
    };

    const handleRejectSite = async (domain) => {
        if (!window.confirm(`Bạn có chắc muốn từ chối và xóa site "${domain}" khỏi danh sách chờ duyệt?`)) return;
        try {
            const res = await authFetch(`${API_BASE}/api/sites/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain, delete_permanently: true })
            });
            const d = await res.json();
            if (d.success) {
                addToast(`Đã xóa site ${domain} khỏi hàng chờ`, 'info');
                if (refreshPendingSites) refreshPendingSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(d.error || 'Thao tác thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
    };

    const handleBulkReject = async (domains) => {
        if (!domains || !domains.length) return;
        if (!window.confirm(`Bạn có chắc muốn từ chối và xóa ${domains.length} site đã chọn?`)) return;
        try {
            const res = await authFetch(`${API_BASE}/api/sites/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains, delete_permanently: true })
            });
            const d = await res.json();
            if (d.success) {
                addToast(`Đã từ chối ${domains.length} site`, 'info');
                setSelectedPendingDomains([]);
                if (refreshPendingSites) refreshPendingSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(d.error || 'Thao tác thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
    };

    const filteredPending = pendingSites.filter(s => {
        const q = pendingSearch.trim().toLowerCase();
        if (!q) return true;
        return (
            s.domain?.toLowerCase().includes(q) ||
            s.server_ip?.toLowerCase().includes(q) ||
            s.ip?.toLowerCase().includes(q) ||
            s.cluster?.toLowerCase().includes(q)
        );
    });

    const handleMouseEnterBadge = (e, domain, type, title, items) => {
        if (!items || items.length === 0) return;
        if (closeTimer) clearTimeout(closeTimer);
        const rect = e.currentTarget.getBoundingClientRect();
        setHoveredPopover({
            domain,
            type,
            title,
            items,
            rect,
            onKeepOpen: () => { if (closeTimer) clearTimeout(closeTimer); }
        });
    };

    const handleMouseLeaveBadge = () => {
        closeTimer = setTimeout(() => {
            setHoveredPopover(null);
        }, 200);
    };

    const clusters = [...new Set(sites.map(s => s.cluster).filter(Boolean))];

    // Server site counts
    const serverSiteCounts = {};
    (sites || []).forEach(s => {
        if (s.server_host) serverSiteCounts[s.server_host] = (serverSiteCounts[s.server_host] || 0) + 1;
        if (s.server_ip && s.server_ip !== s.server_host) serverSiteCounts[s.server_ip] = (serverSiteCounts[s.server_ip] || 0) + 1;
        if (s.server_id) serverSiteCounts[String(s.server_id)] = (serverSiteCounts[String(s.server_id)] || 0) + 1;
    });

    const redirectedTotal = (sites || []).filter(s => Boolean(s.redirect_to)).length;
    const directTotal = (sites || []).length - redirectedTotal;

    const filtered = sites.filter(s => {
        const query = (searchQuery || '').trim().toLowerCase();
        let matchesSearch = true;
        if (query) {
            const tokens = query.split(/\s+/).filter(Boolean);
            const searchableText = `${s.domain || ''} ${s.redirect_to || ''} ${s.server_host || ''} ${s.server_ip || ''} ${s.cluster || ''} ${s.ip || ''}`.toLowerCase();
            matchesSearch = tokens.every(token => searchableText.includes(token));
        }
            
        const matchesStatus = statusFilter === 'ALL' ||
            (statusFilter === 'ONLINE' && s.status === 'ONLINE') ||
            (statusFilter === 'OFFLINE' && s.status === 'OFFLINE');

        const matchesCluster = clusterFilter === 'ALL' || s.cluster === clusterFilter;

        const matchesBacklinks = () => {
            const count = backlinks.filter(b => b.site_domain === s.domain && b.status === 'active').length;
            if (backlinkFilter === 'ALL') return true;
            if (backlinkFilter === '0') return count === 0;
            if (backlinkFilter === '1') return count === 1;
            if (backlinkFilter === '2') return count === 2;
            if (backlinkFilter === '3+') return count >= 3;
            return true;
        };

        const matchesServer = serverFilter === 'ALL' ||
            s.server_host === serverFilter ||
            s.server_ip === serverFilter ||
            String(s.server_id) === String(serverFilter);

        const matchesRedirect = redirectFilter === 'ALL' ||
            (redirectFilter === 'REDIRECT' && Boolean(s.redirect_to)) ||
            (redirectFilter === 'DIRECT' && !s.redirect_to);

        return matchesSearch && matchesStatus && matchesCluster && matchesBacklinks() && matchesServer && matchesRedirect;
    });

    const totalPages = pageSize === 'ALL' ? 1 : Math.max(1, Math.ceil(filtered.length / pageSize));
    const safeCurrentPage = Math.min(currentPage, totalPages);
    const paginatedSites = pageSize === 'ALL' 
        ? filtered 
        : filtered.slice((safeCurrentPage - 1) * pageSize, safeCurrentPage * pageSize);

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            const pageDomains = paginatedSites.map(s => s.domain);
            setSelectedDomains(prev => Array.from(new Set([...prev, ...pageDomains])));
        } else {
            const pageDomains = new Set(paginatedSites.map(s => s.domain));
            setSelectedDomains(prev => prev.filter(d => !pageDomains.has(d)));
        }
    };

    const handleSelectRow = (domain) => {
        setSelectedDomains(prev => 
            prev.includes(domain) ? prev.filter(d => d !== domain) : [...prev, domain]
        );
    };

    const isCurrentPageSelected = paginatedSites.length > 0 && paginatedSites.every(s => selectedDomains.includes(s.domain));
    const isAllFilteredSelected = filtered.length > 0 && filtered.every(s => selectedDomains.includes(s.domain));

    return (
        <>
            {/* SUB-TABS: Active vs Pending */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <button
                    className={`btn btn-sm ${subTab === 'active' ? 'btn-primary' : ''}`}
                    onClick={() => setSubTab('active')}
                    style={subTab !== 'active' ? { background: 'rgba(30, 41, 59, 0.6)', color: '#94a3b8' } : {}}
                >
                    <Globe size={13} /> {t('approvedSitesTab')} ({sites.length})
                </button>
                <button
                    className={`btn btn-sm ${subTab === 'pending' ? 'btn-primary' : ''}`}
                    onClick={() => setSubTab('pending')}
                    style={subTab !== 'pending' ? { background: 'rgba(30, 41, 59, 0.6)', color: '#94a3b8' } : {}}
                >
                    <Clock size={13} /> {t('pendingSitesTab')} ({pendingSites.length})
                    {pendingSites.length > 0 && (
                        <span style={{
                            marginLeft: 6,
                            background: '#f59e0b',
                            color: '#0f172a',
                            fontSize: 10,
                            fontWeight: 700,
                            padding: '1px 6px',
                            borderRadius: 8
                        }}>
                            {pendingSites.length}
                        </span>
                    )}
                </button>
            </div>

            {subTab === 'pending' ? (
                <div>
                    <div className="toolbar" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                        <div className="search-wrapper" style={{ flex: 1, minWidth: 250 }}>
                            <Search size={16} />
                            <input
                                type="text"
                                className="search-input"
                                placeholder={t('filterDomainPlaceholder')}
                                value={pendingSearch}
                                onChange={e => setPendingSearch(e.target.value)}
                            />
                        </div>
                        {pendingSites.length > 0 && (
                            <button
                                className="btn btn-success"
                                onClick={() => handleBulkApprove(pendingSites.map(s => s.domain))}
                            >
                                <Check size={14} /> Duyệt tất cả ({pendingSites.length})
                            </button>
                        )}
                    </div>

                    {selectedPendingDomains.length > 0 && (
                        <div className="bulk-actions-bar" style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            background: 'rgba(245, 158, 11, 0.1)',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            borderRadius: 12,
                            padding: '12px 24px',
                            marginBottom: 16,
                        }}>
                            <div style={{ color: '#f59e0b', fontWeight: 600, fontSize: 14 }}>
                                {t('selectedSitesCount', { count: selectedPendingDomains.length })}
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button
                                    className="btn btn-sm btn-success"
                                    onClick={() => handleBulkApprove(selectedPendingDomains)}
                                >
                                    <Check size={12} /> {t('bulkApproveBtn')}
                                </button>
                                <button
                                    className="btn btn-sm btn-danger"
                                    onClick={() => handleBulkReject(selectedPendingDomains)}
                                >
                                    <Trash2 size={12} /> {t('bulkRejectBtn')}
                                </button>
                            </div>
                        </div>
                    )}

                    {filteredPending.length === 0 ? (
                        <div className="empty-state">
                            <Clock size={56} style={{ color: '#64748b' }} />
                            <h3>{t('noPendingSites')}</h3>
                            <p>{t('noPendingSitesSub')}</p>
                        </div>
                    ) : (
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style={{ width: 40 }}>
                                            <input
                                                type="checkbox"
                                                checked={filteredPending.length > 0 && selectedPendingDomains.length === filteredPending.length}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        setSelectedPendingDomains(filteredPending.map(s => s.domain));
                                                    } else {
                                                        setSelectedPendingDomains([]);
                                                    }
                                                }}
                                            />
                                        </th>
                                        <th>{t('domainCol')}</th>
                                        <th>{t('serverIpCol')}</th>
                                        <th>{t('clientIpCol')}</th>
                                        <th>{t('clusterCol')}</th>
                                        <th>{t('pendingSinceCol')}</th>
                                        <th style={{ textAlign: 'right' }}>{t('actionsCol')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredPending.map((site) => {
                                        const isSelected = selectedPendingDomains.includes(site.domain);
                                        const lastSeen = site.last_seen ? new Date(site.last_seen).toLocaleString('vi-VN') : 'Mới ping';
                                        return (
                                            <tr key={site.domain} className={isSelected ? 'selected-row' : ''} style={isSelected ? { background: 'rgba(245, 158, 11, 0.05)' } : {}}>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={isSelected}
                                                        onChange={() => {
                                                            setSelectedPendingDomains(prev =>
                                                                prev.includes(site.domain)
                                                                    ? prev.filter(d => d !== site.domain)
                                                                    : [...prev, site.domain]
                                                            );
                                                        }}
                                                    />
                                                </td>
                                                <td style={{ fontWeight: 600 }}>
                                                    <a href={`http://${site.domain}`} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                                        {site.domain} <ExternalLink size={10} />
                                                    </a>
                                                </td>
                                                <td>
                                                    <span style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        gap: 6,
                                                        background: 'rgba(56, 189, 248, 0.1)',
                                                        color: '#38bdf8',
                                                        padding: '3px 8px',
                                                        borderRadius: 6,
                                                        fontWeight: 600,
                                                        fontSize: 13
                                                    }}>
                                                        <Server size={13} /> {site.server_ip || site.ip || 'N/A'}
                                                    </span>
                                                </td>
                                                <td style={{ color: '#94a3b8', fontSize: 13 }}>
                                                    {site.ip || 'N/A'}
                                                </td>
                                                <td>
                                                    <span style={{
                                                        background: 'rgba(148,163,184,0.1)',
                                                        color: '#94a3b8',
                                                        padding: '2px 8px',
                                                        borderRadius: 6,
                                                        fontSize: 12
                                                    }}>
                                                        {site.cluster || 'default'}
                                                    </span>
                                                </td>
                                                <td style={{ color: '#94a3b8', fontSize: 13 }}>
                                                    {lastSeen}
                                                </td>
                                                <td style={{ textAlign: 'right' }}>
                                                    <div style={{ display: 'inline-flex', gap: 6, justifyContent: 'flex-end' }}>
                                                        <button
                                                            className="btn btn-sm btn-success"
                                                            style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                                            onClick={() => handleApproveSite(site.domain)}
                                                        >
                                                            <Check size={12} /> {t('approveBtn')}
                                                        </button>
                                                        <button
                                                            className="btn btn-sm btn-danger"
                                                            style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                                            onClick={() => handleRejectSite(site.domain)}
                                                        >
                                                            <Trash2 size={12} /> {t('rejectBtn')}
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            ) : (
            <>
            <div className="toolbar" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <div className="search-wrapper" style={{ flex: 1, minWidth: 240 }}>
                    <Search size={16} />
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Tìm kiếm domain (không cần chính xác), redirect, IP, server..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button 
                            onClick={() => setSearchQuery('')} 
                            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0 4px', fontSize: 14 }}
                            title="Xóa tìm kiếm"
                        >
                            ✕
                        </button>
                    )}
                </div>
                
                <div className="filter-group" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {/* Server filter */}
                    <select 
                        className="form-select" 
                        value={serverFilter} 
                        onChange={e => setServerFilter(e.target.value)}
                        style={{ minWidth: 190, maxWidth: 240 }}
                        title="Lọc theo Máy chủ (Server)"
                    >
                        <option value="ALL">🖥️ Server: Tất cả ({sites.length})</option>
                        {servers.map(srv => {
                            const count = serverSiteCounts[srv.host] || serverSiteCounts[srv.ip] || serverSiteCounts[String(srv.id)] || 0;
                            return (
                                <option key={srv.id} value={srv.host}>
                                    {srv.name ? `${srv.name} (${srv.host})` : srv.host} [{count}]
                                </option>
                            );
                        })}
                    </select>

                    {/* 301 Redirect Filter */}
                    <select 
                        className="form-select" 
                        value={redirectFilter} 
                        onChange={e => setRedirectFilter(e.target.value)}
                        style={{ width: 180 }}
                        title="Lọc trạng thái Chuyển hướng 301"
                    >
                        <option value="ALL">🔀 Redirect: Tất cả ({sites.length})</option>
                        <option value="REDIRECT">⚡ Có 301 Redirect ({redirectedTotal})</option>
                        <option value="DIRECT">🌐 Site trực tiếp ({directTotal})</option>
                    </select>

                    {/* Status filter */}
                    <select 
                        className="form-select" 
                        value={statusFilter} 
                        onChange={e => setStatusFilter(e.target.value)}
                        style={{ width: 125 }}
                    >
                        <option value="ALL">{t('allStatus')}</option>
                        <option value="ONLINE">{t('onlineSites')}</option>
                        <option value="OFFLINE">{t('offlineSites')}</option>
                    </select>

                    {/* Cluster filter */}
                    <select 
                        className="form-select" 
                        value={clusterFilter} 
                        onChange={e => setClusterFilter(e.target.value)}
                        style={{ width: 145 }}
                    >
                        <option value="ALL">{t('allClusters')}</option>
                        {clusters.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>

                    {/* Backlink filter */}
                    <select 
                        className="form-select" 
                        value={backlinkFilter} 
                        onChange={e => setBacklinkFilter(e.target.value)}
                        style={{ width: 135 }}
                    >
                        <option value="ALL">{t('allBacklinks')}</option>
                        <option value="0">{t('backlinksCount0')}</option>
                        <option value="1">{t('backlinksCount1')}</option>
                        <option value="2">{t('backlinksCount2')}</option>
                        <option value="3+">{t('backlinksCount3Plus')}</option>
                    </select>
                </div>

                {/* Scan 301 Redirect Button */}
                <button 
                    className="btn btn-sm" 
                    onClick={handleScanRedirects}
                    disabled={scanningRedirects}
                    style={{ 
                        background: 'rgba(234, 179, 8, 0.15)', 
                        color: '#fde047', 
                        border: '1px solid rgba(234, 179, 8, 0.35)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        fontWeight: 600
                    }}
                    title="Kiểm tra và quét tự động các site đã 301 redirect sang domain khác"
                >
                    <Zap size={14} style={{ color: '#eab308', animation: scanningRedirects ? 'spin 1s linear infinite' : 'none' }} />
                    {scanningRedirects ? 'Đang quét...' : 'Quét 301'}
                </button>

                <button className="btn btn-primary" onClick={() => setModal({
                    title: t('registerSitesTitle'),
                    content: <RegisterSiteForm addToast={addToast} onClose={() => setModal(null)} lang={lang} />
                })}>
                    <Plus size={14} /> {t('addSite')}
                </button>
            </div>

            {selectedDomains.length > 0 && (
                <div className="bulk-actions-bar" style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'rgba(34, 211, 238, 0.1)',
                    border: '1px solid rgba(34, 211, 238, 0.3)',
                    borderRadius: 12,
                    padding: '12px 24px',
                    marginBottom: 16,
                    flexWrap: 'wrap',
                    gap: 12
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ color: '#22d3ee', fontWeight: 600, fontSize: 14 }}>
                            {t('selectedSitesCount', { count: selectedDomains.length })}
                        </span>
                        {!isAllFilteredSelected && filtered.length > paginatedSites.length && (
                            <button
                                className="btn btn-sm"
                                onClick={() => setSelectedDomains(filtered.map(s => s.domain))}
                                style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid #0284c7', fontSize: 12 }}
                            >
                                Chọn toàn bộ {filtered.length} domain
                            </button>
                        )}
                        <button
                            className="btn btn-sm"
                            onClick={() => setSelectedDomains([])}
                            style={{ background: 'transparent', color: '#94a3b8', border: '1px solid #475569', fontSize: 12 }}
                        >
                            Bỏ chọn
                        </button>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button className="btn btn-sm btn-success" onClick={() => setModal({
                            title: t('bulkPostTitle', { count: selectedDomains.length }),
                            content: <CreatePostForm siteDomains={selectedDomains} addToast={addToast} onClose={() => { setSelectedDomains([]); setModal(null); }} lang={lang} />
                        })}>
                            <FileText size={12} /> {t('bulkPost')}
                        </button>
                        <button className="btn btn-sm btn-primary" onClick={() => setModal({
                            title: t('bulkLinkTitle', { count: selectedDomains.length }),
                            content: <InsertLinkForm siteDomains={selectedDomains} addToast={addToast} onClose={() => { setSelectedDomains([]); setModal(null); }} lang={lang} />
                        })}>
                            <Link2 size={12} /> {t('bulkLink')}
                        </button>
                        <button className="btn btn-sm" onClick={() => setModal({
                            title: t('editHeadTitle', { count: selectedDomains.length }),
                            content: <UpdateHeadForm siteDomains={selectedDomains} sites={sites} addToast={addToast} onClose={() => { setSelectedDomains([]); setModal(null); }} lang={lang} />
                        })}>
                            <Shield size={12} /> {t('editHeadSchema')}
                        </button>
                        <button className="btn btn-sm" onClick={() => setModal({
                            title: t('changeClusterTitle', { count: selectedDomains.length }),
                            content: <UpdateClusterForm siteDomains={selectedDomains} addToast={addToast} onClose={() => { setSelectedDomains([]); setModal(null); }} lang={lang} />
                        })}>
                            <Globe size={12} /> {t('changeCluster')}
                        </button>
                    </div>
                </div>
            )}

            {filtered.length === 0 ? (
                <div className="empty-state">
                    <Server size={56} />
                    <h3>{t('noSitesMatched')}</h3>
                    <p>{t('noSitesMatchedSub')}</p>
                </div>
            ) : (
                <>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ width: 40 }}>
                                    <input 
                                        type="checkbox" 
                                        checked={isCurrentPageSelected} 
                                        onChange={handleSelectAll} 
                                        title={isCurrentPageSelected ? "Bỏ chọn các domain trên trang này" : "Chọn tất cả domain trên trang này"}
                                    />
                                </th>
                                <th>{t('domainCol')}</th>
                                <th>{t('statusCol')}</th>
                                <th>{t('ipCol')}</th>
                                <th>{t('clusterCol')}</th>
                                <th>{t('backlinksToolCol')}</th>
                                <th>{t('homepageLinksCol')}</th>
                                <th>{t('pbnInlinksCol')}</th>
                                <th>{t('lastSeenCol')}</th>
                                <th style={{ textAlign: 'right' }}>{t('actionsCol')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedSites.map((site, rowIndex) => {
                                const isOnline = site.status === 'ONLINE';
                                const isSelected = selectedDomains.includes(site.domain);
                                const lastSeen = site.last_seen ? new Date(site.last_seen).toLocaleString('vi-VN') : 'Never';
                                return (
                                    <tr key={site.domain} className={isSelected ? 'selected-row' : ''} style={isSelected ? { background: 'rgba(34, 211, 238, 0.02)' } : {}}>
                                        <td>
                                            <input 
                                                type="checkbox" 
                                                checked={isSelected} 
                                                onChange={() => handleSelectRow(site.domain)} 
                                            />
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                    <a 
                                                        href={`http://${site.domain}`} 
                                                        target="_blank" 
                                                        rel="noreferrer" 
                                                        style={{ 
                                                            color: '#38bdf8', 
                                                            fontWeight: 600, 
                                                            fontSize: 14, 
                                                            textDecoration: 'none', 
                                                            display: 'inline-flex', 
                                                            alignItems: 'center', 
                                                            gap: 4 
                                                        }}
                                                    >
                                                        {site.domain} <ExternalLink size={11} />
                                                    </a>
                                                </div>
                                                {site.redirect_to && (
                                                    <div 
                                                        style={{ 
                                                            display: 'inline-flex', 
                                                            alignItems: 'center', 
                                                            gap: 5, 
                                                            background: 'rgba(234, 179, 8, 0.12)', 
                                                            border: '1px solid rgba(234, 179, 8, 0.35)', 
                                                            padding: '2px 8px', 
                                                            borderRadius: 6, 
                                                            fontSize: 11, 
                                                            color: '#fef08a',
                                                            maxWidth: '100%',
                                                            width: 'fit-content'
                                                        }}
                                                        title={`Domain gốc trên server đã 301 Redirect sang: ${site.redirect_to}`}
                                                    >
                                                        <span style={{ fontWeight: 700, color: '#eab308' }}>
                                                            ⚡ 301 ➔
                                                        </span>
                                                        <a 
                                                            href={site.redirect_to.startsWith('http') ? site.redirect_to : `http://${site.redirect_to}`} 
                                                            target="_blank" 
                                                            rel="noreferrer" 
                                                            style={{ 
                                                                color: '#fef08a', 
                                                                textDecoration: 'underline', 
                                                                fontWeight: 500,
                                                                maxWidth: 240, 
                                                                overflow: 'hidden', 
                                                                textOverflow: 'ellipsis', 
                                                                whiteSpace: 'nowrap' 
                                                            }}
                                                        >
                                                            {site.redirect_to.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                                                        </a>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <span className={`site-status-badge ${isOnline ? 'online' : 'offline'}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                                {isOnline ? 'Online' : 'Offline'}
                                            </span>
                                        </td>
                                        <td style={{ color: '#94a3b8' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                                <span style={{ color: '#e2e8f0', fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                                    <Server size={11} style={{ color: '#38bdf8' }} /> {site.server_ip || site.ip || 'N/A'}
                                                </span>
                                                {site.server_ip && site.ip && site.server_ip !== site.ip && (
                                                    <span style={{ fontSize: 11, color: '#64748b' }} title="IP TCP Socket / Proxy">
                                                        Proxy: {site.ip}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td>
                                            <span style={{ 
                                                background: site.cluster ? 'rgba(56,189,248,0.1)' : 'rgba(148,163,184,0.1)', 
                                                color: site.cluster ? '#38bdf8' : '#94a3b8',
                                                padding: '2px 8px',
                                                borderRadius: 6,
                                                fontSize: 12
                                            }}>
                                                {site.cluster || 'None'}
                                            </span>
                                        </td>
                                        <td>
                                            {(() => {
                                                const activeBks = backlinks.filter(b => b.site_domain === site.domain && b.status === 'active');
                                                const bkCount = activeBks.length;
                                                return (
                                                    <span 
                                                        className="backlink-count-badge"
                                                        onMouseEnter={(e) => handleMouseEnterBadge(e, site.domain, 'backlinks', `🎯 Backlinks Tool - ${site.domain}`, activeBks)}
                                                        onMouseLeave={handleMouseLeaveBadge}
                                                        onClick={() => bkCount > 0 && setModal({
                                                            title: `Backlinks Tool - ${site.domain}`,
                                                            content: (
                                                                <div style={{ padding: '8px 0', maxHeight: '70vh', overflowY: 'auto' }}>
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                                        {activeBks.map((b, idx) => {
                                                                            const sourceUrl = b.post_id ? `http://${site.domain}/?p=${b.post_id}` : `http://${site.domain}`;
                                                                            const sourceLabel = b.post_id ? `Bài viết #${b.post_id}` : `Trang chủ (${site.domain})`;
                                                                            return (
                                                                                <div key={idx} style={{ 
                                                                                    padding: '14px 16px', 
                                                                                    borderRadius: 10, 
                                                                                    background: 'rgba(30, 41, 59, 0.85)', 
                                                                                    border: '1px solid #334155', 
                                                                                    display: 'flex', 
                                                                                    flexDirection: 'column', 
                                                                                    gap: 8 
                                                                                }}>
                                                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
                                                                                        <span style={{ color: '#38bdf8', fontWeight: 700, fontSize: 15 }}>
                                                                                            {b.anchor_text}
                                                                                        </span>
                                                                                        <a 
                                                                                            href={sourceUrl} 
                                                                                            target="_blank" 
                                                                                            rel="noreferrer" 
                                                                                            style={{ 
                                                                                                color: '#34d399', 
                                                                                                background: 'rgba(52, 211, 153, 0.15)', 
                                                                                                border: '1px solid rgba(52, 211, 153, 0.3)', 
                                                                                                padding: '4px 12px', 
                                                                                                borderRadius: 6, 
                                                                                                fontSize: 12, 
                                                                                                fontWeight: 600, 
                                                                                                display: 'inline-flex', 
                                                                                                alignItems: 'center', 
                                                                                                gap: 6, 
                                                                                                textDecoration: 'none' 
                                                                                            }}
                                                                                        >
                                                                                            <ExternalLink size={12} /> Nguồn: {sourceLabel}
                                                                                        </a>
                                                                                    </div>
                                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#94a3b8' }}>
                                                                                        <span style={{ fontWeight: 600, color: '#64748b' }}>Target URL (Money Site):</span>
                                                                                        <a href={b.target_url} target="_blank" rel="noreferrer" style={{ color: '#cbd5e1', wordBreak: 'break-all', textDecoration: 'none' }}>
                                                                                            {b.target_url}
                                                                                        </a>
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </div>
                                                            )
                                                        })}
                                                        style={{ 
                                                            background: bkCount > 0 ? 'rgba(34, 211, 238, 0.15)' : 'rgba(148, 163, 184, 0.1)', 
                                                            color: bkCount > 0 ? '#22d3ee' : '#94a3b8',
                                                            border: bkCount > 0 ? '1px solid rgba(34, 211, 238, 0.3)' : '1px solid transparent',
                                                            padding: '4px 12px',
                                                            borderRadius: 6,
                                                            fontSize: 13,
                                                            fontWeight: 600,
                                                            cursor: bkCount > 0 ? 'pointer' : 'default'
                                                        }}
                                                        title={bkCount > 0 ? "Hover hoặc click để mở xem chi tiết" : ""}
                                                    >
                                                        {t('linksCountText', { count: bkCount })}
                                                    </span>
                                                );
                                            })()}
                                        </td>
                                        <td>
                                            {(() => {
                                                let outboundLinks = [];
                                                try {
                                                    if (site.homepage_outbound_links) {
                                                        outboundLinks = typeof site.homepage_outbound_links === 'string' 
                                                            ? JSON.parse(site.homepage_outbound_links) 
                                                            : site.homepage_outbound_links;
                                                    }
                                                } catch (e) {
                                                    console.error(e);
                                                }
                                                const outCount = outboundLinks.length || site.total_homepage_links || 0;
                                                return (
                                                    <span 
                                                        className="backlink-count-badge"
                                                        onMouseEnter={(e) => handleMouseEnterBadge(e, site.domain, 'outbound', `🌐 Outbound Links Trang Chủ - ${site.domain}`, outboundLinks)}
                                                        onMouseLeave={handleMouseLeaveBadge}
                                                        onClick={() => outCount > 0 && setModal({
                                                            title: `Outbound Links Trang Chủ - ${site.domain}`,
                                                            content: (
                                                                <div style={{ padding: '8px 0', maxHeight: '70vh', overflowY: 'auto' }}>
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                                        {outboundLinks.map((link, idx) => {
                                                                            const sourceUrl = `http://${site.domain}`;
                                                                            const sourceLabel = `Trang chủ (${site.domain})`;
                                                                            return (
                                                                                <div key={idx} style={{ 
                                                                                    padding: '14px 16px', 
                                                                                    borderRadius: 10, 
                                                                                    background: 'rgba(30, 41, 59, 0.85)', 
                                                                                    border: '1px solid #334155', 
                                                                                    display: 'flex', 
                                                                                    flexDirection: 'column', 
                                                                                    gap: 8 
                                                                                }}>
                                                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
                                                                                        <span style={{ color: '#38bdf8', fontWeight: 700, fontSize: 15 }}>
                                                                                            {link.anchor || '[No Anchor]'}
                                                                                        </span>
                                                                                        <a 
                                                                                            href={sourceUrl} 
                                                                                            target="_blank" 
                                                                                            rel="noreferrer" 
                                                                                            style={{ 
                                                                                                color: '#34d399', 
                                                                                                background: 'rgba(52, 211, 153, 0.15)', 
                                                                                                border: '1px solid rgba(52, 211, 153, 0.3)', 
                                                                                                padding: '4px 12px', 
                                                                                                borderRadius: 6, 
                                                                                                fontSize: 12, 
                                                                                                fontWeight: 600, 
                                                                                                display: 'inline-flex', 
                                                                                                alignItems: 'center', 
                                                                                                gap: 6, 
                                                                                                textDecoration: 'none' 
                                                                                            }}
                                                                                        >
                                                                                            <ExternalLink size={12} /> Nguồn: {sourceLabel}
                                                                                        </a>
                                                                                    </div>
                                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#94a3b8' }}>
                                                                                        <span style={{ fontWeight: 600, color: '#64748b' }}>Outbound URL:</span>
                                                                                        <a href={link.url} target="_blank" rel="noreferrer" style={{ color: '#cbd5e1', wordBreak: 'break-all', textDecoration: 'none' }}>
                                                                                            {link.url}
                                                                                        </a>
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </div>
                                                            )
                                                        })}

                                                        style={{ 
                                                            background: outCount > 0 ? 'rgba(34, 211, 238, 0.15)' : 'rgba(148, 163, 184, 0.1)', 
                                                            color: outCount > 0 ? '#22d3ee' : '#94a3b8',
                                                            border: outCount > 0 ? '1px solid rgba(34, 211, 238, 0.3)' : '1px solid transparent',
                                                            padding: '4px 12px',
                                                            borderRadius: 6,
                                                            fontSize: 13,
                                                            fontWeight: 600,
                                                            cursor: outCount > 0 ? 'pointer' : 'default'
                                                        }}
                                                        title={outCount > 0 ? "Hover hoặc click để mở xem chi tiết" : ""}
                                                    >
                                                        {t('linksCountText', { count: outCount })}
                                                    </span>
                                                );
                                            })()}
                                        </td>
                                        <td>
                                            {(() => {
                                                const inlinks = getNetworkInboundLinks(site.domain, sites, backlinks);
                                                const uniqueSitesCount = Array.from(new Set(inlinks.map(l => l.sourceDomain))).length;
                                                const inlinksCount = inlinks.length;
                                                return (
                                                    <span 
                                                        className="backlink-count-badge"
                                                        onMouseEnter={(e) => uniqueSitesCount > 0 && handleMouseEnterBadge(e, site.domain, 'pbn_inlinks', `🔗 PBN Inlinks (Hệ thống trỏ về) - ${site.domain}`, inlinks)}
                                                        onMouseLeave={handleMouseLeaveBadge}
                                                        onClick={() => uniqueSitesCount > 0 && setModal({
                                                            title: `🔗 PBN Inlinks (Các site trong hệ thống trỏ về ${site.domain})`,
                                                            content: (
                                                                <div style={{ padding: '8px 0', maxHeight: '70vh', overflowY: 'auto' }}>
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                                        {inlinks.map((link, idx) => {
                                                                            const sourceUrl = link.postId ? `http://${link.sourceDomain}/?p=${link.postId}` : `http://${link.sourceDomain}`;
                                                                            const sourceLabel = link.postId ? `${link.sourceDomain} (#${link.postId})` : `${link.sourceDomain}`;
                                                                            return (
                                                                                <div key={idx} style={{ 
                                                                                    padding: '14px 16px', 
                                                                                    borderRadius: 10, 
                                                                                    background: 'rgba(30, 41, 59, 0.85)', 
                                                                                    border: '1px solid #334155', 
                                                                                    display: 'flex', 
                                                                                    flexDirection: 'column', 
                                                                                    gap: 8 
                                                                                }}>
                                                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
                                                                                        <span style={{ color: '#c084fc', fontWeight: 700, fontSize: 15 }}>
                                                                                            {link.anchor || '[No Anchor]'}
                                                                                        </span>
                                                                                        <a 
                                                                                            href={sourceUrl} 
                                                                                            target="_blank" 
                                                                                            rel="noreferrer" 
                                                                                            style={{ 
                                                                                                color: '#c084fc', 
                                                                                                background: 'rgba(168, 85, 247, 0.15)', 
                                                                                                border: '1px solid rgba(168, 85, 247, 0.3)', 
                                                                                                padding: '4px 12px', 
                                                                                                borderRadius: 6, 
                                                                                                fontSize: 12, 
                                                                                                fontWeight: 600, 
                                                                                                display: 'inline-flex', 
                                                                                                alignItems: 'center', 
                                                                                                gap: 6, 
                                                                                                textDecoration: 'none' 
                                                                                            }}
                                                                                        >
                                                                                            <ExternalLink size={12} /> Nguồn: {sourceLabel}
                                                                                        </a>
                                                                                    </div>
                                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#94a3b8' }}>
                                                                                        <span style={{ fontWeight: 600, color: '#64748b' }}>Target URL (Site này):</span>
                                                                                        <a href={link.targetUrl} target="_blank" rel="noreferrer" style={{ color: '#cbd5e1', wordBreak: 'break-all', textDecoration: 'none' }}>
                                                                                            {link.targetUrl}
                                                                                        </a>
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </div>
                                                            )
                                                        })}
                                                        style={{ 
                                                            background: uniqueSitesCount > 0 ? 'rgba(168, 85, 247, 0.15)' : 'rgba(148, 163, 184, 0.1)', 
                                                            color: uniqueSitesCount > 0 ? '#c084fc' : '#94a3b8',
                                                            border: uniqueSitesCount > 0 ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid transparent',
                                                            padding: '4px 12px',
                                                            borderRadius: 6,
                                                            fontSize: 13,
                                                            fontWeight: 600,
                                                            cursor: uniqueSitesCount > 0 ? 'pointer' : 'default'
                                                        }}
                                                        title={uniqueSitesCount > 0 ? "Click để xem chi tiết các site trong hệ thống đang trỏ backlink về site này" : "Chưa có site nào trong hệ thống trỏ về"}
                                                    >
                                                        {t('sitesCountText', { sitesCount: uniqueSitesCount, linksCount: inlinksCount })}
                                                    </span>
                                                );
                                            })()}
                                        </td>

                                        <td style={{ color: '#64748b', fontSize: 13 }}>{lastSeen}</td>
                                        <td>
                                            <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                                                <button className="btn btn-sm btn-success" onClick={() => setModal({
                                                    title: `${t('postTitle')} - ${site.domain}`,
                                                    content: <CreatePostForm siteDomain={site.domain} addToast={addToast} onClose={() => setModal(null)} lang={lang} />
                                                })}>
                                                    <FileText size={10} /> {t('postBtn')}
                                                </button>
                                                <button className="btn btn-sm" onClick={() => setModal({
                                                    title: `${t('link')} - ${site.domain}`,
                                                    content: <InsertLinkForm siteDomain={site.domain} addToast={addToast} onClose={() => setModal(null)} lang={lang} />
                                                })}>
                                                    <Link2 size={10} /> {t('linkBtn')}
                                                </button>
                                                <button className="btn btn-sm" onClick={() => setModal({
                                                    title: `${t('head')} - ${site.domain}`,
                                                    content: <UpdateHeadForm siteDomains={[site.domain]} sites={sites} addToast={addToast} onClose={() => setModal(null)} lang={lang} />
                                                })}>
                                                    <Shield size={10} /> {t('headBtn')}
                                                </button>
                                                <button className="btn btn-sm" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.3)' }} onClick={() => setModal({
                                                    title: `⚙️ RAG Persona & Tone - ${site.domain}`,
                                                    content: <SiteProfileForm domain={site.domain} addToast={addToast} onClose={() => setModal(null)} lang={lang} />
                                                })}>
                                                    <Sliders size={10} /> {t('personaBtn')}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* PAGINATION BAR */}
                {filtered.length > 0 && (
                    <div className="pagination-bar" style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '14px 20px',
                        background: 'rgba(15, 23, 42, 0.85)',
                        border: '1px solid #334155',
                        borderTop: 'none',
                        borderRadius: '0 0 12px 12px',
                        marginBottom: 16,
                        flexWrap: 'wrap',
                        gap: 12
                    }}>
                        {/* Left: Summary */}
                        <div style={{ color: '#94a3b8', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span>
                                Hiển thị <strong style={{ color: '#38bdf8' }}>{pageSize === 'ALL' ? 1 : (safeCurrentPage - 1) * pageSize + 1}</strong> - <strong style={{ color: '#38bdf8' }}>{pageSize === 'ALL' ? filtered.length : Math.min(safeCurrentPage * pageSize, filtered.length)}</strong> trong <strong style={{ color: '#f8fafc' }}>{filtered.length}</strong> domain {sites.length !== filtered.length && `(Tổng: ${sites.length})`}
                            </span>
                        </div>

                        {/* Right: Page Navigation & Page Size Selector */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                            {/* Page size selector */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#94a3b8' }}>
                                <span>Mỗi trang:</span>
                                <select
                                    className="form-select"
                                    value={pageSize}
                                    onChange={e => {
                                        const val = e.target.value === 'ALL' ? 'ALL' : Number(e.target.value);
                                        setPageSize(val);
                                        setCurrentPage(1);
                                    }}
                                    style={{ width: 'auto', padding: '4px 10px', fontSize: 13, height: 32 }}
                                >
                                    <option value={50}>50 domain</option>
                                    <option value={100}>100 domain (Chuẩn)</option>
                                    <option value={200}>200 domain</option>
                                    <option value="ALL">Tất cả ({filtered.length})</option>
                                </select>
                            </div>

                            {/* Pagination buttons */}
                            {pageSize !== 'ALL' && totalPages > 1 && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <button
                                        className="btn btn-sm"
                                        disabled={safeCurrentPage === 1}
                                        onClick={() => setCurrentPage(1)}
                                        style={{ padding: '4px 8px', fontSize: 12, opacity: safeCurrentPage === 1 ? 0.35 : 1, cursor: safeCurrentPage === 1 ? 'not-allowed' : 'pointer' }}
                                        title="Trang đầu tiên"
                                    >
                                        ««
                                    </button>
                                    <button
                                        className="btn btn-sm"
                                        disabled={safeCurrentPage === 1}
                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                        style={{ padding: '4px 10px', fontSize: 12, opacity: safeCurrentPage === 1 ? 0.35 : 1, cursor: safeCurrentPage === 1 ? 'not-allowed' : 'pointer' }}
                                        title="Trang trước"
                                    >
                                        « Trước
                                    </button>

                                    {/* Dynamic Page Numbers */}
                                    {(() => {
                                        const pages = [];
                                        const maxVisible = 5;
                                        let startPage = Math.max(1, safeCurrentPage - 2);
                                        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
                                        if (endPage - startPage < maxVisible - 1) {
                                            startPage = Math.max(1, endPage - maxVisible + 1);
                                        }

                                        if (startPage > 1) {
                                            pages.push(
                                                <button key={1} className="btn btn-sm" onClick={() => setCurrentPage(1)} style={{ padding: '4px 10px', fontSize: 12 }}>
                                                    1
                                                </button>
                                            );
                                            if (startPage > 2) {
                                                pages.push(<span key="dots-start" style={{ color: '#64748b', padding: '0 2px' }}>...</span>);
                                            }
                                        }

                                        for (let p = startPage; p <= endPage; p++) {
                                            const isActive = p === safeCurrentPage;
                                            pages.push(
                                                <button
                                                    key={p}
                                                    className={`btn btn-sm ${isActive ? 'btn-primary' : ''}`}
                                                    onClick={() => setCurrentPage(p)}
                                                    style={{
                                                        padding: '4px 10px',
                                                        fontSize: 12,
                                                        fontWeight: isActive ? 700 : 500,
                                                        background: isActive ? '#0284c7' : 'rgba(30, 41, 59, 0.6)',
                                                        borderColor: isActive ? '#38bdf8' : '#334155',
                                                        color: isActive ? '#ffffff' : '#cbd5e1'
                                                    }}
                                                >
                                                    {p}
                                                </button>
                                            );
                                        }

                                        if (endPage < totalPages) {
                                            if (endPage < totalPages - 1) {
                                                pages.push(<span key="dots-end" style={{ color: '#64748b', padding: '0 2px' }}>...</span>);
                                            }
                                            pages.push(
                                                <button key={totalPages} className="btn btn-sm" onClick={() => setCurrentPage(totalPages)} style={{ padding: '4px 10px', fontSize: 12 }}>
                                                    {totalPages}
                                                </button>
                                            );
                                        }

                                        return pages;
                                    })()}

                                    <button
                                        className="btn btn-sm"
                                        disabled={safeCurrentPage === totalPages}
                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                        style={{ padding: '4px 10px', fontSize: 12, opacity: safeCurrentPage === totalPages ? 0.35 : 1, cursor: safeCurrentPage === totalPages ? 'not-allowed' : 'pointer' }}
                                        title="Trang sau"
                                    >
                                        Sau »
                                    </button>
                                    <button
                                        className="btn btn-sm"
                                        disabled={safeCurrentPage === totalPages}
                                        onClick={() => setCurrentPage(totalPages)}
                                        style={{ padding: '4px 8px', fontSize: 12, opacity: safeCurrentPage === totalPages ? 0.35 : 1, cursor: safeCurrentPage === totalPages ? 'not-allowed' : 'pointer' }}
                                        title="Trang cuối cùng"
                                    >
                                        »»
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}
                </>
            )}
            </>
            )}

            {/* FLOATING POPOVER (Fixed position outside table overflow) */}
            <FloatingPopover 
                popover={hoveredPopover} 
                onClose={() => setHoveredPopover(null)} 
            />
        </>
    );
}


// ============================================================
// BACKLINKS TAB
// ============================================================
function BacklinksTab({ backlinks, sites, addToast, refreshBacklinks, setModal, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [searchQuery, setSearchQuery] = useState('');
    const [grouping, setGrouping] = useState('none'); // 'none', 'target', 'anchor'

    const handleRemove = async (link) => {
        if (!confirm(t('confirmRemoveLink'))) return;
        try {
            const res = await fetch(`${API_BASE}/api/backlinks/remove`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: link.id, site_domain: link.site_domain, target_url: link.target_url }),
            });
            const data = await res.json();
            if (data.success) {
                addToast('Backlink removed successfully', 'success');
                refreshBacklinks();
            } else {
                addToast(data.error || 'Failed to remove', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
    };

    // Filter backlinks
    const filtered = backlinks.filter(link => 
        link.target_url?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        link.anchor_text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        link.site_domain?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const renderTable = () => {
        if (grouping === 'target') {
            const groups = {};
            filtered.forEach(link => {
                if (!groups[link.target_url]) {
                    groups[link.target_url] = { url: link.target_url, count: 0, sites: new Set(), anchors: new Set() };
                }
                groups[link.target_url].count++;
                groups[link.target_url].sites.add(link.site_domain);
                groups[link.target_url].anchors.add(link.anchor_text);
            });

            const groupList = Object.values(groups).sort((a, b) => b.count - a.count);

            return (
                <table>
                    <thead>
                        <tr>
                            <th>{t('targetUrl')} (Money Site)</th>
                            <th>{t('recordsPerPage')}</th>
                            <th>{t('sourceDomain')}</th>
                            <th>{t('anchorText')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {groupList.map(g => (
                            <tr key={g.url}>
                                <td style={{ fontWeight: 600, color: '#38bdf8' }}>
                                    <a href={g.url} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none' }}>{g.url}</a>
                                </td>
                                <td>
                                    <span style={{ background: 'rgba(34,211,238,0.1)', color: '#22d3ee', padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 'bold' }}>
                                        {g.count} links
                                    </span>
                                </td>
                                <td style={{ color: '#cbd5e1', fontSize: 13 }}>{Array.from(g.sites).join(', ')}</td>
                                <td style={{ color: '#94a3b8', fontSize: 13 }}>{Array.from(g.anchors).join(', ')}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            );
        }

        if (grouping === 'anchor') {
            const groups = {};
            filtered.forEach(link => {
                if (!groups[link.anchor_text]) {
                    groups[link.anchor_text] = { anchor: link.anchor_text, count: 0, sites: new Set(), targets: new Set() };
                }
                groups[link.anchor_text].count++;
                groups[link.anchor_text].sites.add(link.site_domain);
                groups[link.anchor_text].targets.add(link.target_url);
            });

            const groupList = Object.values(groups).sort((a, b) => b.count - a.count);

            return (
                <table>
                    <thead>
                        <tr>
                            <th>{t('anchorText')} (Keyword)</th>
                            <th>{t('recordsPerPage')}</th>
                            <th>{t('targetUrl')}</th>
                            <th>{t('sourceDomain')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {groupList.map(g => (
                            <tr key={g.anchor}>
                                <td style={{ fontWeight: 600, color: '#22d3ee' }}>{g.anchor}</td>
                                <td>
                                    <span style={{ background: 'rgba(34,211,238,0.1)', color: '#22d3ee', padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 'bold' }}>
                                        {g.count} links
                                    </span>
                                </td>
                                <td style={{ color: '#cbd5e1', fontSize: 13, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {Array.from(g.targets).join(', ')}
                                </td>
                                <td style={{ color: '#94a3b8', fontSize: 13 }}>{Array.from(g.sites).join(', ')}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            );
        }

        return (
            <table>
                <thead>
                    <tr>
                        <th>{t('sourceDomain')}</th>
                        <th>{t('targetUrl')}</th>
                        <th>{t('anchorText')}</th>
                        <th>{t('location')}</th>
                        <th>Paragraph</th>
                        <th>{t('status')}</th>
                        <th>{t('date')}</th>
                        <th>{t('actions')}</th>
                    </tr>
                </thead>
                <tbody>
                    {filtered.map(link => (
                        <tr key={link.id}>
                            <td style={{ fontWeight: 600, color: '#22d3ee' }}>{link.site_domain}</td>
                            <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{link.target_url}</td>
                            <td>{link.anchor_text}</td>
                            <td>
                                <span style={{ background: 'rgba(148,163,184,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 11, color: '#cbd5e1' }}>
                                    {link.location}
                                </span>
                            </td>
                            <td>
                                {link.paragraph_html ? (
                                    <span 
                                        className="backlink-count-badge"
                                        style={{ 
                                            background: 'rgba(34, 211, 238, 0.1)', 
                                            color: '#22d3ee',
                                            padding: '2px 8px',
                                            borderRadius: 6,
                                            fontSize: 11,
                                            fontWeight: 600,
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Hover to view
                                        <span className="tooltip-text" style={{ minWidth: 320, whiteSpace: 'normal', textAlign: 'left' }}>
                                            <div style={{ fontWeight: 'bold', color: '#22d3ee', paddingBottom: 6, borderBottom: '1px solid #475569', marginBottom: 6, fontSize: 13 }}>
                                                Paragraph Preview
                                            </div>
                                            <div 
                                                style={{ color: '#cbd5e1', fontSize: 12, lineHeight: '1.5' }} 
                                                dangerouslySetInnerHTML={{ __html: link.paragraph_html }} 
                                            />
                                        </span>
                                    </span>
                                ) : (
                                    <span style={{ color: '#64748b', fontSize: 12 }}>N/A</span>
                                )}
                            </td>
                            <td>
                                <span className={`site-status-badge ${link.status === 'active' ? 'online' : 'offline'}`}>
                                    {link.status}
                                </span>
                            </td>
                            <td>{new Date(link.created_at).toLocaleDateString('vi-VN')}</td>
                            <td>
                                {link.status === 'active' && (
                                    <button className="btn btn-sm btn-danger" onClick={() => handleRemove(link)}>
                                        <Trash2 size={12} /> {t('delete')}
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    return (
        <>
            <div className="toolbar" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={() => setModal({
                    title: t('insertBacklinkBtn'),
                    content: <InsertLinkForm sites={sites} addToast={addToast} onClose={() => { setModal(null); refreshBacklinks(); }} lang={lang} />
                })}>
                    <Plus size={14} /> {t('insertBacklinkBtn')}
                </button>

                <div className="search-wrapper" style={{ flex: 1, minWidth: 200 }}>
                    <Search size={16} />
                    <input
                        type="text"
                        className="search-input"
                        placeholder={t('searchBacklinksPlaceholder')}
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="filter-group" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <label style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500 }}>Group By:</label>
                    <select 
                        className="form-select" 
                        value={grouping} 
                        onChange={e => setGrouping(e.target.value)}
                        style={{ width: 150 }}
                    >
                        <option value="none">No Grouping</option>
                        <option value="target">By Target URL</option>
                        <option value="anchor">By Anchor Text</option>
                    </select>
                </div>
            </div>

            {filtered.length === 0 ? (
                <div className="empty-state">
                    <Link2 size={56} />
                    <h3>No backlinks matched</h3>
                    <p>Try modifying your search query or filters.</p>
                </div>
            ) : (
                <div className="table-container">
                    {renderTable()}
                </div>
            )}
        </>
    );
}

// ============================================================
// POSTS TAB
// ============================================================
function PostsTab({ posts, sites, addToast, refreshPosts, setModal, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedIds, setSelectedIds] = useState([]);
    const [deleting, setDeleting] = useState(false);

    const filtered = posts.filter(post => 
        post.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.site_domain?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(post.wp_post_id).includes(searchQuery)
    );

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedIds(filtered.map(p => p.id));
        } else {
            setSelectedIds([]);
        }
    };

    const handleSelectRow = (id) => {
        setSelectedIds(prev => 
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const handleDeletePost = async (post) => {
        if (!confirm(t('confirmDeletePost', { title: post.title }))) return;

        setDeleting(true);
        try {
            const res = await fetch(`${API_BASE}/api/posts/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: post.id, site_domain: post.site_domain, wp_post_id: post.wp_post_id }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã xóa thành công bài viết #${post.wp_post_id} khỏi ${post.site_domain}`, 'success');
                refreshPosts();
            } else {
                addToast(data.error || 'Lỗi khi xóa bài viết', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối Server', 'error');
        }
        setDeleting(false);
    };

    const handleBulkDelete = async () => {
        if (selectedIds.length === 0) return;
        const selectedPosts = posts.filter(p => selectedIds.includes(p.id));

        if (!confirm(t('confirmBulkDelete', { count: selectedPosts.length }))) return;

        setDeleting(true);
        try {
            const res = await fetch(`${API_BASE}/api/posts/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    posts: selectedPosts.map(p => ({ id: p.id, site_domain: p.site_domain, wp_post_id: p.wp_post_id }))
                }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã xóa hàng loạt thành công ${data.deleted.length} bài viết!`, 'success');
                setSelectedIds([]);
                refreshPosts();
            } else {
                addToast(data.error || 'Lỗi khi xóa hàng loạt', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối Server', 'error');
        }
        setDeleting(false);
    };

    const isAllSelected = filtered.length > 0 && selectedIds.length === filtered.length;

    return (
        <>
            <div className="toolbar" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                <button className="btn btn-primary" onClick={() => setModal({
                    title: t('postTitle'),
                    content: <CreatePostForm sites={sites} addToast={addToast} onClose={() => { setModal(null); refreshPosts(); }} lang={lang} />
                })}>
                    <Plus size={14} /> {t('postTitle')}
                </button>

                <div className="search-wrapper" style={{ flex: 1, minWidth: 250 }}>
                    <Search size={16} />
                    <input
                        type="text"
                        className="search-input"
                        placeholder={t('searchPostsPlaceholder')}
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {selectedIds.length > 0 && (
                <div className="bulk-actions-bar" style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 12,
                    padding: '12px 24px',
                    marginBottom: 16,
                }}>
                    <div style={{ color: '#f87171', fontWeight: 600, fontSize: 14 }}>
                        {t('selectedPostsCount', { count: selectedIds.length })}
                    </div>
                    <button className="btn btn-danger" onClick={handleBulkDelete} disabled={deleting}>
                        <Trash2 size={14} /> {deleting ? '...' : t('bulkDelete')}
                    </button>
                </div>
            )}

            {filtered.length === 0 ? (
                <div className="empty-state">
                    <FileText size={56} />
                    <h3>{t('noPostsFound')}</h3>
                    <p>{t('noPostsSub')}</p>
                </div>
            ) : (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ width: 40, textAlign: 'center' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={isAllSelected}
                                        onChange={handleSelectAll}
                                        style={{ cursor: 'pointer' }}
                                    />
                                </th>
                                <th>{t('siteDomain')}</th>
                                <th>{t('wpPostId')}</th>
                                <th>{t('postTitle')}</th>
                                <th>{t('status')}</th>
                                <th>{t('date')}</th>
                                <th style={{ textAlign: 'right' }}>{t('actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map(post => {
                                const postUrl = `http://${post.site_domain}/?p=${post.wp_post_id}`;
                                const isSelected = selectedIds.includes(post.id);

                                return (
                                    <tr key={post.id} style={{ background: isSelected ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                                        <td style={{ textAlign: 'center' }}>
                                            <input 
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => handleSelectRow(post.id)}
                                                style={{ cursor: 'pointer' }}
                                            />
                                        </td>
                                        <td style={{ fontWeight: 600, color: '#22d3ee' }}>{post.site_domain}</td>
                                        <td style={{ fontWeight: 600, color: '#94a3b8' }}>#{post.wp_post_id}</td>
                                        <td style={{ maxWidth: 450 }}>
                                            <a 
                                                href={postUrl} 
                                                target="_blank" 
                                                rel="noreferrer" 
                                                style={{ color: '#f8fafc', textDecoration: 'none', fontWeight: 500 }}
                                                onMouseEnter={e => e.target.style.color = '#38bdf8'}
                                                onMouseLeave={e => e.target.style.color = '#f8fafc'}
                                            >
                                                {post.title} <ExternalLink size={12} style={{ opacity: 0.6, marginLeft: 4 }} />
                                            </a>
                                        </td>
                                        <td><span className="site-status-badge online">{post.status || 'PUBLISHED'}</span></td>
                                        <td>{new Date(post.created_at).toLocaleDateString('vi-VN')}</td>
                                        <td style={{ textAlign: 'right' }}>
                                            <button 
                                                className="btn btn-sm btn-danger" 
                                                onClick={() => handleDeletePost(post)}
                                                disabled={deleting}
                                                title="Xóa vĩnh viễn bài viết này khỏi WordPress & Dashboard"
                                            >
                                                <Trash2 size={12} /> Xóa
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}

// ============================================================
// ============================================================
// ACTIVITY LOG TAB (Pagination, Month/Action Filter & Auto-Prune)
// ============================================================
function LogTab({ addToast, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(50);
    const [actionFilter, setActionFilter] = useState('');
    const [monthFilter, setMonthFilter] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [totalCount, setTotalCount] = useState(0);
    const [totalPages, setTotalPages] = useState(1);
    const [availableMonths, setAvailableMonths] = useState([]);
    const [pruning, setPruning] = useState(false);

    const fetchLogs = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page,
                limit,
                ...(actionFilter ? { action: actionFilter } : {}),
                ...(monthFilter ? { month: monthFilter } : {}),
                ...(searchQuery ? { search: searchQuery } : {})
            });

            const res = await authFetch(`${API_BASE}/api/log?${params.toString()}`);
            const data = await res.json();
            if (data.success) {
                setLogs(data.data || []);
                setTotalCount(data.totalCount || 0);
                setTotalPages(data.totalPages || 1);
                setAvailableMonths(data.availableMonths || []);
            }
        } catch (e) {
            console.error('Failed to fetch log', e);
        }
        setLoading(false);
    }, [page, limit, actionFilter, monthFilter, searchQuery]);

    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);

    const handlePruneLogs = async (clearAll = false) => {
        const msg = clearAll 
            ? '⚠️ DỌN SẠCH LOG: Bạn có chắc chắn muốn xóa TOÀN BỘ Activity Log?' 
            : 'Xóa tất cả bản ghi Log cũ hơn 30 ngày?';
        if (!confirm(msg)) return;

        setPruning(true);
        try {
            const res = await authFetch(`${API_BASE}/api/log/prune`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ daysToKeep: 30, clearAll })
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message, 'success');
                setPage(1);
                fetchLogs();
            } else {
                addToast(data.error || 'Lỗi dọn log', 'error');
            }
        } catch (e) {
            addToast('Lỗi mạng', 'error');
        }
        setPruning(false);
    };

    const getIcon = (action) => {
        if (action?.includes('heartbeat')) return <Activity size={14} />;
        if (action?.includes('offline')) return <WifiOff size={14} />;
        if (action?.includes('post')) return <FileText size={14} />;
        if (action?.includes('link') || action?.includes('backlink')) return <Link2 size={14} />;
        if (action?.includes('kill')) return <AlertTriangle size={14} />;
        return <Zap size={14} />;
    };

    const getIconClass = (action) => {
        if (action?.includes('heartbeat')) return 'heartbeat';
        if (action?.includes('offline')) return 'offline';
        if (action?.includes('post')) return 'post';
        if (action?.includes('link') || action?.includes('backlink')) return 'link';
        if (action?.includes('kill')) return 'kill';
        return 'heartbeat';
    };

    return (
        <div className="panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
                <div className="panel-title" style={{ marginBottom: 0 }}>
                    <Activity size={18} /> {t('logAuditTitle')}
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-sm" onClick={() => handlePruneLogs(false)} disabled={pruning} title="Dọn dẹp log cũ hơn 30 ngày">
                        <Trash2 size={12} /> {pruning ? t('pruningLogs') : t('pruneOldLogs')}
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handlePruneLogs(true)} disabled={pruning} title="Xóa toàn bộ nhật ký log">
                        <AlertTriangle size={12} /> {t('clearAllLogs')}
                    </button>
                </div>
            </div>

            {/* BỘ LỌC SEARCH & FILTER TOOLBAR */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 16, background: 'rgba(30, 41, 59, 0.4)', padding: 14, borderRadius: 10, border: '1px solid #334155' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Filter size={11} /> {t('actionFilter')}
                    </label>
                    <select className="form-select" value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1); }}>
                        <option value="">{t('allActions')}</option>
                        <option value="heartbeat">{t('heartbeatAction')}</option>
                        <option value="post">{t('postAction')}</option>
                        <option value="link">{t('linkAction')}</option>
                        <option value="registered">{t('registeredAction')}</option>
                        <option value="login">{t('loginAction')}</option>
                        <option value="kill">{t('killAction')}</option>
                    </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Calendar size={11} /> {t('monthFilter')}
                    </label>
                    <select className="form-select" value={monthFilter} onChange={e => { setMonthFilter(e.target.value); setPage(1); }}>
                        <option value="">{t('allMonths')}</option>
                        {availableMonths.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Search size={11} /> {t('searchDomain')}
                    </label>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                    />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ fontSize: 11 }}>{t('recordsPerPage')}</label>
                    <select className="form-select" value={limit} onChange={e => { setLimit(parseInt(e.target.value)); setPage(1); }}>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                        <option value={200}>200</option>
                    </select>
                </div>
            </div>

            {/* DANH SÁCH LOG BẢN GHI */}
            {loading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#38bdf8' }}>
                    <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', marginRight: 8 }} /> Loading...
                </div>
            ) : logs.length === 0 ? (
                <div className="empty-state">
                    <Activity size={56} />
                    <h3>{t('noLogsFound')}</h3>
                    <p style={{ fontSize: 13, color: '#64748b' }}>{t('noLogsSub')}</p>
                </div>
            ) : (
                <>
                    {logs.map(item => (
                        <div key={item.id} className="log-item">
                            <div className={`log-icon ${getIconClass(item.action)}`}>
                                {getIcon(item.action)}
                            </div>
                            <div className="log-content">
                                <div>
                                    <span className="log-action">{item.action}</span>
                                    {' — '}
                                    <span className="log-domain">{item.site_domain}</span>
                                </div>
                                <div className="log-time">
                                    {new Date(item.created_at).toLocaleString('vi-VN')}
                                    {item.details && ` • ${typeof item.details === 'string' ? item.details.substring(0, 100) : JSON.stringify(item.details)}`}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* THANH PHÂN TRANG (PAGINATION BAR) */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginTop: 20, paddingTop: 16, borderTop: '1px solid #334155' }}>
                        <div style={{ fontSize: 13, color: '#94a3b8' }}>
                            {t('pageInfo', { count: logs.length, total: totalCount, page, totalPages })}
                        </div>

                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <button
                                className="btn btn-sm"
                                disabled={page <= 1 || loading}
                                onClick={() => setPage(prev => Math.max(1, prev - 1))}
                            >
                                <ChevronLeft size={14} /> {t('prevPage')}
                            </button>

                            <span style={{ fontSize: 13, color: '#38bdf8', fontWeight: 600, padding: '0 8px' }}>
                                {page} / {totalPages}
                            </span>

                            <button
                                className="btn btn-sm"
                                disabled={page >= totalPages || loading}
                                onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                            >
                                {t('nextPage')} <ChevronRight size={14} />
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

// ============================================================
// CONTROL PANEL — Kill Switch & Mass Actions
// ============================================================
function ControlPanel({ sites, clusters, addToast, refreshAll, currentUser, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [killTarget, setKillTarget] = useState('');
    const [killType, setKillType] = useState('site');
    const [loading, setLoading] = useState(false);

    const executeKillSwitch = async () => {
        if (!killTarget) return addToast('Please select a target', 'error');
        if (!confirm(`⚠️ KILL SWITCH: This will remove ALL backlinks from ${killType === 'cluster' ? `cluster "${killTarget}"` : killTarget}. Are you sure?`)) return;

        setLoading(true);
        try {
            const body = killType === 'cluster' ? { cluster: killTarget } : { site_domain: killTarget };
            const res = await fetch(`${API_BASE}/api/backlinks/kill-switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Kill Switch executed! ${data.data?.length || 0} sites processed`, 'success');
                refreshAll();
            } else {
                addToast(data.error || 'Kill switch failed', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setLoading(false);
    };

    return (
        <div className="panel">
            <div className="panel-title"><Shield size={18} /> {t('controlPanel')}</div>

            {/* Kill Switch */}
            <div style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 12, padding: 24, marginTop: 16 }}>
                <h3 style={{ color: '#ef4444', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, fontSize: 16 }}>
                    <AlertTriangle size={18} /> {t('killSwitchTitle')}
                </h3>
                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 16 }}>
                    {t('killSwitchDesc')}
                </p>

                <div className="form-row">
                    <div className="form-group">
                        <label className="form-label">{t('targetType')}</label>
                        <select className="form-select" value={killType} onChange={e => { setKillType(e.target.value); setKillTarget(''); }}>
                            <option value="site">{t('singleSite')}</option>
                            <option value="cluster">{t('entireCluster')}</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">
                            {t('selectTarget')}
                        </label>
                        <select className="form-select" value={killTarget} onChange={e => setKillTarget(e.target.value)}>
                            <option value="">-- {t('selectTarget')} --</option>
                            {killType === 'cluster'
                                ? clusters.map(c => <option key={c} value={c}>{c}</option>)
                                : sites.map(s => <option key={s.domain} value={s.domain}>{s.domain}</option>)
                            }
                        </select>
                    </div>
                </div>

                <button className="btn btn-danger btn-lg" onClick={executeKillSwitch} disabled={loading} style={{ marginTop: 8 }}>
                    <AlertTriangle size={16} /> {loading ? t('executing') : t('executeKillSwitch')}
                </button>
            </div>

            {/* OpenClaw AI Task Manager Section */}
            <OpenClawTaskCenter addToast={addToast} lang={lang} />

            {/* User Management Section */}
            <UserManagementSection addToast={addToast} currentUser={currentUser} lang={lang} />
        </div>
    );
}

function UserManagementSection({ addToast, currentUser, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [users, setUsers] = useState([]);
    const [newUsername, setNewUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [creating, setCreating] = useState(false);

    const fetchUsers = useCallback(async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/users`);
            const data = await res.json();
            if (data.success) setUsers(data.data || []);
        } catch (e) {
            console.error(e);
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleCreateUser = async (e) => {
        e.preventDefault();
        if (!newUsername.trim() || !newPassword.trim()) {
            return addToast(t('usernameLabel') + ' & ' + t('passwordLabel') + ' required', 'error');
        }

        setCreating(true);
        try {
            const res = await authFetch(`${API_BASE}/api/users/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: newUsername, password: newPassword }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message, 'success');
                setNewUsername('');
                setNewPassword('');
                fetchUsers();
            } else {
                addToast(data.error || 'Failed', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setCreating(false);
    };

    const handleDeleteUser = async (user) => {
        if (!confirm(t('confirmDeleteUser', { username: user.username }))) return;
        try {
            const res = await authFetch(`${API_BASE}/api/users/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: user.id }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message, 'success');
                fetchUsers();
            } else {
                addToast(data.error || 'Failed', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
    };

    return (
        <div style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid #334155', borderRadius: 12, padding: 24, marginTop: 24 }}>
            <h3 style={{ color: '#38bdf8', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, fontSize: 16 }}>
                <UserCheck size={18} /> {t('userManagement')}
            </h3>

            {/* Form tạo user */}
            <form onSubmit={handleCreateUser} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 12, marginBottom: 20 }}>
                <input
                    type="text"
                    className="form-input"
                    placeholder={`${t('usernameLabel')}...`}
                    value={newUsername}
                    onChange={e => setNewUsername(e.target.value)}
                />
                <input
                    type="password"
                    className="form-input"
                    placeholder={`${t('passwordLabel')}...`}
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                />
                <button type="submit" className="btn btn-primary" disabled={creating}>
                    <Plus size={14} /> {creating ? '...' : t('createUser')}
                </button>
            </form>

            {/* Bảng danh sách users */}
            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>{t('usernameCol')}</th>
                            <th>{t('roleCol')}</th>
                            <th>{t('createdAtCol')}</th>
                            <th style={{ textAlign: 'right' }}>{t('actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id}>
                                <td style={{ color: '#64748b' }}>#{u.id}</td>
                                <td style={{ fontWeight: 600, color: '#f8fafc' }}>
                                    {u.username} {currentUser && currentUser.id === u.id && <span style={{ fontSize: 11, color: '#38bdf8', background: 'rgba(56,189,248,0.15)', padding: '2px 6px', borderRadius: 4, marginLeft: 6 }}>You</span>}
                                </td>
                                <td><span className="site-status-badge online">{u.role || 'admin'}</span></td>
                                <td>{new Date(u.created_at).toLocaleDateString('vi-VN')}</td>
                                <td style={{ textAlign: 'right' }}>
                                    {currentUser && currentUser.id !== u.id && (
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteUser(u)}>
                                            <Trash2 size={12} /> {t('deleteUserBtn')}
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ============================================================
// OPENCLAW TASK CENTER COMPONENT
// ============================================================
function OpenClawTaskCenter({ addToast, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [command, setCommand] = useState('');
    const [sending, setSending] = useState(false);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchTasks = useCallback(async () => {
        try {
            const res = await authFetch(`${API_BASE}/api/openclaw/tasks`);
            const data = await res.json();
            if (data.success) {
                setTasks(data.data || []);
            }
        } catch (e) {
            console.error('Failed to fetch OpenClaw tasks', e);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchTasks();
        socket.on('openclaw:task', (evt) => {
            setTasks(prev => [evt, ...prev]);
        });
        socket.on('openclaw:task_completed', (evt) => {
            setTasks(prev => prev.map(tk => (tk.task_id === evt.taskId || tk.taskId === evt.taskId || tk.id === evt.taskId) ? { ...tk, status: evt.status, response: evt.response } : tk));
        });
        return () => {
            socket.off('openclaw:task');
            socket.off('openclaw:task_completed');
        };
    }, [fetchTasks]);

    const handleSendTask = async (e) => {
        e?.preventDefault();
        if (!command.trim()) return addToast('Please enter a command for OpenClaw', 'error');

        setSending(true);
        try {
            const res = await authFetch(`${API_BASE}/api/openclaw/command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command.trim() })
            });
            const data = await res.json();
            if (data.success) {
                addToast(`🤖 OpenClaw Task #${data.taskId} dispatched!`, 'success');
                setCommand('');
                fetchTasks();
            } else {
                addToast(data.error || 'Failed to dispatch task', 'error');
            }
        } catch (err) {
            addToast('Network error', 'error');
        }
        setSending(false);
    };

    const handleQuickAction = (cmdText) => {
        setCommand(cmdText);
    };

    return (
        <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(6, 182, 212, 0.3)', borderRadius: 14, padding: 24, marginTop: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                    <h3 style={{ color: '#06b6d4', margin: 0, display: 'flex', alignItems: 'center', gap: 10, fontSize: 17 }}>
                        <Cpu size={20} /> OpenClaw Agent Task Center
                    </h3>
                    <p style={{ color: '#94a3b8', fontSize: 13, margin: '4px 0 0 0' }}>
                        {t('openclawSubtitle')}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span className="status-dot online" style={{ background: '#06b6d4', boxShadow: '0 0 8px #06b6d4' }} />
                    <span style={{ fontSize: 12, color: '#38bdf8', fontWeight: 600 }}>VPS Agent Active</span>
                </div>
            </div>

            {/* Quick Action Chips */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                <button type="button" className="btn btn-sm" style={{ background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.25)', fontSize: 12 }} onClick={() => handleQuickAction('Kiểm tra trạng thái toàn bộ 200 site PBN')}>
                    🔍 Check 200 Sites Status
                </button>
                <button type="button" className="btn btn-sm" style={{ background: 'rgba(168, 85, 247, 0.12)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.25)', fontSize: 12 }} onClick={() => handleQuickAction('Thống kê tổng số lượng backlinks đang active')}>
                    🔗 Audit Backlink Count
                </button>
                <button type="button" className="btn btn-sm" style={{ background: 'rgba(52, 211, 153, 0.12)', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.25)', fontSize: 12 }} onClick={() => handleQuickAction('Dọn dẹp nhật ký log cũ hơn 30 ngày')}>
                    🧹 Prune Old Logs (&gt;30 Days)
                </button>
            </div>

            {/* Command Form */}
            <form onSubmit={handleSendTask} style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
                <input
                    type="text"
                    className="form-input"
                    placeholder={t('openclawInputPlaceholder')}
                    value={command}
                    onChange={e => setCommand(e.target.value)}
                    style={{ flex: 1, fontFamily: 'sans-serif' }}
                />
                <button type="submit" className="btn btn-primary" disabled={sending} style={{ minWidth: 160, background: '#0891b2', borderColor: '#06b6d4' }}>
                    <Zap size={14} /> {sending ? t('openclawSending') : t('openclawSendBtn')}
                </button>
            </form>

            {/* Recent Tasks List */}
            <div style={{ fontWeight: 600, fontSize: 14, color: '#f8fafc', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Clock size={14} style={{ color: '#06b6d4' }} /> {t('openclawRecentTasks')}
            </div>

            {loading ? (
                <div style={{ color: '#64748b', fontSize: 13, textAlign: 'center', padding: 20 }}>Loading tasks...</div>
            ) : tasks.length === 0 ? (
                <div style={{ color: '#64748b', fontSize: 13, fontStyle: 'italic', textAlign: 'center', padding: 20, background: 'rgba(30, 41, 59, 0.3)', borderRadius: 8 }}>
                    {t('openclawNoTasks')}
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 300, overflowY: 'auto' }}>
                    {tasks.map(tk => {
                        const isDone = tk.status === 'completed';
                        const isFail = tk.status === 'failed';
                        const badgeColor = isDone ? '#34d399' : isFail ? '#f87171' : '#38bdf8';
                        const badgeBg = isDone ? 'rgba(52, 211, 153, 0.15)' : isFail ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.15)';

                        return (
                            <div key={tk.id || tk.task_id || tk.taskId} style={{ background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', borderRadius: 10, padding: 14 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                    <span style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 14 }}>
                                        💬 {tk.command}
                                    </span>
                                    <span style={{ background: badgeBg, color: badgeColor, padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700 }}>
                                        {tk.status ? tk.status.toUpperCase() : 'PENDING'}
                                    </span>
                                </div>
                                {tk.response && (
                                    <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: 10, borderRadius: 6, fontSize: 13, color: '#cbd5e1', fontFamily: 'monospace', whiteSpace: 'pre-wrap', border: '1px solid #1e293b' }}>
                                        {tk.response}
                                    </div>
                                )}
                                <div style={{ fontSize: 11, color: '#64748b', marginTop: 6 }}>
                                    Task ID: #{tk.task_id || tk.taskId} • Created: {new Date(tk.created_at || tk.timestamp || Date.now()).toLocaleString('vi-VN')}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

// ============================================================
// FORMS
// ============================================================
function SiteProfileForm({ domain, addToast, onClose }) {
    const [tone, setTone] = useState('Informative & Professional');
    const [brand, setBrand] = useState('');
    const [logoUrl, setLogoUrl] = useState('');
    const [language, setLanguage] = useState('vi');
    const [persona, setPersona] = useState('SEO Expert');
    const [forbiddenTerms, setForbiddenTerms] = useState('');
    const [customInstructions, setCustomInstructions] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/sites/${domain}/profile`);
                const data = await res.json();
                if (data.success && data.data) {
                    setTone(data.data.tone || 'Informative & Professional');
                    setBrand(data.data.brand || '');
                    setLogoUrl(data.data.logo_url || '');
                    setLanguage(data.data.language || 'vi');
                    setPersona(data.data.persona || 'SEO Expert');
                    setForbiddenTerms(data.data.forbidden_terms || '');
                    setCustomInstructions(data.data.custom_instructions || '');
                }
            } catch (e) {
                console.error(e);
            }
            setLoading(false);
        };
        fetchProfile();
    }, [domain]);

    const submit = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/sites/${domain}/profile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tone, brand, logo_url: logoUrl, language, persona,
                    forbidden_terms: forbiddenTerms,
                    custom_instructions: customInstructions
                }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã lưu cấu hình RAG, Persona & Logo cho ${domain}`, 'success');
                onClose();
            } else {
                addToast(data.error || 'Lỗi khi lưu', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối Server', 'error');
        }
        setSaving(false);
    };

    if (loading) return <div style={{ padding: 20, textAlign: 'center', color: '#38bdf8' }}>Đang tải cấu hình Persona...</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 13, color: '#c084fc', background: 'rgba(168, 85, 247, 0.08)', padding: 12, borderRadius: 8, border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                🎯 <strong>RAG, Persona & Logo Engine</strong>: Cấu hình phong cách và Logo watermark cho <strong>{domain}</strong>. Ảnh bài viết sẽ được tự động chèn Logo/Favicon của site trước khi post.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Tone of Voice (Văn phong)</label>
                    <select className="form-select" value={tone} onChange={e => setTone(e.target.value)}>
                        <option value="Informative & Professional">Tin tức & Trang trọng (Informative)</option>
                        <option value="Casino & Gambling Expert">Chuyên gia iGaming & Cá cược (Kịch tính, Hấp dẫn)</option>
                        <option value="Engaging & Friendly">Thân thiện, Gần gũi (Blog/Reviewer)</option>
                        <option value="Instructional & Educational">Hướng dẫn Chi tiết & Mẹo hay (Instructional)</option>
                        <option value="Persuasive & Sales">Thuyết phục & Kích thích Nạp tiền (Sales)</option>
                    </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Persona Role (Vai trò AI)</label>
                    <input className="form-input" placeholder="VD: Senior Casino Analyst" value={persona} onChange={e => setPersona(e.target.value)} />
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Tên Thương Hiệu (Brand Name)</label>
                    <input className="form-input" placeholder="VD: DE88 Club, PBN Site 2" value={brand} onChange={e => setBrand(e.target.value)} />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Ngôn Ngữ Bài Viết</label>
                    <select className="form-select" value={language} onChange={e => setLanguage(e.target.value)}>
                        <option value="vi">Tiếng Việt (Vietnamese)</option>
                        <option value="en">Tiếng Anh (English)</option>
                        <option value="zh">Tiếng Trung (Chinese)</option>
                    </select>
                </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Logo / Favicon URL (Đóng dấu Watermark vào ảnh bài viết)</span>
                    <button type="button" style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: 11 }} onClick={() => setLogoUrl(`https://${domain}/favicon.ico`)}>
                        ⚡ Lấy Mặc Định (favicon.ico)
                    </button>
                </label>
                <input className="form-input" placeholder={`Mặc định: https://${domain}/favicon.ico`} value={logoUrl} onChange={e => setLogoUrl(e.target.value)} />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ color: '#f87171' }}>Từ Khóa Cấm (Forbidden Words / Terms)</label>
                <textarea
                    className="form-input"
                    rows={2}
                    placeholder="VD: lừa đảo, lừa khách, quịt tiền, cờ bạc lừa (cách nhau bởi dấu phẩy)"
                    value={forbiddenTerms}
                    onChange={e => setForbiddenTerms(e.target.value)}
                />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Chỉ Đạo Đặc Thù Cho Site (Custom RAG Directives)</label>
                <textarea
                    className="form-input"
                    rows={3}
                    placeholder="VD: Luôn xưng hưng 'Chúng tôi', thêm ví dụ thực tế ở mỗi thẻ H2, kết bài nhắc nhở cá cược có trách nhiệm."
                    value={customInstructions}
                    onChange={e => setCustomInstructions(e.target.value)}
                />
            </div>

            <button className="btn btn-primary btn-lg" onClick={submit} disabled={saving} style={{ marginTop: 6 }}>
                {saving ? 'Đang lưu Cấu hình...' : 'Lưu Cấu Hình RAG & Persona'}
            </button>
        </div>
    );
}

function RegisterSiteForm({ addToast, onClose }) {
    const [domainsInput, setDomainsInput] = useState('');
    const [cluster, setCluster] = useState('default');
    const [checkActive, setCheckActive] = useState(true);
    const [loading, setLoading] = useState(false);
    const [resultSummary, setResultSummary] = useState(null);

    const submit = async () => {
        const rawDomains = domainsInput.trim();
        if (!rawDomains) return addToast('Vui lòng nhập ít nhất 1 domain', 'error');

        setLoading(true);
        setResultSummary(null);

        try {
            const res = await fetch(`${API_BASE}/api/sites/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domains: rawDomains,
                    cluster: cluster || 'default',
                    check_active: checkActive
                }),
            });
            const data = await res.json();
            
            if (data.registered && data.registered.length > 0) {
                addToast(`Đã đăng ký thành công ${data.registered.length} site!`, 'success');
            }

            if (data.failed && data.failed.length > 0) {
                addToast(`⚠️ Có ${data.failed.length} site KHÔNG REGISTER ĐƯỢC (không active)!`, 'error');
            }

            setResultSummary(data);

            if (data.success && (!data.failed || data.failed.length === 0)) {
                setTimeout(() => {
                    onClose();
                }, 1500);
            }
        } catch (e) {
            addToast('Lỗi kết nối Server', 'error');
        }
        setLoading(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {!resultSummary ? (
                <>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label" style={{ fontWeight: 600, color: '#38bdf8' }}>
                            Danh Sách Domain (Mỗi domain 1 dòng hoặc cách nhau bởi phẩy)
                        </label>
                        <textarea
                            className="form-input"
                            rows={5}
                            placeholder={`pbnsite1.group\npbnsite2.group\ndomain3.com`}
                            value={domainsInput}
                            onChange={e => setDomainsInput(e.target.value)}
                            style={{ resize: 'vertical', fontFamily: 'monospace', fontSize: 13 }}
                        />
                    </div>

                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                            <label className="form-label">Cluster Name</label>
                            <input
                                className="form-input"
                                placeholder="default"
                                value={cluster}
                                onChange={e => setCluster(e.target.value)}
                            />
                        </div>

                        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, marginTop: 20 }}>
                            <input
                                type="checkbox"
                                id="checkActive"
                                checked={checkActive}
                                onChange={e => setCheckActive(e.target.checked)}
                                style={{ width: 16, height: 16, cursor: 'pointer' }}
                            />
                            <label htmlFor="checkActive" style={{ fontSize: 13, color: '#cbd5e1', cursor: 'pointer', userSelect: 'none' }}>
                                Kiểm tra Active trước khi Register
                            </label>
                        </div>
                    </div>

                    <button
                        className="btn btn-primary btn-lg"
                        onClick={submit}
                        disabled={loading}
                        style={{ width: '100%', marginTop: 8 }}
                    >
                        <Plus size={16} /> {loading ? 'Đang kiểm tra & Register...' : 'Register Sites'}
                    </button>
                </>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: 15, fontWeight: 'bold', color: '#22d3ee' }}>
                        📊 Kết quả Đăng Ký ({resultSummary.total} Sites)
                    </div>

                    {/* Danh sách thành công */}
                    {resultSummary.registered && resultSummary.registered.length > 0 && (
                        <div style={{ background: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)', borderRadius: 10, padding: 14 }}>
                            <div style={{ color: '#34d399', fontWeight: 700, marginBottom: 8, fontSize: 14 }}>
                                ✅ Đăng Ký Thành Công ({resultSummary.registered.length})
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 150, overflowY: 'auto' }}>
                                {resultSummary.registered.map((item, idx) => (
                                    <div key={idx} style={{ fontSize: 13, color: '#e2e8f0', display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ fontWeight: 600 }}>🌐 {item.domain}</span>
                                        <span style={{ color: '#34d399', fontSize: 12 }}>ONLINE & Active</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Danh sách thất bại */}
                    {resultSummary.failed && resultSummary.failed.length > 0 && (
                        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 10, padding: 14 }}>
                            <div style={{ color: '#f87171', fontWeight: 700, marginBottom: 8, fontSize: 14 }}>
                                ❌ KHÔNG REGISTER ĐƯỢC - Không Active được ({resultSummary.failed.length})
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
                                {resultSummary.failed.map((item, idx) => (
                                    <div key={idx} style={{ fontSize: 13, color: '#fca5a5', background: 'rgba(15, 23, 42, 0.6)', padding: '8px 10px', borderRadius: 6, border: '1px solid #450a0a' }}>
                                        <div style={{ fontWeight: 700, color: '#ef4444' }}>⚠️ {item.domain}</div>
                                        <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 2 }}>Lý do: {item.error}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                        <button className="btn" onClick={() => setResultSummary(null)} style={{ flex: 1 }}>
                            Thêm Domain Khác
                        </button>
                        <button className="btn btn-primary" onClick={onClose} style={{ flex: 1 }}>
                            Đóng Cửa Sổ
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

function CreatePostForm({ siteDomain, siteDomains, sites, addToast, onClose }) {
    const domains = siteDomains || (siteDomain ? [siteDomain] : []);
    const [selectedDomains, setSelectedDomains] = useState(domains);
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);
    const editorRef = React.useRef(null);
    const quillRef = React.useRef(null);

    React.useEffect(() => {
        if (window.Quill && editorRef.current && !quillRef.current) {
            quillRef.current = new window.Quill(editorRef.current, {
                theme: 'snow',
                placeholder: 'Start writing content (HTML formatting is supported, images will copy automatically)...',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'color': [] }, { 'background': [] }],
                        ['link', 'image'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        ['clean']
                    ]
                }
            });
            quillRef.current.on('text-change', () => {
                setContent(quillRef.current.root.innerHTML);
            });
        }
    }, []);

    const submit = async () => {
        if (selectedDomains.length === 0 || !title || !content) return addToast('All fields required', 'error');
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/posts/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ site_domains: selectedDomains, title, content }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Post "${title}" created successfully on ${selectedDomains.length} sites`, 'success');
                onClose();
            } else {
                addToast(data.error || 'Failed to create post', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setLoading(false);
    };

    return (
        <>
            {domains.length === 0 && sites && (
                <div className="form-group">
                    <label className="form-label">Target Site(s)</label>
                    <select 
                        className="form-select" 
                        multiple 
                        value={selectedDomains} 
                        onChange={e => setSelectedDomains(Array.from(e.target.selectedOptions, option => option.value))}
                        style={{ height: 100 }}
                    >
                        {sites.map(s => <option key={s.domain} value={s.domain}>{s.domain}</option>)}
                    </select>
                    <small style={{ color: '#64748b' }}>Hold Ctrl (or Cmd) to select multiple sites.</small>
                </div>
            )}
            {selectedDomains.length > 0 && (
                <div style={{ marginBottom: 12, fontSize: 13, color: '#94a3b8' }}>
                    Posting to: <strong style={{ color: '#22d3ee' }}>{selectedDomains.join(', ')}</strong>
                </div>
            )}
            <div className="form-group">
                <label className="form-label">Title</label>
                <input className="form-input" placeholder="Post title" value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div className="form-group">
                <label className="form-label">Content</label>
                <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, overflow: 'hidden' }}>
                    <div ref={editorRef} style={{ height: '220px', border: 'none', color: '#f8fafc' }} />
                </div>
            </div>
            <button className="btn btn-primary btn-lg" onClick={submit} disabled={loading} style={{ width: '100%', marginTop: 12 }}>
                <Send size={16} /> {loading ? 'Publishing...' : 'Publish Post'}
            </button>
        </>
    );
}

function InsertLinkForm({ siteDomain, siteDomains, sites, addToast, onClose }) {
    const domains = siteDomains || (siteDomain ? [siteDomain] : []);
    const [selectedDomains, setSelectedDomains] = useState(domains);
    const [content, setContent] = useState('');
    const [detectedLinks, setDetectedLinks] = useState([]);
    const [location, setLocation] = useState(domains.length > 1 ? 'footer' : 'homepage_post');
    const [postId, setPostId] = useState('');
    const [loading, setLoading] = useState(false);
    const editorRef = React.useRef(null);
    const quillRef = React.useRef(null);

    React.useEffect(() => {
        if (window.Quill && editorRef.current && !quillRef.current) {
            quillRef.current = new window.Quill(editorRef.current, {
                theme: 'snow',
                placeholder: 'Write your lead-in sentence and insert backlinks here. Use the link icon on the toolbar to add anchors...',
                modules: {
                    toolbar: [
                        ['bold', 'italic', 'underline'],
                        ['link'],
                        ['clean']
                    ]
                }
            });
            quillRef.current.on('text-change', () => {
                const html = quillRef.current.root.innerHTML;
                setContent(html);

                // Detect backlinks
                const regex = /<a[^>]+href=["']([^"']+)["'][^>]*>(.*?)<\/a>/gi;
                const found = [];
                let match;
                while ((match = regex.exec(html)) !== null) {
                    found.push({
                        url: match[1],
                        anchor: match[2].replace(/<[^>]*>/g, '') // strip nested html
                    });
                }
                setDetectedLinks(found);
            });
        }
    }, [sites]);

    const submit = async () => {
        if (selectedDomains.length === 0) return addToast('Please select at least one site', 'error');
        if (!content.trim() || content === '<p><br></p>') return addToast('Content is required', 'error');
        if (detectedLinks.length === 0) return addToast('Please add at least one backlink inside the editor using the link tool', 'error');

        setLoading(true);
        try {
            const endpoint = selectedDomains.length > 1 ? '/api/backlinks/insert-bulk' : '/api/backlinks/insert';
            const body = selectedDomains.length > 1 
                ? { site_domains: selectedDomains, link_html: content, location }
                : { site_domain: selectedDomains[0], link_html: content, location, post_id: postId ? parseInt(postId) : undefined };

            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Link inserted successfully on ${selectedDomains.length} sites`, 'success');
                onClose();
            } else {
                addToast(data.error || 'Failed', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setLoading(false);
    };

    return (
        <>
            {domains.length === 0 && sites && (
                <div className="form-group">
                    <label className="form-label">Target Site(s)</label>
                    <select 
                        className="form-select" 
                        multiple 
                        value={selectedDomains} 
                        onChange={e => setSelectedDomains(Array.from(e.target.selectedOptions, option => option.value))}
                        style={{ height: 100 }}
                    >
                        {sites.map(s => <option key={s.domain} value={s.domain}>{s.domain}</option>)}
                    </select>
                    <small style={{ color: '#64748b' }}>Hold Ctrl (or Cmd) to select multiple sites.</small>
                </div>
            )}
            {selectedDomains.length > 0 && (
                <div style={{ marginBottom: 12, fontSize: 13, color: '#94a3b8' }}>
                    Inserting link on: <strong style={{ color: '#22d3ee' }}>{selectedDomains.join(', ')}</strong>
                </div>
            )}
            <div className="form-group">
                <label className="form-label">Lead-in Text & Backlinks (Rich Text Editor)</label>
                <p style={{ color: '#64748b', fontSize: 11, margin: '2px 0 8px 0' }}>
                    💡 You can write multiple sentence options separated by <strong>"|"</strong> to randomly select one per site (e.g. <code>Sentence A with link | Sentence B with link</code>).
                </p>
                <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, overflow: 'hidden' }}>
                    <div ref={editorRef} style={{ height: '180px', border: 'none', color: '#f8fafc' }} />
                </div>
            </div>

            {/* List of detected backlinks */}
            <div style={{ marginBottom: 16 }}>
                {detectedLinks.length > 0 ? (
                    <div style={{ padding: 12, background: 'rgba(34, 211, 238, 0.05)', border: '1px solid rgba(34, 211, 238, 0.2)', borderRadius: 8 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: '#22d3ee', marginBottom: 6 }}>
                            Detected Backlinks ({detectedLinks.length}):
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, color: '#cbd5e1', listStyleType: 'disc' }}>
                            {detectedLinks.map((link, idx) => (
                                <li key={idx} style={{ marginBottom: 4 }}>
                                    <strong style={{ color: '#38bdf8' }}>{link.anchor}</strong> &rarr; <span style={{ color: '#94a3b8' }}>{link.url}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : (
                    <div style={{ padding: 10, background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 8, fontSize: 12, color: '#fca5a5' }}>
                        No backlinks detected yet. Please select text and click the 🔗 (link) button in the editor toolbar to add your backlink(s).
                    </div>
                )}
            </div>

            <div className="form-row">
                <div className="form-group">
                    <label className="form-label">Location</label>
                    <select 
                        className="form-select" 
                        value={location} 
                        onChange={e => setLocation(e.target.value)}
                    >
                        <option value="footer">Homepage Footer</option>
                        <option value="homepage_post">Homepage Latest Post</option>
                        {selectedDomains.length <= 1 && <option value="post">In a Specific Post</option>}
                    </select>
                </div>
                {location === 'post' && selectedDomains.length <= 1 && (
                    <div className="form-group">
                        <label className="form-label">Post ID (optional, latest if empty)</label>
                        <input className="form-input" placeholder="123" value={postId} onChange={e => setPostId(e.target.value)} />
                    </div>
                )}
            </div>
            <button className="btn btn-primary btn-lg" onClick={submit} disabled={loading} style={{ width: '100%', marginTop: 12 }}>
                <Link2 size={16} /> {loading ? 'Inserting...' : 'Insert Backlink'}
            </button>
        </>
    );
}

function UpdateHeadForm({ siteDomains, sites, addToast, onClose }) {
    const [headCode, setHeadCode] = useState(() => {
        if (siteDomains && siteDomains.length === 1 && sites) {
            const site = sites.find(s => s.domain === siteDomains[0]);
            return site ? (site.head_code || '') : '';
        }
        return '';
    });
    const [loading, setLoading] = useState(false);

    const submit = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/sites/update-head`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ site_domains: siteDomains, head_code: headCode }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Head script updated on ${siteDomains.length} sites`, 'success');
                onClose();
            } else {
                addToast(data.error || 'Failed to update', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setLoading(false);
    };

    return (
        <>
            <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 12 }}>
                Inject custom scripts, meta tags, or schema code into the <code>&lt;head&gt;</code> of {siteDomains.length} selected sites.
            </p>
            <div className="form-group">
                <label className="form-label">Head Code (HTML/JS/CSS)</label>
                <textarea 
                    className="form-textarea" 
                    placeholder="<!-- Paste your Schema JSON-LD, Analytics tracking code or meta tags here -->" 
                    value={headCode} 
                    onChange={e => setHeadCode(e.target.value)} 
                    style={{ height: 200, fontFamily: 'monospace' }}
                />
            </div>
            <button className="btn btn-primary btn-lg" onClick={submit} disabled={loading} style={{ width: '100%' }}>
                <Send size={16} /> {loading ? 'Saving...' : 'Update Head Code'}
            </button>
        </>
    );
}

function UpdateClusterForm({ siteDomains, addToast, onClose }) {
    const [cluster, setCluster] = useState('');
    const [loading, setLoading] = useState(false);

    const submit = async () => {
        if (!cluster.trim()) return addToast('Cluster name is required', 'error');
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/sites/update-clusters`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ site_domains: siteDomains, cluster: cluster.trim() }),
            });
            const data = await res.json();
            if (data.success) {
                addToast(`Cluster updated for ${siteDomains.length} sites`, 'success');
                onClose();
            } else {
                addToast(data.error || 'Failed to update', 'error');
            }
        } catch (e) {
            addToast('Network error', 'error');
        }
        setLoading(false);
    };

    return (
        <>
            <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 12 }}>
                Set a new cluster designation for {siteDomains.length} selected sites.
            </p>
            <div className="form-group">
                <label className="form-label">New Cluster Name</label>
                <input 
                    className="form-input" 
                    placeholder="e.g. Health, Finance, PBN-Tier1" 
                    value={cluster} 
                    onChange={e => setCluster(e.target.value)} 
                />
            </div>
            <button className="btn btn-primary btn-lg" onClick={submit} disabled={loading} style={{ width: '100%' }}>
                <Plus size={16} /> {loading ? 'Updating...' : 'Change Cluster'}
            </button>
        </>
    );
}

// ============================================================
// AI WRITER TAB
// ============================================================
function AIWriterTab({ sites, addToast, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const [subTab, setSubTab] = useState('generator'); // 'generator', 'seo_assistant', or 'settings'
    const [targetUrl, setTargetUrl] = useState('');
    const [anchorText, setAnchorText] = useState('');
    const [userCommandPrompt, setUserCommandPrompt] = useState('');
    const [customInstructions, setCustomInstructions] = useState('');
    const [targetLang, setTargetLang] = useState('vi');

    const [seoPlan, setSeoPlan] = useState(null);
    const [generatingPlan, setGeneratingPlan] = useState(false);
    const [publishedUrls, setPublishedUrls] = useState([]);

    const [aiProvider, setAiProvider] = useState('openai');
    const [aiApiKey, setAiApiKey] = useState('');
    const [aiApiBase, setAiApiBase] = useState('https://api.openai.com/v1');
    const [aiModel, setAiModel] = useState('gpt-4o');
    const [seoPrompt, setSeoPrompt] = useState('');
    const [rewritePrompt, setRewritePrompt] = useState('');
    const [useHistoryChain, setUseHistoryChain] = useState(false);
    const [historyChainPrompt, setHistoryChainPrompt] = useState('');

    const [selectedSites, setSelectedSites] = useState([]);
    const [mode, setMode] = useState('keywords'); // 'keywords' or 'urls'
    const [keywordsText, setKeywordsText] = useState('');
    const [urlsText, setUrlsText] = useState('');
    const [articlesCount, setArticlesCount] = useState(1);
    const [logs, setLogs] = useState([]);
    const [running, setRunning] = useState(false);

    // Fetch settings on mount
    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings/ai`);
            const data = await res.json();
            if (data.success && data.data) {
                const s = data.data;
                setAiProvider(s.ai_provider || 'openai');
                setAiApiKey(s.ai_api_key || '');
                setAiApiBase(s.ai_api_base || 'https://api.openai.com/v1');
                setAiModel(s.ai_model || 'gpt-4o');
                setSeoPrompt(s.ai_seo_prompt || '');
                setRewritePrompt(s.ai_rewrite_prompt || '');
                setUseHistoryChain(s.ai_use_history_chain === 'true');
                setHistoryChainPrompt(s.ai_history_chain_prompt || '');
            }
        } catch (e) {
            console.error('Failed to load AI settings');
        }
    };

    const saveSettings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/settings/ai`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ai_provider: aiProvider,
                    ai_api_key: aiApiKey,
                    ai_api_base: aiApiBase,
                    ai_model: aiModel,
                    ai_seo_prompt: seoPrompt,
                    ai_rewrite_prompt: rewritePrompt,
                    ai_use_history_chain: useHistoryChain ? 'true' : 'false',
                    ai_history_chain_prompt: historyChainPrompt
                })
            });
            const data = await res.json();
            if (data.success) {
                addToast('AI Settings saved successfully', 'success');
            } else {
                addToast(data.error || 'Failed to save settings', 'error');
            }
        } catch (e) {
            addToast('Network error while saving settings', 'error');
        }
    };

    // Socket listener for logs & completed URLs
    useEffect(() => {
        const handleProgress = (data) => {
            setLogs(prev => [...prev, data]);
            if (data.type === 'published_url' || (data.step && data.step.toLowerCase().includes('published wp post'))) {
                if (data.details && data.details.includes('http')) {
                    const matches = data.details.match(/https?:\/\/[^\s]+/g);
                    if (matches) {
                        setPublishedUrls(prev => [...new Set([...prev, ...matches])]);
                    }
                }
            }
        };

        const handleCompleted = (job) => {
            if (job && job.results && Array.isArray(job.results)) {
                const urls = job.results.filter(r => r.url).map(r => r.url);
                if (urls.length > 0) {
                    setPublishedUrls(prev => [...new Set([...prev, ...urls])]);
                }
            }
        };

        socket.on('ai:progress', handleProgress);
        socket.on('ai:job_completed', handleCompleted);
        return () => {
            socket.off('ai:progress', handleProgress);
            socket.off('ai:job_completed', handleCompleted);
        };
    }, []);

    // Brainstorm SEO Plan (SEO Employee Mode)
    const handleBrainstormPlan = async () => {
        if (!targetUrl.trim() && !userCommandPrompt.trim()) {
            return addToast('Vui lòng nhập Trang đích (Target URL) hoặc Câu lệnh tự do cho Nhân viên SEO AI', 'error');
        }

        setGeneratingPlan(true);
        setSeoPlan(null);
        try {
            const res = await fetch(`${API_BASE}/api/ai/seo-assistant/plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_prompt: userCommandPrompt.trim(),
                    target_url: targetUrl.trim(),
                    anchor_text: anchorText.trim(),
                    site_domains: selectedSites.length > 0 ? selectedSites : sites.map(s => s.domain),
                    articles_count: articlesCount,
                    language: targetLang
                })
            });
            const data = await res.json();
            if (data.success && data.plan) {
                setSeoPlan(data.plan);
                addToast('🧠 Đã lập xong Kế Hoạch SEO! Vui lòng kiểm tra và bấm "Duyệt & Tiến Hành Đăng Bài".', 'success');
            } else {
                addToast(data.error || 'Lỗi khi lập kế hoạch SEO', 'error');
            }
        } catch (e) {
            addToast('Lỗi mạng khi phân tích kế hoạch SEO', 'error');
        }
        setGeneratingPlan(false);
    };

    // Approve Plan & Launch Publishing
    const handleApproveAndLaunchPlan = async () => {
        if (!seoPlan) return;
        setRunning(true);
        try {
            const res = await fetch(`${API_BASE}/api/ai/seo-assistant/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_url: seoPlan.targetUrl || targetUrl.trim(),
                    anchor_text: seoPlan.anchorText || anchorText.trim(),
                    site_domains: selectedSites.length > 0 ? selectedSites : sites.map(s => s.domain),
                    articles_count: articlesCount,
                    plan: seoPlan
                })
            });
            const data = await res.json();
            if (data.success) {
                addToast(`🚀 Đã duyệt Kế hoạch & Khởi chạy Chiến dịch SEO #${data.jobId}! AI đang viết bài và đăng ngầm.`, 'success');
            } else {
                addToast(data.error || 'Lỗi khi khởi chạy chiến dịch SEO', 'error');
            }
        } catch (e) {
            addToast('Lỗi mạng khi gọi API Autonomous SEO', 'error');
        }
        setRunning(false);
    };

    // Content Generator (Manual Mode)
    const handleGenerate = async () => {
        if (selectedSites.length === 0) {
            return addToast('Please select at least one PBN site', 'error');
        }
        
        let kwList = [];
        let urlList = [];
        
        if (mode === 'keywords') {
            kwList = keywordsText.split('\n').map(k => k.trim()).filter(Boolean);
            if (kwList.length === 0) return addToast('Please enter at least one keyword', 'error');
        } else {
            urlList = urlsText.split('\n').map(u => u.trim()).filter(Boolean);
            if (urlList.length === 0) return addToast('Please enter at least one target URL', 'error');
        }

        setRunning(true);
        
        try {
            const res = await fetch(`${API_BASE}/api/ai/generate-publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    site_domains: selectedSites,
                    mode,
                    keywords: kwList,
                    urls: urlList,
                    articles_count: articlesCount,
                    custom_instructions: customInstructions
                })
            });
            
            const data = await res.json();
            if (data.success) {
                addToast(`🚀 Đã khởi chạy tiến trình tạo bài viết ngầm #${data.jobId}!`, 'success');
            } else {
                addToast(data.error || 'AI generation process failed', 'error');
            }
        } catch (e) {
            addToast('Network error during generation', 'error');
        }
        setRunning(false);
    };

    const toggleSite = (domain) => {
        setSelectedSites(prev => 
            prev.includes(domain) ? prev.filter(d => d !== domain) : [...prev, domain]
        );
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, width: '100%' }}>
            {/* Top Verification Status Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid #1e293b', padding: '10px 18px', borderRadius: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <span style={{ fontSize: 13, color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Zap size={14} color="#10b981" /> 🔌 OpenClaw Gateway: <strong>Connected (Port 18789/18791)</strong>
                    </span>
                    <span style={{ fontSize: 13, color: '#38bdf8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Cpu size={14} color="#38bdf8" /> 🤖 AI Engine: <strong>{aiProvider.toUpperCase()} ({aiModel})</strong>
                    </span>
                </div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                    VPS Node: <code>38.180.203.206</code>
                </div>
            </div>

            <div style={{ display: 'flex', gap: 20, width: '100%' }}>
                {/* Left Column: Form & Settings */}
                <div style={{ flex: 2, background: 'rgba(30, 41, 59, 0.5)', border: '1px solid #334155', borderRadius: 16, padding: 24 }}>
                    <div style={{ display: 'flex', gap: 10, borderBottom: '1px solid #334155', paddingBottom: 12, marginBottom: 20 }}>
                        <button 
                            className={`btn ${subTab === 'generator' ? 'btn-primary' : ''}`} 
                            onClick={() => setSubTab('generator')}
                        >
                            Content Generator
                        </button>
                        <button 
                            className={`btn ${subTab === 'seo_assistant' ? 'btn-primary' : ''}`} 
                            style={subTab === 'seo_assistant' ? { background: '#0891b2', borderColor: '#06b6d4' } : {}}
                            onClick={() => setSubTab('seo_assistant')}
                        >
                            🚀 SEO Employee Mode
                        </button>
                        <button 
                            className={`btn ${subTab === 'settings' ? 'btn-primary' : ''}`} 
                            onClick={() => setSubTab('settings')}
                        >
                            API Settings
                        </button>
                    </div>

                    {subTab === 'seo_assistant' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <div style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.3)', borderRadius: 10, padding: 14 }}>
                                <h4 style={{ color: '#06b6d4', margin: '0 0 6px 0', fontSize: 15 }}>
                                    🎯 Chế Độ Nhân Viên SEO Chuyên Nghiệp (SEO Employee Mode)
                                </h4>
                                <p style={{ color: '#cbd5e1', fontSize: 13, margin: 0 }}>
                                    Nhập yêu cầu bằng câu lệnh tự do ➔ OpenClaw & AI tự phân tích đối thủ & Lập Kế Hoạch ➔ Bạn xem duyệt Kế hoạch trước khi bấm Đăng bài.
                                </p>
                            </div>

                            <div className="form-group">
                                <label className="form-label" style={{ color: '#38bdf8', fontWeight: 600 }}>
                                    💬 Câu Lệnh Tự Do Cho Nhân Viên SEO (SEO Prompt / Directive)
                                </label>
                                <textarea
                                    className="form-textarea"
                                    style={{ height: 90 }}
                                    placeholder="Ví dụ: Hãy lập chiến dịch kéo từ khóa cho website https://megapari-peru.com/ với 3 bài viết iGaming tiếng Tây Ban Nha, phân tích đối thủ và chèn backlink ngữ cảnh tự nhiên."
                                    value={userCommandPrompt}
                                    onChange={e => setUserCommandPrompt(e.target.value)}
                                />
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">{t('targetUrlLabel')}</label>
                                    <input
                                        type="url"
                                        className="form-input"
                                        placeholder="https://megapari-peru.com/"
                                        value={targetUrl}
                                        onChange={e => setTargetUrl(e.target.value)}
                                    />
                                </div>

                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">{t('anchorTextLabel')}</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Để trống AI tự chọn từ khóa neo"
                                        value={anchorText}
                                        onChange={e => setAnchorText(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">Ngôn Ngữ Bài Viết & Cơ Sở Tìm Kiếm (Language & Search Context)</label>
                                    <select className="form-select" value={targetLang} onChange={e => setTargetLang(e.target.value)}>
                                        <option value="vi">🇻🇳 Tiếng Việt (Vietnamese - Mặc định)</option>
                                        <option value="en">🇺🇸 Tiếng Anh (English - US/UK)</option>
                                        <option value="es">🇪🇸 Tiếng Tây Ban Nha (Spanish - Peru/LatAm/Spain)</option>
                                        <option value="pt">🇧🇷 Tiếng Bồ Đào Nha (Portuguese - Brazil/Portugal)</option>
                                        <option value="zh">🇨🇳 Tiếng Trung (Chinese - Simplified)</option>
                                        <option value="ja">🇯🇵 Tiếng Nhật (Japanese)</option>
                                        <option value="ko">🇰🇷 Tiếng Hàn (Korean)</option>
                                        <option value="th">🇹🇭 Tiếng Thái (Thai)</option>
                                        <option value="id">🇮🇩 Tiếng Indonesia (Indonesian)</option>
                                        <option value="de">🇩🇪 Tiếng Đức (German)</option>
                                        <option value="fr">🇫🇷 Tiếng Pháp (French)</option>
                                        <option value="ru">🇷🇺 Tiếng Nga (Russian)</option>
                                        <option value="it">🇮🇹 Tiếng Ý (Italian)</option>
                                        <option value="tr">🇹🇷 Tiếng Thổ Nhĩ Kỳ (Turkish)</option>
                                        <option value="ar">🇦🇪 Tiếng Ả Rập (Arabic)</option>
                                    </select>
                                </div>

                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">Số Lượng Bài Viết (Articles Count)</label>
                                    <input 
                                        type="number" 
                                        className="form-input" 
                                        min="1" 
                                        max="20"
                                        value={articlesCount} 
                                        onChange={e => setArticlesCount(parseInt(e.target.value) || 1)}
                                    />
                                </div>
                            </div>

                            <button 
                                className="btn btn-primary btn-lg" 
                                onClick={handleBrainstormPlan} 
                                disabled={generatingPlan || running}
                                style={{ background: 'linear-gradient(135deg, #0891b2 0%, #0284c7 100%)', borderColor: '#06b6d4', marginTop: 4 }}
                            >
                                <Sparkles size={16} /> {generatingPlan ? 'OpenClaw & AI Đang Phân Tích Kế Hoạch...' : '🧠 Phân Tích & Lập Kế Hoạch SEO'}
                            </button>

                            {/* PLAN REVIEW BOX */}
                            {seoPlan && (
                                <div style={{ background: 'rgba(15, 23, 42, 0.9)', border: '2px solid #06b6d4', borderRadius: 14, padding: 18, marginTop: 10 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155', paddingBottom: 10, marginBottom: 12 }}>
                                        <h4 style={{ color: '#38bdf8', margin: 0, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                                            📋 Kế Hoạch SEO Đề Xuất (Chờ Bạn Duyệt)
                                        </h4>
                                        <span style={{ fontSize: 12, background: 'rgba(6, 182, 212, 0.2)', color: '#06b6d4', padding: '2px 8px', borderRadius: 6 }}>
                                            {seoPlan.articles?.length || 0} Bài viết
                                        </span>
                                    </div>

                                    <div style={{ fontSize: 13, color: '#e2e8f0', marginBottom: 12 }}>
                                        <strong>📌 Chiến lược:</strong> {seoPlan.strategy || 'Phân bổ bài viết chất lượng cao kèm backlink ngữ cảnh.'}
                                    </div>

                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 220, overflowY: 'auto', marginBottom: 16 }}>
                                        {seoPlan.articles?.map((art, idx) => (
                                            <div key={idx} style={{ background: 'rgba(30, 41, 59, 0.8)', border: '1px solid #334155', borderRadius: 8, padding: 10, fontSize: 12 }}>
                                                <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: 2 }}>
                                                    Bài #{idx + 1}: {art.topic}
                                                </div>
                                                <div style={{ color: '#94a3b8', display: 'flex', gap: 12 }}>
                                                    <span>🌐 Target Site: <strong style={{ color: '#cbd5e1' }}>{art.targetDomain}</strong></span>
                                                    <span>🔗 Anchor: <strong style={{ color: '#cbd5e1' }}>{art.anchorText}</strong></span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div style={{ display: 'flex', gap: 10 }}>
                                        <button 
                                            className="btn btn-primary btn-lg" 
                                            onClick={handleApproveAndLaunchPlan} 
                                            disabled={running}
                                            style={{ flex: 2, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', borderColor: '#10b981' }}
                                        >
                                            <Zap size={16} /> {running ? 'Đang Khởi Chạy Đăng Bài...' : '🟢 Duyệt & Tiến Hành Đăng Bài'}
                                        </button>
                                        <button 
                                            className="btn" 
                                            onClick={() => setSeoPlan(null)} 
                                            disabled={running}
                                            style={{ flex: 1, background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.4)' }}
                                        >
                                            🔴 Hủy / Làm Lại
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : subTab === 'settings' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <div className="form-group">
                                <label className="form-label">AI Provider</label>
                                <select className="form-select" value={aiProvider} onChange={e => setAiProvider(e.target.value)}>
                                    <option value="openai">OpenAI</option>
                                    <option value="openrouter">OpenRouter</option>
                                    <option value="9router">9Router</option>
                                    <option value="gemini">Google Gemini</option>
                                    <option value="poe">Poe API</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label className="form-label">API Key</label>
                                <input 
                                    type="password" 
                                    className="form-input" 
                                    placeholder="Paste your API key here..." 
                                    value={aiApiKey} 
                                    onChange={e => setAiApiKey(e.target.value)} 
                                />
                            </div>

                            {aiProvider !== 'gemini' && (
                                <div className="form-group">
                                    <label className="form-label">API Base URL (Optional)</label>
                                    <input 
                                        className="form-input" 
                                        placeholder={aiProvider === 'openrouter' ? 'https://openrouter.ai/api/v1' : aiProvider === '9router' ? 'https://api.9router.com/v1' : aiProvider === 'poe' ? 'https://api.poe.com/v1' : 'https://api.openai.com/v1'} 
                                        value={aiApiBase} 
                                        onChange={e => setAiApiBase(e.target.value)} 
                                    />
                                </div>
                            )}

                            <div className="form-group">
                                <label className="form-label">Model Name</label>
                                <input 
                                    className="form-input" 
                                    placeholder={aiProvider === 'gemini' ? 'gemini-1.5-pro' : aiProvider === 'openrouter' ? 'meta-llama/llama-3-8b-instruct:free' : aiProvider === 'poe' ? 'Claude-3.5-Sonnet' : 'gpt-4o'} 
                                    value={aiModel} 
                                    onChange={e => setAiModel(e.target.value)} 
                                />
                            </div>

                            <button className="btn btn-primary" onClick={saveSettings} style={{ marginTop: 8 }}>
                                Save API Config
                            </button>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <div className="form-group">
                                <label className="form-label">Mode</label>
                                <select className="form-select" value={mode} onChange={e => setMode(e.target.value)}>
                                    <option value="keywords">Generate from Keywords</option>
                                    <option value="urls">Rewrite from target URLs</option>
                                </select>
                            </div>

                            {mode === 'keywords' ? (
                                <div className="form-group">
                                    <label className="form-label">Keywords (One per line)</label>
                                    <textarea 
                                        className="form-textarea" 
                                        placeholder="e.g.&#10;baccarat hitclub&#10;tai xiu hitclub" 
                                        style={{ height: 100 }}
                                        value={keywordsText}
                                        onChange={e => setKeywordsText(e.target.value)}
                                    />
                                </div>
                            ) : (
                                <div className="form-group">
                                    <label className="form-label">Target URLs (One per line)</label>
                                    <textarea 
                                        className="form-textarea" 
                                        placeholder="e.g.&#10;https://site.com/article-1/&#10;https://site.com/article-2/" 
                                        style={{ height: 100 }}
                                        value={urlsText}
                                        onChange={e => setUrlsText(e.target.value)}
                                    />
                                </div>
                            )}

                            {/* CUSTOM INSTRUCTIONS PROMPT FIELD */}
                            <div className="form-group">
                                <label className="form-label" style={{ color: '#38bdf8', fontWeight: 600 }}>
                                    💬 Yêu Cầu Bổ Sung / Custom Instructions Prompt
                                </label>
                                <textarea
                                    className="form-textarea"
                                    style={{ height: 80 }}
                                    placeholder="Ví dụ: Viết bằng Tiếng Việt, sử dụng văn phong sôi nổi, chèn bảng so sánh ưu nhược điểm và 3 câu hỏi FAQ ở cuối bài."
                                    value={customInstructions}
                                    onChange={e => setCustomInstructions(e.target.value)}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Articles Count to Generate</label>
                                <input 
                                    type="number" 
                                    className="form-input" 
                                    value={articlesCount} 
                                    onChange={e => setArticlesCount(parseInt(e.target.value) || 1)} 
                                    min={1}
                                />
                            </div>

                            <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={running}>
                                <Send size={14} /> {running ? 'Processing Pipeline...' : 'Generate & Publish Articles'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Right Column: Site Selection & Console Logging */}
                <div style={{ flex: 1.5, display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {/* Select Sites */}
                    {subTab !== 'settings' && (
                        <div style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid #334155', borderRadius: 16, padding: 20 }}>
                            <div style={{ fontWeight: 600, fontSize: 14, color: '#f8fafc', marginBottom: 12 }}>
                                Target Sites ({selectedSites.length} selected)
                            </div>
                            <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {sites.map(s => {
                                    const isOnline = s.status === 'ONLINE';
                                    return (
                                        <label key={s.domain} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: isOnline ? '#e2e8f0' : '#64748b' }}>
                                            <input 
                                                type="checkbox" 
                                                checked={selectedSites.includes(s.domain)} 
                                                onChange={() => toggleSite(s.domain)} 
                                                disabled={!isOnline && running}
                                            />
                                            <span>{s.domain}</span>
                                            <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} style={{ width: 6, height: 6 }} />
                                        </label>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Published Articles URLs List */}
                    {publishedUrls.length > 0 && (
                        <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 16, padding: 18 }}>
                            <div style={{ fontWeight: 600, fontSize: 13, color: '#10b981', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                                <ExternalLink size={14} /> 🔗 Danh Sách URL Bài Viết Đã Đăng ({publishedUrls.length})
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 150, overflowY: 'auto' }}>
                                {publishedUrls.map((url, idx) => (
                                    <a key={idx} href={url} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: '#38bdf8', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {idx + 1}. {url} ↗
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Console Log Log terminal */}
                    <div style={{ flex: 1, minHeight: 300, background: '#090d16', border: '1px solid #1e293b', borderRadius: 16, padding: 20, display: 'flex', flexDirection: 'column' }}>
                        <div style={{ fontWeight: 600, fontSize: 13, color: '#06b6d4', borderBottom: '1px solid #1e293b', paddingBottom: 8, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>AI Log Terminal</span>
                            {running && <span className="status-dot online animate-pulse" />}
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', fontFamily: 'monospace', fontSize: 12, color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 350 }}>
                            {logs.length === 0 ? (
                                <div style={{ color: '#475569', fontStyle: 'italic', textAlign: 'center', marginTop: 80 }}>
                                    Logs console inactive. Start generation to display progress.
                                </div>
                            ) : (
                                logs.map((log, index) => {
                                    let color = '#cbd5e1';
                                    if (log.type === 'success') color = '#10b981';
                                    if (log.type === 'warning') color = '#f59e0b';
                                    if (log.type === 'error') color = '#ef4444';
                                    
                                    return (
                                        <div key={index} style={{ borderLeft: `2px solid ${color}`, paddingLeft: 8 }}>
                                            <span style={{ color: '#64748b', fontSize: 11 }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                                            <span style={{ color, fontWeight: 'bold' }}>{log.step}</span>
                                            {log.details && <div style={{ color: '#94a3b8', fontSize: 11, marginLeft: 4 }}>{log.details}</div>}
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function App() {
    return (
        <ErrorBoundary>
            <MainApp />
        </ErrorBoundary>
    );
}

