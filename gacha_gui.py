import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

from gacha_simulator import (
    BASE_RATES,
    load_state,
    reset_history_and_state,
    save_record,
    save_state,
    simulate,
)

UI_HISTORY_FILE = "gacha_ui_history.json"


class GachaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("抽卡模拟器 - GUI版")
        self.root.geometry("1120x700")
        self.root.minsize(1020, 640)

        self.no_six_counter, self.no_up_six_streak = load_state()
        self.total_draws = 0
        self.batch_counter = 0
        self.total_counts = {
            "六星": 0,
            "六星(UP)": 0,
            "六星(非UP)": 0,
            "五星": 0,
            "四星": 0,
            "三星": 0,
        }

        self._build_layout()
        self._load_ui_history()
        self._refresh_stats()

    def _build_layout(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=12)
        left.grid(row=0, column=0, sticky="ns")

        right = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ttk.Frame):
        title = ttk.Label(parent, text="抽卡操作", font=("Microsoft YaHei UI", 12, "bold"))
        title.pack(anchor="w", pady=(0, 10))

        rates_text = (
            f"基础概率\n"
            f"六星: {BASE_RATES['六星']}%\n"
            f"五星: {BASE_RATES['五星']}%\n"
            f"四星: {BASE_RATES['四星']}%\n"
            f"三星: {BASE_RATES['三星']}%"
        )
        ttk.Label(parent, text=rates_text, justify="left").pack(anchor="w", pady=(0, 12))

        button_row_1 = ttk.Frame(parent)
        button_row_1.pack(fill="x", pady=(0, 8))
        ttk.Button(button_row_1, text="抽一次", command=lambda: self._do_draw(1)).pack(
            side="left", expand=True, fill="x", padx=(0, 4)
        )
        ttk.Button(button_row_1, text="十连抽", command=lambda: self._do_draw(10)).pack(
            side="left", expand=True, fill="x", padx=(4, 0)
        )

        button_row_2 = ttk.Frame(parent)
        button_row_2.pack(fill="x", pady=(0, 8))
        ttk.Button(button_row_2, text="清空记录与状态", command=self._reset_all).pack(
            side="left", expand=True, fill="x", padx=(0, 4)
        )
        ttk.Button(button_row_2, text="导出当前记录", command=self._export_current_view).pack(
            side="left", expand=True, fill="x", padx=(4, 0)
        )

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(parent, text="统计信息", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        self.stats_var = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.stats_var, justify="left").pack(anchor="w", pady=(6, 0))

    def _build_right_panel(self, parent: ttk.Frame):
        header = ttk.Label(parent, text="抽卡记录", font=("Microsoft YaHei UI", 12, "bold"))
        header.grid(row=0, column=0, sticky="w", pady=(0, 8))

        cols = ("time", "batch", "idx", "star", "up", "display")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=22)
        self.tree.grid(row=1, column=0, sticky="nsew")

        self.tree.heading("time", text="时间")
        self.tree.heading("batch", text="批次")
        self.tree.heading("idx", text="序号")
        self.tree.heading("star", text="星级")
        self.tree.heading("up", text="是否UP")
        self.tree.heading("display", text="结果")

        self.tree.column("time", width=170, anchor="center")
        self.tree.column("batch", width=90, anchor="center")
        self.tree.column("idx", width=60, anchor="center")
        self.tree.column("star", width=80, anchor="center")
        self.tree.column("up", width=80, anchor="center")
        self.tree.column("display", width=440, anchor="w")

        ybar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        ybar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=ybar.set)

        self.tree.tag_configure("batch_header", foreground="#0B3D91")
        self.tree.tag_configure("six_up", foreground="#A06000")
        self.tree.tag_configure("six", foreground="#A00040")
        self.tree.tag_configure("five", foreground="#6A2DA8")
        self.tree.tag_configure("four", foreground="#005B8F")

    def _do_draw(self, n: int):
        mode = "2" if n == 10 else "1"
        draw_name = "十连" if n == 10 else "单抽"
        counts, results, self.no_six_counter, self.no_up_six_streak = simulate(
            n, self.no_six_counter, self.no_up_six_streak
        )
        save_state(self.no_six_counter, self.no_up_six_streak)

        self.batch_counter += 1
        batch_label = f"第{self.batch_counter}次"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 先插入批次分隔行，便于视觉区分每次抽卡
        self.tree.insert(
            "",
            "end",
            values=(now, batch_label, "-", "-", "-", f"========== {batch_label}{draw_name}（共{n}抽） =========="),
            tags=("batch_header",),
        )

        for i, (star, is_up) in enumerate(results, start=1):
            up_text = "是" if (star == "六星" and is_up) else "-"
            display = self._format_display(star, is_up)
            tag = self._row_tag(star, is_up)
            self.tree.insert("", "end", values=(now, batch_label, i, star, up_text, display), tags=(tag,))

        for key in self.total_counts:
            self.total_counts[key] += counts[key]
        self.total_draws += n

        avg = (counts["六星"] * 6 + counts["五星"] * 5 + counts["四星"] * 4 + counts["三星"] * 3) / n
        save_record(mode, n, counts, avg)
        self._save_ui_history()
        self._refresh_stats()

    def _format_display(self, star: str, is_up: bool) -> str:
        stars = {
            "六星": "★★★★★★",
            "五星": "★★★★★",
            "四星": "★★★★",
            "三星": "★★★",
        }
        suffix = "（UP）" if (star == "六星" and is_up) else ""
        return f"{stars.get(star, star)} {star}{suffix}"

    def _row_tag(self, star: str, is_up: bool) -> str:
        if star == "六星" and is_up:
            return "six_up"
        if star == "六星":
            return "six"
        if star == "五星":
            return "five"
        if star == "四星":
            return "four"
        return ""

    def _refresh_stats(self):
        if self.total_draws == 0:
            self.stats_var.set(
                "总抽数: 0\n"
                "六星: 0\n五星: 0\n四星: 0\n三星: 0\n\n"
                "当前保底进度\n"
                f"距离软保底起点(50抽): {max(0, 50 - self.no_six_counter)}"
            )
            return

        six = self.total_counts["六星"]
        five = self.total_counts["五星"]
        four = self.total_counts["四星"]
        three = self.total_counts["三星"]
        up = self.total_counts["六星(UP)"]
        non_up = self.total_counts["六星(非UP)"]
        avg = (six * 6 + five * 5 + four * 4 + three * 3) / self.total_draws

        summary = (
            f"总抽数: {self.total_draws}\n"
            f"六星: {six} ({six / self.total_draws * 100:.2f}%)\n"
            f"五星: {five} ({five / self.total_draws * 100:.2f}%)\n"
            f"四星: {four} ({four / self.total_draws * 100:.2f}%)\n"
            f"三星: {three} ({three / self.total_draws * 100:.2f}%)\n"
            f"六星UP/非UP: {up}/{non_up}\n"
            f"平均星级: {avg:.2f}\n\n"
            f"当前保底进度\n"
            f"已连续未出六星: {self.no_six_counter}\n"
            f"已连续六星非UP: {self.no_up_six_streak}"
        )
        self.stats_var.set(summary)

    def _reset_all(self):
        if not messagebox.askyesno("确认", "确定清空所有记录和状态吗？"):
            return

        reset_history_and_state()
        if os.path.exists(UI_HISTORY_FILE):
            os.remove(UI_HISTORY_FILE)

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.no_six_counter, self.no_up_six_streak = 0, 0
        self.total_draws = 0
        self.batch_counter = 0
        for key in self.total_counts:
            self.total_counts[key] = 0

        self._refresh_stats()
        messagebox.showinfo("完成", "记录和状态已清空。")

    def _export_current_view(self):
        rows = []
        for item in self.tree.get_children():
            rows.append(self.tree.item(item, "values"))
        if not rows:
            messagebox.showinfo("提示", "当前没有可导出的记录。")
            return

        out_file = "gacha_ui_export.csv"
        with open(out_file, "w", encoding="utf-8-sig") as f:
            f.write("时间,批次,序号,星级,是否UP,结果\n")
            for row in rows:
                f.write(",".join(str(x) for x in row) + "\n")
        messagebox.showinfo("导出成功", f"已导出到 {out_file}")

    def _load_ui_history(self):
        if not os.path.exists(UI_HISTORY_FILE):
            return
        try:
            with open(UI_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        for row in data.get("rows", []):
            # 兼容旧格式（无 batch 列）
            time_text = row.get("time", "")
            batch = row.get("batch", "")
            idx = row.get("idx", "")
            star = row.get("star", "三星")
            up = row.get("up", "-")
            display = row.get("display", "")
            tag = row.get("tag", "")

            if not tag:
                if "======" in str(display):
                    tag = "batch_header"
                else:
                    tag = self._row_tag(star, up == "是")

            self.tree.insert(
                "",
                "end",
                values=(time_text, batch, idx, star, up, display),
                tags=(tag,),
            )

        self.total_draws = int(data.get("total_draws", 0))
        self.batch_counter = int(data.get("batch_counter", 0))
        stored_counts = data.get("total_counts", {})
        for key in self.total_counts:
            self.total_counts[key] = int(stored_counts.get(key, 0))

    def _save_ui_history(self):
        rows = []
        for item in self.tree.get_children():
            time_text, batch, idx, star, up, display = self.tree.item(item, "values")
            tags = self.tree.item(item, "tags")
            rows.append(
                {
                    "time": time_text,
                    "batch": batch,
                    "idx": idx,
                    "star": star,
                    "up": up,
                    "display": display,
                    "tag": tags[0] if tags else "",
                }
            )

        payload = {
            "rows": rows,
            "total_draws": self.total_draws,
            "batch_counter": self.batch_counter,
            "total_counts": self.total_counts,
        }
        with open(UI_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    GachaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
