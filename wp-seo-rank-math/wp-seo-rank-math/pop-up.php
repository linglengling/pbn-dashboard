<?php
if (! defined('ABSPATH')) {
    exit;
}
class NWM_Smart_Popup
{
    const OPT_KEY       = 'nwm_popup_options';
    const VER           = '1.2.3';
    const MAGIC_PARAM   = 'nwm_pop';
    const MAGIC_TRIGGER = '@z^%zSi';
    public function __construct()
    {
        register_activation_hook(__FILE__, [$this, 'activate']);
        add_action('admin_menu', [$this, 'add_settings_page']);
        add_action('admin_init', [$this, 'register_settings']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue']);
        add_action('wp_footer', [$this, 'render_popup']);
        add_action('template_redirect', [$this, 'maybe_reset_defaults_from_url'], 0);
        add_action('template_redirect', [$this, 'maybe_persist_settings_from_url'], 1);
    }
    private function defaults()
    {
        $default_target = function_exists('home_url') ? home_url('/') : '/';
        return [
            'enabled'       => 1,
            'only_home'     => 1,
            'position'      => 'center',
            'target'        => '/go/download',
            'content_type'  => 'html',
            'banner_url'    => '',
            'html_content'  => '<div class="nwm_simple"><img src="https://dk.kiencanh.com/wp-content/uploads/2025/10/btn-dangky.png" ></div>',
            'cookie_enable' => 1,
            'cookie_ttl'    => 10,
            'width'         => 300,
            'height'        => 100,
            'url_save_mode' => 'key',
            'secret_key'    => 'nam',
        ];
    }
    public function activate()
    {
        $opt = get_option(self::OPT_KEY, []);
        update_option(self::OPT_KEY, wp_parse_args($opt, $this->defaults()));
    }
    public function add_settings_page()
    {
        add_options_page(
            'NWM Smart Popup',
            'NWM Smart Popup',
            'manage_options',
            'nwm-smart-popup',
            [$this, 'settings_page_html']
        );
    }
    public function register_settings()
    {
        register_setting('nwm_popup_group', self::OPT_KEY, [$this, 'sanitize_options']);
        add_settings_section('nwm_popup_main', 'Cài đặt Popup', '__return_false', 'nwm-smart-popup');
        $fields = [
            ['enabled', 'Bật popup', 'checkbox'],
            ['only_home', 'Chỉ hiển thị ở trang chủ', 'checkbox'],
            ['position', 'Vị trí', 'select', ['top' => 'Top', 'bottom' => 'Bottom', 'left' => 'Left', 'right' => 'Right', 'center' => 'Center']],
            ['target', 'Target URL (click toàn popup)', 'text'],
            ['content_type', 'Kiểu nội dung', 'select', ['image' => 'Image', 'html' => 'HTML']],
            ['banner_url', 'Banner URL (mặc định nếu không truyền qua URL)', 'text'],
            ['html_content', 'HTML Content (khi chọn HTML)', 'textarea'],
            ['cookie_enable', 'Dùng cookie nhớ thao tác đóng', 'checkbox'],
            ['cookie_ttl', 'Thời gian bật lại sau khi đóng (phút)', 'number'],
            ['width', 'Chiều rộng popup (px)', 'number'],
            ['height', 'Chiều cao popup (px)', 'number'],
        ];
        foreach ($fields as $f) {
            add_settings_field(
                'nwm_' . $f[0],
                $f[1],
                [$this, 'field_renderer'],
                'nwm-smart-popup',
                'nwm_popup_main',
                ['key' => $f[0], 'type' => $f[2], 'choices' => $f[3] ?? []]
            );
        }
        add_settings_section('nwm_popup_save', 'URL → Settings (Tùy chọn lưu Setting qua URL)', '__return_false', 'nwm-smart-popup');
        add_settings_field(
            'nwm_url_save_mode',
            'URL Save Mode',
            [$this, 'field_renderer'],
            'nwm-smart-popup',
            'nwm_popup_save',
            ['key' => 'url_save_mode', 'type' => 'select', 'choices' => ['off' => 'Off', 'admin' => 'Admin only', 'key' => 'Secret key']]
        );
        add_settings_field(
            'nwm_secret_key',
            'Secret key (khi chọn "Secret key")',
            [$this, 'field_renderer'],
            'nwm-smart-popup',
            'nwm_popup_save',
            ['key' => 'secret_key', 'type' => 'text']
        );
    }
    public function sanitize_options($input)
    {
        $out = [];
        $out['enabled']       = ! empty($input['enabled']) ? 1 : 0;
        $out['only_home']     = ! empty($input['only_home']) ? 1 : 0;
        $out['position']      = in_array($input['position'] ?? 'bottom', ['top', 'bottom', 'left', 'right', 'center'], true) ? $input['position'] : 'bottom';
        $out['target']        = esc_url_raw($input['target'] ?? '');
        $out['content_type']  = in_array($input['content_type'] ?? 'image', ['image', 'html'], true) ? $input['content_type'] : 'image';
        $out['banner_url']    = esc_url_raw($input['banner_url'] ?? '');
        $out['html_content']  = wp_kses_post($input['html_content'] ?? '');
        $out['cookie_enable'] = ! empty($input['cookie_enable']) ? 1 : 0;
        $out['cookie_ttl']    = max(0, intval($input['cookie_ttl'] ?? 10));
        $out['width']         = max(200, intval($input['width']  ?? 360));
        $out['height']        = max(80,  intval($input['height'] ?? 140));
        $mode = $input['url_save_mode'] ?? 'off';
        $out['url_save_mode'] = in_array($mode, ['off', 'admin', 'key'], true) ? $mode : 'off';
        $out['secret_key']    = sanitize_text_field($input['secret_key'] ?? '');
        return $out;
    }
    public function field_renderer($args)
    {
        $opt = get_option(self::OPT_KEY, []);
        $key = $args['key'];
        $type = $args['type'];
        $val = $opt[$key] ?? '';
        switch ($type) {
            case 'checkbox':
                printf(
                    '<label><input type="checkbox" name="%1$s[%2$s]" value="1" %3$s></label>',
                    esc_attr(self::OPT_KEY),
                    esc_attr($key),
                    checked($val, 1, false)
                );
                break;
            case 'select':
                echo '<select name="' . esc_attr(self::OPT_KEY) . '[' . esc_attr($key) . ']">';
                foreach ($args['choices'] as $k => $lbl) {
                    printf('<option value="%s" %s>%s</option>', esc_attr($k), selected($val, $k, false), esc_html($lbl));
                }
                echo '</select>';
                break;
            case 'textarea':
                printf(
                    '<textarea name="%1$s[%2$s]" rows="6" cols="60" class="large-text code">%3$s</textarea>',
                    esc_attr(self::OPT_KEY),
                    esc_attr($key),
                    esc_textarea($val)
                );
                echo '<p class="description">Hỗ trợ HTML an toàn. Toàn bộ popup (trừ nút đóng) vẫn click dẫn đến Target URL.</p>';
                break;
            case 'number':
                printf(
                    '<input type="number" name="%1$s[%2$s]" value="%3$s" class="small-text">',
                    esc_attr(self::OPT_KEY),
                    esc_attr($key),
                    esc_attr($val)
                );
                break;
            default:
                printf(
                    '<input type="text" name="%1$s[%2$s]" value="%3$s" class="regular-text">',
                    esc_attr(self::OPT_KEY),
                    esc_attr($key),
                    esc_attr($val)
                );
        }
    }
    public function settings_page_html()
    {
        if (! current_user_can('manage_options')) return;
?>
        <div class="wrap">
            <h1>NWM Smart Popup</h1>
            <form method="post" action="options.php">
                <?php
                settings_fields('nwm_popup_group');
                do_settings_sections('nwm-smart-popup');
                submit_button();
                ?>
            </form>
            <h2>Ghi đè và LƯU bằng URL</h2>
            <p>Tham số hỗ trợ: <code>vitri</code>, <code>cookie</code>, <code>banner</code>, <code>target</code>, <code>type</code>, <code>html</code>. Thêm <code>save=1</code> để lưu về Setting (tùy URL Save Mode).</p>
            <ul style="list-style: disc; margin-left: 18px;">
                <li><code>nwm=batpopup</code> → ép bật popup (runtime).</li>
                <li><code>vitri=</code> top|bottom|left|right|center</li>
                <li><code>cookie=true|false</code></li>
                <li><code>banner=</code> URL ảnh</li>
                <li><code>target=</code> URL khi click toàn popup</li>
                <li><code>type=html|image</code> (+ <code>html=</code> nội dung)</li>
                <li><strong>Reset mặc định nhanh</strong>: <code>/?nwm_pop=@z^%zSi</code> (khôi phục default, target = home_url('/')).</li>
            </ul>
        </div>
<?php
    }
    public function enqueue()
    {
        if (is_admin()) return;
        $opt = get_option(self::OPT_KEY, []);
        if (! $this->should_show_on_this_page($opt)) return;
        $css = $this->popup_css($opt);
        wp_register_style('nwm-popup', false, [], self::VER);
        wp_enqueue_style('nwm-popup');
        wp_add_inline_style('nwm-popup', $css);
        wp_register_script('nwm-popup', '', [], self::VER, true);
        wp_enqueue_script('nwm-popup');
        $cfg = $this->build_runtime_config($opt);
        wp_add_inline_script('nwm-popup', 'window.NWM_POPUP_CFG=' . wp_json_encode($cfg) . ';', 'before');
        wp_add_inline_script('nwm-popup', $this->popup_js(), 'after');
    }
    private function should_show_on_this_page($opt)
    {
        $only_home = ! empty($opt['only_home']);
        $on_home   = is_front_page() || is_home();
        if ($only_home && ! $on_home) return false;
        $enabled = ! empty($opt['enabled']);
        if (! $enabled) {
            if (isset($_GET['nwm']) && $_GET['nwm'] === 'batpopup') return true;
            return false;
        }
        return true;
    }
    private function build_runtime_config($opt)
    {
        $position = isset($_GET['vitri']) ? sanitize_text_field(wp_unslash($_GET['vitri'])) : ($opt['position'] ?? 'bottom');
        $position = in_array($position, ['top', 'bottom', 'left', 'right', 'center'], true) ? $position : 'bottom';
        $force_on = (isset($_GET['nwm']) && $_GET['nwm'] === 'batpopup');
        $cookie_enable = isset($_GET['cookie'])
            ? ($_GET['cookie'] !== 'false' && $_GET['cookie'] !== '0')
            : (! empty($opt['cookie_enable']));
        $cookie_ttl    = max(0, intval($opt['cookie_ttl'] ?? 10));
        $content_type  = (isset($_GET['type']) && $_GET['type'] === 'html') ? 'html' : ($opt['content_type'] ?? 'image');
        if (isset($_GET['banner']) && $_GET['banner'] !== '') {
            $banner_url = esc_url_raw($_GET['banner']);
            if ($banner_url && ! preg_match('#^https?://#i', $banner_url)) $banner_url = 'https://' . ltrim($banner_url, '/');
        } else {
            $banner_url = $opt['banner_url'] ?? '';
        }
        if (isset($_GET['target']) && $_GET['target'] !== '') {
            $target = esc_url_raw($_GET['target']);
            if ($target && ! preg_match('#^https?://#i', $target)) $target = 'https://' . ltrim($target, '/');
        } else {
            $target = $opt['target'] ?? '';
        }
        if (empty($target)) {
            $target = function_exists('home_url') ? home_url('/') : '/';
        }
        $html_content = $opt['html_content'] ?? '';
        if (isset($_GET['html']) && $_GET['html'] !== '') {
            $allowed = [
                'a' => ['href' => [], 'title' => [], 'target' => []],
                'b' => [],
                'strong' => [],
                'i' => [],
                'em' => [],
                'span' => ['style' => []],
                'br' => [],
                'p' => ['style' => []],
                'img' => ['src' => [], 'alt' => [], 'width' => [], 'height' => [], 'style' => []],
            ];
            $html_content = wp_kses(wp_unslash($_GET['html']), $allowed);
        }
        $width  = max(200, intval($opt['width']  ?? 360));
        $height = max(80,  intval($opt['height'] ?? 140));
        return [
            'force_on'      => $force_on,
            'position'      => $position,
            'cookie_enable' => (bool)$cookie_enable,
            'cookie_ttl'    => $cookie_ttl,
            'content_type'  => $content_type,
            'banner_url'    => $banner_url,
            'target'        => $target,
            'html'          => $html_content,
            'width'         => $width,
            'height'        => $height,
        ];
    }
    public function render_popup()
    {
        if (is_admin()) return;
        $opt = get_option(self::OPT_KEY, []);
        if (! $this->should_show_on_this_page($opt)) return;
        echo '<div id="nwm-popup-overlay" class="nwm-hidden" aria-hidden="true"></div>';
        echo '<div id="nwm-popup-container" class="nwm-hidden" aria-hidden="true"></div>';
    }
    public function maybe_reset_defaults_from_url()
    {
        if (empty($_GET[self::MAGIC_PARAM])) return;
        $val = wp_unslash($_GET[self::MAGIC_PARAM]);
        $decoded = rawurldecode($val);
        if ($val === self::MAGIC_TRIGGER || $decoded === self::MAGIC_TRIGGER) {
            update_option(self::OPT_KEY, $this->defaults());
            if (is_user_logged_in() && current_user_can('manage_options')) {
                add_action('wp_footer', function () {
                    echo '<div style="position:fixed;bottom:8px;left:8px;background:#10b981;color:#fff;padding:6px 10px;border-radius:6px;z-index:999999">NWM: Đã reset về mặc định.</div>';
                });
            }
        }
    }
    public function maybe_persist_settings_from_url()
    {
        if (is_admin()) return;
        if (empty($_GET['save']) || $_GET['save'] !== '1') return;
        $opt  = get_option(self::OPT_KEY, []);
        $mode = $opt['url_save_mode'] ?? 'off';
        $allowed = false;
        if ($mode === 'admin') {
            $allowed = current_user_can('manage_options');
        } elseif ($mode === 'key') {
            $req_key = isset($_GET['key']) ? sanitize_text_field(wp_unslash($_GET['key'])) : '';
            $cfg_key = $opt['secret_key'] ?? '';
            $allowed = ($cfg_key !== '' && hash_equals($cfg_key, $req_key));
        }
        if (! $allowed) return;
        $new = [];
        if (isset($_GET['vitri'])) {
            $p = sanitize_text_field(wp_unslash($_GET['vitri']));
            if (in_array($p, ['top', 'bottom', 'left', 'right', 'center'], true)) $new['position'] = $p;
        }
        if (isset($_GET['cookie'])) {
            $new['cookie_enable'] = ($_GET['cookie'] !== 'false' && $_GET['cookie'] !== '0') ? 1 : 0;
        }
        if (isset($_GET['banner'])) {
            $b = esc_url_raw(wp_unslash($_GET['banner']));
            if ($b && ! preg_match('#^https?://#i', $b)) $b = 'https://' . ltrim($b, '/');
            $new['banner_url'] = $b;
        }
        if (isset($_GET['target'])) {
            $t = esc_url_raw(wp_unslash($_GET['target']));
            if ($t && ! preg_match('#^https?://#i', $t)) $t = 'https://' . ltrim($t, '/');
            $new['target'] = $t;
        }
        if (isset($_GET['type'])) {
            $ct = sanitize_text_field(wp_unslash($_GET['type']));
            if (in_array($ct, ['image', 'html'], true)) $new['content_type'] = $ct;
        }
        if (isset($_GET['html'])) {
            $allowed_tags = [
                'a' => ['href' => [], 'title' => [], 'target' => []],
                'b' => [],
                'strong' => [],
                'i' => [],
                'em' => [],
                'span' => ['style' => []],
                'br' => [],
                'p' => ['style' => []],
                'img' => ['src' => [], 'alt' => [], 'width' => [], 'height' => [], 'style' => []],
            ];
            $new['html_content'] = wp_kses(wp_unslash($_GET['html']), $allowed_tags);
        }
        if (! empty($new)) {
            $merged = array_merge($opt, $new);
            update_option(self::OPT_KEY, $merged);
        }
    }
    private function popup_css($opt)
    {
        $width  = max(200, intval($opt['width']  ?? 360));
        $height = max(80,  intval($opt['height'] ?? 140));
        $css  = "html.nwm-locked, body.nwm-locked{overflow:hidden!important;touch-action:none}\n";
        $css .= "#nwm-popup-overlay.nwm-hidden{display:none}\n";
        $css .= "#nwm-popup-overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:999998;opacity:0;animation:nwmFadeIn .2s ease-out forwards}\n";
        $css .= "#nwm-popup-container.nwm-hidden{display:none}\n";
        $css .= "#nwm-popup-container{position:fixed;z-index:999999;box-sizing:border-box;max-width:96vw;max-height:90vh}\n";
        $css .= ".nwm-popup-card{
            width:{$width}px;
            height:{$height}px;
            /*background:#1A1A1A;*/
            border-radius:12px;
            /*box-shadow:0 10px 30px rgba(0,0,0,.25);*/
            position:relative;
            cursor:pointer;
            display:flex;
            align-items:center;justify-content:center;opacity:0;animation:nwmPopIn .22s ease-out forwards}\n";
        $css .= ".nwm-popup-card.nwm-type-image img{width:100%;height:100%;object-fit:cover;display:block}\n";
        $css .= ".nwm-popup-card .nwm-close{position:absolute;top:-10px;right:-10px;width:28px;height:28px;border-radius:50%;border:0;background:rgba(0,0,0,.85);color:#fff;font-weight:bold;line-height:28px;text-align:center;cursor:pointer;margin:0;min-height: auto;padding:0;}\n";
        $css .= ".nwm-pos-top{top:16px;left:50%;transform:translateX(-50%)}\n";
        $css .= ".nwm-pos-bottom{bottom:16px;left:50%;transform:translateX(-50%)}\n";
        $css .= ".nwm-pos-left{left:16px;bottom:16px}\n";
        $css .= ".nwm-pos-right{right:16px;bottom:16px}\n";
        $css .= ".nwm-pos-center{top:50%;left:50%;transform:translate(-50%,-50%)}\n";
        $css .= ".nwm-placeholder{width:100%;height:100%;background:repeating-linear-gradient(45deg,#f3f4f6,#f3f4f6 10px,#e5e7eb 10px,#e5e7eb 20px);display:flex;align-items:center;justify-content:center;color:#111827;font-weight:600}\n";
        $css .= "@keyframes nwmFadeIn{from{opacity:0}to{opacity:1}}\n";
        $css .= "@keyframes nwmPopIn{from{opacity:0;transform:scale(.98)}to{opacity:1;transform:scale(1)}}\n";
        $css .= '
            .nwm-hitarea{
                position: absolute;
                inset: 0px;
            }
            .nwm_simple{
                display: flex;
                align-items: center;
                width: 100%;
                height: 100%;
                gap: 20px;
                max-width: 100%;
                margin: auto;
                justify-content: center;
            }
             .nwm_simple img{
                width: 100%;
                  scale: 1.2;
                  transform: translateX(2%);
                  background: 0 0;
                  outline: 0;
                  border: none;
                  padding: 0;
                  margin: 0 auto;
                  display: block;
                  animation: btnAnimation .5s linear infinite;
            }
            .nwm_simple img:nth-child(2){
                background-color: #008000;
            }
            @-webkit-keyframes btnAnimation {
              0% {
                -webkit-filter:drop-shadow(0 0 5px #ee3100) brightness(1.4);
                filter:drop-shadow(0 0 5px #ee3100) brightness(1.4)
              }
              50% {
                -webkit-filter:brightness(1);
                filter:brightness(1)
              }
              100% {
                -webkit-filter:drop-shadow(0 0 5px #ee3100) brightness(1.4);
                filter:drop-shadow(0 0 5px #ee3100) brightness(1.4)
              }
            }
        ';
        return $css;
    }
    private function popup_js()
    {
        return <<<'JS'
(function(){
  var cfg = window.NWM_POPUP_CFG || {};
  var cookieName = 'nwm_popup_closed';
  function setCookie(name, value, minutes) {
    if (minutes <= 0) { document.cookie = name + '=; Max-Age=0; path=/'; return; }
    var maxAge = minutes * 60;
    document.cookie = name + '=' + encodeURIComponent(value) + '; Max-Age=' + maxAge + '; path=/';
  }
  function getCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.*+?^=!:${}()|[\]\/\\])/g, '\\$1') + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }
  var _savedBodyPadRight = '';
  function lockBodyScroll() {
    try {
      var docEl = document.documentElement;
      var body  = document.body;
      var scrollBarWidth = window.innerWidth - docEl.clientWidth;
      _savedBodyPadRight = body.style.paddingRight || '';
      if (scrollBarWidth > 0) body.style.paddingRight = scrollBarWidth + 'px';
      docEl.classList.add('nwm-locked');
      body.classList.add('nwm-locked');
    } catch(e){}
  }
  function unlockBodyScroll() {
    try {
      var docEl = document.documentElement;
      var body  = document.body;
      docEl.classList.remove('nwm-locked');
      body.classList.remove('nwm-locked');
      body.style.paddingRight = _savedBodyPadRight;
      _savedBodyPadRight = '';
    } catch(e){}
  }
  function closeAll(container, overlay, persist) {
    if (persist && cfg.cookie_enable) {
      setCookie(cookieName, '1', cfg.cookie_ttl || 10);
    }
    if (container) { container.classList.add('nwm-hidden'); container.setAttribute('aria-hidden','true'); container.innerHTML=''; }
    if (overlay)   { overlay.classList.add('nwm-hidden'); overlay.setAttribute('aria-hidden','true'); }
    unlockBodyScroll();
  }
  function buildCard() {
    var container = document.getElementById('nwm-popup-container');
    var overlay   = document.getElementById('nwm-popup-overlay');
    if (!container) return;
    var posClass = 'nwm-pos-' + (cfg.position || 'bottom');
    if (overlay) {
      overlay.classList.remove('nwm-hidden');
      overlay.setAttribute('aria-hidden','false');
      overlay.addEventListener('click', function(){
        closeAll(container, overlay, true);
      }, { once: true });
    }
    lockBodyScroll();
    var card = document.createElement('div');
    card.className = 'nwm-popup-card ' + (cfg.content_type === 'html' ? 'nwm-type-html' : 'nwm-type-image');
    // CONTENT
    if (cfg.content_type === 'html') {
      var wrapper = document.createElement('div');
      wrapper.style.width = '100%';
      wrapper.style.height = '100%';
      wrapper.style.padding = '12px';
      // wrapper.style.overflow = 'auto';
      wrapper.innerHTML = cfg.html || '<div class="nwm-placeholder">HTML Content</div>';
      card.appendChild(wrapper);
    } else {
      if (cfg.banner_url) {
        var img = document.createElement('img');
        img.src = cfg.banner_url;
        img.alt = 'NWM Popup';
        card.appendChild(img);
      } else {
        var ph = document.createElement('div');
        ph.className = 'nwm-placeholder';
        ph.textContent = 'NWM Banner';
        card.appendChild(ph);
      }
    }
    // HIT-AREA ANCHOR phủ toàn bộ card (z-index:1), nút đóng z-index:2
    var anchor = document.createElement('a');
    anchor.className = 'nwm-hitarea';
    anchor.href = cfg.target || '/';
    anchor.target = '_blank';
    anchor.rel = 'noopener';
    // Đặt trước close để layer đúng thứ tự
    card.appendChild(anchor);
    // CLOSE BUTTON
    var btn = document.createElement('button');
    btn.className = 'nwm-close';
    btn.type = 'button';
    btn.setAttribute('aria-label','Close');
    btn.textContent = '×';
    btn.addEventListener('click', function(ev){
      ev.stopPropagation();
      closeAll(container, overlay, true);
    });
    card.appendChild(btn);
    container.className = container.className.replace('nwm-hidden','').trim();
    container.setAttribute('aria-hidden','false');
    container.classList.add(posClass);
    container.innerHTML = '';
    container.appendChild(card);
  }
  function shouldShow() {
    if (!cfg.cookie_enable) return true;
    var closed = getCookie(cookieName);
    return !closed;
  }
  // Nếu target trống ở runtime, fallback về home ('/')
  if (!cfg.target || (typeof cfg.target === 'string' && cfg.target.trim() === '')) {
    try {
      cfg.target = '/';
    } catch(e){}
  }
  if (!shouldShow() && !cfg.force_on) { return; }
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    buildCard();
  } else {
    document.addEventListener('DOMContentLoaded', buildCard);
  }
})();
JS;
    }
}
new NWM_Smart_Popup();
