<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "START_TEST\n";
require_once __DIR__ . '/wp-load.php';
echo "WP_LOADED\n";
echo "SITEURL: " . get_option('siteurl') . "\n";
echo "HOME: " . get_option('home') . "\n";

