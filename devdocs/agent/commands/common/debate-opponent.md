# Debate Opponent Command

> **Role:** Opponent - Bên phản biện và kiểm định chất lượng đề xuất

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
| `aw docs create` | Tạo document (nếu cần share tài liệu) |

**KHÔNG được sử dụng (chỉ dành cho Proposer):**
- `aw debate create`
- `aw debate appeal`
- `aw debate request-completion`

## 2. Join Debate

### 2.1 Lấy Context

```bash
aw debate get-context --debate-id <debate_id> --argument-limit 20
```

### 2.2 Parse Response

```json
{
  "debate": {
    "id": "xxx",
    "title": "...",
    "debate_type": "coding_plan_debate",
    "state": "AWAITING_OPPONENT"
  },
  "motion": {
    "id": "motion-xxx",
    "type": "MOTION",
    "role": "proposer",
    "content": "..."
  },
  "arguments": [...]
}
```

**Thông tin quan trọng:**
- `debate.debate_type` → Dùng để load rule file
- `debate.state` → Xác định lượt của ai
- `motion.content` → Vấn đề gốc cần debate
- `arguments[-1]` → Argument cuối cùng

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

1. **Đọc kỹ MOTION content**
2. **Nếu có doc_id references:**
   ```bash
   aw docs get --id <doc_id>
   ```
3. **Load rule file** theo `debate_type`
4. **Thực hiện additional context gathering** nếu cần:
   - Scan folders liên quan
   - Read source code files
   - Understand codebase structure
5. **Phân tích theo rule** và chuẩn bị CLAIM

### 3.2 Submit CLAIM Đầu Tiên

```bash
aw debate submit \
  --debate-id $DEBATE_ID \
  --role opponent \
  --target-id $MOTION_ID \
  --file ./claim.md \
  --client-request-id $(aw debate generate-id | jq -r '.content[0].data.id')
```

### 3.3 Wait for Response

```bash
aw debate wait \
  --debate-id $DEBATE_ID \
  --argument-id $CLAIM_ID \
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

```bash
aw debate wait \
  --debate-id $DEBATE_ID \
  --argument-id $LAST_ARG_ID \
  --role opponent
```

## 5. Xử Lý Response

### 5.1 Parse Response từ `aw debate wait`

```json
{
  "status": "new_argument",
  "action": "respond",
  "debate_state": "AWAITING_OPPONENT",
  "argument": {
    "id": "xxx",
    "type": "CLAIM",
    "role": "proposer",
    "content": "..."
  }
}
```

### 5.2 Action Mapping

| `action` | Ý nghĩa | Hành động |
|----------|---------|-----------|
| `respond` | Lượt phản biện | Phân tích CLAIM và submit response |
| `wait_for_ruling` | Đang chờ Arbitrator | Call `aw debate wait` tiếp |
| `wait_for_proposer` | Arbitrator RULING, chờ Proposer align | Call `aw debate wait` |
| `debate_closed` | Debate kết thúc | Dừng |

### 5.3 Phản Hồi CLAIM từ Proposer

**Workflow:**

1. **Đọc kỹ CLAIM** của Proposer
2. **So sánh với claims trước** - Proposer đã address đầy đủ chưa?
3. **Load rule file** để đánh giá theo đúng nghiệp vụ
4. **Phân tích:**
   - Proposer đã revise hợp lý? → Acknowledge và tiếp tục review các điểm khác
   - Proposer phản biện lại? → Xem xét logic, có thể accept hoặc counter
   - Vẫn còn issues? → Raise tiếp

5. **Submit response:**

```bash
aw debate submit \
  --debate-id $DEBATE_ID \
  --role opponent \
  --target-id $PROPOSER_ARG_ID \
  --file ./response.md \
  --client-request-id $(aw debate generate-id | jq -r '.content[0].data.id')
```

6. **Wait tiếp:**

```bash
aw debate wait \
  --debate-id $DEBATE_ID \
  --argument-id $NEW_ARG_ID \
  --role opponent
```

### 5.4 Xử Lý RULING từ Arbitrator

Khi `action = "wait_for_proposer"` (sau RULING):

1. **Đọc nội dung RULING** để hiểu direction
2. **KHÔNG cần hành động** - Proposer sẽ align trước
3. **Wait** cho Proposer submit response đã align
4. **Sau khi nhận Proposer response:** Verify xem Proposer đã align đúng ruling chưa

### 5.5 Xử Lý APPEAL từ Proposer

Khi nhận được argument type `APPEAL`:

1. **Đọc nội dung APPEAL** để hiểu context
2. **Thông báo:** "Proposer đã yêu cầu Arbitrator phán xử"
3. **Call `aw debate wait`** với APPEAL argument_id
4. **Chờ RULING** từ Arbitrator

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

Nếu cần Proposer cung cấp thêm context:

```markdown
## Request for Additional Information

Để đánh giá đầy đủ, tôi cần:

1. **[Loại thông tin]** - [Lý do cần]
2. **[Document/Code]** - [Mô tả]

Vui lòng sử dụng `aw docs create` để upload và share `doc_id`.
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

```json
{
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "current_state": "AWAITING_PROPOSER",
    "allowed_roles": ["proposer"]
  }
}
```

**Hành động:** Không phải lượt mình → Call `aw debate wait`

### 9.2 DEBATE_NOT_FOUND

- Verify debate_id với user
- Có thể debate đã bị xóa hoặc ID sai

### 9.3 Network Error

- Retry tối đa 3 lần
- Thông báo và dừng nếu vẫn fail

## 10. Best Practices

### 10.1 Objective Review

- Đánh giá khách quan, không bias
- Focus vào technical correctness
- Acknowledge điểm tốt, không chỉ tìm lỗi

### 10.2 Constructive Feedback

- Mỗi criticism đi kèm suggestion
- Giải thích "why" không chỉ "what"
- Prioritize issues theo severity

### 10.3 Respect Process

- Không skip steps để "nhanh hơn"
- Follow debate flow đúng quy trình
- Trust Arbitrator khi cần resolution

### 10.4 Document Everything

- Giữ track của tất cả issues raised
- Reference previous arguments khi cần
- Clear conclusion cho mỗi CLAIM

## 11. Checklist Trước Khi Kết Thúc Session

- [ ] Đã submit CLAIM hoặc đang wait?
- [ ] User có debate_id để resume?
- [ ] Outstanding issues đã được document?
- [ ] Có cần yêu cầu Proposer APPEAL không?
