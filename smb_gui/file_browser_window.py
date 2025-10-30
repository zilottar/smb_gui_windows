"""File browser window for SMB shares."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from .smb_client import SMBClient, SMBConnectionError


class FileBrowserWindow(tk.Toplevel):
    """Window that displays files and folders for a connected SMB share."""

    def __init__(
        self,
        master: tk.Misc,
        smb_client: SMBClient,
        share: str,
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master)
        self.title(f"SMB Клиент - {share}")
        self.geometry("600x400")

        self._client = smb_client
        self._share = share
        self._on_close = on_close
        self._current_path = "/"

        self.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        self._path_label = ttk.Label(toolbar, text=self._current_path)
        self._path_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        up_button = ttk.Button(toolbar, text="Вверх", command=self._go_up)
        up_button.pack(side=tk.RIGHT)

        self._tree = ttk.Treeview(self, columns=("name", "type", "size"), show="headings")
        self._tree.heading("name", text="Имя")
        self._tree.heading("type", text="Тип")
        self._tree.heading("size", text="Размер (байт)")
        self._tree.column("name", width=300)
        self._tree.column("type", width=80, anchor=tk.CENTER)
        self._tree.column("size", width=120, anchor=tk.E)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._tree.bind("<Double-1>", self._on_item_double_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))

        self._download_button = ttk.Button(
            actions,
            text="Скачать…",
            command=self._download_selected,
            state=tk.DISABLED,
        )
        self._download_button.pack(side=tk.RIGHT)

    def _populate(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        try:
            entries = self._client.list_directory(self._share, self._current_path)
        except SMBConnectionError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        for entry in entries:
            entry_type = "Папка" if entry.is_directory else "Файл"
            size = "" if entry.is_directory else str(entry.file_size)
            self._tree.insert(
                "",
                tk.END,
                iid=entry.filename,
                values=(entry.filename, entry_type, size),
            )

        self._path_label.configure(text=self._current_path)
        self._download_button.configure(state=tk.DISABLED)

    def _on_item_double_click(self, event: tk.Event[tk.Misc]) -> None:
        selection = self._tree.selection()
        if not selection:
            return

        item_id = selection[0]
        item = self._tree.item(item_id)
        item_type = item["values"][1]

        if item_type == "Папка":
            self._current_path = self._join_path(self._current_path, item_id)
            self._populate()
        else:
            self._download_selected()

    def _on_selection_change(self, _event: tk.Event[tk.Misc]) -> None:
        selection = self._tree.selection()
        if not selection:
            self._download_button.configure(state=tk.DISABLED)
            return

        item_id = selection[0]
        item = self._tree.item(item_id)
        item_type = item["values"][1]
        if item_type == "Файл":
            self._download_button.configure(state=tk.NORMAL)
        else:
            self._download_button.configure(state=tk.DISABLED)

    def _go_up(self) -> None:
        if self._current_path in ("/", ""):
            return
        parent_path = "/".join(self._current_path.rstrip("/").split("/")[:-1])
        if not parent_path:
            parent_path = "/"
        self._current_path = parent_path
        self._populate()

    def _join_path(self, base: str, name: str) -> str:
        if base in ("", "/"):
            return f"/{name.strip('/')}"
        return f"{base.rstrip('/')}/{name.strip('/')}"

    def _download_selected(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return

        item_id = selection[0]
        item = self._tree.item(item_id)
        item_type = item["values"][1]
        if item_type != "Файл":
            return

        remote_path = self._join_path(self._current_path, item_id)
        target_path = filedialog.asksaveasfilename(
            title="Сохранить файл как",
            initialfile=item_id,
        )
        if not target_path:
            return

        try:
            self._client.download_file(self._share, remote_path, target_path)
        except SMBConnectionError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        messagebox.showinfo("Готово", f"Файл сохранён: {target_path}")

    def _handle_close(self) -> None:
        if self._on_close:
            self._on_close()
        self.destroy()
