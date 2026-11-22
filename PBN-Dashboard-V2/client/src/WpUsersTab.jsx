import React, { useState } from 'react';
import {
    UserCheck, Key, Globe, Shield, RefreshCw, CheckCircle,
    AlertTriangle, Copy, Check, Download, Sparkles, ExternalLink,
    Filter, Search, Server, UserPlus, Eye, EyeOff
} from 'lucide-react';

const API_BASE = '';

export default function WpUsersTab({ addToast, lang = 'vi' }) {
    const [domainListText, setDomainListText] = useState('');
    const [username, setUsername] = useState('pbn_admin');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [emailPattern, setEmailPattern] = useState('{username}@{domain}');
    const [role, setRole] = useState('administrator');
    const [actionType, setActionType] = useState('updateu');
    
    const [isExecuting, setIsExecuting] = useState(false);
    const [results, setResults] = useState(null);
    const [filterStatus, setFilterStatus] = useState('all');
    const [copiedIndex, setCopiedIndex] = useState(null);

    // Auto calculate count of entered domains
    const domainsCount = domainListText
        .split('\n')
        .map(d => d.trim())
        .filter(d => d.length > 0).length;

    // Generate strong random password
    const handleGeneratePassword = () => {
        const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*';
        let pass = '';
        for (let i = 0; i < 14; i++) {
            pass += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        setPassword(pass);
        setShowPassword(true);
        if (addToast) addToast('Đã tạo mật khẩu bảo mật ngẫu nhiên!', 'success');
    };

    // Execute bulk upsert
    const handleExecute = async () => {
        const domains = domainListText
            .split('\n')
            .map(d => d.trim())
            .filter(d => d.length > 0);

        if (domains.length === 0) {
            if (addToast) addToast('Vui lòng nhập ít nhất 1 domain!', 'error');
            return;
        }

        if (!username.trim()) {
            if (addToast) addToast('Vui lòng nhập Username!', 'error');
            return;
        }

        if (!password.trim()) {
            if (addToast) addToast('Vui lòng nhập hoặc tạo Mật khẩu!', 'error');
            return;
        }

        setIsExecuting(true);
        setResults(null);
        if (addToast) addToast(`Đang xử lý ${domains.length} domain qua API p-manager.php...`, 'info');

        try {
            const token = localStorage.getItem('pbn_token');
            const res = await fetch(`${API_BASE}/api/users/bulk-wp-users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    domains,
                    username: username.trim(),
                    password: password.trim(),
                    email: emailPattern.trim() || null,
                    role,
                    action: actionType
                })
            });

            const data = await res.json();
            if (data.success) {
                setResults(data);
                if (addToast) {
                    addToast(`Hoàn tất! Thành công: ${data.success_count} / Thất bại: ${data.error_count}`, data.error_count === 0 ? 'success' : 'info');
                }
            } else {
                if (addToast) addToast(data.detail || data.error || 'Có lỗi xảy ra khi xử lý', 'error');
            }
        } catch (err) {
            if (addToast) addToast(`Lỗi kết nối máy chủ: ${err.message}`, 'error');
        } finally {
            setIsExecuting(false);
        }
    };

    // Copy single login info
    const copyLoginInfo = (item, idx) => {
        const text = `URL: https://${item.domain}/wp-admin\nUser: ${username}\nPass: ${password}\nRole: ${item.role || role}`;
        navigator.clipboard.writeText(text);
        setCopiedIndex(idx);
        setTimeout(() => setCopiedIndex(null), 2000);
        if (addToast) addToast(`Đã copy thông tin đăng nhập cho ${item.domain}`, 'success');
    };

    // Export all successful to TXT
    const handleExportTxt = () => {
        if (!results || !results.results) return;
        const valid = results.results.filter(r => r.status === 'success');
        if (valid.length === 0) {
            if (addToast) addToast('Không có domain thành công để xuất!', 'info');
            return;
        }

        let content = `BÁO CÁO CẤP TÀI KHOẢN WORDPRESS HÀNG LOẠT\n`;
        content += `Thời gian: ${new Date().toLocaleString()}\n`;
        content += `Tổng site: ${valid.length}\n`;
        content += `====================================================\n\n`;

        valid.forEach((item, index) => {
            content += `${index + 1}. Domain: ${item.domain}\n`;
            content += `   Đăng nhập: https://${item.domain}/wp-admin\n`;
            content += `   Username : ${username}\n`;
            content += `   Password : ${password}\n`;
            content += `   Role     : ${item.role || role}\n`;
            content += `   Server   : ${item.server_name} (${item.server_host})\n`;
            content += `----------------------------------------------------\n`;
        });

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pbn_wp_users_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        if (addToast) addToast('Đã tải xuống file tài khoản TXT', 'success');
    };

    // Filter results
    const filteredResults = results?.results?.filter(r => {
        if (filterStatus === 'all') return true;
        return r.status === filterStatus;
    }) || [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* INTRO CARD */}
            <div className="section-card" style={{
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: 16,
                padding: 24
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
                    <div style={{
                        background: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                        width: 44,
                        height: 44,
                        borderRadius: 12,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 14px rgba(56, 189, 248, 0.3)'
                    }}>
                        <UserCheck size={24} color="#ffffff" />
                    </div>
                    <div>
                        <h2 style={{ margin: 0, fontSize: 20, color: '#f8fafc', fontWeight: 700 }}>
                            Quản Lý & Cấp User WordPress Hàng Loạt
                        </h2>
                        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: 13 }}>
                            Dán danh sách domain ➜ Tự động nạp API siêu tốc <code style={{ color: '#38bdf8' }}>p-manager.php (?ttpp=atc=...)</code> kèm cơ chế SSH dự phòng để Tạo mới hoặc Đổi mật khẩu hàng loạt trong vài giây.
                        </p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 10, fontSize: 12, color: '#38bdf8' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <CheckCircle size={14} color="#10b981" /> Hỗ trợ cả VPS aaPanel &amp; cPanel Hosting
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Shield size={14} color="#10b981" /> Bỏ qua Cloudflare / 301 Redirect / DNS
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Key size={14} color="#10b981" /> Tự động nhận diện User đã tồn tại để cập nhật Pass
                    </span>
                </div>
            </div>

            {/* FORM CONFIG */}
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.2fr)', gap: 20 }}>
                {/* LEFT: DOMAIN LIST INPUT */}
                <div className="section-card" style={{ borderRadius: 16, padding: 20, display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                        <label style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Globe size={16} color="#38bdf8" /> Danh sách Domain ({domainsCount})
                        </label>
                        <span style={{ fontSize: 12, color: '#64748b' }}>1 domain / dòng</span>
                    </div>

                    <textarea
                        value={domainListText}
                        onChange={e => setDomainListText(e.target.value)}
                        placeholder={`x8.games\n8xbet-1\nbayvip.life\nhttps://vaoroitv.sbs/\n...`}
                        rows={12}
                        style={{
                            width: '100%',
                            flex: 1,
                            minHeight: 240,
                            background: '#090d16',
                            border: '1px solid #334155',
                            borderRadius: 10,
                            padding: 14,
                            color: '#f8fafc',
                            fontFamily: 'monospace',
                            fontSize: 13,
                            lineHeight: 1.6,
                            resize: 'vertical',
                            outline: 'none',
                            boxSizing: 'border-box'
                        }}
                    />

                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10 }}>
                        <button
                            type="button"
                            className="btn btn-secondary"
                            style={{ fontSize: 12, padding: '4px 10px' }}
                            onClick={() => setDomainListText('')}
                        >
                            Xóa trắng ô
                        </button>
                        <span style={{ fontSize: 12, color: '#94a3b8' }}>
                            {domainsCount > 0 ? `Đã nhập ${domainsCount} domain` : 'Chưa có domain nào'}
                        </span>
                    </div>
                </div>

                {/* RIGHT: USER CREDENTIALS & OPTIONS */}
                <div className="section-card" style={{ borderRadius: 16, padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <UserPlus size={16} color="#38bdf8" /> Thông tin Tài khoản WordPress cần cấp
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        {/* ACTION TYPE SELECTOR */}
                        <div>
                            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#cbd5e1', marginBottom: 6 }}>
                                Chế độ thực thi (Action)
                            </label>
                            <select
                                value={actionType}
                                onChange={e => setActionType(e.target.value)}
                                style={{
                                    width: '100%',
                                    background: '#090d16',
                                    border: '1px solid #334155',
                                    borderRadius: 8,
                                    padding: '10px 12px',
                                    color: '#f8fafc',
                                    fontSize: 13,
                                    outline: 'none',
                                    cursor: 'pointer',
                                    boxSizing: 'border-box'
                                }}
                            >
                                <option value="updateu">⚡ Cập nhật mật khẩu (Chưa có thì tạo mới) — updateu [Mặc định]</option>
                                <option value="createu">➕ Chỉ tạo mới (Báo lỗi nếu User đã tồn tại) — createu</option>
                            </select>
                        </div>

                        {/* USERNAME */}
                        <div>
                            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#cbd5e1', marginBottom: 6 }}>
                                Tên đăng nhập (Username) <span style={{ color: '#ef4444' }}>*</span>
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                placeholder="Ví dụ: pbn_admin, seo_editor..."
                                style={{
                                    width: '100%',
                                    background: '#090d16',
                                    border: '1px solid #334155',
                                    borderRadius: 8,
                                    padding: '10px 12px',
                                    color: '#f8fafc',
                                    fontSize: 14,
                                    outline: 'none',
                                    boxSizing: 'border-box'
                                }}
                            />
                        </div>

                        {/* PASSWORD WITH RANDOM GENERATOR */}
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                <label style={{ fontSize: 13, fontWeight: 500, color: '#cbd5e1' }}>
                                    Mật khẩu (Password) <span style={{ color: '#ef4444' }}>*</span>
                                </label>
                                <button
                                    type="button"
                                    onClick={handleGeneratePassword}
                                    style={{
                                        background: 'rgba(56, 189, 248, 0.1)',
                                        border: '1px solid #0284c7',
                                        color: '#38bdf8',
                                        padding: '2px 8px',
                                        borderRadius: 6,
                                        fontSize: 12,
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 4
                                    }}
                                >
                                    <Sparkles size={12} /> Tạo mật khẩu mạnh
                                </button>
                            </div>
                            <div style={{ position: 'relative' }}>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    placeholder="Nhập mật khẩu hoặc nhấn 'Tạo mật khẩu mạnh'..."
                                    style={{
                                        width: '100%',
                                        background: '#090d16',
                                        border: '1px solid #334155',
                                        borderRadius: 8,
                                        padding: '10px 40px 10px 12px',
                                        color: '#f8fafc',
                                        fontSize: 14,
                                        fontFamily: showPassword ? 'monospace' : 'inherit',
                                        outline: 'none',
                                        boxSizing: 'border-box'
                                    }}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{
                                        position: 'absolute',
                                        right: 10,
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        background: 'transparent',
                                        border: 'none',
                                        color: '#64748b',
                                        cursor: 'pointer'
                                    }}
                                >
                                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {/* ROLE & EMAIL */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <div>
                                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#cbd5e1', marginBottom: 6 }}>
                                    Quyền hạn (Role)
                                </label>
                                <select
                                    value={role}
                                    onChange={e => setRole(e.target.value)}
                                    style={{
                                        width: '100%',
                                        background: '#090d16',
                                        border: '1px solid #334155',
                                        borderRadius: 8,
                                        padding: '10px 12px',
                                        color: '#f8fafc',
                                        fontSize: 14,
                                        outline: 'none',
                                        cursor: 'pointer',
                                        boxSizing: 'border-box'
                                    }}
                                >
                                    <option value="administrator">👑 Administrator (Quản trị viên)</option>
                                    <option value="editor">📝 Editor (Biên tập viên)</option>
                                    <option value="author">✍️ Author (Tác giả)</option>
                                    <option value="contributor">📑 Contributor (Cộng tác viên)</option>
                                    <option value="subscriber">👤 Subscriber (Thành viên)</option>
                                </select>
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#cbd5e1', marginBottom: 6 }}>
                                    Email mẫu
                                </label>
                                <input
                                    type="text"
                                    value={emailPattern}
                                    onChange={e => setEmailPattern(e.target.value)}
                                    placeholder="{username}@{domain}"
                                    style={{
                                        width: '100%',
                                        background: '#090d16',
                                        border: '1px solid #334155',
                                        borderRadius: 8,
                                        padding: '10px 12px',
                                        color: '#f8fafc',
                                        fontSize: 14,
                                        outline: 'none',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* SUBMIT BUTTON */}
                    <div style={{ marginTop: 'auto', paddingTop: 10 }}>
                        <button
                            type="button"
                            onClick={handleExecute}
                            disabled={isExecuting || domainsCount === 0}
                            style={{
                                width: '100%',
                                background: isExecuting || domainsCount === 0 ? '#334155' : 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)',
                                color: '#ffffff',
                                border: 'none',
                                borderRadius: 10,
                                padding: '14px',
                                fontSize: 15,
                                fontWeight: 700,
                                cursor: isExecuting || domainsCount === 0 ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 10,
                                boxShadow: isExecuting || domainsCount === 0 ? 'none' : '0 4px 16px rgba(56, 189, 248, 0.35)',
                                transition: 'all 0.2s'
                            }}
                        >
                            {isExecuting ? (
                                <>
                                    <RefreshCw size={18} style={{ animation: 'spin 1s linear infinite' }} />
                                    Đang thực thi tạo / cập nhật tài khoản...
                                </>
                            ) : (
                                <>
                                    <UserCheck size={18} />
                                    Bắt đầu Thực thi ({domainsCount} Website)
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* RESULTS SECTION */}
            {results && (
                <div className="section-card" style={{ borderRadius: 16, padding: 20 }}>
                    {/* STATS HEADER */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16, borderBottom: '1px solid #334155', paddingBottom: 16 }}>
                        <div>
                            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#f8fafc' }}>
                                Kết Quả Thực Thi Hàng Loạt
                            </h3>
                            <span style={{ fontSize: 13, color: '#94a3b8' }}>
                                Tổng cộng: <b style={{ color: '#f8fafc' }}>{results.total}</b> domain | 
                                Thành công: <b style={{ color: '#10b981' }}>{results.success_count}</b> | 
                                Lỗi: <b style={{ color: '#ef4444' }}>{results.error_count}</b>
                            </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            {/* FILTER BUTTONS */}
                            <div style={{ display: 'flex', background: '#090d16', border: '1px solid #334155', borderRadius: 8, padding: 2 }}>
                                <button
                                    onClick={() => setFilterStatus('all')}
                                    style={{
                                        background: filterStatus === 'all' ? '#1e293b' : 'transparent',
                                        color: filterStatus === 'all' ? '#38bdf8' : '#94a3b8',
                                        border: 'none',
                                        borderRadius: 6,
                                        padding: '4px 10px',
                                        fontSize: 12,
                                        cursor: 'pointer',
                                        fontWeight: 600
                                    }}
                                >
                                    Tất cả ({results.results?.length || 0})
                                </button>
                                <button
                                    onClick={() => setFilterStatus('success')}
                                    style={{
                                        background: filterStatus === 'success' ? '#1e293b' : 'transparent',
                                        color: filterStatus === 'success' ? '#10b981' : '#94a3b8',
                                        border: 'none',
                                        borderRadius: 6,
                                        padding: '4px 10px',
                                        fontSize: 12,
                                        cursor: 'pointer',
                                        fontWeight: 600
                                    }}
                                >
                                    Thành công ({results.success_count})
                                </button>
                                <button
                                    onClick={() => setFilterStatus('error')}
                                    style={{
                                        background: filterStatus === 'error' ? '#1e293b' : 'transparent',
                                        color: filterStatus === 'error' ? '#ef4444' : '#94a3b8',
                                        border: 'none',
                                        borderRadius: 6,
                                        padding: '4px 10px',
                                        fontSize: 12,
                                        cursor: 'pointer',
                                        fontWeight: 600
                                    }}
                                >
                                    Lỗi ({results.error_count})
                                </button>
                            </div>

                            {/* EXPORT TXT */}
                            <button
                                onClick={handleExportTxt}
                                style={{
                                    background: 'rgba(16, 185, 129, 0.15)',
                                    border: '1px solid #10b981',
                                    color: '#34d399',
                                    padding: '6px 14px',
                                    borderRadius: 8,
                                    fontSize: 13,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6
                                }}
                            >
                                <Download size={14} /> Xuất file TXT
                            </button>
                        </div>
                    </div>

                    {/* RESULTS TABLE */}
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                            <thead>
                                <tr style={{ background: '#090d16', borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                                    <th style={{ padding: '10px 12px', width: 40 }}>#</th>
                                    <th style={{ padding: '10px 12px' }}>Website Domain</th>
                                    <th style={{ padding: '10px 12px' }}>Máy chủ (Server)</th>
                                    <th style={{ padding: '10px 12px' }}>Hành động</th>
                                    <th style={{ padding: '10px 12px' }}>Trạng thái</th>
                                    <th style={{ padding: '10px 12px' }}>Chi tiết kết quả</th>
                                    <th style={{ padding: '10px 12px', textAlign: 'right', width: 100 }}>Thao tác</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredResults.map((item, idx) => (
                                    <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                                        <td style={{ padding: '12px', color: '#64748b' }}>{idx + 1}</td>
                                        <td style={{ padding: '12px' }}>
                                            <a
                                                href={`https://${item.domain}/wp-admin`}
                                                target="_blank"
                                                rel="noreferrer"
                                                style={{ color: '#38bdf8', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                            >
                                                {item.domain} <ExternalLink size={12} color="#64748b" />
                                            </a>
                                            {item.site_name && (
                                                <div style={{ fontSize: 11, color: '#64748b' }}>{item.site_name}</div>
                                            )}
                                        </td>
                                        <td style={{ padding: '12px', color: '#cbd5e1' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                <Server size={13} color="#818cf8" />
                                                <span>{item.server_name}</span>
                                            </div>
                                            <div style={{ fontSize: 11, color: '#64748b', marginLeft: 19 }}>{item.server_host}</div>
                                        </td>
                                        <td style={{ padding: '12px' }}>
                                            {item.action === 'created' ? (
                                                <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>
                                                    Tạo mới
                                                </span>
                                            ) : item.action === 'updated' ? (
                                                <span style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>
                                                    Đổi mật khẩu
                                                </span>
                                            ) : (
                                                <span style={{ color: '#64748b', fontSize: 11 }}>-</span>
                                            )}
                                        </td>
                                        <td style={{ padding: '12px' }}>
                                            {item.status === 'success' ? (
                                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#10b981', fontWeight: 600, fontSize: 12 }}>
                                                    <CheckCircle size={14} /> Thành công
                                                </span>
                                            ) : (
                                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#ef4444', fontWeight: 600, fontSize: 12 }}>
                                                    <AlertTriangle size={14} /> Lỗi
                                                </span>
                                            )}
                                        </td>
                                        <td style={{ padding: '12px', color: item.status === 'success' ? '#94a3b8' : '#f87171', fontSize: 12 }}>
                                            {item.message}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right' }}>
                                            {item.status === 'success' && (
                                                <button
                                                    onClick={() => copyLoginInfo(item, idx)}
                                                    style={{
                                                        background: copiedIndex === idx ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                                                        border: `1px solid ${copiedIndex === idx ? '#10b981' : '#334155'}`,
                                                        color: copiedIndex === idx ? '#34d399' : '#cbd5e1',
                                                        borderRadius: 6,
                                                        padding: '4px 8px',
                                                        fontSize: 11,
                                                        cursor: 'pointer',
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        gap: 4
                                                    }}
                                                    title="Copy thông tin đăng nhập"
                                                >
                                                    {copiedIndex === idx ? <Check size={12} /> : <Copy size={12} />}
                                                    {copiedIndex === idx ? 'Đã copy' : 'Copy'}
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
