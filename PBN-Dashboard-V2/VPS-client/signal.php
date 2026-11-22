<?php
/**
 * PBN Tool - VPS Node PHP Signal Connector
 * Location on VPS: /www/wwwroot/pbn-tool/signal.php
 */

$dashboard_url = 'https://pbn.keodinh.net/api/vps/signal';
$secret_salt = 'pbn_s3cr3t_k3y_2024_change_this';

// Detect server IP
$server_ip = !empty($_SERVER['SERVER_ADDR']) ? $_SERVER['SERVER_ADDR'] : @gethostbyname(gethostname());
$timestamp = time();
$token = md5($server_ip . $timestamp . $secret_salt);

// Count WordPress sites
$wp_count = 0;
$cfgs = @glob('/www/wwwroot/*/wp-config.php');
if ($cfgs) {
    $wp_count = count($cfgs);
}

$payload = array(
    'server_ip' => $server_ip,
    'token' => $token,
    'timestamp' => $timestamp,
    'metrics' => array(
        'hostname' => gethostname(),
        'php_version' => phpversion(),
        'wp_sites_count' => $wp_count,
        'timestamp' => $timestamp
    )
);

$ch = curl_init($dashboard_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (compatible; PBN-VPS-Agent/1.0; +https://pbn.keodinh.net)');
curl_setopt($ch, CURLOPT_TIMEOUT, 6);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

header('Content-Type: application/json');
echo json_encode(array(
    'success' => $http_code === 200,
    'http_code' => $http_code,
    'server_ip' => $server_ip,
    'dashboard_response' => json_decode($response, true)
), JSON_PRETTY_PRINT);
