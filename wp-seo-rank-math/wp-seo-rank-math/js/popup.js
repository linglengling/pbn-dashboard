jQuery(document).ready(function($) {
    let popup = $('#nwm-popup');
    if (!popup.length) return;

    let cookieEnabled = popup.data('cookie') !== 'false';
    let targetUrl = popup.data('target');

    // Kiểm tra cookie nếu bật cookie
    if (cookieEnabled && document.cookie.indexOf('nwm_popup_closed=true') > -1) {
        return;
    }

    popup.fadeIn();

    // Nếu có target, click vào popup sẽ chuyển hướng
    if (targetUrl) {
        popup.css('cursor', 'pointer');
        popup.on('click', function(e) {
            // Nếu click vào nút đóng thì không redirect
            if (!$(e.target).hasClass('nwm-close')) {
                window.location.href = targetUrl;
            }
        });
    }

    $('.nwm-close').on('click', function(e) {
        e.stopPropagation(); // Ngăn chặn click vào close cũng redirect
        popup.fadeOut();
        if (cookieEnabled) {
            let date = new Date();
            date.setTime(date.getTime() + (10 * 60 * 1000)); // 10 phút
            document.cookie = "nwm_popup_closed=true; expires=" + date.toUTCString() + "; path=/";
        }
    });
});
