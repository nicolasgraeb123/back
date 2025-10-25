import os
from models import Base
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

conn_string='postgresql://neondb_owner:npg_4HEr2hJpyVSP@ep-rough-leaf-a9dyf9vg-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require'
database_url = os.getenv("DATABASE_URL", conn_string)

if not database_url:
        raise RuntimeError(
            "Brak zmiennej środowiskowej DATABASE_URL, np.: "
            "export DATABASE_URL='postgresql+psycopg://user:pass@localhost:5432/mydb'"
        )

# Konwersja dla Heroku - postgres:// -> postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url, echo=True, future=True)
Base.metadata.create_all(engine)
print("✅ Tabele zostały utworzone.")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


