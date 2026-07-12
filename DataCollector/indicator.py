import tkinter as tk
import threading
import time


class LiveIndicator:
    """
    Tiny always-on-top, click-through square in the top-right corner.
    Green = collector healthy. Red = poll error detected.
    """

    SIZE = 14
    MARGIN = 10

    def __init__(self, is_alive_callback):
        self._is_alive_callback = is_alive_callback
        self._root = None
        self._canvas = None
        self._dot = None
        self._running = False

    def _setup_window(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.85)

        screen_width = self._root.winfo_screenwidth()
        x = screen_width - self.SIZE - self.MARGIN
        y = self.MARGIN
        self._root.geometry(f"{self.SIZE}x{self.SIZE}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=self.SIZE, height=self.SIZE,
            highlightthickness=0, bg="black"
        )
        self._canvas.pack()
        self._dot = self._canvas.create_oval(2, 2, self.SIZE - 2, self.SIZE - 2, fill="green")

        # Apply click-through after mainloop starts — winfo_id() needs the window mapped.
        # tkinter's -alpha already sets WS_EX_LAYERED; we only add WS_EX_TRANSPARENT.
        self._root.after(200, self._apply_click_through)

    def _apply_click_through(self):
        try:
            import win32gui
            import win32con

            hwnd = self._root.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                hwnd, win32con.GWL_EXSTYLE,
                style | win32con.WS_EX_TRANSPARENT
            )
        except Exception as e:
            print(f"[Indicator] Could not set click-through: {e}")

    def _update_loop(self):
        while self._running:
            try:
                color = "green" if self._is_alive_callback() else "red"
                self._canvas.itemconfig(self._dot, fill=color)
            except Exception:
                pass
            time.sleep(2)

    def start(self):
        self._running = True
        self._setup_window()
        threading.Thread(target=self._update_loop, daemon=True).start()
        self._root.mainloop()

    def stop(self):
        self._running = False
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass
