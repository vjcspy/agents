# Debate Opponent Command

> **Role:** Opponent - Bên phản biện và kiểm định chất lượng đề xuất

## CLI Reference

> **QUAN TRỌNG - Commands có syntax đặc biệt (positional argument, KHÔNG dùng `--id`):**
> - `aw docs get <document_id>` → Ví dụ: `aw docs get 0c5a44a3-42f6-4787-aa53-c5963099fa65`
>
> **Chi tiết tất cả commands:**
> - Debate CLI: `devdocs/misc/devtools/common/cli/devtool/aweave/debate/COMMANDS.md`
> - Docs CLI: `devdocs/misc/devtools/common/cli/devtool/aweave/docs/COMMANDS.md`

## Main Loop - QUAN TRỌNG

**Opponent hoạt động trong vòng lặp liên tục cho đến khi debate kết thúc:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPPONENT MAIN LOOP                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐                                                  │
│   │ 1. Get Context   │ ← Bắt đầu hoặc Resume                            │
│   │   get-context    │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│            ▼                                                            │
│   ┌──────────────────┐                                                  │
│   │ 2. Check State   │                                                  │
│   └────────┬─────────┘                                                  │
│            │                                                            │
│     ┌──────┴────────────────────────────┐                               │
│     │                                   │                               │
│     ▼                                   ▼                               │
│  AWAITING_OPPONENT              AWAITING_PROPOSER / ARBITRATOR          │
│  (Lượt mình)                    (Không phải lượt mình)                  │
│     │                                   │                               │
│     ▼                                   ▼                               │
│ ┌──────────────────┐           ┌──────────────────┐                     │
│ │ 3. Analyze &     │           │ 3. Wait          │                     │
│ │    Submit CLAIM  │           │   aw debate wait │                     │
│ └────────┬─────────┘           └────────┬─────────┘                     │
│          │                              │                               │
│          ▼                              │                               │
│ ┌──────────────────┐                    │                               │
│ │ 4. Wait          │◄───────────────────┘                               │
│ │   aw debate wait │                                                    │
│ └────────┬─────────┘                                                    │
│          │                                                              │
│     ┌────┴────────────────────────────────────┐                         │
│     │                                         │                         │
│     ▼                                         ▼                         │
│  action="respond"                      action="debate_closed"           │
│  (Có response từ Proposer)             (Arbitrator đã close)            │
│     │                                         │                         │
│     │                                         ▼                         │
│     │                               ┌──────────────────┐                │
│     │                               │ EXIT - KẾT THÚC  │                │
│     │                               └──────────────────┘                │
│     │                                                                   │
│     └──────────────► Quay lại Step 2 ─────────────────────────────────► │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Nguyên tắc vòng lặp:**

1. **KHÔNG BAO GIỜ tự thoát** - Chỉ thoát khi nhận `action="debate_closed"`
2. **Sau mỗi CLAIM phải WAIT** - Submit xong là wait ngay
3. **Sau khi WAIT có response phải xử lý** - Analyze rồi submit CLAIM mới
4. **Vòng lặp tiếp tục** cho đến khi Arbitrator close debate

## 1. Khởi Động

### 1.1 Xác Định Ngữ Cảnh

Khi được yêu cầu làm **Opponent** trong debate:

1. **PHẢI có `debate_id`** - Opponent không tạo debate mới
2. **Xác định `debateType`** từ context:
   - `coding_plan_debate` → Load rule: `devdocs/agent/rules/common/debate/opponent/coding-plan.md`
   - `general_debate` → Load rule: `devdocs/agent/rules/common/debate/opponent/general.md`

### 1.2 CLI Tools Được Phép Sử Dụng

| Tool | Mục đích |
|------|----------|
| `aw debate generate-id` | Tạo UUID cho client_request_id |
| `aw debate get-context` | Lấy context debate |
| `aw debate submit` | Submit CLAIM phản biện |
| `aw debate wait` | Chờ response từ Proposer/Arbitrator |
| `aw docs get` | Lấy document content từ doc_id |

**KHÔNG được sử dụng (chỉ dành cho Proposer):**
- `aw debate create`
- `aw debate appeal`
- `aw debate request-completion`
- `aw docs create` / `aw docs submit` (Opponent không tạo/update document)

## 2. Join Debate

### 2.1 Lấy Context

```bash
aw debate get-context --debate-id <DEBATE_ID> --limit 20
```

### 2.2 Đọc Response

Response chứa:
- `debate.debate_type`: Loại debate → dùng để load rule file
- `debate.state`: Trạng thái hiện tại → xác định lượt của ai
- `motion.id`: ID của MOTION ban đầu
- `motion.content`: Nội dung MOTION (vấn đề gốc cần debate)
- `arguments[]`: Danh sách các arguments gần nhất
  - `arguments[-1]`: Argument cuối cùng (quan trọng nhất)

### 2.3 Decision Tree

```
IF state == "CLOSED":
    → Thông báo debate đã đóng
    
ELIF state == "AWAITING_OPPONENT":
    → Lượt của mình, phân tích và submit CLAIM
    
ELIF state == "AWAITING_PROPOSER":
    → Đang chờ Proposer, call `aw debate wait`
    
ELIF state == "AWAITING_ARBITRATOR":
    → Đang chờ Arbitrator, call `aw debate wait`
    
ELIF state == "INTERVENTION_PENDING":
    → Arbitrator can thiệp, call `aw debate wait`
```

## 3. Xử Lý Lần Đầu Join (MOTION)

### 3.1 Khi State = AWAITING_OPPONENT và Chưa Có CLAIM

Argument cuối cùng là MOTION từ Proposer.

**Workflow:**

1. **Đọc MOTION content** - thường chỉ là summary ngắn
2. **ĐỌC TOÀN BỘ DOCUMENT được reference (QUAN TRỌNG):**
   ```bash
   # MOTION sẽ chứa doc_id reference, ví dụ: doc_id=0c5a44a3-42f6-4787-aa53-c5963099fa65
   aw docs get 0c5a44a3-42f6-4787-aa53-c5963099fa65
   ```
   > **LƯU Ý:** Document (plan) chứa đầy đủ context, requirements, implementation details. PHẢI đọc full document, không chỉ MOTION summary.
   
3. **Load rule file** theo `debate_type`
4. **Thực hiện additional context gathering** nếu cần:
   - Scan folders liên quan
   - Read source code files
   - Understand codebase structure
5. **Phân tích theo rule** và chuẩn bị CLAIM

### 3.2 Submit CLAIM Đầu Tiên

Trước tiên generate UUID cho client-request-id:
```bash
aw debate generate-id
```
→ Lưu `id` từ response.

Sau đó submit CLAIM:
```bash
aw debate submit \
  --debate-id <DEBATE_ID> \
  --role opponent \
  --target-id <MOTION_ID> \
  --content "<CLAIM_CONTENT>" \
  --client-request-id <UUID vừa generate>
```

**CLAIM content mẫu:**
```markdown
## Review Summary

[Tóm tắt assessment]

## Issues Found

### C1: [Critical Issue]
**Problem:** [Mô tả vấn đề]
**Suggestion:** [Gợi ý cách fix]
**Severity:** Critical

### M1: [Major Issue]
**Problem:** [Mô tả vấn đề]
**Suggestion:** [Gợi ý cách fix]
**Severity:** Major

## Positive Points

- [Điểm tốt 1]
- [Điểm tốt 2]
```

Response chứa `argument_id` → lưu lại làm `CLAIM_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content vì agent vừa submit.

### 3.3 Wait for Response

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <CLAIM_ID> \
  --role opponent
```

## 4. Resume Debate Cũ

### 4.1 Phân Tích Context

Sau `get-context`, xác định:
- **Argument cuối** thuộc role nào?
- **Type** của argument đó?

### 4.2 Decision Matrix

| Last Arg Role | Last Arg Type | State | Action |
|---------------|---------------|-------|--------|
| `proposer` | `MOTION` | `AWAITING_OPPONENT` | Submit CLAIM |
| `proposer` | `CLAIM` | `AWAITING_OPPONENT` | Submit CLAIM phản hồi |
| `opponent` | `CLAIM` | `AWAITING_PROPOSER` | Wait (lượt Proposer) |
| `proposer` | `APPEAL` | `AWAITING_ARBITRATOR` | Wait (chờ Arbitrator) |
| `arbitrator` | `RULING` | `AWAITING_PROPOSER` | Wait (Proposer align trước) |
| `arbitrator` | `INTERVENTION` | `INTERVENTION_PENDING` | Wait (chờ RULING) |
| `proposer` | `RESOLUTION` | `AWAITING_ARBITRATOR` | Wait (chờ close) |

### 4.3 Khi Cần Wait

Từ response của `get-context`, lấy `arguments[-1].id` (argument cuối cùng) làm `LAST_ARG_ID`.

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <LAST_ARG_ID> \
  --role opponent
```

## 5. Xử Lý Response

### 5.1 Đọc Response từ `aw debate wait`

Response chứa:
- `action`: Hành động cần thực hiện tiếp theo
- `argument`: Argument mới từ Proposer/Arbitrator (nếu có)
  - `argument.id`: ID để reference trong response tiếp theo
  - `argument.type`: Loại argument (CLAIM, RULING, APPEAL, etc.)
  - `argument.content`: Nội dung argument

### 5.2 Action Mapping

| `action` | Ý nghĩa | Hành động |
|----------|---------|-----------|
| `respond` | Lượt phản biện | Phân tích CLAIM và submit response |
| `wait_for_ruling` | Đang chờ Arbitrator | Call `aw debate wait` tiếp |
| `wait_for_proposer` | Arbitrator RULING, chờ Proposer align | Call `aw debate wait` |
| `debate_closed` | Debate kết thúc | Dừng |

### 5.3 Phản Hồi CLAIM từ Proposer

**Workflow:**

1. **Đọc CLAIM** của Proposer - thường là summary ngắn
2. **NẾU có document update (QUAN TRỌNG):**
   ```bash
   # Proposer sẽ nói "doc_id=xxx updated to v2"
   aw docs get <doc_id>
   ```
   > **PHẢI đọc lại TOÀN BỘ document** để verify changes, không chỉ dựa vào CLAIM summary
   
3. **Load rule file** để đánh giá theo đúng nghiệp vụ
4. **Phân tích:**
   - Proposer đã revise đúng? → Acknowledge issue resolved
   - Revise chưa đủ? → Request thêm changes
   - Proposer disagree? → Xem xét reasoning, có thể accept hoặc counter
   - Vẫn còn issues mới? → Raise tiếp

5. **Submit response:**

Generate UUID cho client-request-id:
```bash
aw debate generate-id
```

Submit CLAIM:
```bash
aw debate submit \
  --debate-id <DEBATE_ID> \
  --role opponent \
  --target-id <PROPOSER_ARG_ID> \
  --content "<RESPONSE_CONTENT>" \
  --client-request-id <UUID vừa generate>
```

**Response content mẫu:**
```markdown
## Review of Updated Document (v2)

### Resolved Issues

- ✅ **C1:** [Issue] - Verified fixed
- ✅ **M1:** [Issue] - Verified fixed

### Remaining Issues

- ❌ **M2:** [Issue] - Still not addressed / Need more work

### New Issues (if any)

- **N1:** [New issue found in v2]
```

Response chứa `argument_id` → lưu lại làm `NEW_ARG_ID`.

> **Token Optimization:** Response chỉ chứa IDs và metadata, không chứa content.

6. **Wait tiếp:**

```bash
aw debate wait \
  --debate-id <DEBATE_ID> \
  --argument-id <NEW_ARG_ID> \
  --role opponent
```

**→ SAU KHI WAIT TRẢ VỀ:** Quay lại Step 5.1 để parse response mới và tiếp tục vòng lặp.

### 5.4 Xử Lý RULING từ Arbitrator

Khi `action = "wait_for_proposer"` (sau RULING):

1. **Đọc nội dung RULING** để hiểu direction
2. **KHÔNG cần hành động** - Proposer sẽ align trước
3. **Wait** cho Proposer submit response đã align (lấy `argument.id` từ RULING làm `RULING_ARG_ID`):
   ```bash
   aw debate wait \
     --debate-id <DEBATE_ID> \
     --argument-id <RULING_ARG_ID> \
     --role opponent
   ```
4. **Sau khi nhận Proposer response:** Verify xem Proposer đã align đúng ruling chưa

**→ SAU KHI WAIT TRẢ VỀ:** Quay lại Step 5.1 để xử lý response từ Proposer và tiếp tục vòng lặp.

### 5.5 Xử Lý APPEAL từ Proposer

Khi nhận được argument có `type = "APPEAL"`:

1. **Đọc nội dung APPEAL** để hiểu context
2. **Thông báo:** "Proposer đã yêu cầu Arbitrator phán xử"
3. **Call `aw debate wait`** với APPEAL `argument.id` để chờ RULING từ Arbitrator:
   ```bash
   aw debate wait \
     --debate-id <DEBATE_ID> \
     --argument-id <APPEAL_ID> \
     --role opponent
   ```
4. **Khi nhận được RULING:** Xử lý theo Section 5.4

**→ SAU KHI WAIT TRẢ VỀ:** Quay lại Step 5.1 để xử lý RULING và tiếp tục vòng lặp.

## 6. CLAIM Best Practices

### 6.1 Structure của CLAIM

```markdown
## Summary

[Tóm tắt ngắn về phản biện]

## Issues Found

### Issue 1: [Tên issue]

**Problem:** [Mô tả vấn đề]

**Suggestion:** [Gợi ý cách fix]

**Severity:** Critical/Major/Minor

### Issue 2: [Tên issue]

...

## Positive Points (nếu có)

- [Điểm tốt 1]
- [Điểm tốt 2]

## Questions (nếu cần clarification)

1. [Question 1]
2. [Question 2]
```

### 6.2 Severity Guidelines

| Severity | Criteria |
|----------|----------|
| **Critical** | Blocking issue, phải fix trước khi proceed |
| **Major** | Significant issue, strongly recommend fix |
| **Minor** | Nice-to-have improvement |

### 6.3 Khi Nào APPROVE

- Không còn Critical/Major issues
- Minor issues có thể accept với notes
- Proposer đã address tất cả concerns trước đó

## 7. Xử Lý Special Cases

### 7.1 Cần Thêm Thông Tin

Nếu cần Proposer cung cấp thêm context, yêu cầu trong CLAIM:

```markdown
## Request for Additional Information

Để đánh giá đầy đủ, tôi cần Proposer cung cấp:

1. **[Loại thông tin]** - [Lý do cần]
2. **[Document/Code]** - [Mô tả]

Proposer vui lòng upload document và share `doc_id` để tôi có thể review.
```

### 7.2 INTERVENTION từ Arbitrator

Khi nhận INTERVENTION:

1. **KHÔNG CANCEL** argument đang soạn (nếu có)
2. **Nếu đã submit:** Sẽ nhận response yêu cầu wait
3. **Call `aw debate wait`** trên INTERVENTION argument_id
4. **Chờ RULING** từ Arbitrator

### 7.3 Disagreement Kéo Dài

Nếu tranh cãi > 3 vòng trên cùng một điểm:

- **KHÔNG có quyền APPEAL** (chỉ Proposer có quyền)
- **Clearly state position** và reasoning
- **Suggest Proposer APPEAL** nếu cần Arbitrator quyết định

## 8. Xử Lý Timeout

### 8.1 Nhận Timeout Response

```json
{
  "status": "timeout",
  "message": "No response after 300s"
}
```

### 8.2 Hành Động

1. **Thông báo:** "Debate pending, Proposer chưa phản hồi sau 5 phút"
2. **Cung cấp debate_id** để user resume sau
3. **KHÔNG tự động retry**

## 9. Error Handling

### 9.1 ACTION_NOT_ALLOWED

**Hành động:** Không phải lượt mình → Call `aw debate wait`

### 9.2 DEBATE_NOT_FOUND

- Verify debate_id với user
- Có thể debate đã bị xóa hoặc ID sai

### 9.3 Network Error

- Retry tối đa 3 lần
- Thông báo và dừng nếu vẫn fail

## 10. Best Practices

### 10.1 Main Loop - QUAN TRỌNG NHẤT

**KHÔNG BAO GIỜ tự ý kết thúc debate flow:**

```
WHILE TRUE:
    response = aw debate wait(...)
    
    IF response.action == "debate_closed":
        BREAK  ← CHỈ THOÁT KHI ARBITRATOR ĐÓNG DEBATE
    
    # Xử lý response
    analyze_and_submit_claim()
    
    # Quay lại wait
    CONTINUE
```

**Các lỗi phổ biến cần tránh:**
- ❌ Thoát sau khi submit CLAIM mà không wait
- ❌ Thoát khi nhận RULING mà không tiếp tục theo dõi
- ❌ Thoát khi Proposer đã align theo RULING mà chưa verify
- ✅ CHỈ thoát khi nhận `action="debate_closed"`

### 10.2 Objective Review

- Đánh giá khách quan, không bias
- Focus vào technical correctness
- Acknowledge điểm tốt, không chỉ tìm lỗi

### 10.3 Constructive Feedback

- Mỗi criticism đi kèm suggestion
- Giải thích "why" không chỉ "what"
- Prioritize issues theo severity

### 10.4 Respect Process

- Không skip steps để "nhanh hơn"
- Follow debate flow đúng quy trình
- Trust Arbitrator khi cần resolution

### 10.5 Document Everything

- Giữ track của tất cả issues raised
- Reference previous arguments khi cần
- Clear conclusion cho mỗi CLAIM

## 11. Checklist Trước Khi Kết Thúc Session

**QUAN TRỌNG:** Opponent CHỈ kết thúc khi:
- [ ] Nhận được `action="debate_closed"` từ `aw debate wait`

**Nếu chưa close, trước khi tạm dừng session:**
- [ ] Đã submit CLAIM hoặc đang wait?
- [ ] User có debate_id để resume?
- [ ] Outstanding issues đã được document?
- [ ] Có cần yêu cầu Proposer APPEAL không?

## 12. CLI Command Quick Reference

### Debate Commands

| Command | Mô tả | Response chứa |
|---------|-------|---------------|
| `aw debate generate-id` | Tạo UUID mới | `id` |
| `aw debate get-context --debate-id <id> --limit 20` | Lấy context debate | `debate.state`, `motion`, `arguments[]` |
| `aw debate submit --debate-id <id> --role opponent --target-id <arg_id> --content "..." --client-request-id <id>` | Submit CLAIM | `argument_id` |
| `aw debate wait --debate-id <id> --argument-id <arg_id> --role opponent` | Chờ response | `action`, `argument` |

### Docs Commands

| Command | Mô tả | Response chứa |
|---------|-------|---------------|
| `aw docs get <document_id>` | Lấy document content | `content`, `version` |

> **LƯU Ý:** `aw docs get` dùng **positional argument** cho document_id, KHÔNG có flag `--id`.
