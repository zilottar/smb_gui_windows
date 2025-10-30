"""Wrapper around pysmb for simple SMB operations."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Iterable, List, Optional

from smb.SMBConnection import SMBConnection
from smb.base import SharedFile


class SMBConnectionError(Exception):
    """Raised when SMB connection or operations fail."""


@dataclass
class DirectoryEntry:
    """Simplified representation of a directory entry."""

    filename: str
    is_directory: bool
    file_size: int


class SMBClient:
    """Simple SMB client for listing directories."""

    def __init__(self) -> None:
        self._connection: Optional[SMBConnection] = None

    def connect(
        self,
        server: str,
        share: str,
        username: str,
        password: str,
        domain: Optional[str] = None,
        port: int = 445,
        server_name: Optional[str] = None,
    ) -> None:
        """Connect to the SMB share."""
        if not server or not share:
            raise SMBConnectionError("Сервер и папка должны быть заполнены")

        server_name = server_name or server
        client_name = socket.gethostname()

        connection = SMBConnection(
            username,
            password,
            client_name=client_name,
            remote_name=server_name,
            domain=domain or "",
            use_ntlm_v2=True,
            is_direct_tcp=True,
        )

        try:
            if not connection.connect(server, port):
                raise SMBConnectionError("Не удалось подключиться к SMB серверу")
        except Exception as exc:  # pylint: disable=broad-except
            raise SMBConnectionError(f"Ошибка подключения: {exc}") from exc

        self._connection = connection

    def list_directory(self, share: str, path: str) -> List[DirectoryEntry]:
        """List directory contents for the given path."""
        if not self._connection:
            raise SMBConnectionError("Нет активного подключения")

        normalized_path = self._normalize_path(path)

        try:
            raw_entries: Iterable[SharedFile] = self._connection.listPath(share, normalized_path)
        except Exception as exc:  # pylint: disable=broad-except
            raise SMBConnectionError(f"Не удалось получить список файлов: {exc}") from exc

        entries: List[DirectoryEntry] = []
        for entry in raw_entries:
            if entry.filename in (".", ".."):  # skip parent/current
                continue
            entries.append(
                DirectoryEntry(
                    filename=entry.filename,
                    is_directory=entry.isDirectory,
                    file_size=getattr(entry, "file_size", 0),
                )
            )

        return entries

    def close(self) -> None:
        """Close the SMB connection if open."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:  # pylint: disable=broad-except
                pass
            finally:
                self._connection = None

    def download_file(self, share: str, path: str, local_path: str) -> None:
        """Download a file from the SMB share to the local filesystem."""
        if not self._connection:
            raise SMBConnectionError("Нет активного подключения")

        normalized_path = self._normalize_path(path)

        try:
            with open(local_path, "wb") as file_obj:
                self._connection.retrieveFile(share, normalized_path, file_obj)
        except Exception as exc:  # pylint: disable=broad-except
            raise SMBConnectionError(f"Не удалось скачать файл: {exc}") from exc

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path or path in ("", "/"):
            return "/"
        return path.lstrip("/")
