"""Local SQLite storage for intake answers (injuries + prescribed plan)."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "physx.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS intakes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL,
    plan_text       TEXT NOT NULL,
    generated_plan  TEXT
);

CREATE TABLE IF NOT EXISTS injuries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id    INTEGER NOT NULL REFERENCES intakes(id) ON DELETE CASCADE,
    created_at   TEXT NOT NULL,
    description  TEXT NOT NULL
);
"""


@contextmanager
def connect():
    """A connection that commits on success, rolls back on error, and always closes."""
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
        migrate_injuries(connection)


def migrate_injuries(connection: sqlite3.Connection) -> None:
    """Fold an older body_part/severity/notes injuries table into one description column."""
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(injuries)")}
    if "description" in columns or not columns:
        return
    rows = connection.execute("SELECT * FROM injuries ORDER BY id").fetchall()
    connection.execute("ALTER TABLE injuries RENAME TO injuries_old")
    connection.executescript(SCHEMA)
    connection.executemany(
        "INSERT INTO injuries (intake_id, created_at, description) VALUES (?, ?, ?)",
        [
            (
                row["intake_id"],
                row["created_at"],
                " — ".join(
                    part for part in (row["body_part"], row["severity"], row["notes"]) if part
                ),
            )
            for row in rows
        ],
    )
    connection.execute("DROP TABLE injuries_old")


def save_intake(injuries_text: str, plan_text: str) -> int:
    """Store one intake plus the injuries the user described. Returns the new intake id."""
    init_db()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    injuries_text = (injuries_text or "").strip()
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO intakes (created_at, plan_text) VALUES (?, ?)",
            (now, plan_text),
        )
        intake_id = int(cursor.lastrowid)
        if injuries_text:
            connection.execute(
                "INSERT INTO injuries (intake_id, created_at, description) VALUES (?, ?, ?)",
                (intake_id, now, injuries_text),
            )
    return intake_id


def attach_generated_plan(intake_id: int, plan: dict) -> None:
    """Keep the generated plan next to the intake it came from."""
    with connect() as connection:
        connection.execute(
            "UPDATE intakes SET generated_plan = ? WHERE id = ?",
            (json.dumps(plan, ensure_ascii=False), intake_id),
        )


def list_injuries(intake_id: int | None = None) -> list[dict]:
    init_db()
    with connect() as connection:
        if intake_id is None:
            rows = connection.execute(
                "SELECT * FROM injuries ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM injuries WHERE intake_id = ? ORDER BY id", (intake_id,)
            ).fetchall()
    return [dict(row) for row in rows]


def injuries_text(intake_id: int) -> str:
    """The injuries the user typed for one intake, as a single string."""
    return " ".join(row["description"] for row in list_injuries(intake_id))


def latest_intake() -> dict | None:
    init_db()
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM intakes ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None
