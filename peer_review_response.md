
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
