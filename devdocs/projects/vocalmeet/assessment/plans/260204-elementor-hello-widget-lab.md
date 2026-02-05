# 📋 260204 - Elementor Hello Widget Lab

## References

- Learning path: `devdocs/projects/vocalmeet/common/index.md`
- Widget fundamentals: `devdocs/projects/vocalmeet/common/elementor/02-widget-fundamentals.md`
- Existing Elementor plugin reference: `projects/vocalmeet/assessment/wordpress/wp-content/plugins/vocalmeet-elementor-woo/`

## User Requirements

> Tạo lab plugin để thực hành widget fundamentals:
> 1. Tạo widget "Hello" render static text.
> 2. Thêm 1 control (text) và render text đó trong preview.
> Khi làm được 2 bước này, bạn đã nắm 80% cơ chế widget.

## 🎯 Objective

Tạo plugin lab đơn giản nhất có thể để nắm vững cơ chế Elementor widget:
- Hiểu widget lifecycle (identity → controls → render)
- Hiểu cách data flow từ control → settings → render

### ⚠️ Key Considerations

1. **Minimal dependencies**: Plugin chỉ cần Elementor, không cần WooCommerce
2. **Focus on fundamentals**: Không thêm complexity (CSS, JS, AJAX) - chỉ PHP thuần
3. **Progressive learning**: Step 1 (static) phải chạy trước khi làm Step 2 (dynamic)

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Hiểu Elementor widget registration flow
  - **Outcome**: Hook `elementor/widgets/register` để đăng ký widget
- [ ] Xác định minimum viable widget structure
  - **Outcome**: 1 file plugin + 1 widget class

### Phase 2: Implementation Structure

```
projects/vocalmeet/assessment/wordpress/wp-content/plugins/
└── vocalmeet-hello-widget/                    # 🚧 TODO - Lab plugin
    ├── vocalmeet-hello-widget.php             # 🚧 TODO - Plugin bootstrap
    └── widgets/
        └── class-hello-widget.php             # 🚧 TODO - Widget class
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Tạo widget render static text

**File: `vocalmeet-hello-widget.php`** (Plugin bootstrap)
```php
<?php
/*
Plugin Name: VocalMeet Hello Widget Lab
Description: Lab plugin to learn Elementor widget fundamentals.
Version: 1.0.0
Requires Plugins: elementor
*/

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// Wait for Elementor to load
add_action( 'plugins_loaded', function() {
    if ( ! did_action( 'elementor/loaded' ) ) {
        return;
    }
    
    // Register widget
    add_action( 'elementor/widgets/register', function( $widgets_manager ) {
        require_once __DIR__ . '/widgets/class-hello-widget.php';
        $widgets_manager->register( new \Vocalmeet_Hello_Widget() );
    });
});
```

**File: `widgets/class-hello-widget.php`** (Widget class - Step 1)
```php
<?php
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Vocalmeet_Hello_Widget extends \Elementor\Widget_Base {

    // Identity methods
    public function get_name(): string {
        return 'vocalmeet_hello';
    }

    public function get_title(): string {
        return 'Hello Widget';
    }

    public function get_icon(): string {
        return 'eicon-code';
    }

    public function get_categories(): array {
        return [ 'general' ];
    }

    // No controls yet (Step 1)
    protected function register_controls(): void {
        // Empty for Step 1
    }

    // Render static text
    protected function render(): void {
        echo '<div class="vocalmeet-hello">Hello from Elementor Widget!</div>';
    }
}
```

**Verification Step 1:**
- [ ] Activate plugin trong WordPress admin
- [ ] Mở Elementor editor trên bất kỳ page nào
- [ ] Search "Hello Widget" trong widget panel
- [ ] Kéo widget vào canvas
- [ ] Xác nhận thấy text "Hello from Elementor Widget!" trong preview

---

#### Step 2: Thêm text control và render dynamic text

**Update: `widgets/class-hello-widget.php`** (Add controls)
```php
<?php
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class Vocalmeet_Hello_Widget extends \Elementor\Widget_Base {

    public function get_name(): string {
        return 'vocalmeet_hello';
    }

    public function get_title(): string {
        return 'Hello Widget';
    }

    public function get_icon(): string {
        return 'eicon-code';
    }

    public function get_categories(): array {
        return [ 'general' ];
    }

    // ADD: Register text control
    protected function register_controls(): void {
        $this->start_controls_section(
            'content_section',
            [
                'label' => 'Content',
                'tab'   => \Elementor\Controls_Manager::TAB_CONTENT,
            ]
        );

        $this->add_control(
            'hello_text',
            [
                'label'       => 'Text',
                'type'        => \Elementor\Controls_Manager::TEXT,
                'default'     => 'Hello from Elementor Widget!',
                'placeholder' => 'Enter your text here',
            ]
        );

        $this->end_controls_section();
    }

    // UPDATE: Render dynamic text from settings
    protected function render(): void {
        $settings = $this->get_settings_for_display();
        $text = $settings['hello_text'];
        
        echo '<div class="vocalmeet-hello">' . esc_html( $text ) . '</div>';
    }
}
```

**Verification Step 2:**
- [ ] Refresh Elementor editor
- [ ] Click vào Hello Widget đã có trên canvas
- [ ] Thấy panel "Content" với input "Text" bên trái
- [ ] Thay đổi text → xác nhận preview cập nhật real-time

## 📊 Summary of Results

> Do not summarize the results until the implementation is done and I request it

### ✅ Completed Achievements

- [ ] Step 1: Widget renders static text
- [ ] Step 2: Widget renders dynamic text from control

## 🚧 Outstanding Issues & Follow-up

### Next Steps (sau khi hoàn thành lab này)

- [ ] Thử thêm các control types khác: TEXTAREA, SELECT, SWITCHER
- [ ] Thử multiple sections (Content, Style, Advanced)
- [ ] Đọc tiếp về Editor Scripts nếu cần interactivity (AJAX, modal)
