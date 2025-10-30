"""Main entry point for the SMB GUI client."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Optional

from .auth_window import AuthWindow
from .file_browser_window import FileBrowserWindow
from .smb_client import SMBClient, SMBConnectionError


def run_app() -> None:
    """Launch the SMB GUI application."""
    root = tk.Tk()
    root.withdraw()  # hide root window; windows created by classes

    client = SMBClient()

    def on_connect(
        server: str,
        share: str,
        username: str,
        password: str,
        domain: Optional[str],
        port: int,
        server_name: Optional[str],
    ) -> None:
        try:
            client.connect(
                server=server,
                share=share,
                username=username,
                password=password,
                domain=domain,
                port=port,
                server_name=server_name,
            )
        except SMBConnectionError as exc:
            messagebox.showerror("Ошибка подключения", str(exc))
            return

        auth_window.hide()
        FileBrowserWindow(
            master=root,
            smb_client=client,
            share=share,
            on_close=lambda: (client.close(), root.destroy()),
        )

    auth_window = AuthWindow(master=root, on_connect=on_connect)
    root.mainloop()


if __name__ == "__main__":
    run_app()
