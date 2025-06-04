import random
from faker import Faker
from tqdm import tqdm
from sqlalchemy import text
from src.database import engine

fake = Faker()

NUM_USERS = 100_000
NUM_GROUPS = 10_000
NUM_CHORES = 500_000
NUM_ASSIGNMENTS = 390_000

with engine.begin() as conn:
    # Insert groups
    print("Inserting groups...")
    for i in tqdm(range(1, NUM_GROUPS + 1)):
        conn.execute(
            text("""
                INSERT INTO groups (group_name, created_at, invite_code)
                VALUES (:name, :created_at, :invite_code)
            """),
            {
                "name": f"Group {i}",
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "invite_code": fake.bothify(text='????-####')
            }
        )

    group_ids = [row[0] for row in conn.execute(text("SELECT id FROM groups")).fetchall()]
    print(f"Inserted {len(group_ids)} groups.")

    # Insert users
    print("Inserting users...")
    for i in tqdm(range(NUM_USERS)):
        conn.execute(
            text("""
                INSERT INTO users (username, email, group_id)
                VALUES (:username, :email, :group_id)
            """),
            {
                "username": f"user{i}",
                "email": fake.email(),
                "group_id": random.choice(group_ids)
            }
        )

    user_ids = [row[0] for row in conn.execute(text("SELECT id FROM users")).fetchall()]

    # Insert chores
    print("Inserting chores...")
    for _ in tqdm(range(NUM_CHORES)):
        conn.execute(
            text("""
                INSERT INTO chores (group_id, name, description, due_date, created_by)
                VALUES (:group_id, :name, :desc, :due_date, :created_by)
            """),
            {
                "group_id": random.choice(group_ids),
                "name": fake.job()[:50],
                "desc": fake.sentence(),
                "due_date": fake.date_time_between(start_date='-1y', end_date='now'),
                "created_by": random.choice(user_ids)
            }
        )

    chore_ids = [row[0] for row in conn.execute(text("SELECT id FROM chores")).fetchall()]

    # Insert assignments
    print("Inserting assignments...")
    for _ in tqdm(range(NUM_ASSIGNMENTS)):
        conn.execute(
            text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore, :user, :assigned_at)
            """),
            {
                "chore": random.choice(chore_ids),
                "user": random.choice(user_ids),
                "assigned_at": fake.date_time_between(start_date='-1y', end_date='now')
            }
        )

# Run VACUUM ANALYZE outside of transaction block
with engine.connect() as conn:
    print("🧹 Running VACUUM ANALYZE...")
    conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM ANALYZE"))

print("Fake data generation complete.")
