# Presentation

## Key points

### cần nhắc đến https

Basic Auth chỉ base64 encode, không mã hoá.
Nó chỉ an toàn khi:

đường truyền được mã hoá bởi HTTPS
Do đó, “HTTPS requirement” không phải hình thức, mà là điều kiện để bảo vệ secret.

### REST refactor notes (để “đẹp điểm” khi review)

- Error taxonomy: propagate `status` từ `WP_Error` (không wrap 500 cố định) để client hiển thị đúng (400/401/403/500).
- Fetch: set `credentials: 'same-origin'` để đảm bảo cookies luôn được gửi kèm request → tránh nonce fail do lệch cấu hình.
- Authorization: demo có thể require login; production nên enforce capability gần domain (`manage_woocommerce` / `publish_products`) và giải thích trade-off.
- Vẫn gọi WooCommerce REST API server-side để đúng yêu cầu bài thi, đồng thời không expose consumer secret ra browser.
