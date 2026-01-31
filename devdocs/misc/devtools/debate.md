# Debate

Ý tưởng của tôi là xây dựng 1 ecosytem để cung cấp các rules, tools, applications và environment để cho các AI agents có thể tranh luận xung quanh các topic.
Dưới đây là mô tả về nghiệp vụ cũng như hệ thống

## 1. Các bên tham gia

- `Proposer` (AI Agent) – Bên Đề Xuất
Đóng vai trò là thực thể khởi xướng và duy trì định hướng của cuộc tranh luận.

Khởi tạo (MOTION): Có quyền đưa ra chủ đề hoặc vấn đề cần thảo luận ban đầu.

Tiếp nhận & Điều chỉnh (REVISE): Có quyền chấp nhận các CLAIM từ Opponent để cập nhật, chỉnh sửa (revise) lại nội dung đề xuất ban đầu cho phù hợp hơn.

Thỉnh cầu (APPEAL): Khi xảy ra xung đột không thể tự giải quyết với Opponent, Proposer có quyền gửi một bản thỉnh cầu (APPEAL) tới Arbitrator để yêu cầu một quyết định định hướng.

- `Opponent` (AI Agent) – Bên Phản Biện
Đóng vai trò là thực thể kiểm định và đưa ra góc nhìn đối lập.

Phản biện (CLAIM): Có quyền đưa ra các lập luận, bằng chứng hoặc lý lẽ để phản bác, đóng góp ý kiến vào vấn đề mà Proposer đưa ra.

Mục tiêu: Tìm ra các lỗ hổng hoặc điểm chưa tối ưu trong MOTION hoặc các bản REVISE của Proposer.

- `Arbitrator` (User hoặc AI Agent) – Trọng Tài/Người Phân Xử
Đóng vai trò là thực thể có quyền quyết định cao nhất, đảm bảo cuộc tranh luận không bị bế tắc.

Tiếp nhận xung đột: Chỉ tham gia xử lý khi có một record APPEAL được khởi tạo bởi Proposer.

Ra phán quyết (RULING): Có nhiệm vụ xem xét các CLAIM hiện tại của cả hai bên và đưa ra một bản phán quyết (RULING). Record này sẽ đóng vai trò là "kim chỉ nam" bắt buộc để các bên phải tuân thủ và tiếp tục tranh luận theo hướng đó.

### 1.1 Mô tả quy trình debate

**1.1.1** Step1 `Proposer`:
Sử dụng `Proposer Command` để hiểu được cách làm việc, xác định kiểu `debateType` rồi sau đó xác định xem trạng thái hiện tai của debate.
Lúc này sẽ có 2 trường hợp:

- Tham gia lại vào debate đã open trước đó
- Tạo mới một debate conversation

**Trường hợp user gửi một `debate_id` đã tồn tại:**
Sẽ gọi command `aw debate get-context` để lấy thông tin debate cũ đọc và hiểu context, phân tích và có thể cần thực hiện thêm các addition steps như scan folder, read source code, nói chung là làm toàn bộ nhưng thứ mà cho là cần thiết để lấy được lại context cũ, cuối cùng xem role của argument cuối cùng là gì?
Nếu role là của `Proposer` chính là role của mình thì sẽ gọi `aw debate wait` để chờ kết quả
Nếu role khác `Proposer` tức là đã có phản hồi thì xem phản hồi đó là gì để đánh giá xem có chuẩn không, hoặc nếu là của `Arbitrator` thì follow theo option mà `Arbitrator` đưa ra. Sau đó thực hiện tiếp các công việc cần thiết rồi gọi `aw debate submit` lấy được `argument_id` rồi gọi `aw debate wait` trên `argument_id` để chờ phản hồi

**Trường hợp user yêu cầu create new debate:**
Nếu user yêu cầu tạo debate mới, sử dụng `aw debate generate-id` và `aw debate create`.

Sau khi `aw debate create` trả về response thành công sẽ có `debate_id`, `argument_id`, thì sẽ gọi `aw debate wait` dùng 2 tham số đó và chờ response

**1.1.2** Step2 `Opponent`:
Sử dụng `Opponent Command` để hiểu được cách làm việc, user sẽ cung cấp `debate_id`. Gọi command `aw debate get-context` để lấy thông tin debate cũ đọc và hiểu context, phân tích và có thể cần thực hiện thêm các addition steps như scan folder, read source code, nói chung là làm toàn bộ nhưng thứ mà cho là cần thiết để lấy được lại context cũ, cuối cùng xem role của argument cuối cùng là gì?
Nếu role là `Proposer` thì do chưa có `argument_id` tại thời điểm này nên sẽ xem `type` của `argument` nếu nó là `MOTION` tức là 1 vấn đề mới thì follow theo các rules đã được nạp trước đó để tiền hành đánh giá và sau khi có kết quả thì gọi `aw debate submit`. Response sẽ trả về là `argument_id` tức là thành công và đó chính là `argument` cần được truyền vào command `aw debate wait` cùng với `debate_id` để chờ phản hồi.

**1.1.3** Step3 Lặp lại quá trình debate:
2 bên `Proposer` và `Opponent` sẽ tương tác với nhau. Trong quá trình này sẽ follow theo `rules` đã được nạp từ trước. Các bên có thể sử dụng các công cụ cho phép để yêu cầu thêm thông tin ví dụ như Opponent yêu cầu Proposer submit các document cần thiết và gửi cho Opponent id của document để verify. Nếu `Proposer` thấy các CLAIM của `Opponent` là hợp lý thì sẽ chỉnh sửa, nếu thấy không hợp lý thì phản hồi lại, trong trường hợp KHÔNG thể thống nhất thì `Proposer` có quyền raise `APPEAL` cho `Arbitrator` phán quyết.
`Proposer` sẽ gọi command `aw debate appeal` với tham số `--debate-id`, `--target-id` là `argument_id` trước đó mà cần phán quyết. Cần lưu ý cách đặt câu hỏi chỗ này. Phải nói đủ context, đưa ra các option (luôn phải có 1 option cuối cùng là user sẽ chọn phương án khác). Response từ CLI sẽ trả về new `argument_id` cho bản ghi argument đã được tạo. `Proposer` sau đó sẽ lại call `aw debate wait`.
`Opponent` trước đó đã called `aw debate wait` và nhận được phản hồi tuy nhiên argument có type là `APPEAL` thì sẽ chỉ thông báo cho user là phía `Proposer` đang yêu cầu phán xử, và sẽ call tiếp `aw debate wait` với new `argument_id` chờ `Arbitrator` phán quyết.

**1.1.4** Step4 `Arbitrator` phán quyết:
`Arbitrator` sẽ sử dụng debate-web application (sẽ được build để monitoring conversation) để submit RULING, cái này sẽ call xuống debate-server để tạo bản ghi mới trong database.
Khi có bản ghi mới thì `Proposer` và `Opponent` đều sẽ nhận được response. Tuy nhiên lúc đó mỗi bên sẽ hành động khác nhau.
`Proposer` hành động để align theo phán quyết. Sau đó gọi `aw debate submit` rồi gọi `aw debate wait`.
`Opponent` chỉ đơn giản là đọc hiểu ngữ cảnh, lấy được `argument_id` của phán quyết này rồi gọi luôn `aw debate wait` để chờ `Proposer` align theo phán quyết.

**1.1.5** Step5 2 bên đều nhất trí hết các điểm:
Lúc đó `Proposer` sẽ gọi `aw debate request-completion` để tạo bản ghi `RESOLUTION`. Lúc này cả 2 `Proposer` và `Opponent` đều sẽ cần `aw debate wait` trên argument_id này, `Arbitrator` sẽ hành động trên web để tạo bản ghi `RULING` để complete → chuyển state của debate sang `CLOSED` hoặc đưa ra 1 hướng khác. Nếu đưa ra hướng khác thì quay lại step 4 còn nếu close thì 2 bên `Proposer` và `Opponent` sẽ dừng.

**1.1.6** Lưu ý về INTERVENTION:

Vào bất cứ thời điểm nào `Arbitrator` cũng có thể can thiệp bằng cách submit 1 bản ghi `INTERVENTION`.

**QUAN TRỌNG - INTERVENTION Semantics:**
- INTERVENTION **không hủy** argument mà AI agent đang soạn
- INTERVENTION được xử lý như một argument mới "đứng trước" vòng tiếp theo
- Nếu 1 AI agent đang soạn argument, agent đó vẫn submit được, nhưng sau khi submit xong sẽ nhận được response yêu cầu `aw debate wait` trên `argument_id` của bản ghi `INTERVENTION`

**Flow:**
1. `debate-web` submit `INTERVENTION` → state chuyển sang `INTERVENTION_PENDING`
2. Cả 2 AI agents nhận response với `action: "wait_for_ruling"`
3. `Arbitrator` submit tiếp bản ghi `RULING` → quay về Step4

### 1.2 Document Sharing Mechanism (Cơ chế chia sẻ tài liệu)

**QUAN TRỌNG:** Argument content chỉ chứa **summary ngắn + references (doc_id)**, không paste nội dung dài. Sử dụng CLI tool `aw docs` để chia sẻ tài liệu đầy đủ.

**Nguyên tắc:**

1. **Tài liệu dài phải qua docs CLI tool**: Sử dụng `aw docs` để submit và get document
2. **Argument chỉ chứa summary + doc_id**: Có thể kèm snippet cực ngắn nếu cần, nhưng không paste toàn bộ nội dung
3. **Giới hạn content size**: Server enforce max content length (ví dụ: 10KB) để tránh abuse
4. **Mỗi bên duy trì file ở local**: Proposer/Opponent làm việc trực tiếp trên file local của mình, khi cần bên kia review thì submit lên để có version tracking
5. **Lấy tài liệu qua ID**: Bất kỳ bên nào (Proposer/Opponent) có thể get document qua ID ở bất kỳ thời điểm nào

**Các trường hợp sử dụng:**

| Trường hợp | Hành động |
|------------|-----------|
| Proposer tạo debate với tài liệu | Tạo file qua `aw docs create`, gửi `doc_id` kèm trong MOTION content |
| Opponent cần thêm context | Gửi CLAIM yêu cầu Proposer submit tài liệu bổ sung và cung cấp `doc_id` |
| Update tài liệu sau khi chỉnh sửa | Submit version mới qua `aw docs submit <doc_id>`, gửi `doc_id` cho bên kia |

> **Note:** `aw docs create` = tạo document mới (version 1), `aw docs submit` = tạo version mới cho document đã tồn tại.

**Cấu hình Tools cho Debate:**

Cần có cơ chế cấu hình để AI agents biết các CLI tools được phép sử dụng trong debate. Các tools này sẽ được mô tả trong Command/Skill của từng role (Proposer/Opponent) theo `debateType`.

## 2. Hệ thống cần xây dựng

### 2.0 Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECTURE OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐         HTTP/REST         ┌──────────────────────┐       │
│   │  CLI Python  │ ◄───────────────────────► │   debate-server      │       │
│   │  (aw debate) │                           │   (Node.js)          │       │
│   └──────────────┘                           │                      │       │
│         ▲                                    │  ┌────────────────┐  │       │
│         │                                    │  │ better-sqlite3 │  │       │
│   AI Agents call                             │  │    (SQLite)    │  │       │
│   CLI commands                               │  └────────────────┘  │       │
│                                              │         │            │       │
│                                              │  ┌──────▼─────────┐  │       │
│   ┌──────────────┐      WebSocket            │  │  ~/.aweave/    │  │       │
│   │  debate-web  │ ◄───────────────────────► │  │  debate.db     │  │       │
│   │  (Next.js)   │                           │  └────────────────┘  │       │
│   └──────────────┘                           └──────────────────────┘       │
│         ▲                                                                   │
│         │                                                                   │
│   Human (Arbitrator)                                                        │
│   monitors & submits                                                        │
│   RULING/INTERVENTION                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Quyết định kỹ thuật:**

| Component | Technology | Lý do |
|-----------|------------|-------|
| Database | SQLite | Lightweight, file-based, không cần server |
| DB Library | `better-sqlite3` | Sync API, nhanh, locking tốt cho Node.js |
| CLI | Python | Consistency với `aw docs` CLI đã có |
| Server | Node.js | WebSocket support tốt, dễ integrate với Next.js |
| Web | Next.js + shadcn | Modern, fast development |

**Data Flow:**
- CLI **KHÔNG** access database trực tiếp
- Mọi data access đều qua `debate-server` (HTTP REST API)
- `debate-server` là single source of truth cho state machine và locking

### 2.1 State Machine

#### 2.1.1 States

| State | Mô tả | Ai đang chờ? |
|-------|-------|--------------|
| `AWAITING_OPPONENT` | Chờ Opponent phản hồi | Proposer waiting |
| `AWAITING_PROPOSER` | Chờ Proposer phản hồi | Opponent waiting |
| `AWAITING_ARBITRATOR` | Chờ Arbitrator phán xử (APPEAL/RESOLUTION) | **Cả 2 waiting** |
| `INTERVENTION_PENDING` | Arbitrator đã INTERVENTION, chờ RULING | **Cả 2 waiting** |
| `CLOSED` | Debate kết thúc | Không ai chờ |

#### 2.1.2 Transitions

| From State | Action | By | To State |
|------------|--------|-----|----------|
| - | `createDebate(MOTION)` | Proposer | `AWAITING_OPPONENT` |
| `AWAITING_OPPONENT` | `submitArgument(CLAIM)` | Opponent | `AWAITING_PROPOSER` |
| `AWAITING_OPPONENT` | `submitIntervention()` | Arbitrator | `INTERVENTION_PENDING` |
| `AWAITING_PROPOSER` | `submitArgument(CLAIM)` | Proposer | `AWAITING_OPPONENT` |
| `AWAITING_PROPOSER` | `submitAppeal()` | Proposer | `AWAITING_ARBITRATOR` |
| `AWAITING_PROPOSER` | `requestCompletion()` | Proposer | `AWAITING_ARBITRATOR` |
| `AWAITING_PROPOSER` | `submitIntervention()` | Arbitrator | `INTERVENTION_PENDING` |
| `AWAITING_ARBITRATOR` | `submitRuling()` | Arbitrator | `AWAITING_PROPOSER` |
| `AWAITING_ARBITRATOR` | `submitRuling(close=true)` | Arbitrator | `CLOSED` |
| `INTERVENTION_PENDING` | `submitRuling()` | Arbitrator | `AWAITING_PROPOSER` |
| `INTERVENTION_PENDING` | `submitRuling(close=true)` | Arbitrator | `CLOSED` |

#### 2.1.3 Argument Types

| Type | Ai tạo | Mô tả |
|------|--------|-------|
| `MOTION` | Proposer | Khởi tạo vấn đề ban đầu |
| `CLAIM` | Proposer/Opponent | Lập luận, phản biện qua lại |
| `APPEAL` | Proposer | Yêu cầu Arbitrator phán xử |
| `RULING` | Arbitrator | Phán quyết |
| `INTERVENTION` | Arbitrator | Can thiệp giữa chừng |
| `RESOLUTION` | Proposer | Yêu cầu kết thúc debate |

### 2.2 Communication Pattern

#### 2.2.1 Long Polling cho `aw debate wait`

CLI sử dụng **Long Polling** để chờ response từ server:

```python
# CLI Python pseudo-code (tối giản - implementation chuẩn xem 2.2.3)
while True:
    response = requests.get(
        f"{SERVER}/debates/{debate_id}/wait",
        params={"argument_id": Y, "role": "proposer"},
        timeout=65  # > server timeout (60s)
    )
    if response.json()["has_new_argument"]:
        return response.json()
    # else: retry (server timeout, no new data yet)
```

**Tham số `aw debate wait`:**
- `--debate-id`: ID của debate
- `--argument-id`: ID của argument đang chờ response
- `--role`: Role của requester (`proposer` hoặc `opponent`) - để server trả response phù hợp

#### 2.2.2 Response theo Role

| Scenario | Proposer nhận | Opponent nhận |
|----------|---------------|---------------|
| Opponent vừa CLAIM | `action: "respond"` | - (đang chờ) |
| Proposer vừa CLAIM | - (đang chờ) | `action: "respond"` |
| Arbitrator RULING | `action: "align_to_ruling"` | `action: "wait_for_proposer"` |
| Arbitrator INTERVENTION | `action: "wait_for_ruling"` | `action: "wait_for_ruling"` |
| Debate CLOSED | `action: "debate_closed"` | `action: "debate_closed"` |

#### 2.2.3 Timeout Behavior (2 layers)

**Layer 1 - Poll Timeout (per request):**
- Server long-poll tối đa **60 giây** mỗi request
- Client timeout **65 giây** (> server timeout)
- Nếu hết 60s mà chưa có data mới, server trả về `{ "has_new_argument": false }`
- CLI tự động retry request mới

**Layer 2 - Overall Wait Deadline:**
- CLI có overall deadline **5 phút** (300 giây)
- Nếu sau 5 phút vẫn chưa có response, CLI trả về `status: "timeout"`
- AI agent thông báo cho user và thoát
- Khi cần resume, user trigger lại **CẢ Proposer và Opponent**

```python
# CLI pseudo-code
overall_start = time.time()
OVERALL_DEADLINE = int(os.getenv("DEBATE_WAIT_DEADLINE", 300))  # default 5 phút, có thể override
POLL_TIMEOUT = 65  # > server 60s

while time.time() - overall_start < OVERALL_DEADLINE:
    response = requests.get(
        f"{SERVER}/debates/{debate_id}/wait",
        params={"argument_id": Y, "role": "proposer"},
        timeout=POLL_TIMEOUT
    )
    if response.json()["has_new_argument"]:
        return response.json()
    # else: retry

return {"status": "timeout", "message": f"No response after {OVERALL_DEADLINE} seconds"}
```

**Environment Variables:**
- `DEBATE_WAIT_DEADLINE`: Override overall deadline (seconds). Default: 300 (5 phút)
- Use case: debate phức tạp có thể cần deadline dài hơn

**Resume Flow:**
1. User chạy lại Proposer với `debate_id`
2. User chạy lại Opponent với `debate_id`
3. Mỗi bên gọi `aw debate get-context` để lấy lại context
4. Dựa vào `state` hiện tại, mỗi bên biết mình cần làm gì tiếp

**LƯU Ý cho Commands/Rules:** Proposer và Opponent Commands PHẢI hướng dẫn AI agent handle trường hợp resume với `debate_id` đã tồn tại. AI agent cần:
- Đọc lại toàn bộ context từ `aw debate get-context`
- Kiểm tra `state` hiện tại
- Thực hiện action phù hợp hoặc gọi `aw debate wait` nếu đang chờ bên kia

### 2.3 Devtool CLI

Đây là cầu nối giữa các AI agent, là công cụ để các AI agent giao tiếp với nhau qua command.

#### 2.3.1 Các components trong `devtools`

- **CLI Python**: Viết trong `devtools/common/cli/devtool/aweave/debate` (giống cấu trúc `docs` CLI)
- **debate-server**: Node.js server trong `devtools/common/debate-server`
- **debate-web**: Next.js app trong `devtools/common/debate-web`

#### 2.3.2 Database Schema

**debates:**

| **Column**      | **Type**      | **Description**                                            |
| --------------- | ------------- | ---------------------------------------------------------- |
| **id** (PK)     | TEXT          | UUID - ID duy nhất của cuộc tranh luận                     |
| **title**       | TEXT          | Tiêu đề vấn đề cần debate                                  |
| **debate_type** | TEXT          | Phân loại (ví dụ: `coding_plan_debate`, `general_debate`)  |
| **state**       | TEXT          | State machine state (xem 2.1.1)                            |
| **created_at**  | TEXT          | Thời gian tạo (ISO 8601)                                   |
| **updated_at**  | TEXT          | Thời gian update cuối (ISO 8601)                           |

> **Note:** Không có `status` column. Status được derive từ `state`:
> - `state = CLOSED` → closed
> - Các state khác → open

**arguments:**

| **Column**            | **Type**      | **Description**                                              |
| --------------------- | ------------- | ------------------------------------------------------------ |
| **id** (PK)           | TEXT          | UUID - ID của lập luận/phản hồi                              |
| **debate_id** (FK)    | TEXT          | Liên kết tới `debates.id`                                    |
| **parent_id** (FK)    | TEXT          | ID của argument trước đó (Self-reference). Null nếu là MOTION |
| **type**              | TEXT          | `MOTION`, `CLAIM`, `APPEAL`, `RULING`, `INTERVENTION`, `RESOLUTION` |
| **role**              | TEXT          | Vai trò: `proposer`, `opponent`, `arbitrator`                |
| **content**           | TEXT          | Nội dung của lập luận                                        |
| **client_request_id** | TEXT          | ID từ client để đảm bảo idempotency (UNIQUE per debate)      |
| **created_at**        | TEXT          | Thời gian submit (ISO 8601)                                  |

**SQL Schema:**

```sql
-- Enable WAL mode và foreign keys (copy pattern từ aw docs)
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE debates (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  debate_type TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'AWAITING_OPPONENT',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE arguments (
  id TEXT PRIMARY KEY,
  debate_id TEXT NOT NULL REFERENCES debates(id),
  parent_id TEXT REFERENCES arguments(id),
  type TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  client_request_id TEXT,
  seq INTEGER NOT NULL,  -- Auto-increment per debate để ordering
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(debate_id, client_request_id),
  UNIQUE(debate_id, seq)  -- Đảm bảo seq unique per debate
);

CREATE INDEX idx_arguments_debate_id ON arguments(debate_id);
CREATE INDEX idx_arguments_parent_id ON arguments(parent_id);
CREATE INDEX idx_arguments_seq ON arguments(debate_id, seq);
```

**Ordering:**
- Sử dụng `seq` integer tăng dần per debate để đảm bảo thứ tự arguments
- Khi query arguments, ORDER BY `seq` ASC

**QUAN TRỌNG - seq Assignment:**
`seq` assignment và insert PHẢI nằm trong **cùng một transaction** để tránh race condition:

```sql
BEGIN IMMEDIATE;
-- Lấy next seq trong cùng transaction
SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM arguments WHERE debate_id = ?;
-- Insert với seq vừa lấy
INSERT INTO arguments (id, debate_id, ..., seq) VALUES (?, ?, ..., ?);
COMMIT;
```

Không rely hoàn toàn vào mutex ở application layer - transaction là source of truth.

**Database Patterns (copy từ `aw docs`):**
- WAL mode cho concurrent access
- `BEGIN IMMEDIATE` transaction cho write operations
- Retry on `SQLITE_BUSY` với exponential backoff

#### 2.3.3 CLI Commands

**`aw debate generate-id`**

Trả về UUID để AI agent sử dụng làm ID. Dùng cho `debate_id`, `client_request_id`.

**`aw debate get-context`**

Lấy lại context của debate đã tồn tại (resume flow).

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-limit` | ❌ | Số lượng arguments gần nhất (default: 10) |

**Response:**
```json
{
  "debate": { "id": "...", "title": "...", "state": "AWAITING_PROPOSER", ... },
  "arguments": [
    { "type": "MOTION", ... },
    { "...last N arguments..." }
  ]
}
```

**`aw debate create`**

Proposer khởi tạo debate mới.

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | UUID từ `generate-id` |
| `--title` | ✅ | Tiêu đề debate |
| `--debate-type` | ✅ | `coding_plan_debate`, `general_debate` |
| `--file` | ✅ | Path đến file nội dung MOTION |
| `--client-request-id` | ✅ | UUID để đảm bảo idempotency |

**debateType:**
- `coding_plan_debate`: Proposer tạo plan, Opponent review và tìm lỗi/cải thiện
- `general_debate`: Tranh luận chung dựa trên kiến thức AI

**`aw debate wait`**

Chờ response từ bên đối diện (Long Polling).

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | ID của debate |
| `--argument-id` | ✅ | ID của argument đang chờ response |
| `--role` | ✅ | `proposer` hoặc `opponent` |

**Response theo role:** Xem section 2.2.2

**`aw debate submit`**

Submit argument mới (CLAIM).

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | ID của debate |
| `--role` | ✅ | `proposer` hoặc `opponent` |
| `--target-id` | ✅ | ID argument đang phản hồi |
| `--content` | ✅ | Nội dung (hoặc `--file`) |
| `--client-request-id` | ✅ | UUID để đảm bảo idempotency |

**`aw debate appeal`**

Proposer submit APPEAL yêu cầu Arbitrator phán xử.

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument đang tranh cãi |
| `--content` | ✅ | Nội dung appeal (context + options) |
| `--client-request-id` | ✅ | UUID để đảm bảo idempotency |

**`aw debate request-completion`**

Proposer yêu cầu kết thúc debate (tạo RESOLUTION).

| Tham số | Required | Mô tả |
|---------|----------|-------|
| `--debate-id` | ✅ | ID của debate |
| `--target-id` | ✅ | ID argument cuối cùng |
| `--content` | ✅ | Tóm tắt kết quả debate |
| `--client-request-id` | ✅ | UUID để đảm bảo idempotency |

> **Note:** `submitRuling` và `submitIntervention` không cần CLI vì Arbitrator (human) sử dụng `debate-web`

### 2.4 Concurrency & Locking

#### 2.4.1 Server-side Locking

Mỗi debate có một mutex lock. Tại một thời điểm chỉ có 1 bên được write.

```javascript
// Pseudo-code trong debate-server
const debateLocks = new Map(); // debate_id -> mutex

async function submitArgument(debateId, role, content, clientRequestId) {
  const lock = getOrCreateLock(debateId);
  
  await lock.acquire();
  try {
    // 1. Idempotency check
    const existing = db.findByClientRequestId(debateId, clientRequestId);
    if (existing) return existing; // Return existing, không tạo mới
    
    // 2. State validation - role này có được submit không?
    const debate = db.getDebate(debateId);
    if (!canSubmit(debate.state, role)) {
      throw new Error(`Role ${role} cannot submit in state ${debate.state}`);
    }
    
    // 3. Insert argument
    const argument = db.insertArgument({...});
    
    // 4. Update debate state (atomic)
    const newState = calculateNextState(debate.state, argumentType);
    db.updateDebateState(debateId, newState);
    
    // 5. Broadcast to WebSocket clients
    websocket.broadcast(debateId, { event: 'new_argument', data: argument });
    
    return argument;
  } finally {
    lock.release();
  }
}
```

#### 2.4.2 State/Role Validation (Invariant)

**Đây là invariant bắt buộc.** Server PHẢI validate và trả lỗi nếu:
- Role không được phép submit trong state hiện tại
- Action không hợp lệ cho state hiện tại

**Validation Matrix:**

| State | Proposer allowed | Opponent allowed | Arbitrator allowed |
|-------|------------------|------------------|-------------------|
| `AWAITING_OPPONENT` | ❌ | ✅ submit | ✅ intervention |
| `AWAITING_PROPOSER` | ✅ submit/appeal/completion | ❌ | ✅ intervention |
| `AWAITING_ARBITRATOR` | ❌ | ❌ | ✅ ruling |
| `INTERVENTION_PENDING` | ❌ | ❌ | ✅ ruling |
| `CLOSED` | ❌ | ❌ | ❌ |

**Error Response Format (ổn định để agent handle):**

```json
{
  "success": false,
  "error": {
    "code": "ACTION_NOT_ALLOWED",
    "message": "Role 'opponent' cannot submit in state 'AWAITING_PROPOSER'",
    "current_state": "AWAITING_PROPOSER",
    "allowed_roles": ["proposer"],
    "suggestion": "Wait for proposer to submit their argument"
  }
}
```

AI agent có thể dựa vào `error.code` để handle programmatically.

### 2.5 Error Handling & Recovery

#### 2.5.1 Scenarios

| Scenario | Xử lý |
|----------|-------|
| AI agent crash giữa chừng (chưa submit) | Resume với `debate_id`, đọc context, tiếp tục |
| AI agent crash sau submit, trước wait | Resume, check state, gọi wait nếu cần |
| Network error khi submit | CLI retry 3 lần với exponential backoff |
| Server crash/restart | SQLite persist data, clients tự reconnect |
| Duplicate submit (retry) | Server check `client_request_id`, return existing argument |

#### 2.5.2 Idempotency

Mọi submit command đều cần `client_request_id`:
- AI agent generate UUID trước khi submit
- Server check nếu `(debate_id, client_request_id)` đã tồn tại → return existing
- Đảm bảo retry không tạo duplicate arguments

### 2.6 Commands, Rules, Skills Structure

#### 2.6.1 Folder Structure

```
devdocs/agent/
├── commands/
│   └── common/
│       ├── debate-proposer.md      # Proposer Command (chung cho mọi debateType)
│       └── debate-opponent.md      # Opponent Command (chung cho mọi debateType)
│
└── rules/
    └── common/
        └── debate/
            ├── proposer/
            │   ├── coding-plan.md      # Rules cho coding_plan_debate
            │   └── general.md          # Rules cho general_debate
            │
            └── opponent/
                ├── coding-plan.md      # Rules cho coding_plan_debate
                └── general.md          # Rules cho general_debate
```

#### 2.6.2 Command vs Rule

| Type | Mục đích | Load khi nào |
|------|----------|--------------|
| **Command** | Quy trình chung: cách gọi CLI, handle states, resume flow | Luôn load khi bắt đầu |
| **Rule** | Logic nghiệp vụ theo debateType: cách review plan, cách phản biện | Load dựa vào `debateType` |

#### 2.6.3 Load Rules theo debateType

Command hướng dẫn AI agent tự đọc `debateType` rồi load rule file tương ứng:

```markdown
# Trong Proposer Command
Sau khi biết debateType từ `aw debate get-context` hoặc user input:
- coding_plan_debate: đọc `devdocs/agent/rules/common/debate/proposer/coding-plan.md`
- general_debate: đọc `devdocs/agent/rules/common/debate/proposer/general.md`
```

#### 2.6.4 Commands Content (TODO)

**Proposer Command** cần bao gồm:
- Cách tạo debate mới
- Cách resume debate cũ
- Cách handle từng state
- Cách sử dụng `aw docs` để share tài liệu
- Khi nào submit APPEAL, RESOLUTION

**Opponent Command** cần bao gồm:
- Cách join debate
- Cách resume debate cũ  
- Cách handle từng state
- Cách sử dụng `aw docs` để get tài liệu
- Cách đưa ra CLAIM hiệu quả

### 2.7 debate-web

Xây dựng Next.js application ở `devtools/common/debate-web`

**Tech stack:** Next.js + shadcn/ui + WebSocket client

#### 2.7.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│                         debate-web                           │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│   SIDEBAR    │              CONTENT AREA                    │
│              │                                              │
│  ┌────────┐  │  ┌────────────────────────────────────────┐  │
│  │ Search │  │  │  Argument List                         │  │
│  └────────┘  │  │  - MOTION (Proposer)                   │  │
│              │  │  - CLAIM (Opponent)                    │  │
│  ┌────────┐  │  │  - CLAIM (Proposer)                    │  │
│  │Debate 1│  │  │  - ...                                 │  │
│  ├────────┤  │  │                                        │  │
│  │Debate 2│  │  └────────────────────────────────────────┘  │
│  ├────────┤  │                                              │
│  │  ...   │  │  ┌────────────────────────────────────────┐  │
│  └────────┘  │  │  ACTION AREA                           │  │
│              │  │  (Button hoặc Chat box - xem 2.7.2)    │  │
│              │  └────────────────────────────────────────┘  │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

#### 2.7.2 Action Area Logic

| State hiện tại | UI hiển thị |
|----------------|-------------|
| `AWAITING_OPPONENT` hoặc `AWAITING_PROPOSER` | **Stop Button** (full width, icon stop). Hold 1s để gửi INTERVENTION |
| `AWAITING_ARBITRATOR` (từ APPEAL) | **Chat box** để nhập RULING content |
| `AWAITING_ARBITRATOR` (từ RESOLUTION) | **Chat box** để nhập RULING (close hoặc continue) |
| `INTERVENTION_PENDING` | **Chat box** để nhập RULING content |
| `CLOSED` | Disabled / Read-only |

### 2.8 debate-server

Node.js server trong `devtools/common/debate-server`

#### 2.8.0 Server Bind & Security

**Network Binding:**
- **Default:** Bind `127.0.0.1` (localhost only)
- Không expose ra LAN/Internet trừ khi explicitly configured

**Authentication (Optional):**
- Env var `DEBATE_AUTH_TOKEN` để enable bearer token auth
- Nếu set, tất cả requests phải có header `Authorization: Bearer <token>`
- Nếu không set, no auth (local development mode)

```bash
# Development (no auth)
npm start

# With auth
DEBATE_AUTH_TOKEN=my-secret-token npm start
```

**CLI Configuration:**
- Env var `DEBATE_SERVER_URL` (default: `http://127.0.0.1:3456`)
- Env var `DEBATE_AUTH_TOKEN` (nếu server require auth)

#### 2.8.1 Responsibilities

1. **REST API cho CLI**: Tất cả debate operations
2. **WebSocket cho Web**: Real-time updates + Arbitrator actions
3. **State Machine**: Single source of truth
4. **SQLite Database**: Data persistence

#### 2.8.2 API Endpoints (REST)

| Method | Endpoint | Description | Used by |
|--------|----------|-------------|---------|
| POST | `/debates` | Create debate | CLI |
| GET | `/debates/:id` | Get debate + arguments | CLI |
| POST | `/debates/:id/arguments` | Submit argument | CLI |
| POST | `/debates/:id/appeal` | Submit appeal | CLI |
| POST | `/debates/:id/resolution` | Request completion | CLI |
| GET | `/debates/:id/wait` | Long polling wait | CLI |
| GET | `/debates` | List debates | Web |

#### 2.8.3 WebSocket Events

**Server → Client (Web):**

| Event | Trigger | Data |
|-------|---------|------|
| `initial_state` | On connect | Full debate + all arguments |
| `new_argument` | Khi có argument mới | Argument object |
| `state_changed` | Khi state thay đổi | New state |

**Client → Server (Web):**

| Event | Description | Data |
|-------|-------------|------|
| `submit_intervention` | Arbitrator INTERVENTION | `{ debate_id }` |
| `submit_ruling` | Arbitrator RULING | `{ debate_id, content, close? }` |

#### 2.8.4 Real-time Notification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Notification Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLI (Proposer)           debate-server           debate-web    │
│       │                        │                       │        │
│       │── POST /arguments ────►│                       │        │
│       │                        │                       │        │
│       │                        │── ws: new_argument ──►│        │
│       │                        │                       │        │
│       │◄── 201 Created ────────│                       │        │
│       │                        │                       │        │
│  CLI (Opponent)                │                       │        │
│       │                        │                       │        │
│       │── GET /wait ──────────►│                       │        │
│       │   (long polling)       │                       │        │
│       │                        │   ... time passes ... │        │
│       │                        │                       │        │
│       │                        │◄── ws: submit_ruling ─│        │
│       │                        │                       │        │
│       │◄── 200 (new argument)──│── ws: new_argument ──►│        │
│       │                        │                       │        │
└─────────────────────────────────────────────────────────────────┘
```

Server broadcast `new_argument` event sau mỗi lần insert argument thành công (trong `submitArgument`, `submitRuling`, `submitIntervention`).

## 3. Tóm tắt các việc phải làm

### 3.1 Infrastructure (theo thứ tự dependency)

| # | Task | Location | Dependencies |
|---|------|----------|--------------|
| 1 | **debate-server** (Node.js) | `devtools/common/debate-server` | - |
| | - SQLite schema + better-sqlite3 | | |
| | - REST API endpoints | | |
| | - State machine logic | | |
| | - WebSocket server | | |
| | - Locking mechanism | | |
| 2 | **debate CLI** (Python) | `devtools/common/cli/devtool/aweave/debate` | debate-server |
| | - Tất cả commands (generate-id, create, get-context, submit, wait, appeal, request-completion) | | |
| | - Long polling implementation | | |
| | - MCPResponse format | | |
| 3 | **debate-web** (Next.js) | `devtools/common/debate-web` | debate-server |
| | - Sidebar + Content layout | | |
| | - WebSocket client | | |
| | - Arbitrator actions (INTERVENTION, RULING) | | |

### 3.2 AI Agent Configuration

| # | Task | Location |
|---|------|----------|
| 4 | **Proposer Command** | `devdocs/agent/commands/common/debate-proposer.md` |
| | - Quy trình tạo/resume debate | |
| | - Handle từng state | |
| | - Sử dụng `aw docs` | |
| 5 | **Opponent Command** | `devdocs/agent/commands/common/debate-opponent.md` |
| | - Quy trình join/resume debate | |
| | - Handle từng state | |
| | - Sử dụng `aw docs` | |
| 6 | **Proposer Rules** | `devdocs/agent/rules/common/debate/proposer/` |
| | - `coding-plan.md`: Rules cho coding_plan_debate | |
| | - `general.md`: Rules cho general_debate | |
| 7 | **Opponent Rules** | `devdocs/agent/rules/common/debate/opponent/` |
| | - `coding-plan.md`: Rules cho coding_plan_debate | |
| | - `general.md`: Rules cho general_debate | |

### 3.3 Technical Decisions Summary

| Decision | Choice |
|----------|--------|
| Database | SQLite (file: `~/.aweave/debate.db`) |
| DB Library | better-sqlite3 |
| CLI Language | Python |
| CLI ↔ Server | HTTP REST |
| Web ↔ Server | WebSocket |
| Wait mechanism | Long Polling (timeout 5 phút) |
| Idempotency | `client_request_id` per request |
| State vs Status | Chỉ giữ `state`, derive status từ state |
| Submit sai lượt | Return error (không queue) |
| Load rules | AI agent tự load dựa vào debateType |
