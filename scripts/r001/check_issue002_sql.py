#!/usr/bin/env python3
"""Host-SQL preflight against pinned Yomotsu; never reports Android runtime PASS."""
import argparse
from pathlib import Path
import re
import sqlite3
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    pinned = "0fb80c439ef816eeb50674f1b90af39918b176d8"
    actual = subprocess.check_output(
        ["git", "-C", str(args.baseline), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != pinned:
        raise SystemExit(f"Wrong baseline: {actual}")
    sql_root = Path(__file__).resolve().parents[2] / "spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi"
    migration = (sql_root / "migrations/14.sqm").read_text()
    mangas = (args.baseline / "data/src/main/sqldelight/tachiyomi/data/mangas.sq").read_text()
    mangas = "CREATE TABLE mangas(" + mangas.split("CREATE TABLE mangas(", 1)[1].split(");", 1)[0] + ");"
    mangas = re.sub(r" AS (?:List<String>|UpdateStrategy|JsonObject|Boolean)", "", mangas)
    with sqlite3.connect(":memory:") as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(mangas)
        db.executescript(migration)
        columns = [row for row in db.execute("PRAGMA table_info(mangas)") if row[3] and row[4] is None]
        names = ",".join(row[1] for row in columns)
        placeholders = ",".join("?" for _ in columns)
        for manga_id in (10, 20, 30):
            values = [manga_id if row[1] == "_id" else ("fixture" if "TEXT" in row[2] else 0) for row in columns]
            db.execute(f"INSERT INTO mangas({names}) VALUES ({placeholders})", values)
        for manga_id in (10, 20, 30):
            db.execute(
                "INSERT INTO merged VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (manga_id, manga_id == 10, 1, 1, manga_id, 0, 30, "merged://10-20", manga_id, f"manga/{manga_id}", manga_id),
            )
        db.execute("DELETE FROM merged WHERE _id=10")
        assert db.execute("SELECT _id FROM mangas WHERE _id=30").fetchone() == (30,)
        assert db.execute("SELECT manga_id FROM merged WHERE merge_id=30 AND manga_id=20").fetchone() == (20,)
        print("REMOVE_ONE_REFERENCE_SQLITE_PASS")
        db.execute("DELETE FROM mangas WHERE _id=20")
        assert db.execute("SELECT manga_id FROM merged WHERE _id=20").fetchone() == (None,)
        assert db.execute("SELECT _id FROM mangas WHERE _id=30").fetchone() == (30,)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        print("REMOVE_CHILD_ROW_SET_NULL_SQLITE_PASS")
    print(f"HOST_SQLITE_ONLY_NOT_ANDROID_RUNTIME; sqlite={sqlite3.sqlite_version}")


if __name__ == "__main__":
    main()
