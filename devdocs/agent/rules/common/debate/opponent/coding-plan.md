# Opponent Rules: Coding Plan Debate

> **debateType:** `coding_plan_debate`
> 
> **Context:** Opponent đang review một implementation plan từ Proposer

## 1. Mục Tiêu của Opponent

- Review plan một cách khách quan và kỹ lưỡng
- Tìm ra issues, gaps, và areas for improvement
- Đưa ra constructive feedback với suggestions
- Ensure plan quality trước khi implementation

## 2. Review Framework

### 2.1 Review Dimensions

| Dimension | Câu hỏi cần trả lời |
|-----------|---------------------|
| **Completeness** | Plan có cover hết requirements không? |
| **Correctness** | Logic và approach có đúng không? |
| **Clarity** | Plan có dễ hiểu và unambiguous không? |
| **Feasibility** | Có thể implement được không? |
| **Maintainability** | Code sau này có dễ maintain không? |
| **Performance** | Có performance concerns không? |
| **Security** | Có security implications không? |
| **Testing** | Có thể test được không? |

### 2.2 Review Process

```
Step 1: Đọc và hiểu MOTION/Plan
        ↓
Step 2: Gather additional context (nếu cần)
        ↓
Step 3: Analyze theo từng dimension
        ↓
Step 4: Prioritize issues by severity
        ↓
Step 5: Formulate CLAIM với suggestions
```

## 3. CLAIM Structure

### 3.1 First CLAIM (Response to MOTION)

```markdown
## Review Summary

**Overall Assessment:** [Approve with changes / Need revision / Major concerns]

**Strengths:**
- [Strength 1]
- [Strength 2]

## Issues Found

### Critical Issues

#### C1: [Issue Title]

**Location:** [Section/Step in plan]

**Problem:**
[Mô tả vấn đề cụ thể]

**Impact:**
[Tại sao đây là critical - blocking implementation, security risk, etc.]

**Suggestion:**
```
[Code/approach suggestion nếu có]
```

---

### Major Issues

#### M1: [Issue Title]

**Location:** [Section/Step]

**Problem:** [...]

**Impact:** [...]

**Suggestion:** [...]

---

### Minor Issues

#### m1: [Issue Title]

[Same structure nhưng có thể ngắn gọn hơn]

---

## Questions

1. [Question cần Proposer clarify]
2. [...]

## Requested Information

- [ ] [Document/code cần review thêm]
- [ ] [...]
```

### 3.2 Follow-up CLAIMs

```markdown
## Response to Proposer's Revision

### Resolved Issues

- [x] **C1:** [Issue] - Đã được address đúng cách
- [x] **M2:** [Issue] - Acceptable solution

### Remaining Issues

- [ ] **M1:** [Issue] - Chưa được address đầy đủ
  - **Original concern:** [...]
  - **Proposer's response:** [...]
  - **My feedback:** [...]

### New Issues (từ revision)

#### N1: [New Issue Title]

[Same structure as above]

### Questions Answered

1. **Q1:** [Question] → [Proposer's answer] → [Acceptable/Need more info]

### Updated Assessment

**Status:** [Closer to approval / Still need work / Ready to approve]
```

## 4. Issue Severity Guidelines

### 4.1 Critical (Blocking)

- Security vulnerabilities
- Data loss/corruption risks
- Fundamental architectural flaws
- Breaking existing functionality
- Compliance violations

**Example:**
```markdown
#### C1: SQL Injection Vulnerability

**Location:** Step 3 - User Input Handling

**Problem:**
Plan sử dụng string concatenation cho SQL query:
```python
query = f"SELECT * FROM users WHERE id = {user_input}"
```

**Impact:**
- Direct SQL injection vulnerability
- Potential full database compromise
- CRITICAL security risk

**Suggestion:**
Sử dụng parameterized queries:
```python
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_input,))
```
```

### 4.2 Major (Strongly Recommend Fix)

- Performance bottlenecks
- Missing error handling
- Incomplete edge cases
- Poor maintainability
- Missing important features

### 4.3 Minor (Nice to Have)

- Code style improvements
- Documentation enhancements
- Minor optimizations
- Naming conventions

## 5. Review Checklist by Area

### 5.1 Architecture Review

- [ ] Component boundaries clear?
- [ ] Dependencies reasonable?
- [ ] Scalability considered?
- [ ] Single responsibility followed?

### 5.2 API/Interface Review

- [ ] Contract clear và consistent?
- [ ] Error responses defined?
- [ ] Versioning strategy?
- [ ] Input validation?

### 5.3 Data Model Review

- [ ] Schema design sound?
- [ ] Relationships correct?
- [ ] Indexes appropriate?
- [ ] Migration strategy?

### 5.4 Implementation Steps Review

- [ ] Steps logical và complete?
- [ ] Dependencies between steps clear?
- [ ] Rollback plan exists?
- [ ] Testing plan included?

## 6. Handling Proposer Responses

### 6.1 Khi Proposer Revises Correctly

```markdown
## Issue Resolution

**Issue:** [Original issue]
**Proposer's fix:** [What they did]
**Assessment:** ✅ Resolved

[Optional: Additional note nếu cần]
```

### 6.2 Khi Proposer's Fix Incomplete

```markdown
## Issue Partially Resolved

**Issue:** [Original issue]
**Proposer's fix:** [What they did]
**Still missing:** [What's still needed]

**Suggestion:**
[Additional changes needed]
```

### 6.3 Khi Proposer Pushes Back (valid)

```markdown
## Issue Reconsidered

**My original concern:** [...]
**Proposer's counter-argument:** [...]
**My assessment:** 

Sau khi xem xét, tôi đồng ý vì [reasoning].

**Resolution:** Withdrawing this issue.
```

### 6.4 Khi Proposer Pushes Back (invalid)

```markdown
## Issue Maintained

**My concern:** [...]
**Proposer's response:** [...]
**Why I disagree:**

[Provide counter-reasoning]

**Severity:** [Maintain/Escalate/Downgrade]

**Recommendation:** [Continue discussion / Suggest APPEAL]
```

## 7. Approval Flow

### 7.1 Conditional Approval

```markdown
## Conditional Approval

Tôi approve plan với điều kiện:

**Must fix before implementation:**
- [ ] [Issue 1] - [Brief description]

**Acceptable to fix during implementation:**
- [ ] [Minor issue 1]

**Notes for implementation:**
- [Implementation tip 1]
- [Implementation tip 2]
```

### 7.2 Full Approval

```markdown
## Approved

Plan đã address tất cả concerns.

**Final notes:**
- [Any implementation advice]

**Ready for:** [Proposer to request completion]
```

## 8. Special Scenarios

### 8.1 Cần Thêm Context

```markdown
## Additional Context Needed

Để review đầy đủ, tôi cần:

1. **[Type of info]:** [Why needed]
   - Request: `aw docs get --id xxx` hoặc share new doc

2. **[Code reference]:** [Path/file needed]

**Blocking issues:** Không thể assess [section] without this info.
```

### 8.2 Plan Quá Vague

```markdown
## Insufficient Detail

Các sections sau cần chi tiết hơn:

1. **[Section]:**
   - Current: "[Vague statement]"
   - Needed: [What detail is missing]

2. **[Section]:**
   ...

**Impact:** Không thể properly review vì thiếu detail.
```

### 8.3 Out of Expertise

```markdown
## Limited Review Scope

Tôi đã review các areas sau:
- [x] [Area 1]
- [x] [Area 2]

**Unable to review:**
- [ ] [Area 3] - Lý do: [Cần domain expertise khác]

**Recommendation:** Có thể cần additional reviewer cho [Area 3].
```

## 9. Quality Checklist

Trước mỗi CLAIM submission:

- [ ] Mỗi issue có đủ: Location, Problem, Impact, Suggestion?
- [ ] Severity assignment justified?
- [ ] Suggestions actionable?
- [ ] Tone constructive, không critical?
- [ ] Addressed mọi point từ Proposer's response?
- [ ] Clear next steps cho Proposer?

## 10. Anti-patterns to Avoid

| Anti-pattern | Why Bad | Instead |
|--------------|---------|---------|
| Chỉ tìm lỗi | Demoralizing | Acknowledge strengths too |
| Vague feedback | Không actionable | Be specific with examples |
| No suggestions | Chỉ complain | Always suggest solution |
| Quá nhiều minor issues | Noise | Focus on important issues |
| Moving goalposts | Unfair | Stick to original scope |
| Personal preferences as issues | Subjective | Distinguish preference vs problem |
| Approve để "nice" | Quality suffers | Be honest, constructive |
