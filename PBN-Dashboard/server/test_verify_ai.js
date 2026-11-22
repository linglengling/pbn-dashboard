const assert = require('assert');

// Test isAIRefusalOrInvalid logic
function isAIRefusalOrInvalid(text) {
    if (!text || text.trim().length < 200) {
        return { invalid: true, reason: 'Nội dung bài viết quá ngắn hoặc trống (< 200 ký tự).' };
    }

    const lower = text.toLowerCase();

    const refusalPatterns = [
        /xin lỗi[^\w\n]*,?\s*tôi (không thể|không giúp|không hỗ trợ|rất tiếc)/i,
        /tôi không thể (viết|tạo|cung cấp|hỗ trợ|quảng bá)/i,
        /tôi sẵn sàng hỗ trợ bạn với các nội dung khác/i,
        /bạn có muốn tôi giúp viết về một chủ đề khác/i,
        /không thể viết bài (seo|quảng bá)/i,
        /việc viết nội dung nhằm thu hút/i,
        /cá cược.*bất hợp pháp/i,
        /i'm sorry,?\s*i (cannot|can't|am unable)/i,
        /i cannot (fulfill|generate|create|write)/i,
        /as an ai language model/i,
        /against my (safety|content) polic/i,
        /unfortunate(ly)?,?\s*i cannot/i
    ];

    for (const pattern of refusalPatterns) {
        if (pattern.test(lower)) {
            const matchStr = lower.match(pattern)?.[0] || '';
            return { invalid: true, reason: `AI từ chối tạo nội dung ("${matchStr.trim()}")` };
        }
    }

    return { invalid: false };
}

// Case 1: Refusal example from user prompt
const refusalSample = `
Xin lỗi, tôi không thể viết bài SEO quảng bá cho nền tảng cá cược/đánh bạc trực tuyến như “dE88” hoặc hướng dẫn về trò chơi Tài Xỉu trong bối cảnh cờ bạc.
Việc viết nội dung nhằm thu hút người dùng tham gia vào các hoạt động cá cược trực tuyến có thể gây hại, đặc biệt khi cờ bạc trực tuyến là bất hợp pháp tại Việt Nam và có thể dẫn đến những hậu quả nghiêm trọng về tài chính, tâm lý và pháp lý.
Tôi sẵn sàng hỗ trợ bạn với các nội dung khác như:
– Bài viết về trò chơi dân gian Tài Xỉu trong văn hóa Việt Nam (không liên quan đến cá cược)
– Bài viết SEO về các chủ đề giải trí lành mạnh khác
– Nội dung về công nghệ, du lịch, ẩm thực, giáo dục…
Bạn có muốn tôi giúp viết về một chủ đề khác không?
`;

const res1 = isAIRefusalOrInvalid(refusalSample);
assert.strictEqual(res1.invalid, true, 'Should detect AI refusal sample');

// Case 2: Short output
const res2 = isAIRefusalOrInvalid('Too short content');
assert.strictEqual(res2.invalid, true, 'Should reject short text');

// Case 3: Valid article
const validArticle = `
<h1>Hướng Dẫn Chọn Nhà Cái Uy Tín Hàng Đầu năm 2026</h1>
<p>Nhà cái dE88 và các cổng game tài xỉu luôn thu hút sự quan tâm của nhiều người chơi đam mê giải trí trực tuyến. Để tham gia một cách an toàn và hiệu quả, việc lựa chọn thương hiệu uy tín là vô cùng quan trọng.</p>
<p>Bài viết này sẽ chia sẻ chi tiết về các tiêu chí đánh giá cổng game chất lượng, cách quản lý vốn thông minh và những kinh nghiệm quý báu giúp bạn nâng cao tỷ lệ chiến thắng trong từng ván chơi.</p>
<p>Hãy cùng khám phá chi tiết các bí quyết được các cao thủ lâu năm đúc kết ngay dưới đây để có được trải nghiệm tuyệt vời nhất nhé!</p>
`;

const res3 = isAIRefusalOrInvalid(validArticle);
assert.strictEqual(res3.invalid, false, 'Should accept valid article');

console.log('ALL VERIFICATION TESTS PASSED SUCCESSFULLY!');
