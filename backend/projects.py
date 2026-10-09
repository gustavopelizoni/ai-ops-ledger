"""One local directory per project; cwd is the technical session identity."""

from __future__ import annotations

import ntpath
import posixpath
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath


def path_key(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Informe a pasta local.")
    windows = bool(re.match(r"^[A-Za-z]:[/\\]", value) or value.startswith("\\\\"))
    if windows:
        path = PureWindowsPath(value)
        if not path.is_absolute():
            raise ValueError("Informe um caminho absoluto.")
        return "w:" + ntpath.normpath(str(path)).rstrip("\\").casefold()
    path = PurePosixPath(value)
    if not path.is_absolute():
        raise ValueError("Informe um caminho absoluto.")
    return "p:" + posixpath.normpath(str(path)).rstrip("/")


def resolve(cwd: str, projects: list[dict]) -> dict | None:
    try:
        target = path_key(cwd)
    except ValueError:
        return None
    separator = "\\" if target.startswith("w:") else "/"
    matches = [
        project for project in projects
        if target == project["caminho_key"]
        or target.startswith(project["caminho_key"].rstrip(separator) + separator)
    ]
    return max(matches, key=lambda project: len(project["caminho_key"]), default=None)


def public(project: dict) -> dict:
    return {key: project[key] for key in
            ("id", "nome", "caminho_local", "arquivado", "criado_em", "atualizado_em")}


def list_all(con: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in con.execute(
        "SELECT * FROM projeto ORDER BY arquivado, nome COLLATE NOCASE"
    )]


def get(con: sqlite3.Connection, project_id: int) -> dict | None:
    row = con.execute("SELECT * FROM projeto WHERE id = ?", (project_id,)).fetchone()
    return dict(row) if row else None


def save(con: sqlite3.Connection, *, nome: str, caminho_local: str,
         project_id: int | None = None) -> dict:
    name = nome.strip()
    if not name:
        raise ValueError("Informe o nome do projeto.")
    path = caminho_local.strip()
    key = path_key(path)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if project_id is None:
        cursor = con.execute(
            "INSERT INTO projeto (nome, caminho_local, caminho_key, criado_em, atualizado_em) "
            "VALUES (?, ?, ?, ?, ?)", (name, path, key, now, now)
        )
        project_id = int(cursor.lastrowid)
    else:
        con.execute(
            "UPDATE projeto SET nome = ?, caminho_local = ?, caminho_key = ?, "
            "atualizado_em = ? WHERE id = ?", (name, path, key, now, project_id)
        )
    result = get(con, project_id)
    assert result is not None
    return public(result)
