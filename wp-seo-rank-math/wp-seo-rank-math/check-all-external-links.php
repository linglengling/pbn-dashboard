<?php
function nwm_extlinks_site_host()
{
    return parse_url(home_url(), PHP_URL_HOST);
}
function nwm_extlinks_extract_links_from_content($content)
{
    $site_host = nwm_extlinks_site_host();
    $results   = [];
    if (!is_string($content) || $content === '') return $results;
    libxml_use_internal_errors(true);
    $doc = new DOMDocument();
    $doc->loadHTML('<?xml encoding="utf-8" ?>' . $content);
    $links = $doc->getElementsByTagName('a');
    foreach ($links as $link) {
        $href = trim($link->getAttribute('href'));
        if (!$href) continue;
        if (
            !preg_match('~^https?://~i', $href) &&
            preg_match('~^[a-z0-9.-]+\.[a-z]{2,}(?:/.*)?$~i', $href)
        ) {
            $href = 'http://' . ltrim($href, '/');
        }
        if (strpos($href, '//') === 0) {
            $href = 'http:' . $href;
        }
        if (
            !preg_match('#^https?://#i', $href) &&
            preg_match('#^[a-z0-9\-\.]+\.[a-z]{2,}(/.*)?$#i', $href)
        ) {
            $href = 'http://' . ltrim($href, '/');
        }
        $host = parse_url($href, PHP_URL_HOST);
        if (!$host) continue;
        if (strcasecmp($host, $site_host) !== 0) {
            $results[] = [
                'url'  => $href,
                'text' => trim($link->textContent),
            ];
        }
    }
    return $results;
}
function nwm_extlinks_transform_html($html, $mode, $new_url = '')
{
    if (!is_string($html) || trim($html) === '') return $html;
    $site_host = nwm_extlinks_site_host();
    libxml_use_internal_errors(true);
    $doc = new DOMDocument();
    $doc->loadHTML('<?xml encoding="utf-8" ?>' . $html);
    $xpath = new DOMXPath($doc);
    $changed = false;
    foreach ($xpath->query('//a[@href]') as $a) {
        $href = trim($a->getAttribute('href'));
        if ($href === '') continue;
        if (preg_match('#^(mailto:|tel:|javascript:|#)#i', $href)) continue;
        if (strpos($href, '//') === 0) {
            $href = 'http:' . $href;
        } elseif (
            !preg_match('#^https?://#i', $href) &&
            preg_match('#^[a-z0-9\-\.]+\.[a-z]{2,}(/.*)?$#i', $href)
        ) {
            $href = 'http://' . ltrim($href, '/');
        }
        $host = parse_url($href, PHP_URL_HOST);
        if (!$host) continue;
        if (strcasecmp($host, $site_host) === 0) continue;
        if ($mode === 'remove') {
            $text = $doc->createTextNode($a->textContent);
            $a->parentNode->replaceChild($text, $a);
            $changed = true;
        } elseif ($mode === 'replace') {
            if ($new_url && preg_match('#^https?://#i', $new_url)) {
                $a->setAttribute('href', $new_url);
                $a->setAttribute('rel', 'noopener');
                $a->setAttribute('target', '_blank');
                $changed = true;
            }
        } elseif ($mode === 'delete') {
            if ($a->parentNode) {
                $a->parentNode->removeChild($a);
                $changed = true;
            }
        }
    }
    if (!$changed) return $html;
    $body = $doc->getElementsByTagName('body')->item(0);
    $out  = '';
    foreach ($body->childNodes as $child) {
        $out .= $doc->saveHTML($child);
    }
    return $out;
}
function nwm_extlinks_collect_posts()
{
    $external_links = [];
    $post_types = get_post_types(['public' => true], 'names');
    $all_posts = get_posts([
        'post_type'      => $post_types,
        'posts_per_page' => -1,
        'post_status'    => 'publish',
    ]);
    foreach ($all_posts as $post) {
        $urls = nwm_extlinks_extract_links_from_content($post->post_content);
        if (!empty($urls)) {
            $external_links[$post->post_type][$post->ID] = $urls;
        }
    }
    return $external_links;
}
function nwm_extlinks_collect_options()
{
    global $wpdb;
    $external_links = [];
    $options = $wpdb->get_results("SELECT option_name, option_value FROM {$wpdb->options}");
    foreach ($options as $option) {
        $name = $option->option_name;
        $val  = $option->option_value;
        if ($name === 'widget_block') {
            $instances = maybe_unserialize($val);
            if (is_array($instances)) {
                foreach ($instances as $instance_id => $instance) {
                    if (!is_array($instance)) continue;
                    if (!empty($instance['content'])) {
                        $urls = nwm_extlinks_extract_links_from_content($instance['content']);
                        if (!empty($urls)) {
                            $external_links['widget_block']["instance_{$instance_id}"] = $urls;
                        }
                    }
                    if (!empty($instance['raw']) && is_string($instance['raw'])) {
                        $urls = nwm_extlinks_extract_links_from_content($instance['raw']);
                        if (!empty($urls)) {
                            $external_links['widget_block_raw']["instance_{$instance_id}"] = $urls;
                        }
                    }
                }
            }
            continue;
        }
        if ($name === 'widget_text') {
            $instances = maybe_unserialize($val);
            if (is_array($instances)) {
                foreach ($instances as $instance_id => $instance) {
                    if (isset($instance['text']) && !empty($instance['text'])) {
                        $urls = nwm_extlinks_extract_links_from_content($instance['text']);
                        if (!empty($urls)) {
                            $external_links['widget_text']["instance_{$instance_id}"] = $urls;
                        }
                    }
                }
            }
            continue;
        }
        $stringish = is_serialized($val) ? json_encode(maybe_unserialize($val)) : (string)$val;
        if (!empty($stringish)) {
            $urls = nwm_extlinks_extract_links_from_content($stringish);
            if (!empty($urls)) {
                $external_links['option'][$name] = $urls;
            }
        }
    }
    return $external_links;
}
function nwm_extlinks_add_menu()
{
    add_management_page(
        __('External Link', 'nwm-extlinks'),
        __('External Link', 'nwm-extlinks'),
        'manage_options',
        'nwm-external-link',
        'nwm_extlinks_render_page'
    );
}
add_action('admin_menu', 'nwm_extlinks_add_menu');
function nwm_extlinks_render_page()
{
    if (!current_user_can('manage_options')) {
        wp_die(__('Permission denied', 'nwm-extlinks'));
    }
    $posts_map   = nwm_extlinks_collect_posts();
    $options_map = nwm_extlinks_collect_options();
    $res = array_filter([
        'posts'   => $posts_map,
        'options' => $options_map,
    ], function ($v) {
        return !empty($v);
    });
?>
    <div class="wrap">
        <h1><?php esc_html_e('External Links Manager', 'nwm-extlinks'); ?></h1>
        <?php if (empty($res)) : ?>
            <div class="notice notice-success">
                <p><?php esc_html_e('No external links found.', 'nwm-extlinks'); ?></p>
            </div>
        <?php else : ?>
            <div class="nwm-ext-link">
                <?php foreach ($res as $group_key => $group_value): ?>
                    <div class="nwm-item">
                        <div class="nwm-item-header">
                            <?php echo esc_html(strtoupper($group_key)); ?>
                        </div>
                        <div class="nwm-item-main">
                            <?php
                            foreach ($group_value as $subkey => $subval): ?>
                                <h3 style="margin:16px 0 8px;"><?php echo esc_html($subkey); ?></h3>
                                <ul style="padding-left: 40px;">
                                    <?php
                                    $idx = 0;
                                    foreach ($subval as $k => $urls):
                                        $idx++;
                                    ?>
                                        <li style="margin-bottom:12px; position:relative;">
                                            <span style="display:block;height:24px;width:24px;border-radius:50%;border:2px solid #ddd;position:absolute;top:0;left:-30px;text-align:center;line-height:20px;font-size:11px;font-weight:700;"><?php echo (int)$idx; ?></span>
                                            <?php if (is_numeric($k)): ?>
                                                <strong>Title ::: <a target="_blank" href="<?php echo esc_url(get_edit_post_link($k)); ?>">
                                                        <?php echo esc_html(get_the_title($k)); ?>
                                                    </a></strong>
                                            <?php else: ?>
                                                <strong>Key ::: <?php echo esc_html($k); ?></strong>
                                            <?php endif; ?>
                                            <?php foreach ($urls as $one): ?>
                                                <p style="margin:4px 0 0;">
                                                    Anchor text ::: <a target="_blank" rel="noopener" href="<?php echo esc_url($one['url']); ?>"><?php echo esc_html($one['text']); ?></a>
                                                </p>
                                            <?php endforeach; ?>
                                        </li>
                                    <?php endforeach; ?>
                                </ul>
                            <?php endforeach; ?>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
            <div class="nwm-action" style="margin-top:24px;background:#fff;border:1px solid #ddd;padding:16px;">
                <h2 style="margin-top:0;"><?php esc_html_e('Bulk Action for External Links', 'nwm-extlinks'); ?></h2>
                <fieldset style="margin-bottom:12px;">
                    <label style="margin-right:18px;">
                        <input type="radio" name="nwm_action_mode" value="remove" checked>
                        <?php esc_html_e('Remove (unwrap external links)', 'nwm-extlinks'); ?>
                    </label>
                    <label style="margin-right:18px;">
                        <input type="radio" name="nwm_action_mode" value="replace">
                        <?php esc_html_e('Replace (change all external links to a URL)', 'nwm-extlinks'); ?>
                    </label>
                    <label>
                        <input type="radio" name="nwm_action_mode" value="delete">
                        <?php esc_html_e('Delete (remove <a> tag and its text)', 'nwm-extlinks'); ?>
                    </label>
                </fieldset>
                <div id="nwm-replace-url-wrap" style="display:none;margin-bottom:12px;">
                    <label>
                        <?php esc_html_e('New URL:', 'nwm-extlinks'); ?>&nbsp;
                        <input type="text" id="nwm-replace-url" placeholder="https://example.com" style="min-width:360px;">
                    </label>
                </div>
                <?php wp_nonce_field('nwm_extlinks_nonce', 'nwm_extlinks_nonce_field'); ?>
                <button id="nwm-run-bulk" class="button button-primary"><?php esc_html_e('Run', 'nwm-extlinks'); ?></button>
                <span id="nwm-bulk-status" style="margin-left:12px;"></span>
                <p style="margin-top:10px;color:#666;"><?php esc_html_e('Tip: On very large sites, run twice or split by post type to avoid timeouts. A WP-CLI version can be added if needed.', 'nwm-extlinks'); ?></p>
            </div>
        <?php endif; ?>
    </div>
    <style>
        .nwm-item {
            background: #fff;
            width: 100%;
            margin-bottom: 24px;
            border: 1px solid #ccc;
            padding: 16px;
            max-width: 100%;
        }

        .nwm-item-header {
            padding: 10px;
            background: #000;
            color: #fff;
            text-transform: uppercase;
        }

        .nwm-item-main ul {
            padding-left: 50px;
        }

        .nwm-item-main li {
            color: #4F4F4F;
            padding-left: 16px;
            margin-top: 12px;
            position: relative;
            font-size: 14px;
            line-height: 20px;
        }
    </style>
    <script>
        (function() {
            const modeRadios = document.querySelectorAll('input[name="nwm_action_mode"]');
            const replaceWrap = document.getElementById('nwm-replace-url-wrap');
            const runBtn = document.getElementById('nwm-run-bulk');
            const statusEl = document.getElementById('nwm-bulk-status');
            const nonceField = document.getElementById('nwm_extlinks_nonce_field');
            modeRadios.forEach(r => {
                r.addEventListener('change', function() {
                    replaceWrap.style.display = (this.value === 'replace') ? 'block' : 'none';
                });
            });
            runBtn && runBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const mode = document.querySelector('input[name="nwm_action_mode"]:checked')?.value || 'remove';
                const url = document.getElementById('nwm-replace-url')?.value || '';
                const nonce = nonceField?.value;
                if (!['remove', 'replace', 'delete'].includes(mode)) {
                    alert('Invalid mode');
                    return;
                }
                if (mode === 'replace' && (!url || !/^https?:\/\//i.test(url))) {
                    alert('Vui lòng nhập URL dạng https:// hoặc http://');
                    return;
                }
                statusEl.textContent = 'Processing...';
                runBtn.disabled = true;
                fetch(ajaxurl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                        },
                        body: new URLSearchParams({
                            action: 'nwm_extlinks_bulk',
                            mode: mode,
                            new_url: url,
                            _wpnonce: nonce
                        })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data && data.success) {
                            statusEl.textContent = `Done. Posts updated: ${data.data.posts_updated}, Options updated: ${data.data.options_updated}`;
                        } else {
                            statusEl.textContent = 'Error';
                            alert((data && data.data && data.data.message) ? data.data.message : 'Unknown error');
                        }
                    })
                    .catch(err => {
                        statusEl.textContent = 'Error';
                        alert(err?.message || err);
                    })
                    .finally(() => {
                        runBtn.disabled = false;
                    });
            });
        })();
    </script>
<?php
}
add_action('wp_ajax_nwm_extlinks_bulk', 'nwm_extlinks_bulk_handler');
function nwm_extlinks_bulk_handler()
{
    if (! current_user_can('manage_options')) {
        wp_send_json_error(['message' => 'Permission denied'], 403);
    }
    check_ajax_referer('nwm_extlinks_nonce');
    $mode    = isset($_POST['mode']) ? sanitize_text_field($_POST['mode']) : 'remove';
    $new_url = isset($_POST['new_url']) ? esc_url_raw(trim($_POST['new_url'])) : '';
    if (!in_array($mode, ['remove', 'replace', 'delete'], true)) {
        wp_send_json_error(['message' => 'Invalid mode'], 400);
    }
    if ($mode === 'replace' && (empty($new_url) || !preg_match('#^https?://#i', $new_url))) {
        wp_send_json_error(['message' => 'Invalid URL'], 400);
    }
    $posts_updated   = nwm_extlinks_process_all_posts($mode, $new_url);
    $options_updated = nwm_extlinks_process_all_options($mode, $new_url);
    wp_send_json_success([
        'posts_updated'   => $posts_updated,
        'options_updated' => $options_updated,
    ]);
}
function nwm_extlinks_process_all_posts($mode, $new_url = '')
{
    $post_types = get_post_types(['public' => true], 'names');
    $all_posts  = get_posts([
        'post_type'      => $post_types,
        'posts_per_page' => -1,
        'post_status'    => 'publish',
        'fields'         => 'ids',
    ]);
    $count = 0;
    foreach ($all_posts as $pid) {
        $content    = get_post_field('post_content', $pid);
        $processed  = nwm_extlinks_transform_html($content, $mode, $new_url);
        if ($processed !== $content) {
            wp_update_post(['ID' => $pid, 'post_content' => $processed]);
            $count++;
        }
    }
    return $count;
}
function nwm_extlinks_process_all_options($mode, $new_url = '')
{
    global $wpdb;
    $options = $wpdb->get_results("SELECT option_id, option_name, option_value FROM {$wpdb->options}");
    $count   = 0;
    foreach ($options as $opt) {
        $name  = $opt->option_name;
        $value = $opt->option_value;
        if ($name === 'widget_block') {
            $instances = maybe_unserialize($value);
            $changed   = false;
            if (is_array($instances)) {
                foreach ($instances as $id => $inst) {
                    if (!is_array($inst)) continue;
                    if (!empty($inst['content'])) {
                        $new = nwm_extlinks_transform_html($inst['content'], $mode, $new_url);
                        if ($new !== $inst['content']) {
                            $instances[$id]['content'] = $new;
                            $changed = true;
                        }
                    }
                    if (!empty($inst['raw']) && is_string($inst['raw'])) {
                        $new = nwm_extlinks_transform_html($inst['raw'], $mode, $new_url);
                        if ($new !== $inst['raw']) {
                            $instances[$id]['raw'] = $new;
                            $changed = true;
                        }
                    }
                }
            }
            if ($changed) {
                update_option($name, $instances);
                $count++;
            }
            continue;
        }
        if ($name === 'widget_text') {
            $instances = maybe_unserialize($value);
            $changed   = false;
            if (is_array($instances)) {
                foreach ($instances as $id => $inst) {
                    if (isset($inst['text'])) {
                        $new = nwm_extlinks_transform_html($inst['text'], $mode, $new_url);
                        if ($new !== $inst['text']) {
                            $instances[$id]['text'] = $new;
                            $changed = true;
                        }
                    }
                }
            }
            if ($changed) {
                update_option($name, $instances);
                $count++;
            }
            continue;
        }
        if (!is_serialized($value)) {
            $string = (string)$value;
            if ($string !== '') {
                $new = nwm_extlinks_transform_html($string, $mode, $new_url);
                if ($new !== $string) {
                    update_option($name, $new);
                    $count++;
                }
            }
        }
    }
    return $count;
}
