# Presentation

## Plugin 1: vocalmeet-woo-api (Task 4.I-II) ✅

### Key Points đã làm

| Aspect | Implementation | Điểm nhấn khi present |
|--------|---------------|----------------------|
| **REST API** | Custom endpoint `vocalmeet-woo-api/v1/products` | Modern WordPress way (từ WP 4.7+), không dùng `admin-ajax.php` |
| **Security** | Server-side gọi WooCommerce API | Consumer key/secret không expose ra browser |
| **Validation** | Schema-based (`args` trong `register_rest_route`) | Built-in validation, không cần manual check |
| **Permission** | `permission_callback` với `is_user_logged_in()` | Giải thích có thể enforce `publish_products` cho production |

### Cần nhắc đến HTTPS

Basic Auth chỉ base64 encode, **không mã hoá**.
Nó chỉ an toàn khi đường truyền được mã hoá bởi HTTPS.
→ "HTTPS requirement" không phải hình thức, mà là **điều kiện bảo vệ secret**.

### REST Refactor Notes (để "đẹp điểm")

- **Error taxonomy**: propagate `status` từ `WP_Error` (không wrap 500 cố định)
- **Fetch**: set `credentials: 'same-origin'` để cookies luôn gửi kèm → tránh nonce fail
- **Authorization**: demo require login; production nên enforce capability (`manage_woocommerce` / `publish_products`)
- **Server-side calls**: đúng yêu cầu bài thi, không expose consumer secret

---

## Plugin 2: vocalmeet-elementor-woo (Task 4.III) ⏳

> **Đây là phần khó nhất** - cần demonstrate Elementor expertise

### Key Requirements

| Requirement | Ý nghĩa |
|-------------|---------|
| Custom drag-and-drop widget | Hiểu Elementor widget lifecycle |
| **NO raw code in preview** | Form phải ở popup/panel, không trong preview area |
| Tạo product từ widget | Kết hợp WooCommerce API + Elementor JS |

### Architecture Points cần nhấn mạnh

```
Panel (left)     Preview (right)     Frontend
────────────     ───────────────     ────────
Controls         Visual output       Live site
Data input       WYSIWYG             Product display
Popup form       Show product        
```

### Elementor Widget Lifecycle (quan trọng!)

1. `register_controls()` - Định nghĩa settings trong panel
2. `render()` - Output HTML (editor context vs frontend context khác nhau)
3. `get_script_depends()` - Load JS chỉ khi cần

### JS Architecture

- **Editor context**: Hook vào Elementor events, handle popup, AJAX call
- **Frontend context**: Chỉ display, không có create functionality
- **State management**: Sau khi tạo product → save `product_id` vào widget settings

### Security Points (Plugin 2)

- Editor context: Chỉ users có quyền edit page mới thấy widget
- API calls vẫn phải verify permissions + nonce
- Sanitize all output (`esc_html`, `esc_attr`)

---

## General Points để Impress

### 🛡️ Security Awareness

| Concern | Implementation |
|---------|---------------|
| XSS | `esc_html()`, `esc_attr()` cho output |
| CSRF | `wp_nonce_field()`, REST nonce via `X-WP-Nonce` header |
| Input validation | `sanitize_text_field()`, `wc_format_decimal()` |
| Capability | `current_user_can()` / `permission_callback` |

### 📦 Code Quality

- OOP structure với proper namespacing
- PHPDoc comments
- Separation of concerns (API handler / Form / Controller)
- i18n ready: `__()`, `_e()` cho strings

### ⚡ Performance

- Conditional asset loading (chỉ load khi shortcode/widget được dùng)
- Scripts chỉ enqueue trong đúng context (editor vs frontend)

---

## Questions họ có thể hỏi

1. **"Tại sao không gọi WooCommerce API trực tiếp từ JS?"**
   → Bảo mật: không expose consumer key/secret ra browser

2. **"Tại sao dùng REST API thay vì admin-ajax.php?"**
   → Modern best practice, schema validation, proper HTTP status codes

3. **"Làm sao handle error khi WooCommerce API fail?"**
   → Propagate error với đúng status code, show user-friendly message

4. **"Elementor widget: tại sao dùng popup thay vì form trong preview?"**
   → Requirement của bài: "no raw code in preview", đúng Elementor philosophy (preview = WYSIWYG)

---

## Docker/Local Dev Notes (đã fix hôm nay)

### Issue: 401 "not allowed to create resources"

**Root cause**: Container không resolve được `vocalmeet.local`, và HTTP không hỗ trợ Basic Auth cho WooCommerce.

**Solution**:

```yaml
# docker-compose
define('VOCALMEET_WOO_API_WC_REST_BASE_URL', 'https://nginx');
define('VOCALMEET_WOO_API_SSLVERIFY', false);
define('WP_ENVIRONMENT_TYPE', 'local');
```

- `https://nginx`: Internal Docker network hostname, HTTPS qua nginx
- `SSLVERIFY=false`: Self-signed cert không trusted
- `WP_ENVIRONMENT_TYPE=local`: Cho phép disable SSL verify
