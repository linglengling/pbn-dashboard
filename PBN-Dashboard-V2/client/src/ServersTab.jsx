import React, { useState } from 'react';
import {
    Server, Globe, RefreshCw, Plus, Zap, Check, Trash2, Edit3,
    Search, ExternalLink, Activity, HardDrive, Terminal, X,
    CheckCircle2, AlertTriangle, Shield, Clock, Copy, Cloud, Key
} from 'lucide-react';
import { getTranslation } from './i18n';
import ClientCronsModal from './ClientCronsModal';

const API_BASE = '';

const authFetch = (url, options = {}) => {
    const token = localStorage.getItem('pbn_token');
    const headers = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    return fetch(url, { ...options, headers });
};

export default function ServersTab({
    servers = [],
    refreshServers,
    refreshSites,
    refreshStats,
    addToast,
    setModal,
    lang = 'vi'
}) {
    const t = (key, vars) => getTranslation(key, lang, vars);

    const [searchQuery, setSearchQuery] = useState('');
    const [typeFilter, setTypeFilter] = useState('ALL');
    const [busyId, setBusyId] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);
    const [logOutput, setLogOutput] = useState(null);

    // Filter servers
    const filteredServers = servers.filter(srv => {
        const matchesQuery = srv.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            srv.host?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            srv.username?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesType = typeFilter === 'ALL' || srv.type === typeFilter;
        return matchesQuery && matchesType;
    });

    const totalSitesCount = servers.reduce((acc, cur) => acc + (parseInt(cur.sites_count) || 0), 0);
    const vpsCount = servers.filter(s => s.type === 'vps').length;
    const cpanelCount = servers.filter(s => s.type === 'cpanel').length;
    const onlineCount = servers.filter(s => s.status === 'ONLINE').length;

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        addToast(`Đã sao chép: ${text}`, 'success');
    };

    // Test single server
    const handleTestServer = async (srv) => {
        setBusyId(srv.id);
        try {
            const res = await authFetch(`${API_BASE}/api/servers/${srv.id}/test`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addToast(`Kết nối SSH tới [${srv.name}] thành công! (${data.sites_count || 0} WP sites)`, 'success');
                if (refreshServers) refreshServers();
            } else {
                addToast(`Lỗi kết nối [${srv.name}]: ${data.error || 'Thất bại'}`, 'error');
            }
        } catch (e) {
            addToast(`Lỗi gửi yêu cầu kiểm tra: ${e.message}`, 'error');
        }
        setBusyId(null);
    };

    // Scan single server
    const handleScanServer = async (srv) => {
        setBusyId(srv.id);
        try {
            const res = await authFetch(`${API_BASE}/api/servers/${srv.id}/scan`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã quét & đồng bộ ${data.count || 0} website từ [${srv.name}] vào Dashboard!`, 'success');
                if (refreshServers) refreshServers();
                if (refreshSites) refreshSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(`Lỗi quét [${srv.name}]: ${data.error}`, 'error');
            }
        } catch (e) {
            addToast(`Lỗi: ${e.message}`, 'error');
        }
        setBusyId(null);
    };

    // Deploy single server
    const handleDeployServer = async (srv) => {
        setBusyId(srv.id);
        try {
            const res = await authFetch(`${API_BASE}/api/servers/${srv.id}/deploy`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã upload pbn-manager.php vào ${data.count || 0} website trên [${srv.name}]!`, 'success');
                setLogOutput({
                    title: `Kết quả Upload mu-plugin [${srv.name}]`,
                    text: data.output || `Thành công upload tới ${data.count} website.`
                });
                if (refreshServers) refreshServers();
            } else {
                addToast(`Lỗi upload [${srv.name}]: ${data.error}`, 'error');
            }
        } catch (e) {
            addToast(`Lỗi: ${e.message}`, 'error');
        }
        setBusyId(null);
    };

    // Deploy all servers
    const handleDeployAll = async () => {
        if (!window.confirm("Bạn có chắc chắn muốn UPLOAD pbn-manager.php vào TẤT CẢ các website trên toàn bộ máy chủ?")) {
            return;
        }
        setActionLoading(true);
        addToast("Đang chạy batch upload mu-plugin trên tất cả các server...", "info");
        try {
            const res = await authFetch(`${API_BASE}/api/servers/deploy-all`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addToast("Hoàn tất upload pbn-manager.php tới toàn bộ các server!", "success");
                setLogOutput({
                    title: "Kết Quả Upload Toàn Bộ Máy Chủ",
                    text: data.output || "Đã hoàn thành."
                });
                if (refreshServers) refreshServers();
                if (refreshSites) refreshSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(`Lỗi: ${data.error}`, "error");
            }
        } catch (e) {
            addToast(`Lỗi kết nối: ${e.message}`, "error");
        }
        setActionLoading(false);
    };

    // Scan all servers
    const handleScanAll = async () => {
        setActionLoading(true);
        addToast("Đang quét và đồng bộ danh sách website từ tất cả máy chủ...", "info");
        try {
            const res = await authFetch(`${API_BASE}/api/servers/scan-all`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                addToast("Đã quét và đồng bộ xong toàn bộ website vào Database!", "success");
                setLogOutput({
                    title: "Kết Quả Quét Tất Cả Máy Chủ",
                    text: data.output || "Đã hoàn thành."
                });
                if (refreshServers) refreshServers();
                if (refreshSites) refreshSites();
                if (refreshStats) refreshStats();
            } else {
                addToast(`Lỗi: ${data.error}`, "error");
            }
        } catch (e) {
            addToast(`Lỗi kết nối: ${e.message}`, "error");
        }
        setActionLoading(false);
    };

    // Delete server
    const handleDeleteServer = async (srv) => {
        if (!window.confirm(t('confirmDeleteServer') + ` (${srv.name})`)) return;
        try {
            const res = await authFetch(`${API_BASE}/api/servers/${srv.id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                addToast(`Đã xóa server ${srv.name}`, 'success');
                if (refreshServers) refreshServers();
                if (refreshStats) refreshStats();
            } else {
                addToast(data.error || 'Xóa thất bại', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
    };

    // Open Add/Edit Modal
    const openServerModal = (serverToEdit = null) => {
        setModal({
            title: serverToEdit ? `Chỉnh Sửa Máy Chủ: ${serverToEdit.name}` : `+ Thêm Máy Chủ Mới`,
            content: (
                <ServerForm
                    server={serverToEdit}
                    onClose={() => setModal(null)}
                    addToast={addToast}
                    refreshServers={refreshServers}
                    lang={lang}
                />
            )
        });
    };

    // Open Cloudflare Config Modal
    const openCloudflareModal = () => {
        setModal({
            title: `Cấu Hình Cloudflare API & Phân Giải Domain`,
            content: (
                <CloudflareConfigModal
                    onClose={() => setModal(null)}
                    addToast={addToast}
                />
            )
        });
    };

    // Open Client Crons & Requests Management Modal
    const openCronsModal = () => {
        setModal({
            title: `⚙️ Quản Lý Request & Cron Task Máy Con`,
            content: (
                <ClientCronsModal
                    onClose={() => setModal(null)}
                    addToast={addToast}
                    refreshServers={refreshServers}
                />
            )
        });
    };

    return (
        <div className="tab-content" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Top Metric Cards */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 16
            }}>
                <div className="stat-card" style={{ borderLeft: '4px solid #6366f1' }}>
                    <div className="stat-label">{t('totalServers')}</div>
                    <div className="stat-value" style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Server size={22} /> {servers.length}
                    </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '4px solid #10b981' }}>
                    <div className="stat-label">{t('onlineServers')}</div>
                    <div className="stat-value" style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Activity size={22} /> {onlineCount} / {servers.length}
                    </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '4px solid #a855f7' }}>
                    <div className="stat-label">aaPanel Linux VPS</div>
                    <div className="stat-value" style={{ color: '#c084fc', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <HardDrive size={22} /> {vpsCount}
                    </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                    <div className="stat-label">cPanel Hosting</div>
                    <div className="stat-value" style={{ color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Shield size={22} /> {cpanelCount}
                    </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '4px solid #22d3ee' }}>
                    <div className="stat-label">{t('managedSitesAcrossServers')}</div>
                    <div className="stat-value" style={{ color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Globe size={22} /> {totalSitesCount}
                    </div>
                </div>
            </div>

            {/* Toolbar */}
            <div className="toolbar" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300, flexWrap: 'wrap' }}>
                    <div className="search-wrapper" style={{ flex: 1, minWidth: 220 }}>
                        <Search size={16} />
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Tìm kiếm máy chủ theo tên, host IP, username..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <select
                        className="form-select"
                        value={typeFilter}
                        onChange={e => setTypeFilter(e.target.value)}
                        style={{ width: 170 }}
                    >
                        <option value="ALL">Tất cả loại máy chủ</option>
                        <option value="vps">aaPanel Linux VPS</option>
                        <option value="cpanel">cPanel Hosting</option>
                    </select>
                </div>

                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button
                        className="btn btn-warning"
                        onClick={handleDeployAll}
                        disabled={actionLoading}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <Zap size={14} /> {actionLoading ? 'Đang triển khai...' : t('deployAllServers')}
                    </button>

                    <button
                        className="btn btn-success"
                        onClick={handleScanAll}
                        disabled={actionLoading}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <RefreshCw size={14} className={actionLoading ? 'animate-spin' : ''} /> {t('scanAllServers')}
                    </button>

                    <button
                        className="btn"
                        onClick={openCloudflareModal}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, background: 'rgba(249, 115, 22, 0.15)', border: '1px solid rgba(249, 115, 22, 0.5)', color: '#fb923c' }}
                        title="Quản lý Cloudflare API để tự động xác định máy chủ gốc"
                    >
                        <Cloud size={14} /> Cloudflare API
                    </button>

                    <button
                        className="btn"
                        onClick={openCronsModal}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.4)', color: '#38bdf8' }}
                        title="Quản lý Heartbeat, Crontasks & Khóa ký token của các máy con"
                    >
                        <Clock size={14} /> Quản Lý Cron & Request Máy Con
                    </button>

                    <button
                        className="btn btn-primary"
                        onClick={() => openServerModal(null)}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <Plus size={14} /> {t('addServer')}
                    </button>

                    <button
                        className="btn"
                        onClick={() => { if (refreshServers) refreshServers(); }}
                        title={t('refresh')}
                    >
                        <RefreshCw size={14} />
                    </button>
                </div>
            </div>

            {/* Server List Table */}
            <div className="table-container" style={{ background: 'var(--bg-glass)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: 220 }}>Tên & Host Máy Chủ</th>
                            <th style={{ width: 140 }}>Loại</th>
                            <th style={{ width: 160 }}>Thông Tin SSH</th>
                            <th style={{ width: 130 }}>Trạng Thái</th>
                            <th style={{ width: 150 }}>Số Site WP</th>
                            <th style={{ width: 160 }}>Kiểm Tra Gần Nhất</th>
                            <th style={{ textAlign: 'right' }}>Thao Tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredServers.length === 0 ? (
                            <tr>
                                <td colSpan={7} style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                                    Không tìm thấy máy chủ nào phù hợp.
                                </td>
                            </tr>
                        ) : (
                            filteredServers.map(srv => {
                                const isBusy = busyId === srv.id;
                                const isVps = srv.type === 'vps';
                                return (
                                    <tr key={srv.id}>
                                        {/* Name & Host */}
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                <div style={{ fontWeight: 700, fontSize: 14, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
                                                    <Server size={15} color={isVps ? '#818cf8' : '#fbbf24'} />
                                                    {srv.name}
                                                </div>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
                                                    <code>{srv.host}</code>
                                                    <button
                                                        onClick={() => copyToClipboard(srv.host)}
                                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: 2 }}
                                                        title="Sao chép Host IP"
                                                    >
                                                        <Copy size={11} />
                                                    </button>
                                                </div>
                                            </div>
                                        </td>

                                        {/* Type */}
                                        <td>
                                            <span style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: 4,
                                                padding: '3px 8px',
                                                borderRadius: 6,
                                                fontSize: 12,
                                                fontWeight: 600,
                                                background: isVps ? 'rgba(99, 102, 241, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                                color: isVps ? '#818cf8' : '#fbbf24',
                                                border: `1px solid ${isVps ? 'rgba(99, 102, 241, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                                            }}>
                                                {isVps ? <HardDrive size={11} /> : <Shield size={11} />}
                                                {isVps ? 'aaPanel VPS' : 'cPanel Hosting'}
                                            </span>
                                        </td>

                                        {/* SSH Credentials */}
                                        <td>
                                            <div style={{ fontSize: 13, color: '#cbd5e1' }}>
                                                <code>{srv.username}</code> : port <code>{srv.port || 22}</code>
                                            </div>
                                        </td>

                                        {/* Status */}
                                        <td>
                                            {srv.status === 'ONLINE' ? (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    gap: 5,
                                                    padding: '3px 8px',
                                                    borderRadius: 6,
                                                    fontSize: 12,
                                                    fontWeight: 600,
                                                    background: 'rgba(16, 185, 129, 0.15)',
                                                    color: '#34d399',
                                                    border: '1px solid rgba(16, 185, 129, 0.3)'
                                                }}>
                                                    <span className="status-dot online" style={{ width: 6, height: 6 }} />
                                                    Hoạt động
                                                </span>
                                            ) : (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    gap: 5,
                                                    padding: '3px 8px',
                                                    borderRadius: 6,
                                                    fontSize: 12,
                                                    fontWeight: 600,
                                                    background: 'rgba(239, 68, 68, 0.15)',
                                                    color: '#f87171',
                                                    border: '1px solid rgba(239, 68, 68, 0.3)'
                                                }} title={srv.error_message || 'Lỗi kết nối SSH'}>
                                                    <span className="status-dot offline" style={{ width: 6, height: 6 }} />
                                                    Lỗi
                                                </span>
                                            )}
                                        </td>

                                        {/* Sites Count */}
                                        <td>
                                            <span style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: 6,
                                                padding: '4px 10px',
                                                borderRadius: 8,
                                                fontSize: 13,
                                                fontWeight: 700,
                                                background: 'rgba(56, 189, 248, 0.1)',
                                                color: '#38bdf8',
                                                border: '1px solid rgba(56, 189, 248, 0.25)'
                                            }}>
                                                <Globe size={13} /> {srv.sites_count || 0} sites
                                            </span>
                                        </td>

                                        {/* Last Checked */}
                                        <td style={{ fontSize: 12, color: '#94a3b8' }}>
                                            {srv.last_checked ? new Date(srv.last_checked).toLocaleString() : 'Chưa kiểm tra'}
                                        </td>

                                        {/* Actions */}
                                        <td style={{ textAlign: 'right' }}>
                                            <div style={{ display: 'inline-flex', gap: 6, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                                                <button
                                                    className="btn btn-sm"
                                                    onClick={() => handleTestServer(srv)}
                                                    disabled={isBusy}
                                                    title="Kiểm tra kết nối SSH"
                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                                >
                                                    <Activity size={12} color="#38bdf8" />
                                                    {isBusy ? '...' : t('testConnection')}
                                                </button>

                                                <button
                                                    className="btn btn-sm btn-success"
                                                    onClick={() => handleScanServer(srv)}
                                                    disabled={isBusy}
                                                    title="Quét và đồng bộ website WP"
                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                                >
                                                    <Globe size={12} />
                                                    {t('scanSites')}
                                                </button>

                                                <button
                                                    className="btn btn-sm btn-warning"
                                                    onClick={() => handleDeployServer(srv)}
                                                    disabled={isBusy}
                                                    title="Upload pbn-manager.php vào thư mục mu-plugins"
                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                                >
                                                    <Zap size={12} />
                                                    {t('deployMuPlugin')}
                                                </button>

                                                <button
                                                    className="btn btn-sm"
                                                    onClick={() => openServerModal(srv)}
                                                    title={t('editServer')}
                                                >
                                                    <Edit3 size={12} />
                                                </button>

                                                <button
                                                    className="btn btn-sm btn-danger"
                                                    onClick={() => handleDeleteServer(srv)}
                                                    title={t('deleteServer')}
                                                >
                                                    <Trash2 size={12} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>

            {/* Terminal Log Modal */}
            {logOutput && (
                <div className="modal-overlay" onClick={() => setLogOutput(null)}>
                    <div className="modal" style={{ maxWidth: 800 }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Terminal size={18} color="#22d3ee" /> {logOutput.title}
                            </div>
                            <button className="btn btn-sm" onClick={() => setLogOutput(null)}><X size={14} /></button>
                        </div>
                        <div style={{
                            background: '#090d16',
                            border: '1px solid #1e293b',
                            borderRadius: 10,
                            padding: 16,
                            fontFamily: 'monospace',
                            fontSize: 13,
                            color: '#a5f3fc',
                            maxHeight: 450,
                            overflowY: 'auto',
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.6
                        }}>
                            {logOutput.text}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                            <button className="btn btn-primary" onClick={() => setLogOutput(null)}>
                                Đóng
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Subcomponent: Add/Edit Server Form
function ServerForm({ server, onClose, addToast, refreshServers, lang }) {
    const t = (key, vars) => getTranslation(key, lang, vars);
    const isEdit = !!server;

    const [name, setName] = useState(server?.name || '');
    const [type, setType] = useState(server?.type || 'vps');
    const [host, setHost] = useState(server?.host || '');
    const [port, setPort] = useState(server?.port || 22);
    const [username, setUsername] = useState(server?.username || (type === 'vps' ? 'root' : ''));
    const [password, setPassword] = useState(server?.password || '');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name.trim() || !host.trim() || !username.trim() || (!isEdit && !password.trim())) {
            return addToast('Vui lòng điền đầy đủ thông tin máy chủ', 'error');
        }

        setLoading(true);
        try {
            const url = isEdit ? `${API_BASE}/api/servers/${server.id}` : `${API_BASE}/api/servers`;
            const method = isEdit ? 'PUT' : 'POST';
            const res = await authFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name.trim(),
                    type,
                    host: host.trim(),
                    port: parseInt(port) || 22,
                    username: username.trim(),
                    password: password || undefined
                })
            });
            const data = await res.json();
            if (data.success) {
                addToast(isEdit ? 'Cập nhật server thành công!' : 'Thêm server thành công!', 'success');
                if (refreshServers) refreshServers();
                onClose();
            } else {
                addToast(data.error || 'Thao tác thất bại', 'error');
            }
        } catch (err) {
            addToast('Lỗi kết nối máy chủ', 'error');
        }
        setLoading(false);
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{t('serverName')}</label>
                <input
                    type="text"
                    className="form-input"
                    placeholder="Ví dụ: VPS aaPanel 1, cPanel US 2..."
                    value={name}
                    onChange={e => setName(e.target.value)}
                    required
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">{t('serverType')}</label>
                    <select
                        className="form-select"
                        value={type}
                        onChange={e => {
                            const newType = e.target.value;
                            setType(newType);
                            if (newType === 'vps' && !username) setUsername('root');
                        }}
                    >
                        <option value="vps">aaPanel Linux VPS (root)</option>
                        <option value="cpanel">cPanel Shared Hosting</option>
                    </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">{t('serverPort')}</label>
                    <input
                        type="number"
                        className="form-input"
                        placeholder="22"
                        value={port}
                        onChange={e => setPort(e.target.value)}
                    />
                </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{t('serverHost')}</label>
                <input
                    type="text"
                    className="form-input"
                    placeholder="194.233.83.83 hoặc domain.com"
                    value={host}
                    onChange={e => setHost(e.target.value)}
                    required
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">{t('serverUsername')}</label>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="root hoặc cpanel user"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">{t('serverPassword')}</label>
                    <input
                        type="password"
                        className="form-input"
                        placeholder={isEdit ? 'Để trống nếu không đổi' : 'Nhập mật khẩu SSH'}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        required={!isEdit}
                    />
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
                <button type="button" className="btn" onClick={onClose} disabled={loading}>
                    Hủy
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Đang lưu...' : (isEdit ? 'Lưu Thay Đổi' : 'Thêm Máy Chủ')}
                </button>
            </div>
        </form>
    );
}

// ============================================================
// CLOUDFLARE API CONFIG & DOMAIN RESOLVER MODAL
// ============================================================
function CloudflareConfigModal({ onClose, addToast }) {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [name, setName] = useState('');
    const [authType, setAuthType] = useState('token');
    const [token, setToken] = useState('');
    const [email, setEmail] = useState('');
    const [key, setKey] = useState('');
    const [saving, setSaving] = useState(false);
    const [testingId, setTestingId] = useState(null);
    const [testResults, setTestResults] = useState({});

    // Domain resolver test
    const [testDomain, setTestDomain] = useState('');
    const [resolving, setResolving] = useState(false);
    const [resolveResult, setResolveResult] = useState(null);

    const loadAccounts = async () => {
        setLoading(true);
        try {
            const res = await authFetch(`${API_BASE}/api/cloudflare/accounts`);
            const data = await res.json();
            if (data.success) {
                setAccounts(data.data || []);
            }
        } catch (e) {
            addToast('Lỗi tải danh sách Cloudflare', 'error');
        }
        setLoading(false);
    };

    React.useEffect(() => {
        loadAccounts();
    }, []);

    const handleSaveAccounts = async (accList) => {
        setSaving(true);
        try {
            const res = await authFetch(`${API_BASE}/api/cloudflare/accounts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ accounts: accList })
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message || 'Đã lưu tài khoản Cloudflare', 'success');
                loadAccounts();
            } else {
                addToast(data.error || 'Lỗi lưu tài khoản', 'error');
            }
        } catch (e) {
            addToast(e.message, 'error');
        }
        setSaving(false);
    };

    const handleAddAccount = (e) => {
        e.preventDefault();
        if (!name.trim()) {
            addToast('Vui lòng nhập tên gợi nhớ tài khoản', 'error');
            return;
        }
        if (authType === 'token' && !token.trim()) {
            addToast('Vui lòng nhập API Token', 'error');
            return;
        }
        if (authType === 'key' && (!email.trim() || !key.trim())) {
            addToast('Vui lòng nhập Email và Global API Key', 'error');
            return;
        }

        const newAcc = {
            id: `cf_${Date.now()}`,
            name: name.trim(),
            token: authType === 'token' ? token.trim() : null,
            email: authType === 'key' ? email.trim() : null,
            key: authType === 'key' ? key.trim() : null
        };

        const updated = [...accounts, newAcc];
        setAccounts(updated);
        setName('');
        setToken('');
        setEmail('');
        setKey('');
        handleSaveAccounts(updated);
    };

    const handleDeleteAccount = (accId) => {
        if (!window.confirm('Bạn có chắc muốn xóa tài khoản Cloudflare này?')) return;
        const updated = accounts.filter(a => a.id !== accId);
        setAccounts(updated);
        handleSaveAccounts(updated);
    };

    const handleTestAccount = async (acc) => {
        setTestingId(acc.id);
        try {
            const res = await authFetch(`${API_BASE}/api/cloudflare/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    token: acc.token,
                    email: acc.email,
                    key: acc.key
                })
            });
            const data = await res.json();
            setTestResults(prev => ({ ...prev, [acc.id]: data }));
            if (data.success) {
                addToast(`[${acc.name}] Kết nối CF thành công! Tìm thấy ${data.zone_count || 0} Zone`, 'success');
            } else {
                addToast(`[${acc.name}] Kiểm tra thất bại: ${data.error || 'Token không hợp lệ'}`, 'error');
            }
        } catch (e) {
            addToast(e.message, 'error');
        }
        setTestingId(null);
    };

    const handleResolveDomain = async (e) => {
        e.preventDefault();
        if (!testDomain.trim()) return;
        setResolving(true);
        setResolveResult(null);
        try {
            const res = await authFetch(`${API_BASE}/api/cloudflare/resolve/${encodeURIComponent(testDomain.trim())}`);
            const data = await res.json();
            setResolveResult(data.data || data);
        } catch (e) {
            setResolveResult({ found: false, reason: e.message });
        }
        setResolving(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxHeight: '80vh', overflowY: 'auto', paddingRight: 4 }}>
            <div style={{ background: 'rgba(249, 115, 22, 0.1)', border: '1px solid rgba(249, 115, 22, 0.3)', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#fed7aa', lineHeight: 1.5 }}>
                <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, color: '#fb923c' }}>
                    <Cloud size={16} /> Cloudflare DNS Origin IP Resolver
                </div>
                Khi cấu hình Cloudflare API, hệ thống sẽ <strong>ưu tiên truy vấn bản ghi DNS A gốc</strong> trên Cloudflare để xác định chính xác domain đang nằm trên VPS hay cPanel nào (kể cả khi domain đã bật proxy đám mây cam).
            </div>

            {/* List of configured accounts */}
            <div>
                <h4 style={{ margin: '0 0 10px 0', fontSize: 14, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Key size={15} style={{ color: '#818cf8' }} /> Danh Sách Tài Khoản Cloudflare ({accounts.length})
                </h4>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>Đang tải danh sách...</div>
                ) : accounts.length === 0 ? (
                    <div style={{ padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, border: '1px dashed var(--border-color)' }}>
                        Chưa có tài khoản Cloudflare nào được thêm. Hãy thêm tài khoản bên dưới để tự động tra cứu Server!
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {accounts.map(acc => {
                            const isTesting = testingId === acc.id;
                            const result = testResults[acc.id];
                            return (
                                <div key={acc.id} style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '12px 16px',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    borderRadius: 8,
                                    border: '1px solid var(--border-color)',
                                    flexWrap: 'wrap',
                                    gap: 12
                                }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        <div style={{ fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span>{acc.name}</span>
                                            {acc.token ? (
                                                <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.4)' }}>API Token</span>
                                            ) : (
                                                <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: 'rgba(234, 179, 8, 0.2)', color: '#fde047', border: '1px solid rgba(234, 179, 8, 0.4)' }}>Global Key</span>
                                            )}
                                        </div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                            {acc.token ? `Token: ${acc.token_masked || '••••••••'}` : `${acc.email} | Key: ${acc.key_masked || '••••••••'}`}
                                        </div>
                                        {result && (
                                            <div style={{ fontSize: 12, marginTop: 4, color: result.success ? '#34d399' : '#f87171', display: 'flex', alignItems: 'center', gap: 4 }}>
                                                {result.success ? `✓ Hợp lệ (${result.zone_count || 0} zones)` : `✗ Lỗi: ${result.error}`}
                                            </div>
                                        )}
                                    </div>

                                    <div style={{ display: 'flex', gap: 8 }}>
                                        <button
                                            type="button"
                                            className="btn btn-sm"
                                            onClick={() => handleTestAccount(acc)}
                                            disabled={isTesting}
                                            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12 }}
                                        >
                                            <RefreshCw size={12} className={isTesting ? 'animate-spin' : ''} />
                                            {isTesting ? 'Đang kiểm tra...' : 'Kiểm Tra'}
                                        </button>
                                        <button
                                            type="button"
                                            className="btn btn-sm btn-danger"
                                            onClick={() => handleDeleteAccount(acc.id)}
                                            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12 }}
                                        >
                                            <Trash2 size={12} /> Xóa
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Add Account Form */}
            <form onSubmit={handleAddAccount} style={{ background: 'rgba(255,255,255,0.02)', padding: 16, borderRadius: 8, border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h4 style={{ margin: 0, fontSize: 14, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Plus size={15} style={{ color: '#38bdf8' }} /> Thêm Tài Khoản Cloudflare Mới
                </h4>

                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" style={{ fontSize: 12 }}>Tên Gợi Nhớ</label>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Ví dụ: Cloudflare Công Ty, CF PBN..."
                        value={name}
                        onChange={e => setName(e.target.value)}
                        required
                    />
                </div>

                <div style={{ display: 'flex', gap: 16, fontSize: 13, alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                        <input
                            type="radio"
                            name="authType"
                            checked={authType === 'token'}
                            onChange={() => setAuthType('token')}
                        />
                        <span>API Token <strong style={{ color: '#34d399', fontSize: 11 }}>(Khuyên dùng)</strong></span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                        <input
                            type="radio"
                            name="authType"
                            checked={authType === 'key'}
                            onChange={() => setAuthType('key')}
                        />
                        <span>Global API Key + Email</span>
                    </label>
                </div>

                {authType === 'token' ? (
                    <div className="form-group" style={{ marginBottom: 0 }}>
                        <label className="form-label" style={{ fontSize: 12 }}>API Token (Quyền Zone:Read, DNS:Read)</label>
                        <input
                            type="password"
                            className="form-input"
                            placeholder="Nhập Cloudflare API Token..."
                            value={token}
                            onChange={e => setToken(e.target.value)}
                            required={authType === 'token'}
                        />
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label" style={{ fontSize: 12 }}>Email Cloudflare</label>
                            <input
                                type="email"
                                className="form-input"
                                placeholder="admin@domain.com"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                required={authType === 'key'}
                            />
                        </div>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label" style={{ fontSize: 12 }}>Global API Key</label>
                            <input
                                type="password"
                                className="form-input"
                                placeholder="Nhập Global API Key..."
                                value={key}
                                onChange={e => setKey(e.target.value)}
                                required={authType === 'key'}
                            />
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                    <button type="submit" className="btn btn-primary" disabled={saving} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                        <Plus size={14} /> {saving ? 'Đang lưu...' : 'Thêm Tài Khoản'}
                    </button>
                </div>
            </form>

            {/* Test Resolver */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: 16, borderRadius: 8, border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h4 style={{ margin: 0, fontSize: 14, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Search size={15} style={{ color: '#fb923c' }} /> Kiểm Tra Phân Giải Máy Chủ Gốc (Test Domain Lookup)
                </h4>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Nhập tên domain để kiểm tra xem Cloudflare API có đọc được Origin IP và khớp với máy chủ nào trong PBN Dashboard không.
                </div>

                <form onSubmit={handleResolveDomain} style={{ display: 'flex', gap: 10 }}>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Ví dụ: vietscore.app hoặc https://domain.com"
                        value={testDomain}
                        onChange={e => setTestDomain(e.target.value)}
                        style={{ flex: 1 }}
                    />
                    <button type="submit" className="btn btn-warning" disabled={resolving} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap' }}>
                        <Search size={14} /> {resolving ? 'Đang kiểm tra...' : 'Tra Cứu'}
                    </button>
                </form>

                {resolveResult && (
                    <div style={{
                        padding: 12,
                        borderRadius: 6,
                        background: resolveResult.found ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        border: `1px solid ${resolveResult.found ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                        fontSize: 13
                    }}>
                        {resolveResult.found ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                <div style={{ color: '#34d399', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
                                    ✓ Đã tìm thấy trên Cloudflare ({resolveResult.account_name})!
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8, marginTop: 4 }}>
                                    <div><strong>Domain:</strong> {resolveResult.domain}</div>
                                    <div><strong>Zone CF:</strong> {resolveResult.zone_name}</div>
                                    <div><strong>IP Gốc (Origin):</strong> <code style={{ color: '#38bdf8' }}>{resolveResult.origin_ip}</code></div>
                                    <div><strong>Proxy Đám Mây:</strong> {resolveResult.proxied ? '🟠 Có (Proxied)' : '⚪ DNS Only'}</div>
                                    <div style={{ gridColumn: '1 / -1', background: 'rgba(0,0,0,0.2)', padding: '6px 10px', borderRadius: 4 }}>
                                        <strong>Máy chủ khớp trong PBN:</strong>{' '}
                                        {resolveResult.server_id ? (
                                            <span style={{ color: '#34d399', fontWeight: 600 }}>
                                                {resolveResult.server_name} ({resolveResult.server_host})
                                            </span>
                                        ) : (
                                            <span style={{ color: '#fbbf24' }}>
                                                {resolveResult.origin_ip} (Chưa được thêm vào danh sách Máy Chủ)
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ color: '#f87171' }}>
                                ✗ {resolveResult.reason || 'Không tìm thấy domain này trong các tài khoản Cloudflare đã cấu hình.'}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" className="btn" onClick={onClose}>
                    Đóng
                </button>
            </div>
        </div>
    );
}
