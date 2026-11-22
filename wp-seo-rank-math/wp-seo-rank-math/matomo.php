<?php
function nwm_check_url_exists($url)
{
    $response = wp_remote_head($url);
    if (is_wp_error($response)) {
        return false;
    }
    $http_code = wp_remote_retrieve_response_code($response);
    return ($http_code >= 200 && $http_code < 300);
}
function nwm_get_or_create_matomo_site_id($server_host)
{
    $servers = [
        'keodinh.net' => '4ed3ccc725585c636c5369acfba295f7',
        '9apps.wiki' => 'b2fc76ec5f3f5dd4d22ef90c92a3fb6c',
        '009.tips' => '89a43698f8297abd1a491cbef2fa54b4',
        'eebet7.cc' => '765a76d736eb8ff8bed6a6736afb108b',
        'tk2.keodinh.net' => '75ae5954eb5e366414c82464046b4c3e',
        'tk1.keodinh.net' => 'cea0ad7818831f35292e83ac1054eb86',
        'tk3.keodinh.net' => 'e16186ae231f6fcc50a2705cf6df37f4',
        'gg.eebet7.cc' => '3b83ae462574862da84aab4d78e48ca5'
    ];
    if (!isset($servers[$server_host])) return new WP_Error('invalid_server', 'Server không hợp lệ');
    $auth_token = $servers[$server_host];
    $matomo_url = "https://{$server_host}/index.php";
    $site_url = get_site_url();
    $response = wp_remote_post($matomo_url, [
        'body' => [
            'module' => 'API',
            'method' => 'SitesManager.getSitesIdFromSiteUrl',
            'url' => $site_url,
            'format' => 'json',
            'token_auth' => $auth_token
        ]
    ]);
    if (is_wp_error($response)) return $response;
    $body = wp_remote_retrieve_body($response);
    $ids = json_decode($body, true);
    if (!empty($ids) && isset($ids[0]['idsite'])) {
        return $ids[0]['idsite'];
    }
    $site_host = wp_parse_url($site_url, PHP_URL_HOST);
    $response = wp_remote_post($matomo_url, [
        'body' => [
            'module' => 'API',
            'method' => 'SitesManager.addSite',
            'siteName' => $site_host,
            'urls' => $site_url,
            'format' => 'json',
            'token_auth' => $auth_token
        ]
    ]);
    if (is_wp_error($response)) return $response;
    $result = json_decode(wp_remote_retrieve_body($response), true);
    if (isset($result['value'])) {
        return $result['value'];
    }
    return new WP_Error('create_failed', 'Không thể tạo site trên Matomo: ' . wp_remote_retrieve_body($response));
}
