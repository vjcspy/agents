# 📋 [PROD-XXX: 2026-01-21] - Soft Delete Recurring Schedule Series

## References

- **Target Repository**: `eve` (Java/Dropwizard)
- **Database Schema**: `typ-e`
- **Key Files**:
  - `eve/src/main/java/nl/tinybots/eve/resource/DeleteV4ScheduleResource.java`
  - `eve/src/main/java/nl/tinybots/eve/service/ScheduleService.java`
  - `eve/src/main/java/nl/tinybots/eve/repository/TaskRepository.java`
  - `eve/src/main/java/nl/tinybots/eve/util/ScheduleUtils.java`

## User Requirements

> **From Stakeholder:**
>
> **Relevance:**
> If on my.tinybots.academy you plan a recurring task. Then go let your robot execute a task. After it is executed you go to the future and delete the whole series, all executions are also deleted.
>
> We do not want that! So make sure the old executions stay and only tasks from that point are deleted.
>
> **Solution:**
> When the delete series command is used it should only delete items in the series in the future. If you delete from 2026-05-05 then only tasks after 2026-05-05 should be deleted. If you select a value in the past: 2020-10-10 it should be blocked.
>
> **Endpoint:**
> ```
> DELETE https://api.tinybots.academy/v4/schedules/{robotId}
> ```

## 🎯 Objective

Modify the DELETE schedule endpoint to **soft delete** recurring series by setting `end_at` on `task_schedule` instead of hard deleting `robot_schema`. This preserves historical execution records while preventing future task occurrences.

### ⚠️ Key Considerations

#### 1. Database Relationship Understanding

```
┌──────────────────┐        ┌─────────────────┐        ┌───────────────────┐
│   robot_schema   │        │  task_schedule  │        │ script_execution  │
│   (CHILD)        │───FK──►│   (PARENT)      │◄──FK───│   (CHILD)         │
│                  │        │                 │        │                   │
│ id               │        │ id              │        │ id                │
│ robot_id         │        │ start_at        │        │ schedule_id (FK)  │
│ schedule_id (FK) │        │ end_at ←────────┼────────│ planned           │
│ script_v2_task_id│        │ minute, hour... │        │ script_ref_id     │
└──────────────────┘        └─────────────────┘        └───────────────────┘
```

- **FK Constraints**: All are `RESTRICT` (no CASCADE)
- **Current behavior**: Deleting `robot_schema` leaves `task_schedule` orphaned but `script_execution` records intact
- **Problem**: Historical data relationship is broken, UI may not display correctly

#### 2. Evidence that `end_at` Controls Future Scheduling

The following code analysis proves that setting `end_at` will prevent future task occurrences:

##### 2.1 Query Filter - Schedules with `end_at <= now` are excluded

**File**: `eve/src/main/java/nl/tinybots/eve/repository/TaskRepository.java` (lines 57-61)
```java
// findRobotSchedule() - Robot's schedule query
+ "WHERE rs.`robot_id` = :robotId "
+ "AND (rs.script_v2_task_id IS NULL) "
+ "AND (ts.`end_at` > :now OR ts.`end_at` IS NULL)")  // ← KEY FILTER
```

**Impact**: Robot will NOT receive schedules where `end_at` has passed.

##### 2.2 `mightFire()` - Prevents scheduling after endTime

**File**: `eve/src/main/java/nl/tinybots/eve/util/ScheduleUtils.java` (lines 145-153)
```java
public static boolean mightFire(V6Schedule schedule, Robot robot, ZonedDateTime now) {
    ZonedDateTime start = schedule.getStartTime() == null ? now : schedule.getStartTime();
    if (schedule.getEndTime() == null) {
        return true;
    }
    ZonedDateTime end = schedule.getEndTime();
    ZonedDateTime nextFire = getNextOccurence(schedule, start);
    return nextFire != null && nextFire.isBefore(end);  // ← Returns false if nextFire >= end
}
```

**Impact**: New occurrences will NOT be created after `endTime`.

##### 2.3 `explode()` - Calendar view respects endTime

**File**: `eve/src/main/java/nl/tinybots/eve/util/ScheduleUtils.java` (lines 175-183)
```java
// Similarly we need to stop sooner when the until is after the Tasks endTime.
ZonedDateTime correctedUntil = schedule.getEndTime() != null && until.isAfter(schedule.getEndTime())
    ? schedule.getEndTime() : until;  // ← Caps at endTime

ZonedDateTime time = getNextOccurence(task.getSchedule(), correctedFrom);
while (time != null && time.isBefore(correctedUntil)) {  // ← Only creates occurrences before endTime
    result.add(withTime(task, time));
    time = getNextOccurence(task.getSchedule(), time);
}
```

**Impact**: Calendar will NOT display occurrences after `endTime`.

##### 2.4 Existing Pattern - `deleteScheduledScripts()` already uses this approach

**File**: `eve/src/main/java/nl/tinybots/eve/repository/TaskRepository.java` (lines 327-332)
```java
@SqlUpdate("UPDATE `task_schedule` AS ts "
    + "JOIN robot_schema AS rs ON (rs.schedule_id = ts.id)"
    + "JOIN script_task AS st ON (rs.script_task_id = st.`id`) "
    + "SET ts.`end_at` = NOW() "  // ← EXISTING PATTERN!
    + "WHERE rs.`robot_id` = :robotId AND st.`script_robot_id` = :scriptId "
    + "AND (ts.`end_at` > NOW() OR ts.`end_at` IS NULL)")
int deleteScheduledScripts(@Bind("scriptId") Long scriptId, @Bind("robotId") Long robotId);
```

**Impact**: This pattern is **already proven** in production for script unscheduling.

##### 2.5 Summary Table

| Checkpoint | Status | Evidence Location |
|------------|--------|-------------------|
| Robot không nhận schedule sau `end_at` | ✅ | `TaskRepository.findRobotSchedule()` SQL filter |
| Calendar không hiển thị sau `end_at` | ✅ | `ScheduleUtils.explode()` caps at endTime |
| Không tạo new executions sau `end_at` | ✅ | `ScheduleUtils.mightFire()` returns false |
| Pattern đã được sử dụng trong production | ✅ | `TaskRepository.deleteScheduledScripts()` |

#### 3. Business Rules

- `fromDate` parameter **MUST** be in the future or present (today/now)
- If `fromDate` is in the past → return **400 Bad Request**
- Historical `script_execution` records must remain intact
- `robot_schema` record should **NOT** be deleted (to maintain relationships)

#### 4. Boundary Semantics (Exclusive)

> **Definition**: `fromDate` acts as an exclusive boundary in robot's timezone.
> - Occurrences with `time < fromDate` → **KEPT** (historical)
> - Occurrences with `time >= fromDate` → **REMOVED** (future)

**Example** (Robot TZ: Europe/Amsterdam):
- Schedule: Daily at 09:00
- `fromDate`: 2026-05-05T00:00:00+02:00
- Result: 
  - 2026-05-04 09:00 → ✅ Kept
  - 2026-05-05 09:00 → ❌ Removed
  - 2026-05-06 09:00 → ❌ Removed

**Timezone Handling**:
- `fromDate` MUST be interpreted in robot's timezone (from `X-Time-Zone` header)
- Mapper converts to `ZonedDateTime` using robot TZ before storing as `end_at`

#### 5. Idempotency & No-op Behavior

| Scenario | Response | Behavior |
|----------|----------|----------|
| Schedule exists, `end_at` updated | **204 No Content** | Success |
| Schedule already ended before `fromDate` | **204 No Content** | No-op (idempotent) |
| Schedule not found | **404 Not Found** | Error |
| `fromDate` in the past | **400 Bad Request** | Validation error |

> **Rationale**: REST semantics - "soft delete from X" on an already-ended series is a valid no-op, not an error. This ensures idempotent behavior for retries.

#### 6. Concurrency & Transaction Handling

**Concern**: Race condition between `updateScheduleEndAt()` and occurrence-creation jobs.

**Solution**:
- Wrap `updateScheduleEndAt()` in a transaction at service layer
- Use `SELECT ... FOR UPDATE` pattern if needed for critical sections
- Scheduler jobs should re-check `end_at` after reading schedule

```java
// In ScheduleService (transactional)
@Transaction
public void softDeleteSeries(Long scheduleId, ZonedDateTime fromDate) {
    int updated = taskRepository.updateScheduleEndAt(scheduleId, fromDate);
    // No exception on updated=0, just a no-op
}
```

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [x] Analyze database schema and FK relationships
  - **Outcome**: `script_execution` → `task_schedule` (FK), no CASCADE delete
- [x] Analyze current DELETE logic flow
  - **Outcome**: Hard delete on `robot_schema`, `task_schedule` orphaned
- [x] Verify `end_at` behavior across codebase
  - **Outcome**: All queries filter by `end_at`, pattern already used in `deleteScheduledScripts()`
- [x] Define edge cases:
  - `fromDate` in the past → Block with **400 Bad Request**
  - `fromDate` = today/now → Allow (delete from now onwards)
  - Schedule already ended (`end_at` < `fromDate`) → **204 No-op** (idempotent)
  - Non-recurring schedule → Delete single occurrence (existing behavior)
  - Boundary: exclusive semantics (`>= fromDate` removed, `< fromDate` kept)
- [ ] Review existing integration tests
  - **Outcome**: `DeleteV4ScheduleResourceIT.java` has tests for single occurrence delete

### Phase 2: Implementation (File Structure)

```
eve/src/main/java/nl/tinybots/eve/
├── resource/
│   └── DeleteV4ScheduleResource.java       # 🔄 UPDATE - Add fromDate query param + body support
├── service/
│   └── ScheduleService.java                # 🔄 UPDATE - Change delete logic, add @Transaction
├── repository/
│   └── TaskRepository.java                 # 🔄 UPDATE - Add updateScheduleEndAt method
├── model/dto/
│   └── TaskIdentifierDto.java              # 🔄 UPDATE - Add fromDate field with @InFutureOrPresent
├── mapper/
│   └── TaskIdentifierDtoMapper.java        # 🔄 UPDATE - Map fromDate with robot TZ
├── validate/
│   └── InFutureOrPresent.java              # ✨ NEW (if not exists) - Allow NOW, reject past

eve/src/test/java/nl/tinybots/eve/
├── resource/
│   └── DeleteV4ScheduleResourceIT.java     # 🔄 UPDATE - Add soft delete + boundary + no-op tests
├── service/
│   └── ScheduleServiceTest.java            # 🔄 UPDATE - Add unit tests
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Update `TaskIdentifierDto` - Add `fromDate` field

**File**: `eve/src/main/java/nl/tinybots/eve/model/dto/TaskIdentifierDto.java`

```java
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class TaskIdentifierDto {
    
    @Min(1)
    @NotNull
    private Long id;
    
    @InFuture
    private ZonedDateTime time;  // Existing - for single occurrence delete
    
    @InFutureOrPresent  // Allow NOW, reject past
    private ZonedDateTime fromDate;  // NEW - for series soft delete (API name)
}
```

> **Note**: `@InFutureOrPresent` allows `fromDate=NOW` which is the common use case. Create custom validator if not exists, or use `@FutureOrPresent` from javax.validation with robot TZ normalization in mapper.

**Behavior**:
- If `time` is provided → Delete single occurrence (existing behavior)
- If `fromDate` is provided (and `time` is null) → Soft delete series from `fromDate`
- If neither provided → Soft delete series from NOW (backward compatible)

**Naming Convention**:
- API level: `fromDate` (business-friendly, "delete from this date")
- Internal/DB: `endAt` (technical, matches `task_schedule.end_at` column)

#### Step 2: Add Repository Method

**File**: `eve/src/main/java/nl/tinybots/eve/repository/TaskRepository.java`

```java
/**
 * Soft delete a schedule by setting end_at to the specified date.
 * Only updates if current end_at is after the new end date or is null.
 */
@SqlUpdate("UPDATE `task_schedule` AS ts "
    + "SET ts.`end_at` = :endAt "
    + "WHERE ts.`id` = :scheduleId "
    + "AND (ts.`end_at` > :endAt OR ts.`end_at` IS NULL)")
int updateScheduleEndAt(@Bind("scheduleId") Long scheduleId, @Bind("endAt") ZonedDateTime endAt);
```

#### Step 3: Update `ScheduleService.delete()` Method

**File**: `eve/src/main/java/nl/tinybots/eve/service/ScheduleService.java`

```java
@Transaction  // Ensure atomicity
public List<Task> delete(@NonNull Task task, @NonNull Robot robot, 
                         @NonNull ZonedDateTime now, DateTimeZone robotTz) {
    Task toBeDeleted = taskRepository.findRobotTaskById(robot.getId(), task.getId());
    if (toBeDeleted == null) {
        throw new NotFoundException("Schedule not found for robot");
    }

    toBeDeleted.getSchedule().setTimeZone(ZoneId.of(robotTz.getID()));

    // Case 1: Delete single occurrence (existing behavior - unchanged)
    if (task.getTime() != null) {
        // ... existing split series logic ...
    }
    
    // Case 2: Soft delete series from a specific date
    // Convert fromDate (API) to endAt (DB) - same value, different naming context
    ZonedDateTime endAt = task.getFromDate() != null ? task.getFromDate() : now;
    
    // Validate: endAt must not be in the past (DTO @InFutureOrPresent should catch this, but double-check)
    if (endAt.isBefore(now)) {
        throw new BadRequestException("Cannot delete schedule series from a past date");
    }
    
    // Soft delete by setting end_at
    Long scheduleId = toBeDeleted.getSchedule().getId();
    int updated = taskRepository.updateScheduleEndAt(scheduleId, endAt);
    
    // No exception on updated=0 - this is a no-op (idempotent)
    // Schedule was already ended before endAt, which is a valid state
    // Resource layer will return 204 regardless
    
    return Lists.newLinkedList();
}
```

> **Idempotency Note**: `updated=0` means schedule already ended → no-op, still return 204. This follows REST DELETE semantics where deleting an already-deleted resource is not an error.

#### Step 4: Update `DeleteV4ScheduleResource`

**File**: `eve/src/main/java/nl/tinybots/eve/resource/DeleteV4ScheduleResource.java`

```java
@DELETE
@Timed
public void deleteScheduledTask(
    @NotNull @HeaderParam(EveConstants.TZ_HEADER) String timeZoneId,
    @PathParam("robotId") Long robotId, 
    @Auth TinyPrincipal user,
    @QueryParam("fromDate") String fromDateParam,  // NEW: Query param support
    TaskIdentifierDto taskDto) {
    
    Robot robot = ((User) user).getRobots().get(robotId);
    if (robot == null) {
        throw new ForbiddenException("Not allowed to manage robot with id " + robotId);
    }
    
    DateTimeZone robotTz = robotTimeZoneService.getRobotTimeZone(robot);
    ResourceUtils.checkTimezone(robotTz, timeZoneId);

    // Support both: query param and body (query param takes precedence for clients that can't send DELETE body)
    if (fromDateParam != null && taskDto.getFromDate() == null) {
        taskDto.setFromDate(ZonedDateTime.parse(fromDateParam));
    }

    Task task = taskIdentifierDtoMapper.map(taskDto, robot, robotTz);
    task.setRobotId(robotId);
    
    scheduleService.delete(task, robot, robotTz);
    changeNotificationService.notifyChange(robot);
}
```

**API Contract** (both supported):

```bash
# Option 1: Query param (for clients that don't support DELETE body)
DELETE /v4/schedules/{robotId}?fromDate=2026-05-05T00:00:00%2B02:00
Content-Type: application/json
X-Time-Zone: Europe/Amsterdam
{"id": 123}

# Option 2: Request body (standard)
DELETE /v4/schedules/{robotId}
Content-Type: application/json
X-Time-Zone: Europe/Amsterdam
{"id": 123, "fromDate": "2026-05-05T00:00:00+02:00"}

# Option 3: No fromDate (backward compatible - defaults to NOW)
DELETE /v4/schedules/{robotId}
Content-Type: application/json
X-Time-Zone: Europe/Amsterdam
{"id": 123}
```

#### Step 5: Update Mapper

**File**: `eve/src/main/java/nl/tinybots/eve/mapper/TaskIdentifierDtoMapper.java`

Update to map the new `fromDate` field from DTO to Task model.

#### Step 6: Integration Tests

**File**: `eve/src/test/java/nl/tinybots/eve/resource/DeleteV4ScheduleResourceIT.java`

```java
@Test
@DataSet("data/DeleteV4ScheduleResourceIT/recurringScheduleWithExecutions.sql")
public void softDeleteSeriesFromFutureDate_shouldPreserveHistoricalExecutions() {
    // Given: A recurring schedule with some past executions
    
    // When: Delete series from a future date
    TaskIdentifierDto deleteRequest = new TaskIdentifierDto();
    deleteRequest.setId(scheduleId);
    deleteRequest.setFromDate(ZonedDateTime.now(NL).plusDays(7));
    
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .body(deleteRequest)
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(204);
    
    // Then: Schedule end_at is updated
    // And: Historical executions still exist
    // And: Future occurrences are not returned
}

@Test
public void softDeleteSeriesFromPastDate_shouldReturn400() {
    TaskIdentifierDto deleteRequest = new TaskIdentifierDto();
    deleteRequest.setId(scheduleId);
    deleteRequest.setFromDate(ZonedDateTime.now(NL).minusDays(7));
    
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .body(deleteRequest)
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(400);
}

@Test
public void softDeleteSeriesWithoutFromDate_shouldDeleteFromNow() {
    // Given: A recurring schedule
    
    // When: Delete series without fromDate (backward compatible)
    TaskIdentifierDto deleteRequest = new TaskIdentifierDto();
    deleteRequest.setId(scheduleId);
    // No fromDate - defaults to NOW
    
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .body(deleteRequest)
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(204);
    
    // Then: Schedule end_at is set to approximately NOW
}

@Test
@DataSet("data/DeleteV4ScheduleResourceIT/alreadyEndedSchedule.sql")
public void softDeleteAlreadyEndedSeries_shouldReturn204NoOp() {
    // Given: A schedule that already ended (end_at in the past)
    
    // When: Try to soft delete from a future date
    TaskIdentifierDto deleteRequest = new TaskIdentifierDto();
    deleteRequest.setId(scheduleId);
    deleteRequest.setFromDate(ZonedDateTime.now(NL).plusDays(7));
    
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .body(deleteRequest)
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(204);  // No-op, idempotent - NOT 404
    
    // Then: end_at unchanged (still the old value)
}

@Test
public void softDeleteWithQueryParam_shouldWork() {
    // Given: A recurring schedule
    String fromDate = ZonedDateTime.now(NL).plusDays(7).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
    
    // When: Delete using query param (for clients that can't send DELETE body)
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .queryParam("fromDate", fromDate)
        .body("{\"id\": " + scheduleId + "}")
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(204);
    
    // Then: Schedule end_at is updated to fromDate
}

@Test
@DataSet("data/DeleteV4ScheduleResourceIT/recurringScheduleWithExecutions.sql")
public void softDeleteBoundary_shouldBeExclusive() {
    // Given: Schedule with occurrences at 09:00 daily
    // fromDate = 2026-05-05T00:00:00 (robot TZ)
    
    // When: Soft delete from 2026-05-05
    TaskIdentifierDto deleteRequest = new TaskIdentifierDto();
    deleteRequest.setId(scheduleId);
    deleteRequest.setFromDate(ZonedDateTime.of(2026, 5, 5, 0, 0, 0, 0, ZoneId.of("Europe/Amsterdam")));
    
    given()
        .contentType(ContentType.JSON)
        .header("X-Time-Zone", "Europe/Amsterdam")
        .body(deleteRequest)
        .delete("/v4/schedules/" + robotId)
    .then()
        .statusCode(204);
    
    // Then: 
    // - 2026-05-04 09:00 occurrence → KEPT (< fromDate)
    // - 2026-05-05 09:00 occurrence → REMOVED (>= fromDate)
    // - 2026-05-06 09:00 occurrence → REMOVED (>= fromDate)
}
```

### Phase 4: Testing Checklist

- [ ] Unit tests for `ScheduleService.delete()` with `fromDate`
- [ ] Integration test: Soft delete from future date preserves executions
- [ ] Integration test: Soft delete from past date returns 400
- [ ] Integration test: Soft delete without `fromDate` defaults to NOW
- [ ] Integration test: Single occurrence delete still works (regression)
- [ ] Integration test: **No-op returns 204** (already ended schedule)
- [ ] Integration test: **Query param** `?fromDate=...` works
- [ ] Integration test: **Boundary semantics** (exclusive, occurrences >= fromDate removed)
- [ ] Integration test: **Timezone handling** (fromDate interpreted in robot TZ)
- [ ] Manual test on staging: Create recurring task → Execute → Delete series → Verify executions remain

## 📊 Summary of Results

> *To be completed after implementation*

### ✅ Completed Achievements

- [ ] Soft delete implemented using `end_at` pattern
- [ ] Historical executions preserved
- [ ] Backward compatible (no `fromDate` = delete from NOW)
- [ ] Past date validation working
- [ ] All integration tests passing

## 🚧 Outstanding Issues & Follow-up

### ✅ Resolved Questions (from Review)

1. **Query param support?** 
   - **Answer**: YES - Supporting both `?fromDate=ISO8601` query param AND request body for compatibility with clients that don't support DELETE body.

2. **Boundary semantics?**
   - **Answer**: Exclusive - occurrences `>= fromDate` are removed, `< fromDate` are kept. Documented in Section 4.

3. **No-op notification?**
   - **Answer**: Return 204 for no-op (idempotent). UI can optionally show "series already ended" based on calendar data, no special header needed.

### ⚠️ Open Questions (for Stakeholder)

1. **API Contract Change**: Adding `fromDate` to request body is backward compatible, but should we document this change in API specs (`docs/eve.yaml`)?

2. **Frontend Update**: Does `my.tinybots.academy` need to be updated to pass `fromDate` when user selects a specific date to delete from? Or should it always default to NOW?

3. **Notification**: Should we notify user/admin when a series is soft-deleted vs hard-deleted?
