import argparse
import os
import string
import sys
from typing import Iterable

from sqlalchemy.orm import Session

from database import SessionLocal
from models import ApiToken, DAILY_QUOTA_DEFAULT
from security import hash_token


ALPHABET = string.ascii_letters + string.digits


def generate_token(length: int = 24) -> str:
    rng = os.urandom
    # use byte-based randomness to avoid relying on global secrets module
    chars = []
    for _ in range(length):
        chars.append(ALPHABET[rng(1)[0] % len(ALPHABET)])
    return "".join(chars)


def print_tokens(tokens: Iterable[ApiToken]) -> None:
    print(f"{'ID':<6}{'HASH':<20}{'QUOTA':<12}{'USED':<8}")
    for token in tokens:
        short_hash = (token.token_hash or "")[:16]
        print(f"{token.id:<6}{short_hash:<20}{token.daily_quota:<12}{token.used_today:<8}")


def create_token_entry(db: Session, daily_quota: int | None = None) -> tuple[ApiToken, str]:
    salt = os.getenv("LOOTMORE_TOKEN_SALT")
    if not salt:
        raise RuntimeError("LOOTMORE_TOKEN_SALT environment variable is not set")

    raw_token = generate_token()
    token_hash = hash_token(raw_token, salt)

    token = ApiToken(token_hash=token_hash, daily_quota=daily_quota or DAILY_QUOTA_DEFAULT)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token, raw_token


def create_token(db: Session, daily_quota: int | None = None) -> None:
    token, raw_token = create_token_entry(db, daily_quota)
    print(f"Created token (id={token.id}): {raw_token}")


def list_tokens(db: Session) -> None:
    tokens = db.query(ApiToken).all()
    if not tokens:
        print("No tokens found")
        return
    print_tokens(tokens)


def revoke_token(db: Session, token_id: int) -> bool:
    token = db.get(ApiToken, token_id)
    if not token:
        print(f"Token with id {token_id} not found")
        return False
    db.delete(token)
    db.commit()
    print(f"Revoked token {token_id}")
    return True


def update_quota(db: Session, token_id: int, daily_quota: int) -> bool:
    token = db.get(ApiToken, token_id)
    if not token:
        print(f"Token with id {token_id} not found")
        return False
    token.daily_quota = daily_quota
    db.commit()
    print(f"Updated token {token_id} quota to {daily_quota}")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Manage Lootmore API tokens")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new API token")
    create_parser.add_argument("--quota", type=int, help="Daily quota for the token", default=None)
    subparsers.add_parser("list", help="List API tokens")

    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API token by id")
    revoke_parser.add_argument("id", type=int, help="Token id")

    update_parser = subparsers.add_parser("update", help="Update token quota")
    update_parser.add_argument("id", type=int, help="Token id")
    update_parser.add_argument("quota", type=int, help="New daily quota")

    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if args.command == "create":
            create_token(db, args.quota)
        elif args.command == "list":
            list_tokens(db)
        elif args.command == "revoke":
            revoke_token(db, args.id)
        elif args.command == "update":
            update_quota(db, args.id, args.quota)
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
