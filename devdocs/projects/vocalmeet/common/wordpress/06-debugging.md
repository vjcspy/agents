# Debugging trong WordPress (cơ chế & best practice)

## 1) WordPress “bật debug” bằng cách nào?

Trung tâm của cơ chế debug là hàm `wp_debug_mode()` trong core.

- `WP_DEBUG` quyết định mức `error_reporting()` (bật E_NOTICE/E_WARNING/E_DEPRECATED… khi development).
- `WP_DEBUG_DISPLAY` quyết định có `ini_set('display_errors', 1|0)` hay không.
- `WP_DEBUG_LOG` quyết định việc log vào `wp-content/debug.log` (thông qua `error_log()` với cấu hình phù hợp).

Điểm quan trọng: ngay cả khi `WP_DEBUG_DISPLAY = true`, WordPress vẫn có thể *tắt hiển thị lỗi* cho một số loại request (AJAX/REST/XML-RPC) để tránh làm hỏng response body.

## 2) Vì sao không nên sửa `index.php` để show lỗi?

Không nên sửa `index.php` để “bật show error” vì:

- Dễ làm lệch hành vi giữa môi trường và khó kiểm soát khi deploy.
- Dễ gây lộ thông tin nhạy cảm (đường dẫn, query, dữ liệu) nếu lỡ chạy ở môi trường không an toàn.
- WordPress đã có cơ chế chuẩn qua constants trong `wp-config.php` + cấu hình PHP runtime (php.ini/Xdebug).

Best practice: cấu hình qua `wp-config.php`, và dùng env (Docker) để chọn profile dev/prod.

## 3) “Full stack trace” trong request: WordPress có tự show không?

Mặc định WordPress không nhằm mục tiêu “show full stack trace” ra response khi có lỗi.

- `WP_DEBUG_DISPLAY` chủ yếu điều khiển `display_errors`.
- Stack trace chi tiết thường cần Xdebug (`xdebug.mode=develop`) hoặc error handler chuyên dụng.

Trong local dev (Docker), hướng đi chuẩn là:

- `WP_DEBUG = true`
- `WP_DEBUG_LOG = true` (để xem lỗi ổn định qua `wp-content/debug.log`)
- `WP_DEBUG_DISPLAY = false` (để response REST/AJAX không bị “vỡ JSON/HTML”)
- Bật Xdebug “develop” nếu muốn stack trace rõ ràng

## 4) Cấu hình khuyến nghị theo môi trường

### Local development

- `WP_DEBUG=true`
- `WP_DEBUG_LOG=true`
- `WP_DEBUG_DISPLAY=false`
- `SCRIPT_DEBUG=true`

### Production

- `WP_DEBUG=false`
- `WP_DEBUG_LOG=false` (hoặc bật log theo nhu cầu nhưng phải kiểm soát quyền truy cập)
- `WP_DEBUG_DISPLAY=false`
- `SCRIPT_DEBUG=false`

## 5) Gợi ý pattern với Docker

Nên define các flags debug qua `docker-compose` (environment), sau đó để `wp-config.php` đọc từ env.

Ưu điểm:

- Switch dev/prod rõ ràng qua env, không phải sửa code.
- Tránh tình trạng define trùng lặp qua `WORDPRESS_CONFIG_EXTRA`.
