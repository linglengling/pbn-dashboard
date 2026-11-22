<?php
/**
 * Plugin Name: PBN Site Manager
 * Description: Quản lý website WordPress từ Dashboard trung tâm. Gửi heartbeat, nhận lệnh qua REST API.
 * Version: 1.0.0
 * Author: PBN Manager
 */

if (!defined('ABSPATH'))
    exit;

// ============================================================
// CẤU HÌNH — Thay đổi theo hệ thống của bạn
// ============================================================
if (!defined('PBN_DASHBOARD_DOMAIN')) define('PBN_DASHBOARD_DOMAIN', 'pbn.keodinh.net');             // Domain Dashboard trung tâm
if (!defined('PBN_DASHBOARD_IP')) define('PBN_DASHBOARD_IP', '103.106.105.77');                  // IP VPS trực tiếp (cho socket WebSocket port 9090)
if (!defined('PBN_DASHBOARD_PORT')) define('PBN_DASHBOARD_PORT', 9090);                            // Port WebSocket trên Dashboard
if (!defined('PBN_SECRET_SALT')) define('PBN_SECRET_SALT', 'pbn_s3cr3t_k3y_2024_change_this'); // Phải trùng với .env trên server
if (!defined('PBN_API_KEY')) define('PBN_API_KEY', 'change_this_api_key_per_site');         // API key riêng cho site này
if (!defined('PBN_HEARTBEAT_INTERVAL')) define('PBN_HEARTBEAT_INTERVAL', 300);                          // 5 phút (giây)
if (!defined('PBN_CLUSTER')) define('PBN_CLUSTER', 'default');                              // Tên cụm (cluster) của site này

// ============================================================
// 1. HEARTBEAT & PING — Gửi tín hiệu online và IP máy chủ về Dashboard
// ============================================================

/**
 * Tự động xác định chính xác IP máy chủ thật (Server IP) của site con
 */
function pbn_get_server_ip()
{
    // 1. Kiểm tra SERVER_ADDR từ Web server
    if (!empty($_SERVER['SERVER_ADDR']) && filter_var($_SERVER['SERVER_ADDR'], FILTER_VALIDATE_IP)) {
        if (!in_array($_SERVER['SERVER_ADDR'], array('127.0.0.1', '::1', '0.0.0.0'))) {
            return $_SERVER['SERVER_ADDR'];
        }
    }
    // 2. Kiểm tra qua hostname hệ thống
    $hostname = @gethostname();
    if ($hostname) {
        $host_ip = @gethostbyname($hostname);
        if (!empty($host_ip) && $host_ip !== $hostname && filter_var($host_ip, FILTER_VALIDATE_IP)) {
            if (!in_array($host_ip, array('127.0.0.1', '::1', '0.0.0.0'))) {
                return $host_ip;
            }
        }
    }
    // 3. Fallback: cache transient để không gọi external API liên tục
    $cached_ip = get_transient('pbn_cached_server_ip');
    if ($cached_ip && filter_var($cached_ip, FILTER_VALIDATE_IP)) {
        return $cached_ip;
    }
    // Lấy IP từ service bên ngoài (timeout ngắn 2s)
    $res = wp_remote_get('https://api.ipify.org', array('timeout' => 2, 'sslverify' => false));
    if (!is_wp_error($res) && wp_remote_retrieve_response_code($res) === 200) {
        $external_ip = trim(wp_remote_retrieve_body($res));
        if (filter_var($external_ip, FILTER_VALIDATE_IP)) {
            set_transient('pbn_cached_server_ip', $external_ip, 86400); // Lưu cache 24h
            return $external_ip;
        }
    }
    return !empty($_SERVER['SERVER_ADDR']) ? $_SERVER['SERVER_ADDR'] : '127.0.0.1';
}

add_action('init', 'pbn_heartbeat_init');

function pbn_heartbeat_init()
{
    // Hỗ trợ trigger ping trực tiếp qua URL: ?pbn_ping=now hoặc ?force_pbn_heartbeat=1
    if (isset($_GET['pbn_ping']) && $_GET['pbn_ping'] === 'now') {
        pbn_trigger_ping(true);
        exit;
    }

    if (isset($_GET['force_pbn_heartbeat'])) {
        delete_transient('pbn_heartbeat_lock');
    }
    // Rate-limit bằng Transient: chỉ gửi 1 lần mỗi PBN_HEARTBEAT_INTERVAL giây
    if (get_transient('pbn_heartbeat_lock'))
        return;
    set_transient('pbn_heartbeat_lock', 1, PBN_HEARTBEAT_INTERVAL);

    // Chạy heartbeat chạy ngầm sau khi trang đã render xong cho khách (0ms delay)
    if (function_exists('fastcgi_finish_request')) {
        register_shutdown_function(function() {
            @fastcgi_finish_request();
            pbn_send_heartbeat();
        });
    } else {
        register_shutdown_function('pbn_send_heartbeat');
    }
}

function pbn_send_heartbeat($return_details = false)
{
    $domain = isset($_SERVER['HTTP_HOST']) ? sanitize_text_field($_SERVER['HTTP_HOST']) : parse_url(site_url(), PHP_URL_HOST);
    $domain = preg_replace('/:\d+$/', '', $domain); // Loại bỏ port nếu có
    $timestamp = time();
    $token = md5($domain . $timestamp . PBN_SECRET_SALT);
    $server_ip = pbn_get_server_ip();

    // Đếm tổng số link out trên trang chủ (bỏ qua link nội bộ, link không có a tag, v.v...)
    $total_homepage_links = 0;
    $homepage_outbound_links = array();
    $home_url = add_query_arg('pbn_nocache', time(), home_url('/'));
    $response = wp_remote_get($home_url, array(
        'timeout' => 5,
        'sslverify' => false,
        'headers' => array(
            'User-Agent' => 'PBN-Link-Checker/1.0',
            'Cache-Control' => 'no-cache, no-store, must-revalidate',
            'Pragma' => 'no-cache'
        )
    ));
    if (!is_wp_error($response)) {
        $html = wp_remote_retrieve_body($response);
        if (!empty($html)) {
            // Lấy host của domain hiện tại để nhận dạng link nội bộ
            $domain_host = parse_url(site_url(), PHP_URL_HOST);
            $domain_clean = preg_replace('/^www\./i', '', $domain_host);

            preg_match_all('/<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)<\/a>/is', $html, $matches, PREG_SET_ORDER);
            foreach ($matches as $match) {
                $url = trim($match[1]);
                $anchor = trim(strip_tags($match[2]));

                $url_host = parse_url($url, PHP_URL_HOST);
                if (empty($url_host)) {
                    // Link tương đối, được coi là link nội bộ
                    continue;
                }

                $url_clean = preg_replace('/^www\./i', '', $url_host);
                if (strcasecmp($domain_clean, $url_clean) !== 0) {
                    // Đây là outbound link
                    $homepage_outbound_links[] = array(
                        'url' => esc_url_raw($url),
                        'anchor' => $anchor ? $anchor : '[No Anchor]'
                    );
                }
            }
            $total_homepage_links = count($homepage_outbound_links);
        }
    }

    $payload_data = array(
        'action' => 'heartbeat',
        'domain' => $domain,
        'timestamp' => $timestamp,
        'token' => $token,
        'cluster' => PBN_CLUSTER,
        'site_url' => site_url(),
        'api_key' => PBN_API_KEY,
        'server_ip' => $server_ip,
        'total_homepage_links' => $total_homepage_links,
        'homepage_outbound_links' => $homepage_outbound_links,
        'head_code' => get_option('pbn_head_code', ''),
    );
    $payload = json_encode($payload_data);

    $sent = false;
    $method = '';
    $sent = false;
    $method = '';
    $dash_response = null;

    // 1. Gửi ping chính thức qua HTTPS REST API tới domain Dashboard: https://pbn.keodinh.net/api/sites/ping
    $dash_domain = defined('PBN_DASHBOARD_DOMAIN') ? PBN_DASHBOARD_DOMAIN : 'pbn.keodinh.net';
    $http_url = 'https://' . $dash_domain . '/api/sites/ping';
    $http_res = wp_remote_post($http_url, array(
        'timeout' => 4,
        'sslverify' => false,
        'headers' => array('Content-Type' => 'application/json'),
        'body' => $payload,
    ));
    if (!is_wp_error($http_res) && wp_remote_retrieve_response_code($http_res) === 200) {
        $sent = true;
        $method = 'https_domain';
        $dash_response = json_decode(wp_remote_retrieve_body($http_res), true);
    } else {
        // Thử lại qua HTTP thông thường nếu HTTPS có vấn đề
        $http_url_plain = 'http://' . $dash_domain . '/api/sites/ping';
        $http_res_plain = wp_remote_post($http_url_plain, array(
            'timeout' => 4,
            'sslverify' => false,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => $payload,
        ));
        if (!is_wp_error($http_res_plain) && wp_remote_retrieve_response_code($http_res_plain) === 200) {
            $sent = true;
            $method = 'http_domain';
            $dash_response = json_decode(wp_remote_retrieve_body($http_res_plain), true);
        }
    }

    // 2. Dự phòng: Nếu gửi qua HTTP domain không được, thử kết nối trực tiếp qua raw WebSocket socket TCP
    if (!$sent && defined('PBN_DASHBOARD_IP') && defined('PBN_DASHBOARD_PORT')) {
        $prev_error = error_reporting(0);
        $fp = @fsockopen(PBN_DASHBOARD_IP, PBN_DASHBOARD_PORT, $errno, $errstr, 0.5);

        if ($fp) {
            // WebSocket Handshake
            $key = base64_encode(random_bytes(16));
            $host = PBN_DASHBOARD_IP . ':' . PBN_DASHBOARD_PORT;

            $handshake = "GET / HTTP/1.1\r\n";
            $handshake .= "Host: {$host}\r\n";
            $handshake .= "Upgrade: websocket\r\n";
            $handshake .= "Connection: Upgrade\r\n";
            $handshake .= "Sec-WebSocket-Key: {$key}\r\n";
            $handshake .= "Sec-WebSocket-Version: 13\r\n\r\n";

            @fwrite($fp, $handshake);
            @stream_set_timeout($fp, 0, 500000); // 0.5s timeout cho read
            @fread($fp, 2048);

            // Gửi WebSocket frame
            $len = strlen($payload);
            $mask = random_bytes(4);
            $masked = '';
            for ($i = 0; $i < $len; $i++) {
                $masked .= $payload[$i] ^ $mask[$i % 4];
            }

            // Frame header
            $frame = chr(0x81); // FIN + Text opcode
            if ($len < 126) {
                $frame .= chr($len | 0x80); // Masked + length
            } elseif ($len < 65536) {
                $frame .= chr(126 | 0x80) . pack('n', $len);
            }
            $frame .= $mask . $masked;

            @fwrite($fp, $frame);
            @fclose($fp);
            $sent = true;
            $method = 'websocket';
        }
        error_reporting($prev_error);
    }

    if ($return_details) {
        return array(
            'success' => $sent,
            'domain' => $domain,
            'server_ip' => $server_ip,
            'cluster' => PBN_CLUSTER,
            'method' => $method ?: 'none',
            'dashboard_response' => $dash_response,
            'message' => $sent ? 'Ping gửi tới Dashboard ' . (defined('PBN_DASHBOARD_DOMAIN') ? PBN_DASHBOARD_DOMAIN : '') . ' thành công!' : 'Không thể kết nối tới Dashboard qua domain ' . (defined('PBN_DASHBOARD_DOMAIN') ? PBN_DASHBOARD_DOMAIN : '') . ' và WebSocket port ' . PBN_DASHBOARD_PORT,
        );
    }
}

/**
 * Function kích hoạt ping Dashboard ngay lập tức dành cho AI Agent hoặc WP-CLI/Script setup
 * 
 * Cách dùng:
 * 1. AI Agent gọi trong PHP / WP: pbn_trigger_ping(true);
 * 2. WP-CLI: wp pbn ping
 * 3. URL kiểm tra: https://site.com/?pbn_ping=now
 * 4. REST route: /wp-json/pbn-mgr/v1/trigger-ping
 */
function pbn_trigger_ping($echo_output = false)
{
    delete_transient('pbn_heartbeat_lock');
    $result = pbn_send_heartbeat(true);

    if ($echo_output) {
        if (defined('WP_CLI') && WP_CLI) {
            if (!empty($result['success'])) {
                WP_CLI::success(sprintf(
                    "Ping Dashboard thành công! [Domain: %s] [Server IP: %s] [Method: %s]",
                    $result['domain'],
                    $result['server_ip'],
                    $result['method']
                ));
            } else {
                WP_CLI::error(sprintf("Ping thất bại: %s", $result['message']));
            }
        } else {
            if (!headers_sent()) {
                header('Content-Type: application/json; charset=utf-8');
            }
            echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        }
    }

    return $result;
}

// Đăng ký lệnh WP-CLI cho AI Agent: `wp pbn ping`
if (defined('WP_CLI') && WP_CLI) {
    WP_CLI::add_command('pbn ping', function ($args, $assoc_args) {
        pbn_trigger_ping(true);
    });
}

// ============================================================
// 2. THEO DÕI ĐỔI DOMAIN — Gửi heartbeat ngay khi domain thay đổi
// ============================================================
add_action('update_option_siteurl', 'pbn_domain_changed', 10, 2);
add_action('update_option_home', 'pbn_domain_changed', 10, 2);

function pbn_domain_changed($old_value, $new_value)
{
    if ($old_value !== $new_value) {
        delete_transient('pbn_heartbeat_lock'); // Reset rate-limit
        pbn_send_heartbeat();
    }
}

// ============================================================
// 3. REST API ENDPOINTS — Nhận lệnh từ Dashboard Server
// ============================================================
add_action('rest_api_init', 'pbn_register_rest_routes');

function pbn_register_rest_routes()
{
    $namespace = 'pbn-mgr/v1';

    // Đăng bài mới
    register_rest_route($namespace, '/post', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_create_post',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Cập nhật bài viết (freshness / chèn thêm nội dung)
    register_rest_route($namespace, '/update-post', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_update_post',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Chèn backlink
    register_rest_route($namespace, '/insert-link', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_insert_link',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Gỡ backlink
    register_rest_route($namespace, '/remove-links', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_remove_links',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Kill Switch — xóa toàn bộ backlink
    register_rest_route($namespace, '/kill-switch', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_kill_switch',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Xóa bài viết
    register_rest_route($namespace, '/delete-post', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_delete_post',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Lấy thông tin site
    register_rest_route($namespace, '/status', array(
        'methods' => 'GET',
        'callback' => 'pbn_api_status',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Cập nhật mã chèn vào Head (Schema, Pixel, v.v...)
    register_rest_route($namespace, '/update-head', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_update_head',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Upload Media / Watermarked Images
    register_rest_route($namespace, '/upload-media', array(
        'methods' => 'POST',
        'callback' => 'pbn_api_upload_media',
        'permission_callback' => 'pbn_verify_dashboard_request',
    ));

    // Debug Headers
    register_rest_route($namespace, '/debug-headers', array(
        'methods' => 'POST',
        'callback' => function($request) {
            return new WP_REST_Response(array(
                'headers' => $request->get_headers(),
                'token_header' => $request->get_header('x_pbn_token'),
                'token_server' => $_SERVER['HTTP_X_PBN_TOKEN'] ?? 'NONE'
            ), 200);
        },
        'permission_callback' => '__return_true',
    ));

    // Kích hoạt Ping tức thì (dành cho AI Agent / Monitoring trigger)
    register_rest_route($namespace, '/trigger-ping', array(
        'methods' => array('GET', 'POST'),
        'callback' => function($request) {
            $res = pbn_trigger_ping(false);
            return new WP_REST_Response($res, 200);
        },
        'permission_callback' => '__return_true',
    ));
}

// Whitelist route pbn-mgr trong All In One WP Security (AIOS) Firewall
add_filter('aios_whitelisted_rest_routes', function($routes) {
    if (!is_array($routes)) $routes = array();
    $routes[] = 'pbn-mgr';
    return $routes;
});

// Bỏ qua các plugin firewall (như All In One WP Security) đối với các request REST API có PBN signature hợp lệ
add_filter('rest_authentication_errors', 'pbn_bypass_firewall_for_valid_requests', 1);
function pbn_bypass_firewall_for_valid_requests($errors)
{
    $token = isset($_SERVER['HTTP_X_PBN_TOKEN']) ? $_SERVER['HTTP_X_PBN_TOKEN'] : (isset($_REQUEST['pbn_token']) ? $_REQUEST['pbn_token'] : '');
    $timestamp = isset($_SERVER['HTTP_X_PBN_TIMESTAMP']) ? $_SERVER['HTTP_X_PBN_TIMESTAMP'] : (isset($_REQUEST['pbn_timestamp']) ? $_REQUEST['pbn_timestamp'] : '');

    if (!empty($token) && !empty($timestamp)) {
        if (abs(time() - intval($timestamp)) <= 600) {
            return true; // Cho phép bypass bẫy firewall của All In One WP Security / Wordfence
        }
    }
    return $errors;
}

// Xác thực yêu cầu từ Dashboard bằng chữ ký dựa trên SECRET_SALT
function pbn_verify_dashboard_request($request)
{
    $token = $request->get_header('X-PBN-Token');
    if (empty($token) && isset($_SERVER['HTTP_X_PBN_TOKEN'])) {
        $token = $_SERVER['HTTP_X_PBN_TOKEN'];
    }
    if (empty($token)) {
        $token = $request->get_param('pbn_token');
    }

    $timestamp = $request->get_header('X-PBN-Timestamp');
    if (empty($timestamp) && isset($_SERVER['HTTP_X_PBN_TIMESTAMP'])) {
        $timestamp = $_SERVER['HTTP_X_PBN_TIMESTAMP'];
    }
    if (empty($timestamp)) {
        $timestamp = $request->get_param('pbn_timestamp');
    }

    if (empty($token) || empty($timestamp)) {
        return false;
    }

    // Cho phép lệch thời gian tối đa 10 phút để tránh lệch múi giờ/đồng hồ server
    if (abs(time() - intval($timestamp)) > 600) {
        return false;
    }

    $route = '/' . ltrim($request->get_route(), '/');
    $expected1 = md5($route . $timestamp . PBN_SECRET_SALT);
    $expected2 = md5(ltrim($route, '/') . $timestamp . PBN_SECRET_SALT);

    return (hash_equals($expected1, strtolower($token)) || hash_equals($expected2, strtolower($token)));
}

// API: Cập nhật mã chèn vào Head
function pbn_api_update_head($request)
{
    $params = $request->get_json_params();
    $head_code = isset($params['head_code']) ? $params['head_code'] : '';

    update_option('pbn_head_code', $head_code);

    return new WP_REST_Response(array(
        'success' => true,
        'message' => 'Head code updated successfully'
    ));
}

// Hook chèn code vào thẻ <head> của WordPress
add_action('wp_head', 'pbn_output_head_code', 100);
function pbn_output_head_code()
{
    $code = get_option('pbn_head_code', '');
    if (!empty($code)) {
        echo $code . "\n";
    }
}

// ============================================================
// 3a. API: Đăng bài mới
// ============================================================
function pbn_api_create_post($request)
{
    $params = $request->get_json_params();
    $title = sanitize_text_field($params['title'] ?? '');
    $content = wp_kses_post($params['content'] ?? '');
    $status = sanitize_text_field($params['status'] ?? 'publish');

    if (empty($title) || empty($content)) {
        return new WP_REST_Response(array('success' => false, 'error' => 'title and content required'), 400);
    }

    // Tự động tải hình ảnh ngoại về media library và đổi tên ngẫu nhiên
    $content = pbn_sideload_images($content);

    $post_id = wp_insert_post(array(
        'post_title' => $title,
        'post_content' => $content,
        'post_status' => $status,
        'post_type' => 'post',
    ));

    if (is_wp_error($post_id)) {
        return new WP_REST_Response(array('success' => false, 'error' => $post_id->get_error_message()), 500);
    }

    return new WP_REST_Response(array(
        'success' => true,
        'post_id' => $post_id,
        'url' => get_permalink($post_id),
    ));
}

// ============================================================
// 3b. API: Cập nhật bài viết (Auto-Freshness)
// ============================================================
function pbn_api_update_post($request)
{
    $params = $request->get_json_params();
    $post_id = intval($params['post_id'] ?? 0);
    $append_content = wp_kses_post($params['append_content'] ?? '');
    $update_date = $params['update_date'] ?? true;

    if (!$post_id) {
        return new WP_REST_Response(array('success' => false, 'error' => 'post_id required'), 400);
    }

    $post = get_post($post_id);
    if (!$post) {
        return new WP_REST_Response(array('success' => false, 'error' => 'Post not found'), 404);
    }

    $update_data = array('ID' => $post_id);

    // Chèn thêm nội dung vào cuối bài viết
    if (!empty($append_content)) {
        // Tự động tải hình ảnh ngoại về media library và đổi tên ngẫu nhiên
        $append_content = pbn_sideload_images($append_content);
        $update_data['post_content'] = $post->post_content . "\n\n" . $append_content;
    }

    // Cập nhật ngày sửa đổi (freshness)
    if ($update_date) {
        $update_data['post_modified'] = current_time('mysql');
        $update_data['post_modified_gmt'] = current_time('mysql', 1);
    }

    $result = wp_update_post($update_data);
    if (is_wp_error($result)) {
        return new WP_REST_Response(array('success' => false, 'error' => $result->get_error_message()), 500);
    }

    return new WP_REST_Response(array('success' => true, 'post_id' => $post_id));
}

// ============================================================
// 3b-2. API: Xóa bài viết khỏi WordPress
// ============================================================
function pbn_api_delete_post($request)
{
    $params = $request->get_json_params();
    $post_id = intval($params['post_id'] ?? 0);

    if (!$post_id) {
        return new WP_REST_Response(array('success' => false, 'error' => 'post_id required'), 400);
    }

    $deleted = wp_delete_post($post_id, true); // true = xóa vĩnh viễn
    if (!$deleted) {
        return new WP_REST_Response(array('success' => false, 'error' => 'Failed to delete post or post not found'), 404);
    }

    delete_transient('pbn_heartbeat_lock');
    pbn_send_heartbeat();

    return new WP_REST_Response(array(
        'success' => true,
        'post_id' => $post_id,
        'message' => "Post #{$post_id} deleted successfully"
    ));
}

// ============================================================
// 3c. API: Chèn backlink vào bài viết
// ============================================================
function pbn_api_insert_link($request)
{
    $params = $request->get_json_params();
    $link_html = $params['link_html'] ?? '';
    $location = sanitize_text_field($params['location'] ?? 'post');
    $post_id = intval($params['post_id'] ?? 0);

    if (empty($link_html)) {
        $target_url = esc_url_raw($params['target_url'] ?? '');
        $anchor_text = sanitize_text_field($params['anchor_text'] ?? '');
        if (empty($target_url) || empty($anchor_text)) {
            return new WP_REST_Response(array('success' => false, 'error' => 'link_html or target_url + anchor_text required'), 400);
        }
        $link_html = '<p><a href="' . esc_url($target_url) . '">' . esc_html($anchor_text) . '</a></p>';
    } else {
        // Track các link chèn từ HTML để Kill Switch hoạt động tốt
        preg_match_all('/<a[^>]+href=["\']([^"\']+)["\']/i', $link_html, $url_matches);
        if (!empty($url_matches[1])) {
            $managed = get_option('pbn_managed_urls', array());
            foreach ($url_matches[1] as $url) {
                $url_raw = esc_url_raw($url);
                if (!empty($url_raw) && !in_array($url_raw, $managed)) {
                    $managed[] = $url_raw;
                }
            }
            update_option('pbn_managed_urls', $managed);
        }
    }

    if ($location === 'homepage' || $location === 'footer') {
        // Lưu vào option để hook vào wp_footer/wp_head hiển thị trên homepage
        $links = get_option('pbn_homepage_links', array());
        $links[] = array(
            'html' => $link_html,
            'added_at' => current_time('mysql'),
        );
        update_option('pbn_homepage_links', $links);
        return new WP_REST_Response(array('success' => true, 'location' => $location));
    }

    if ($location === 'homepage_post') {
        $post_id = 0;
        if (get_option('show_on_front') === 'page') {
            $post_id = intval(get_option('page_on_front'));
        }

        if ($post_id) {
            $post = get_post($post_id);
            if ($post) {
                $new_content = $post->post_content . "\n\n" . $link_html;
                wp_update_post(array('ID' => $post_id, 'post_content' => $new_content));
                return new WP_REST_Response(array('success' => true, 'post_id' => $post_id, 'location' => 'homepage_post'));
            }
        }
        return new WP_REST_Response(array('success' => false, 'error' => 'Homepage static page not configured on this site'), 400);
    }

    // Chèn vào bài viết cụ thể
    if ($post_id) {
        $post = get_post($post_id);
        if (!$post) {
            return new WP_REST_Response(array('success' => false, 'error' => 'Post not found'), 404);
        }
        $new_content = $post->post_content . "\n\n" . $link_html;
        wp_update_post(array('ID' => $post_id, 'post_content' => $new_content));
        return new WP_REST_Response(array('success' => true, 'post_id' => $post_id));
    }

    // Nếu không chỉ định post_id, chèn vào bài viết mới nhất
    $latest = get_posts(array('numberposts' => 1, 'post_type' => 'post', 'post_status' => 'publish'));
    if (!empty($latest)) {
        $post = $latest[0];
        $new_content = $post->post_content . "\n\n" . $link_html;
        wp_update_post(array('ID' => $post->ID, 'post_content' => $new_content));
        return new WP_REST_Response(array('success' => true, 'post_id' => $post->ID));
    }

    return new WP_REST_Response(array('success' => false, 'error' => 'No posts found'), 404);
}

// ============================================================
// 3d. API: Gỡ backlink theo target URL
// ============================================================
function pbn_api_remove_links($request)
{
    $params = $request->get_json_params();
    $target_url = esc_url_raw($params['target_url'] ?? '');
    $paragraph_html = $params['paragraph_html'] ?? '';

    if (empty($target_url)) {
        return new WP_REST_Response(array('success' => false, 'error' => 'target_url required'), 400);
    }

    $removed_count = 0;

    // Gỡ từ homepage links
    $links = get_option('pbn_homepage_links', array());
    $filtered = array_filter($links, function ($link) use ($target_url) {
        return strpos($link['html'], $target_url) === false;
    });
    if (count($filtered) !== count($links)) {
        update_option('pbn_homepage_links', array_values($filtered));
        $removed_count += count($links) - count($filtered);
    }

    // Gỡ từ nội dung tất cả bài viết chứa URL đó
    global $wpdb;
    $posts_with_link = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT ID, post_content FROM {$wpdb->posts} WHERE (post_content LIKE %s OR (%s != '' AND post_content LIKE %s)) AND post_type IN ('post', 'page')",
            '%' . $wpdb->esc_like($target_url) . '%',
            $paragraph_html,
            '%' . $wpdb->esc_like(strip_tags($paragraph_html)) . '%'
        )
    );

    foreach ($posts_with_link as $post) {
        $cleaned = $post->post_content;

        // Nếu có truyền paragraph_html, hãy thử xóa toàn bộ đoạn văn trước
        if (!empty($paragraph_html)) {
            $cleaned = str_replace($paragraph_html, '', $post->post_content);

            // Nếu không xóa được chính xác, thử chuẩn hóa khoảng trắng/dòng mới
            if ($cleaned === $post->post_content) {
                $escaped = preg_quote($paragraph_html, '/');
                $pattern = preg_replace('/\s+/', '\s*', $escaped);
                $pattern = '/\s*' . $pattern . '\s*/is';
                $cleaned = preg_replace($pattern, '', $post->post_content);
            }
        }

        // Nếu chưa thay đổi hoặc không có paragraph_html, giải phóng tag <a> và giữ lại anchor text
        if ($cleaned === $post->post_content) {
            $pattern = '/<a[^>]+href=["\']' . preg_quote($target_url, '/') . '["\'][^>]*>(.*?)<\/a>/is';
            $cleaned = preg_replace($pattern, '$1', $post->post_content);
        }

        if ($cleaned !== $post->post_content) {
            wp_update_post(array('ID' => $post->ID, 'post_content' => $cleaned));
            $removed_count++;
        }
    }

    // Kích hoạt ngay Heartbeat mới để cập nhật Dashboard tức thì
    delete_transient('pbn_heartbeat_lock');
    pbn_send_heartbeat();

    return new WP_REST_Response(array('success' => true, 'removed_count' => $removed_count));
}

// ============================================================
// 3e. API: Kill Switch — Xóa TẤT CẢ backlink được quản lý
// ============================================================
function pbn_api_kill_switch($request)
{
    $removed_count = 0;

    // Xóa homepage links
    $links = get_option('pbn_homepage_links', array());
    if (!empty($links)) {
        $removed_count += count($links);
        update_option('pbn_homepage_links', array());
    }

    // Quét tất cả bài viết và gỡ mọi link chỉ tới Money Site URLs đã lưu
    // Tìm tất cả bài viết có chứa thẻ <a> với href bắt đầu bằng http
    global $wpdb;
    $all_posts = $wpdb->get_results(
        "SELECT ID, post_content FROM {$wpdb->posts} WHERE post_type = 'post' AND post_content LIKE '%<a %'"
    );

    // Lấy danh sách tất cả target URLs đã từng được chèn (lưu trong option)
    $managed_urls = get_option('pbn_managed_urls', array());

    foreach ($all_posts as $post) {
        $changed = false;
        $content = $post->post_content;
        foreach ($managed_urls as $url) {
            $pattern = '/<a[^>]*href=["\']' . preg_quote($url, '/') . '["\'][^>]*>(.*?)<\/a>/is';
            $new_content = preg_replace($pattern, '$1', $content);
            if ($new_content !== $content) {
                $content = $new_content;
                $changed = true;
                $removed_count++;
            }
        }
        if ($changed) {
            wp_update_post(array('ID' => $post->ID, 'post_content' => $content));
        }
    }

    // Xóa option lưu trữ
    update_option('pbn_managed_urls', array());

    // Kích hoạt ngay Heartbeat mới để cập nhật Dashboard tức thì
    delete_transient('pbn_heartbeat_lock');
    pbn_send_heartbeat();

    return new WP_REST_Response(array('success' => true, 'removed_count' => $removed_count));
}

// ============================================================
// 3f. API: Lấy thông tin site
// ============================================================
function pbn_api_status($request)
{
    global $wp_version;
    return new WP_REST_Response(array(
        'success' => true,
        'domain' => isset($_SERVER['HTTP_HOST']) ? sanitize_text_field($_SERVER['HTTP_HOST']) : '',
        'site_url' => site_url(),
        'wp_version' => $wp_version,
        'php_version' => phpversion(),
        'post_count' => wp_count_posts()->publish,
        'theme' => get_stylesheet(),
        'plugins' => array_keys(get_plugins()),
    ));
}

// ============================================================
// 4. HOMEPAGE LINK OUTPUT — Hiển thị backlink đã chèn vào homepage
// ============================================================
add_action('wp_footer', 'pbn_output_homepage_links');

function pbn_output_homepage_links()
{
    if (!is_front_page() && !is_home())
        return;

    $links = get_option('pbn_homepage_links', array());
    if (empty($links))
        return;

    echo '<div class="pbn-links" style="margin:20px 0;font-size:14px;">';
    foreach ($links as $link) {
        echo $link['html'] . "\n";
    }
    echo '</div>';
}

// ============================================================
// 5. THEO DÕI MANAGED URLS — Lưu lại mọi URL đã chèn để Kill Switch dùng
// ============================================================
add_action('rest_api_init', function () {
    // Hook thêm: mỗi khi chèn link, lưu URL vào managed list
    add_filter('rest_post_dispatch', 'pbn_track_managed_urls', 10, 3);
});

function pbn_track_managed_urls($response, $server, $request)
{
    if (strpos($request->get_route(), '/pbn-mgr/v1/insert-link') !== false && $request->get_method() === 'POST') {
        $params = $request->get_json_params();
        $target_url = $params['target_url'] ?? '';
        if (!empty($target_url)) {
            $managed = get_option('pbn_managed_urls', array());
            if (!in_array($target_url, $managed)) {
                $managed[] = $target_url;
                update_option('pbn_managed_urls', $managed);
            }
        }
    }
    return $response;
}

// ============================================================
// 6. IMAGE SIDELOADER — Tải ảnh ngoại và đổi tên ngẫu nhiên
// ============================================================
function pbn_sideload_images($content)
{
    if (empty($content))
        return $content;

    // Tìm tất cả thẻ img src
    preg_match_all('/<img[^>]+src="([^">]+)"/i', $content, $matches);
    if (empty($matches[1]))
        return $content;

    require_once(ABSPATH . 'wp-admin/includes/image.php');
    require_once(ABSPATH . 'wp-admin/includes/file.php');
    require_once(ABSPATH . 'wp-admin/includes/media.php');

    $processed_urls = array();

    foreach ($matches[1] as $url) {
        if (isset($processed_urls[$url]))
            continue;

        // Bỏ qua nếu là hình ảnh thuộc domain hiện tại
        $site_url = site_url();
        $site_host = parse_url($site_url, PHP_URL_HOST);
        $img_host = parse_url($url, PHP_URL_HOST);

        if (empty($img_host) || strcasecmp($site_host, $img_host) === 0) {
            continue;
        }

        // Tải ảnh về thư mục tạm
        $tmp = download_url($url);
        if (is_wp_error($tmp))
            continue;

        // Lấy định dạng ảnh
        $path_info = pathinfo(parse_url($url, PHP_URL_PATH));
        $ext = isset($path_info['extension']) ? $path_info['extension'] : 'jpg';
        $ext = preg_replace('/[^a-zA-Z0-9]/', '', strtok($ext, '?'));
        if (empty($ext))
            $ext = 'jpg';

        // Đổi tên ngẫu nhiên bằng MD5
        $random_name = md5(uniqid(microtime(), true)) . '.' . $ext;

        $file_array = array(
            'name' => $random_name,
            'tmp_name' => $tmp
        );

        // Upload vào Media Library
        $id = media_handle_sideload($file_array, 0);

        if (!is_wp_error($id)) {
            $local_url = wp_get_attachment_url($id);
            if ($local_url) {
                // Thay thế link cũ bằng link mới
                $content = str_replace($url, $local_url, $content);
                $processed_urls[$url] = $local_url;
            }
        } else {
            @unlink($tmp);
        }
    }

    return $content;
}

// Xử lý upload ảnh đã đóng dấu Watermark từ Dashboard vào Media Library
function pbn_api_upload_media($request)
{
    $params = $request->get_json_params();
    $filename = sanitize_file_name($params['filename'] ?? 'watermarked_img_' . time() . '.jpg');
    $base64_data = $params['base64_data'] ?? '';

    if (empty($base64_data)) {
        return new WP_REST_Response(array('success' => false, 'error' => 'Empty image data'), 400);
    }

    if (preg_match('/^data:image\/(\w+);base64,/', $base64_data, $type)) {
        $base64_data = substr($base64_data, strpos($base64_data, ',') + 1);
    }
    $decoded_data = base64_decode($base64_data);
    if ($decoded_data === false) {
        return new WP_REST_Response(array('success' => false, 'error' => 'Invalid base64 encoding'), 400);
    }

    $upload_dir = wp_upload_dir();
    $file_path = $upload_dir['path'] . '/' . $filename;

    file_put_contents($file_path, $decoded_data);

    $file_type = wp_check_filetype($filename, null);
    $attachment = array(
        'post_mime_type' => $file_type['type'],
        'post_title'     => sanitize_file_name($filename),
        'post_content'   => '',
        'post_status'    => 'inherit'
    );

    $attach_id = wp_insert_attachment($attachment, $file_path);
    require_once(ABSPATH . 'wp-admin/includes/image.php');
    $attach_data = wp_generate_attachment_metadata($attach_id, $file_path);
    wp_update_attachment_metadata($attach_id, $attach_data);

    $url = wp_get_attachment_url($attach_id);

    return new WP_REST_Response(array(
        'success' => true,
        'attachment_id' => $attach_id,
        'url' => $url
    ), 200);
}
