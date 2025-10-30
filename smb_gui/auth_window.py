"""Authentication window for SMB GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional


class AuthWindow(tk.Toplevel):
    """Window that collects SMB credentials from the user."""

    def __init__(
        self,
        master: tk.Misc,
        on_connect: Callable[
            [str, str, str, str, Optional[str], int, Optional[str]], None
        ],
    ) -> None:
        super().__init__(master)
        self.title("SMB Клиент - Авторизация")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._on_connect = on_connect

        self._server_var = tk.StringVar()
        self._server_name_var = tk.StringVar()
        self._share_var = tk.StringVar()
        self._username_var = tk.StringVar()
        self._password_var = tk.StringVar()
        self._domain_var = tk.StringVar()
        self._port_var = tk.StringVar(value="445")

        self._build_ui()

        self.grab_set()
        self.focus()

    def _build_ui(self) -> None:
        padding = {"padx": 10, "pady": 5}

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Сервер (IP / DNS):").grid(row=0, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self._server_var, width=30).grid(
            row=0, column=1, **padding
        )

        ttk.Label(frame, text="Имя сервера (опционально):").grid(
            row=1, column=0, sticky="w", **padding
        )
        ttk.Entry(frame, textvariable=self._server_name_var, width=30).grid(
            row=1, column=1, **padding
        )

        ttk.Label(frame, text="Папка (share):").grid(row=2, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self._share_var, width=30).grid(
            row=2, column=1, **padding
        )

        ttk.Label(frame, text="Имя пользователя:").grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self._username_var, width=30).grid(
            row=3, column=1, **padding
        )

        ttk.Label(frame, text="Пароль:").grid(row=4, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self._password_var, width=30, show="*").grid(
            row=4, column=1, **padding
        )

        ttk.Label(frame, text="Домен / Рабочая группа:").grid(
            row=5, column=0, sticky="w", **padding
        )
        ttk.Entry(frame, textvariable=self._domain_var, width=30).grid(
            row=5, column=1, **padding
        )

        ttk.Label(frame, text="Порт:").grid(row=6, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self._port_var, width=30).grid(
            row=6, column=1, **padding
        )

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))

        connect_button = ttk.Button(button_frame, text="Подключиться", command=self._handle_connect)
        connect_button.grid(row=0, column=0, padx=5)

        cancel_button = ttk.Button(button_frame, text="Выход", command=self._on_close)
        cancel_button.grid(row=0, column=1, padx=5)

        self.bind("<Return>", lambda event: self._handle_connect())

    def _handle_connect(self) -> None:
        try:
            port = int(self._port_var.get())
        except ValueError:
            messagebox.showerror("Некорректный порт", "Порт должен быть числом")
            return

        self._on_connect(
            self._server_var.get().strip(),
            self._share_var.get().strip(),
            self._username_var.get().strip(),
            self._password_var.get(),
            self._domain_var.get().strip() or None,
            port,
            self._server_name_var.get().strip() or None,
        )

    def _on_close(self) -> None:
        self.grab_release()
        self.master.destroy()

    def hide(self) -> None:
        """Hide the window once authenticated."""
        self.withdraw()
