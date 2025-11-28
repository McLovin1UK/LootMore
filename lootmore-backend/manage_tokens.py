import argparse
import os
import string
import sys
from typing import Iterable

from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
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


def create_token(db: Session) -> None:
    salt = os.getenv("LOOTMORE_TOKEN_SALT")
    if not salt:
        raise RuntimeError("LOOTMORE_TOKEN_SALT environment variable is not set")

    raw_token = generate_token()
    token_hash = hash_token(raw_token, salt)

    token = ApiToken(token_hash=token_hash, daily_quota=DAILY_QUOTA_DEFAULT)
    db.add(token)
    db.commit()
    db.refresh(token)
    print(f"Created token (id={token.id}): {raw_token}")


def list_tokens(db: Session) -> None:
    tokens = db.query(ApiToken).all()
    if not tokens:
        print("No tokens found")
        return
    print_tokens(tokens)


def revoke_token(db: Session, token_id: int) -> None:
    token = db.get(ApiToken, token_id)
    if not token:
        print(f"Token with id {token_id} not found")
        return
    db.delete(token)
    db.commit()
    print(f"Revoked token {token_id}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Manage Lootmore API tokens")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("create", help="Create a new API token")
    subparsers.add_parser("list", help="List API tokens")

    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API token by id")
    revoke_parser.add_argument("id", type=int, help="Token id")

    args = parser.parse_args(argv)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.command == "create":
            create_token(db)
        elif args.command == "list":
            list_tokens(db)
        elif args.command == "revoke":
            revoke_token(db, args.id)
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
