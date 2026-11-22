import React, { useState } from 'react';
import {
    BookOpen, Search, Globe, Server, ShieldCheck, Link2, FileText,
    Zap, Activity, Shield, Check, Copy, ExternalLink, HelpCircle,
    ChevronRight, Info, AlertTriangle, Layers, Camera, RefreshCw,
    Sliders, Cpu, Terminal
} from 'lucide-react';

export default function GuideTab({ navigateTo }) {
    const [search, setSearch] = useState('');
    const [activeSection, setActiveSection] = useState('overview');
    const [copiedSnippet, setCopiedSnippet] = useState(null);

    const copyCode = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedSnippet(id);
        setTimeout(() => setCopiedSnippet(null), 2000);
    };

    const sections = [
        { id: 'overview', title: 'Tổng Quan Hệ Thống', icon: Globe, badge: 'V2.0' },
        { id: 'sites', title: '1. Danh Sách Website (Sites)', icon: Globe },
        { id: 'redirect301', title: '2. Quản Lý 301 Redirect', icon: Zap, highlight: true },
        { id: 'outlinks', title: '3. Outlink & PBN Inlinks', icon: Link2 },
        { id: 'servers', title: '4. Máy Chủ & Crontab Máy Con', icon: Server },
        { id: 'audit', title: '5. Audit Sức Khỏe & Index', icon: ShieldCheck },
        { id: 'backlinks', title: '6. Quản Lý Backlink & Money Site', icon: Link2 },
        { id: 'content', title: '7. Bài Viết, AI Writer & Persona', icon: FileText },
        { id: 'users', title: '8. Quản Lý User WP & Mật Khẩu', icon: Shield },
        { id: 'faq', title: '9. Câu Hỏi Thường Gặp (FAQs)', icon: HelpCircle }
    ];

    const filteredSections = search.trim() === '' ? sections : sections.filter(s => 
        s.title.toLowerCase().includes(search.toLowerCase()) ||
        s.id.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Header Hero Banner */}
            <div style={{
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)',
                border: '1px solid #334155',
                borderRadius: 14,
                padding: '24px 28px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 16,
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
            }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                        <div style={{
                            background: 'rgba(56, 189, 248, 0.15)',
                            color: '#38bdf8',
                            padding: '6px 10px',
                            borderRadius: 8,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            fontWeight: 700,
                            fontSize: 13
                        }}>
                            <BookOpen size={16} /> TÀI LIỆU VẬN HÀNH
                        </div>
                        <span style={{ color: '#94a3b8', fontSize: 13 }}>Phiên bản PBN Matrix V2.0</span>
                    </div>
                    <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                        Trung Tâm Hướng Dẫn & Tra Cứu Chức Năng
                    </h2>
                    <p style={{ color: '#94a3b8', fontSize: 13, margin: '6px 0 0', maxWidth: 650 }}>
                        Mô tả chi tiết nguyên lý hoạt động, cách đọc các chỉ số trên bảng điều khiển, mẹo tối ưu SEO PBN và hướng dẫn xử lý sự cố thường gặp.
                    </p>
                </div>

                {/* Search Bar */}
                <div style={{ minWidth: 280, flex: 1, maxWidth: 360 }}>
                    <div className="search-bar" style={{ margin: 0, width: '100%' }}>
                        <Search size={15} style={{ color: '#94a3b8' }} />
                        <input
                            type="text"
                            placeholder="Tìm kiếm chức năng: 301, outlink, cron, audit..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            style={{ fontSize: 13 }}
                        />
                    </div>
                </div>
            </div>

            {/* Layout 2 Cột: Sidebar Danh Mục + Nội Dung Chi Tiết */}
            <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, alignItems: 'start' }}>
                {/* Sidebar Menu */}
                <div style={{
                    background: 'rgba(15, 23, 42, 0.85)',
                    border: '1px solid #334155',
                    borderRadius: 12,
                    padding: '12px 8px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                    position: 'sticky',
                    top: 20
                }}>
                    <div style={{ padding: '6px 12px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        Danh Mục Hướng Dẫn
                    </div>
                    {filteredSections.map(sec => {
                        const Icon = sec.icon;
                        const isActive = activeSection === sec.id;
                        return (
                            <button
                                key={sec.id}
                                onClick={() => setActiveSection(sec.id)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '9px 12px',
                                    borderRadius: 8,
                                    border: 'none',
                                    background: isActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                                    color: isActive ? '#38bdf8' : '#cbd5e1',
                                    fontWeight: isActive ? 600 : 500,
                                    fontSize: 13,
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                    transition: 'all 0.15s ease'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Icon size={14} style={{ color: isActive ? '#38bdf8' : (sec.highlight ? '#eab308' : '#94a3b8') }} />
                                    <span>{sec.title}</span>
                                </div>
                                {sec.badge && (
                                    <span style={{ fontSize: 10, background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', padding: '1px 5px', borderRadius: 4, fontWeight: 700 }}>
                                        {sec.badge}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* Content Panel */}
                <div style={{
                    background: 'rgba(15, 23, 42, 0.85)',
                    border: '1px solid #334155',
                    borderRadius: 12,
                    padding: '24px 28px',
                    minHeight: 600
                }}>

                    {/* OVERVIEW SECTION */}
                    {activeSection === 'overview' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 14 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Globe size={18} color="#38bdf8" /> Kiến Trúc & Tổng Quan Hệ Thống PBN Matrix V2
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    PBN Dashboard V2 là nền tảng quản trị mạng lưới website vệ tinh tập trung (WordPress), hỗ trợ từ hàng trăm đến hàng ngàn site trên nhiều hạ tầng máy chủ khác nhau.
                                </p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
                                <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                    <div style={{ color: '#38bdf8', fontWeight: 700, fontSize: 14, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Zap size={14} /> Backend FastAPI Siêu Tốc
                                    </div>
                                    <p style={{ color: '#94a3b8', fontSize: 13, margin: 0, lineHeight: 1.5 }}>
                                        Chạy trên nền tảng Python 3.10 + Uvicorn, xử lý đồng thời hàng chục ngàn ping và request quét đa luồng mà không gây nghẽn máy chủ.
                                    </p>
                                </div>

                                <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                    <div style={{ color: '#c084fc', fontWeight: 700, fontSize: 14, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Server size={14} /> Plugin Nhẹ (mu-plugin)
                                    </div>
                                    <p style={{ color: '#94a3b8', fontSize: 13, margin: 0, lineHeight: 1.5 }}>
                                        Chỉ gồm duy nhất file <code>pbn-manager.php</code> đặt trong <code>wp-content/mu-plugins/</code>. Không giao diện, không làm nặng trang web của khách.
                                    </p>
                                </div>

                                <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 16 }}>
                                    <div style={{ color: '#34d399', fontWeight: 700, fontSize: 14, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <ShieldCheck size={14} /> SPA HTML5 Routing
                                    </div>
                                    <p style={{ color: '#94a3b8', fontSize: 13, margin: 0, lineHeight: 1.5 }}>
                                        Mỗi chức năng là một trang URL riêng biệt (<code>/sites</code>, <code>/servers</code>, <code>/audit</code>...). F5 không bị mất trang, tải dữ liệu on-demand.
                                    </p>
                                </div>
                            </div>

                            <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: 10, padding: 16 }}>
                                <div style={{ fontWeight: 600, color: '#38bdf8', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <Info size={15} /> Điều hướng nhanh đến chức năng:
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                    {sections.filter(s => s.id !== 'overview').map(s => (
                                        <button
                                            key={s.id}
                                            className="btn btn-sm"
                                            onClick={() => setActiveSection(s.id)}
                                            style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', fontSize: 12 }}
                                        >
                                            {s.title}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* SITES TAB GUIDE */}
                    {activeSection === 'sites' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Globe size={18} color="#38bdf8" /> 1. Hướng Dẫn Trang Danh Sách Website (Sites Tab)
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Đây là màn hình trung tâm quản trị toàn bộ các tên miền trong hệ thống.
                                </p>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#38bdf8', margin: '0 0 8px', fontSize: 14 }}>Các Cột Dữ Liệu Chính Trong Bảng:</h4>
                                    <ul style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                        <li><strong>DOMAIN</strong>: Tên miền của website, kèm icon mở nhanh ra tab mới.</li>
                                        <li><strong>TRẠNG THÁI</strong>: <code>Online</code> (website phản hồi tốt) hoặc <code>Offline</code> (không phản hồi hoặc đã bị từ chối).</li>
                                        <li><strong>301 REDIRECT</strong>: Cột chuyên dụng thể hiện chuyển hướng (xem mục 2 bên dưới).</li>
                                        <li><strong>INDEX</strong>: Nút toggle bật/tắt cho phép Google Index (<code>Mở Index</code> màu xanh, <code>Đóng Index</code> màu vàng cảnh báo). Bấm vào để đổi trạng thái từ xa tức thì.</li>
                                        <li><strong>ĐỊA CHỈ IP</strong>: IP máy chủ hosting của website.</li>
                                        <li><strong>CỤM CLUSTER</strong>: Nhóm các website theo cùng dự án hoặc danh mục (VD: <code>default</code>, <code>bóng đá</code>, <code>game bài</code>).</li>
                                        <li><strong>BACKLINKS (TOOL)</strong>: Số lượng backlink đang trỏ từ website này do công cụ quản lý.</li>
                                        <li><strong>LINK TRANG CHỦ (TỔNG)</strong>: Tổng số outbound link ra ngoài bóc tách từ trang chủ. Click vào để xem chi tiết từng URL & anchor text.</li>
                                        <li><strong>PBN INLINKS</strong>: Số lượng liên kết nội bộ mà các website khác trong cùng hệ thống đang trỏ về site này.</li>
                                        <li><strong>ẢNH CHỤP / PREVIEW</strong>: Thumbnail xem trước giao diện thực tế. Click vào để phóng to độ phân giải cao.</li>
                                        <li><strong>HOẠT ĐỘNG LẦN CUỐI</strong>: Thời điểm gần nhất máy con gửi heartbeat ping về Dashboard.</li>
                                    </ul>
                                </div>

                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#f59e0b', margin: '0 0 8px', fontSize: 14 }}>Các Thao Tác Hàng Loạt (Bulk Actions):</h4>
                                    <p style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 8px' }}>
                                        Tick chọn một hoặc nhiều website (hoặc tick ô trên cùng để chọn cả trang), sau đó bạn có thể:
                                    </p>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                        <span style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.3)', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
                                            Gán Cụm Cluster
                                        </span>
                                        <span style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
                                            Đăng Bài Hàng Loạt
                                        </span>
                                        <span style={{ background: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
                                            Chèn Link Hàng Loạt
                                        </span>
                                        <span style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#fde047', border: '1px solid rgba(234, 179, 8, 0.3)', padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
                                            Sửa Head / Schema
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 301 REDIRECT GUIDE */}
                    {activeSection === 'redirect301' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Zap size={18} color="#eab308" /> 2. Quản Lý 301 Redirect & Nhóm Chuyển Hướng
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Theo dõi chính xác các domain vệ tinh đang chuyển hướng về money site hoặc các site chính trong mạng lưới.
                                </p>
                            </div>

                            <div style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 10, padding: 16 }}>
                                <div style={{ color: '#fef08a', fontWeight: 700, fontSize: 14, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <Zap size={15} /> Nhận Diện Hai Chiều Của Cột 301:
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                                    <div style={{ background: '#0f172a', padding: 14, borderRadius: 8, border: '1px solid rgba(234, 179, 8, 0.25)' }}>
                                        <div style={{ color: '#eab308', fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
                                            1. Domain Nguồn (Đang 301 ra ngoài)
                                        </div>
                                        <div style={{ marginBottom: 6 }}>
                                            <span style={{ background: 'rgba(234, 179, 8, 0.2)', color: '#fef08a', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700 }}>
                                                ⚡ 301 ➔ target.com
                                            </span>
                                        </div>
                                        <p style={{ color: '#94a3b8', fontSize: 12, margin: 0 }}>
                                            Domain này khi truy cập sẽ tự động nhảy sang <code>target.com</code>. Click vào badge để mở link kiểm tra.
                                        </p>
                                    </div>

                                    <div style={{ background: '#0f172a', padding: 14, borderRadius: 8, border: '1px solid rgba(168, 85, 247, 0.25)' }}>
                                        <div style={{ color: '#c084fc', fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
                                            2. Domain Đích (Nhận 301 từ các vệ tinh)
                                        </div>
                                        <div style={{ marginBottom: 6 }}>
                                            <span style={{ background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700 }}>
                                                🎯 Nhận 5 domain 301
                                            </span>
                                        </div>
                                        <p style={{ color: '#94a3b8', fontSize: 12, margin: 0 }}>
                                            Website này là đích đến của 5 domain vệ tinh khác. <strong>Click vào badge để mở popup xem danh sách và copy toàn bộ domain nguồn</strong>.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#38bdf8', margin: '0 0 8px', fontSize: 14 }}>Cơ Chế Quét & Cập Nhật Tự Động (Cron 2 Ngày / Lần):</h4>
                                <ul style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                    <li>Trên VPS có một cron task chạy ngầm định kỳ <strong>2 ngày 1 lần vào lúc 03:00 sáng</strong> (<code>scan_301_redirects.py</code>).</li>
                                    <li>Script sử dụng <strong>40 luồng song song</strong> kiểm tra cả giao thức HTTPS và HTTP của toàn bộ danh sách site trong ~2 phút.</li>
                                    <li>Nếu phát hiện domain có phản hồi <code>301, 302, 307, 308</code>, hệ thống tự động bóc tách URL đích và lưu vào CSDL.</li>
                                    <li>Nếu domain đã gỡ redirect (trở về mã 200 OK), hệ thống tự động xóa bỏ trạng thái 301 cũ để dữ liệu luôn chính xác 100%.</li>
                                    <li>Bạn có thể chủ động bấm nút <strong>"⚡ Quét 301"</strong> trên thanh công cụ để cập nhật tức thì bất cứ lúc nào.</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* OUTLINKS GUIDE */}
                    {activeSection === 'outlinks' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Link2 size={18} color="#22d3ee" /> 3. Outlink Trang Chủ & Mạng Lưới PBN Inlinks
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Kiểm soát chặt chẽ việc rò rỉ link ra ngoài và theo dõi sức mạnh liên kết chéo giữa các site PBN.
                                </p>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#22d3ee', margin: '0 0 8px', fontSize: 14 }}>1. Link Trang Chủ (Tổng Outbound Links):</h4>
                                <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: '0 0 10px' }}>
                                    Mỗi khi crawler quét hoặc website ping về, hệ thống sẽ bóc tách tất cả các thẻ <code>&lt;a href="..."&gt;</code> trỏ ra ngoài tên miền chính.
                                </p>
                                <div style={{ background: '#0f172a', padding: 12, borderRadius: 8, border: '1px solid #334155', fontSize: 13, color: '#94a3b8' }}>
                                    👉 <strong>Thao tác:</strong> Click vào badge (ví dụ: <span style={{ color: '#22d3ee', fontWeight: 600 }}>23 link</span>) để mở Modal:
                                    <ul style={{ margin: '6px 0 0', paddingLeft: 18, color: '#cbd5e1' }}>
                                        <li>Xem danh sách từng domain đích (kèm badge Cyan).</li>
                                        <li>Xem chính xác <strong>Anchor text</strong> mà link đang sử dụng.</li>
                                        <li>Nút <strong>"Chép URL"</strong> 1-click và link mở thẳng ra trang web.</li>
                                        <li>Ô tìm kiếm lọc nhanh theo tên miền hoặc từ khóa anchor.</li>
                                        <li>Nút <strong>"Quét Lại Link Out Ngay"</strong> để cào lại real-time nếu vừa thêm/xóa link.</li>
                                    </ul>
                                </div>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#c084fc', margin: '0 0 8px', fontSize: 14 }}>2. PBN Inlinks (Hệ Thống Trỏ Về):</h4>
                                <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                    Cột này thống kê xem <strong>có bao nhiêu site khác trong cùng hệ thống PBN đang đặt link trỏ về website này</strong>. Click vào badge để xem danh sách chi tiết các trang nguồn và từ khóa anchor text đang truyền sức mạnh SEO.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* SERVERS TAB GUIDE */}
                    {activeSection === 'servers' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Server size={18} color="#38bdf8" /> 4. Quản Lý Máy Chủ & Cấu Hình Cron Máy Con
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Quản trị kết nối SSH đến các VPS Linux (aaPanel) và Web Hosting (cPanel).
                                </p>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#38bdf8', margin: '0 0 8px', fontSize: 14 }}>Các Chức Năng Nổi Bật Trên Trang Máy Chủ:</h4>
                                    <ul style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                        <li><strong>+ Thêm Máy Chủ</strong>: Lưu thông tin Host/IP, Port SSH, User và Mật khẩu (hỗ trợ cả aaPanel VPS và cPanel).</li>
                                        <li><strong>Kiểm Tra Kết Nối</strong>: Ping SSH kiểm tra tài khoản có truy cập được vào máy chủ hay không.</li>
                                        <li><strong>Quét Sites</strong>: Tự động chạy lệnh quét hệ thống tập tin trên máy chủ để đếm chính xác số lượng thư mục WordPress vật lý (hiện có 1,140 site trên 10 server).</li>
                                        <li><strong>Upload mu-plugin Tất Cả</strong>: Đẩy tự động file <code>pbn-manager.php</code> vào thư mục <code>wp-content/mu-plugins/</code> của tất cả các site trên server.</li>
                                        <li><strong>Cloudflare API</strong>: Cấu hình kết nối API Cloudflare để lấy IP máy chủ thật của các domain đang bật proxy đám mây cam.</li>
                                    </ul>
                                </div>

                                <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: 16, borderRadius: 10, border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                                    <h4 style={{ color: '#38bdf8', margin: '0 0 6px', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Terminal size={15} /> Thiết Lập Cron Heartbeat Trên Máy Con:
                                    </h4>
                                    <p style={{ color: '#cbd5e1', fontSize: 13, margin: '0 0 10px' }}>
                                        Để các website con tự động ping báo trạng thái về Dashboard, bạn có thể thêm cron job trên máy con (hoặc vào mục <em>"Quản Lý Cron & Request Máy Con"</em> để xem hướng dẫn chi tiết):
                                    </p>
                                    <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: 6, border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <code style={{ color: '#38bdf8', fontSize: 12 }}>
                                            */15 * * * * curl -s -k "https://domain-con.com/?ttpp=atc=heartbeat" &gt;/dev/null 2&gt;&amp;1
                                        </code>
                                        <button className="btn btn-sm" onClick={() => copyCode('*/15 * * * * curl -s -k "https://domain-con.com/?ttpp=atc=heartbeat" >/dev/null 2>&1', 'cron1')}>
                                            {copiedSnippet === 'cron1' ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* AUDIT TAB GUIDE */}
                    {activeSection === 'audit' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <ShieldCheck size={18} color="#38bdf8" /> 5. Trung Tâm Audit Sức Khỏe, Nội Dung & Index
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Kiểm tra tự động đa luồng 4 lớp sức khỏe toàn diện cho hơn 2,600 website vệ tinh.
                                </p>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#38bdf8', margin: '0 0 8px', fontSize: 14 }}>4 Lớp Kiểm Tra Tự Động:</h4>
                                <ol style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                    <li><strong>Phân Giải DNS</strong>: Phát hiện tên miền chưa trỏ IP, sai Nameserver, hoặc trỏ nhầm về <code>127.0.0.1</code> (Loopback).</li>
                                    <li><strong>Kiểm Tra HTTP / Cloudflare</strong>: Bắt các mã lỗi mạng như <code>520-524</code> (Cloudflare timeout), <code>403</code> (Forbidden), <code>404</code> (Not Found), <code>500</code> (Server Error).</li>
                                    <li><strong>Nội Dung & Lỗi WordPress</strong>: Nhận diện lỗi rớt Database (<em>"Error establishing a database connection"</em>), lỗi PHP Fatal Error, hoặc trang mặc định chưa có web của cPanel / OpenLiteSpeed.</li>
                                    <li><strong>Soi Chặn Google Index (NoIndex)</strong>: Quét thẻ <code>&lt;meta name="robots" content="noindex"&gt;</code> để đảm bảo site PBN không bị vô tình chặn tìm kiếm.</li>
                                </ol>
                            </div>

                            <div style={{ background: 'rgba(52, 211, 153, 0.1)', padding: 16, borderRadius: 10, border: '1px solid rgba(52, 211, 153, 0.3)' }}>
                                <h4 style={{ color: '#34d399', margin: '0 0 6px', fontSize: 14 }}>Tính Năng 1-Click Fix NoIndex:</h4>
                                <p style={{ color: '#cbd5e1', fontSize: 13, margin: 0, lineHeight: 1.6 }}>
                                    Khi phát hiện các site bị dính NoIndex, bạn chỉ cần bấm nút <strong>"Mở Index (X sites)"</strong>, Dashboard sẽ tự động gửi lệnh điều khiển từ xa đến WordPress để chuyển <code>blog_public = 1</code> mà bạn không cần phải đăng nhập vào từng trang wp-admin bằng tay.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* BACKLINKS & CONTENT & USERS */}
                    {activeSection === 'backlinks' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Link2 size={18} color="#38bdf8" /> 6. Quản Lý Backlink & Money Site
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Theo dõi dòng chảy liên kết truyền về các trang kiếm tiền (Money Site).
                                </p>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#38bdf8', margin: '0 0 8px', fontSize: 14 }}>Chức Năng Gom Nhóm Báo Cáo:</h4>
                                <ul style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                    <li><strong>Nhóm theo Target URL</strong>: Xem một URL trang chủ hoặc bài viết của Money Site đang được bao nhiêu site PBN trỏ về.</li>
                                    <li><strong>Nhóm theo Anchor Text</strong>: Kiểm tra tỷ lệ từ khóa chính xác / từ khóa thương hiệu để tránh bị Google phạt tối ưu hóa quá liều (Over-optimization).</li>
                                    <li><strong>Thêm Backlink Nhanh</strong>: Chèn trực tiếp backlink vào bài viết WordPress qua API mà không cần mở website.</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {activeSection === 'content' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <FileText size={18} color="#38bdf8" /> 7. Quản Lý Bài Viết, AI Writer & Cấu Hình Persona
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Tự động hóa sản xuất nội dung vệ tinh chất lượng cao với văn phong chuyên nghiệp.
                                </p>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <h4 style={{ color: '#c084fc', margin: '0 0 8px', fontSize: 14 }}>Persona & Tone (Văn Phong Riêng Từng Site):</h4>
                                <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                    Trên bảng danh sách website, mỗi dòng có nút <strong>Persona</strong> màu tím. Bạn có thể cài đặt cho site đó đóng vai một chuyên gia cụ thể (VD: "Chuyên gia review bóng đá", "Kỹ sư công nghệ"). Khi AI Writer viết bài cho site này, nó sẽ tự động áp dụng đúng ngữ điệu và kiến thức của nhân vật đó.
                                </p>
                            </div>
                        </div>
                    )}

                    {activeSection === 'users' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Shield size={18} color="#38bdf8" /> 8. Quản Lý User WordPress & Đổi Mật Khẩu Khẩn Cấp
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Kiểm soát danh sách tài khoản Admin WordPress trên toàn bộ hệ thống từ một nơi duy nhất.
                                </p>
                            </div>

                            <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                <ul style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, margin: 0, paddingLeft: 20 }}>
                                    <li><strong>Quét Danh Sách User</strong>: Đọc trực tiếp danh sách tài khoản quản trị từ CSDL WordPress của máy con.</li>
                                    <li><strong>Đổi Mật Khẩu Khẩn Cấp</strong>: Đặt lại mật khẩu tài khoản Admin ngay từ Dashboard nếu bị quên hoặc nghi ngờ lộ bảo mật.</li>
                                    <li><strong>Tạo Tài Khoản Mới</strong>: Thêm nhanh user quản trị viên mới vào hàng chục website cùng một lúc.</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* FAQ SECTION */}
                    {activeSection === 'faq' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                            <div style={{ borderBottom: '1px solid #334155', paddingBottom: 12 }}>
                                <h3 style={{ fontSize: 18, color: '#f8fafc', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <HelpCircle size={18} color="#38bdf8" /> 9. Giải Đáp Các Câu Hỏi Thường Gặp (FAQs)
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
                                    Tổng hợp các câu hỏi thắc mắc phổ biến nhất khi vận hành hệ thống.
                                </p>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#fde047', margin: '0 0 6px', fontSize: 14 }}>
                                        Q1: Vì sao số lượng site trên Máy Chủ là 1,140 nhưng Tổng Số Site trên Dashboard là 2,648?
                                    </h4>
                                    <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                        <strong>Trả lời:</strong> Con số 1,140 là số <em>thư mục WordPress vật lý thực tế</em> cài đặt trên máy chủ. Con số 2,648 là tổng số <em>bản ghi tên miền</em> được lưu trong CSDL, vì hệ thống bao gồm: gần 900 cặp trùng lặp giữa <code>www.domain</code> và <code>domain</code>, 335 domain được cấu hình 301 Redirect sang site khác, và một số domain phụ / alias chưa map vào server ID.
                                    </p>
                                </div>

                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#fde047', margin: '0 0 6px', fontSize: 14 }}>
                                        Q2: Nếu hosting cPanel không có SSH thì làm sao cài đặt plugin kết nối?
                                    </h4>
                                    <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                        <strong>Trả lời:</strong> Bạn chỉ cần tải file <code>pbn-manager.php</code> và upload thủ công vào thư mục <code>/wp-content/mu-plugins/</code> của website đó qua File Manager hoặc FTP. Website sẽ ngay lập tức tự động nhận diện và gửi ping về Dashboard mà không cần kích hoạt trong trang quản trị.
                                    </p>
                                </div>

                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#fde047', margin: '0 0 6px', fontSize: 14 }}>
                                        Q3: Phiên đăng nhập trên Dashboard kéo dài bao lâu?
                                    </h4>
                                    <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                        <strong>Trả lời:</strong> Dashboard V2 sử dụng cơ chế bảo mật JWT Token lưu trữ với thời hạn <strong>7 ngày liên tục</strong>. Bạn không bị văng đăng nhập khi mở lại trình duyệt hoặc khi chuyển đổi giữa các tab.
                                    </p>
                                </div>

                                <div style={{ background: '#1e293b', padding: 16, borderRadius: 10, border: '1px solid #334155' }}>
                                    <h4 style={{ color: '#fde047', margin: '0 0 6px', fontSize: 14 }}>
                                        Q4: Khi nào nên bấm nút "Quét 301" trên Dashboard?
                                    </h4>
                                    <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                                        <strong>Trả lời:</strong> Hệ thống đã có cron tự động quét 2 ngày 1 lần. Bạn chỉ cần bấm nút này khi bạn vừa mua thêm một loạt domain mới và vừa cấu hình chuyển hướng 301 trên Cloudflare hoặc vhost, muốn hệ thống cập nhật kết quả ngay lập tức vào bảng.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}

