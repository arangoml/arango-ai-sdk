"""Load a local ``.env`` so integration tests can use real endpoints.

CI does not ship this file. Copy ``.env.example`` to ``.env`` and fill in
values. The file is gitignored.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
