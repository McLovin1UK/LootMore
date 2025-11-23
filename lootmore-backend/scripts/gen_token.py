import secrets, os, argparse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import User
from app.auth import hash_token

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--tier", default="alpha")
    parser.add_argument("--quota", type=int, default=int(os.getenv("DAILY_QUOTA_DEFAULT", "200")))
    args = parser.parse_args()

    token = "lm_" + args.tier + "_" + secrets.token_urlsafe(12)
    th = hash_token(token)

    db: Session = SessionLocal()
    try:
        user = User(
            email=args.email,
            display_name=args.name,
            token_hash=th,
            tier=args.tier,
            daily_quota=args.quota,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("Created user:")
        print("  id:", user.id)
        print("  tier:", user.tier)
        print("  daily_quota:", user.daily_quota)
        print("\nRAW TOKEN (give to tester once):")
        print(token)

    finally:
        db.close()

if __name__ == "__main__":
    main()
