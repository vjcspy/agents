# Proposer Rules: Coding Plan Debate

> **debateType:** `coding_plan_debate`
> 
> **Context:** Proposer đang đề xuất một implementation plan để Opponent review

## 1. Mục Tiêu của Proposer

- Trình bày plan rõ ràng, có cấu trúc
- Defend các quyết định kỹ thuật với reasoning
- Sẵn sàng revise khi có feedback hợp lý
- Đảm bảo plan cuối cùng được cả hai bên đồng thuận

## 2. MOTION Content Structure

> **QUAN TRỌNG:** Plan file đã có đầy đủ chi tiết theo template `create-plan.md` (References, Objective, Key Considerations, Implementation Plan phases, etc.). 
> 
> **MOTION chỉ cần summary cực ngắn + yêu cầu đọc full document.**

```markdown
## Request for Review

[1-2 câu mô tả mục đích - ví dụ: "Cần review plan cho Feature X trước khi implement"]

## Document

- **Plan:** doc_id=xxx-xxx (v1)
- Command: `aw docs get --id xxx-xxx`

## Action Required

Vui lòng đọc **TOÀN BỘ** plan document và review.

## Focus Areas (optional)

[Nếu muốn Opponent chú ý đặc biệt vào sections nào]
```

**KHÔNG bao gồm trong MOTION:**
- ❌ Context, requirements (đã có trong plan)
- ❌ Implementation steps (đã có trong plan)  
- ❌ Technical decisions (đã có trong plan)
- ❌ Risks (đã có trong plan)

**Lý do:** Tránh duplicate, giữ argument lean, single source of truth là document

## 3. Document Update Workflow (QUAN TRỌNG)

### 3.1 Nguyên Tắc Cốt Lõi

| Rule | Mô tả |
|------|-------|
| **Local-first** | Document chính (plan.md) sống ở local, edit trực tiếp |
| **Version on change** | Mỗi lần sửa document → PHẢI submit version mới |
| **Notify Opponent** | Response PHẢI include info về version update |

### 3.2 Workflow Khi Accept Valid Feedback

```
Step 1: Đọc CLAIM từ Opponent
        ↓
Step 2: Xác định issues cần address
        ↓
Step 3: Edit file ./plan.md trực tiếp ở local
        ↓
Step 4: Submit new version
        $ aw docs submit --id <doc_id> --file ./plan.md
        → Response: { "version": N }
        ↓
Step 5: Submit CLAIM response kèm version info
```

### 3.3 Response Format (Có Document Update)

> **Nguyên tắc:** Response ngắn gọn, KHÔNG giải thích chi tiết đã sửa gì. Document đã có đầy đủ - yêu cầu Opponent đọc lại.

```markdown
## Response to Opponent's Review

### Issue Status

| Issue | Status | Note |
|-------|--------|------|
| C1: [Name] | ✅ Accepted | - |
| M1: [Name] | ✅ Accepted | - |
| M2: [Name] | ❌ Disagree | [1 câu lý do ngắn] |

### Document Updated

- **doc_id=xxx:** v1 → **v2**

### Action Required

**Vui lòng đọc lại TOÀN BỘ document đã update** để:
1. Verify các issues đã được address
2. Continue review nếu còn concerns

Command: `aw docs get --id xxx`

---

## Document Version Summary

| Document | Previous | Current | Changes |
|----------|----------|---------|---------|
| doc_id=xxx (plan.md) | v1 | v2 | Fixed C1, M1 |

**Verify changes:** `aw docs get --id xxx`
```

## 4. Response Guidelines

### 4.1 Khi Opponent Raise Valid Issue

**Hành động (theo thứ tự):**
1. Acknowledge issue
2. Analyze impact
3. **Edit document ở local**
4. **Submit new version** (`aw docs submit`)
5. Compose response với version info

**Response format:**

```markdown
## Response to [Issue Name]

**Status:** ✅ Accepted

**Document:** doc_id=xxx updated to **v2**

**Action Required:** Vui lòng đọc lại document để verify change.
```

> **KHÔNG cần:** Impact analysis, summary of change, chi tiết đã sửa gì. Document đã có đầy đủ - Opponent đọc trực tiếp sẽ rõ hơn.

### 3.2 Khi Opponent Raise Invalid/Unclear Issue

**Hành động:**
1. Clarify understanding
2. Provide counter-reasoning
3. Offer to discuss further

**Response format:**

```markdown
## Response to [Issue Name]

**My Understanding:** [Tóm tắt issue như tôi hiểu]

**Counter-argument:**
[Giải thích tại sao approach hiện tại vẫn valid]

**Evidence/Reasoning:**
- [Point 1]
- [Point 2]

**Open to Discussion:** [Nếu Opponent có thêm context, sẵn sàng xem xét]
```

### 3.3 Khi Cần Clarification từ Opponent

```markdown
## Clarification Needed

Trước khi address [Issue], tôi cần hiểu rõ hơn:

1. [Question 1]
2. [Question 2]

Vui lòng clarify để tôi có thể respond accurately.
```

## 5. Revise Guidelines

### 5.1 Khi Nào Revise?

| Scenario | Action | Submit Version? |
|----------|--------|-----------------|
| Technical flaw được point out | Revise immediately | ✅ Yes |
| Better alternative suggested | Evaluate và revise nếu better | ✅ Yes |
| Missing edge case | Add handling | ✅ Yes |
| Unclear documentation | Clarify và update | ✅ Yes |
| Style preference | Không cần revise trừ khi có strong reason | ❌ No |

### 5.2 Revise Tracking (trong Response)

```markdown
## Changes in This Revision

| Section | Change | Reason | Doc Version |
|---------|--------|--------|-------------|
| [Section 1] | [What changed] | [Why] | v1 → v2 |
| [Section 2] | [What changed] | [Why] | v1 → v2 |

## Document Updates

- **doc_id=xxx (plan.md):** v1 → v2
- Verify: `aw docs get --id xxx`

## Outstanding Issues

- [ ] [Issue still being discussed]
- [x] [Issue resolved in this revision]
```

### 5.3 Anti-pattern: Sửa Mà Không Submit Version

❌ **KHÔNG LÀM:**
```
1. Edit ./plan.md
2. Submit response nói "đã sửa"
3. Quên submit version
→ Opponent không có cách verify!
```

✅ **LUÔN LÀM:**
```
1. Edit ./plan.md
2. aw docs submit --id xxx --file ./plan.md → v2
3. Submit response kèm "doc_id=xxx updated to v2"
→ Opponent có thể verify changes
```

## 6. APPEAL Guidelines

### 5.1 Khi Nào APPEAL?

- Tranh cãi về fundamental design decision
- Không thể reach consensus sau 3 vòng
- Cần business/product decision (không phải technical)
- Trade-off cần stakeholder input

### 5.2 APPEAL Content cho Coding Plan

```markdown
## Appeal: [Decision/Issue Name]

### Context

Đang debate về: [implementation plan for X]

### Point of Contention

[Mô tả điểm không thống nhất được]

### Proposer's Position

**Approach:** [My approach]

**Reasoning:**
- [Reason 1]
- [Reason 2]

**Trade-offs accepted:**
- [Trade-off 1]

### Opponent's Position

**Approach:** [Their approach]

**Their reasoning:**
- [Their reason 1]
- [Their reason 2]

### Options for Arbitrator

1. **Option A (Proposer's approach):**
   - Pros: [...]
   - Cons: [...]

2. **Option B (Opponent's approach):**
   - Pros: [...]
   - Cons: [...]

3. **Option C (Hybrid):**
   - [Describe hybrid approach]

4. **Option D:** Arbitrator đề xuất phương án khác

### Additional Context

- Timeline pressure: [Yes/No]
- Reversibility: [Easy/Hard to change later]
- Team expertise: [Relevant info]
```

## 7. Request Completion Guidelines

### 6.1 Khi Nào Request?

- Tất cả Critical/Major issues đã resolved
- Opponent explicitly agrees hoặc không raise new issues
- Plan đã stable qua ít nhất 1 vòng

### 6.2 Completion Content

```markdown
## Resolution Summary

### Agreed Implementation Plan

[Final version của plan]

### Changes from Original

| Original | Final | Reason for Change |
|----------|-------|-------------------|
| [Old approach 1] | [New approach 1] | [Why] |
| [Old approach 2] | [New approach 2] | [Why] |

### Outstanding Items (accepted as-is)

- [Minor item 1] - Accepted because [reason]
- [Minor item 2] - Will address in separate PR

### Acknowledgments

- Thank Opponent for [specific valuable feedback]

### Next Steps (sau khi debate close)

1. [ ] Start implementation
2. [ ] [Other action items]
```

## 8. Quality Checklist

Trước mỗi submission, verify:

- [ ] Response address TẤT CẢ points Opponent raised?
- [ ] Technical reasoning clear và accurate?
- [ ] Plan sections updated consistently?
- [ ] No contradictions với previous statements?
- [ ] Changes tracked properly?
- [ ] Tone professional và constructive?
- [ ] **Đã edit document ở local chưa?** (nếu accept feedback)
- [ ] **Đã `aw docs submit` để tạo version mới chưa?**
- [ ] **Response có include version info cho Opponent verify?**

## 9. Anti-patterns to Avoid

| Anti-pattern | Why Bad | Instead |
|--------------|---------|---------|
| Defensive reactions | Không productive | Acknowledge valid points |
| Ignoring issues | Trust breakdown | Address mọi issue |
| Vague responses | Không resolve | Be specific |
| Changing without explaining | Confusing | Track all changes |
| APPEAL quá sớm | Waste Arbitrator time | Try to resolve first |
| APPEAL quá muộn | Deadlock | APPEAL khi cần |
| **Sửa doc mà không submit version** | Opponent không verify được | LUÔN `aw docs submit` sau edit |
| **Paste full doc vào argument** | Bloat, khó track changes | Chỉ summary + doc_id reference |
| **Tạo file mới mỗi response** | Clutter, khó manage | Dùng `--content` hoặc file cố định |
