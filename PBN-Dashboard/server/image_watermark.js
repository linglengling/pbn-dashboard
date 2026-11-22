const sharp = require('sharp');
const db = require('./database');

/**
 * Downloads a buffer from a URL with timeout
 */
async function fetchBuffer(url) {
    try {
        const res = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            signal: AbortSignal.timeout(8000)
        });
        if (!res.ok) return null;
        const arrayBuffer = await res.arrayBuffer();
        return Buffer.from(arrayBuffer);
    } catch (e) {
        console.error(`fetchBuffer failed for ${url}:`, e.message);
        return null;
    }
}

/**
 * Stamps site logo/favicon onto an image buffer using Sharp
 */
async function watermarkBuffer(mainImageBuf, logoBuf) {
    try {
        const mainImg = sharp(mainImageBuf);
        const metadata = await mainImg.metadata();
        if (!metadata.width || !metadata.height) return mainImageBuf;

        // Resize logo to ~15-20% of main image width
        const targetLogoWidth = Math.max(30, Math.round(metadata.width * 0.18));
        const resizedLogo = await sharp(logoBuf)
            .resize({ width: targetLogoWidth })
            .ensureAlpha(0.8)
            .toBuffer();

        const logoMeta = await sharp(resizedLogo).metadata();
        const padding = 15;
        const left = Math.max(0, metadata.width - (logoMeta.width || targetLogoWidth) - padding);
        const top = Math.max(0, metadata.height - (logoMeta.height || targetLogoWidth) - padding);

        const watermarked = await mainImg
            .composite([{
                input: resizedLogo,
                top,
                left,
                blend: 'over'
            }])
            .toBuffer();

        return watermarked;
    } catch (e) {
        console.error('watermarkBuffer error:', e.message);
        return mainImageBuf;
    }
}

/**
 * Processes article HTML content: extracts <img src="...">, watermarks each image with site's logo,
 * uploads to WP Media Library via callWPApi, and replaces image URLs in HTML.
 */
async function processArticleImagesForSite(htmlContent, targetDomain, callWPApiFn) {
    if (!htmlContent || !targetDomain) return htmlContent;

    // Fetch site profile to get logo_url
    let logoUrl = '';
    try {
        const profile = await db.getSiteProfile(targetDomain);
        if (profile && profile.logo_url) {
            logoUrl = profile.logo_url;
        }
    } catch (e) {}

    if (!logoUrl) {
        logoUrl = `https://${targetDomain}/favicon.ico`;
    }

    // Extract image URLs
    const imgMatches = [...htmlContent.matchAll(/<img[^>]+src=["']([^"']+)["']/gi)];
    if (imgMatches.length === 0) return htmlContent;

    // Tải Logo Buffer
    let logoBuf = await fetchBuffer(logoUrl);
    if (!logoBuf) {
        // Fallback to Google Favicon service
        logoBuf = await fetchBuffer(`https://www.google.com/s2/favicons?domain=${targetDomain}&sz=128`);
    }

    if (!logoBuf) {
        console.log(`[Watermark] Could not load logo/favicon for ${targetDomain}, skipping watermark.`);
        return htmlContent;
    }

    let updatedHtml = htmlContent;
    const processedMap = new Map();

    for (const match of imgMatches) {
        const originalSrc = match[1];
        if (processedMap.has(originalSrc)) {
            updatedHtml = updatedHtml.replaceAll(originalSrc, processedMap.get(originalSrc));
            continue;
        }

        // Tải ảnh chính
        const mainBuf = await fetchBuffer(originalSrc);
        if (!mainBuf) continue;

        // Đóng dấu Watermark
        const wmBuf = await watermarkBuffer(mainBuf, logoBuf);
        const base64Data = wmBuf.toString('base64');
        const filename = `wm_${Date.now()}_${Math.random().toString(36).substring(2, 6)}.jpg`;

        // Upload lên WordPress Media Library
        try {
            const wpMediaRes = await callWPApiFn(targetDomain, '/pbn-mgr/v1/upload-media', 'POST', {
                filename,
                base64_data: base64Data
            });

            if (wpMediaRes && wpMediaRes.success && wpMediaRes.url) {
                processedMap.set(originalSrc, wpMediaRes.url);
                updatedHtml = updatedHtml.replaceAll(originalSrc, wpMediaRes.url);
                console.log(`[Watermark] Replaced image ${originalSrc.substring(0, 40)}... -> ${wpMediaRes.url}`);
            }
        } catch (uErr) {
            console.error(`[Watermark] Upload WP media failed for ${targetDomain}:`, uErr.message);
        }
    }

    return updatedHtml;
}

module.exports = {
    processArticleImagesForSite,
    watermarkBuffer
};
