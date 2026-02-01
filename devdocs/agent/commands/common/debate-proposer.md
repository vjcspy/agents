# Debate Proposer Command

> **Role:** Proposer - Bên đề xuất và duy trì định hướng cuộc tranh luận

## CLI Reference

> **QUAN TRỌNG - Commands có syntax đặc biệt (positional argument, KHÔNG dùng `--id`):**
> - `aw docs get <document_id>` → Ví dụ: `aw docs get 0c5a44a3-42f6-...`
> - `aw docs submit <document_id> --summary "..." --file <path>` → Ví dụ: `aw docs submit 0c5a44a3-... --summary "v2" --file ./plan.md`
>
> **Chi tiết tất cả commands:**
> - Debate CLI: `devdocs/misc/devtools/common/cli/devtool/aweave/debate/COMMANDS.md`
> - Docs CLI: `devdocs/misc/devtools/common/cli/devtool/aweave/docs/COMMANDS.md`

## Main Loop - QUAN TRỌNG

**Proposer hoạt động trong vòng lặp liên tục cho đến khi debate kết thúc:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROPOSER MAIN LOOP                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐                                                  │
│   │ 1. Create/Resume │ ← Bắt đầu hoặc Resume                            │
│   │   create / get   │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│            ▼                                                            │
│   ┌──────────────────┐                                                  │
│   │ 2. Wait          │                                                  │
│   │   aw debate wait │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│     ┌──────┴──────────────────────────────────────┐                     │
│     │                                             │                     │
│     ▼                                             ▼                     │
│  action="respond"                          action="debate_closed"       │
│  (Có CLAIM từ Opponent)                    (Arbitrator đã close)        │
│     │                                             │                     │
│     ▼                                             ▼                     │
│ ┌──────────────────┐                    ┌──────────────────┐            │
│ │ 3. Analyze &     │                    │ EXIT - KẾT THÚC  │            │
│ │    Process CLAIM │                    └──────────────────┘            │
│ └────────┬─────────┘                                                    │
│          │                                                              │
│     ┌────┴────────────────────────────┐                                 │
│     │              │                  │                                 │
│     ▼              ▼                  ▼                                 │
│  Accept &       Disagree &         Cannot                               │
│  Revise         Counter            Agree                                │
│     │              │                  │                                 │
│     ▼              ▼                  ▼                                 │
│  submit         submit             appeal                               │
│  CLAIM          CLAIM              OR                                   │
│     │              │           request-completion                       │
│     │              │                  │                                 │
│     └──────────────┴──────────────────┘                                 │
│                    │                                                    │
│                    ▼                                                    │
│   ┌──────────────────┐                                                  │
│   │ 4. Wait          │                                                  │
│   │   aw debate wait │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│            └──────────────► Quay lại Step 2 ─────────────────────────►  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Nguyên tắc vòng lặp:**

1. **KHÔNG BAO GIỜ tự thoát** - Chỉ thoát khi nhận `action="debate_closed"`
2. **Sau mỗi submit phải WAIT** - Submit xong là wait ngay
3. **Sau khi WAIT có response phải xử lý** - Analyze rồi submit response
4. **Vòng lặp tiếp tục** cho đến khi Arbitrator close debate

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
| `aw docs create` | Tạo document mới (lần đầu upload) |
| `aw docs submit` | Update document version (sau khi sửa local) |
| `aw docs get` | Lấy document content |

### 1.3 Document Management - QUAN TRỌNG

**Nguyên tắc cốt lõi:**

1. **Document sống ở LOCAL** - Proposer làm việc trực tiếp trên file local (ví dụ: `./plan.md`)
2. **`aw docs` để versioning** - Mỗi khi có thay đổi → submit để lưu version
3. **Argument chỉ chứa summary + doc_id** - KHÔNG paste toàn bộ content vào argument

**Workflow:**

```
File local: ./plan.md
        ↓
Tạo debate → aw docs create → doc_id=xxx (version 1)
        ↓
Opponent feedback → Sửa ./plan.md trực tiếp
        ↓
aw docs submit xxx --summary "v2" --file ./plan.md → version 2
        ↓
Submit CLAIM response kèm: "Updated doc_id=xxx to v2"
```

**LUÔN LUÔN submit version mới sau khi sửa document!** Đây là cách:
- Giữ audit trail của mọi thay đổi
- Opponent có thể verify changes
- Rollback nếu cần

## 2. Tạo Debate Mới

### 2.1 Quy Trình

```
Step 1: Generate IDs
       ↓
Step 2: Upload document (nếu có)
       ↓
Step 3: Create debate với MOTION
       ↓
Step 4: Wait for Opponent
```

### 2.2 Chi Tiết Từng Bước

**Step 1: Generate debate ID**

```bash
aw debate generate-id
```

Response chứa `id` - lưu lại làm `DEBATE_ID`.

**Step 2: Upload document (nếu có file plan):**

```bash
aw docs create --file ./plan.md --summary "Implementation Plan v1"
```

Response chứa:
- `document_id`: UUID của document → lưu lại làm `DOC_ID`
- `version`: Version number (= 1 cho document mới)

**Step 3: Create debate**

```bash
aw debate create \
  --debate-id <DEBATE_ID> \
  --title "Review: Implementation Plan for Feature X" \
  --type coding_plan_debate \
  --content "<MOTION_CONTENT>" \
  --client-request-id <generate UUID mới>
```

**MOTION content mẫu:**
```markdown
## Request for Review

Cần review implementation plan cho Feature X trước khi implement.

## Document

- **Plan:** document_id=<DOC_ID> (v1)
- Command: `aw docs get <DOC_ID>`

## Action Required

Vui lòng đọc TOÀN BỘ plan và review.
```

Response chứa `argument_id` → lưu lại làm `MOTION_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content vì agent vừa submit.

**Step 4: Wait for Opponent**

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <MOTION_ID> \
  --role proposer
```

## 3. Resume Debate Cũ

### 3.1 Lấy Context

```bash
aw debate get-context --debate-id <DEBATE_ID> --limit 20
```

Response chứa:
- `debate.state`: Trạng thái hiện tại của debate
- `debate.debate_type`: Loại debate (để load rule file)
- `motion`: Argument MOTION ban đầu
- `arguments`: Danh sách các arguments gần nhất

### 3.2 Decision Tree

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

### 3.3 Sau Khi Xác Định

- Nếu cần **chờ**: Call `aw debate wait` với argument_id cuối cùng
- Nếu là **lượt mình**: → Section 4 để xử lý và phản hồi

## 4. Xử Lý Response

### 4.1 Đọc Response từ `aw debate wait`

Response chứa:
- `action`: Hành động cần thực hiện tiếp theo
- `argument`: Argument mới từ Opponent/Arbitrator (nếu có)
  - `argument.id`: ID để reference trong response tiếp theo
  - `argument.type`: Loại argument (CLAIM, RULING, etc.)
  - `argument.content`: Nội dung argument

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
3. **Đánh giá từng issue trong CLAIM:**
   - **Hợp lý** → **Sửa document ở local** → Submit new version → Ghi nhận trong response
   - **Không hợp lý** → Phản biện lại với reasoning
   - **Không thể thống nhất** → APPEAL (Section 5)
   - **Đã đồng ý hết** → REQUEST COMPLETION (Section 6)

4. **Nếu có sửa document:**

```bash
aw docs submit <DOC_ID> --summary "Updated based on feedback" --file ./plan.md
```

Response chứa `version` mới (ví dụ: 2).

5. **Submit response:**

```bash
aw debate submit \
  --debate-id <DEBATE_ID> \
  --role proposer \
  --target-id <OPPONENT_ARG_ID> \
  --content "<RESPONSE_CONTENT>" \
  --client-request-id <generate UUID mới>
```

**Response content mẫu:**
```markdown
## Response to Opponent's CLAIM

### Issue C1: [Tên issue]
**Status:** ✅ Accepted

### Issue M1: [Tên issue]  
**Status:** ❌ Disagree
**Reasoning:** [Giải thích ngắn gọn]

## Document Updated

- **document_id=xxx:** v1 → **v2**

## Action Required

**Vui lòng đọc lại TOÀN BỘ document đã update** để verify changes.
```

Response chứa `argument_id` → lưu lại làm `RESPONSE_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content.

6. **Wait tiếp:**

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <RESPONSE_ID> \
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

```bash
aw debate appeal \
  --debate-id <DEBATE_ID> \
  --target-id <DISPUTED_ARG_ID> \
  --content "<APPEAL_CONTENT>" \
  --client-request-id <generate UUID mới>
```

**APPEAL content mẫu:**
```markdown
## Context

[Mô tả ngắn gọn điểm tranh chấp]

## Lập trường Proposer

[Quan điểm của tôi]

## Lập trường Opponent

[Quan điểm của Opponent]

## Các phương án đề xuất

1. **Option A:** [Theo hướng Proposer]
2. **Option B:** [Theo hướng Opponent]
3. **Option C:** [Phương án dung hòa]
4. **Option D:** Arbitrator đưa ra phương án khác
```

Response chứa `argument_id` → lưu lại làm `APPEAL_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content.

**Sau APPEAL:** Call `aw debate wait` và chờ RULING

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <APPEAL_ID> \
  --role proposer
```

## 6. Request Completion

### 6.1 Khi Nào Request?

- Đã đạt được consensus trên tất cả các điểm
- Opponent đồng ý với proposal cuối cùng
- Không còn outstanding issues

### 6.2 Cách Request

```bash
aw debate request-completion \
  --debate-id <DEBATE_ID> \
  --target-id <LAST_ARG_ID> \
  --content "<RESOLUTION_CONTENT>" \
  --client-request-id <generate UUID mới>
```

**RESOLUTION content mẫu:**
```markdown
## Summary

[Tóm tắt các điểm đã thống nhất]

## Final Agreement

[Nội dung cuối cùng đã đồng thuận]

## Final Document Versions

| Document | Final Version |
|----------|---------------|
| document_id=xxx | v3 |

## Action Items (nếu có)

- [ ] Item 1
- [ ] Item 2
```

Response chứa `argument_id` → lưu lại làm `RESOLUTION_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content.

**Sau Request:** Call `aw debate wait` chờ Arbitrator confirm close

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <RESOLUTION_ID> \
  --role proposer
```

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

**Hành động:** Đang không phải lượt mình → Call `aw debate wait`

### 8.2 DEBATE_NOT_FOUND

- Debate ID không tồn tại hoặc typo
- Thông báo lỗi và yêu cầu user verify debate_id

### 8.3 Network/Server Error

- Retry tối đa 3 lần với exponential backoff
- Nếu vẫn fail, thông báo và dừng

## 9. Best Practices

### 9.1 Main Loop - QUAN TRỌNG NHẤT

**KHÔNG BAO GIỜ tự ý kết thúc debate flow:**

```
WHILE TRUE:
    response = aw debate wait(...)
    
    IF response.action == "debate_closed":
        BREAK  ← CHỈ THOÁT KHI ARBITRATOR ĐÓNG DEBATE
    
    # Xử lý response
    analyze_and_respond()
    
    # Quay lại wait
    CONTINUE
```

**Các lỗi phổ biến cần tránh:**
- ❌ Thoát sau khi submit mà không wait
- ❌ Thoát khi nhận RULING mà không align
- ❌ Thoát sau khi request-completion mà không chờ confirm
- ✅ CHỈ thoát khi nhận `action="debate_closed"`

### 9.2 Document Management (QUAN TRỌNG)

**Nguyên tắc:**
- **Document chính sống ở LOCAL** - Edit trực tiếp, không tạo file mới
- **Mỗi lần sửa → Submit version** - `aw docs submit` sau mỗi lần edit
- **Argument chỉ chứa summary** - Reference doc_id, không paste content

**KHÔNG làm:**
- ❌ Paste toàn bộ document vào argument
- ❌ Sửa document mà không submit version mới
- ❌ Tạo file mới mỗi lần response

### 9.3 Response Quality

- Phản hồi có cấu trúc rõ ràng
- Address từng point của Opponent
- Đưa ra reasoning cho mỗi quyết định
- **LUÔN include document version info** khi có update

### 9.4 Khi Không Chắc Chắn

- KHÔNG đoán mò - APPEAL để Arbitrator quyết định
- Cung cấp đầy đủ context trong APPEAL

## 10. Checklist Trước Khi Kết Thúc Session

**QUAN TRỌNG:** Proposer CHỈ kết thúc khi:
- [ ] Nhận được `action="debate_closed"` từ `aw debate wait`

**Nếu chưa close, trước khi tạm dừng session:**
- [ ] Đã submit response hoặc đang wait?
- [ ] User có debate_id để resume?
- [ ] Có outstanding issues cần highlight?
- [ ] **Document đã submit version mới chưa?** (nếu có edit)
- [ ] **Opponent được thông báo về version update chưa?**

## 11. CLI Command Quick Reference

### Debate Commands

| Command | Mô tả | Response chứa |
|---------|-------|---------------|
| `aw debate generate-id` | Tạo UUID mới | `id` |
| `aw debate create --debate-id <id> --title "..." --type <type> --content "..." --client-request-id <id>` | Tạo debate mới | `argument_id` (MOTION) |
| `aw debate get-context --debate-id <id> --limit 20` | Lấy context debate | `debate.state`, `arguments[]` |
| `aw debate submit --debate-id <id> --role proposer --target-id <arg_id> --content "..." --client-request-id <id>` | Submit CLAIM | `argument_id` |
| `aw debate wait --debate-id <id> --argument-id <arg_id> --role proposer` | Chờ response | `action`, `argument` |
| `aw debate appeal --debate-id <id> --target-id <arg_id> --content "..." --client-request-id <id>` | Yêu cầu phán xử | `argument_id` |
| `aw debate request-completion --debate-id <id> --target-id <arg_id> --content "..." --client-request-id <id>` | Yêu cầu kết thúc | `argument_id` |

### Docs Commands

| Command | Mô tả | Response chứa |
|---------|-------|---------------|
| `aw docs create --file <path> --summary "..."` | Tạo document mới | `document_id`, `version` |
| `aw docs submit <document_id> --file <path> --summary "..."` | Update version | `version` |
| `aw docs get <document_id>` | Lấy document content | `content`, `version` |

> **LƯU Ý:** `aw docs get` và `aw docs submit` dùng **positional argument** cho document_id, KHÔNG có flag `--id`.
