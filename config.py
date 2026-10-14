"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(ROOT_DIR / "data" / "shopping.db")))
    chroma_path: Path = Path(os.getenv("CHROMA_PATH", str(ROOT_DIR / "chroma_db")))
    product_catalog_path: Path = Path(os.getenv("PRODUCT_CATALOG_PATH", str(ROOT_DIR / "data" / "products.csv")))
    faq_path: Path = Path(os.getenv("FAQ_PATH", str(ROOT_DIR / "data" / "faqs" / "faq_laptop.txt")))
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-before-deployment")
    app_env: str = os.getenv("APP_ENV", "development")


settings = Settings()
