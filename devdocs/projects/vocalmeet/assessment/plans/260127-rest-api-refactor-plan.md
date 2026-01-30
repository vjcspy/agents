# 📋 [ASSESSMENT: 2026-01-27] - Refactor to WordPress REST API

## References

- `devdocs/vocalmeet/assessment/plans/260127-woocommerce-rest-api-plugin-plan.md` (original plan)
- `vocalmeet/assessment/wordpress`
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [WooCommerce REST API Docs](https://woocommerce.github.io/woocommerce-rest-api-docs/)

## User Requirements

Refactor plugin từ `admin-ajax.php` sang **Custom REST API** (`register_rest_route`) để:
- Follow WordPress modern best practices (từ WP 4.7+)
- RESTful design với proper HTTP methods
- Built-in permission callbacks & schema validation
- Dễ test và maintain hơn

## 🎯 Objective

Chuyển đổi AJAX handler của plugin `vocalmeet-woo-api` từ `admin-ajax.php` sang **WordPress REST API** với:
- Custom namespace: `vocalmeet-woo-api/v1`
- Endpoint: `POST /wp-json/vocalmeet-woo-api/v1/products`
- Proper permission callback
- Schema-based input validation
- Nonce verification via `X-WP-Nonce` header

### ⚠️ Key Considerations

- **Backward Compatibility**: Không cần giữ `admin-ajax.php` endpoint cũ (assessment project)
- **Nonce Type**: Dùng `wp_rest` nonce thay vì custom nonce
- **Content-Type**: REST API nhận `application/json` thay vì `application/x-www-form-urlencoded`
- **Error Response**: Dùng `WP_Error` để trả proper HTTP status codes (giữ đúng error taxonomy theo nguồn lỗi)
- **Fetch Credentials**: Explicit `credentials: 'same-origin'` để đảm bảo cookies luôn được gửi kèm request
- **Authorization Policy**: Demo có thể require login; production nên enforce capability gần domain (`manage_woocommerce`, `publish_products`)
- **Customer Login UX**: Link “Log in” nên dẫn tới WooCommerce My Account (`/my-account`) thay vì `wp-login.php` (login theo customer)
- **CORS**: Không cần config vì same-origin request
- **Keep Existing**: Giữ nguyên `Vocalmeet_Woo_Api_Handler` class (API wrapper)
- **Woo REST API Call**: Vẫn gọi WooCommerce REST API server-side để đúng yêu cầu bài thi (không expose credentials ra browser)

---

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Review existing `admin-ajax.php` implementation
  - **Outcome**: Hiểu flow hiện tại: nonce verification → input sanitization → call API handler → JSON response
- [ ] Define REST API schema
  - **Outcome**: Schema cho `name` (string, required) và `price` (number, required, min: 0.01)
- [ ] Identify files to modify
  - **Outcome**: 
    - **Delete**: `includes/class-ajax-handler.php`
    - **Create**: `includes/class-rest-controller.php`
    - **Modify**: `vocalmeet-woo-api.php`, `includes/class-product-form.php`, `assets/js/product-form.js`

---

### Phase 2: Implementation (File Structure)

```
vocalmeet/assessment/wordpress/wp-content/plugins/
└── vocalmeet-woo-api/
    ├── vocalmeet-woo-api.php           # 🔄 MODIFY - Register REST controller
    ├── uninstall.php                   # ✅ NO CHANGE
    ├── includes/
    │   ├── class-woo-api-handler.php   # ✅ NO CHANGE - WooCommerce API wrapper
    │   ├── class-ajax-handler.php      # ❌ DELETE - Replaced by REST controller
    │   ├── class-rest-controller.php   # 🚧 CREATE - New REST API endpoint
    │   └── class-product-form.php      # 🔄 MODIFY - Update wp_localize_script
    ├── assets/
    │   ├── js/
    │   │   └── product-form.js         # 🔄 MODIFY - Use fetch/REST instead of admin-ajax
    │   └── css/
    │       └── product-form.css        # ✅ NO CHANGE
    └── templates/
        └── product-form.php            # ✅ NO CHANGE
```

---

### Phase 3: Detailed Implementation Steps

#### 3.1 Create REST Controller Class

File: `includes/class-rest-controller.php`

```php
<?php
/**
 * REST API Controller for product creation
 *
 * @package Vocalmeet_Woo_API
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * REST Controller class
 */
class Vocalmeet_Woo_Api_REST_Controller {

	/**
	 * API namespace
	 */
	const NAMESPACE = 'vocalmeet-woo-api/v1';

	/**
	 * Route base
	 */
	const REST_BASE = 'products';

	/**
	 * API Handler instance
	 *
	 * @var Vocalmeet_Woo_Api_Handler
	 */
	private $api_handler;

	/**
	 * Constructor
	 *
	 * @param Vocalmeet_Woo_Api_Handler $api_handler API handler instance.
	 */
	public function __construct( Vocalmeet_Woo_Api_Handler $api_handler ) {
		$this->api_handler = $api_handler;
	}

	/**
	 * Register REST routes
	 */
	public function register(): void {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
	}

	/**
	 * Register the routes for the objects of the controller.
	 */
	public function register_routes(): void {
		register_rest_route(
			self::NAMESPACE,
			'/' . self::REST_BASE,
			array(
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'callback'            => array( $this, 'create_product' ),
					'permission_callback' => array( $this, 'create_product_permissions_check' ),
					'args'                => $this->get_endpoint_args_for_create(),
				),
			)
		);
	}

	/**
	 * Get endpoint arguments for create
	 *
	 * @return array
	 */
	public function get_endpoint_args_for_create(): array {
		return array(
			'name'  => array(
				'description'       => __( 'Product name.', 'vocalmeet-woo-api' ),
				'type'              => 'string',
				'required'          => true,
				'sanitize_callback' => 'sanitize_text_field',
				'validate_callback' => function ( $value ) {
					if ( empty( trim( $value ) ) ) {
						return new WP_Error(
							'rest_invalid_param',
							__( 'Product name cannot be empty.', 'vocalmeet-woo-api' ),
							array( 'status' => 400 )
						);
					}
					return true;
				},
			),
			'price' => array(
				'description'       => __( 'Product price.', 'vocalmeet-woo-api' ),
				'type'              => 'number',
				'required'          => true,
				'minimum'           => 0.01,
				'sanitize_callback' => function ( $value ) {
					return function_exists( 'wc_format_decimal' )
						? wc_format_decimal( $value )
						: (string) floatval( $value );
				},
				'validate_callback' => function ( $value ) {
					$price = floatval( $value );
					if ( $price <= 0 ) {
						return new WP_Error(
							'rest_invalid_param',
							__( 'Price must be greater than 0.', 'vocalmeet-woo-api' ),
							array( 'status' => 400 )
						);
					}
					return true;
				},
			),
		);
	}

	/**
	 * Check if user has permission to create products
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return bool|WP_Error
	 */
	public function create_product_permissions_check( WP_REST_Request $request ) {
		// Demo: require login only
		if ( ! is_user_logged_in() ) {
			return new WP_Error(
				'rest_forbidden',
				__( 'Please log in to create products.', 'vocalmeet-woo-api' ),
				array( 'status' => 401 )
			);
		}

		// Production: uncomment for stricter permission
		// if ( ! current_user_can( 'publish_products' ) ) {
		//     return new WP_Error(
		//         'rest_forbidden',
		//         __( 'You do not have permission to create products.', 'vocalmeet-woo-api' ),
		//         array( 'status' => 403 )
		//     );
		// }

		return true;
	}

	/**
	 * Create a product
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return WP_REST_Response|WP_Error
	 */
	public function create_product( WP_REST_Request $request ) {
		$name  = $request->get_param( 'name' );
		$price = $request->get_param( 'price' );

		$result = $this->api_handler->create_product( $name, $price );

		if ( is_wp_error( $result ) ) {
			$error_data = $result->get_error_data();
			$status     = 500;

			if ( is_array( $error_data ) && isset( $error_data['status'] ) ) {
				$status = (int) $error_data['status'];
			}

			return new WP_Error(
				$result->get_error_code(),
				$result->get_error_message(),
				array( 'status' => $status )
			);
		}

		return rest_ensure_response(
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
- [ ] Create REST controller class file
- [ ] Implement `register_routes()` with proper namespace
- [ ] Implement schema-based validation
- [ ] Implement permission callback
- [ ] Implement `create_product()` endpoint

---

#### 3.2 Update Main Plugin File

File: `vocalmeet-woo-api.php`

**Changes:**
- Remove: `require_once` for `class-ajax-handler.php`
- Add: `require_once` for `class-rest-controller.php`
- Replace: `Vocalmeet_Woo_Api_Ajax_Handler` → `Vocalmeet_Woo_Api_REST_Controller`

```php
// REMOVE this line:
// require_once VOCALMEET_WOO_API_PLUGIN_DIR . '/includes/class-ajax-handler.php';

// ADD this line:
require_once VOCALMEET_WOO_API_PLUGIN_DIR . '/includes/class-rest-controller.php';

// In plugins_loaded callback, REPLACE:
// $ajax = new Vocalmeet_Woo_Api_Ajax_Handler( $api_handler );
// $ajax->register();

// WITH:
$rest = new Vocalmeet_Woo_Api_REST_Controller( $api_handler );
$rest->register();
```

**Tasks:**
- [ ] Update require statements
- [ ] Replace AJAX handler with REST controller instantiation

---

#### 3.3 Update Product Form Class

File: `includes/class-product-form.php`

**Changes to `wp_localize_script()`:**

```php
wp_localize_script(
	'vocalmeet-product-form',
	'vocalmeetWooAPI',
	array(
		// CHANGE: Use REST endpoint instead of admin-ajax.php
		'rest_url' => esc_url_raw( rest_url( 'vocalmeet-woo-api/v1/products' ) ),
		// CHANGE: Use wp_rest nonce
		'nonce'    => wp_create_nonce( 'wp_rest' ),
		'i18n'     => array(
			'submitting'    => __( 'Creating product...', 'vocalmeet-woo-api' ),
			'error'         => __( 'Error creating product.', 'vocalmeet-woo-api' ),
			'missing_name'  => __( 'Please enter a product name.', 'vocalmeet-woo-api' ),
			'missing_price' => __( 'Please enter a valid price.', 'vocalmeet-woo-api' ),
		),
	)
);
```

**Tasks:**
- [ ] Replace `ajax_url` → `rest_url`
- [ ] Replace custom nonce → `wp_rest` nonce
- [ ] Remove `action` parameter (not needed for REST)
- [ ] Update login link: dùng `wc_get_page_permalink( 'myaccount' )` (kèm redirect về page hiện tại nếu cần)

---

#### 3.4 Update JavaScript

File: `assets/js/product-form.js`

**Major Changes:**
- Use `fetch()` API thay vì jQuery `$.ajax()` (modern approach)
- Send JSON body thay vì form data
- Add `X-WP-Nonce` header
- Handle REST API response format

```javascript
(function() {
	'use strict';

	const VocalMeetProductForm = {

		init: function() {
			this.form = document.getElementById('vocalmeet-product-form');
			if (!this.form) return;

			this.submitBtn = this.form.querySelector('.vocalmeet-submit-btn');
			this.message = document.getElementById('vocalmeet-form-message');
			this.nameInput = document.getElementById('vocalmeet-product-name');
			this.priceInput = document.getElementById('vocalmeet-product-price');
			this.originalBtnText = this.submitBtn.textContent;

			this.bindEvents();
		},

		bindEvents: function() {
			this.form.addEventListener('submit', this.handleSubmit.bind(this));
		},

		handleSubmit: async function(e) {
			e.preventDefault();

			const name = this.nameInput.value.trim();
			const price = parseFloat(this.priceInput.value);

			// Reset validation states
			this.nameInput.classList.remove('is-invalid');
			this.priceInput.classList.remove('is-invalid');

			// Client-side validation
			if (!name) {
				this.nameInput.classList.add('is-invalid');
				this.showMessage(vocalmeetWooAPI.i18n.missing_name, 'warning');
				this.nameInput.focus();
				return;
			}

			if (!price || price <= 0) {
				this.priceInput.classList.add('is-invalid');
				this.showMessage(vocalmeetWooAPI.i18n.missing_price, 'warning');
				this.priceInput.focus();
				return;
			}

			this.setLoading(true);

			try {
				const response = await fetch(vocalmeetWooAPI.rest_url, {
					method: 'POST',
					credentials: 'same-origin',
					headers: {
						'Content-Type': 'application/json',
						'X-WP-Nonce': vocalmeetWooAPI.nonce,
					},
					body: JSON.stringify({ name, price }),
				});

				const data = await response.json();

				if (response.ok) {
					this.handleSuccess(data);
				} else {
					this.handleError(data);
				}
			} catch (error) {
				this.handleError({ message: vocalmeetWooAPI.i18n.error });
			} finally {
				this.setLoading(false);
			}
		},

		handleSuccess: function(data) {
			const message = `
				<strong>${data.message}</strong><br>
				<a href="${data.product_url}" target="_blank" class="alert-link">
					View "${data.product_name}" →
				</a>
			`;
			this.showMessage(message, 'success');
			this.form.reset();
		},

		handleError: function(data) {
			const message = data.message || vocalmeetWooAPI.i18n.error;
			this.showMessage(message, 'danger');
		},

		setLoading: function(loading) {
			this.submitBtn.disabled = loading;
			if (loading) {
				this.submitBtn.innerHTML =
					'<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ' +
					vocalmeetWooAPI.i18n.submitting;
			} else {
				this.submitBtn.textContent = this.originalBtnText;
			}
		},

		showMessage: function(text, type) {
			this.message.className = `alert alert-${type}`;
			this.message.innerHTML = text;
			this.message.style.display = 'block';
		},
	};

	document.addEventListener('DOMContentLoaded', function() {
		VocalMeetProductForm.init();
	});

})();
```

**Tasks:**
- [ ] Replace jQuery `$.ajax()` with native `fetch()` API
- [ ] Update to send JSON body with `Content-Type: application/json`
- [ ] Add `X-WP-Nonce` header for authentication
- [ ] Update response handling for REST API format
- [ ] Remove jQuery dependency (optional enhancement)

---

#### 3.5 Delete Old AJAX Handler

- [ ] Delete file: `includes/class-ajax-handler.php`

---

### Phase 4: Testing & Verification

#### 4.1 REST API Testing

```bash
# Test endpoint exists (should return 401 without auth)
curl -X POST "https://localhost/wp-json/vocalmeet-woo-api/v1/products" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 19.99}'

# Test with valid WordPress cookie + nonce (via browser DevTools)
```

#### 4.2 Test Checklist

| Test Case | Expected Result | Status |
|-----------|-----------------|--------|
| REST route registered | Endpoint appears in `/wp-json/` | ⏳ |
| Unauthenticated request | 401 Unauthorized | ⏳ |
| Missing name | 400 Bad Request + validation message | ⏳ |
| Invalid price (0 or negative) | 400 Bad Request + validation message | ⏳ |
| Valid submission | 200 OK + product data | ⏳ |
| Product created in WooCommerce | Product visible in Admin | ⏳ |
| Form UI works correctly | Success/error messages display | ⏳ |
| No JS console errors | Clean console | ⏳ |

#### 4.3 Browser DevTools Verification

- [ ] Network tab: Request goes to `/wp-json/vocalmeet-woo-api/v1/products`
- [ ] Network tab: Request headers include `X-WP-Nonce` and `Content-Type: application/json`
- [ ] Network tab: Request body is JSON format
- [ ] Network tab: Response is proper REST response

---

## 📊 Summary of Results

> Do not summarize until implementation is done

### ✅ Completed Achievements

- [ ] REST Controller created with proper namespace
- [ ] Schema-based validation working
- [ ] Permission callback implemented
- [ ] Frontend updated to use `fetch()` API
- [ ] Old AJAX handler removed
- [ ] All tests passing

---

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Potential Enhancements (Optional)

- [ ] **Rate Limiting**: Consider adding rate limiting via `rest_pre_dispatch` filter
- [ ] **Response Schema**: Add response schema for documentation
- [ ] **Additional Endpoints**: 
  - `GET /products` - List products created by user
  - `GET /products/{id}` - Get single product
  - `DELETE /products/{id}` - Delete product
- [ ] **OpenAPI/Swagger**: Generate API documentation

---

## 📝 Files Summary

| Action | File | Description |
|--------|------|-------------|
| CREATE | `includes/class-rest-controller.php` | New REST API endpoint |
| DELETE | `includes/class-ajax-handler.php` | Old AJAX handler |
| MODIFY | `vocalmeet-woo-api.php` | Update bootstrap |
| MODIFY | `includes/class-product-form.php` | Update localize script |
| MODIFY | `assets/js/product-form.js` | Use fetch() + REST |

---

## ✅ Success Criteria

1. [ ] `GET /wp-json/vocalmeet-woo-api/v1` returns route info
2. [ ] `POST /wp-json/vocalmeet-woo-api/v1/products` creates product
3. [ ] Proper HTTP status codes (200, 400, 401, 500)
4. [ ] Form works as before but uses REST API
5. [ ] No `admin-ajax.php` calls in Network tab
6. [ ] Clean uninstall still works
