from .db import engine, Base
from . import models  # noqa

def init():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init()
    print("DB tables created.")
