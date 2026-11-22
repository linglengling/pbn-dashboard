import React, { useState, useEffect } from 'react';
import {
    Zap, KeyRound, Globe, FileText, CheckCircle2, AlertTriangle,
    RefreshCw, ExternalLink, Settings, ChevronRight, Layers,
    Search, X, Check, Eye, EyeOff
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

export default function IndexingModalContent({ initialDomains = [], addToast, onClose }) {
    // API Key & Account state
    const [statusLoading, setStatusLoading] = useState(true);
    const [hasKey, setHasKey] = useState(false);
    const [maskedKey, setMaskedKey] = useState('');
    const [account, setAccount] = useState(null);
    const [editingKey, setEditingKey] = useState(false);
    const [apiKeyInput, setApiKeyInput] = useState('');
    const [showKey, setShowKey] = useState(false);
    const [savingKey, setSavingKey] = useState(false);

    // Submission configuration state
    const [domains, setDomains] = useState(() => {
        return (initialDomains || []).map(d => d.trim().replace(/^https?:\/\//, '').replace(/\/$/, '')).filter(Boolean);
    });
    const [newDomainInput, setNewDomainInput] = useState('');
    const [mode, setMode] = useState('homepage'); // 'homepage', 'sitemap', 'custom_urls'
    const [customUrlsText, setCustomUrlsText] = useState('');
    const [google, setGoogle] = useState(true);
    const [bing, setBing] = useState(true);
    const [yandex, setYandex] = useState(false);

    // Sitemap preview state
    const [previewLoading, setPreviewLoading] = useState(false);
    const [sitemapPreview, setSitemapPreview] = useState(null);

    // Submission execution state
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);

    // Fetch indexing status and account info
    const fetchStatus = async () => {
        setStatusLoading(true);
        try {
            const res = await (await authFetch(`${API_BASE}/api/indexing/status`)).json();
            if (res.success) {
                setHasKey(res.has_key);
                setMaskedKey(res.masked_key);
                setGoogle(res.google !== 0);
                setBing(res.bing !== 0);
                setYandex(res.yandex === 1);
                setAccount(res.account);
                if (!res.has_key) {
                    setEditingKey(true);
                }
            }
        } catch (e) {
            console.error('Error fetching indexing status:', e);
        }
        setStatusLoading(false);
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    // Save API Key
    const handleSaveKey = async () => {
        const key = apiKeyInput.trim();
        if (!key) {
            return addToast('Vui lòng nhập API Token của 2Index.ninja', 'error');
        }
        setSavingKey(true);
        try {
            const res = await (await authFetch(`${API_BASE}/api/indexing/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: key,
                    google: google ? 1 : 0,
                    bing: bing ? 1 : 0,
                    yandex: yandex ? 1 : 0
                })
            })).json();

            if (res.success) {
                addToast(res.message || 'Kết nối thành công với 2Index.ninja!', 'success');
                setHasKey(true);
                setAccount(res.account);
                setEditingKey(false);
                setApiKeyInput('');
                fetchStatus();
            } else {
                addToast(res.error || 'API Token không hợp lệ!', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối tới máy chủ', 'error');
        }
        setSavingKey(false);
    };

    // Add manual domains
    const handleAddDomains = () => {
        const text = newDomainInput.trim();
        if (!text) return;
        const newDoms = text.split(/[\n,;\s]+/)
            .map(d => d.trim().replace(/^https?:\/\//, '').replace(/\/$/, ''))
            .filter(d => d && !domains.includes(d));
        if (newDoms.length > 0) {
            setDomains(prev => [...prev, ...newDoms]);
            setNewDomainInput('');
            addToast(`Đã thêm ${newDoms.length} domain vào danh sách`, 'info');
        }
    };

    const handleRemoveDomain = (dom) => {
        setDomains(prev => prev.filter(d => d !== dom));
    };

    // Preview sitemap of first domain
    const handlePreviewSitemap = async () => {
        if (domains.length === 0) return;
        setPreviewLoading(true);
        setSitemapPreview(null);
        try {
            const res = await (await authFetch(`${API_BASE}/api/indexing/preview-sitemap`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain: domains[0] })
            })).json();
            if (res.success && res.data) {
                setSitemapPreview(res.data);
            } else {
                addToast(res.error || 'Không thể lấy thông tin sitemap', 'error');
            }
        } catch (e) {
            addToast('Lỗi khi kiểm tra sitemap', 'error');
        }
        setPreviewLoading(false);
    };

    // Submit Indexing Job
    const handleSubmit = async () => {
        if (!hasKey) {
            return addToast('Vui lòng kết nối API Token 2Index.ninja trước khi gửi index', 'error');
        }

        if (mode !== 'custom_urls' && domains.length === 0) {
            return addToast('Vui lòng chọn hoặc nhập ít nhất 1 domain', 'error');
        }

        let customUrls = [];
        if (mode === 'custom_urls') {
            customUrls = customUrlsText.split('\n')
                .map(u => u.trim())
                .filter(u => u.startsWith('http://') || u.startsWith('https://'));
            if (customUrls.length === 0) {
                return addToast('Vui lòng nhập ít nhất 1 đường link (URL) hợp lệ', 'error');
            }
        }

        if (!google && !bing && !yandex) {
            return addToast('Vui lòng chọn ít nhất 1 công cụ tìm kiếm (Google, Bing hoặc Yandex)', 'error');
        }

        setSubmitting(true);
        setResult(null);

        try {
            const res = await (await authFetch(`${API_BASE}/api/indexing/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domains: domains,
                    mode: mode,
                    custom_urls: customUrls,
                    google: google ? 1 : 0,
                    bing: bing ? 1 : 0,
                    yandex: yandex ? 1 : 0
                })
            })).json();

            setResult(res);
            if (res.success) {
                addToast(`Đã gửi thành công ${res.total_submitted} link tới 2Index.ninja!`, 'success');
                if (res.account) {
                    setAccount(res.account);
                }
            } else {
                addToast(res.error || 'Gửi index không thành công', 'error');
            }
        } catch (e) {
            addToast('Lỗi kết nối khi gửi yêu cầu index', 'error');
        }
        setSubmitting(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxHeight: '82vh', overflowY: 'auto', paddingRight: 4 }}>
            {/* 1. API Token Connection Card */}
            <div style={{
                background: hasKey ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                border: `1px solid ${hasKey ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                borderRadius: 10,
                padding: '12px 16px'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                            width: 34,
                            height: 34,
                            borderRadius: 8,
                            background: hasKey ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: hasKey ? '#34d399' : '#ef4444'
                        }}>
                            <Zap size={18} />
                        </div>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <strong style={{ fontSize: 14, color: '#f8fafc' }}>
                                    Dịch Vụ Ép Index Tự Động (2Index.ninja API)
                                </strong>
                                <a
                                    href="https://2index.ninja/api-documentation"
                                    target="_blank"
                                    rel="noreferrer"
                                    style={{ fontSize: 11, color: '#38bdf8', display: 'inline-flex', alignItems: 'center', gap: 3, textDecoration: 'none' }}
                                >
                                    Docs ↗
                                </a>
                            </div>
                            <div style={{ fontSize: 12, color: hasKey ? '#34d399' : '#f87171', marginTop: 2 }}>
                                {statusLoading ? (
                                    'Đang tải trạng thái tài khoản...'
                                ) : hasKey ? (
                                    account ? (
                                        <span>
                                            ✅ Gói: <strong>{account.tariff}</strong> | Số link còn lại: <strong style={{ color: '#fbbf24' }}>{account.available_links}</strong> | Tốc độ: <strong>{account.link_sending_speed} links/ngày</strong> ({account.email})
                                        </span>
                                    ) : (
                                        `✅ Đã kết nối token: ${maskedKey}`
                                    )
                                ) : (
                                    '⚠️ Chưa cấu hình API Token 2Index.ninja. Vui lòng nhập token để sử dụng.'
                                )}
                            </div>
                        </div>
                    </div>

                    <button
                        className="btn btn-sm"
                        onClick={() => setEditingKey(!editingKey)}
                        style={{ fontSize: 11, padding: '4px 10px' }}
                    >
                        {editingKey ? 'Hủy' : (hasKey ? '⚙ Đổi Token' : '🔑 Nhập Token')}
                    </button>
                </div>

                {editingKey && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <div style={{ fontSize: 12, color: '#cbd5e1', marginBottom: 6 }}>
                            Nhập <strong>Bearer Access Token</strong> từ tài khoản 2Index.ninja của bạn:
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <div style={{ position: 'relative', flex: 1 }}>
                                <input
                                    type={showKey ? 'text' : 'password'}
                                    className="form-input"
                                    placeholder="Dán mã Bearer Token tại đây (VD: 1|abcd...)"
                                    value={apiKeyInput}
                                    onChange={e => setApiKeyInput(e.target.value)}
                                    style={{ paddingRight: 36, fontSize: 13 }}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowKey(!showKey)}
                                    style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                                >
                                    {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                                </button>
                            </div>
                            <button
                                className="btn btn-primary"
                                onClick={handleSaveKey}
                                disabled={savingKey}
                                style={{ minWidth: 120 }}
                            >
                                {savingKey ? 'Đang lưu...' : 'Lưu & Kết Nối'}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* 2. Target Domains Section */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <label className="form-label" style={{ fontWeight: 600, color: '#38bdf8', margin: 0 }}>
                        🌐 Danh Sách Tên Miền Cần Gửi Index ({domains.length} Website)
                    </label>
                    <span style={{ fontSize: 11, color: '#94a3b8' }}>
                        Có thể nhập thêm domain bên dưới
                    </span>
                </div>

                {/* Tags preview */}
                <div style={{
                    maxHeight: 120,
                    overflowY: 'auto',
                    border: '1px solid #334155',
                    borderRadius: 8,
                    padding: 8,
                    background: 'rgba(15, 23, 42, 0.6)',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 6
                }}>
                    {domains.length === 0 ? (
                        <span style={{ fontSize: 12, color: '#94a3b8', fontStyle: 'italic', padding: 4 }}>
                            Chưa có tên miền nào được chọn. Hãy nhập tên miền vào ô bên dưới.
                        </span>
                    ) : (
                        domains.map(dom => (
                            <span
                                key={dom}
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 5,
                                    background: 'rgba(56, 189, 248, 0.15)',
                                    border: '1px solid rgba(56, 189, 248, 0.3)',
                                    color: '#e0f2fe',
                                    fontSize: 12,
                                    padding: '2px 8px',
                                    borderRadius: 6
                                }}
                            >
                                {dom}
                                <button
                                    onClick={() => handleRemoveDomain(dom)}
                                    style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0, display: 'inline-flex' }}
                                    title="Xóa domain này"
                                >
                                    <X size={12} />
                                </button>
                            </span>
                        ))
                    )}
                </div>

                {/* Input to add more domains */}
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <input
                        className="form-input"
                        placeholder="Nhập thêm domain (cách nhau bởi phẩy hoặc dấu cách, VD: abc.com, xyz.net)"
                        value={newDomainInput}
                        onChange={e => setNewDomainInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddDomains(); } }}
                        style={{ fontSize: 12 }}
                    />
                    <button className="btn btn-sm" onClick={handleAddDomains} style={{ whiteSpace: 'nowrap' }}>
                        Thêm Domain
                    </button>
                    {domains.length > 0 && (
                        <button className="btn btn-sm btn-danger" onClick={() => setDomains([])} style={{ whiteSpace: 'nowrap' }}>
                            Xóa Hết
                        </button>
                    )}
                </div>
            </div>

            {/* 3. Indexing Mode Selection */}
            <div>
                <label className="form-label" style={{ fontWeight: 600, color: '#38bdf8', marginBottom: 8 }}>
                    🎯 Chế Độ Gửi Index:
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
                    {/* Option 1: Homepage */}
                    <div
                        onClick={() => setMode('homepage')}
                        style={{
                            border: `2px solid ${mode === 'homepage' ? '#38bdf8' : '#334155'}`,
                            background: mode === 'homepage' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                            borderRadius: 10,
                            padding: '12px 14px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, color: mode === 'homepage' ? '#38bdf8' : '#f8fafc', fontSize: 13 }}>
                            <Globe size={16} /> Gửi Trang Chủ (Homepages)
                        </div>
                        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                            Gửi URL trang chủ <code>https://domain/</code> của từng site được chọn.
                        </div>
                    </div>

                    {/* Option 2: Full Sitemap */}
                    <div
                        onClick={() => setMode('sitemap')}
                        style={{
                            border: `2px solid ${mode === 'sitemap' ? '#38bdf8' : '#334155'}`,
                            background: mode === 'sitemap' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                            borderRadius: 10,
                            padding: '12px 14px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, color: mode === 'sitemap' ? '#38bdf8' : '#f8fafc', fontSize: 13 }}>
                            <FileText size={16} /> Gửi Toàn Bộ Sitemap
                        </div>
                        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                            Tự động quét sitemap XML, lấy toàn bộ link bài viết & trang để ép index.
                        </div>
                    </div>

                    {/* Option 3: Custom URLs */}
                    <div
                        onClick={() => setMode('custom_urls')}
                        style={{
                            border: `2px solid ${mode === 'custom_urls' ? '#38bdf8' : '#334155'}`,
                            background: mode === 'custom_urls' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                            borderRadius: 10,
                            padding: '12px 14px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, color: mode === 'custom_urls' ? '#38bdf8' : '#f8fafc', fontSize: 13 }}>
                            <Layers size={16} /> Trang Cụ Thể (Custom URLs)
                        </div>
                        <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                            Dán danh sách các link cụ thể bạn muốn submit trực tiếp.
                        </div>
                    </div>
                </div>

                {/* Sitemap Mode Details */}
                {mode === 'sitemap' && (
                    <div style={{ marginTop: 10, padding: 10, background: 'rgba(56, 189, 248, 0.05)', border: '1px dashed rgba(56, 189, 248, 0.3)', borderRadius: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 12, color: '#94a3b8' }}>
                                Hệ thống sẽ tự động tìm <code>sitemap_index.xml</code> / <code>wp-sitemap.xml</code> và giải nén link bài viết.
                            </span>
                            {domains.length > 0 && (
                                <button
                                    className="btn btn-sm"
                                    onClick={handlePreviewSitemap}
                                    disabled={previewLoading}
                                    style={{ fontSize: 11, padding: '2px 8px' }}
                                >
                                    {previewLoading ? 'Đang đọc sitemap...' : `🔍 Test Sitemap site đầu tiên (${domains[0]})`}
                                </button>
                            )}
                        </div>

                        {sitemapPreview && (
                            <div style={{ marginTop: 8, fontSize: 12, color: '#cbd5e1', background: 'rgba(15, 23, 42, 0.7)', padding: 8, borderRadius: 6 }}>
                                <div>Sitemap tìm thấy: <strong style={{ color: '#38bdf8' }}>{sitemapPreview.sitemap_url}</strong></div>
                                <div>Tổng số link phát hiện: <strong style={{ color: '#34d399' }}>{sitemapPreview.total_urls} links</strong></div>
                                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4, maxHeight: 60, overflowY: 'auto' }}>
                                    {sitemapPreview.urls.slice(0, 5).join(' | ')} ...
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Custom URLs Mode Details */}
                {mode === 'custom_urls' && (
                    <div style={{ marginTop: 10 }}>
                        <label className="form-label" style={{ fontSize: 12, color: '#94a3b8' }}>
                            Dán danh sách các link (Mỗi link 1 dòng, bắt đầu bằng http:// hoặc https://):
                        </label>
                        <textarea
                            className="form-input"
                            rows={4}
                            placeholder={`https://domain1.com/bai-viet-1\nhttps://domain1.com/bai-viet-2\nhttps://domain2.com/gioi-thieu`}
                            value={customUrlsText}
                            onChange={e => setCustomUrlsText(e.target.value)}
                            style={{ fontSize: 12 }}
                        />
                    </div>
                )}
            </div>

            {/* 4. Search Engines Selection */}
            <div>
                <label className="form-label" style={{ fontWeight: 600, color: '#38bdf8', marginBottom: 6 }}>
                    🚀 Công Cụ Tìm Kiếm Cần Ép Index:
                </label>
                <div style={{ display: 'flex', gap: 18, alignItems: 'center', background: 'rgba(15, 23, 42, 0.5)', padding: '8px 14px', borderRadius: 8, border: '1px solid #334155' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#f8fafc', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={google}
                            onChange={e => setGoogle(e.target.checked)}
                            style={{ accentColor: '#38bdf8' }}
                        />
                        <span style={{ fontWeight: 600, color: '#4ade80' }}>Google</span> (Khuyến nghị)
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#f8fafc', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={bing}
                            onChange={e => setBing(e.target.checked)}
                            style={{ accentColor: '#38bdf8' }}
                        />
                        <span style={{ fontWeight: 600, color: '#60a5fa' }}>Bing / Yahoo</span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#f8fafc', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={yandex}
                            onChange={e => setYandex(e.target.checked)}
                            style={{ accentColor: '#38bdf8' }}
                        />
                        <span style={{ fontWeight: 600, color: '#f87171' }}>Yandex</span>
                    </label>
                </div>
            </div>

            {/* 5. Result Display */}
            {result && (
                <div style={{
                    background: result.success ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                    border: `1px solid ${result.success ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
                    borderRadius: 10,
                    padding: 14
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, color: result.success ? '#34d399' : '#f87171', fontSize: 14 }}>
                        {result.success ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                        {result.success ? '✅ Gửi Index Thành Công!' : '❌ Gửi Index Thất Bại'}
                    </div>
                    <div style={{ fontSize: 13, color: '#f8fafc', marginTop: 4 }}>
                        {result.message}
                    </div>

                    {result.total_submitted > 0 && (
                        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 6 }}>
                            Đã nạp <strong>{result.total_submitted} link</strong> từ <strong>{result.domains_count} website</strong> vào hàng đợi index.
                            {result.account && (
                                <span style={{ marginLeft: 8, color: '#fbbf24' }}>
                                    (Số link còn lại: <strong>{result.account.available_links}</strong>)
                                </span>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* 6. Footer Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, paddingTop: 14, borderTop: '1px solid #334155' }}>
                <button className="btn" onClick={onClose}>
                    Đóng Cửa Sổ
                </button>

                <button
                    className="btn btn-primary"
                    onClick={handleSubmit}
                    disabled={submitting || !hasKey || (mode !== 'custom_urls' && domains.length === 0)}
                    style={{
                        padding: '8px 24px',
                        fontWeight: 700,
                        fontSize: 14,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        border: 'none',
                        boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)'
                    }}
                >
                    <Zap size={16} className={submitting ? 'animate-spin' : ''} />
                    {submitting ? 'Đang gửi sang 2Index.ninja...' : `🚀 Bắt Đầu Gửi Index (${mode === 'custom_urls' ? 'Custom URLs' : `${domains.length} Sites`})`}
                </button>
            </div>
        </div>
    );
}
