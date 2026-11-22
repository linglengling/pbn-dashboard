import React, { useState, useEffect } from 'react';
import { 
    Search, RefreshCw, AlertTriangle, CheckCircle, XCircle, 
    ExternalLink, Eye, ShieldCheck, Globe, Zap, Server, ShieldAlert,
    Copy, Trash2, Eraser, CheckSquare, Lock, Unlock, MinusCircle
} from 'lucide-react';
import IndexingModalContent from './IndexingModalContent';

const API_BASE = '';

const authFetch = async (url, options = {}) => {
    const token = localStorage.getItem('pbn_token');
    const headers = {
        ...options.headers || {},
        ...token ? { 'Authorization': `Bearer ${token}` } : {}
    };
    const resp = await fetch(url, { ...options, headers });
    if (resp.status === 401) {
        localStorage.removeItem('pbn_token');
    }
    return resp;
};

export default function AuditTab({ addToast, lang = 'vi' }) {
    const [summary, setSummary] = useState({
        total_audited: 0,
        healthy: 0,
        noindex: 0,
        errors: 0,
        breakdown: {}
    });
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [fixing, setFixing] = useState(false);
    const [filterType, setFilterType] = useState('ISSUES'); // ISSUES, NOINDEX, ERROR, HEALTHY, ALL
    const [searchQuery, setSearchQuery] = useState('');
    const [activeModalImg, setActiveModalImg] = useState(null);
    const [reAuditLoading, setReAuditLoading] = useState({});
    const [selectedDomains, setSelectedDomains] = useState([]);
    const [indexingModalDomains, setIndexingModalDomains] = useState(null);

    // Fetch summary
    const loadSummary = async () => {
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/summary`)).json();
            if (res.success) {
                setSummary(res.data);
            }
        } catch (e) {
            console.error('Error loading audit summary:', e);
        }
    };

    // Fetch audited sites
    const loadSites = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                filter_type: filterType,
                limit: 200
            });
            if (searchQuery.trim()) {
                params.append('search', searchQuery.trim());
            }
            const res = await (await authFetch(`${API_BASE}/api/audit/sites?${params.toString()}`)).json();
            if (res.success) {
                setSites(res.data || []);
            }
        } catch (e) {
            addToast?.('Lỗi tải danh sách audit website', 'error');
        }
        setLoading(false);
    };

    useEffect(() => {
        loadSummary();
        loadSites();
    }, [filterType]);

    // Handle Search
    const handleSearch = (e) => {
        e.preventDefault();
        loadSites();
    };

    // Run Scan
    const handleRunScan = async (scanOption = 'UNAUDITED') => {
        setScanning(true);
        addToast?.(
            scanOption === 'ALL' 
                ? 'Đang bắt đầu quét toàn diện tất cả website...' 
                : 'Đang quét các website chưa được kiểm tra...', 
            'info'
        );

        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scan_all: scanOption === 'ALL',
                    filter_status: scanOption,
                    limit: scanOption === 'ALL' ? 100 : 50
                })
            })).json();

            if (res.success) {
                addToast?.(res.message || 'Quét hoàn tất!', 'success');
                loadSummary();
                loadSites();
            } else {
                addToast?.(res.message || 'Lỗi khi quét', 'error');
            }
        } catch (e) {
            addToast?.(`Lỗi gửi lệnh quét: ${e.message}`, 'error');
        }
        setScanning(false);
    };

    // Single site re-audit
    const handleReAudit = async (domain) => {
        setReAuditLoading(prev => ({ ...prev, [domain]: true }));
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains: [domain] })
            })).json();

            if (res.success) {
                addToast?.(`Đã kiểm tra lại [${domain}]`, 'success');
                loadSummary();
                loadSites();
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
        setReAuditLoading(prev => ({ ...prev, [domain]: false }));
    };

    // Toggle Index (open / close)
    const handleToggleIndex = async (domains, action = 'open') => {
        if (!domains || domains.length === 0) return;
        setFixing(true);
        const actionText = action === 'open' ? 'mở index' : 'đóng index';
        addToast?.(`Đang gửi lệnh ${actionText} tới ${domains.length} website...`, 'info');

        try {
            const resp = await authFetch(`${API_BASE}/api/audit/toggle-index`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains, action })
            });
            const res = await resp.json().catch(() => ({}));

            if (resp.status === 401) {
                addToast?.('Phiên đăng nhập đã hết hạn (401). Đang tải lại để đăng nhập lại...', 'error');
                setTimeout(() => window.location.reload(), 1200);
            } else if (resp.ok && res.success) {
                addToast?.(res.message || `${action === 'open' ? 'Mở' : 'Đóng'} index thành công!`, 'success');
                loadSummary();
                loadSites();
            } else {
                addToast?.(res.message || res.detail || `Lỗi ${actionText} (HTTP ${resp.status})`, 'error');
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
        setFixing(false);
    };

    const handleFixNoIndex = (domains) => handleToggleIndex(domains, 'open');

    // Selection handlers
    const toggleSelect = (domain) => {
        setSelectedDomains(prev => 
            prev.includes(domain) ? prev.filter(d => d !== domain) : [...prev, domain]
        );
    };

    const toggleSelectAll = () => {
        if (selectedDomains.length === sites.length && sites.length > 0) {
            setSelectedDomains([]);
        } else {
            setSelectedDomains(sites.map(s => s.domain));
        }
    };

    // Bulk Action: Copy to clipboard
    const handleBulkCopy = () => {
        const selectedSites = sites.filter(s => selectedDomains.includes(s.domain));
        const text = selectedSites.map(s => {
            const errText = s.error_type !== 'NONE' ? ` | Lỗi: ${s.error_type} (${s.error_detail || ''})` : ' | Hoạt động tốt';
            const idxText = s.is_noindex ? ' [NoIndex]' : '';
            return `${s.domain}${idxText}${errText}`;
        }).join('\n');
        navigator.clipboard.writeText(text);
        addToast?.(`Đã sao chép danh sách ${selectedDomains.length} website vào bộ nhớ tạm!`, 'success');
    };

    // Bulk Action: Clear Audit Errors
    const handleBulkClearErrors = async () => {
        if (!window.confirm(`Bạn có chắc muốn xóa trạng thái lỗi cho ${selectedDomains.length} website đã chọn?`)) return;
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/bulk-clear-errors`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains: selectedDomains })
            })).json();
            if (res.success) {
                addToast?.(res.message, 'success');
                setSelectedDomains([]);
                loadSummary();
                loadSites();
            } else {
                addToast?.(res.detail || 'Lỗi khi xóa trạng thái lỗi', 'error');
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
    };

    // Bulk Action: Delete Sites Permanently
    const handleBulkDeleteSites = async () => {
        if (!window.confirm(`⚠️ CẢNH BÁO: Bạn có chắc chắn muốn XÓA HOÀN TOÀN ${selectedDomains.length} website đã chọn khỏi hệ thống Dashboard? Thao tác này không thể hoàn tác!`)) return;
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/bulk-delete-sites`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains: selectedDomains })
            })).json();
            if (res.success) {
                addToast?.(res.message, 'success');
                setSelectedDomains([]);
                loadSummary();
                loadSites();
            } else {
                addToast?.(res.detail || 'Lỗi khi xóa website', 'error');
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
    };

    // Bulk Action: Re-Audit Selected
    const handleBulkReAudit = async () => {
        setScanning(true);
        addToast?.(`Đang quét lại ${selectedDomains.length} website đã chọn...`, 'info');
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domains: selectedDomains })
            })).json();
            if (res.success) {
                addToast?.(res.message || 'Quét hoàn tất!', 'success');
                loadSummary();
                loadSites();
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
        setScanning(false);
    };

    // Clean all invalid domains (no dots, folder names, etc.)
    const handleCleanInvalidDomains = async () => {
        if (!window.confirm("Hệ thống sẽ tự động quét và xóa tất cả các tên không đúng định dạng domain (ví dụ các thư mục cPanel không có dấu chấm .). Bạn có chắc muốn thực hiện?")) return;
        try {
            const res = await (await authFetch(`${API_BASE}/api/audit/clean-invalid-domains`, { method: 'POST' })).json();
            if (res.success) {
                addToast?.(res.message, 'success');
                setSelectedDomains([]);
                loadSummary();
                loadSites();
            } else {
                addToast?.(res.detail || 'Lỗi dọn dẹp', 'error');
            }
        } catch (e) {
            addToast?.(`Lỗi: ${e.message}`, 'error');
        }
    };

    // Get list of all currently displayed noindex domains
    const noindexDomains = sites.filter(s => s.is_noindex === 1).map(s => s.domain);

    return (
        <div className="tab-content" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Header info */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: 20, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 10 }}>
                        <ShieldCheck size={24} style={{ color: '#38bdf8' }} />
                        Trung Tâm Audit Sức Khỏe, Nội Dung & Index Website
                    </h2>
                    <p style={{ margin: '4px 0 0 0', fontSize: 13, color: '#94a3b8' }}>
                        Chụp ảnh màn hình (Screenshot), đọc nội dung phát hiện lỗi CSDL/PHP/Cloudflare và lọc website chặn Google Index (NoIndex).
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button 
                        className="btn btn-danger"
                        onClick={handleCleanInvalidDomains}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                        title="Tự động quét và xóa sạch tất cả domain sai định dạng (thư mục cPanel không có dấu .)"
                    >
                        <Trash2 size={14} /> Xóa Domain Sai Format
                    </button>
                    <button 
                        className="btn btn-warning"
                        onClick={() => handleFixNoIndex(noindexDomains)}
                        disabled={fixing || noindexDomains.length === 0}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                        title="Tự động mở index (blog_public = 1) cho tất cả các site đang bị noindex"
                    >
                        <Zap size={14} /> {fixing ? 'Đang mở index...' : `Mở Index (${summary.noindex || 0} sites)`}
                    </button>
                    <button 
                        className="btn btn-success"
                        onClick={() => handleRunScan('ALL')}
                        disabled={scanning}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <RefreshCw size={14} className={scanning ? 'animate-spin' : ''} />
                        {scanning ? 'Đang quét...' : 'Quét Toàn Diện Tất Cả Sites'}
                    </button>
                    <button 
                        className="btn btn-primary"
                        onClick={() => handleRunScan('UNAUDITED')}
                        disabled={scanning}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <Globe size={14} /> Quét 50 Site Mới
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                <div className="stat-card" style={{ borderLeft: '4px solid #6366f1' }}>
                    <div className="stat-label">Tổng Site Đã Kiểm Tra</div>
                    <div className="stat-value" style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Globe size={22} /> {summary.total_audited}
                    </div>
                </div>
                <div className="stat-card" style={{ borderLeft: '4px solid #10b981' }}>
                    <div className="stat-label">Hoạt Động Tốt & Đã Mở Index</div>
                    <div className="stat-value" style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CheckCircle size={22} /> {summary.healthy}
                    </div>
                </div>
                <div className="stat-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                    <div className="stat-label">Chưa Mở Index (Chặn NoIndex)</div>
                    <div className="stat-value" style={{ color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <AlertTriangle size={22} /> {summary.noindex}
                    </div>
                </div>
                <div className="stat-card" style={{ borderLeft: '4px solid #ef4444' }}>
                    <div className="stat-label">Site Lỗi (DNS / CSDL / HTTP)</div>
                    <div className="stat-value" style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <ShieldAlert size={22} /> {summary.errors}
                    </div>
                </div>
            </div>

            {/* Toolbar Filters & Search */}
            <div className="toolbar" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button 
                        className={`btn btn-sm ${filterType === 'ISSUES' ? 'btn-primary' : ''}`}
                        onClick={() => setFilterType('ISSUES')}
                        style={filterType === 'ISSUES' ? { fontWeight: 700 } : { background: 'rgba(255,255,255,0.05)' }}
                    >
                        🚨 Site Lỗi & Chặn Index ({(summary.errors || 0) + (summary.noindex || 0)})
                    </button>
                    <button 
                        className={`btn btn-sm ${filterType === 'NOINDEX' ? 'btn-warning' : ''}`}
                        onClick={() => setFilterType('NOINDEX')}
                        style={filterType === 'NOINDEX' ? { fontWeight: 700 } : { background: 'rgba(255,255,255,0.05)', color: '#fbbf24' }}
                    >
                        ⚠️ Chặn Index (NoIndex: {summary.noindex})
                    </button>
                    <button 
                        className={`btn btn-sm ${filterType === 'ERROR' ? 'btn-danger' : ''}`}
                        onClick={() => setFilterType('ERROR')}
                        style={filterType === 'ERROR' ? { fontWeight: 700 } : { background: 'rgba(255,255,255,0.05)', color: '#f87171' }}
                    >
                        🔴 Lỗi Website ({summary.errors})
                    </button>
                    <button 
                        className={`btn btn-sm ${filterType === 'HEALTHY' ? 'btn-success' : ''}`}
                        onClick={() => setFilterType('HEALTHY')}
                        style={filterType === 'HEALTHY' ? { fontWeight: 700 } : { background: 'rgba(255,255,255,0.05)', color: '#34d399' }}
                    >
                        🟢 Hoạt động tốt ({summary.healthy})
                    </button>
                    <button 
                        className={`btn btn-sm ${filterType === 'ALL' ? 'btn-primary' : ''}`}
                        onClick={() => setFilterType('ALL')}
                        style={filterType === 'ALL' ? { fontWeight: 700 } : { background: 'rgba(255,255,255,0.05)', color: '#94a3b8' }}
                    >
                        Tất cả ({summary.total_audited})
                    </button>
                    <button
                        className="btn btn-sm"
                        onClick={() => setIndexingModalDomains(selectedDomains.length > 0 ? selectedDomains : sites.map(s => s.domain))}
                        style={{
                            background: 'rgba(234, 179, 8, 0.15)',
                            color: '#facc15',
                            border: '1px solid rgba(234, 179, 8, 0.35)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            fontWeight: 600
                        }}
                        title="Gửi sitemap hoặc trang chủ của các site đang chọn / đang lọc lên 2Index.ninja"
                    >
                        <Zap size={13} /> ⚡ Gửi Index (2Index)
                    </button>
                </div>

                <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, minWidth: 280, flex: 1, maxWidth: 450 }}>
                    <div className="search-wrapper" style={{ flex: 1 }}>
                        <Search size={16} />
                        <input 
                            type="text" 
                            className="search-input" 
                            placeholder="Tìm domain, tiêu đề hoặc mã lỗi..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ padding: '0 12px' }}>
                        Tìm
                    </button>
                </form>
            </div>

            {/* Bulk Action Toolbar */}
            {selectedDomains.length > 0 && (
                <div style={{
                    position: 'sticky',
                    top: 10,
                    zIndex: 50,
                    background: 'rgba(15, 23, 42, 0.95)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid #38bdf8',
                    borderRadius: 10,
                    padding: '10px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 12,
                    boxShadow: '0 8px 30px rgba(0,0,0,0.5)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ 
                            background: '#0284c7', 
                            color: '#fff', 
                            fontWeight: 700, 
                            fontSize: 12, 
                            padding: '3px 10px', 
                            borderRadius: 20 
                        }}>
                            Đã chọn {selectedDomains.length} website
                        </span>
                        <button 
                            className="btn btn-sm"
                            onClick={() => setSelectedDomains([])}
                            style={{ fontSize: 11, padding: '2px 8px' }}
                        >
                            Bỏ chọn
                        </button>
                    </div>

                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                            className="btn btn-sm btn-primary"
                            onClick={handleBulkCopy}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                            title="Sao chép danh sách các site kèm mã lỗi vào clipboard để gửi báo cáo fix lỗi"
                        >
                            <Copy size={13} /> Sao Chép Danh Sách ({selectedDomains.length})
                        </button>

                        <button
                            className="btn btn-sm"
                            onClick={() => setIndexingModalDomains(selectedDomains)}
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 6,
                                fontWeight: 600,
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                color: '#ffffff',
                                border: 'none',
                                boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                            }}
                            title="Gửi sitemap hoặc trang chủ của các site đã chọn lên 2Index.ninja để ép index"
                        >
                            <Zap size={13} /> ⚡ Gửi 2Index ({selectedDomains.length})
                        </button>

                        <button
                            className="btn btn-sm btn-warning"
                            onClick={handleBulkClearErrors}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                            title="Xóa trạng thái lỗi kiểm tra cho các site đã chọn"
                        >
                            <Eraser size={13} /> Xóa Lỗi Audit ({selectedDomains.length})
                        </button>

                        <button
                            className="btn btn-sm"
                            onClick={handleBulkReAudit}
                            disabled={scanning}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)' }}
                            title="Quét kiểm tra lại chỉ các site đã chọn"
                        >
                            <RefreshCw size={13} className={scanning ? 'animate-spin' : ''} /> Quét Lại ({selectedDomains.length})
                        </button>

                        <button
                            className="btn btn-sm btn-danger"
                            onClick={handleBulkDeleteSites}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                            title="Xóa hoàn toàn các site này khỏi toàn bộ hệ thống"
                        >
                            <Trash2 size={13} /> Xóa Khỏi Hệ Thống ({selectedDomains.length})
                        </button>
                    </div>
                </div>
            )}

            {/* Results Table */}
            <div className="table-container" style={{ background: 'var(--bg-glass)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: 44, textAlign: 'center' }}>
                                <input 
                                    type="checkbox" 
                                    checked={selectedDomains.length === sites.length && sites.length > 0}
                                    onChange={toggleSelectAll}
                                    style={{ cursor: 'pointer', transform: 'scale(1.15)' }}
                                    title="Chọn / Bỏ chọn tất cả"
                                />
                            </th>
                            <th style={{ width: 140 }}>Screenshot</th>
                            <th style={{ width: 220 }}>Tên Miền (Domain)</th>
                            <th style={{ width: 140 }}>DNS IP</th>
                            <th style={{ width: 100 }}>HTTP Status</th>
                            <th style={{ width: 150 }}>Trạng Thái Index</th>
                            <th>Chi Tiết Nội Dung & Lỗi</th>
                            <th style={{ textAlign: 'right', width: 160 }}>Thao Tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={8} style={{ textAlign: 'center', padding: '50px 0', color: 'var(--text-muted)' }}>
                                    <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px', display: 'block', color: '#38bdf8' }} />
                                    Đang tải dữ liệu kiểm tra...
                                </td>
                            </tr>
                        ) : sites.length === 0 ? (
                            <tr>
                                <td colSpan={8} style={{ textAlign: 'center', padding: '50px 0', color: 'var(--text-muted)' }}>
                                    {summary.total_audited === 0 ? (
                                        <div>
                                            <p style={{ fontSize: 15, color: '#f1f5f9', fontWeight: 600 }}>Chưa có website nào được audit.</p>
                                            <p style={{ fontSize: 13 }}>Bấm <strong>"Quét Toàn Diện Tất Cả Sites"</strong> bên trên để hệ thống bắt đầu quét và chụp ảnh màn hình các site.</p>
                                            <button 
                                                className="btn btn-primary"
                                                onClick={() => handleRunScan('UNAUDITED')}
                                                style={{ marginTop: 10 }}
                                            >
                                                Bắt đầu Quét Ngay
                                            </button>
                                        </div>
                                    ) : (
                                        'Không tìm thấy website nào phù hợp với bộ lọc.'
                                    )}
                                </td>
                            </tr>
                        ) : (
                            sites.map((site) => {
                                const isSiteError = site.error_type && site.error_type !== 'NONE' && site.error_type !== 'NOINDEX';
                                const isNoIndex = site.is_noindex === 1 || site.error_type === 'NOINDEX';
                                const isHealthy = site.error_type === 'NONE' && !isNoIndex;
                                const isReAuditing = reAuditLoading[site.domain];
                                const isSelected = selectedDomains.includes(site.domain);

                                return (
                                    <tr key={site.domain} style={isSelected ? { background: 'rgba(56, 189, 248, 0.08)' } : {}}>
                                        {/* Checkbox */}
                                        <td style={{ textAlign: 'center' }}>
                                            <input 
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => toggleSelect(site.domain)}
                                                style={{ cursor: 'pointer', transform: 'scale(1.15)' }}
                                            />
                                        </td>
                                        {/* Screenshot Thumbnail */}
                                        <td>
                                            <div 
                                                style={{ 
                                                    width: 120, 
                                                    height: 75, 
                                                    borderRadius: 6, 
                                                    overflow: 'hidden', 
                                                    border: '1px solid rgba(255,255,255,0.1)', 
                                                    background: '#090d16',
                                                    position: 'relative',
                                                    cursor: 'pointer'
                                                }}
                                                onClick={() => setActiveModalImg({ domain: site.domain, url: site.screenshot_url, title: site.title })}
                                                title="Bấm để xem ảnh chụp màn hình phóng to"
                                            >
                                                <img 
                                                    src={site.screenshot_url} 
                                                    alt={site.domain}
                                                    loading="lazy"
                                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                    }}
                                                />
                                                <div style={{
                                                    position: 'absolute',
                                                    bottom: 2,
                                                    right: 2,
                                                    background: 'rgba(0,0,0,0.7)',
                                                    padding: '1px 4px',
                                                    borderRadius: 4,
                                                    fontSize: 10,
                                                    color: '#cbd5e1',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: 2
                                                }}>
                                                    <Eye size={10} /> Xem
                                                </div>
                                            </div>
                                        </td>

                                        {/* Domain & Title */}
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                <a 
                                                    href={`https://${site.domain}`} 
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
                                                <div style={{ fontSize: 12, color: '#94a3b8', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={site.title || 'Chưa đọc được tiêu đề'}>
                                                    {site.title || <span style={{ fontStyle: 'italic', color: '#64748b' }}>Không có tiêu đề</span>}
                                                </div>
                                            </div>
                                        </td>

                                        {/* DNS IP */}
                                        <td>
                                            <div style={{ fontSize: 13, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: 5 }}>
                                                <Server size={12} color="#38bdf8" />
                                                <code>{site.dns_ip || 'N/A'}</code>
                                            </div>
                                        </td>

                                        {/* HTTP Status */}
                                        <td>
                                            {site.http_status ? (
                                                <span style={{ 
                                                    padding: '2px 8px', 
                                                    borderRadius: 6, 
                                                    fontSize: 12, 
                                                    fontWeight: 700,
                                                    background: site.http_status === 200 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                                    color: site.http_status === 200 ? '#34d399' : '#f87171',
                                                    border: `1px solid ${site.http_status === 200 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                                                }}>
                                                    {site.http_status}
                                                </span>
                                            ) : (
                                                <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: 12, background: 'rgba(239, 68, 68, 0.15)', color: '#f87171' }}>
                                                    Fail
                                                </span>
                                            )}
                                        </td>

                                        {/* Index Status */}
                                        <td>
                                            {isSiteError ? (
                                                <span style={{ 
                                                    display: 'inline-flex', 
                                                    alignItems: 'center', 
                                                    gap: 4, 
                                                    padding: '3px 8px', 
                                                    borderRadius: 6, 
                                                    fontSize: 11, 
                                                    fontWeight: 600, 
                                                    background: 'rgba(148, 163, 184, 0.12)', 
                                                    color: '#94a3b8', 
                                                    border: '1px solid rgba(148, 163, 184, 0.25)' 
                                                }} title="Không xác định được trạng thái index do website đang bị lỗi kết nối hoặc DNS!">
                                                    <MinusCircle size={12} /> Chưa rõ (Lỗi site)
                                                </span>
                                            ) : isNoIndex ? (
                                                <span style={{ 
                                                    display: 'inline-flex', 
                                                    alignItems: 'center', 
                                                    gap: 4, 
                                                    padding: '4px 8px', 
                                                    borderRadius: 6, 
                                                    fontSize: 11, 
                                                    fontWeight: 700, 
                                                    background: 'rgba(245, 158, 11, 0.15)', 
                                                    color: '#fbbf24', 
                                                    border: '1px solid rgba(245, 158, 11, 0.4)' 
                                                }} title="Website có thẻ meta robots noindex hoặc header noindex chặn Google!">
                                                    <AlertTriangle size={12} /> CHẶN INDEX
                                                </span>
                                            ) : (
                                                <span style={{ 
                                                    display: 'inline-flex', 
                                                    alignItems: 'center', 
                                                    gap: 4, 
                                                    padding: '4px 8px', 
                                                    borderRadius: 6, 
                                                    fontSize: 11, 
                                                    fontWeight: 600, 
                                                    background: 'rgba(16, 185, 129, 0.15)', 
                                                    color: '#34d399', 
                                                    border: '1px solid rgba(16, 185, 129, 0.3)' 
                                                }}>
                                                    <CheckCircle size={12} /> Đã Mở Index
                                                </span>
                                            )}
                                        </td>

                                        {/* Content & Error Detail */}
                                        <td>
                                            {isHealthy ? (
                                                <span style={{ color: '#34d399', fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                                                    <CheckCircle size={13} /> Sẵn sàng hoạt động (SEO OK)
                                                </span>
                                            ) : (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                                    <span style={{ color: '#f87171', fontWeight: 600, fontSize: 13 }}>
                                                        {site.error_detail || site.error_type}
                                                    </span>
                                                    <span style={{ color: '#64748b', fontSize: 11 }}>
                                                        Mã lỗi: <code>{site.error_type}</code>
                                                    </span>
                                                </div>
                                            )}
                                        </td>

                                        {/* Actions */}
                                        <td style={{ textAlign: 'right' }}>
                                            <div style={{ display: 'inline-flex', gap: 6, justifyContent: 'flex-end' }}>
                                                {isSiteError ? (
                                                    <button 
                                                        className="btn btn-sm"
                                                        disabled
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '3px 8px', opacity: 0.35, cursor: 'not-allowed', color: '#94a3b8' }}
                                                        title="Không thể đổi trạng thái index vì website đang bị lỗi kết nối hoặc DNS"
                                                    >
                                                        <Lock size={11} /> Đóng/Mở
                                                    </button>
                                                ) : isNoIndex ? (
                                                    <button 
                                                        className="btn btn-sm btn-warning"
                                                        onClick={() => handleToggleIndex([site.domain], 'open')}
                                                        disabled={fixing}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '3px 8px', fontWeight: 600 }}
                                                        title="Bấm để MỞ index (cho phép Google index website này)"
                                                    >
                                                        <Unlock size={11} /> Mở Index
                                                    </button>
                                                ) : (
                                                    <button 
                                                        className="btn btn-sm"
                                                        onClick={() => handleToggleIndex([site.domain], 'close')}
                                                        disabled={fixing}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '3px 8px', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.3)' }}
                                                        title="Bấm để ĐÓNG index (bật thẻ NoIndex chặn Google)"
                                                    >
                                                        <Lock size={11} /> Đóng Index
                                                    </button>
                                                )}
                                                <button 
                                                    className="btn btn-sm"
                                                    onClick={() => setIndexingModalDomains([site.domain])}
                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '3px 8px', color: '#facc15', background: 'rgba(234, 179, 8, 0.15)', border: '1px solid rgba(234, 179, 8, 0.35)' }}
                                                    title="Gửi index 2Index.ninja cho website này"
                                                >
                                                    <Zap size={11} /> Index
                                                </button>
                                                <button 
                                                    className="btn btn-sm"
                                                    onClick={() => handleReAudit(site.domain)}
                                                    disabled={isReAuditing}
                                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, padding: '3px 8px' }}
                                                    title="Kiểm tra lại website này"
                                                >
                                                    <RefreshCw size={11} className={isReAuditing ? 'animate-spin' : ''} />
                                                    {isReAuditing ? '...' : 'Quét'}
                                                </button>
                                                <a 
                                                    href={`https://${site.domain}`} 
                                                    target="_blank" 
                                                    rel="noreferrer" 
                                                    className="btn btn-sm"
                                                    style={{ padding: '3px 6px', color: '#94a3b8' }}
                                                    title="Mở website trong tab mới"
                                                >
                                                    <ExternalLink size={12} />
                                                </a>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal Zoom Screenshot */}
            {activeModalImg && (
                <div className="modal-overlay" onClick={() => setActiveModalImg(null)}>
                    <div className="modal" style={{ maxWidth: 850, padding: 20 }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 16 }}>
                                <Globe size={18} color="#38bdf8" />
                                Ảnh chụp màn hình: {activeModalImg.domain}
                            </div>
                            <button className="btn btn-sm" onClick={() => setActiveModalImg(null)}>✕</button>
                        </div>
                        <div style={{ 
                            background: '#090d16', 
                            border: '1px solid rgba(255,255,255,0.1)', 
                            borderRadius: 8, 
                            overflow: 'hidden', 
                            maxHeight: 520,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <img 
                                src={activeModalImg.url} 
                                alt={activeModalImg.domain}
                                style={{ width: '100%', height: 'auto', maxHeight: 520, objectFit: 'contain' }}
                            />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14 }}>
                            <div style={{ fontSize: 12, color: '#94a3b8' }}>
                                Tiêu đề: {activeModalImg.title || 'N/A'}
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <a 
                                    href={`https://${activeModalImg.domain}`} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    className="btn btn-primary btn-sm"
                                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                >
                                    <ExternalLink size={12} /> Truy cập Website
                                </a>
                                <button className="btn btn-sm" onClick={() => setActiveModalImg(null)}>Đóng</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal 2Index.ninja Indexing */}
            {indexingModalDomains && (
                <div className="modal-overlay" onClick={() => setIndexingModalDomains(null)}>
                    <div className="modal" style={{ maxWidth: 780 }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Zap size={18} color="#eab308" />
                                ⚡ Gửi Index Lên 2Index.ninja ({indexingModalDomains.length} Website)
                            </div>
                            <button className="btn btn-sm" onClick={() => setIndexingModalDomains(null)}>✕</button>
                        </div>
                        <IndexingModalContent
                            initialDomains={indexingModalDomains}
                            addToast={addToast}
                            onClose={() => setIndexingModalDomains(null)}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
