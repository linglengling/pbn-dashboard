<?php
if (!defined('ABSPATH')) exit;
class MediaWebPConverterReplacer
{
    public function __construct()
    {
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_post_convert_to_webp', [$this, 'convert_images_to_webp']);
        add_action('admin_post_replace_images_with_webp', [$this, 'replace_image_urls_in_content']);
        add_filter('wp_generate_attachment_metadata', [$this, 'auto_convert_on_upload'], 10, 2);
    }
    public function add_admin_menu()
    {
        add_menu_page('WebP Converter', 'WebP Converter', 'manage_options', 'webp-converter', [$this, 'admin_page']);
    }
    public function admin_page()
    {
?>
        <div class="wrap">
            <h1>WebP Converter & URL Replacer</h1>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
                <input type="hidden" name="action" value="convert_to_webp">
                <input type="submit" class="button button-primary" value="Convert All Images to WebP">
            </form>
            <br>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
                <input type="hidden" name="action" value="replace_images_with_webp">
                <input type="submit" class="button button-secondary" value="Replace Image URLs in Content">
            </form>
        </div>
<?php
    }
    public function convert_images_to_webp()
    {
        $attachments = get_posts([
            'post_type' => 'attachment',
            'post_mime_type' => 'image',
            'numberposts' => -1
        ]);
        foreach ($attachments as $attachment) {
            $file_path = get_attached_file($attachment->ID);
            $this->generate_webp($file_path);
        }
        wp_redirect(admin_url('admin.php?page=webp-converter&converted=1'));
        exit;
    }
    public function replace_image_urls_in_content()
    {
        $posts = get_posts([
            'post_type' => ['post', 'page'],
            'numberposts' => -1
        ]);
        foreach ($posts as $post) {
            $content = $post->post_content;
            $updated_content = preg_replace_callback('/<img[^>]+src=["\']([^"\']+\.(jpg|jpeg|png))["\']/', function ($matches) {
                $webp_url = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $matches[1]);
                return str_replace($matches[1], $webp_url, $matches[0]);
            }, $content);
            if ($content !== $updated_content) {
                wp_update_post([
                    'ID' => $post->ID,
                    'post_content' => $updated_content
                ]);
            }
        }
        wp_redirect(admin_url('admin.php?page=webp-converter&replaced=1'));
        exit;
    }
    public function auto_convert_on_upload($metadata, $attachment_id)
    {
        $file_path = get_attached_file($attachment_id);
        $this->generate_webp($file_path);
        return $metadata;
    }
    private function generate_webp($file_path)
    {
        $webp_path = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $file_path);
        if (!file_exists($webp_path)) {
            $image = wp_get_image_editor($file_path);
            if (!is_wp_error($image)) {
                $image->save($webp_path, 'image/webp');
                if (file_exists($webp_path) && file_exists($file_path)) {
                    unlink($file_path);
                }
            }
        }
    }
}
new MediaWebPConverterReplacer();
