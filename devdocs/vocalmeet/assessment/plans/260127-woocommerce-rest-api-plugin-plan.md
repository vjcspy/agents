# 📋 [ASSESSMENT: 2026-01-27] - WooCommerce REST API Plugin (Task I/II)

## References

- `vocalmeet/assessment/wordpress`
- `devdocs/vocalmeet/assessment/OVERVIEW.md`
- [WooCommerce REST API Docs](https://woocommerce.github.io/woocommerce-rest-api-docs/)

## User Requirements

Từ Assessment description:

> I and II) Understand the WooCommerce Rest API: Connect to the WooCommerce REST API using standard authentication methods recommended by WooCommerce.
> Build a page within WordPress where a user can create a WooCommerce product on the website (not through the admin dashboard). Fields for product name and price are sufficient.

## 🎯 Objective

Tạo Plugin `vocalmeet-woo-api` cho phép:

- User tạo WooCommerce product từ frontend page (không qua admin)
- Kết nối WooCommerce REST API với authentication chuẩn
- Form tối thiểu: Product Name + Price
- Demonstrate WordPress best practices: hooks, nonce, sanitization, AJAX

### ⚠️ Key Considerations

- **Security First**: Không expose API credentials ra browser
- **WordPress Way**: Dùng `wp_ajax_*`, `wp_localize_script`, nonce verification
- **Clean Architecture**: Separation of concerns (API handler, Form handler, AJAX handler)
- **Error Handling**: Graceful error messages, validation feedback
- **Reusability**: API wrapper có thể reuse cho Plugin 2 (Elementor widget)
- **i18n Ready**: Tất cả strings dùng `__()`, `_e()` với text domain
- **Clean Uninstall**: Xóa options khi plugin bị xóa
- **Modern UI**: Bootstrap 5 cho professional look, responsive design

---

## 🎯 Design Decisions

### Permission Model

**Question:** Assessment nói "user can create a product" - "user" là ai?

| Option | Pros | Cons |
|--------|------|------|
| Guest (no login) | Dễ test | Security risk, spam products |
| Any logged-in user | Balance security/usability | Có thể không phù hợp production |
| Shop Manager+ only | Most secure | Quá restrictive cho demo |

**Decision:** Yêu cầu **logged-in user** (`is_user_logged_in()`).

**Rationale:**
- Assessment không specify role → không over-engineer
- Logged-in đủ để demonstrate security awareness
- Comment trong code cho thấy biết về `current_user_can('publish_products')` cho production

```php
// Demo: require login
if (!is_user_logged_in()) {
    return '<p>Please log in to create products.</p>';
}

// Production: uncomment for stricter permission
// if (!current_user_can('publish_products')) {
//     wp_send_json_error(['message' => 'Permission denied'], 403);
// }
```

### UI Framework Choice

| Option | Pros | Cons |
|--------|------|------|
| Custom CSS | Full control, no deps | More work, basic look |
| **Bootstrap 5** | Popular, professional, responsive | ~25KB CSS |
| Tailwind CSS | Modern | Requires build process |

**Decision:** Dùng **Bootstrap 5** vì:
- Widely recognized, professional look
- Built-in responsive grid
- CDN delivery (no build required)
- Form components, alerts, cards sẵn có
- Easily customizable với CSS overrides

**Conflict Prevention:**
- Scope Bootstrap trong `.vocalmeet-product-form-wrapper`
- Minimal custom CSS chỉ override khi cần

---

### WooCommerce Authentication Method

WooCommerce REST API hỗ trợ nhiều auth methods:

| Method | Use Case | Security Level |
|--------|----------|----------------|
| **Basic Auth** | Server-to-server over HTTPS | ✅ Good (our choice) |
| OAuth 1.0a | External apps, no HTTPS | ✅ Good |
| API Keys in URL | Testing only | ❌ Insecure |

**Decision:** Dùng **Basic Auth** vì:
- Server-to-server call (PHP → WooCommerce API)
- HTTPS required (self-signed OK for local)
- Simpler implementation, same security level

---

## 📁 Plugin Structure

```
vocalmeet/assessment/wordpress/wp-content/plugins/
└── vocalmeet-woo-api/
    ├── vocalmeet-woo-api.php           # Main plugin file, bootstrap
    ├── uninstall.php                   # Cleanup on plugin deletion
    ├── includes/
    │   ├── class-woo-api-handler.php   # WooCommerce REST API wrapper
    │   ├── class-product-form.php      # Shortcode registration + rendering
    │   └── class-ajax-handler.php      # AJAX endpoint handlers
    ├── assets/
    │   ├── js/
    │   │   └── product-form.js         # Form validation + AJAX submission
    │   └── css/
    │       └── product-form.css        # Form styling
    └── templates/
        └── product-form.php            # Form HTML template
```

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER FLOW                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User visits page with shortcode [vocalmeet_product_form]        │
│     └─▶ PHP renders form + enqueue JS/CSS                           │
│     └─▶ wp_localize_script passes nonce + ajax_url                  │
│                                                                     │
│  2. User fills form (name, price) and clicks Submit                 │
│     └─▶ JS validates input client-side                              │
│     └─▶ JS sends AJAX POST to wp-admin/admin-ajax.php               │
│         (action: vocalmeet_create_product, nonce, name, price)      │
│                                                                     │
│  3. Server receives AJAX request                                    │
│     └─▶ wp_ajax_vocalmeet_create_product hook fires                 │
│     └─▶ Verify nonce (wp_verify_nonce)                              │
│     └─▶ Check logged-in user                                        │
│     └─▶ Sanitize input (sanitize_text_field, wc_format_decimal)     │
│     └─▶ Optional: capability check (current_user_can)               │
│                                                                     │
│  4. Server calls WooCommerce REST API                               │
│     └─▶ POST /wp-json/wc/v3/products                                │
│     └─▶ Authentication: Consumer Key + Secret (server-side only)    │
│     └─▶ Returns product_id on success                               │
│                                                                     │
│  5. Server returns JSON response to browser                         │
│     └─▶ Success: { success: true, product_id: 123, message: "..." } │
│     └─▶ Error: { success: false, message: "Error description" }     │
│                                                                     │
│  6. JS updates UI                                                   │
│     └─▶ Show success message + link to product                      │
│     └─▶ Or show error message                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Implementation Plan

### Phase 1: Prerequisites & Environment Check

- [ ] Verify WordPress + WooCommerce đang chạy (`just start`)
- [ ] Verify HTTPS working (self-signed cert OK)
- [ ] Nếu WP-CLI bị fatal `Allowed memory size...` (thường do Elementor): tăng `memory_limit` qua `devtools/vocalmeet/local/php/runtime.ini` và mount vào cả `wordpress` + `wpcli` trong `devtools/vocalmeet/local/docker-compose-assessment.yaml`, sau đó `just restart`
- [ ] Generate WooCommerce REST API credentials:
  - WP Admin → WooCommerce → Settings → Advanced → REST API
  - Create new key với permissions: Read/Write
  - Save Consumer Key + Consumer Secret
- [ ] Test API endpoint manually:
  ```bash
  curl -k -X GET "https://localhost/wp-json/wc/v3/products" \
    -u "consumer_key:consumer_secret"
  ```

**Outcome**: API credentials ready, endpoint accessible.

---

### Phase 2: Plugin Bootstrap

#### 2.1 Create main plugin file

File: `vocalmeet-woo-api.php`

```php
<?php
/*
Plugin Name: VocalMeet WooCommerce API
Version: 1.0.0
Text Domain: vocalmeet-woo-api
Requires Plugins: woocommerce
*/

if ( ! defined( 'ABSPATH' ) ) {
	die();
}

define( 'VOCALMEET_WOO_API_VERSION', '1.0.0' );
define( 'VOCALMEET_WOO_API_PLUGIN_FILE', __FILE__ );
define( 'VOCALMEET_WOO_API_PLUGIN_DIR', __DIR__ );
define( 'VOCALMEET_WOO_API_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

require_once VOCALMEET_WOO_API_PLUGIN_DIR . '/includes/class-woo-api-handler.php';
require_once VOCALMEET_WOO_API_PLUGIN_DIR . '/includes/class-ajax-handler.php';
require_once VOCALMEET_WOO_API_PLUGIN_DIR . '/includes/class-product-form.php';

add_action(
	'init',
	function () {
		load_plugin_textdomain( 'vocalmeet-woo-api', false, dirname( plugin_basename( __FILE__ ) ) . '/languages' );
	}
);

function vocalmeet_woo_api_missing_wc_notice(): void {
	?>
	<div class="notice notice-error">
		<p><?php esc_html_e( 'VocalMeet WooCommerce API requires WooCommerce to be installed and active.', 'vocalmeet-woo-api' ); ?></p>
	</div>
	<?php
}

add_action(
	'plugins_loaded',
	function () {
		if ( ! class_exists( 'WooCommerce' ) ) {
			add_action( 'admin_notices', 'vocalmeet_woo_api_missing_wc_notice' );
			return;
		}

		$api_handler = new Vocalmeet_Woo_Api_Handler();

		$form = new Vocalmeet_Woo_Api_Product_Form();
		$form->register();

		$ajax = new Vocalmeet_Woo_Api_Ajax_Handler( $api_handler );
		$ajax->register();
	}
);
```

**Tasks:**
- [ ] Create plugin directory structure
- [ ] Create main plugin file with header
- [ ] Add WooCommerce dependency check
- [ ] Test plugin activation in WP Admin

---

### Phase 3: API Handler Class

#### 3.1 WooCommerce API Wrapper

File: `includes/class-woo-api-handler.php`

Responsibilities:
- Store/retrieve API credentials securely
- Make authenticated requests to WooCommerce REST API
- Handle API errors gracefully

```php
class Vocalmeet_Woo_Api_Handler {
	public function create_product( string $name, string $price ) {
		$credentials = $this->get_credentials();
		if ( is_wp_error( $credentials ) ) {
			return $credentials;
		}

		$endpoint  = rest_url( 'wc/v3/products' );
		$sslverify = $this->get_sslverify();

		$body = array(
			'name'          => $name,
			'type'          => 'simple',
			'regular_price' => (string) $price,
			'status'        => 'publish',
		);

		$response = wp_remote_post(
			$endpoint,
			array(
				'headers'   => array(
					'Authorization' => 'Basic ' . base64_encode( $credentials['consumer_key'] . ':' . $credentials['consumer_secret'] ),
					'Content-Type'  => 'application/json',
				),
				'body'      => wp_json_encode( $body ),
				'timeout'   => 30,
				'sslverify' => $sslverify,
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$status_code   = (int) wp_remote_retrieve_response_code( $response );
		$response_body = wp_remote_retrieve_body( $response );
		$decoded_body  = json_decode( $response_body, true );

		if ( 201 !== $status_code ) {
			$message = is_array( $decoded_body ) && isset( $decoded_body['message'] ) ? (string) $decoded_body['message'] : __( 'Unknown WooCommerce API error.', 'vocalmeet-woo-api' );
			return new WP_Error( 'vocalmeet_woo_api_error', $message, array( 'status' => $status_code ) );
		}

		if ( ! is_array( $decoded_body ) ) {
			return new WP_Error( 'vocalmeet_woo_api_invalid_response', __( 'Invalid response from WooCommerce API.', 'vocalmeet-woo-api' ) );
		}

		return $decoded_body;
	}

	private function get_credentials() {
		$consumer_key    = defined( 'VOCALMEET_WOO_CONSUMER_KEY' ) ? (string) VOCALMEET_WOO_CONSUMER_KEY : (string) get_option( 'vocalmeet_woo_consumer_key', '' );
		$consumer_secret = defined( 'VOCALMEET_WOO_CONSUMER_SECRET' ) ? (string) VOCALMEET_WOO_CONSUMER_SECRET : (string) get_option( 'vocalmeet_woo_consumer_secret', '' );

		$consumer_key    = trim( $consumer_key );
		$consumer_secret = trim( $consumer_secret );

		if ( '' === $consumer_key || '' === $consumer_secret ) {
			return new WP_Error( 'vocalmeet_woo_api_missing_credentials', __( 'WooCommerce REST API credentials are missing.', 'vocalmeet-woo-api' ) );
		}

		return array(
			'consumer_key'    => $consumer_key,
			'consumer_secret' => $consumer_secret,
		);
	}

	private function get_sslverify(): bool {
		$sslverify = true;

		if ( defined( 'VOCALMEET_WOO_API_SSLVERIFY' ) ) {
			$sslverify = (bool) VOCALMEET_WOO_API_SSLVERIFY;
		}

		if ( false === $sslverify && ( ! defined( 'WP_ENVIRONMENT_TYPE' ) || 'local' !== WP_ENVIRONMENT_TYPE ) ) {
			$sslverify = true;
		}

		return $sslverify;
	}
}
```

**Tasks:**
- [ ] Create API handler class
- [ ] Implement credential loading (options + constants fallback)
- [ ] Implement `create_product()` method
- [ ] Test API call manually (via temporary admin page or WP-CLI)

**Security Notes:**
- Credentials NEVER sent to browser
- `sslverify` mặc định `true`; chỉ cho phép tắt khi `WP_ENVIRONMENT_TYPE === 'local'` và có flag rõ ràng (`VOCALMEET_WOO_API_SSLVERIFY`)
- Consider encrypting credentials in `wp_options`

---

### Phase 4: AJAX Handler

#### 4.1 AJAX Endpoint

File: `includes/class-ajax-handler.php`

```php
class Vocalmeet_Woo_Api_Ajax_Handler {
	public const ACTION       = 'vocalmeet_create_product';
	public const NONCE_ACTION = 'vocalmeet_woo_api_nonce';

	private $api_handler;

	public function __construct( Vocalmeet_Woo_Api_Handler $api_handler ) {
		$this->api_handler = $api_handler;
	}

	public function register(): void {
		add_action( 'wp_ajax_' . self::ACTION, array( $this, 'handle_create_product' ) );
	}

	public function handle_create_product(): void {
		if ( ! is_user_logged_in() ) {
			wp_send_json_error( array( 'message' => __( 'Please log in to create products.', 'vocalmeet-woo-api' ) ), 401 );
		}

		$nonce_ok = check_ajax_referer( self::NONCE_ACTION, 'nonce', false );
		if ( ! $nonce_ok ) {
			wp_send_json_error( array( 'message' => __( 'Security check failed.', 'vocalmeet-woo-api' ) ), 403 );
		}

		$name  = isset( $_POST['product_name'] ) ? sanitize_text_field( wp_unslash( $_POST['product_name'] ) ) : '';
		$price = '';

		if ( isset( $_POST['product_price'] ) ) {
			$raw_price = wp_unslash( $_POST['product_price'] );
			$price     = function_exists( 'wc_format_decimal' ) ? wc_format_decimal( $raw_price ) : (string) floatval( $raw_price );
		}

		if ( '' === $name ) {
			wp_send_json_error( array( 'message' => __( 'Product name is required.', 'vocalmeet-woo-api' ) ), 400 );
		}

		if ( '' === $price || (float) $price <= 0 ) {
			wp_send_json_error( array( 'message' => __( 'Price must be greater than 0.', 'vocalmeet-woo-api' ) ), 400 );
		}

		$result = $this->api_handler->create_product( $name, $price );
		if ( is_wp_error( $result ) ) {
			wp_send_json_error( array( 'message' => $result->get_error_message() ), 500 );
		}

		wp_send_json_success(
			array(
				'message'      => __( 'Product created successfully!', 'vocalmeet-woo-api' ),
				'product_id'   => (int) ( $result['id'] ?? 0 ),
				'product_name' => (string) ( $result['name'] ?? $name ),
				'product_url'  => (string) ( $result['permalink'] ?? '' ),
			)
		);
	}
}
```

**Tasks:**
- [ ] Create AJAX handler class
- [ ] Implement nonce verification
- [ ] Implement input sanitization
- [ ] Implement validation with clear error messages
- [ ] Connect to API handler
- [ ] Test AJAX endpoint via browser DevTools

---

### Phase 5: Shortcode & Form

#### 5.1 Product Form Class

File: `includes/class-product-form.php`

```php
namespace VocalMeet\WooAPI;

class Product_Form {
    
    const SHORTCODE = 'vocalmeet_product_form';
    
    public static function init() {
        add_shortcode(self::SHORTCODE, [__CLASS__, 'render_shortcode']);
        add_action('wp_enqueue_scripts', [__CLASS__, 'enqueue_assets']);
    }
    
    /**
     * Enqueue assets - See Phase 7 for full Bootstrap implementation
     */
    public static function enqueue_assets() {
        // Only load on pages with our shortcode
        global $post;
        if (!is_a($post, 'WP_Post') || !has_shortcode($post->post_content, self::SHORTCODE)) {
            return;
        }
        
        // See Phase 7 for full Bootstrap enqueue implementation
        // Bootstrap CSS, Icons, Custom CSS, JS, wp_localize_script
    }
    
    public static function render_shortcode($atts) {
        $atts = shortcode_atts([
            'button_text' => __('Create Product', 'vocalmeet-woo-api'),
        ], $atts, self::SHORTCODE);
        
        // Check if user is logged in
        // Decision: require login for demo; production would use current_user_can()
        if (!is_user_logged_in()) {
            return '<div class="container"><div class="row justify-content-center"><div class="col-md-6">' .
                '<div class="alert alert-warning" role="alert">' .
                '<i class="bi bi-exclamation-triangle me-2"></i>' .
                esc_html__('Please log in to create products.', 'vocalmeet-woo-api') .
                ' <a href="' . esc_url(wp_login_url(get_permalink())) . '" class="alert-link">' .
                esc_html__('Log in', 'vocalmeet-woo-api') . '</a>' .
                '</div></div></div></div>';
        }
        
        ob_start();
        include VOCALMEET_WOO_API_PATH . 'templates/product-form.php';
        return ob_get_clean();
    }
}
```

#### 5.2 Form Template (Bootstrap 5)

File: `templates/product-form.php`

```php
<?php
/**
 * Product creation form template (Bootstrap 5)
 * 
 * @var array $atts Shortcode attributes
 */

if (!defined('ABSPATH')) {
    exit;
}
?>

<div class="vocalmeet-product-form-wrapper">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="card">
                    <div class="card-header bg-dark text-white">
                        <h5 class="card-title mb-0">
                            <i class="bi bi-plus-circle me-2"></i>
                            <?php esc_html_e('Create New Product', 'vocalmeet-woo-api'); ?>
                        </h5>
                    </div>
                    <div class="card-body">
                        <form id="vocalmeet-product-form">
                            <div class="mb-3">
                                <label for="vocalmeet-product-name" class="form-label">
                                    <?php esc_html_e('Product Name', 'vocalmeet-woo-api'); ?>
                                    <span class="text-danger">*</span>
                                </label>
                                <input 
                                    type="text" 
                                    class="form-control" 
                                    id="vocalmeet-product-name" 
                                    name="product_name" 
                                    required
                                    placeholder="<?php esc_attr_e('Enter product name', 'vocalmeet-woo-api'); ?>"
                                >
                            </div>
                            
                            <div class="mb-3">
                                <label for="vocalmeet-product-price" class="form-label">
                                    <?php esc_html_e('Price', 'vocalmeet-woo-api'); ?>
                                    <span class="text-danger">*</span>
                                </label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input 
                                        type="number" 
                                        class="form-control" 
                                        id="vocalmeet-product-price" 
                                        name="product_price" 
                                        required
                                        min="0.01"
                                        step="0.01"
                                        placeholder="0.00"
                                    >
                                </div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-dark btn-lg vocalmeet-submit-btn">
                                    <?php echo esc_html($atts['button_text']); ?>
                                </button>
                            </div>
                            
                            <div id="vocalmeet-form-message" class="mt-3" style="display:none;"></div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

**Tasks:**
- [ ] Create Product_Form class
- [ ] Implement conditional asset loading (chỉ khi có shortcode)
- [ ] Implement `wp_localize_script` với nonce + ajax_url
- [ ] Create form template
- [ ] Test shortcode renders correctly on a page

---

### Phase 6: JavaScript

#### 6.1 Form Handler JS

File: `assets/js/product-form.js`

```javascript
(function($) {
    'use strict';
    
    const VocalMeetProductForm = {
        
        init: function() {
            this.form = $('#vocalmeet-product-form');
            this.submitBtn = this.form.find('.vocalmeet-submit-btn');
            this.message = $('#vocalmeet-form-message');
            this.originalBtnText = this.submitBtn.text();
            
            this.bindEvents();
        },
        
        bindEvents: function() {
            this.form.on('submit', this.handleSubmit.bind(this));
        },
        
        handleSubmit: function(e) {
            e.preventDefault();
            
            const nameInput = $('#vocalmeet-product-name');
            const priceInput = $('#vocalmeet-product-price');
            const name = nameInput.val().trim();
            const price = parseFloat(priceInput.val());
            
            // Reset validation states
            nameInput.removeClass('is-invalid');
            priceInput.removeClass('is-invalid');
            
            // Client-side validation with Bootstrap styling
            if (!name) {
                nameInput.addClass('is-invalid');
                this.showMessage('Please enter a product name.', 'warning');
                nameInput.focus();
                return;
            }
            
            if (!price || price <= 0) {
                priceInput.addClass('is-invalid');
                this.showMessage('Please enter a valid price.', 'warning');
                priceInput.focus();
                return;
            }
            
            this.setLoading(true);
            
            $.ajax({
                url: vocalmeetWooAPI.ajax_url,
                type: 'POST',
                data: {
                    action: vocalmeetWooAPI.action,
                    nonce: vocalmeetWooAPI.nonce,
                    product_name: name,
                    product_price: price,
                },
                success: this.handleSuccess.bind(this),
                error: this.handleError.bind(this),
                complete: () => this.setLoading(false),
            });
        },
        
        handleSuccess: function(response) {
            if (response.success) {
                const data = response.data;
                const message = `
                    <strong>${data.message}</strong><br>
                    <a href="${data.product_url}" target="_blank" class="alert-link">
                        View "${data.product_name}" →
                    </a>
                `;
                this.showMessage(message, 'success');
                this.form[0].reset();
            } else {
                this.showMessage(response.data.message || 'Unknown error', 'danger');
            }
        },
        
        handleError: function(xhr) {
            let message = vocalmeetWooAPI.i18n.error;
            
            if (xhr.responseJSON && xhr.responseJSON.data) {
                message = xhr.responseJSON.data.message || message;
            }
            
            this.showMessage(message, 'danger');
        },
        
        setLoading: function(loading) {
            this.submitBtn.prop('disabled', loading);
            if (loading) {
                this.submitBtn.html(
                    '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>' +
                    vocalmeetWooAPI.i18n.submitting
                );
            } else {
                this.submitBtn.text(this.originalBtnText);
            }
        },
        
        showMessage: function(text, type) {
            // type: 'success', 'danger', 'warning', 'info'
            const alertClass = `alert alert-${type}`;
            this.message
                .removeClass()
                .addClass(alertClass)
                .html(text)
                .slideDown();
        },
    };
    
    $(document).ready(function() {
        if ($('#vocalmeet-product-form').length) {
            VocalMeetProductForm.init();
        }
    });
    
})(jQuery);
```

**Tasks:**
- [ ] Create JavaScript file
- [ ] Implement client-side validation
- [ ] Implement AJAX submission
- [ ] Implement loading state
- [ ] Implement success/error message display
- [ ] Test full flow in browser

---

### Phase 7: Bootstrap Integration & Styling

#### 7.1 Bootstrap Enqueue

Update `includes/class-product-form.php` để enqueue Bootstrap:

```php
public function enqueue_assets(): void {
	global $post;

	if ( ! is_a( $post, 'WP_Post' ) || ! has_shortcode( $post->post_content, self::SHORTCODE ) ) {
		return;
	}

	wp_enqueue_style(
		'bootstrap',
		'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
		array(),
		'5.3.3'
	);

	wp_enqueue_style(
		'bootstrap-icons',
		'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
		array(),
		'1.11.3'
	);

	wp_enqueue_style(
		'vocalmeet-product-form',
		VOCALMEET_WOO_API_PLUGIN_URL . 'assets/css/product-form.css',
		array( 'bootstrap' ),
		VOCALMEET_WOO_API_VERSION
	);

	wp_enqueue_script(
		'vocalmeet-product-form',
		VOCALMEET_WOO_API_PLUGIN_URL . 'assets/js/product-form.js',
		array( 'jquery' ),
		VOCALMEET_WOO_API_VERSION,
		true
	);

	wp_localize_script(
		'vocalmeet-product-form',
		'vocalmeetWooAPI',
		array(
			'ajax_url' => admin_url( 'admin-ajax.php' ),
			'nonce'    => wp_create_nonce( Vocalmeet_Woo_Api_Ajax_Handler::NONCE_ACTION ),
			'action'   => Vocalmeet_Woo_Api_Ajax_Handler::ACTION,
			'i18n'     => array(
				'submitting'    => __( 'Creating product...', 'vocalmeet-woo-api' ),
				'error'         => __( 'Error creating product.', 'vocalmeet-woo-api' ),
				'missing_name'  => __( 'Please enter a product name.', 'vocalmeet-woo-api' ),
				'missing_price' => __( 'Please enter a valid price.', 'vocalmeet-woo-api' ),
				'view_product'  => __( 'View', 'vocalmeet-woo-api' ),
				'unknown_error' => __( 'Unknown error', 'vocalmeet-woo-api' ),
			),
		)
	);
}
```

#### 7.2 Custom Overrides (Minimal)

File: `assets/css/product-form.css`

```css
.vocalmeet-product-form-wrapper .card {
	box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
}

.vocalmeet-product-form-wrapper .card-header {
	border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.vocalmeet-product-form-wrapper .btn-dark {
	background-color: #111;
	border-color: #111;
}

.vocalmeet-product-form-wrapper .btn-dark:hover,
.vocalmeet-product-form-wrapper .btn-dark:focus {
	background-color: #000;
	border-color: #000;
}

.vocalmeet-product-form-wrapper .vocalmeet-submit-btn:disabled {
	cursor: not-allowed;
	opacity: 0.7;
}

.vocalmeet-product-form-wrapper .vocalmeet-submit-btn .spinner-border {
	width: 1rem;
	height: 1rem;
	margin-right: 0.5rem;
}

.vocalmeet-product-form-wrapper #vocalmeet-form-message a {
	color: inherit;
	text-decoration: underline;
	font-weight: 600;
}
```

#### 7.3 Bootstrap Icons

Đã bật sẵn `bootstrap-icons` để dùng icon trong form template (ví dụ: `bi bi-plus-circle`).

**Tasks:**
- [ ] Enqueue Bootstrap CSS from CDN
- [ ] Enqueue Bootstrap Icons
- [ ] Create minimal custom CSS for overrides
- [ ] Test no conflicts with WordPress theme
- [ ] Test responsive behavior

---

### Phase 8: Configuration & Settings

#### 8.1 API Credentials Setup

**Option A: Via wp-config.php (Recommended for assessment)**

```php
// In wp-config.php
define('VOCALMEET_WOO_CONSUMER_KEY', 'ck_your_key_here');
define('VOCALMEET_WOO_CONSUMER_SECRET', 'cs_your_secret_here');
```

**Option B: Via WP Options (for production)**

- Create simple admin page under WooCommerce settings
- Store encrypted credentials in `wp_options`

**Tasks:**
- [ ] Add validation for missing credentials (show admin notice)

---

### Phase 9: i18n & Uninstall Cleanup

#### 9.1 Load Text Domain

Thêm vào `vocalmeet-woo-api.php`:

```php
// Load text domain for translations
add_action('init', 'vocalmeet_woo_api_load_textdomain');

function vocalmeet_woo_api_load_textdomain() {
    load_plugin_textdomain(
        'vocalmeet-woo-api',
        false,
        dirname(plugin_basename(__FILE__)) . '/languages'
    );
}
```

#### 9.2 Uninstall Cleanup

File: `uninstall.php`

```php
<?php
/**
 * Uninstall script - runs when plugin is deleted via WP Admin
 * 
 * This file is called by WordPress when user deletes the plugin.
 * It cleans up all plugin data from the database.
 *
 * @package VocalMeet_Woo_API
 */

// Exit if not called by WordPress uninstall
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Delete plugin options
delete_option('vocalmeet_woo_consumer_key');
delete_option('vocalmeet_woo_consumer_secret');

// Optional: Delete any transients
delete_transient('vocalmeet_woo_api_cache');

// Optional: Clean up user meta if any
// delete_metadata('user', 0, 'vocalmeet_woo_preference', '', true);
```

**Why this matters:**
- Shows respect for user's database
- Professional practice that junior devs often skip
- Evaluator sẽ notice clean uninstall behavior

**Tasks:**
- [ ] Create `uninstall.php`
- [ ] Load text domain in main plugin file
- [ ] Ensure all user-facing strings use `__()` or `_e()`
- [ ] Test uninstall removes options from database

---

### Phase 10: Testing & Verification

#### 10.1 Manual Test Checklist

| Test Case | Expected Result | Status |
|-----------|-----------------|--------|
| Plugin activates without error | No PHP warnings/errors | ⏳ |
| Plugin shows notice if WooCommerce missing | Admin notice displayed | ⏳ |
| Shortcode renders form | Form visible on page | ⏳ |
| Assets load only on pages with shortcode | No extra requests on other pages | ⏳ |
| Empty name submission | Error: "Product name is required" | ⏳ |
| Invalid price (0 or negative) | Error: "Price must be greater than 0" | ⏳ |
| Valid submission | Success message + product link | ⏳ |
| Product appears in WooCommerce | Product visible in Admin → Products | ⏳ |
| Non-logged-in user | "Please log in" message | ⏳ |
| Invalid nonce (manual test) | "Security check failed" error | ⏳ |
| Plugin deletion | Options removed from wp_options | ⏳ |

#### 10.2 Browser DevTools Verification

- [ ] Network tab: AJAX request shows correct payload
- [ ] Network tab: Response is valid JSON
- [ ] Console: No JavaScript errors
- [ ] Application tab: No sensitive data in localStorage/sessionStorage

---

## 🔐 Security & Quality Checklist

| Concern | Implementation | Status |
|---------|---------------|--------|
| API Credentials | Server-side only, never in JS | ⏳ |
| Nonce verification | `check_ajax_referer()` | ⏳ |
| Input sanitization | `sanitize_text_field()`, `floatval()` | ⏳ |
| Output escaping | `esc_html()`, `esc_attr()` in templates | ⏳ |
| XSS prevention | No raw `$_POST` in output | ⏳ |
| User permission | `is_user_logged_in()` (documented: `current_user_can()`) | ⏳ |
| i18n ready | All strings use `__()`, `_e()` | ⏳ |
| Clean uninstall | `uninstall.php` removes options | ⏳ |

---

## 📝 Files to Create

| # | File | Purpose |
|---|------|---------|
| 1 | `vocalmeet-woo-api.php` | Plugin bootstrap + text domain |
| 2 | `uninstall.php` | Cleanup on plugin deletion |
| 3 | `includes/class-woo-api-handler.php` | WooCommerce API wrapper |
| 4 | `includes/class-ajax-handler.php` | AJAX endpoint |
| 5 | `includes/class-product-form.php` | Shortcode + asset loading |
| 6 | `assets/js/product-form.js` | Form JavaScript |
| 7 | `assets/css/product-form.css` | Form styling |
| 8 | `templates/product-form.php` | Form HTML |

---

## 🚧 Outstanding Issues & Follow-up

- [x] ~~Decide: Allow non-logged-in users to create products?~~ → **Decision: Require login** (see Design Decisions)
- [ ] Consider: Add admin settings page for API credentials? (nice-to-have, not required)
- [ ] Consider: Rate limiting to prevent abuse? (production concern, skip for assessment)
- [ ] Consider: Add more product fields (description, image)? (beyond requirement scope)

---

## ✅ Success Criteria

When complete, the following must work:

1. [ ] Plugin activates without errors
2. [ ] Page with `[vocalmeet_product_form]` shows form
3. [ ] Logged-in user can create product via form
4. [ ] Product appears in WooCommerce Admin
5. [ ] No JS console errors
6. [ ] No PHP warnings in debug.log
7. [ ] API credentials are NOT exposed in browser
8. [ ] All user-facing strings are translatable (i18n)
9. [ ] Plugin deletion cleans up options (uninstall.php works)
