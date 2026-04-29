import customtkinter as ctk
import pyperclip
import random
import string
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":          "#080b14",
    "surface":     "#0f1320",
    "surface2":    "#161b2e",
    "surface3":    "#1e2540",
    "accent":      "#6c8fff",
    "accent2":     "#a78bfa",
    "accent_glow": "#3d5adb",
    "success":     "#34d399",
    "warning":     "#fbbf24",
    "danger":      "#f87171",
    "text":        "#f0f4ff",
    "text_dim":    "#8892b0",
    "text_faint":  "#3d4a6b",
    "border":      "#1e2a45",
    "border2":     "#2a3760",
}

FONT_MONO = "Courier New"
FONT_UI   = "Segoe UI" if os.name == "nt" else "SF Pro Display"

W, H = 780, 780


class PasswordLogic:
    SIMILAR = "O0l1Ii|"

    @staticmethod
    def generate(length, use_upper, use_lower, use_digits, use_symbols, avoid_similar):
        pool, guaranteed = "", []
        rng = random.SystemRandom()

        def filtered(chars):
            return "".join(c for c in chars if c not in PasswordLogic.SIMILAR) if avoid_similar else chars

        if use_upper:
            ch = filtered(string.ascii_uppercase)
            pool += ch; guaranteed.append(rng.choice(ch))
        if use_lower:
            ch = filtered(string.ascii_lowercase)
            pool += ch; guaranteed.append(rng.choice(ch))
        if use_digits:
            ch = filtered(string.digits)
            pool += ch; guaranteed.append(rng.choice(ch))
        if use_symbols:
            ch = "!@#$%^&*()-_=+[]{}|;:,.<>?"
            pool += ch; guaranteed.append(rng.choice(ch))

        if not pool:
            raise ValueError("Enable at least one character type.")

        rest = [rng.choice(pool) for _ in range(length - len(guaranteed))]
        chars = guaranteed + rest
        rng.shuffle(chars)
        return "".join(chars)

    @staticmethod
    def strength(pw):
        s = 0
        if len(pw) >= 10: s += 1
        if len(pw) >= 16: s += 1
        if len(pw) >= 24: s += 1
        if any(c in string.ascii_uppercase for c in pw): s += 1
        if any(c in string.ascii_lowercase for c in pw): s += 1
        if any(c in string.digits for c in pw): s += 1
        if any(c in string.punctuation for c in pw): s += 1
        if s <= 3:  return "Weak",   C["danger"],  1
        if s <= 5:  return "Medium", C["warning"], 2
        return              "Strong", C["success"], 3


class AnimatedButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orig_fg = kwargs.get("fg_color", C["accent"])
        self.bind("<ButtonPress-1>",   self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _press(self, _=None):
        self.configure(fg_color=C["accent_glow"])

    def _release(self, _=None):
        self.after(120, lambda: self.configure(fg_color=self._orig_fg))


class ToggleChip(ctk.CTkFrame):
    def __init__(self, parent, label, icon, default=True, **kwargs):
        super().__init__(parent,
                         fg_color=C["surface3"] if default else C["surface2"],
                         corner_radius=22, cursor="hand2", **kwargs)
        self.var = ctk.BooleanVar(value=default)

        self._icon_lbl = ctk.CTkLabel(
            self, text=icon, font=ctk.CTkFont(size=13),
            text_color=C["accent"] if default else C["text_faint"],
            fg_color="transparent", width=20)
        self._icon_lbl.pack(side="left", padx=(8, 2), pady=7)

        self._text_lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            text_color=C["accent"] if default else C["text_dim"],
            fg_color="transparent")
        self._text_lbl.pack(side="left", padx=(0, 10), pady=7)

        for w in (self, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        new = not self.var.get()
        self.var.set(new)
        self.configure(fg_color=C["surface3"] if new else C["surface2"])
        self._icon_lbl.configure(text_color=C["accent"] if new else C["text_faint"])
        self._text_lbl.configure(text_color=C["accent"] if new else C["text_dim"])

    def get(self):
        return self.var.get()


class StrengthMeter(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._segs = []
        for i in range(3):
            seg = ctk.CTkFrame(self, height=5, corner_radius=3, fg_color=C["surface3"])
            seg.grid(row=0, column=i, padx=3, sticky="ew")
            self.columnconfigure(i, weight=1)
            self._segs.append(seg)
        self._lbl = ctk.CTkLabel(self, text="",
                                  font=ctk.CTkFont(family=FONT_UI, size=11, weight="bold"),
                                  text_color=C["text_dim"], fg_color="transparent")
        self._lbl.grid(row=0, column=3, padx=(10, 0))

    def update(self, level, color, label):
        for i, seg in enumerate(self._segs):
            seg.configure(fg_color=color if i < level else C["surface3"])
        self._lbl.configure(text=label, text_color=color)

    def reset(self):
        for seg in self._segs:
            seg.configure(fg_color=C["surface3"])
        self._lbl.configure(text="", text_color=C["text_dim"])


class PasswordGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Password Generator")
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self._toast_job = None
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - W) // 2
        y  = (sh - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")
        self._build()

    def _build(self):
        self._build_header()
        self.main = ctk.CTkFrame(self, fg_color=C["bg"])
        self.main.pack(fill="both", expand=True, padx=20, pady=(6, 12))
        self._build_length_card()
        self._build_charset_card()
        self._build_output_card()
        self._build_actions_card()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w", x=20)
        ctk.CTkLabel(inner, text="🔐",
                     font=ctk.CTkFont(size=20),
                     fg_color="transparent", text_color=C["accent"]).pack(side="left")
        ctk.CTkLabel(inner, text="  Password Generator",
                     font=ctk.CTkFont(family=FONT_UI, size=17, weight="bold"),
                     fg_color="transparent", text_color=C["text"]).pack(side="left")

        ctk.CTkLabel(hdr, text="BY XCYBERSPY",
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     fg_color="transparent",
                     text_color=C["text_dim"]).place(relx=1, rely=0.5, anchor="e", x=-20)

        ctk.CTkFrame(hdr, height=1, fg_color=C["border"]).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1)

    def _card(self, title, icon):
        outer = ctk.CTkFrame(self.main, fg_color=C["surface"], corner_radius=14,
                              border_width=1, border_color=C["border"])
        outer.pack(fill="x", pady=5)

        title_row = ctk.CTkFrame(outer, fg_color="transparent")
        title_row.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(title_row, text=icon, font=ctk.CTkFont(size=14),
                     text_color=C["accent"], fg_color="transparent").pack(side="left")
        ctk.CTkLabel(title_row, text=f"  {title}",
                     font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
                     text_color=C["text"], fg_color="transparent").pack(side="left")

        ctk.CTkFrame(outer, height=1, fg_color=C["border"]).pack(
            fill="x", padx=16, pady=(8, 0))

        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(8, 12))
        return body

    def _build_length_card(self):
        body = self._card("Password Length", "📏")

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(top, text="Characters",
                     font=ctk.CTkFont(family=FONT_UI, size=12),
                     text_color=C["text_dim"], fg_color="transparent").pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=C["surface3"], corner_radius=8, width=46, height=28)
        badge.pack(side="right")
        badge.pack_propagate(False)
        self.len_label = ctk.CTkLabel(badge, text="16",
                                       font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                                       text_color=C["accent"], fg_color="transparent")
        self.len_label.place(relx=0.5, rely=0.5, anchor="center")

        self.slider = ctk.CTkSlider(
            body, from_=6, to=64, number_of_steps=58,
            command=self._on_slider, height=14,
            button_color=C["accent"],
            button_hover_color=C["accent2"],
            progress_color=C["accent"],
            fg_color=C["surface3"])
        self.slider.set(16)
        self.slider.pack(fill="x", pady=(0, 4))

        tick_row = ctk.CTkFrame(body, fg_color="transparent")
        tick_row.pack(fill="x")
        for v in ["*", "**", "***", "****", "*****"]:
            ctk.CTkLabel(tick_row, text=v,
                         font=ctk.CTkFont(family=FONT_MONO, size=9),
                         text_color=C["text_faint"],
                         fg_color="transparent").pack(side="left", expand=True)

    def _build_charset_card(self):
        body = self._card("Character Sets", "🔡")

        chips_row = ctk.CTkFrame(body, fg_color="transparent")
        chips_row.pack(fill="x", pady=(0, 12))

        self.ch_upper   = ToggleChip(chips_row, "ABC", "🔠", default=True)
        self.ch_lower   = ToggleChip(chips_row, "abc", "🔡", default=True)
        self.ch_digits  = ToggleChip(chips_row, "123", "🔢", default=True)
        self.ch_symbols = ToggleChip(chips_row, "!@#", "✦",  default=False)
        for chip in (self.ch_upper, self.ch_lower, self.ch_digits, self.ch_symbols):
            chip.pack(side="left", padx=(0, 8))

        ctk.CTkFrame(body, height=1, fg_color=C["border"]).pack(fill="x", pady=(4, 10))

        self.avoid_var = ctk.BooleanVar(value=False)
        avoid_row = ctk.CTkFrame(body, fg_color="transparent")
        avoid_row.pack(fill="x")
        ctk.CTkLabel(avoid_row, text="⚠️", font=ctk.CTkFont(size=14),
                     fg_color="transparent", text_color=C["warning"]).pack(side="left")
        ctk.CTkLabel(avoid_row, text="  Avoid ambiguous characters  (O, 0, l, 1, I)",
                     font=ctk.CTkFont(family=FONT_UI, size=13),
                     text_color=C["text_dim"], fg_color="transparent").pack(side="left")
        ctk.CTkSwitch(avoid_row, text="", variable=self.avoid_var,
                       width=46, height=22,
                       button_color=C["accent"],
                       button_hover_color=C["accent2"],
                       progress_color=C["accent"]).pack(side="right")

    def _build_output_card(self):
        body = self._card("Generated Password", "🔑")

        pw_bg = ctk.CTkFrame(body, fg_color=C["surface2"], corner_radius=12,
                              border_width=1, border_color=C["border2"])
        pw_bg.pack(fill="x", pady=(0, 12))

        self.pw_var = ctk.StringVar()
        self.pw_entry = ctk.CTkEntry(
            pw_bg, textvariable=self.pw_var,
            font=ctk.CTkFont(family=FONT_MONO, size=15, weight="bold"),
            text_color=C["text"], fg_color="transparent",
            border_width=0, height=44, justify="center",
            state="readonly")
        self.pw_entry.pack(fill="x", padx=16, pady=2)

        strength_row = ctk.CTkFrame(body, fg_color="transparent")
        strength_row.pack(fill="x")
        ctk.CTkLabel(strength_row, text="STRENGTH",
                     font=ctk.CTkFont(family=FONT_UI, size=10, weight="bold"),
                     text_color=C["text_faint"], fg_color="transparent").pack(side="left")
        self.meter = StrengthMeter(strength_row)
        self.meter.pack(side="right")

    def _build_actions_card(self):
        body = self._card("Actions", "⚡")

        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x")
        row1.columnconfigure(0, weight=2)
        row1.columnconfigure(1, weight=1)
        row1.columnconfigure(2, weight=1)

        self.gen_btn = AnimatedButton(
            row1, text="⚡   Generate Password",
            command=self._generate,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=C["accent"], hover_color=C["accent2"],
            text_color=C["bg"], height=40, corner_radius=12)
        self.gen_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(row1, text="📋  Copy", command=self._copy,
                       font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
                       fg_color=C["surface3"], hover_color=C["border2"],
                       text_color=C["text"], height=40, corner_radius=12,
                       border_width=1, border_color=C["border2"]
                       ).grid(row=0, column=1, padx=(0, 8), sticky="ew")

        ctk.CTkButton(row1, text="✕  Clear", command=self._clear,
                       font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
                       fg_color=C["surface3"], hover_color=C["border2"],
                       text_color=C["text_dim"], height=40, corner_radius=12,
                       border_width=1, border_color=C["border"]
                       ).grid(row=0, column=2, sticky="ew")

        self.toast = ctk.CTkLabel(body, text="",
                                   font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
                                   text_color=C["text_dim"], fg_color="transparent")
        self.toast.pack(pady=(10, 0))

    def _on_slider(self, val):
        self.len_label.configure(text=str(int(val)))

    def _generate(self):
        try:
            pw = PasswordLogic.generate(
                int(self.slider.get()),
                self.ch_upper.get(), self.ch_lower.get(),
                self.ch_digits.get(), self.ch_symbols.get(),
                self.avoid_var.get())
        except ValueError as e:
            self._show_toast(f"⚠  {e}", C["danger"])
            return

        self.pw_var.set(pw)
        label, color, level = PasswordLogic.strength(pw)
        self.meter.update(level, color, label)
        self._show_toast("✓  New password generated", C["success"])

    def _copy(self):
        pw = self.pw_var.get()
        if not pw:
            self._show_toast("Nothing to copy", C["warning"]); return
        pyperclip.copy(pw)
        self._show_toast("✓  Copied to clipboard", C["success"])

    def _clear(self):
        self.pw_var.set("")
        self.meter.reset()
        self._show_toast("Cleared", C["text_dim"])

    def _show_toast(self, msg, color):
        self.toast.configure(text=msg, text_color=color)
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(3200, lambda: self.toast.configure(text=""))


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()