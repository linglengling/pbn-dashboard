import React, { useState } from 'react';
import { Globe, Search, RefreshCw, AlertTriangle, ExternalLink, Copy, Check } from 'lucide-react';

const API_BASE = '';

const authFetch = (url, options = {}) => {
    const token = localStorage.getItem('pbn_token');
    const headers = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    return fetch(url, { ...options, headers });
};

export default function OutboundLinksModalContent({ site, initialLinks = [], refreshSites, addToast }) {
    const [links, setLinks] = useState(() => {
        if (Array.isArray(initialLinks)) return initialLinks;
        try {
            return typeof initialLinks === 'string' ? JSON.parse(initialLinks) : [];
        } catch (e) {
            return [];
        }
    });
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [copiedIdx, setCopiedIdx] = useState(null);

    const handleCrawlNow = async () => {
        setLoading(true);
        if (addToast) addToast(`Đang cào lại link out trang chủ ${site.domain}...`, 'info');
        try {
            const res = await authFetch(`${API_BASE}/api/sites/scan-links`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain: site.domain })
            });
            const data = await res.json();
            if (data.success) {
                const newLinks = data.homepage_outbound_links || [];
                setLinks(newLinks);
                if (addToast) addToast(`Đã cào xong: tìm thấy ${data.total_homepage_links || 0} link out!`, 'success');
                if (refreshSites) refreshSites();
            } else {
                if (addToast) addToast(data.detail || 'Lỗi khi cào link', 'error');
            }
        } catch (e) {
            if (addToast) addToast(`Lỗi kết nối: ${e.message}`, 'error');
        }
        setLoading(false);
    };

    const copyUrl = (url, idx) => {
        navigator.clipboard.writeText(url);
        setCopiedIdx(idx);
        setTimeout(() => setCopiedIdx(null), 2000);
    };

    const filtered = (links || []).filter(l => {
        const q = search.toLowerCase();
        return (l.url && l.url.toLowerCase().includes(q)) ||
               (l.anchor && l.anchor.toLowerCase().includes(q)) ||
               (l.domain && l.domain.toLowerCase().includes(q));
    });

    return (
        <div style={{ padding: '4px 0', maxHeight: '72vh', overflowY: 'auto' }}>
            {/* Header Toolbar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 200 }}>
                    <div className="search-bar" style={{ margin: 0, width: '100%' }}>
                        <Search size={14} style={{ color: '#94a3b8' }} />
                        <input
                            type="text"
                            placeholder="Tìm kiếm domain đích, anchor, URL..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            style={{ fontSize: 13 }}
                        />
                    </div>
                </div>
                <button
                    className="btn btn-sm btn-primary"
                    onClick={handleCrawlNow}
                    disabled={loading}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600, flexShrink: 0 }}
                >
                    <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                    {loading ? 'Đang cào...' : 'Quét Lại Link Out Ngay'}
                </button>
            </div>

            {/* Content List or Empty State */}
            {(!links || links.length === 0) ? (
                <div style={{ 
                    padding: '36px 16px', 
                    textAlign: 'center', 
                    background: 'rgba(30, 41, 59, 0.5)', 
                    borderRadius: 10, 
                    border: '1px dashed #334155' 
                }}>
                    <AlertTriangle size={32} style={{ color: '#f59e0b', margin: '0 auto 12px' }} />
                    <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: 15, marginBottom: 6 }}>
                        Chưa có dữ liệu danh sách link out chi tiết
                    </div>
                    <p style={{ color: '#94a3b8', fontSize: 13, maxWidth: 460, margin: '0 auto 16px', lineHeight: 1.5 }}>
                        Domain này có tổng số link out ghi nhận là <b>{site.total_homepage_links || 0}</b> link, nhưng chi tiết danh sách chưa được đồng bộ về Dashboard.
                    </p>
                    <button
                        className="btn btn-sm btn-success"
                        onClick={handleCrawlNow}
                        disabled={loading}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
                    >
                        <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                        Bấm Vào Đây Để Cào & Trích Xuất Link Out Ngay
                    </button>
                </div>
            ) : filtered.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8' }}>
                    Không tìm thấy link nào khớp với từ khóa "{search}".
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ fontSize: 12, color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Hiển thị <b>{filtered.length}</b> / <b>{links.length}</b> link out trang chủ</span>
                        <span>Nguồn: <b>{site.domain}</b></span>
                    </div>

                    {filtered.map((link, idx) => {
                        let targetDomain = link.domain || '';
                        if (!targetDomain && link.url) {
                            try {
                                targetDomain = new URL(link.url).hostname.replace(/^www\./, '');
                            } catch (e) {
                                targetDomain = link.url;
                            }
                        }
                        const sourceUrl = `http://${site.domain}`;
                        return (
                            <div key={idx} style={{ 
                                padding: '12px 16px', 
                                borderRadius: 10, 
                                background: 'rgba(30, 41, 59, 0.85)', 
                                border: '1px solid #334155', 
                                display: 'flex', 
                                flexDirection: 'column', 
                                gap: 8 
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                        <span style={{ 
                                            background: 'rgba(34, 211, 238, 0.15)', 
                                            color: '#22d3ee', 
                                            border: '1px solid rgba(34, 211, 238, 0.35)', 
                                            padding: '2px 9px', 
                                            borderRadius: 6, 
                                            fontSize: 12, 
                                            fontWeight: 700,
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: 4
                                        }}>
                                            <Globe size={11} /> {targetDomain}
                                        </span>
                                        <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: 13 }}>
                                            Anchor: <span style={{ color: '#38bdf8' }}>"{link.anchor || '[No Anchor]'}"</span>
                                        </span>
                                    </div>

                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <button
                                            className="btn btn-sm"
                                            onClick={() => copyUrl(link.url, idx)}
                                            style={{ padding: '2px 8px', fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                            title="Sao chép URL"
                                        >
                                            {copiedIdx === idx ? <Check size={11} style={{ color: '#10b981' }} /> : <Copy size={11} />}
                                            {copiedIdx === idx ? 'Đã chép' : 'Chép URL'}
                                        </button>
                                        <a 
                                            href={sourceUrl} 
                                            target="_blank" 
                                            rel="noreferrer" 
                                            style={{ 
                                                color: '#34d399', 
                                                background: 'rgba(52, 211, 153, 0.12)', 
                                                border: '1px solid rgba(52, 211, 153, 0.3)', 
                                                padding: '2px 8px', 
                                                borderRadius: 6, 
                                                fontSize: 11, 
                                                fontWeight: 600, 
                                                display: 'inline-flex', 
                                                alignItems: 'center', 
                                                gap: 4, 
                                                textDecoration: 'none' 
                                            }}
                                        >
                                            Trang chủ <ExternalLink size={10} />
                                        </a>
                                    </div>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#94a3b8' }}>
                                    <span style={{ fontWeight: 600, color: '#64748b', minWidth: 80 }}>Outbound:</span>
                                    <a href={link.url} target="_blank" rel="noreferrer" style={{ color: '#cbd5e1', wordBreak: 'break-all', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                        {link.url} <ExternalLink size={11} />
                                    </a>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

