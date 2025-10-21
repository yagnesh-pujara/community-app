import asyncio
from datetime import datetime, timedelta
import uuid
from app.database import get_supabase


async def seed_database():
    """Seed Supabase with initial data"""
    supabase = get_supabase()
    print("🚀 Starting database seeding...")

    # ======================================================
    # 1. Create Households
    # ======================================================
    print("\n1️⃣  Creating households...")
    households_data = [
        {"flat_no": "A101", "name": "The Johnson Family"},
        {"flat_no": "A102", "name": "The Kim Family"},
        {"flat_no": "B201", "name": "The Singh Family"},
    ]
    households_result = supabase.table("households").insert(households_data).execute()
    household_ids = {row["flat_no"]: row["id"] for row in households_result.data}
    print(f"✅ Created {len(household_ids)} households")

    # ======================================================
    # 2. Create Users
    # ======================================================
    print("\n2️⃣  Creating users...")
    users_data = [
        {
            "email": "john@example.com",
            "phone": "+1555111001",
            "display_name": "John Johnson",
            "household_id": household_ids["A101"],
            "roles": ["resident"],
        },
        {
            "email": "emma@example.com",
            "phone": "+1555111002",
            "display_name": "Emma Johnson",
            "household_id": household_ids["A101"],
            "roles": ["resident"],
        },
        {
            "email": "guard.mike@example.com",
            "phone": "+1555222001",
            "display_name": "Mike Guard",
            "roles": ["guard"],
        },
        {
            "email": "admin.sara@example.com",
            "phone": "+1555333001",
            "display_name": "Sara Admin",
            "roles": ["admin"],
        },
        {
            "email": "minho@example.com",
            "phone": "+821055550001",
            "display_name": "Minho Kim",
            "household_id": household_ids["A102"],
            "roles": ["resident"],
        },
    ]
    users_result = supabase.table("users").insert(users_data).execute()
    user_ids = {u["display_name"]: u["id"] for u in users_result.data}
    print(f"✅ Created {len(user_ids)} users")

    # ======================================================
    # 3. Create Visitors
    # ======================================================
    print("\n3️⃣  Creating visitors...")
    now = datetime.utcnow()
    visitors_data = [
        {
            "name": "Jake Brown",
            "phone": "+1555777001",
            "purpose": "Delivery",
            "host_household_id": household_ids["A101"],
            "status": "approved",
            "approved_by": user_ids["Mike Guard"],
            "approved_at": (now - timedelta(days=1)).isoformat(),
            "checked_in_at": (now - timedelta(hours=23)).isoformat(),
            "checked_out_at": (now - timedelta(hours=22)).isoformat(),
            "scheduled_time": (now - timedelta(hours=25)).isoformat(),
        },
        {
            "name": "Alice White",
            "phone": "+1555777002",
            "purpose": "Guest Visit",
            "host_household_id": household_ids["A102"],
            "status": "pending",
            "scheduled_time": (now + timedelta(hours=2)).isoformat(),
        },
        {
            "name": "Robert Lee",
            "phone": "+1555777003",
            "purpose": "Plumber Service",
            "host_household_id": household_ids["B201"],
            "status": "checked_in",
            "approved_by": user_ids["Mike Guard"],
            "approved_at": (now - timedelta(hours=2)).isoformat(),
            "checked_in_at": (now - timedelta(hours=1)).isoformat(),
            "scheduled_time": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "name": "Lisa Park",
            "phone": "+1555777004",
            "purpose": "Friend Visit",
            "host_household_id": household_ids["A102"],
            "status": "approved",
            "approved_by": user_ids["Sara Admin"],
            "approved_at": (now - timedelta(days=3)).isoformat(),
            "scheduled_time": (now - timedelta(days=2)).isoformat(),
        },
        {
            "name": "David Wu",
            "phone": "+1555777005",
            "purpose": "Courier Delivery",
            "host_household_id": household_ids["A101"],
            "status": "checked_out",
            "approved_by": user_ids["Mike Guard"],
            "approved_at": (now - timedelta(hours=5)).isoformat(),
            "checked_in_at": (now - timedelta(hours=4)).isoformat(),
            "checked_out_at": (now - timedelta(hours=3)).isoformat(),
            "scheduled_time": (now - timedelta(hours=6)).isoformat(),
        },
        {
            "name": "Sophia Singh",
            "phone": "+1555777006",
            "purpose": "Relative Visit",
            "host_household_id": household_ids["B201"],
            "status": "approved",
            "approved_by": user_ids["Sara Admin"],
            "approved_at": (now - timedelta(days=2)).isoformat(),
            "scheduled_time": (now - timedelta(days=3)).isoformat(),
        },
    ]
    visitors_result = supabase.table("visitors").insert(visitors_data).execute()
    visitor_ids = {v["name"]: v["id"] for v in visitors_result.data}
    print(f"✅ Created {len(visitor_ids)} visitors")

    # ======================================================
    # 4. Create Events (Audit Log)
    # ======================================================
    print("\n4️⃣  Creating events...")
    events_data = [
        {
            "type": "visitor_approved",
            "actor_user_id": user_ids["Mike Guard"],
            "subject_id": visitor_ids["Jake Brown"],
            "payload": {"status": "approved", "by": "guard.mike@example.com"},
            "occurred_at": (now - timedelta(days=1)).isoformat(),
        },
        {
            "type": "visitor_checked_in",
            "actor_user_id": user_ids["Mike Guard"],
            "subject_id": visitor_ids["Robert Lee"],
            "payload": {"status": "checked_in"},
            "occurred_at": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "type": "visitor_checked_out",
            "actor_user_id": user_ids["Mike Guard"],
            "subject_id": visitor_ids["David Wu"],
            "payload": {"status": "checked_out"},
            "occurred_at": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "type": "user_created",
            "actor_user_id": user_ids["Sara Admin"],
            "subject_id": user_ids["Minho Kim"],
            "payload": {"role": "resident"},
            "occurred_at": (now - timedelta(days=4)).isoformat(),
        },
    ]
    supabase.table("events").insert(events_data).execute()
    print(f"✅ Created {len(events_data)} events")

    # ======================================================
    # 5. Create Device Tokens
    # ======================================================
    print("\n5️⃣  Creating device tokens...")
    device_tokens = [
        {"user_id": user_ids["John Johnson"], "token": "fcm_token_abc123"},
        {"user_id": user_ids["Emma Johnson"], "token": "fcm_token_def456"},
        {"user_id": user_ids["Mike Guard"], "token": "fcm_token_guard789"},
        {"user_id": user_ids["Sara Admin"], "token": "fcm_token_adminxyz"},
    ]
    supabase.table("device_tokens").insert(device_tokens).execute()
    print(f"✅ Created {len(device_tokens)} device tokens")

    # ======================================================
    # 6. Completion Summary
    # ======================================================
    print("\n" + "=" * 70)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📧 Test Accounts:")
    print("  🏠 Residents:")
    print("     - John Johnson  → john@example.com")
    print("     - Emma Johnson  → emma@example.com")
    print("     - Minho Kim     → minho@example.com")
    print("\n  🛡️ Guards:")
    print("     - Mike Guard    → guard.mike@example.com")
    print("\n  🧑‍💼 Admin:")
    print("     - Sara Admin    → admin.sara@example.com")
    print("\n📋 Visitors:")
    for name, status in [
        ("Jake Brown", "approved"),
        ("Alice White", "pending"),
        ("Robert Lee", "checked_in"),
        ("Lisa Park", "approved"),
        ("David Wu", "checked_out"),
        ("Sophia Singh", "approved"),
    ]:
        print(f"   - {name} ({status})")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(seed_database())
