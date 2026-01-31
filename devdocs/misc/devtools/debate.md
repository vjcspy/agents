# Debate

Ý tưởng của tôi là xây dựng 1 ecosytem để cung cấp các rules, tools, applications và environment để cho các AI agents có thể tranh luận xung quanh các topic.
Dưới đây là mô tả về nghiệp vụ cũng như hệ thống

## 1. Các bên tham gia

- Proposer (AI Agent) – Bên Đề Xuất
Đóng vai trò là thực thể khởi xướng và duy trì định hướng của cuộc tranh luận.

Khởi tạo (MOTION): Có quyền đưa ra chủ đề hoặc vấn đề cần thảo luận ban đầu.

Tiếp nhận & Điều chỉnh (REVISE): Có quyền chấp nhận các CLAIM từ Opponent để cập nhật, chỉnh sửa (revise) lại nội dung đề xuất ban đầu cho phù hợp hơn.

Thỉnh cầu (APPEAL): Khi xảy ra xung đột không thể tự giải quyết với Opponent, Proposer có quyền gửi một bản thỉnh cầu (APPEAL) tới Arbitrator để yêu cầu một quyết định định hướng.

- Opponent (AI Agent) – Bên Phản Biện
Đóng vai trò là thực thể kiểm định và đưa ra góc nhìn đối lập.

Phản biện (CLAIM): Có quyền đưa ra các lập luận, bằng chứng hoặc lý lẽ để phản bác, đóng góp ý kiến vào vấn đề mà Proposer đưa ra.

Mục tiêu: Tìm ra các lỗ hổng hoặc điểm chưa tối ưu trong MOTION hoặc các bản REVISE của Proposer.

- Arbitrator (User hoặc AI Agent) – Trọng Tài/Người Phân Xử
Đóng vai trò là thực thể có quyền quyết định cao nhất, đảm bảo cuộc tranh luận không bị bế tắc.

Tiếp nhận xung đột: Chỉ tham gia xử lý khi có một record APPEAL được khởi tạo bởi Proposer.

Ra phán quyết (RULING): Có nhiệm vụ xem xét các CLAIM hiện tại của cả hai bên và đưa ra một bản phán quyết (RULING). Record này sẽ đóng vai trò là "kim chỉ nam" bắt buộc để các bên phải tuân thủ và tiếp tục tranh luận theo hướng đó.

### 1.1 Mô tả quy trình debate

Step1 `Proposer`:
Sử dụng `Proposer Command` để hiểu được cách làm việc, xác định kiểu `debateType` rồi sau đó xác định xem trạng thái hiện tai của debate.
Lúc này sẽ có 2 trường hợp:

- Tham gia lại vào debate đã open trước đó
- Tạo mới một debate conversation

**Trường hợp user gửi một `debate_id` đã tồn tại:**
Sẽ gọi command `getOldDebateContext` để lấy thông tin debate cũ đọc và hiểu context, phân tích và có thể cần thực hiện thêm các addition steps như scan folder, read source code, nói chung là làm toàn bộ nhưng thứ mà cho là cần thiết để lấy được lại context cũ, cuối cùng xem role của argument cuối cùng là gì?
Nếu role là của `Proposer` chính là role của mình thì sẽ gọi `waitForArgumentResponse` để chờ kết quả
Nếu role khác `Proposer` tức là đã có phản hồi thì xem phản hồi đó là gì để đánh giá xem có chuẩn không, hoặc nếu là của `Arbitrator` thì follow theo option mà `Arbitrator` đưa ra. Sau đó thực hiện tiếp các công việc cần thiết rồi gọi `submitArgument` lấy được `argument_id` rồi gọi `waitForArgumentResponse` trên `argument_id` để chờ phản hồi

**Trường hợp user yêu cầu create new debate:**
 Nếu user gửi 1 .create 1 debetate conversation bằng cách sử dụng `generateId` và `createDebate`.

   Sau khi `createDebate` trả về resonse thành công sẽ có `debate_id`, `argument_id`, thì sẽ gọi `waitForArgumentResponse` dùng 2 tham số đó và chờ response

Step2 `Opponent`:
Sử dụng `Opponent Command` để hiểu được cách làm việc, user sẽ cung cấp `debate_id`. Gọi command `getOldDebateContext` để lấy thông tin debate cũ đọc và hiểu context,phân tích và có thể cần thực hiện thêm các addition steps như scan folder, read source code, nói chung là làm toàn bộ nhưng thứ mà cho là cần thiết để lấy được lại context cũ, cuối cùng xem role của argument cuối cùng là gì?
Nếu role là `Proposer` thì do chưa có `argument_id` tại thời điểm này nên sẽ xem `type` của `argument` nếu nó là `MOTION` tức là 1 vấn đề mới thì follow theo các rules đã được nạp trước đó để tiền hành đánh giá và sau khi có kết quả thì gọi `submitArgument`. Response sẽ trả về là `argument_id` tức là thành công và đó chính là `argument` cần được truyền vào command `waitForArgumentResponse` cùng với `debate_id` để chờ phản hồi.

Step3 Lặp lại quá trình debate:
2 bên `Proposer` và `Opponent`

## 2. Hệ thống cần xây dựng

### 2.1 Devtool cli

Đây là cầu nối giữa các AI agent, là công cụ để các AI agent giao tiếp với nhau qua command.

#### 2.1.1 Các components trong `devtools`

- Cần phải có database để lưu trữ -> suggest 1 framework để lưu trữ được data xuống file mà có thể query được dễ dàng
- Cung cấp các cli commands để AI Agent gọi. Tôi sẽ viết trong `devtools`, hãy refer REAMDE ở đây để hiểu context `devtools/README.md`. Nên viết code trong package `devtools/common/cli/devtool/aweave` bằng cách tạo thêm package `debate`
- Expose được API để làm giao diện frontend để user có thể xem được các conversation của 1 debateId, cũng như có khả năng gửi message với vai trò là `Arbitrator` -> tôi nghĩ nên viết phần server socket này bằng nodejs. Tức là tạo thêm package nodejs server trong `devtools/common/debate-server`

#### 2.1.2 Database

- **debates**

| **Column**      | **Type**      | **Description**                                     |
| --------------- | ------------- | --------------------------------------------------- |
| **id** (PK)     | UUID / String | ID duy nhất của cuộc tranh luận.                    |
| **title**       | String        | Tiêu đề vấn đề cần debate.                          |
| **debate_type** | String        | Phân loại (ví dụ: coding_plan_debate...).           |
| **status**      | Enum          | Trạng thái: `open`, `judging`, `closed`. |
| **created_at**  | Timestamp     | Thời gian tạo.                                      |

- **arguments**

| **Column**         | **Type**      | **Description**                                              |
| ------------------ | ------------- | ------------------------------------------------------------ |
| **id** (PK)        | UUID / String | ID của lập luận/phản hồi.                                    |
| **debate_id** (FK) | UUID          | Liên kết tới `debates.id`.                                   |
| **parent_id** (FK) | UUID          | **ID của câu trả lời trước đó** (Self-reference). Null nếu là câu mở đầu. |
| **type** (FK)      | Enum          | `MOTION`, **`CLAIM`** (Lập luận), **`APPEAL`**(Thỉnh cầu), **`RULING`** (Phán quyết định hướng). |
| **role**           | Enum          | Vai trò lúc viết: `proponent`, `opponent`, `arbitrator`      |
| **content**        | Text          | Nội dung chữ của lập luận.                                   |
| **created_at**     | Timestamp     | Thời gian submit.                                            |

#### 2.1.3 Commands

**generateId**

Trả về uuid để các AI agent sử dụng làm các ID của vấn đề, của câu trả lời(mỗi khi submit câu trả lời sẽ cần có ID). Tóm lại là sử dụng cho tất cả các trường hợp cần phải có 1 ID để làm reference

**getOldDebateContext**
Sử dụng để lấy lại một debate cũ, hay được sử dụng nhất trong trường hợp là resume lại debate chưa hoàn thành.
Tham số là:

- debateId
- argumentLimit: X records

Trả về:

- debate row
- argument rows:[
- row với type là MOTION
- X last arguments
]

**createDebate**

Proposer khởi tạo 1 debate conversation. Tham số sẽ là:

1. debateId: proposer sẽ dùng `generateId` để tạo debateId và gửi
2. title: summary debate content
3. debateType: Kiểu công việc cần phải tranh luận. Chúng ta cũng dựa vào kiểu tranh luận là gì để các AI Agent sẽ nạp các `skill` theo role thích hợp. Ví dụ:
   - coding_plan_debate: Liên quan đến việc coding, đó là khi Proposer tạo ra 1 file plan chi tiết để thực hiện một ticket nào đó. Với kiểu này `Proposer` sẽ nạp skill liên quan đến việc người tạo plan. Còn `Opponent` sẽ nạp skill người tìm ra lỗi sai sót cần improve trong plan đó...
   - general_debate: kiểu debate chung chung, 2 bên chỉ tranh luận qua lại dựa trên kiến thức của AI model.
4. filePath: là đường dẫn đến file chứa nội dung cần debate. Vì cli `aw` là global và chạy local nên trong này sẽ cần phải đọc file content để submit

Phía server xử lý:

1. Tạo record trong table `debates`
2. Init first argumen trong `arguments` table với type là `MOTION`.
3. Lưu các thông tin cần thiết và return lại id của `argumen` cho `Proposer`

**waitForArgumentResponse**

Cả `Proposer` và `Opponent` gọi command này và đợi đến khi có response để lấy phản hồi cho argument của mình đã đưa ra trước đó.

Các bên `Proposer`và `Opponent` luôn kết thúc lượt của mình sau khi thực hiện `submitArgument` bằng cách gọi `waitForResponse`

**submitArgument**

Là khi các bên Proposer hoặc Opponent trả lời lại bên đối diện để đưa ra ý kiến, các luận điểm mới. Nó sẽ cần có các tham số là:

1. debateId: id của debate hiện tại
2. role: là bên nào
3. targetId: phản biện lại id câu trả lời trước đó của phe đối diện

**submitRuling**

#### 2.1.3 Yêu cầu chung

### 2.2 Commands, Rules, SKill

#### 2.2.1 Commands

**Proposer Command**:
**Opponent Command**:

## 3. Tóm tắt lại các việc phải làm

1. Xây dựng cli application bằng cách tạo thêm module trong `devtools/common/cli/devtool/aweave`
2. Xây dựng nodejs server application ở `devtools/common/debate-server`
3. Xây dựng 1 nextjs application ở `devtools/common/debate-web`
4. Xây dựng `Proposer Command` hướng dẫn thực thi cho: `Proposer` để handle các step trong debate, xây dựng các `rules` thực thi cho `Proposer` với các loại debate type khác nhau ví dụ như coding_plan_debate thì cần phải scan code, đọc overview....
5. Xây dựng `Opponent Command` hướng dẫn thực thi cho: `Opponent` để handle các step trong debate, xây dựng các `rules` thực thi cho `Opponent` với các loại debate type khác nhau ví dụ như coding_plan_debate thì cần phải scan code, đọc overview... mới đưa ra được CLAIM
