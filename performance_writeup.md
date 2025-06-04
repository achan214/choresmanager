Performance Writeup

1. Fake Data Modeling
Data generation script: generate_fake_data.py

Final row counts:

groups: 10,001 rows

users: 100,000 rows

chores: 500,000 rows

assignments: 390,000 rows

We chose this distribution because each group typically contains multiple users, and each user is expected to have several chores. With 10,000+ groups and 100,000 users, we expect our service to support large apartment complexes or universities with shared living arrangements. The volume of 500,000 chores and 390,000 assignments mimics the workload of long-term, daily-use behavior over time (e.g., daily, weekly, recurring tasks). This level of scaling ensures that we can simulate real production-like load and observe performance under high usage.

2. Endpoint Performance Results
Each endpoint was tested using Swagger UI after generating the data. Results below are execution times (in milliseconds):

Endpoint	Execution Time (ms)
POST /chores/	51 ms
POST /chores/assign-balanced	64 ms
POST /chores/reminders/send	103 ms (slowest)
PATCH /chores/{chore_id}/archive	31 ms
POST /chores/{chore_id}/duplicate	59 ms

Slowest Endpoint: POST /chores/reminders/send

3. Performance Tuning
Original EXPLAIN ANALYZE
sql
Copy
Edit
SELECT u.id as user_id, u.username, c.id as chore_id, c.name, c.due_date
FROM chores c
JOIN assignments a ON c.id = a.chore_id
JOIN users u ON a.user_id = u.id
JOIN groups g ON c.group_id = g.id
WHERE g.group_name = 'Room101'
  AND c.completed = false
  AND c.archived = false
  AND c.due_date BETWEEN NOW() AND NOW() + INTERVAL '48 hours';
Before Indexing:

Execution time: ~93.5–95.3 ms

Execution plan: Heavy use of Parallel Seq Scan on chores and assignments

Problem: No indexes meant full table scans with high cost (e.g. cost=13969.12..19358.64)

Indexes Added

-- Fast lookup for group by name
CREATE INDEX IF NOT EXISTS idx_groups_group_name ON groups(group_name);

-- Improve filtering on upcoming chores
CREATE INDEX IF NOT EXISTS idx_chores_due_date_completed_archived
  ON chores(due_date)
  WHERE completed = false AND archived = false;

-- Help with JOIN between chores and assignments
CREATE INDEX IF NOT EXISTS idx_assignments_chore_id ON assignments(chore_id);

-- Help JOIN on users
CREATE INDEX IF NOT EXISTS idx_assignments_user_id ON assignments(user_id);
EXPLAIN ANALYZE After Indexes
Execution time: 0.186–0.188 ms

Used:

idx_groups_group_name

idx_chores_due_date_completed_archived

idx_assignments_chore_id

Join operations reduced from full table scans to efficient Index Scans and Bitmap Heap Scans

Performance Result:
The query is now lightning-fast (under 1 ms), with dramatic improvement from the original 95 ms. The indexes are highly effective, and this performance is acceptable for production-scale usage.