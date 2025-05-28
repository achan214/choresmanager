# Concurrency Control Documentation

This file documents three concurrency issues that would occur in our service if concurrency control were not in place. Each case includes a sequence diagram and the concurrency mechanism we use to prevent it.

## Case 1: Lost Update – Completing the Same Chore

Two users attempt to mark the same chore as complete at the same time. Both read `is_complete = false`, and both write `true`, but one update is lost.

Phenomenon: Lost Update

```mermaid
sequenceDiagram
    participant T1 as Transaction 1
    participant T2 as Transaction 2
    participant DB as Database

    T1->>DB: SELECT is_complete FROM chores WHERE id=1
    T2->>DB: SELECT is_complete FROM chores WHERE id=1
    T1->>DB: UPDATE chores SET is_complete = true WHERE id=1
    T2->>DB: UPDATE chores SET is_complete = true WHERE id=1
```

Solution: Use `SELECT ... FOR UPDATE` to apply row-level locking in the update transaction. This prevents two users from updating the same row concurrently.

## Case 2: Non-Repeatable Read – Checking Unassigned Chores

A user loads the list of unassigned chores. Another user assigns one of them during the transaction. When the first user checks again, the list has changed.

Phenomenon: Non-Repeatable Read

```mermaid
sequenceDiagram
    participant T1 as Transaction 1
    participant T2 as Transaction 2
    participant DB as Database

    T1->>DB: SELECT * FROM chores WHERE assigned_to IS NULL
    T2->>DB: UPDATE chores SET assigned_to = 3 WHERE id=4
    T1->>DB: SELECT * FROM chores WHERE assigned_to IS NULL
```

Solution: Use the `REPEATABLE READ` isolation level to ensure stable reads during the transaction.

## Case 3: Phantom Read – Counting Assigned Chores

A user queries how many chores are assigned to them. Another user inserts a new chore assigned to that user during the transaction, changing the result.

Phenomenon: Phantom Read

```mermaid
sequenceDiagram
    participant T1 as Transaction 1
    participant T2 as Transaction 2
    participant DB as Database

    T1->>DB: SELECT COUNT(*) FROM chores WHERE assigned_to = 5
    T2->>DB: INSERT INTO chores (description, assigned_to) VALUES ("Trash", 5)
    T1->>DB: SELECT COUNT(*) FROM chores WHERE assigned_to = 5
```

Solution: Use the `SERIALIZABLE` isolation level to prevent insertions that would change the result of a repeated query in the same transaction.
