# WordPress Developer Assessment

> Hello Reviewer! I'm Kai. Thank you for taking the time to review my work. This document serves as both an instruction guide and a space to share my thoughts on this code challenge. I'll walk you through each problem, present my perspective, and provide step-by-step guidance so you can review and run the applications smoothly.

---

## 📋 Table of Contents

- [My Approach](#-my-approach)
- [Quick Start](#-quick-start)
- [Problem I/II: WooCommerce REST API Plugin](#-problem-iii-woocommerce-rest-api-plugin)
- [Problem III: Custom Elementor Widget](#-problem-iii-custom-elementor-widget)
- [Security Considerations](#-security-considerations)
- [What I Would Do Differently in Production](#-what-i-would-do-differently-in-production)
- [Final Thoughts](#-final-thoughts)

---

## 💡 My Approach

As mentioned in the challenge, AI has become a powerful tool in software development. I don't deny using AI to assist with this code challenge, but I believe **the most important thing is truly knowing what you're doing** — understanding the "why" behind every decision, not just the "how."

This mindset shapes how I approached each problem:

### Philosophy

1. **Security First** — Never expose credentials to the browser. All WooCommerce API calls happen server-side with proper authentication.

2. **The WordPress Way** — Leverage native WordPress patterns: REST API (not `admin-ajax.php`), proper hooks, nonce verification, capability checks, and i18n-ready strings.

3. **Elementor Philosophy** — Respect the WYSIWYG principle. Preview area shows *results*, not input forms. Configuration happens in the panel or via popup triggered from panel.

4. **Clean Architecture** — Separation of concerns with dedicated classes for API handling, form rendering, and AJAX processing. Reusable components between plugins.

5. **Assessment Scope** — Focused on demonstrating understanding of WordPress/WooCommerce/Elementor ecosystems without over-engineering. Production hardening is documented but not all implemented.

### Development Environment

I built a complete Docker-based local development environment with:

- WordPress + WooCommerce + Elementor (pre-configured)
- HTTPS via self-signed SSL certificate for `vocalmeet.local` (required for WooCommerce REST API)
- Nginx reverse proxy with proper SSL termination
- phpMyAdmin for database management
- Justfile for streamlined CLI commands (`just setup`, `just start`, `just logs`, etc.)

<!-- TODO: Add screenshot of just commands -->

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- [Just](https://github.com/casey/just) command runner

### Setup & Run

```bash
# Clone and navigate to the project
cd devtools/vocalmeet/local

# First-time setup (generates SSL, starts containers, configures WordPress)
just setup

# Daily usage
just start
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| WordPress | <https://vocalmeet.local> | admin / admin |
| phpMyAdmin | <http://localhost:8081> | root / root |

> **Note:** Add `127.0.0.1 vocalmeet.local` to your `/etc/hosts` file. The SSL certificate is self-signed for this domain.

### Plugin Locations

```
wp-content/plugins/
├── vocalmeet-woo-api/         # Problem I/II
└── vocalmeet-elementor-woo/   # Problem III
```

---

## 🛒 Problem I/II: WooCommerce REST API Plugin

> **Goal:** Build a frontend page where users can create WooCommerce products using the REST API, without accessing the admin dashboard.

### Location

```
wp-content/plugins/vocalmeet-woo-api/
```

### The Approach

The challenge asks to "connect to WooCommerce REST API using standard authentication methods." This immediately raised a security concern: **WooCommerce API credentials (Consumer Key/Secret) should NEVER be exposed to the browser.**

My solution: Create a **server-side proxy** pattern where:

1. Frontend form submits to a custom WordPress REST endpoint
2. Server validates request (nonce, permissions, input sanitization)
3. Server makes authenticated call to WooCommerce API
4. Response is relayed back to the client

```
┌─────────────────┐         ┌───────────────────┐         ┌─────────────────┐
│  Browser/Form   │────────▶│  Custom REST API  │────────▶│ WooCommerce API │
│  (No secrets)   │  AJAX   │  (Server-side)    │  Auth   │  (Consumer Key) │
└─────────────────┘         └───────────────────┘         └─────────────────┘
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **REST API instead of admin-ajax.php** | Modern WordPress best practice (WP 4.7+). Built-in schema validation, proper HTTP status codes, better performance. |
| **Server-side WooCommerce calls** | Security requirement — Consumer Key/Secret never sent to browser. |
| **Basic Auth over HTTPS** | Standard WooCommerce authentication. Base64 encoding is only safe over encrypted connection. |
| **Logged-in user requirement** | Balance between security and demo simplicity. Production should check `current_user_can('publish_products')`. |

### The Solution

The plugin follows a clean separation of concerns:

- **API Handler Class** — Wraps WooCommerce REST API calls with proper authentication (Consumer Key/Secret via Basic Auth). Handles SSL verification for local development.

- **REST Endpoint** — Registers a custom endpoint (`POST /wp-json/vocalmeet-woo-api/v1/products`) with schema-based validation, nonce verification, and permission callbacks.

- **Shortcode** — `[vocalmeet_product_form]` renders a Bootstrap 5 form that can be added to any page. Assets are conditionally loaded only when the shortcode is present.

- **Form Handler** — Client-side validation, loading states, and success/error feedback. Uses `fetch()` with `X-WP-Nonce` header for CSRF protection.

### Notes

> **Why use WooCommerce REST API instead of direct CRUD?**
>
> In a real production environment, since we're already on the server-side, I would use WooCommerce's PHP functions directly (e.g., `wc_create_product()` or the `WC_Product` class) instead of making an HTTP request to the REST API. This approach:
>
> - **Eliminates network overhead** — No HTTP roundtrip to self
> - **Better performance** — Direct database operations
> - **Simpler authentication** — No need for Consumer Key/Secret
> - **Easier error handling** — Direct PHP exceptions
>
> However, for this assessment, I used the REST API approach because:
>
> 1. The requirement explicitly asks to "connect to WooCommerce REST API using standard authentication methods"
> 2. It demonstrates understanding of WooCommerce's API authentication (OAuth/Basic Auth)
> 3. Plugin 2 (Elementor widget) reuses this endpoint, showing modular architecture

### Outcome

<!-- TODO: Add screenshots showing:
1. Frontend form on a page
2. Success message after product creation
3. Product appearing in WooCommerce admin
-->

---

## 🧩 Problem III: Custom Elementor Widget

> **Goal:** Create a custom Elementor widget that allows users to create WooCommerce products within the Elementor editor.

> **Critical Requirement:** *"Try not to put any raw code directly into the preview page of Elementor."*

### Location

```
wp-content/plugins/vocalmeet-elementor-woo/
```

### The Approach

This was the most complex part. The requirement "no raw code in preview" initially seemed ambiguous, but understanding Elementor's philosophy clarified it:

**Elementor WYSIWYG Principle:**

- **Panel (Left):** Configuration, settings, controls
- **Preview (Right):** Visual output — what visitors will see

Putting a product creation form in the preview area violates this principle. The solution: **Trigger popup from panel button, render popup in editor document (not preview iframe).**

**Chosen UX Flow (Auto-Trigger):**

```
1. User drags widget to page → POPUP AUTO-OPENS! 🎉
2. User fills form (name, price) in popup → Submit
3. Product created via REST API (reusing Plugin 1's endpoint)
4. Widget settings updated → Preview shows product card
5. Page saved → Frontend displays product
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **2 separate plugins** | Separation of concerns. Plugin 2 depends on Plugin 1's REST API — demonstrates modular architecture. |
| **Backbone.js + Marionette** | Elementor is built on Backbone/Marionette. Using native patterns demonstrates deep understanding of Elementor internals. |
| **State Machine Pattern** | Explicit state transitions (idle → creating → success/error). Prevents invalid UI states. |
| **Auto-trigger popup on widget drop** | Best UX — user immediately enters product creation flow without extra clicks. |
| **Popup in editor document** | Completely avoids "raw code in preview" concern. Popup is a configuration action. |
| **Conditional panel button** | Backup trigger — only visible when no product exists. |
| **Fresh data on frontend** | `wc_get_product()` on render — handles product changes/deletions outside Elementor. |

### The Solution

**Widget Class** — Extends `\Elementor\Widget_Base` with:

- Custom widget category ("VocalMeet") for organization
- HIDDEN controls to store product data (populated by JavaScript after creation)
- BUTTON control in panel that triggers the popup
- Two render states: placeholder (no product) vs product card (with product)
- `content_template()` for live preview updates in editor

**JavaScript Architecture (Backbone/Marionette)** — Instead of vanilla JS, I used Elementor's native patterns:

- **State Model** (`Backbone.Model`) — Manages widget state with explicit transitions (`idle → creating → success/error`). Invalid transitions are rejected, preventing inconsistent UI states.

- **Popup View** (`Marionette.View`) — Handles form rendering with proper lifecycle hooks (`onRender`, `onDestroy`). Uses `modelEvents` to automatically update UI when model state changes.

- **Auto-Trigger Hook** — Listens to `panel/open_editor/widget` event. When a new widget (no `product_id`) is dropped, popup opens automatically for the best UX.

- **Elementor API Integration** — Uses `$e.run('document/elements/settings')` to update widget settings after product creation, triggering live preview refresh.

### Outcome

<!-- TODO: Add screenshots showing:
1. Widget in Elementor panel (VocalMeet category)
2. Popup auto-opening when widget dropped
3. Product card in preview after creation
4. Frontend display of the product
-->

---

## 🛡️ Security Considerations

| Concern | Implementation |
|---------|---------------|
| **Credential Protection** | WooCommerce Consumer Key/Secret stored server-side only, never sent to browser |
| **XSS Prevention** | `esc_html()`, `esc_attr()`, `esc_url()` for all output |
| **CSRF Protection** | WordPress REST nonce via `X-WP-Nonce` header |
| **Input Validation** | `sanitize_text_field()`, `wc_format_decimal()`, schema-based validation |
| **Permission Checks** | `permission_callback` with `is_user_logged_in()` |
| **HTTPS Requirement** | Basic Auth only safe over encrypted connection |

---

## 🔮 What I Would Do Differently in Production

| Aspect | Assessment Scope | Production Enhancement |
|--------|------------------|------------------------|
| **Permission Model** | `is_user_logged_in()` | `current_user_can('publish_products')` or custom capability |
| **Rate Limiting** | Not implemented | Prevent abuse with `wp_rate_limit` or custom throttling |
| **Error Taxonomy** | Basic error messages | Structured error codes, detailed logging |
| **Caching** | Fresh API calls | Transient caching for product display, Redis object cache |
| **Testing** | Manual testing | PHPUnit for PHP, Jest for JS, E2E with Cypress |
| **CI/CD** | Local Docker | GitHub Actions for linting, testing, deployment |
| **Infrastructure** | Docker Compose | Kubernetes (Helm charts), horizontal pod autoscaling, managed database |
| **Observability** | Error logs | APM (New Relic/Datadog), structured logging, alerting |
| **i18n** | Strings prepared with `__()` | Generate `.pot` file, add translations |

---

## 🙏 Final Thoughts

There's much more I'd love to discuss — from architectural patterns to infrastructure decisions, from testing strategies to monitoring approaches. However, to keep this document focused and respect your time, I've tried to highlight the most important aspects. Feel free to explore the source code for deeper implementation details.

---

### What Sets Me Apart

**I know exactly what I'm doing.** When issues arise, I understand the root cause and know where to improve and which layer to fix. Instead of just making things work, I focus on understanding the fundamentals.

To achieve this, I've continuously invested in learning — not just at the application layer, but at deeper levels:

| Area | Depth |
|------|-------|
| **Languages** | Deep understanding of JavaScript, Java, Python, C#, PHP and their underlying principles |
| **Frameworks** | Knowing the strengths of different frameworks and applying them appropriately |
| **Infrastructure** | Certified in AWS, Kubernetes (CKAD), Terraform, Harness — giving me a comprehensive view across the full stack |

This breadth of knowledge enables me to have a **holistic perspective** when developing solutions — from writing clean application code to understanding how it runs in production infrastructure.

---

Thank you for taking the time to review my work. I look forward to any feedback or questions you might have!

— Kai
