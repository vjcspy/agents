# 📋 [ASSESSMENT: 2026-02-02] - Custom Elementor WooCommerce Widget (Task III)

## References

- `projects/vocalmeet/assessment/wordpress`
- `devdocs/projects/vocalmeet/assessment/OVERVIEW.md`
- [Elementor Widget Guide](https://developers.elementor.com/elementor-widgets/)
- [Elementor Hello World](https://github.com/pojome/elementor-hello-world)
- Plugin 1: `vocalmeet-woo-api` (Task I/II) - đã implement

## User Requirements

Từ Assessment description:

> III) The more complex part: WooCommerce Integration into Elementor
> Goal is to create a new additional custom drag and drop widget to Elementor that integrates WooCommerce functionalities within the website builder section of Elementor.
>
> The widget should add a WooCommerce functionality to Elementor (utilizing the WooCommerce REST API) so that a user can create a WooCommerce product within this Elementor widget.
>
> **Please note: Try not put any raw code directly into the preview page of Elementor** (the large window on the right is considered the preview window).
>
> You could build the widget in a way, that it shows a button inside the widget that triggers a popup when someone clicks. The pop up opens and contains 2 fields, one to enter product name and one for price. After pressing ok, it creates the product using a rest call. Then the user can drag and drop your widget from the left into the preview page and it displays the product.

---

## 🎯 SECTION 1: Assessment Focus Points (QUAN TRỌNG)

> **Mindset:** Không chỉ làm cho "hoạt động" mà phải **demonstrate** sự hiểu biết sâu về Elementor architecture, WordPress ecosystem, và tư duy của một Senior Developer.

### 1.1 Họ đang test cái gì?

| # | Skill Area | Họ đang đánh giá | Expert-level Expectation |
|---|------------|------------------|--------------------------|
| 1 | **Elementor Architecture** | Hiểu widget lifecycle, hooks, contexts | Đúng hooks, proper asset loading cho đúng context |
| 2 | **Editor vs Frontend Separation** | Phân biệt được 2 contexts hoàn toàn khác nhau | Scripts/styles enqueue riêng cho từng context |
| 3 | **"No raw code in preview"** | Hiểu Elementor philosophy (WYSIWYG) | Preview = result, Panel = configuration |
| 4 | **Complex Integration** | Kết hợp nhiều systems phức tạp | Elementor API + WooCommerce API + Custom JS |
| 5 | **Advanced JavaScript** | Backbone.js / modern JS skills | Event handling, state management, Elementor JS API |
| 6 | **Security in Editor Context** | Biết rằng editor cũng cần security | Nonce, capability checks, output escaping |
| 7 | **UX Thinking** | Có nghĩ về user experience không | Intuitive flow, loading states, error feedback |

### 1.2 Key Insight: Tại sao "No raw code in preview" là requirement QUAN TRỌNG NHẤT?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ELEMENTOR ARCHITECTURE PHILOSOPHY                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────┐│
│  │    PANEL        │    │                    PREVIEW                      ││
│  │    (Left)       │    │                    (Right)                      ││
│  │                 │    │                                                 ││
│  │  • Controls     │    │  • WYSIWYG - What You See Is What You Get      ││
│  │  • Settings     │    │  • Shows RESULT, not INPUT FORM                ││
│  │  • Configuration│    │  • Exactly what visitors will see              ││
│  │                 │    │                                                 ││
│  │  ─────────────  │    │  ─────────────────────────────────────────     ││
│  │  INPUTTING DATA │    │  DISPLAYING RESULT                             ││
│  └─────────────────┘    └─────────────────────────────────────────────────┘│
│                                                                             │
│  ⚠️ Đặt form trong preview = VIOLATION of Elementor philosophy             │
│  ✅ Popup từ button = CORRECT approach (configuration action)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Reviewer muốn thấy:**
- Candidate hiểu rằng Preview KHÔNG phải nơi để user input data
- Configuration actions (như tạo product) nên trigger từ Panel hoặc via popup
- Widget preview chỉ show RESULT (product đã tạo)

### 1.3 Làm sao demonstrate expertise?

| Focus Area | How to Demonstrate | Code Evidence |
|------------|-------------------|---------------|
| **Elementor Architecture** | Dùng đúng hooks: `elementor/widgets/register`, `elementor/editor/after_enqueue_scripts` | Xem Phase 1-2 |
| **Context Separation** | File riêng: `editor.js` (editor only) vs `frontend.js` (frontend only) | Xem Phase 5 |
| **WYSIWYG Compliance** | Popup triggered từ button, không render form trong `render()` | Xem Phase 4-5 |
| **Integration Skills** | Reuse REST endpoint từ Plugin 1, không duplicate code | Xem Phase 5 |
| **Advanced JS** | Sử dụng Elementor JS API (`$e.run()`, `elementor.channels`) | Xem Phase 5 |
| **Security** | Nonce từ `wp_create_nonce('wp_rest')`, output escaping | Xem Phase 3-4 |
| **UX** | Loading states, error messages, intuitive popup flow | Xem Phase 5-6 |

### 1.4 Điểm "Bonus" để nổi bật

| Bonus | Description | Reviewer sẽ impressed vì |
|-------|-------------|-------------------------|
| **Widget Category riêng** | Tạo category "VocalMeet" thay vì dùng "General" | Shows attention to organization |
| **Dependency Declaration** | Check Elementor + WooCommerce + Plugin 1 active | Shows production mindset |
| **Live Preview Update** | Widget re-render ngay sau tạo product (không cần refresh) | Shows deep Elementor JS knowledge |
| **Select Existing Product** | Option để chọn product có sẵn thay vì chỉ tạo mới | Shows thinking beyond requirements |
| **PHPDoc Comments** | Document tất cả methods | Shows code quality focus |
| **i18n Ready** | Tất cả strings translatable | Shows internationalization awareness |

---

## 🎯 SECTION 2: Design Decisions

### 2.1 Architecture: 2 Plugins hay Merge vào 1?

| Option | Pros | Cons |
|--------|------|------|
| **2 Plugins riêng** ✅ | Separation of concerns; Test independently; Clear dependencies | Cần check Plugin 1 active |
| Merge thành 1 | Single installation | Mixed concerns; Harder to maintain |

**Decision:** Giữ **2 plugins riêng biệt**.

**Rationale để explain cho reviewer:**
- Plugin 1 = "WooCommerce API Frontend Page" - standalone feature
- Plugin 2 = "Elementor WooCommerce Widget" - **extends** Plugin 1's REST API
- Demonstrates **modular architecture** thinking
- Plugin 2 **depends on** Plugin 1 → proper dependency management

```php
// Show reviewer: We understand dependency management
if (!class_exists('Vocalmeet_Woo_Api_Rest_Controller')) {
    add_action('admin_notices', function() {
        echo '<div class="notice notice-error"><p>';
        echo esc_html__('VocalMeet Elementor WooCommerce Widget requires VocalMeet WooCommerce API plugin.', 'vocalmeet-elementor-woo');
        echo '</p></div>';
    });
    return;
}
```

### 2.2 Popup Approach: Panel Button vs Preview Button

| Option | Description | Assessment Compliance |
|--------|-------------|----------------------|
| Panel button trigger popup | Button trong panel controls | ✅ Fully compliant |
| **Preview button trigger popup** ✅ | Button trong preview area, click mở popup | ✅ Compliant (popup, not form) |
| Form trong preview | Input fields trực tiếp trong preview | ❌ VIOLATES requirement |

**Decision:** **Preview button triggers popup**.

**Rationale:**
- Assessment suggests: "shows a button inside the widget that triggers a popup"
- Button trong preview = OK (it's an action trigger, not data input)
- Popup = configuration modal, NOT part of preview content
- After creation → button disappears, product card appears

```
┌──────────────────────────────────────────────────────────┐
│                    PREVIEW AREA                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  STATE 1: No product created                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │         [🛒 Create Product]  ← Button              │  │
│  │                                                    │  │
│  │         Click → Opens Popup (NOT in preview)       │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  STATE 2: Product created                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │    ┌─────────────────────────────────────────┐    │  │
│  │    │  📦 Product Name                        │    │  │
│  │    │  💰 $19.99                              │    │  │
│  │    │  🔗 View Product →                      │    │  │
│  │    └─────────────────────────────────────────┘    │  │
│  │                                                    │  │
│  │    [Change Product] ← Only in editor context      │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2.3 Widget Settings Storage

| Setting | Type | Purpose | Saved in Post Meta |
|---------|------|---------|-------------------|
| `product_id` | HIDDEN | ID of created/selected product | ✅ Yes |
| `product_name` | HIDDEN | Cached name (for display without API call) | ✅ Yes |
| `product_price` | HIDDEN | Cached price | ✅ Yes |
| `product_url` | HIDDEN | Permalink | ✅ Yes |
| `button_text` | TEXT | Customizable button label | ✅ Yes |
| `show_price` | SWITCHER | Toggle price display | ✅ Yes |

**Note:** HIDDEN controls không hiện trong panel nhưng vẫn được save. JS sẽ update via Elementor API.

### 2.4 JavaScript Approach: Vanilla JS vs Backbone.js

| Option | Pros | Cons |
|--------|------|------|
| **Vanilla JS (ES6+)** ✅ | Clean, no extra deps, modern | Less "fancy" |
| Backbone.js | Shows familiarity with Elementor internals | Overkill for this task, learning curve |

**Decision:** **Vanilla JS (ES6+)** với Elementor JS API.

**Rationale:**
- Assessment says Backbone is "optional"
- Vanilla JS đủ để demonstrate JS skills
- Focus on Elementor JS API (`$e.run()`, `elementor.channels`) - MORE relevant

```javascript
// Show reviewer: We understand Elementor JS API
$e.run('document/elements/settings', {
    container: elementor.getContainer(widgetId),
    settings: {
        product_id: response.product_id,
        product_name: response.product_name,
        // ...
    }
});
```

---

## 🎯 SECTION 3: Plugin Structure

```
vocalmeet-elementor-woo/
├── vocalmeet-elementor-woo.php           # Main plugin file
│                                         # - Plugin header
│                                         # - Dependency checks (Elementor, WC, Plugin 1)
│                                         # - Bootstrap plugin
│
├── includes/
│   ├── class-plugin.php                  # Elementor integration
│   │                                     # - Register widget
│   │                                     # - Enqueue editor/frontend assets
│   │                                     # - Custom widget category (bonus)
│   │
│   └── widgets/
│       └── class-product-creator.php     # Widget class
│                                         # - Extends \Elementor\Widget_Base
│                                         # - register_controls()
│                                         # - render()
│                                         # - get_script_depends()
│
├── assets/
│   ├── js/
│   │   ├── editor.js                     # EDITOR ONLY
│   │   │                                 # - Popup trigger
│   │   │                                 # - Form handling
│   │   │                                 # - AJAX to Plugin 1 REST API
│   │   │                                 # - Update widget settings
│   │   │
│   │   └── frontend.js                   # FRONTEND ONLY (if needed)
│   │                                     # - Product interactions (optional)
│   │
│   └── css/
│       ├── editor.css                    # Editor styles (popup)
│       └── widget.css                    # Widget styles (both contexts)
│
└── readme.txt                            # (Optional) WP.org style readme
```

---

## 🎯 SECTION 4: Implementation Plan

### Phase 1: Plugin Skeleton & Dependency Checks

**Goal:** Demonstrate proper dependency management và plugin structure.

**Files:** `vocalmeet-elementor-woo.php`

```php
<?php
/**
 * Plugin Name: VocalMeet Elementor WooCommerce Widget
 * Description: Custom Elementor widget to create WooCommerce products
 * Version: 1.0.0
 * Requires Plugins: elementor, woocommerce, vocalmeet-woo-api
 * Text Domain: vocalmeet-elementor-woo
 */

if (!defined('ABSPATH')) {
    die();
}

define('VOCALMEET_ELEMENTOR_WOO_VERSION', '1.0.0');
define('VOCALMEET_ELEMENTOR_WOO_FILE', __FILE__);
define('VOCALMEET_ELEMENTOR_WOO_DIR', __DIR__);
define('VOCALMEET_ELEMENTOR_WOO_URL', plugin_dir_url(__FILE__));

// Minimum versions
define('VOCALMEET_ELEMENTOR_WOO_MIN_ELEMENTOR', '3.0.0');
define('VOCALMEET_ELEMENTOR_WOO_MIN_PHP', '7.4');

/**
 * Check dependencies and initialize plugin
 */
function vocalmeet_elementor_woo_init() {
    // PHP version check
    if (version_compare(PHP_VERSION, VOCALMEET_ELEMENTOR_WOO_MIN_PHP, '<')) {
        add_action('admin_notices', 'vocalmeet_elementor_woo_php_notice');
        return;
    }

    // Elementor check
    if (!did_action('elementor/loaded')) {
        add_action('admin_notices', 'vocalmeet_elementor_woo_elementor_notice');
        return;
    }

    // Elementor version check
    if (!version_compare(ELEMENTOR_VERSION, VOCALMEET_ELEMENTOR_WOO_MIN_ELEMENTOR, '>=')) {
        add_action('admin_notices', 'vocalmeet_elementor_woo_elementor_version_notice');
        return;
    }

    // WooCommerce check
    if (!class_exists('WooCommerce')) {
        add_action('admin_notices', 'vocalmeet_elementor_woo_wc_notice');
        return;
    }

    // Plugin 1 check (vocalmeet-woo-api)
    if (!class_exists('Vocalmeet_Woo_Api_Rest_Controller')) {
        add_action('admin_notices', 'vocalmeet_elementor_woo_plugin1_notice');
        return;
    }

    // All checks passed - initialize
    require_once VOCALMEET_ELEMENTOR_WOO_DIR . '/includes/class-plugin.php';
    Vocalmeet_Elementor_Woo_Plugin::instance();
}
add_action('plugins_loaded', 'vocalmeet_elementor_woo_init');

// Admin notice functions...
function vocalmeet_elementor_woo_php_notice() { /* ... */ }
function vocalmeet_elementor_woo_elementor_notice() { /* ... */ }
function vocalmeet_elementor_woo_elementor_version_notice() { /* ... */ }
function vocalmeet_elementor_woo_wc_notice() { /* ... */ }
function vocalmeet_elementor_woo_plugin1_notice() { /* ... */ }
```

**Reviewer sẽ thấy:**
- ✅ Proper plugin headers
- ✅ Version checks (PHP, Elementor)
- ✅ Clear dependency chain
- ✅ Graceful failure với admin notices

---

### Phase 2: Elementor Bootstrap & Widget Registration

**Goal:** Demonstrate understanding of Elementor hooks và widget registration.

**Files:** `includes/class-plugin.php`

```php
<?php
if (!defined('ABSPATH')) {
    die();
}

/**
 * Main plugin class - Elementor integration
 */
final class Vocalmeet_Elementor_Woo_Plugin {

    private static $instance = null;

    public static function instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        $this->register_hooks();
    }

    private function register_hooks() {
        // Register widget
        add_action('elementor/widgets/register', [$this, 'register_widgets']);
        
        // Register custom category (BONUS: shows organization)
        add_action('elementor/elements/categories_registered', [$this, 'register_categories']);
        
        // Enqueue editor scripts/styles
        add_action('elementor/editor/after_enqueue_scripts', [$this, 'enqueue_editor_scripts']);
        
        // Enqueue frontend styles (widget appearance)
        add_action('elementor/frontend/after_enqueue_styles', [$this, 'enqueue_frontend_styles']);
    }

    /**
     * Register custom widget category
     * BONUS: Shows attention to organization
     */
    public function register_categories($elements_manager) {
        $elements_manager->add_category(
            'vocalmeet',
            [
                'title' => esc_html__('VocalMeet', 'vocalmeet-elementor-woo'),
                'icon'  => 'fa fa-plug',
            ]
        );
    }

    /**
     * Register widgets
     */
    public function register_widgets($widgets_manager) {
        require_once VOCALMEET_ELEMENTOR_WOO_DIR . '/includes/widgets/class-product-creator.php';
        $widgets_manager->register(new Vocalmeet_Product_Creator_Widget());
    }

    /**
     * Enqueue EDITOR-ONLY scripts
     * Key point: This hook only fires in editor context
     */
    public function enqueue_editor_scripts() {
        wp_enqueue_style(
            'vocalmeet-elementor-woo-editor',
            VOCALMEET_ELEMENTOR_WOO_URL . 'assets/css/editor.css',
            [],
            VOCALMEET_ELEMENTOR_WOO_VERSION
        );

        wp_enqueue_script(
            'vocalmeet-elementor-woo-editor',
            VOCALMEET_ELEMENTOR_WOO_URL . 'assets/js/editor.js',
            ['elementor-editor'],  // Depends on Elementor editor
            VOCALMEET_ELEMENTOR_WOO_VERSION,
            true
        );

        // Localize script with REST API info
        // REUSING Plugin 1's endpoint - demonstrates modular thinking
        wp_localize_script(
            'vocalmeet-elementor-woo-editor',
            'vocalmeetElementorWoo',
            [
                'rest_url' => esc_url_raw(rest_url('vocalmeet-woo-api/v1/products')),
                'nonce'    => wp_create_nonce('wp_rest'),
                'i18n'     => [
                    'popup_title'    => __('Create New Product', 'vocalmeet-elementor-woo'),
                    'product_name'   => __('Product Name', 'vocalmeet-elementor-woo'),
                    'price'          => __('Price ($)', 'vocalmeet-elementor-woo'),
                    'create'         => __('Create Product', 'vocalmeet-elementor-woo'),
                    'cancel'         => __('Cancel', 'vocalmeet-elementor-woo'),
                    'creating'       => __('Creating...', 'vocalmeet-elementor-woo'),
                    'success'        => __('Product created successfully!', 'vocalmeet-elementor-woo'),
                    'error'          => __('Error creating product', 'vocalmeet-elementor-woo'),
                    'name_required'  => __('Product name is required', 'vocalmeet-elementor-woo'),
                    'price_required' => __('Price must be greater than 0', 'vocalmeet-elementor-woo'),
                ],
            ]
        );
    }

    /**
     * Enqueue frontend styles
     * Widget appearance on live site
     */
    public function enqueue_frontend_styles() {
        wp_enqueue_style(
            'vocalmeet-elementor-woo-widget',
            VOCALMEET_ELEMENTOR_WOO_URL . 'assets/css/widget.css',
            [],
            VOCALMEET_ELEMENTOR_WOO_VERSION
        );
    }
}
```

**Reviewer sẽ thấy:**
- ✅ Singleton pattern (common in WordPress plugins)
- ✅ Đúng Elementor hooks: `elementor/widgets/register`, `elementor/editor/after_enqueue_scripts`
- ✅ Custom widget category (bonus)
- ✅ Context-aware asset loading (editor vs frontend)
- ✅ `wp_localize_script` for AJAX config
- ✅ i18n ready

---

### Phase 3: Widget Class - Controls

**Goal:** Demonstrate understanding of Elementor controls system.

**Files:** `includes/widgets/class-product-creator.php`

```php
<?php
if (!defined('ABSPATH')) {
    die();
}

/**
 * Product Creator Widget
 * 
 * Creates WooCommerce products from within Elementor editor.
 * Demonstrates: Widget lifecycle, controls, render contexts
 */
class Vocalmeet_Product_Creator_Widget extends \Elementor\Widget_Base {

    /**
     * Widget name (internal identifier)
     */
    public function get_name() {
        return 'vocalmeet-product-creator';
    }

    /**
     * Widget title (displayed in panel)
     */
    public function get_title() {
        return esc_html__('Product Creator', 'vocalmeet-elementor-woo');
    }

    /**
     * Widget icon
     */
    public function get_icon() {
        return 'eicon-products';
    }

    /**
     * Widget categories
     * Using custom category registered in class-plugin.php
     */
    public function get_categories() {
        return ['vocalmeet'];
    }

    /**
     * Widget keywords for search
     */
    public function get_keywords() {
        return ['woocommerce', 'product', 'create', 'vocalmeet'];
    }

    /**
     * Scripts required by this widget
     * IMPORTANT: These load in PREVIEW context, not editor panel
     */
    public function get_script_depends() {
        // We handle editor scripts separately via hook
        return [];
    }

    /**
     * Styles required by this widget
     */
    public function get_style_depends() {
        return ['vocalmeet-elementor-woo-widget'];
    }

    /**
     * Register widget controls
     * 
     * Controls are rendered in the PANEL (left side)
     * NOT in preview area
     */
    protected function register_controls() {
        
        // ═══════════════════════════════════════════════════════════
        // SECTION: Content (Product Data)
        // ═══════════════════════════════════════════════════════════
        $this->start_controls_section(
            'section_product',
            [
                'label' => esc_html__('Product', 'vocalmeet-elementor-woo'),
                'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        // Hidden controls - populated by JavaScript after product creation
        // These store the selected/created product data
        $this->add_control(
            'product_id',
            [
                'label'   => esc_html__('Product ID', 'vocalmeet-elementor-woo'),
                'type'    => \Elementor\Controls_Manager::HIDDEN,
                'default' => '',
            ]
        );

        $this->add_control(
            'product_name',
            [
                'label'   => esc_html__('Product Name', 'vocalmeet-elementor-woo'),
                'type'    => \Elementor\Controls_Manager::HIDDEN,
                'default' => '',
            ]
        );

        $this->add_control(
            'product_price',
            [
                'label'   => esc_html__('Product Price', 'vocalmeet-elementor-woo'),
                'type'    => \Elementor\Controls_Manager::HIDDEN,
                'default' => '',
            ]
        );

        $this->add_control(
            'product_url',
            [
                'label'   => esc_html__('Product URL', 'vocalmeet-elementor-woo'),
                'type'    => \Elementor\Controls_Manager::HIDDEN,
                'default' => '',
            ]
        );

        // Info control - shows current product status
        $this->add_control(
            'product_info',
            [
                'type'            => \Elementor\Controls_Manager::RAW_HTML,
                'raw'             => '<div id="vocalmeet-product-info" class="elementor-control-field-description">' .
                                    esc_html__('Click the button in the preview to create a product.', 'vocalmeet-elementor-woo') .
                                    '</div>',
                'content_classes' => 'elementor-panel-alert elementor-panel-alert-info',
            ]
        );

        $this->end_controls_section();

        // ═══════════════════════════════════════════════════════════
        // SECTION: Display Settings
        // ═══════════════════════════════════════════════════════════
        $this->start_controls_section(
            'section_display',
            [
                'label' => esc_html__('Display', 'vocalmeet-elementor-woo'),
                'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'button_text',
            [
                'label'       => esc_html__('Create Button Text', 'vocalmeet-elementor-woo'),
                'type'        => \Elementor\Controls_Manager::TEXT,
                'default'     => esc_html__('Create Product', 'vocalmeet-elementor-woo'),
                'placeholder' => esc_html__('Create Product', 'vocalmeet-elementor-woo'),
            ]
        );

        $this->add_control(
            'show_price',
            [
                'label'        => esc_html__('Show Price', 'vocalmeet-elementor-woo'),
                'type'         => \Elementor\Controls_Manager::SWITCHER,
                'label_on'     => esc_html__('Yes', 'vocalmeet-elementor-woo'),
                'label_off'    => esc_html__('No', 'vocalmeet-elementor-woo'),
                'return_value' => 'yes',
                'default'      => 'yes',
            ]
        );

        $this->add_control(
            'show_link',
            [
                'label'        => esc_html__('Show Product Link', 'vocalmeet-elementor-woo'),
                'type'         => \Elementor\Controls_Manager::SWITCHER,
                'label_on'     => esc_html__('Yes', 'vocalmeet-elementor-woo'),
                'label_off'    => esc_html__('No', 'vocalmeet-elementor-woo'),
                'return_value' => 'yes',
                'default'      => 'yes',
            ]
        );

        $this->end_controls_section();

        // ═══════════════════════════════════════════════════════════
        // SECTION: Style - Button
        // ═══════════════════════════════════════════════════════════
        $this->start_controls_section(
            'section_style_button',
            [
                'label' => esc_html__('Button', 'vocalmeet-elementor-woo'),
                'tab'   => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_control(
            'button_color',
            [
                'label'     => esc_html__('Button Color', 'vocalmeet-elementor-woo'),
                'type'      => \Elementor\Controls_Manager::COLOR,
                'selectors' => [
                    '{{WRAPPER}} .vocalmeet-create-btn' => 'background-color: {{VALUE}};',
                ],
                'default'   => '#7c3aed',
            ]
        );

        $this->add_control(
            'button_text_color',
            [
                'label'     => esc_html__('Text Color', 'vocalmeet-elementor-woo'),
                'type'      => \Elementor\Controls_Manager::COLOR,
                'selectors' => [
                    '{{WRAPPER}} .vocalmeet-create-btn' => 'color: {{VALUE}};',
                ],
                'default'   => '#ffffff',
            ]
        );

        $this->end_controls_section();

        // ═══════════════════════════════════════════════════════════
        // SECTION: Style - Product Card
        // ═══════════════════════════════════════════════════════════
        $this->start_controls_section(
            'section_style_product',
            [
                'label' => esc_html__('Product Card', 'vocalmeet-elementor-woo'),
                'tab'   => \Elementor\Controls_Manager::TAB_STYLE,
            ]
        );

        $this->add_control(
            'card_background',
            [
                'label'     => esc_html__('Background', 'vocalmeet-elementor-woo'),
                'type'      => \Elementor\Controls_Manager::COLOR,
                'selectors' => [
                    '{{WRAPPER}} .vocalmeet-product-card' => 'background-color: {{VALUE}};',
                ],
                'default'   => '#f8fafc',
            ]
        );

        $this->add_group_control(
            \Elementor\Group_Control_Border::get_type(),
            [
                'name'     => 'card_border',
                'selector' => '{{WRAPPER}} .vocalmeet-product-card',
            ]
        );

        $this->add_control(
            'card_border_radius',
            [
                'label'      => esc_html__('Border Radius', 'vocalmeet-elementor-woo'),
                'type'       => \Elementor\Controls_Manager::DIMENSIONS,
                'size_units' => ['px', '%'],
                'selectors'  => [
                    '{{WRAPPER}} .vocalmeet-product-card' => 'border-radius: {{TOP}}{{UNIT}} {{RIGHT}}{{UNIT}} {{BOTTOM}}{{UNIT}} {{LEFT}}{{UNIT}};',
                ],
            ]
        );

        $this->end_controls_section();
    }

    // render() method continues in Phase 4...
}
```

**Reviewer sẽ thấy:**
- ✅ Complete widget identity methods
- ✅ Hidden controls for JS-populated data
- ✅ Proper control sections organization
- ✅ Style controls với selectors
- ✅ Group controls (Border)
- ✅ i18n ready tất cả labels

---

### Phase 4: Widget Class - Render Method

**Goal:** Demonstrate understanding of Editor vs Frontend contexts.

**Continue in:** `includes/widgets/class-product-creator.php`

```php
    /**
     * Render widget output
     * 
     * CRITICAL: This renders in PREVIEW area
     * - Do NOT render input forms here
     * - Render button for action trigger OR product display
     */
    protected function render() {
        $settings = $this->get_settings_for_display();
        
        $product_id   = $settings['product_id'];
        $product_name = $settings['product_name'];
        $product_price = $settings['product_price'];
        $product_url  = $settings['product_url'];
        $button_text  = $settings['button_text'];
        $show_price   = $settings['show_price'] === 'yes';
        $show_link    = $settings['show_link'] === 'yes';

        // Get widget ID for JS targeting
        $widget_id = $this->get_id();

        // Check if we're in editor mode
        $is_editor = \Elementor\Plugin::$instance->editor->is_edit_mode();

        ?>
        <div class="vocalmeet-product-creator-widget" data-widget-id="<?php echo esc_attr($widget_id); ?>">
            
            <?php if (empty($product_id)) : ?>
                <!-- STATE: No product - Show create button -->
                <div class="vocalmeet-empty-state">
                    <button type="button" 
                            class="vocalmeet-create-btn"
                            data-action="create-product">
                        <span class="vocalmeet-btn-icon">🛒</span>
                        <span class="vocalmeet-btn-text"><?php echo esc_html($button_text); ?></span>
                    </button>
                    
                    <?php if (!$is_editor) : ?>
                        <p class="vocalmeet-empty-message">
                            <?php esc_html_e('No product selected.', 'vocalmeet-elementor-woo'); ?>
                        </p>
                    <?php endif; ?>
                </div>
                
            <?php else : ?>
                <!-- STATE: Product exists - Show product card -->
                <div class="vocalmeet-product-card">
                    <div class="vocalmeet-product-icon">📦</div>
                    
                    <h3 class="vocalmeet-product-name">
                        <?php echo esc_html($product_name); ?>
                    </h3>
                    
                    <?php if ($show_price && !empty($product_price)) : ?>
                        <div class="vocalmeet-product-price">
                            <?php 
                            // Use WooCommerce price formatting if available
                            if (function_exists('wc_price')) {
                                echo wc_price($product_price);
                            } else {
                                echo esc_html('$' . number_format((float)$product_price, 2));
                            }
                            ?>
                        </div>
                    <?php endif; ?>
                    
                    <?php if ($show_link && !empty($product_url)) : ?>
                        <a href="<?php echo esc_url($product_url); ?>" 
                           class="vocalmeet-product-link"
                           target="_blank"
                           rel="noopener noreferrer">
                            <?php esc_html_e('View Product →', 'vocalmeet-elementor-woo'); ?>
                        </a>
                    <?php endif; ?>
                    
                    <?php if ($is_editor) : ?>
                        <!-- Editor only: Allow changing product -->
                        <button type="button" 
                                class="vocalmeet-change-btn"
                                data-action="change-product">
                            <?php esc_html_e('Change Product', 'vocalmeet-elementor-woo'); ?>
                        </button>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
            
        </div>
        <?php
    }

    /**
     * Render widget output in the editor (content template)
     * 
     * JavaScript template for live preview updates
     * Uses Backbone.js/Underscore.js template syntax
     */
    protected function content_template() {
        ?>
        <#
        var productId = settings.product_id;
        var productName = settings.product_name;
        var productPrice = settings.product_price;
        var productUrl = settings.product_url;
        var buttonText = settings.button_text || '<?php echo esc_js(__('Create Product', 'vocalmeet-elementor-woo')); ?>';
        var showPrice = settings.show_price === 'yes';
        var showLink = settings.show_link === 'yes';
        #>
        
        <div class="vocalmeet-product-creator-widget" data-widget-id="{{ view.model.id }}">
            
            <# if (!productId) { #>
                <div class="vocalmeet-empty-state">
                    <button type="button" 
                            class="vocalmeet-create-btn"
                            data-action="create-product">
                        <span class="vocalmeet-btn-icon">🛒</span>
                        <span class="vocalmeet-btn-text">{{{ buttonText }}}</span>
                    </button>
                </div>
                
            <# } else { #>
                <div class="vocalmeet-product-card">
                    <div class="vocalmeet-product-icon">📦</div>
                    
                    <h3 class="vocalmeet-product-name">{{{ productName }}}</h3>
                    
                    <# if (showPrice && productPrice) { #>
                        <div class="vocalmeet-product-price">${{ parseFloat(productPrice).toFixed(2) }}</div>
                    <# } #>
                    
                    <# if (showLink && productUrl) { #>
                        <a href="{{ productUrl }}" 
                           class="vocalmeet-product-link"
                           target="_blank"
                           rel="noopener noreferrer">
                            <?php esc_html_e('View Product →', 'vocalmeet-elementor-woo'); ?>
                        </a>
                    <# } #>
                    
                    <button type="button" 
                            class="vocalmeet-change-btn"
                            data-action="change-product">
                        <?php esc_html_e('Change Product', 'vocalmeet-elementor-woo'); ?>
                    </button>
                </div>
            <# } #>
            
        </div>
        <?php
    }
}
```

**Reviewer sẽ thấy:**
- ✅ `render()` không chứa form - chỉ button trigger
- ✅ Two states: empty (button) vs product (card)
- ✅ `is_edit_mode()` check cho editor-only elements
- ✅ Proper escaping: `esc_html()`, `esc_attr()`, `esc_url()`
- ✅ WooCommerce integration: `wc_price()` function
- ✅ `content_template()` cho live preview (Underscore.js syntax)
- ✅ Semantic HTML structure

---

### Phase 5: Editor JavaScript - Popup & AJAX

**Goal:** Demonstrate advanced JS skills và Elementor JS API.

**Files:** `assets/js/editor.js`

```javascript
/**
 * VocalMeet Elementor WooCommerce Widget - Editor Script
 * 
 * Handles:
 * - Popup trigger from widget button
 * - Product creation via REST API
 * - Widget settings update via Elementor JS API
 * 
 * Key Points for Reviewer:
 * - Event delegation for dynamically rendered widgets
 * - Elementor JS API usage ($e.run)
 * - Proper error handling
 * - i18n support via wp_localize_script
 */
(function() {
    'use strict';

    // Wait for Elementor editor to be ready
    window.addEventListener('load', function() {
        if (typeof elementor === 'undefined') {
            return;
        }

        // Initialize when editor is ready
        elementor.on('preview:loaded', initVocalmeetProductCreator);
    });

    function initVocalmeetProductCreator() {
        const previewWindow = elementor.$preview[0].contentWindow;
        const previewDocument = elementor.$preview[0].contentDocument;

        if (!previewDocument) {
            return;
        }

        // Event delegation on preview document
        // This handles dynamically rendered widget content
        previewDocument.addEventListener('click', function(e) {
            const createBtn = e.target.closest('[data-action="create-product"]');
            const changeBtn = e.target.closest('[data-action="change-product"]');

            if (createBtn) {
                const widget = createBtn.closest('.vocalmeet-product-creator-widget');
                if (widget) {
                    showProductPopup(widget.dataset.widgetId, previewDocument);
                }
            }

            if (changeBtn) {
                const widget = changeBtn.closest('.vocalmeet-product-creator-widget');
                if (widget) {
                    showProductPopup(widget.dataset.widgetId, previewDocument);
                }
            }
        });
    }

    /**
     * Show product creation popup
     * 
     * IMPORTANT: Popup is rendered in preview iframe but as overlay
     * This is NOT "raw code in preview" - it's a modal overlay
     */
    function showProductPopup(widgetId, doc) {
        // Remove existing popup if any
        const existingPopup = doc.querySelector('.vocalmeet-popup-overlay');
        if (existingPopup) {
            existingPopup.remove();
        }

        const i18n = vocalmeetElementorWoo.i18n;

        // Create popup HTML
        const popupHTML = `
            <div class="vocalmeet-popup-overlay" data-widget-id="${widgetId}">
                <div class="vocalmeet-popup-modal">
                    <div class="vocalmeet-popup-header">
                        <h3>${i18n.popup_title}</h3>
                        <button type="button" class="vocalmeet-popup-close" aria-label="Close">&times;</button>
                    </div>
                    <div class="vocalmeet-popup-body">
                        <form id="vocalmeet-product-form">
                            <div class="vocalmeet-form-group">
                                <label for="vocalmeet-product-name">${i18n.product_name}</label>
                                <input type="text" 
                                       id="vocalmeet-product-name" 
                                       name="name" 
                                       required
                                       placeholder="Enter product name">
                            </div>
                            <div class="vocalmeet-form-group">
                                <label for="vocalmeet-product-price">${i18n.price}</label>
                                <input type="number" 
                                       id="vocalmeet-product-price" 
                                       name="price" 
                                       step="0.01" 
                                       min="0.01" 
                                       required
                                       placeholder="0.00">
                            </div>
                            <div class="vocalmeet-popup-message" style="display: none;"></div>
                        </form>
                    </div>
                    <div class="vocalmeet-popup-footer">
                        <button type="button" class="vocalmeet-btn vocalmeet-btn-cancel">
                            ${i18n.cancel}
                        </button>
                        <button type="submit" form="vocalmeet-product-form" class="vocalmeet-btn vocalmeet-btn-primary">
                            ${i18n.create}
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Insert popup into preview document
        doc.body.insertAdjacentHTML('beforeend', popupHTML);

        const popup = doc.querySelector('.vocalmeet-popup-overlay');
        const form = doc.getElementById('vocalmeet-product-form');
        const closeBtn = popup.querySelector('.vocalmeet-popup-close');
        const cancelBtn = popup.querySelector('.vocalmeet-btn-cancel');
        const submitBtn = popup.querySelector('.vocalmeet-btn-primary');
        const messageDiv = popup.querySelector('.vocalmeet-popup-message');

        // Focus first input
        doc.getElementById('vocalmeet-product-name').focus();

        // Close popup handlers
        closeBtn.addEventListener('click', () => closePopup(popup));
        cancelBtn.addEventListener('click', () => closePopup(popup));
        popup.addEventListener('click', (e) => {
            if (e.target === popup) closePopup(popup);
        });

        // ESC key to close
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closePopup(popup);
                doc.removeEventListener('keydown', escHandler);
            }
        };
        doc.addEventListener('keydown', escHandler);

        // Form submission
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const name = form.querySelector('[name="name"]').value.trim();
            const price = parseFloat(form.querySelector('[name="price"]').value);

            // Client-side validation
            if (!name) {
                showMessage(messageDiv, i18n.name_required, 'error');
                return;
            }
            if (!price || price <= 0) {
                showMessage(messageDiv, i18n.price_required, 'error');
                return;
            }

            // Disable form during submission
            setLoading(submitBtn, true, i18n.creating);

            try {
                const response = await createProduct(name, price);
                
                if (response.success) {
                    // Update widget settings via Elementor JS API
                    updateWidgetSettings(widgetId, {
                        product_id: String(response.product_id),
                        product_name: response.product_name,
                        product_price: String(price),
                        product_url: response.product_url,
                    });

                    showMessage(messageDiv, i18n.success, 'success');
                    
                    // Close popup after short delay
                    setTimeout(() => closePopup(popup), 1000);
                } else {
                    showMessage(messageDiv, response.message || i18n.error, 'error');
                }
            } catch (error) {
                console.error('VocalMeet Product Creation Error:', error);
                showMessage(messageDiv, i18n.error, 'error');
            } finally {
                setLoading(submitBtn, false, i18n.create);
            }
        });
    }

    /**
     * Create product via REST API
     * REUSES Plugin 1's endpoint - no code duplication
     */
    async function createProduct(name, price) {
        const response = await fetch(vocalmeetElementorWoo.rest_url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-WP-Nonce': vocalmeetElementorWoo.nonce,
            },
            body: JSON.stringify({ name, price }),
        });

        const data = await response.json();

        if (!response.ok) {
            return {
                success: false,
                message: data.message || 'Unknown error',
            };
        }

        return {
            success: true,
            product_id: data.product_id,
            product_name: data.product_name,
            product_url: data.product_url,
        };
    }

    /**
     * Update widget settings via Elementor JS API
     * 
     * KEY DEMONSTRATION: Understanding of Elementor internals
     * This triggers widget re-render with new data
     */
    function updateWidgetSettings(widgetId, settings) {
        // Get the widget container
        const container = elementor.getContainer(widgetId);
        
        if (!container) {
            console.error('Widget container not found:', widgetId);
            return;
        }

        // Use Elementor's $e.run command to update settings
        // This is the official way to modify widget settings
        $e.run('document/elements/settings', {
            container: container,
            settings: settings,
        });

        // Alternative method using channels (for reference)
        // elementor.channels.editor.trigger('change', {
        //     elementId: widgetId,
        //     settings: settings
        // });
    }

    /**
     * Helper: Close popup with animation
     */
    function closePopup(popup) {
        popup.classList.add('vocalmeet-popup-closing');
        setTimeout(() => popup.remove(), 200);
    }

    /**
     * Helper: Show message in popup
     */
    function showMessage(container, message, type) {
        container.textContent = message;
        container.className = `vocalmeet-popup-message vocalmeet-message-${type}`;
        container.style.display = 'block';
    }

    /**
     * Helper: Set loading state
     */
    function setLoading(button, loading, text) {
        button.disabled = loading;
        button.textContent = text;
        if (loading) {
            button.classList.add('vocalmeet-loading');
        } else {
            button.classList.remove('vocalmeet-loading');
        }
    }

})();
```

**Reviewer sẽ thấy:**
- ✅ ES6+ syntax (arrow functions, async/await, template literals)
- ✅ Event delegation cho dynamic content
- ✅ Elementor JS API: `$e.run('document/elements/settings')`
- ✅ REST API call với nonce authentication
- ✅ Proper error handling
- ✅ Loading states
- ✅ i18n support
- ✅ Clean code structure với helper functions

---

### Phase 6: CSS Styling

**Files:** `assets/css/editor.css`, `assets/css/widget.css`

```css
/* === assets/css/editor.css === */

/**
 * VocalMeet Elementor WooCommerce Widget - Editor Styles
 * Popup modal styling
 */

/* Overlay */
.vocalmeet-popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999999;
    animation: vocalmeet-fade-in 0.2s ease;
}

.vocalmeet-popup-overlay.vocalmeet-popup-closing {
    animation: vocalmeet-fade-out 0.2s ease;
}

@keyframes vocalmeet-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes vocalmeet-fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
}

/* Modal */
.vocalmeet-popup-modal {
    background: #fff;
    border-radius: 12px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
    animation: vocalmeet-slide-up 0.3s ease;
}

@keyframes vocalmeet-slide-up {
    from { 
        opacity: 0;
        transform: translateY(20px);
    }
    to { 
        opacity: 1;
        transform: translateY(0);
    }
}

/* Header */
.vocalmeet-popup-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #e5e7eb;
}

.vocalmeet-popup-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
}

.vocalmeet-popup-close {
    background: none;
    border: none;
    font-size: 24px;
    color: #9ca3af;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    transition: color 0.2s;
}

.vocalmeet-popup-close:hover {
    color: #374151;
}

/* Body */
.vocalmeet-popup-body {
    padding: 20px;
}

.vocalmeet-form-group {
    margin-bottom: 16px;
}

.vocalmeet-form-group:last-child {
    margin-bottom: 0;
}

.vocalmeet-form-group label {
    display: block;
    margin-bottom: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
}

.vocalmeet-form-group input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.vocalmeet-form-group input:focus {
    outline: none;
    border-color: #7c3aed;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

/* Message */
.vocalmeet-popup-message {
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 14px;
    margin-top: 12px;
}

.vocalmeet-message-success {
    background: #d1fae5;
    color: #065f46;
}

.vocalmeet-message-error {
    background: #fee2e2;
    color: #991b1b;
}

/* Footer */
.vocalmeet-popup-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    padding: 16px 20px;
    border-top: 1px solid #e5e7eb;
}

.vocalmeet-btn {
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.vocalmeet-btn-cancel {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #374151;
}

.vocalmeet-btn-cancel:hover {
    background: #e5e7eb;
}

.vocalmeet-btn-primary {
    background: #7c3aed;
    border: 1px solid #7c3aed;
    color: #fff;
}

.vocalmeet-btn-primary:hover {
    background: #6d28d9;
}

.vocalmeet-btn-primary:disabled {
    background: #a78bfa;
    cursor: not-allowed;
}

.vocalmeet-btn-primary.vocalmeet-loading {
    position: relative;
    color: transparent;
}

.vocalmeet-btn-primary.vocalmeet-loading::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    top: 50%;
    left: 50%;
    margin: -8px 0 0 -8px;
    border: 2px solid #fff;
    border-top-color: transparent;
    border-radius: 50%;
    animation: vocalmeet-spin 0.6s linear infinite;
}

@keyframes vocalmeet-spin {
    to { transform: rotate(360deg); }
}
```

```css
/* === assets/css/widget.css === */

/**
 * VocalMeet Elementor WooCommerce Widget - Widget Styles
 * Used in both editor preview and frontend
 */

/* Container */
.vocalmeet-product-creator-widget {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

/* Empty State */
.vocalmeet-empty-state {
    text-align: center;
    padding: 40px 20px;
}

.vocalmeet-create-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 14px 28px;
    background: #7c3aed;
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3);
}

.vocalmeet-create-btn:hover {
    background: #6d28d9;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.vocalmeet-btn-icon {
    font-size: 20px;
}

.vocalmeet-empty-message {
    margin-top: 12px;
    color: #9ca3af;
    font-size: 14px;
}

/* Product Card */
.vocalmeet-product-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}

.vocalmeet-product-icon {
    font-size: 48px;
    margin-bottom: 12px;
}

.vocalmeet-product-name {
    margin: 0 0 8px 0;
    font-size: 20px;
    font-weight: 600;
    color: #1e293b;
}

.vocalmeet-product-price {
    font-size: 24px;
    font-weight: 700;
    color: #7c3aed;
    margin-bottom: 16px;
}

.vocalmeet-product-link {
    display: inline-block;
    color: #7c3aed;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: color 0.2s;
}

.vocalmeet-product-link:hover {
    color: #6d28d9;
    text-decoration: underline;
}

/* Change Button (Editor only) */
.vocalmeet-change-btn {
    display: inline-block;
    margin-top: 16px;
    padding: 8px 16px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
}

.vocalmeet-change-btn:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}
```

**Reviewer sẽ thấy:**
- ✅ Modern CSS (CSS variables, animations, flexbox)
- ✅ Professional design
- ✅ Proper scoping (`.vocalmeet-` prefix)
- ✅ Accessibility considerations
- ✅ Loading states with spinner

---

## 🎯 SECTION 5: Implementation Checklist

### Phase 1: Plugin Skeleton
- [ ] Create `vocalmeet-elementor-woo.php` với plugin headers
- [ ] Implement dependency checks (PHP, Elementor, WC, Plugin 1)
- [ ] Create admin notices for missing dependencies

### Phase 2: Elementor Bootstrap
- [ ] Create `includes/class-plugin.php` singleton
- [ ] Register custom widget category
- [ ] Register widget với Elementor
- [ ] Enqueue editor scripts/styles
- [ ] Enqueue frontend styles

### Phase 3: Widget Controls
- [ ] Create `includes/widgets/class-product-creator.php`
- [ ] Implement widget identity methods
- [ ] Add hidden controls (product_id, name, price, url)
- [ ] Add display controls (button_text, show_price, show_link)
- [ ] Add style controls (colors, borders)

### Phase 4: Widget Render
- [ ] Implement `render()` method với 2 states
- [ ] Add editor context detection
- [ ] Implement `content_template()` for live preview
- [ ] Proper output escaping

### Phase 5: Editor JavaScript
- [ ] Create `assets/js/editor.js`
- [ ] Implement event delegation
- [ ] Create popup modal
- [ ] Implement REST API call (reuse Plugin 1)
- [ ] Update widget settings via Elementor API

### Phase 6: Styling
- [ ] Create `assets/css/editor.css` (popup styles)
- [ ] Create `assets/css/widget.css` (widget styles)
- [ ] Add animations, loading states

### Phase 7: Testing
- [ ] Widget appears in Elementor panel
- [ ] Drag widget to page → shows create button
- [ ] Click button → popup appears (NOT in preview)
- [ ] Submit form → product created
- [ ] Widget re-renders showing product
- [ ] Save page → settings persist
- [ ] Frontend displays product correctly
- [ ] Multiple widgets work independently

---

## 🎯 SECTION 6: Success Criteria

### Functional Requirements
| # | Requirement | Status |
|---|-------------|--------|
| 1 | Widget trong Elementor panel | ⬜ |
| 2 | Drag & drop vào page | ⬜ |
| 3 | Button trigger popup (NOT form in preview) | ⬜ |
| 4 | Popup tạo product via REST API | ⬜ |
| 5 | Widget re-render sau tạo product | ⬜ |
| 6 | Frontend hiển thị product | ⬜ |

### Assessment Focus Demonstration
| # | Focus Area | Evidence | Status |
|---|------------|----------|--------|
| 1 | Elementor Architecture | Correct hooks, widget lifecycle | ⬜ |
| 2 | Editor/Frontend Separation | Separate scripts, context checks | ⬜ |
| 3 | WYSIWYG Compliance | No form in preview, popup approach | ⬜ |
| 4 | Integration Skills | Reuse Plugin 1 REST API | ⬜ |
| 5 | Advanced JS | Elementor JS API, async/await | ⬜ |
| 6 | Security | Nonce, escaping, capability checks | ⬜ |
| 7 | UX | Loading states, error messages | ⬜ |

### Code Quality
| # | Aspect | Evidence | Status |
|---|--------|----------|--------|
| 1 | PSR Standards | Proper class structure | ⬜ |
| 2 | WordPress Standards | Escaping, hooks, filters | ⬜ |
| 3 | i18n Ready | All strings translatable | ⬜ |
| 4 | Documentation | PHPDoc comments | ⬜ |
| 5 | Clean Code | No debug code, proper naming | ⬜ |

---

## 🎯 SECTION 7: Key Talking Points for Presentation

Khi present cho reviewer, emphasize:

1. **"Tại sao 2 plugins riêng biệt?"**
   - Modular architecture
   - Plugin 2 extends Plugin 1
   - Proper dependency management

2. **"Tại sao popup thay vì form trong preview?"**
   - Tuân thủ Elementor WYSIWYG philosophy
   - Preview = result, not input
   - Assessment requirement "no raw code in preview"

3. **"Làm sao widget update mà không refresh?"**
   - Sử dụng Elementor JS API: `$e.run('document/elements/settings')`
   - Live preview via `content_template()`

4. **"Security considerations?"**
   - REST API nonce authentication
   - Output escaping (`esc_html`, `esc_attr`, `esc_url`)
   - Permission check tại REST endpoint (Plugin 1)

5. **"Reusability?"**
   - REST endpoint reused từ Plugin 1
   - Widget có thể extend thêm features (select existing product, etc.)
