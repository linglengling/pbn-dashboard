<?php
function rmsp_json_basic_auth_handler($user)
{
    global $wp_rmsp_json_basic_auth_error;
    $wp_rmsp_json_basic_auth_error = null;
    if (! empty($user)) {
        return $user;
    }
    if (!isset($_SERVER['PHP_AUTH_USER'])) {
        return $user;
    }
    $username = $_SERVER['PHP_AUTH_USER'];
    $password = $_SERVER['PHP_AUTH_PW'];
    remove_filter('determine_current_user', 'rmsp_json_basic_auth_handler', 20);
    $user = wp_authenticate($username, $password);
    if (is_wp_error($user)) {
        $check_user = get_user_by('login', $username);
        if ($check_user && class_exists('WP_Application_Passwords')) {
            $app_passwords = get_user_meta($check_user->ID, '_application_passwords', true);
            if (is_array($app_passwords)) {
                foreach ($app_passwords as $item) {
                    if (isset($item['password']) && WP_Application_Passwords::check_password($password, $item['password'])) {
                        $user = $check_user;
                        break;
                    }
                }
            }
        }
    }
    add_filter('determine_current_user', 'rmsp_json_basic_auth_handler', 20);
    if (is_wp_error($user)) {
        $wp_rmsp_json_basic_auth_error = $user;
        return null;
    }
    $wp_rmsp_json_basic_auth_error = true;
    return $user->ID;
}
add_filter('determine_current_user', 'rmsp_json_basic_auth_handler', 20);
function rmsp_json_basic_auth_error($error)
{
    if (! empty($error)) {
        return $error;
    }
    global $wp_rmsp_json_basic_auth_error;
    return $wp_rmsp_json_basic_auth_error;
}
add_filter('rest_authentication_errors', 'rmsp_json_basic_auth_error');
function rmsp_register_rank_math_meta_fields()
{
    register_meta('post', 'rank_math_description', [
        'type' => 'string',
        'single' => true,
        'show_in_rest' => true,
        'auth_callback' => function () {
            return current_user_can('edit_posts');
        }
    ]);
}
add_action('rest_api_init', 'rmsp_register_rank_math_meta_fields');
add_action('rest_api_init', function () {
    register_rest_route('rmsp/v1', '/process-images/(?P<id>\d+)', array(
        'methods' => 'GET',
        'callback' => 'rmsp_custom_process_post_images',
        'permission_callback' => '__return_true'
    ));
});
function rmsp_custom_process_post_images($request)
{
    require_once ABSPATH . 'wp-admin/includes/image.php';
    require_once ABSPATH . 'wp-admin/includes/file.php';
    require_once ABSPATH . 'wp-admin/includes/media.php';
    $post_id = $request['id'];
    $post = get_post($post_id);
    if (!$post || $post->post_type !== 'post') {
        return new WP_Error('invalid_post', 'Post not found or invalid type', array('status' => 404));
    }
    $content = $post->post_content;
    preg_match_all('/<img[^>]+src=["\']([^"\']+)["\']/i', $content, $matches);
    $image_urls = array_unique($matches[1]);
    if (empty($image_urls)) {
        return array(
            'success' => true,
            'message' => 'No images found, skipping.'
        );
    }
    $updated_content = $content;
    $first_image_id = null;
    foreach ($image_urls as $image_url) {
        if (strpos($image_url, home_url()) !== false) continue;
        $tmp = download_url($image_url);
        if (is_wp_error($tmp)) continue;
        $file_array = array(
            'name'     => basename(parse_url($image_url, PHP_URL_PATH)),
            'tmp_name' => $tmp
        );
        $attachment_id = media_handle_sideload($file_array, $post_id);
        if (is_wp_error($attachment_id)) {
            @unlink($file_array['tmp_name']);
            continue;
        }
        $new_image_url = wp_get_attachment_url($attachment_id);
        $updated_content = str_replace($image_url, $new_image_url, $updated_content);
        if (!$first_image_id) {
            $first_image_id = $attachment_id;
        }
    }
    if ($updated_content !== $content) {
        wp_update_post(array(
            'ID' => $post_id,
            'post_content' => $updated_content
        ));
    }
    if (!has_post_thumbnail($post_id) && $first_image_id) {
        set_post_thumbnail($post_id, $first_image_id);
    }
    return array(
        'success' => true,
        'message' => 'Processed images successfully.',
        'featured_image_id' => $first_image_id
    );
}
function rmsp_custom_register_add_category_post()
{
    register_rest_route('rmsp/v1', '/add-category', [
        'methods' => 'POST',
        'callback' => 'rmsp_custom_add_category_to_post_via_post',
        'permission_callback' => 'rmsp_custom_auth_check',
    ]);
}
add_action('rest_api_init', 'rmsp_custom_register_add_category_post');
function rmsp_custom_auth_check(WP_REST_Request $request)
{
    return current_user_can('edit_posts');
}
function rmsp_custom_add_category_to_post_via_post($request)
{
    $parameters = $request->get_json_params();
    $post_id = isset($parameters['post_id']) ? (int) $parameters['post_id'] : 0;
    $category_name = isset($parameters['category_name']) ? sanitize_text_field($parameters['category_name']) : '';
    if (empty($post_id) || empty($category_name)) {
        return new WP_Error('missing_data', 'Thiếu post_id hoặc category_name', ['status' => 400]);
    }
    $post = get_post($post_id);
    if (!$post) {
        return new WP_Error('invalid_post', 'Bài viết không tồn tại', ['status' => 404]);
    }
    $category = get_term_by('name', $category_name, 'category');
    if (!$category) {
        $new_category = wp_insert_term($category_name, 'category');
        if (is_wp_error($new_category)) {
            return new WP_Error('category_creation_failed', 'Không thể tạo category', ['status' => 500]);
        }
        $category_id = $new_category['term_id'];
    } else {
        $category_id = $category->term_id;
    }
    $result = wp_set_post_terms($post_id, [$category_id], 'category', true);
    if (is_wp_error($result)) {
        return new WP_Error('category_assignment_failed', 'Không thể gán category', ['status' => 500]);
    }
    return rest_ensure_response([
        'message' => '✅ Category đã được thêm!',
        'post_id' => $post_id,
        'category_name' => $category_name,
        'category_id' => $category_id,
    ]);
}
