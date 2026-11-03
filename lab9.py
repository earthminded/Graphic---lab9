import math
import random
import tkinter as tk
from tkinter import messagebox, ttk


INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


def compute_outcode(x, y, xmin, ymin, xmax, ymax):
  code = INSIDE
  if x < xmin:
    code |= LEFT
  elif x > xmax:
    code |= RIGHT
  if y < ymin:
    code |= TOP
  elif y > ymax:
    code |= BOTTOM
  return code


def clip_sutherland_cohen(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    c1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    c2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)

    while True:
        if (c1 | c2) == 0:
            return (x1, y1, x2, y2)
        if (c1 & c2) != 0:
            return None

        out_code = c1 if c1 != 0 else c2

        if out_code & TOP:
            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            y = ymin
        elif out_code & BOTTOM:
            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            y = ymax
        elif out_code & RIGHT:
            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            x = xmax
        elif out_code & LEFT:
            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            x = xmin

        if out_code == c1:
            x1, y1 = x, y
            c1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
        else:
            x2, y2 = x, y
            c2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)


def clip_simple(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
  pts = []

  if xmin <= x1 <= xmax and ymin <= y1 <= ymax:
    pts.append((x1, y1, 0.0))
  if xmin <= x2 <= xmax and ymin <= y2 <= ymax:
    pts.append((x2, y2, 1.0))

  dx = x2 - x1
  dy = y2 - y1

  if abs(dx) > 1e-9:
    t = (xmin - x1) / dx
    if 0.0 <= t <= 1.0:
      y = y1 + t * dy
      if ymin <= y <= ymax:
        pts.append((xmin, y, t))
    t = (xmax - x1) / dx
    if 0.0 <= t <= 1.0:
      y = y1 + t * dy
      if ymin <= y <= ymax:
        pts.append((xmax, y, t))

  if abs(dy) > 1e-9:
    t = (ymin - y1) / dy
    if 0.0 <= t <= 1.0:
      x = x1 + t * dx
      if xmin <= x <= xmax:
        pts.append((x, ymin, t))
    t = (ymax - y1) / dy
    if 0.0 <= t <= 1.0:
      x = x1 + t * dx
      if xmin <= x <= xmax:
        pts.append((x, ymax, t))

  if len(pts) < 2:
    return None

  pts.sort(key=lambda p: p[2])
  unique = []
  for p in pts:
    if not unique or (
        abs(p[0] - unique[-1][0]) > 1e-4 or abs(p[1] - unique[-1][1]) > 1e-4
    ):
      unique.append(p)

  if len(unique) >= 2:
    return (unique[0][0], unique[0][1], unique[-1][0], unique[-1][1])
  return None


def clip_midpoint(x1, y1, x2, y2, xmin, ymin, xmax, ymax, eps=1.0):
  code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
  code2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)

  if (code1 | code2) == 0:
    return (x1, y1, x2, y2)
  if (code1 & code2) != 0:
    return None

  def find_boundary_point(p_in, p_out):
    xin, yin = p_in
    xout, yout = p_out
    while math.hypot(xin - xout, yin - yout) > eps:
      mx = (xin + xout) / 2.0
      my = (yin + yout) / 2.0
      if compute_outcode(mx, my, xmin, ymin, xmax, ymax) == INSIDE:
        xin, yin = mx, my
      else:
        xout, yout = mx, my
    return xin, yin

  if code1 == INSIDE:
    bx, by = find_boundary_point((x1, y1), (x2, y2))
    return (x1, y1, bx, by)
  elif code2 == INSIDE:
    bx, by = find_boundary_point((x2, y2), (x1, y1))
    return (bx, by, x2, y2)
  else:

    def find_internal_segment(xa, ya, xb, yb):
      if (
          compute_outcode(xa, ya, xmin, ymin, xmax, ymax)
          & compute_outcode(xb, yb, xmin, ymin, xmax, ymax)
      ) != 0:
        return None
      mx = (xa + xb) / 2.0
      my = (ya + yb) / 2.0
      if compute_outcode(mx, my, xmin, ymin, xmax, ymax) == INSIDE:
        return (mx, my)
      if math.hypot(xa - xb, ya - yb) <= eps:
        return None
      res = find_internal_segment(xa, ya, mx, my)
      if res:
        return res
      return find_internal_segment(mx, my, xb, yb)

    mid_inside = find_internal_segment(x1, y1, x2, y2)
    if not mid_inside:
      return None

    p1_clip = find_boundary_point(mid_inside, (x1, y1))
    p2_clip = find_boundary_point(mid_inside, (x2, y2))
    return (p1_clip[0], p1_clip[1], p2_clip[0], p2_clip[1])


class ClippingApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Отсечение отрезков - Лабораторная работа №9")
    self.root.geometry("1200x740")

    self.segments = []
    self.clipped_segments = []


    top_bar = tk.Frame(root, padx=10, pady=8)
    top_bar.pack(side=tk.TOP, fill=tk.X)


    algo_box = tk.LabelFrame(
        top_bar, text="Выбор алгоритма", font=("Tahoma", 9), padx=8, pady=4
    )
    algo_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

    self.algo_var = tk.StringVar(value="cohen")
    tk.Radiobutton(
        algo_box,
        text="Сазерленд-Коэн",
        variable=self.algo_var,
        value="cohen",
        command=self.on_algo_change,
    ).pack(side=tk.LEFT, padx=3)
    tk.Radiobutton(
        algo_box,
        text="Простой",
        variable=self.algo_var,
        value="simple",
        command=self.on_algo_change,
    ).pack(side=tk.LEFT, padx=3)
    tk.Radiobutton(
        algo_box,
        text="Средней точки",
        variable=self.algo_var,
        value="midpoint",
        command=self.on_algo_change,
    ).pack(side=tk.LEFT, padx=3)

    self.frame_eps = tk.Frame(algo_box)
    tk.Label(self.frame_eps, text="ε:").pack(side=tk.LEFT)
    self.ent_eps = tk.Entry(self.frame_eps, width=4, justify="center")
    self.ent_eps.insert(0, "1.0")
    self.ent_eps.pack(side=tk.LEFT, padx=3)
    tk.Button(self.frame_eps, text="OK", command=self.draw_all).pack(
        side=tk.LEFT
    )

    win_box = tk.LabelFrame(
        top_bar, text="Окно отсечения", font=("Tahoma", 9), padx=8, pady=4
    )
    win_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

    for label_txt, attr_name, default_val in [
        ("Xmin", "ent_xmin", "200"),
        ("Ymin", "ent_ymin", "150"),
        ("Xmax", "ent_xmax", "600"),
        ("Ymax", "ent_ymax", "450"),
    ]:
      tk.Label(win_box, text=f"{label_txt}:").pack(side=tk.LEFT, padx=(3, 1))
      entry = tk.Entry(win_box, width=5, justify="center")
      entry.insert(0, default_val)
      entry.pack(side=tk.LEFT, padx=(0, 4))
      setattr(self, attr_name, entry)

    tk.Button(win_box, text="Применить", command=self.update_window).pack(
        side=tk.LEFT, padx=4
    )


    act_box = tk.Frame(top_bar)
    act_box.pack(side=tk.RIGHT, fill=tk.Y)
    tk.Button(
        act_box,
        text="Выполнить отсечение",
        font=("Tahoma", 9, "bold"),
        command=self.perform_clipping,
    ).pack(side=tk.TOP, fill=tk.X, pady=(0, 3))
    tk.Button(
        act_box, text="Очистить холст", command=self.clear_all
    ).pack(side=tk.TOP, fill=tk.X)


    workspace = tk.Frame(root, padx=10, pady=4)
    workspace.pack(fill=tk.BOTH, expand=True)

    left_panel = tk.Frame(workspace, width=280)
    left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))


    seg_add_box = tk.LabelFrame(
        left_panel, text="Новый отрезок", font=("Tahoma", 9), padx=6, pady=6
    )
    seg_add_box.pack(fill=tk.X, pady=(0, 6))

    row_c1 = tk.Frame(seg_add_box)
    row_c1.pack(fill=tk.X, pady=2)
    tk.Label(row_c1, text="X1:").pack(side=tk.LEFT)
    self.ent_x1 = tk.Entry(row_c1, width=5, justify="center")
    self.ent_x1.insert(0, "50")
    self.ent_x1.pack(side=tk.LEFT, padx=(2, 8))
    tk.Label(row_c1, text="Y1:").pack(side=tk.LEFT)
    self.ent_y1 = tk.Entry(row_c1, width=5, justify="center")
    self.ent_y1.insert(0, "50")
    self.ent_y1.pack(side=tk.LEFT, padx=2)

    row_c2 = tk.Frame(seg_add_box)
    row_c2.pack(fill=tk.X, pady=2)
    tk.Label(row_c2, text="X2:").pack(side=tk.LEFT)
    self.ent_x2 = tk.Entry(row_c2, width=5, justify="center")
    self.ent_x2.insert(0, "450")
    self.ent_x2.pack(side=tk.LEFT, padx=(2, 8))
    tk.Label(row_c2, text="Y2:").pack(side=tk.LEFT)
    self.ent_y2 = tk.Entry(row_c2, width=5, justify="center")
    self.ent_y2.insert(0, "450")
    self.ent_y2.pack(side=tk.LEFT, padx=2)

    tk.Button(
        seg_add_box, text="Добавить в список", command=self.add_segment
    ).pack(fill=tk.X, pady=(4, 2))
    tk.Button(
        left_panel,
        text="+ 5 случайных отрезков",
        command=self.add_random_segments,
    ).pack(fill=tk.X, pady=(0, 6))


    table_box = tk.LabelFrame(
        left_panel,
        text="Координаты отрезков",
        font=("Tahoma", 9),
        padx=4,
        pady=4,
    )
    table_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

    self.tree = ttk.Treeview(
        table_box,
        columns=("#", "X1", "Y1", "X2", "Y2"),
        show="headings",
        height=8,
    )
    self.tree.heading("#", text="№")
    self.tree.column("#", width=25, anchor="center")
    for col in ("X1", "Y1", "X2", "Y2"):
      self.tree.heading(col, text=col)
      self.tree.column(col, width=42, anchor="center")

    sb = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
    self.tree.configure(yscrollcommand=sb.set)
    self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)


    info_box = tk.LabelFrame(
        left_panel, text="Статус", font=("Tahoma", 9), padx=6, pady=4
    )
    info_box.pack(fill=tk.X)
    self.lbl_info = tk.Label(
        info_box,
        text="Алгоритм: Сазерленд-Коэн\nОтрезков: 0",
        font=("Tahoma", 8),
        justify="left",
    )
    self.lbl_info.pack(anchor="w")


    right_panel = tk.Frame(workspace)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    self.canvas = tk.Canvas(
        right_panel,
        bg="white",
        highlightthickness=1,
        highlightbackground="#c0c0c0",
    )
    self.canvas.pack(fill=tk.BOTH, expand=True)


    legend = tk.Frame(right_panel, pady=4)
    legend.pack(fill=tk.X)

    tk.Label(legend, text="Окно отсечения:", font=("Tahoma", 8)).pack(
        side=tk.LEFT, padx=(4, 2)
    )
    tk.Canvas(legend, width=12, height=12, bg="red", highlightthickness=0).pack(
        side=tk.LEFT, padx=(0, 16)
    )

    tk.Label(legend, text="Исходные отрезки:", font=("Tahoma", 8)).pack(
        side=tk.LEFT, padx=(4, 2)
    )
    tk.Canvas(
        legend, width=12, height=12, bg="#707070", highlightthickness=0
    ).pack(side=tk.LEFT, padx=(0, 16))

    tk.Label(legend, text="Отсечённые части:", font=("Tahoma", 8)).pack(
        side=tk.LEFT, padx=(4, 2)
    )
    tk.Canvas(
        legend, width=12, height=12, bg="blue", highlightthickness=0
    ).pack(side=tk.LEFT, padx=(0, 4))

    self.on_algo_change()
    self.draw_all()

  def get_window_coords(self):
    try:
      return (
          float(self.ent_xmin.get()),
          float(self.ent_ymin.get()),
          float(self.ent_xmax.get()),
          float(self.ent_ymax.get()),
      )
    except ValueError:
      messagebox.showerror("Ошибка", "Координаты окна должны быть числами!")
      return (200.0, 150.0, 600.0, 450.0)

  def on_algo_change(self):
    if self.algo_var.get() == "midpoint":
      self.frame_eps.pack(side=tk.LEFT, padx=(6, 0))
    else:
      self.frame_eps.pack_forget()

  def update_window(self):
    self.clipped_segments = []
    self.draw_all()

  def add_segment(self):
    try:
      x1 = float(self.ent_x1.get())
      y1 = float(self.ent_y1.get())
      x2 = float(self.ent_x2.get())
      y2 = float(self.ent_y2.get())
      self.segments.append((x1, y1, x2, y2))
      self.update_table()
      self.clipped_segments = []
      self.draw_all()
    except ValueError:
      messagebox.showerror(
          "Ошибка", "Координаты отрезка должны быть числами!"
      )

  def add_random_segments(self):
    w = self.canvas.winfo_width()
    h = self.canvas.winfo_height()
    if w <= 1 or h <= 1:
      w, h = 750, 550

    self.segments = []
    for _ in range(5):
      x1 = random.randint(30, max(31, w - 30))
      y1 = random.randint(30, max(31, h - 30))
      x2 = random.randint(30, max(31, w - 30))
      y2 = random.randint(30, max(31, h - 30))
      self.segments.append((x1, y1, x2, y2))

    self.update_table()
    self.clipped_segments = []
    self.draw_all()

  def update_table(self):
    for item in self.tree.get_children():
      self.tree.delete(item)
    for idx, (x1, y1, x2, y2) in enumerate(self.segments, 1):
      self.tree.insert(
          "",
          "end",
          values=(
              idx,
              int(round(x1)),
              int(round(y1)),
              int(round(x2)),
              int(round(y2)),
          ),
      )

  def perform_clipping(self):
    if not self.segments:
      messagebox.showwarning(
          "Предупреждение", "Сначала добавьте отрезки!"
      )
      return

    xmin, ymin, xmax, ymax = self.get_window_coords()
    algo = self.algo_var.get()
    self.clipped_segments = []

    algo_name = ""
    if algo == "cohen":
      algo_name = "Сазерленд-Коэн"
      for s in self.segments:
        res = clip_sutherland_cohen(
            s[0], s[1], s[2], s[3], xmin, ymin, xmax, ymax
        )
        if res:
          self.clipped_segments.append(res)
    elif algo == "simple":
      algo_name = "Простой"
      for s in self.segments:
        res = clip_simple(s[0], s[1], s[2], s[3], xmin, ymin, xmax, ymax)
        if res:
          self.clipped_segments.append(res)
    elif algo == "midpoint":
      algo_name = "Средней точки"
      try:
        eps = float(self.ent_eps.get())
      except ValueError:
        eps = 1.0
      for s in self.segments:
        res = clip_midpoint(
            s[0], s[1], s[2], s[3], xmin, ymin, xmax, ymax, eps
        )
        if res:
          self.clipped_segments.append(res)

    visible_count = len(self.clipped_segments)
    total_count = len(self.segments)
    self.lbl_info.config(
        text=f"Алгоритм: {algo_name}\nВидимых: {visible_count} из {total_count}"
    )
    self.draw_all()

  def clear_all(self):
    self.segments = []
    self.clipped_segments = []
    self.update_table()
    self.lbl_info.config(text="Холст очищен.\nОтрезков: 0")
    self.draw_all()

  def draw_all(self):
    self.canvas.delete("all")
    xmin, ymin, xmax, ymax = self.get_window_coords()

        
    self.canvas.create_rectangle(xmin, ymin, xmax, ymax, outline="red", width=2)
    self.canvas.create_text(xmin + 35, ymin - 10, text=f"({int(xmin)}, {int(ymin)})", fill="red", font=("Tahoma", 9))
    self.canvas.create_text(xmax - 35, ymax + 12, text=f"({int(xmax)}, {int(ymax)})", fill="red", font=("Tahoma", 9))


    for s in self.segments:
     self.canvas.create_line(s[0], s[1], s[2], s[3], fill="#707070", width=1.5)
     self.canvas.create_oval(s[0] - 3, s[1] - 3, s[0] + 3, s[1] + 3, fill="#505050", outline="")
     self.canvas.create_oval(s[2] - 3, s[3] - 3, s[2] + 3, s[3] + 3, fill="#505050", outline="")


    for c in self.clipped_segments:
     self.canvas.create_line(c[0], c[1], c[2], c[3], fill="blue", width=3)
     self.canvas.create_oval(c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3, fill="blue", outline="")
     self.canvas.create_oval(c[2] - 3, c[3] - 3, c[2] + 3, c[3] + 3, fill="blue", outline="")

if __name__ == "__main__":
  app_root = tk.Tk()
  ClippingApp(app_root)
  app_root.mainloop()

