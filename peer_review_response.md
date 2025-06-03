
# Peer Review Response

This document outlines how each comment from the peer review has been addressed, organized into three categories: Code Review Comments, Schema/API Design Comments, and Product Ideas.

---

## Code Review Comments (Felipe Rotelli)

### **1. Use of PATCH instead of POST for marking a chore complete**
- **Fixed**: Changed the endpoint from `POST` to `PATCH` at `/chores/{chore_id}/complete`.

### **2. Model Validation for Chore Creation**
- **Fixed**: Added `if not chore.chore_name or not chore.due_date or not chore.description:` validation checks.

### **3. Assignment Validation**
- **Fixed**: Validates that at least one assignee is present when creating a chore.

### **4. Replace hardcoded user ID in get_current_user()**
- **Fixed**: Now uses the X-API-Key to look up the user in the database using get_current_user()

### **5. Validate group_id when creating chores**
- **Fixed**: create_chore now verifies that the current user's group_id matches the provided group_id.

### **6. Create new user endpoint**
- **Fixed**:  Added POST /users endpoint to create users with duplicate email validation.

### **7. Move assignment logic to assignments.py**
- **Fixed**: Assignment logic extracted from chores.py to a function in assignments.py.

### **8. Validate user existence in get_user_chores**
- **Fixed**: Now checks if user exists and raises 404 if not.

### **9. Add endpoint to leave a group**
- **Fixed**: Added POST /groups/leave to allow users to set their group_id to NULL

### **10.  Automatically join group after creation**
- **Fixed**: Creator of group is automatically linked to it in create_group.

### **11. Add auth check to join_group and create_group**
- **Fixed**: Both endpoints now require authentication via Depends(get_api_key)

### **12. Track who completed chores and when**
- **Fixed**: mark_chore_complete updates completed_by and completed_at fields in both chores and assignments.

---

## Schema/API Design Comments (Felipe Rotelli)

### **1. Record completion user and timestamp**
- **Fixed**: Added `completed_by` and `completed_at` fields to `chores` and `assignments` tables.
- Updated `mark_chore_complete` to write to these fields.

### **2. Alembic Migration for Completed Fields**
- **Done**: Migration created and committed (though not yet applied).

### **3. Allow duplication of chores**
- **Fixed**: Added `/chores/{chore_id}/duplicate` endpoint with override options for assignees, due date, recurrence.

### **4. Create group summary stats endpoint**
- **Fixed**: Added `/groups/{group_id}/summary` endpoint with breakdown of completions, lateness, top and lowest contributors.

### **5. Nullable values for optional fields**
- **Done**: Fields like `recurrence_pattern`, `completed_by`, and `completed_at` made nullable in schema.

### **6. Optional filtering/sorting for chores assigned to a user**
- **Fixed**: `/users/{user_id}/chores` now supports optional `completed` filtering and `sort_by_due=asc|desc`.

### **7. Consistent invite code join logic**
- **Fixed**: Group join endpoint updated to use `group_name + invite_code` for security and consistency.

### **8. Consistent field naming in responses**
- **Fixed**: Group endpoints now return consistent response format (`GroupResponse` model).

### **9. Add missing indexes**
- **Not done (justified)**: Decided not to add new indexes yet due to small dataset and performance not being a concern.

### **10. Error handling for duplicate group names**
- **Fixed**: Group creation checks for duplicate names and returns 409 if conflict exists.

### **11. Return useful info in GET `/groups/{group_id}/chores`**
- **Fixed**: Endpoint returns `chore_name`, `completed` for better frontend display.

### **12. Error handling for duplicate emails**
- **Fixed**: POST `/users` returns 409 Conflict when email already exists.

---

## Product Ideas (Felipe Rotelli)

### **1. Group leaderboard / user stats endpoint**
- **Fixed**: Implemented via `/groups/{group_id}/summary`, includes `top_contributor` and `lowest_contributor`.

### **2. Chore duplication endpoint**
- **Fixed**: `/chores/{chore_id}/duplicate` allows reusing values, with optional overrides.

### **3. Assign chore to least busy users**
- **Not added (justified)**: Already implemented in `/chores/assign-balanced`, which selects users with fewest active chores.

---

## Code Review comments (Kyle Lin)

- Fixed typos and expanded README with database details.
- Added API specification and example flows to docs.
- Added comments on class properties for clarity (e.g., `recurring`).
- Added missing docstrings for better readability.
- Added user creation endpoint (POST `/users`).
- Improved variable names for clarity (`conn` → `connection`).
- Enhanced response details on chore/user creation (include user_id).
- Returned message when no chores found instead of empty list.
- Added error handling for redundant group joins.
- Added validation in `create_chore` to reject empty assignees list.
- Enforced user-group membership check in `create_chore`.
- Added instructions for running endpoints in the repo.

---

## Test Results (Kyle Lin)

- Prod website was not working; unable to test.
- No example flows available.

---

## Schema/API Design Comments (Kyle Lin)

- Marked redundancy in `completed` field in chores and `completed_by_user` in assignments; recommend consolidating.
- Added `created_by_user_id` field in groups to support authorization.
- Suggested archived chores and users tables to maintain history.
- Enforced uniqueness on invite codes.
- Added timestamps for assignment/chore completion.
- Suggested notifications table to remind users about chores.
- Proposed `ChoreTemplate` table for recurring chores.
- Added tags for chores (e.g., "urgent", "cleaning").
- Added chore archiving feature.
- Added endpoint to list all assignees for a chore.
- Added chore reassignment endpoint.
- Enforced uniqueness constraints on emails.

---

## Product Ideas (Kyle Lin)

- Notifications table to remind users about chores with various flags (assigned, due soon, etc.).
- Recurring chores table to manage common repeated chores like dishwashing or vacuuming.

---

## Code Review (Kyle Fan)

- Added user creation endpoint to create DB entries for new users.
- Updated `auth.py` to query user info from DB rather than placeholders.
- Added error for missing user in `get_current_user` rather than failing silently.
- Added consistent docstrings to all functions.
- Added endpoints in `assignments.py` for creating and completing assignments.
- Suggested tests for error and success cases.
- Added `completed_at` update in `mark_chore_complete`.
- Secured `create_group`, `join_group`, and `mark_chore_complete` endpoints with authentication.
- Added stub admin endpoint for elevated DB changes.
- Fixed Alembic migrations to use `server_default` instead of plain `default`.
- Improved `get_group_stats` aggregation query grouping by user ID and ordering results.

---

## Test Results (Kyle Fan)

- Unable to test:
  - Creating user with duplicate email returns 409 error.
  - Marking others' assignments complete returns 403 error.
  - Viewing stats of other groups returns 403 error.

---

## Schema/API Design (Kyle Fan)

- Proposed `Reminders` and `Reminders_Sent` tables for chore due reminders.
- Suggested many-to-many `Group_Members` table for multiple group memberships.
- Noted missing autoincrement on `chore_id` and user IDs; suggested UUIDs or serial IDs.
- Added `created_at` timestamps with server defaults.
- Added completion timestamps to assignments.
- Enforced email uniqueness.
- Suggested hashing invite codes for uniqueness and collision avoidance.
- Highlighted permission checks for chore completion by other users.
- Proposed leave group function with checks.
- Added group admin and creator fields for membership control.
- Suggested system admin roles for broad management.

---

## Product Ideas (Kyle Fan)

- Implemented reminders workflow with recurrence patterns.
- Suggested separate recurrence pattern table shared by reminders and chores.
