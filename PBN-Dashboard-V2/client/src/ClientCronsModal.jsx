import React, { useState, useEffect } from 'react';
import {
    Activity, Clock, Terminal, Server, Shield, RefreshCw,
    Copy, Check, Play, AlertCircle, CheckCircle2, ChevronRight,
    Sliders, Settings, Zap, Globe, FileText
} from 'lucide-react';

const API_BASE = '';

const authFetch = (url, options = {}) => {
    const token = localStorage.getItem('pbn_token');
    const headers = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    return fetch(url, { ...options, headers });
};

export default function ClientCronsModal({ onClose, addToast, refreshServers }) {
    const [subTab, setSubTab] = useState('heartbeats'); // 'heartbeats' | 'crons' | 'generator'
    const [loading, setLoading] = useState(true);
    const [overviewData, setOverviewData] = useState({
        servers: [],
        recent_cron_logs: [],
        recent_pings: [],
        settings: {
            SECRET_SALT: '',
            HEARTBEAT_INTERVAL: '300',
            CRON_SCHEDULE_EXPR: '0 3 */3 * *',
            AUTO_AUDIT_ENABLED: '1',
            AUTO_AUDIT_NOTIFY_LOGIN: '1',
            LAST_AUDIT_RUN: '',
            LAST_AUDIT_REPORT: null
        }
    });

    // Form settings state
    const [formSettings, setFormSettings] = useState({
        SECRET_SALT: '',
        HEARTBEAT_INTERVAL: '300',
        CRON_SCHEDULE_EXPR: '0 3 */3 * *',
        AUTO_AUDIT_ENABLED: '1',
        AUTO_AUDIT_NOTIFY_LOGIN: '1'
    });
    const [savingSettings, setSavingSettings] = useState(false);
    const [runningSystemAudit, setRunningSystemAudit] = useState(false);
    const [runningServerId, setRunningServerId] = useState(null);
    const [terminalOutput, setTerminalOutput] = useState(null);
    const [copiedKey, setCopiedKey] = useState('');

    // Fetch overview data
    const fetchOverview = async () => {
        setLoading(true);
        try {
            const res = await authFetch(`${API_BASE}/api/vps/crons-overview`);
            const data = await res.json();
            if (data.success) {
                setOverviewData(data);
                setFormSettings(data.settings);
            } else {
                addToast(data.detail || 'Không thể tải dữ liệu máy con & crons', 'error');
            }
        } catch (e) {
            addToast(`Lỗi kết nối: ${e.message}`, 'error');
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchOverview();
    }, []);

    // Save Settings
    const handleSaveSettings = async (e) => {
        if (e) e.preventDefault();
        setSavingSettings(true);
        try {
            const res = await authFetch(`${API_BASE}/api/vps/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formSettings)
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message || 'Đã lưu cài đặt thành công!', 'success');
                fetchOverview();
            } else {
                addToast(data.detail || 'Lỗi khi lưu cài đặt', 'error');
            }
        } catch (e) {
            addToast(`Lỗi: ${e.message}`, 'error');
        }
        setSavingSettings(false);
    };

    // Remote Trigger Cron
    const handleTriggerRemoteCron = async (serverId, serverName) => {
        setRunningServerId(serverId);
        setTerminalOutput(`[SSH] Đang kết nối tới máy chủ ${serverName} và kích hoạt script /www/wwwroot/pbn-tool/auto_scan_sites.py...\n`);
        try {
            const res = await authFetch(`${API_BASE}/api/vps/trigger-remote-cron`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ server_id: serverId })
            });
            const data = await res.json();
            if (data.success) {
                setTerminalOutput(prev => prev + `[THÀNH CÔNG] Lệnh đã hoàn tất:\n\n` + data.output);
                addToast(`Kích hoạt chạy quét trên máy chủ ${serverName} thành công!`, 'success');
                fetchOverview();
                if (refreshServers) refreshServers();
            } else {
                setTerminalOutput(prev => prev + `[LỖI] ${data.error || 'Thực thi thất bại'}\n`);
                addToast(`Lỗi chạy cron trên ${serverName}: ${data.error}`, 'error');
            }
        } catch (e) {
            setTerminalOutput(prev => prev + `[LỖI KẾT NỐI] ${e.message}\n`);
            addToast(`Lỗi kết nối: ${e.message}`, 'error');
        }
        setRunningServerId(null);
    };

    // System Error Scan Cron Trigger
    const handleTriggerSystemAudit = async () => {
        setRunningSystemAudit(true);
        addToast('Đang kích hoạt quét toàn bộ website trong hệ thống...', 'info');
        try {
            const res = await authFetch(`${API_BASE}/api/audit/run-system-audit`, {
                method: 'POST'
            });
            const data = await res.json();
            if (data.success) {
                addToast(data.message || 'Đã kích hoạt quét hệ thống thành công!', 'success');
                setTimeout(fetchOverview, 4000);
            } else {
                addToast(data.detail || 'Lỗi khi kích hoạt quét', 'error');
            }
        } catch (e) {
            addToast(`Lỗi: ${e.message}`, 'error');
        }
        setRunningSystemAudit(false);
    };

    const copyText = (text, key) => {
        navigator.clipboard.writeText(text);
        setCopiedKey(key);
        addToast('Đã sao chép vào bộ nhớ tạm!', 'success');
        setTimeout(() => setCopiedKey(''), 2500);
    };

    return (
        <div style={{ maxHeight: '80vh', overflowY: 'auto', padding: '4px 2px' }}>
            {/* Sub-tabs header */}
            <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #334155', paddingBottom: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                <button
                    className={`btn btn-sm ${subTab === 'heartbeats' ? 'btn-primary' : ''}`}
                    onClick={() => setSubTab('heartbeats')}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                >
                    <Activity size={14} /> Giám Sát Heartbeat Máy Con
                </button>
                <button
                    className={`btn btn-sm ${subTab === 'crons' ? 'btn-primary' : ''}`}
                    onClick={() => setSubTab('crons')}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                >
                    <Clock size={14} /> Quản Lý Cron Task Máy Con
                </button>
                <button
                    className={`btn btn-sm ${subTab === 'generator' ? 'btn-primary' : ''}`}
                    onClick={() => setSubTab('generator')}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                >
                    <Terminal size={14} /> Lệnh Cron & Hướng Dẫn Cài Đặt
                </button>
                <button
                    className="btn btn-sm"
                    onClick={fetchOverview}
                    disabled={loading}
                    style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                    title="Làm mới"
                >
                    <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            {loading ? (
                <div style={{ padding: '40px 0', textAlign: 'center', color: '#94a3b8' }}>
                    <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
                    <p>Đang tải thông số máy con & crontasks...</p>
                </div>
            ) : (
                <>
                    {/* TAB 1: HEARTBEAT & INCOMING SIGNALS */}
                    {subTab === 'heartbeats' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            {/* Settings Box */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                                    <Settings size={16} style={{ color: '#38bdf8' }} />
                                    <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                        Cấu Hình Tần Suất Gửi Request & Khóa Bảo Mật
                                    </h4>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6, fontWeight: 500 }}>
                                            Chu Kỳ Heartbeat Plugin (Giây):
                                        </label>
                                        <select
                                            className="form-select"
                                            value={formSettings.HEARTBEAT_INTERVAL}
                                            onChange={e => setFormSettings({ ...formSettings, HEARTBEAT_INTERVAL: e.target.value })}
                                            style={{ width: '100%', fontSize: 13 }}
                                        >
                                            <option value="300">5 phút (300s) - Mặc định, theo dõi sát</option>
                                            <option value="600">10 phút (600s) - Cân bằng</option>
                                            <option value="900">15 phút (900s) - Tiết kiệm tài nguyên</option>
                                            <option value="1800">30 phút (1800s) - Hệ thống trên 1.000 site</option>
                                        </select>
                                        <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
                                            Tần suất các site WordPress gửi ping báo trạng thái & outbound link về Dashboard.
                                        </span>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6, fontWeight: 500 }}>
                                            Khóa Bí Mật Ký Token (Secret Salt Key):
                                        </label>
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <input
                                                type="text"
                                                className="form-control"
                                                value={formSettings.SECRET_SALT}
                                                onChange={e => setFormSettings({ ...formSettings, SECRET_SALT: e.target.value })}
                                                style={{ fontSize: 13, flex: 1, fontFamily: 'monospace' }}
                                            />
                                            <button
                                                className="btn btn-sm"
                                                onClick={() => copyText(formSettings.SECRET_SALT, 'salt')}
                                                title="Sao chép Salt Key"
                                                type="button"
                                            >
                                                {copiedKey === 'salt' ? <Check size={13} style={{ color: '#10b981' }} /> : <Copy size={13} />}
                                            </button>
                                        </div>
                                        <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
                                            Dùng để ký mã hóa token xác thực giữa VPS con và Dashboard.
                                        </span>
                                    </div>
                                </div>

                                <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
                                    <button
                                        className="btn btn-primary btn-sm"
                                        onClick={handleSaveSettings}
                                        disabled={savingSettings}
                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                                    >
                                        <Check size={13} /> {savingSettings ? 'Đang lưu...' : 'Lưu Cấu Hình Request'}
                                    </button>
                                </div>
                            </div>

                            {/* Recent Pings Table */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Activity size={16} style={{ color: '#10b981' }} />
                                        <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                            Danh Sách Request & Pings Nhận Được Gần Nhất (Top 15)
                                        </h4>
                                    </div>
                                    <span style={{ fontSize: 12, color: '#94a3b8' }}>
                                        Tổng {overviewData.recent_pings?.length || 0} pings
                                    </span>
                                </div>

                                <div className="table-container" style={{ maxHeight: 320, overflowY: 'auto' }}>
                                    <table className="data-table" style={{ fontSize: 12 }}>
                                        <thead>
                                            <tr>
                                                <th>Domain Website</th>
                                                <th>IP Máy Chủ Gửi Về</th>
                                                <th>Trạng Thái</th>
                                                <th>Link Out Trang Chủ</th>
                                                <th>Thời Gian Gửi Gần Nhất</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {overviewData.recent_pings?.length === 0 ? (
                                                <tr>
                                                    <td colSpan={5} style={{ textAlign: 'center', color: '#94a3b8', padding: 20 }}>
                                                        Chưa nhận được ping nào gần đây.
                                                    </td>
                                                </tr>
                                            ) : (
                                                overviewData.recent_pings?.map((p, i) => (
                                                    <tr key={i}>
                                                        <td style={{ fontWeight: 600, color: '#38bdf8' }}>{p.domain}</td>
                                                        <td><code>{p.ip || p.server_host || 'N/A'}</code></td>
                                                        <td>
                                                            <span className={`site-status-badge ${p.status === 'ONLINE' ? 'online' : 'offline'}`} style={{ fontSize: 11, padding: '2px 8px' }}>
                                                                {p.status}
                                                            </span>
                                                        </td>
                                                        <td style={{ color: '#22d3ee', fontWeight: 600 }}>
                                                            {p.total_homepage_links || 0} link
                                                        </td>
                                                        <td style={{ color: '#94a3b8' }}>{p.last_seen || 'Chưa rõ'}</td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB 2: CRON TASK QUẢN LÝ MÁY CON */}
                    {subTab === 'crons' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            {/* System Health Audit Cron Settings & Report */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Shield size={18} style={{ color: '#38bdf8' }} />
                                        <div>
                                            <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                                Lịch Quét Tự Động & Báo Cáo Website Lỗi (Cron 3 Ngày/Lần)
                                            </h4>
                                            <span style={{ fontSize: 11, color: '#94a3b8' }}>
                                                Tự động rà soát toàn bộ website trong hệ thống để phát hiện các lỗi HTTP 500/502, PHP Fatal, Lỗi DB, SSL, NoIndex...
                                            </span>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <button
                                            className="btn btn-sm btn-primary"
                                            onClick={handleTriggerSystemAudit}
                                            disabled={runningSystemAudit}
                                            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600 }}
                                        >
                                            <Play size={12} className={runningSystemAudit ? 'animate-spin' : ''} />
                                            {runningSystemAudit ? 'Đang kích hoạt...' : '⚡ Quét Toàn Bộ Website Ngay'}
                                        </button>
                                    </div>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14, background: 'rgba(15, 23, 42, 0.6)', padding: 14, borderRadius: 8, border: '1px solid #1e293b' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6, fontWeight: 500 }}>
                                            Chu Kỳ Quét Hệ Thống:
                                        </label>
                                        <select
                                            className="form-select"
                                            value={formSettings.CRON_SCHEDULE_EXPR}
                                            onChange={e => setFormSettings({ ...formSettings, CRON_SCHEDULE_EXPR: e.target.value })}
                                            style={{ width: '100%', fontSize: 13 }}
                                        >
                                            <option value="0 3 */3 * *">3 ngày 1 lần vào 03:00 sáng (0 3 */3 * *) - Khuyến nghị</option>
                                            <option value="0 3 * * *">Mỗi ngày 1 lần vào 03:00 sáng (0 3 * * *)</option>
                                            <option value="0 3 * * 0">Mỗi tuần 1 lần vào Chủ Nhật lúc 03:00 (0 3 * * 0)</option>
                                            <option value="0 */6 * * *">Mỗi 6 tiếng một lần (0 */6 * * *)</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6, fontWeight: 500 }}>
                                            Tùy Chọn Thông Báo Khi Đăng Nhập:
                                        </label>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#f8fafc', cursor: 'pointer' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={formSettings.AUTO_AUDIT_ENABLED === '1'}
                                                    onChange={e => setFormSettings({ ...formSettings, AUTO_AUDIT_ENABLED: e.target.checked ? '1' : '0' })}
                                                />
                                                <span>Bật lịch chạy cron tự động</span>
                                            </label>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#f8fafc', cursor: 'pointer' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={formSettings.AUTO_AUDIT_NOTIFY_LOGIN === '1'}
                                                    onChange={e => setFormSettings({ ...formSettings, AUTO_AUDIT_NOTIFY_LOGIN: e.target.checked ? '1' : '0' })}
                                                />
                                                <span>Hiện bảng báo cáo lỗi khi người dùng đăng nhập</span>
                                            </label>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                                        <button
                                            className="btn btn-sm btn-primary"
                                            onClick={handleSaveSettings}
                                            disabled={savingSettings}
                                            style={{ width: '100%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6, height: 38 }}
                                        >
                                            <Check size={14} /> {savingSettings ? 'Đang lưu...' : 'Lưu Cài Đặt Cron'}
                                        </button>
                                    </div>
                                </div>

                                {/* Last Audit Report Summary */}
                                {overviewData.settings?.LAST_AUDIT_REPORT && (
                                    <div style={{ marginTop: 14, padding: 12, borderRadius: 8, background: 'rgba(15, 23, 42, 0.4)', border: '1px solid #1e293b' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 6 }}>
                                            <span style={{ fontSize: 12, color: '#94a3b8' }}>
                                                📊 Lần quét gần nhất: <b style={{ color: '#f8fafc' }}>{overviewData.settings.LAST_AUDIT_RUN || 'Chưa có'}</b>
                                            </span>
                                            <span style={{ fontSize: 12, color: '#94a3b8' }}>
                                                Tổng quét: <b>{overviewData.settings.LAST_AUDIT_REPORT.total_scanned || 0}</b> website
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                            <span style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontSize: 12, fontWeight: 600 }}>
                                                ✅ {overviewData.settings.LAST_AUDIT_REPORT.healthy || 0} Site Bình Thường
                                            </span>
                                            <span style={{ padding: '4px 10px', borderRadius: 6, background: (overviewData.settings.LAST_AUDIT_REPORT.errors || 0) > 0 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(100, 116, 139, 0.2)', color: (overviewData.settings.LAST_AUDIT_REPORT.errors || 0) > 0 ? '#ef4444' : '#94a3b8', fontSize: 12, fontWeight: 600 }}>
                                                ❌ {overviewData.settings.LAST_AUDIT_REPORT.errors || 0} Site Bị Lỗi
                                            </span>
                                            <span style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(234, 179, 8, 0.15)', color: '#eab308', fontSize: 12, fontWeight: 600 }}>
                                                ⚠️ {overviewData.settings.LAST_AUDIT_REPORT.noindex || 0} Site NoIndex
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Server Crons Table */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Server size={16} style={{ color: '#38bdf8' }} />
                                        <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                            Trạng Thái Crontask Trên Từng Máy Chủ VPS
                                        </h4>
                                    </div>
                                    <span style={{ fontSize: 12, color: '#94a3b8' }}>
                                        {overviewData.servers?.length || 0} máy chủ
                                    </span>
                                </div>

                                <div className="table-container" style={{ maxHeight: 280, overflowY: 'auto' }}>
                                    <table className="data-table" style={{ fontSize: 12 }}>
                                        <thead>
                                            <tr>
                                                <th>Tên & Host Máy Chủ</th>
                                                <th>Loại</th>
                                                <th>Số Site Quét</th>
                                                <th>Lần Chạy Gần Nhất</th>
                                                <th>Trạng Thái</th>
                                                <th style={{ textAlign: 'right' }}>Thao Tác Từ Xa</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {overviewData.servers?.length === 0 ? (
                                                <tr>
                                                    <td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8', padding: 20 }}>
                                                        Chưa có máy chủ nào được thêm vào hệ thống.
                                                    </td>
                                                </tr>
                                            ) : (
                                                overviewData.servers?.map(srv => {
                                                    const isRunning = runningServerId === srv.id;
                                                    return (
                                                        <tr key={srv.id}>
                                                            <td>
                                                                <div style={{ fontWeight: 600, color: '#f8fafc' }}>{srv.name}</div>
                                                                <div style={{ color: '#94a3b8', fontSize: 11 }}><code>{srv.host}:{srv.port || 22}</code></div>
                                                            </td>
                                                            <td>
                                                                <span style={{ 
                                                                    fontSize: 11, 
                                                                    padding: '2px 8px', 
                                                                    borderRadius: 4, 
                                                                    background: srv.type === 'vps' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                                                                    color: srv.type === 'vps' ? '#38bdf8' : '#eab308'
                                                                }}>
                                                                    {srv.type === 'vps' ? 'aaPanel VPS' : 'cPanel'}
                                                                </span>
                                                            </td>
                                                            <td style={{ fontWeight: 600, color: '#34d399' }}>
                                                                {srv.sites_count || 0} WP Sites
                                                            </td>
                                                            <td style={{ color: '#94a3b8' }}>
                                                                {srv.last_checked || 'Chưa kiểm tra'}
                                                            </td>
                                                            <td>
                                                                <span className={`site-status-badge ${srv.status === 'ONLINE' ? 'online' : 'offline'}`} style={{ fontSize: 11, padding: '2px 8px' }}>
                                                                    {srv.status || 'UNKNOWN'}
                                                                </span>
                                                            </td>
                                                            <td style={{ textAlign: 'right' }}>
                                                                <button
                                                                    className="btn btn-sm btn-primary"
                                                                    onClick={() => handleTriggerRemoteCron(srv.id, srv.name)}
                                                                    disabled={isRunning}
                                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600 }}
                                                                >
                                                                    <Play size={11} className={isRunning ? 'animate-spin' : ''} />
                                                                    {isRunning ? 'Đang chạy...' : '⚡ Chạy Quét Ngay'}
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    );
                                                })
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Terminal Live Output */}
                            {terminalOutput && (
                                <div style={{ background: '#090d16', border: '1px solid #1e293b', borderRadius: 10, padding: 14 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#38bdf8', fontSize: 13, fontWeight: 600 }}>
                                            <Terminal size={14} /> Nhật Ký Thực Thi SSH Từ Xa
                                        </div>
                                        <button className="btn btn-sm" onClick={() => setTerminalOutput(null)} style={{ fontSize: 11 }}>
                                            Đóng log
                                        </button>
                                    </div>
                                    <pre style={{ margin: 0, padding: 12, background: 'rgba(0,0,0,0.4)', borderRadius: 6, fontSize: 12, color: '#34d399', maxHeight: 200, overflowY: 'auto', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                        {terminalOutput}
                                    </pre>
                                </div>
                            )}

                            {/* Recent Cron Sync Logs */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                                    <FileText size={16} style={{ color: '#fb923c' }} />
                                    <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                        Nhật Ký Cron Quét & Đồng Bộ Tự Động Gần Nhất
                                    </h4>
                                </div>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 240, overflowY: 'auto' }}>
                                    {overviewData.recent_cron_logs?.length === 0 ? (
                                        <div style={{ textAlign: 'center', color: '#94a3b8', padding: 20 }}>
                                            Chưa có nhật ký chạy cron nào được ghi lại.
                                        </div>
                                    ) : (
                                        overviewData.recent_cron_logs?.map((l, i) => {
                                            let det = {};
                                            try {
                                                det = typeof l.details === 'string' ? JSON.parse(l.details) : l.details;
                                            } catch (e) {
                                                det = { raw: l.details };
                                            }
                                            return (
                                                <div key={i} style={{ 
                                                    padding: '10px 14px', 
                                                    borderRadius: 8, 
                                                    background: 'rgba(15, 23, 42, 0.7)', 
                                                    border: '1px solid #334155',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    fontSize: 12
                                                }}>
                                                    <div>
                                                        <span style={{ color: '#38bdf8', fontWeight: 600, marginRight: 8 }}>
                                                            {det?.server_name || det?.server_host || l.target_domain || 'VPS'}
                                                        </span>
                                                        <span style={{ color: '#94a3b8' }}>
                                                            {l.action === 'auto_scan_sites' ? 'Tự động quét hoàn tất:' : 'Thao tác:'}
                                                        </span>
                                                        <span style={{ color: '#f8fafc', marginLeft: 6 }}>
                                                            Đã quét <b>{det?.total_scanned ?? 'N/A'}</b> sites (Thêm mới: <b style={{ color: '#34d399' }}>{det?.synced_new ?? 0}</b>)
                                                        </span>
                                                    </div>
                                                    <span style={{ color: '#64748b', fontSize: 11 }}>
                                                        {l.created_at}
                                                    </span>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TAB 3: CRONTAB GENERATOR & INSTALL GUIDE */}
                    {subTab === 'generator' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            {/* Generator Box */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                                    <Terminal size={16} style={{ color: '#38bdf8' }} />
                                    <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                        Bộ Sinh Lệnh Cron Job Chuẩn (1-Click Copy Crontab)
                                    </h4>
                                </div>

                                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 14 }}>
                                    Dán câu lệnh này vào mục <b>Cron Job</b> trong aaPanel hoặc file <code>crontab -e</code> trên máy chủ VPS con để tự động quét website mới và đồng bộ về Dashboard:
                                </p>

                                <div style={{ marginBottom: 12 }}>
                                    <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>
                                        Chọn Chu Kỳ Quét:
                                    </label>
                                    <select
                                        className="form-select"
                                        value={formSettings.CRON_SCHEDULE_EXPR}
                                        onChange={e => setFormSettings({ ...formSettings, CRON_SCHEDULE_EXPR: e.target.value })}
                                        style={{ width: '100%', maxWidth: 380, fontSize: 13 }}
                                    >
                                        <option value="0 3 */3 * *">3 ngày 1 lần vào lúc 03:00 sáng (0 3 */3 * *) - Khuyến nghị</option>
                                        <option value="0 3 * * *">Mỗi ngày 1 lần vào lúc 03:00 sáng (0 3 * * *)</option>
                                        <option value="0 3 * * 0">Mỗi tuần 1 lần vào Chủ Nhật lúc 03:00 sáng (0 3 * * 0)</option>
                                        <option value="0 */6 * * *">Mỗi 6 tiếng một lần (0 */6 * * *) - Test thử nghiệm</option>
                                    </select>
                                </div>

                                {(() => {
                                    const cronCmd = `${formSettings.CRON_SCHEDULE_EXPR} /usr/bin/python3 /www/wwwroot/pbn-tool/auto_scan_sites.py >> /www/wwwroot/pbn-tool/cron_scan.log 2>&1`;
                                    return (
                                        <div style={{ background: '#090d16', border: '1px solid #1e293b', borderRadius: 8, padding: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                                            <code style={{ color: '#38bdf8', fontSize: 13, wordBreak: 'break-all', fontFamily: 'monospace' }}>
                                                {cronCmd}
                                            </code>
                                            <button
                                                className="btn btn-sm btn-primary"
                                                onClick={() => copyText(cronCmd, 'cron')}
                                                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, flexShrink: 0 }}
                                            >
                                                {copiedKey === 'cron' ? <Check size={13} /> : <Copy size={13} />}
                                                {copiedKey === 'cron' ? 'Đã sao chép' : 'Sao chép lệnh'}
                                            </button>
                                        </div>
                                    );
                                })()}
                            </div>

                            {/* Install Guide Box */}
                            <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                                    <Zap size={16} style={{ color: '#eab308' }} />
                                    <h4 style={{ margin: 0, fontSize: 15, color: '#f8fafc', fontWeight: 600 }}>
                                        Lệnh Cài Đặt Nhanh Công Cụ <code>pbn-tool</code> Lên VPS Con Mới
                                    </h4>
                                </div>

                                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 14 }}>
                                    Khi mới thêm 1 VPS aaPanel, anh chỉ cần SSH vào và chạy 1 dòng lệnh này để tạo thư mục <code>/www/wwwroot/pbn-tool</code> và tải sẵn script:
                                </p>

                                {(() => {
                                    const installCmd = `mkdir -p /www/wwwroot/pbn-tool && cd /www/wwwroot/pbn-tool && curl -sO https://pbn.keodinh.net/api/vps/tool-script && chmod +x /www/wwwroot/pbn-tool/auto_scan_sites.py`;
                                    return (
                                        <div style={{ background: '#090d16', border: '1px solid #1e293b', borderRadius: 8, padding: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                                            <code style={{ color: '#34d399', fontSize: 13, wordBreak: 'break-all', fontFamily: 'monospace' }}>
                                                {installCmd}
                                            </code>
                                            <button
                                                className="btn btn-sm"
                                                onClick={() => copyText(installCmd, 'install')}
                                                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, flexShrink: 0 }}
                                            >
                                                {copiedKey === 'install' ? <Check size={13} style={{ color: '#10b981' }} /> : <Copy size={13} />}
                                                {copiedKey === 'install' ? 'Đã sao chép' : 'Sao chép'}
                                            </button>
                                        </div>
                                    );
                                })()}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Modal footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20, borderTop: '1px solid #334155', paddingTop: 14 }}>
                <button className="btn" onClick={onClose} style={{ fontWeight: 600 }}>
                    Đóng Cửa Sổ
                </button>
            </div>
        </div>
    );
}

