# Debate Proposer Command

> **Role:** Proposer - Bên đề xuất và duy trì định hướng cuộc tranh luận

## 1. Khởi Động

### 1.1 Xác Định Ngữ Cảnh

Khi được yêu cầu làm **Proposer** trong debate, PHẢI xác định rõ:

1. **Có `debate_id` không?**
   - **CÓ** → Resume debate cũ (Section 3)
   - **KHÔNG** → Tạo debate mới (Section 2)

2. **`debateType` là gì?**
   - `coding_plan_debate` → Load rule: `devdocs/agent/rules/common/debate/proposer/coding-plan.md`
   - `general_debate` → Load rule: `devdocs/agent/rules/common/debate/proposer/general.md`

### 1.2 CLI Tools Được Phép Sử Dụng

| Tool | Mục đích |
|------|----------|
| `aw debate generate-id` | Tạo UUID cho debate_id, client_request_id |
| `aw debate create` | Tạo debate mới với MOTION |
| `aw debate get-context` | Lấy context debate đã tồn tại |
| `aw debate submit` | Submit CLAIM phản hồi |
| `aw debate wait` | Chờ response từ Opponent/Arbitrator |
| `aw debate appeal` | Yêu cầu Arbitrator phán xử |
| `aw debate request-completion` | Yêu cầu kết thúc debate |
| `aw docs create` | Tạo document mới (cho tài liệu dài) |
| `aw docs submit` | Update document version |
| `aw docs get` | Lấy document content |

## 2. Tạo Debate Mới

### 2.1 Quy Trình

```
Step 1: Generate IDs
       ↓
Step 2: Chuẩn bị MOTION content
       ↓
Step 3: Create debate
       ↓
Step 4: Wait for Opponent
```

### 2.2 Chi Tiết Từng Bước

**Step 1: Generate IDs**

```bash
# Generate debate_id
DEBATE_ID=$(aw debate generate-id | jq -r '.content[0].data.id')

# Generate client_request_id (cho idempotency)
CLIENT_REQ_ID=$(aw debate generate-id | jq -r '.content[0].data.id')
```

**Step 2: Chuẩn bị MOTION Content**

MOTION content PHẢI bao gồm:
- **Tiêu đề/Vấn đề chính** cần debate
- **Context đầy đủ** để Opponent hiểu
- **Nếu có tài liệu dài**: Sử dụng `aw docs create` và include `doc_id` trong content

```bash
# Nếu có tài liệu dài (>5KB), upload trước
aw docs create --file ./detailed-plan.md --title "Implementation Plan v1"
# Response: { "doc_id": "xxx-xxx" }

# MOTION content format
"""
## Vấn đề cần debate

[Mô tả ngắn gọn vấn đề]

## Chi tiết

[Summary của proposal]

## Tài liệu tham khảo

- Full implementation plan: doc_id=xxx-xxx (use `aw docs get --id xxx-xxx` to view)
"""
```

**Step 3: Create Debate**

```bash
aw debate create \
  --debate-id $DEBATE_ID \
  --title "Tiêu đề debate" \
  --debate-type coding_plan_debate \
  --file ./motion.md \
  --client-request-id $CLIENT_REQ_ID
```

**Output quan trọng:**
- `debate_id`: ID của debate
- `argument_id`: ID của MOTION argument (cần cho wait)

**Step 4: Wait for Opponent**

```bash
aw debate wait \
  --debate-id $DEBATE_ID \
  --argument-id $MOTION_ID \
  --role proposer
```

**Sau khi nhận response:** → Chuyển sang Section 4 để xử lý

## 3. Resume Debate Cũ

### 3.1 Lấy Context

```bash
aw debate get-context --debate-id <debate_id> --argument-limit 20
```

### 3.2 Phân Tích Response

Từ response, xác định:

1. **`debate.state`** hiện tại
2. **Argument cuối cùng** (`arguments[-1]`)
   - `role`: Ai gửi (proposer/opponent/arbitrator)
   - `type`: Loại argument (CLAIM/RULING/INTERVENTION/...)

### 3.3 Decision Tree

```
IF state == "CLOSED":
    → Thông báo debate đã đóng, không cần hành động
    
ELIF state == "AWAITING_OPPONENT":
    → Đang chờ Opponent, call `aw debate wait`
    
ELIF state == "AWAITING_PROPOSER":
    → Lượt của mình, đọc argument cuối và phản hồi
    
ELIF state == "AWAITING_ARBITRATOR":
    → Cả 2 đang chờ Arbitrator, call `aw debate wait`
    
ELIF state == "INTERVENTION_PENDING":
    → Arbitrator can thiệp, call `aw debate wait` chờ RULING
```

### 3.4 Sau Khi Xác Định

- Nếu cần **chờ**: Call `aw debate wait` với argument_id cuối cùng
- Nếu là **lượt mình**: → Section 4 để xử lý và phản hồi

## 4. Xử Lý Response

### 4.1 Parse Response từ `aw debate wait`

```json
{
  "status": "new_argument",
  "action": "respond",
  "debate_state": "AWAITING_PROPOSER",
  "argument": {
    "id": "xxx",
    "type": "CLAIM",
    "role": "opponent",
    "content": "..."
  }
}
```

### 4.2 Action Mapping

| `action` | Ý nghĩa | Hành động |
|----------|---------|-----------|
| `respond` | Lượt phản hồi | Phân tích CLAIM và submit response |
| `align_to_ruling` | Arbitrator đã phán quyết | Follow ruling và submit |
| `wait_for_ruling` | Đang chờ Arbitrator | Call `aw debate wait` tiếp |
| `debate_closed` | Debate kết thúc | Dừng |

### 4.3 Phản Hồi CLAIM từ Opponent

**Workflow:**

1. **Đọc kỹ CLAIM** của Opponent
2. **Load rule file** theo debateType để xử lý đúng nghiệp vụ
3. **Đánh giá CLAIM:**
   - **Hợp lý** → Chấp nhận và revise proposal
   - **Không hợp lý** → Phản biện lại
   - **Không thể thống nhất** → APPEAL (Section 5)
   - **Đã đồng ý hết** → REQUEST COMPLETION (Section 6)

4. **Submit response:**

```bash
aw debate submit \
  --debate-id $DEBATE_ID \
  --role proposer \
  --target-id $OPPONENT_ARG_ID \
  --file ./response.md \
  --client-request-id $(aw debate generate-id | jq -r '.content[0].data.id')
```

5. **Wait tiếp:**

```bash
aw debate wait \
  --debate-id $DEBATE_ID \
  --argument-id $NEW_ARG_ID \
  --role proposer
```

### 4.4 Xử Lý RULING từ Arbitrator

Khi `action = "align_to_ruling"`:

1. **Đọc nội dung RULING** trong `argument.content`
2. **Xác định direction** từ Arbitrator
3. **Align proposal** theo ruling
4. **Submit response** với nội dung đã align
5. **Wait** cho Opponent phản hồi

## 5. Submit APPEAL

### 5.1 Khi Nào APPEAL?

- Không thể đạt được consensus với Opponent
- Tranh cãi kéo dài > 3 vòng trên cùng một điểm
- Cần quyết định từ human (Arbitrator)

### 5.2 Cách APPEAL

**QUAN TRỌNG:** APPEAL content PHẢI bao gồm:
- Context đầy đủ của điểm tranh chấp
- Lập trường của Proposer (mình)
- Lập trường của Opponent
- **Các options** cho Arbitrator chọn (LUÔN có option cuối là "Phương án khác")

```markdown
## Context

[Mô tả ngắn gọn điểm tranh chấp]

## Lập trường Proposer

[Quan điểm của tôi]

## Lập trường Opponent

[Quan điểm của Opponent]

## Các phương án đề xuất

1. **Option A:** [Mô tả] - Theo hướng Proposer
2. **Option B:** [Mô tả] - Theo hướng Opponent  
3. **Option C:** [Mô tả] - Phương án dung hòa
4. **Option D:** Arbitrator đưa ra phương án khác
```

```bash
aw debate appeal \
  --debate-id $DEBATE_ID \
  --target-id $DISPUTED_ARG_ID \
  --file ./appeal.md \
  --client-request-id $(aw debate generate-id | jq -r '.content[0].data.id')
```

**Sau APPEAL:** Call `aw debate wait` và chờ RULING

## 6. Request Completion

### 6.1 Khi Nào Request?

- Đã đạt được consensus trên tất cả các điểm
- Opponent đồng ý với proposal cuối cùng
- Không còn outstanding issues

### 6.2 Cách Request

```markdown
## Summary

[Tóm tắt các điểm đã thống nhất]

## Final Agreement

[Nội dung cuối cùng đã đồng thuận]

## Action Items (nếu có)

- [ ] Item 1
- [ ] Item 2
```

```bash
aw debate request-completion \
  --debate-id $DEBATE_ID \
  --target-id $LAST_ARG_ID \
  --file ./resolution.md \
  --client-request-id $(aw debate generate-id | jq -r '.content[0].data.id')
```

**Sau Request:** Call `aw debate wait` chờ Arbitrator confirm close

## 7. Xử Lý Timeout

### 7.1 Nhận Timeout Response

```json
{
  "status": "timeout",
  "message": "No response after 300s"
}
```

### 7.2 Hành Động

1. **Thông báo cho user:** "Debate đang pending, Opponent chưa phản hồi sau 5 phút"
2. **Dừng và hướng dẫn resume:** Cung cấp `debate_id` để user có thể resume sau
3. **KHÔNG tự động retry** - để user quyết định

## 8. Error Handling

### 8.1 ACTION_NOT_ALLOWED

```json
{
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "current_state": "AWAITING_OPPONENT",
    "allowed_roles": ["opponent"]
  }
}
```

**Hành động:** Đang không phải lượt mình → Call `aw debate wait`

### 8.2 DEBATE_NOT_FOUND

- Debate ID không tồn tại hoặc typo
- Thông báo lỗi và yêu cầu user verify debate_id

### 8.3 Network/Server Error

- Retry tối đa 3 lần với exponential backoff
- Nếu vẫn fail, thông báo và dừng

## 9. Best Practices

### 9.1 Document Sharing

- **Content ngắn (<5KB):** Include trực tiếp trong argument
- **Content dài (>5KB):** Dùng `aw docs create`, share doc_id

### 9.2 Response Quality

- Phản hồi có cấu trúc rõ ràng
- Address từng point của Opponent
- Đưa ra reasoning cho mỗi quyết định

### 9.3 Khi Không Chắc Chắn

- KHÔNG đoán mò - APPEAL để Arbitrator quyết định
- Cung cấp đầy đủ context trong APPEAL

### 9.4 Giữ Focus

- Một argument nên tập trung vào một chủ đề
- Nếu có nhiều điểm, structure rõ ràng theo sections

## 10. Checklist Trước Khi Kết Thúc Session

- [ ] Đã submit response hoặc đang wait?
- [ ] User có debate_id để resume?
- [ ] Có outstanding issues cần highlight?
