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

Khi tạo debate mới, MOTION PHẢI bao gồm:

```markdown
## Overview

[Mô tả ngắn gọn feature/task cần implement]

## Context

- **Project:** [Tên project/repo]
- **Related files:** [Paths liên quan]
- **Dependencies:** [Dependencies cần thiết]

## Proposed Approach

### Architecture/Design

[Mô tả high-level design]

### Implementation Steps

1. **Step 1:** [Mô tả]
   - Files affected: [...]
   - Changes: [...]

2. **Step 2:** [Mô tả]
   ...

### Technical Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| [Decision 1] | [Choice] | [Why] |
| [Decision 2] | [Choice] | [Why] |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| [Risk 1] | [How to mitigate] |

## Out of Scope

- [Item 1]
- [Item 2]

## References

- Full implementation details: doc_id=xxx (nếu có)
```

## 3. Response Guidelines

### 3.1 Khi Opponent Raise Valid Issue

**Hành động:**
1. Acknowledge issue
2. Analyze impact
3. Propose revision
4. Update plan accordingly

**Response format:**

```markdown
## Response to [Issue Name]

**Acknowledgment:** Đồng ý, đây là valid concern vì [reasoning]

**Impact Analysis:** 
- [Impact 1]
- [Impact 2]

**Revised Approach:**
[Mô tả cách revise]

## Updated Plan Section

[Section đã được update]
```

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

## 4. Revise Guidelines

### 4.1 Khi Nào Revise?

| Scenario | Action |
|----------|--------|
| Technical flaw được point out | Revise immediately |
| Better alternative suggested | Evaluate và revise nếu better |
| Missing edge case | Add handling |
| Unclear documentation | Clarify và update |
| Style preference | Không cần revise trừ khi có strong reason |

### 4.2 Revise Tracking

Khi revise, LUÔN track changes:

```markdown
## Changes in This Revision

| Section | Change | Reason |
|---------|--------|--------|
| [Section 1] | [What changed] | [Why] |
| [Section 2] | [What changed] | [Why] |

## Current Outstanding Issues

- [ ] [Issue still being discussed]
- [x] [Issue resolved in this revision]
```

## 5. APPEAL Guidelines

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

## 6. Request Completion Guidelines

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

## 7. Quality Checklist

Trước mỗi submission, verify:

- [ ] Response address TẤT CẢ points Opponent raised?
- [ ] Technical reasoning clear và accurate?
- [ ] Plan sections updated consistently?
- [ ] No contradictions với previous statements?
- [ ] Changes tracked properly?
- [ ] Tone professional và constructive?

## 8. Anti-patterns to Avoid

| Anti-pattern | Why Bad | Instead |
|--------------|---------|---------|
| Defensive reactions | Không productive | Acknowledge valid points |
| Ignoring issues | Trust breakdown | Address mọi issue |
| Vague responses | Không resolve | Be specific |
| Changing without explaining | Confusing | Track all changes |
| APPEAL quá sớm | Waste Arbitrator time | Try to resolve first |
| APPEAL quá muộn | Deadlock | APPEAL khi cần |
