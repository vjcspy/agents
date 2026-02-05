# 📋 260205 - Marionette.js in Elementor Editor Lab

## References

- Previous lab: `devdocs/projects/vocalmeet/assessment/plans/260204-elementor-hello-widget-lab.md`
- Target plan: `devdocs/projects/vocalmeet/assessment/plans/260202-elementor-woocommerce-widget-plan.md`
- Elementor source: `projects/vocalmeet/assessment/wordpress/wp-content/plugins/elementor/assets/dev/js/`
- [Backbone.js Docs](https://backbonejs.org/)
- [Marionette.js Docs](https://marionettejs.com/)

## User Requirements

> Học Marionette.js/Backbone.js trong Elementor context trước khi implement full widget.
> Mục tiêu: Sử dụng event-driven architecture, state machine đúng chuẩn Elementor production.

## 🎯 Objective

Hiểu và thực hành:
1. **Backbone.Events** - Event system (`elementor.channels`)
2. **Backbone.Model** - State management
3. **Marionette.View** - View lifecycle trong Elementor
4. **$e.run commands** - Elementor's command API

### ⚠️ Key Considerations

1. **Prerequisite**: Hoàn thành Hello Widget Lab (260204) trước
2. **Progressive complexity**: Event → Model → View → Full integration
3. **Real Elementor patterns**: Study từ Elementor source code

---

## 📚 SECTION 1: Theory - Elementor's JS Architecture

### 1.1 Stack Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ELEMENTOR EDITOR JS STACK                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 4: Elementor API                                         │
│  ├── $e.run() - Command system                                  │
│  ├── $e.routes - Navigation                                     │
│  ├── elementor.channels - Event bus                             │
│  └── elementorModules - Base classes                            │
│                                                                 │
│  Layer 3: Marionette.js (Application framework)                 │
│  ├── Marionette.View - Component views                          │
│  ├── Marionette.Behavior - Reusable behaviors                   │
│  └── Marionette.Region - DOM region management                  │
│                                                                 │
│  Layer 2: Backbone.js (MVC foundation)                          │
│  ├── Backbone.Model - Data + state                              │
│  ├── Backbone.View - UI rendering                               │
│  ├── Backbone.Events - Event mixin                              │
│  └── Backbone.Collection - Model groups                         │
│                                                                 │
│  Layer 1: Underscore.js + jQuery                                │
│  ├── _.template() - JS templating                               │
│  └── jQuery - DOM manipulation                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Concept: Event Channels

Elementor sử dụng **Backbone.Events** để tạo event bus:

```javascript
// Elementor's channel system
elementor.channels = {
    editor: _.extend({}, Backbone.Events),   // Editor events
    data: _.extend({}, Backbone.Events),     // Data events
    // ...
};

// Usage pattern
elementor.channels.editor.on('event:name', callback);
elementor.channels.editor.trigger('event:name', data);
```

### 1.3 Key Concept: Widget Model

Mỗi widget instance có một Backbone Model chứa settings:

```javascript
// Truy cập widget model trong editor
var widgetModel = elementor.getContainer(widgetId).model;
var settings = widgetModel.get('settings');

// Listen to settings changes
widgetModel.on('change:settings', function(model) {
    console.log('Settings changed:', model.changed);
});
```

### 1.4 Key Concept: $e.run Commands

Elementor 2.7+ dùng command pattern:

```javascript
// Update widget settings
$e.run('document/elements/settings', {
    container: elementor.getContainer(widgetId),
    settings: { product_id: '123' }
});

// Get all available commands
console.log($e.commands.getAll());
```

---

## 🔄 SECTION 2: Lab Implementation

### Lab Structure

```
projects/vocalmeet/assessment/wordpress/wp-content/plugins/
└── vocalmeet-marionette-lab/                # 🚧 TODO
    ├── vocalmeet-marionette-lab.php         # Plugin bootstrap
    ├── widgets/
    │   └── class-state-widget.php           # Widget with state machine
    └── assets/
        └── js/
            └── editor.js                    # Marionette/Backbone code
```

---

### Phase 1: BUTTON Control + Event Channel

**Goal:** Hiểu event flow từ panel button → JS handler

#### Step 1.1: Widget với BUTTON control

**File: `vocalmeet-marionette-lab.php`**
```php
<?php
/*
Plugin Name: VocalMeet Marionette Lab
Description: Lab to learn Backbone/Marionette in Elementor context
Version: 1.0.0
Requires Plugins: elementor
*/

if (!defined('ABSPATH')) exit;

define('VOCALMEET_MARIONETTE_LAB_URL', plugin_dir_url(__FILE__));

add_action('plugins_loaded', function() {
    if (!did_action('elementor/loaded')) return;
    
    // Register widget
    add_action('elementor/widgets/register', function($widgets_manager) {
        require_once __DIR__ . '/widgets/class-state-widget.php';
        $widgets_manager->register(new Vocalmeet_State_Widget());
    });
    
    // Enqueue editor script
    add_action('elementor/editor/after_enqueue_scripts', function() {
        wp_enqueue_script(
            'vocalmeet-marionette-lab',
            VOCALMEET_MARIONETTE_LAB_URL . 'assets/js/editor.js',
            ['elementor-editor'],
            '1.0.0',
            true
        );
    });
});
```

**File: `widgets/class-state-widget.php`**
```php
<?php
if (!defined('ABSPATH')) exit;

class Vocalmeet_State_Widget extends \Elementor\Widget_Base {

    public function get_name(): string {
        return 'vocalmeet_state';
    }

    public function get_title(): string {
        return 'State Machine Widget';
    }

    public function get_icon(): string {
        return 'eicon-code';
    }

    public function get_categories(): array {
        return ['general'];
    }

    protected function register_controls(): void {
        $this->start_controls_section('content_section', [
            'label' => 'Content',
            'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
        ]);

        // Hidden control to store state
        $this->add_control('current_state', [
            'type' => \Elementor\Controls_Manager::HIDDEN,
            'default' => 'idle',
        ]);

        // Info display
        $this->add_control('state_info', [
            'type' => \Elementor\Controls_Manager::RAW_HTML,
            'raw' => '<div id="vocalmeet-state-display">Current State: <strong>idle</strong></div>',
            'content_classes' => 'elementor-panel-alert elementor-panel-alert-info',
        ]);

        // BUTTON control with event
        $this->add_control('action_button', [
            'type' => \Elementor\Controls_Manager::BUTTON,
            'text' => 'Trigger Action',
            'event' => 'vocalmeet:state:action',  // Custom event name
            'button_type' => 'success',
        ]);

        $this->end_controls_section();
    }

    protected function render(): void {
        $settings = $this->get_settings_for_display();
        $state = $settings['current_state'] ?? 'idle';
        ?>
        <div class="vocalmeet-state-widget" data-widget-id="<?php echo esc_attr($this->get_id()); ?>">
            <p>Widget State: <strong><?php echo esc_html($state); ?></strong></p>
        </div>
        <?php
    }
}
```

**File: `assets/js/editor.js`** (Phase 1)
```javascript
/**
 * Phase 1: Basic event channel usage
 * 
 * Learn: elementor.channels.editor.on() pattern
 */
(function() {
    'use strict';

    // Wait for editor to be ready
    window.addEventListener('load', function() {
        if (typeof elementor === 'undefined') return;
        
        elementor.on('preview:loaded', initLab);
    });

    function initLab() {
        console.log('[Marionette Lab] Editor initialized');
        
        // ══════════════════════════════════════════════════════════════
        // LESSON 1: Listen to BUTTON control event
        // ══════════════════════════════════════════════════════════════
        
        // When user clicks "Trigger Action" button in panel,
        // Elementor fires this event via Backbone.Events
        elementor.channels.editor.on('vocalmeet:state:action', function(view) {
            console.log('[Marionette Lab] Button clicked!');
            console.log('[Marionette Lab] Widget ID:', view.model.id);
            console.log('[Marionette Lab] Widget Model:', view.model);
            
            // Alert to confirm it works
            alert('Button event received! Widget ID: ' + view.model.id);
        });
    }
})();
```

**Verification Phase 1:**
- [ ] Activate plugin
- [ ] Drag "State Machine Widget" vào page
- [ ] Click "Trigger Action" button trong panel
- [ ] Thấy alert với Widget ID
- [ ] Check console log để thấy view.model

---

### Phase 2: Backbone.Model for State Management

**Goal:** Sử dụng Backbone.Model pattern để manage widget state

**Update: `assets/js/editor.js`** (Phase 2)
```javascript
/**
 * Phase 2: State management with Backbone.Model
 * 
 * Learn: 
 * - Create custom Backbone.Model
 * - State machine pattern
 * - Model events (change)
 */
(function() {
    'use strict';

    // ══════════════════════════════════════════════════════════════
    // LESSON 2: Define State Machine Model
    // ══════════════════════════════════════════════════════════════
    
    /**
     * Widget State Model
     * 
     * States: idle → processing → success/error → idle
     * 
     * This is a Backbone.Model with explicit state transitions.
     */
    var WidgetStateModel = Backbone.Model.extend({
        
        defaults: {
            state: 'idle',        // Current state
            widgetId: null,       // Associated widget
            message: '',          // Status message
            data: null            // Any payload data
        },
        
        // Valid states
        STATES: {
            IDLE: 'idle',
            PROCESSING: 'processing',
            SUCCESS: 'success',
            ERROR: 'error'
        },
        
        // Valid transitions
        transitions: {
            'idle': ['processing'],
            'processing': ['success', 'error'],
            'success': ['idle', 'processing'],
            'error': ['idle', 'processing']
        },
        
        /**
         * Transition to new state with validation
         */
        transitionTo: function(newState, data) {
            var currentState = this.get('state');
            var validTransitions = this.transitions[currentState] || [];
            
            if (validTransitions.indexOf(newState) === -1) {
                console.error('[StateModel] Invalid transition:', currentState, '→', newState);
                return false;
            }
            
            console.log('[StateModel] Transition:', currentState, '→', newState);
            
            this.set({
                state: newState,
                data: data || null,
                message: this.getStateMessage(newState)
            });
            
            return true;
        },
        
        getStateMessage: function(state) {
            var messages = {
                'idle': 'Ready',
                'processing': 'Processing...',
                'success': 'Completed successfully!',
                'error': 'An error occurred'
            };
            return messages[state] || '';
        },
        
        // Convenience methods
        startProcessing: function() {
            return this.transitionTo(this.STATES.PROCESSING);
        },
        
        complete: function(data) {
            return this.transitionTo(this.STATES.SUCCESS, data);
        },
        
        fail: function(error) {
            return this.transitionTo(this.STATES.ERROR, error);
        },
        
        reset: function() {
            return this.transitionTo(this.STATES.IDLE);
        }
    });

    // Store models per widget (keyed by widget ID)
    var widgetModels = {};
    
    function getOrCreateModel(widgetId) {
        if (!widgetModels[widgetId]) {
            widgetModels[widgetId] = new WidgetStateModel({ widgetId: widgetId });
            
            // Listen to state changes
            widgetModels[widgetId].on('change:state', function(model) {
                console.log('[StateModel] State changed for widget', widgetId, ':', model.get('state'));
                updateWidgetPreview(widgetId, model);
            });
        }
        return widgetModels[widgetId];
    }
    
    function updateWidgetPreview(widgetId, model) {
        // Update widget settings via Elementor API
        var container = elementor.getContainer(widgetId);
        if (container) {
            $e.run('document/elements/settings', {
                container: container,
                settings: {
                    current_state: model.get('state')
                }
            });
        }
    }

    // ══════════════════════════════════════════════════════════════
    // INIT
    // ══════════════════════════════════════════════════════════════
    
    window.addEventListener('load', function() {
        if (typeof elementor === 'undefined') return;
        elementor.on('preview:loaded', initLab);
    });

    function initLab() {
        console.log('[Marionette Lab] Phase 2: State Model initialized');
        
        elementor.channels.editor.on('vocalmeet:state:action', function(view) {
            var widgetId = view.model.id;
            var stateModel = getOrCreateModel(widgetId);
            
            console.log('[Lab] Current state:', stateModel.get('state'));
            
            // Simulate state transitions
            var currentState = stateModel.get('state');
            
            if (currentState === 'idle') {
                stateModel.startProcessing();
                
                // Simulate async operation
                setTimeout(function() {
                    // 80% success, 20% error
                    if (Math.random() > 0.2) {
                        stateModel.complete({ product_id: '123' });
                    } else {
                        stateModel.fail({ message: 'Simulated error' });
                    }
                    
                    // Auto reset after 2 seconds
                    setTimeout(function() {
                        stateModel.reset();
                    }, 2000);
                    
                }, 1500);
            }
        });
    }
})();
```

**Verification Phase 2:**
- [ ] Reload Elementor editor
- [ ] Drag widget, click "Trigger Action"
- [ ] Observe state transitions in console: idle → processing → success/error → idle
- [ ] Widget preview updates with each state change

---

### Phase 3: Marionette.View for Popup

**Goal:** Sử dụng Marionette.View để tạo popup với proper lifecycle

**Update: `assets/js/editor.js`** (Phase 3 - Add popup view)
```javascript
/**
 * Phase 3: Marionette.View for Popup
 * 
 * Learn:
 * - Extend Marionette.View
 * - Template rendering
 * - UI hash for element references
 * - Events hash for DOM events
 * - Lifecycle methods (onRender, onDestroy)
 */
(function() {
    'use strict';
    
    // ══════════════════════════════════════════════════════════════
    // LESSON 3: Marionette View for Popup
    // ══════════════════════════════════════════════════════════════
    
    /**
     * Product Creation Popup View
     * 
     * Extends Marionette.View with:
     * - template: Underscore template
     * - ui: DOM element references
     * - events: DOM event handlers
     * - model: Bound to WidgetStateModel
     */
    var PopupView = Marionette.View.extend({
        
        className: 'vocalmeet-popup-overlay',
        
        // Underscore.js template
        template: _.template(`
            <div class="vocalmeet-popup-modal">
                <div class="vocalmeet-popup-header">
                    <h3>Create Product</h3>
                    <button class="vocalmeet-popup-close" data-ui="close">&times;</button>
                </div>
                <div class="vocalmeet-popup-body">
                    <div class="vocalmeet-form-group">
                        <label>Product Name</label>
                        <input type="text" data-ui="name" placeholder="Enter name">
                    </div>
                    <div class="vocalmeet-form-group">
                        <label>Price</label>
                        <input type="number" data-ui="price" step="0.01" min="0" placeholder="0.00">
                    </div>
                    <div class="vocalmeet-popup-message" data-ui="message" style="display:none;"></div>
                </div>
                <div class="vocalmeet-popup-footer">
                    <button class="vocalmeet-btn vocalmeet-btn-cancel" data-ui="cancel">Cancel</button>
                    <button class="vocalmeet-btn vocalmeet-btn-primary" data-ui="submit">Create</button>
                </div>
            </div>
        `),
        
        // UI element references (accessed via this.ui.name, this.ui.price, etc.)
        ui: {
            close: '[data-ui="close"]',
            name: '[data-ui="name"]',
            price: '[data-ui="price"]',
            message: '[data-ui="message"]',
            cancel: '[data-ui="cancel"]',
            submit: '[data-ui="submit"]'
        },
        
        // DOM event bindings
        events: {
            'click @ui.close': 'onClose',
            'click @ui.cancel': 'onClose',
            'click @ui.submit': 'onSubmit',
            'keypress @ui.name': 'onKeypress',
            'keypress @ui.price': 'onKeypress'
        },
        
        // Model events (listen to state changes)
        modelEvents: {
            'change:state': 'onStateChange'
        },
        
        // ─────────────────────────────────────────────────────────
        // Lifecycle Methods
        // ─────────────────────────────────────────────────────────
        
        onRender: function() {
            console.log('[PopupView] Rendered');
            // Focus first input after render
            var self = this;
            setTimeout(function() {
                self.ui.name.focus();
            }, 100);
        },
        
        onDestroy: function() {
            console.log('[PopupView] Destroyed - cleanup complete');
        },
        
        // ─────────────────────────────────────────────────────────
        // Event Handlers
        // ─────────────────────────────────────────────────────────
        
        onClose: function(e) {
            e.preventDefault();
            this.destroy();
        },
        
        onKeypress: function(e) {
            if (e.keyCode === 13) { // Enter key
                this.onSubmit(e);
            }
        },
        
        onSubmit: function(e) {
            e.preventDefault();
            
            var name = this.ui.name.val().trim();
            var price = parseFloat(this.ui.price.val());
            
            // Validation
            if (!name) {
                this.showMessage('Product name is required', 'error');
                return;
            }
            if (!price || price <= 0) {
                this.showMessage('Price must be greater than 0', 'error');
                return;
            }
            
            // Trigger state transition
            this.model.startProcessing();
            
            // Simulate API call
            var self = this;
            setTimeout(function() {
                // Simulate success
                self.model.complete({
                    product_id: Math.floor(Math.random() * 1000),
                    product_name: name,
                    product_price: price
                });
                
                // Close after success
                setTimeout(function() {
                    self.destroy();
                }, 1000);
            }, 1500);
        },
        
        onStateChange: function(model, state) {
            console.log('[PopupView] State changed to:', state);
            
            switch(state) {
                case 'processing':
                    this.ui.submit.prop('disabled', true).text('Creating...');
                    break;
                case 'success':
                    this.showMessage('Product created! ID: ' + model.get('data').product_id, 'success');
                    break;
                case 'error':
                    this.showMessage('Error: ' + (model.get('data')?.message || 'Unknown'), 'error');
                    this.ui.submit.prop('disabled', false).text('Create');
                    break;
            }
        },
        
        // ─────────────────────────────────────────────────────────
        // Helper Methods
        // ─────────────────────────────────────────────────────────
        
        showMessage: function(text, type) {
            this.ui.message
                .text(text)
                .removeClass('success error')
                .addClass(type)
                .show();
        }
    });
    
    // ══════════════════════════════════════════════════════════════
    // State Model (from Phase 2)
    // ══════════════════════════════════════════════════════════════
    
    var WidgetStateModel = Backbone.Model.extend({
        defaults: {
            state: 'idle',
            widgetId: null,
            message: '',
            data: null
        },
        
        STATES: { IDLE: 'idle', PROCESSING: 'processing', SUCCESS: 'success', ERROR: 'error' },
        
        transitions: {
            'idle': ['processing'],
            'processing': ['success', 'error'],
            'success': ['idle', 'processing'],
            'error': ['idle', 'processing']
        },
        
        transitionTo: function(newState, data) {
            var currentState = this.get('state');
            var validTransitions = this.transitions[currentState] || [];
            
            if (validTransitions.indexOf(newState) === -1) {
                console.error('[StateModel] Invalid transition:', currentState, '→', newState);
                return false;
            }
            
            this.set({ state: newState, data: data || null });
            return true;
        },
        
        startProcessing: function() { return this.transitionTo(this.STATES.PROCESSING); },
        complete: function(data) { return this.transitionTo(this.STATES.SUCCESS, data); },
        fail: function(error) { return this.transitionTo(this.STATES.ERROR, error); },
        reset: function() { return this.transitionTo(this.STATES.IDLE); }
    });

    var widgetModels = {};
    var currentPopup = null;
    
    function getOrCreateModel(widgetId) {
        if (!widgetModels[widgetId]) {
            widgetModels[widgetId] = new WidgetStateModel({ widgetId: widgetId });
        }
        return widgetModels[widgetId];
    }

    // ══════════════════════════════════════════════════════════════
    // INIT
    // ══════════════════════════════════════════════════════════════
    
    window.addEventListener('load', function() {
        if (typeof elementor === 'undefined') return;
        elementor.on('preview:loaded', initLab);
        
        // Add popup styles
        addPopupStyles();
    });
    
    function addPopupStyles() {
        var css = `
            .vocalmeet-popup-overlay {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 999999;
            }
            .vocalmeet-popup-modal {
                background: #fff;
                border-radius: 8px;
                width: 400px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .vocalmeet-popup-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid #e5e7eb;
            }
            .vocalmeet-popup-header h3 { margin: 0; font-size: 18px; }
            .vocalmeet-popup-close {
                background: none; border: none;
                font-size: 24px; cursor: pointer; color: #999;
            }
            .vocalmeet-popup-body { padding: 20px; }
            .vocalmeet-form-group { margin-bottom: 16px; }
            .vocalmeet-form-group label {
                display: block; margin-bottom: 6px;
                font-size: 14px; font-weight: 500;
            }
            .vocalmeet-form-group input {
                width: 100%; padding: 10px 12px;
                border: 1px solid #d1d5db; border-radius: 6px;
                font-size: 14px;
            }
            .vocalmeet-popup-message {
                padding: 10px; border-radius: 6px;
                font-size: 14px; margin-top: 12px;
            }
            .vocalmeet-popup-message.success { background: #d1fae5; color: #065f46; }
            .vocalmeet-popup-message.error { background: #fee2e2; color: #991b1b; }
            .vocalmeet-popup-footer {
                display: flex; gap: 12px;
                justify-content: flex-end;
                padding: 16px 20px;
                border-top: 1px solid #e5e7eb;
            }
            .vocalmeet-btn {
                padding: 10px 20px; border-radius: 6px;
                font-size: 14px; font-weight: 500; cursor: pointer;
            }
            .vocalmeet-btn-cancel {
                background: #f3f4f6; border: 1px solid #d1d5db; color: #374151;
            }
            .vocalmeet-btn-primary {
                background: #7c3aed; border: none; color: #fff;
            }
            .vocalmeet-btn-primary:disabled {
                background: #a78bfa; cursor: not-allowed;
            }
        `;
        
        var style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    function initLab() {
        console.log('[Marionette Lab] Phase 3: Popup View initialized');
        
        elementor.channels.editor.on('vocalmeet:state:action', function(view) {
            var widgetId = view.model.id;
            var stateModel = getOrCreateModel(widgetId);
            
            // Close existing popup if any
            if (currentPopup) {
                currentPopup.destroy();
            }
            
            // Create and show popup
            currentPopup = new PopupView({
                model: stateModel
            });
            
            // Render and append to body
            currentPopup.render();
            document.body.appendChild(currentPopup.el);
        });
    }
})();
```

**Verification Phase 3:**
- [ ] Reload editor
- [ ] Click "Trigger Action" → popup appears
- [ ] Fill form → click Create → see state transitions
- [ ] Observe console logs for lifecycle events
- [ ] ESC or Cancel closes popup cleanly

---

## 📊 SECTION 3: Summary & Takeaways

### Key Patterns Learned

| Pattern | Elementor Usage | Your Implementation |
|---------|-----------------|---------------------|
| **Event Channel** | `elementor.channels.editor` | Listen to BUTTON control events |
| **Backbone.Model** | Widget settings model | Custom state machine model |
| **Marionette.View** | Panel controls, dialogs | Popup with lifecycle |
| **$e.run Commands** | All editor operations | Update widget settings |

### State Machine Pattern

```
            ┌──────────┐
            │   IDLE   │◀─────────────────────┐
            └────┬─────┘                      │
                 │ startProcessing()          │
                 ▼                            │
          ┌──────────────┐                    │
          │  PROCESSING  │                    │ reset()
          └──────┬───────┘                    │
                 │                            │
        ┌────────┴────────┐                   │
        ▼                 ▼                   │
  ┌───────────┐    ┌───────────┐              │
  │  SUCCESS  │    │   ERROR   │──────────────┘
  └─────┬─────┘    └───────────┘
        │
        └─────────────────────────────────────┘
```

### Best Practices from Lab

1. **Always use state machine** - Explicit states prevent invalid UI states
2. **Model-View separation** - View renders from model, model handles logic
3. **Event-driven communication** - Use events, not direct method calls
4. **Lifecycle management** - Use `onDestroy` for cleanup

---

## ✅ Completion Checklist

- [ ] **Phase 1**: BUTTON event channel works
- [ ] **Phase 2**: State model transitions correctly
- [ ] **Phase 3**: Marionette popup renders with lifecycle

### Next Step

After completing this lab, proceed to revise the main plan:
`devdocs/projects/vocalmeet/assessment/plans/260202-elementor-woocommerce-widget-plan.md`

The revised plan will use these patterns for the actual Product Creator widget.
