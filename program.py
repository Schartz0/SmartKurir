import tkinter as tk
from tkinter import messagebox, filedialog
import random
import math
from queue import PriorityQueue
from PIL import Image

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

TILE_SIZE = 10 # Ukuran tetap

GRAY = "#666666"
WHITE = "#FFFFFF"
BLACK = "#000000"
YELLOW = "#FFFF00"
RED = "#FF0000"
GREEN = "#00FF00"

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def generate_random_map(grid_width, grid_height):
    return [[0 if random.random() < 0.85 else 1 for _ in range(grid_width)] for _ in range(grid_height)]

def is_walkable(grid, x, y):
    return 0 <= x < len(grid[0]) and 0 <= y < len(grid) and grid[y][x] == 0

def a_star(grid, start, goal):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    while not open_set.empty():
        _, current = open_set.get()
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if is_walkable(grid, *neighbor):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    open_set.put((f_score, neighbor))
    return []

def random_position(grid):
    h = len(grid)
    w = len(grid[0])
    while True:
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        if grid[y][x] == 0:
            return x, y

class Courier:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.path = []
        self.moving = False
        self.angle = 0
    def move(self):
        if self.path:
            nx, ny = self.path.pop(0)
            dx = nx - self.x
            dy = ny - self.y
            if dx or dy:
                self.angle = math.atan2(-dy, dx)
            self.x, self.y = nx, ny
        else:
            self.moving = False

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Courier Tkinter")

        self.map_width_px = WINDOW_WIDTH
        self.map_height_px = WINDOW_HEIGHT
        self.grid_width = self.map_width_px // TILE_SIZE
        self.grid_height = self.map_height_px // TILE_SIZE

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg=WHITE)
        self.canvas.pack(side='top', fill='both', expand=True)

        self.controls_frame = tk.Frame(self.main_frame, height=50)
        self.controls_frame.pack(side='bottom', fill='x')

        self.random_btn = tk.Button(self.controls_frame, text="Acak Peta", command=self.random_map)
        self.random_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.pos_btn = tk.Button(self.controls_frame, text="Acak Posisi", command=self.random_positions)
        self.pos_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_btn = tk.Button(self.controls_frame, text="Play", command=self.play)
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.reset_btn = tk.Button(self.controls_frame, text="Reset Posisi", command=self.reset_position)
        self.reset_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.load_btn = tk.Button(self.controls_frame, text="Load Peta", command=self.load_map)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid = generate_random_map(self.grid_width, self.grid_height)
        self.start = random_position(self.grid)
        self.goal = random_position(self.grid)
        self.courier = Courier(*self.start)

        self.root.bind("<Configure>", lambda e: self.update())
        self.root.minsize(500, 350)

        self.update()

    def draw_grid(self):
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        map_w = self.grid_width * TILE_SIZE
        map_h = self.grid_height * TILE_SIZE
        offset_x = max((canvas_w - map_w) // 2, 0)
        offset_y = max((canvas_h - map_h) // 2, 0)

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                color = GRAY if self.grid[y][x] == 0 else WHITE
                self.canvas.create_rectangle(
                    offset_x + x*TILE_SIZE,
                    offset_y + y*TILE_SIZE,
                    offset_x + (x+1)*TILE_SIZE,
                    offset_y + (y+1)*TILE_SIZE,
                    fill=color, outline=BLACK
                )

        # Start
        sx, sy = self.start
        cx = offset_x + sx*TILE_SIZE + TILE_SIZE//2
        cy = offset_y + sy*TILE_SIZE + TILE_SIZE//2
        self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10), (cx + 10, cy)], fill=YELLOW, outline=BLACK)

        # Goal
        gx, gy = self.goal
        cx = offset_x + gx*TILE_SIZE + TILE_SIZE//2
        cy = offset_y + gy*TILE_SIZE + TILE_SIZE//2
        self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10), (cx + 10, cy)], fill=RED, outline=BLACK)

        # Courier
        cx = offset_x + self.courier.x * TILE_SIZE + TILE_SIZE // 2
        cy = offset_y + self.courier.y * TILE_SIZE + TILE_SIZE // 2
        length = TILE_SIZE // 2
        angle = self.courier.angle
        points = [
            (cx + length * math.cos(angle), cy - length * math.sin(angle)),
            (cx + length * math.cos(angle + 2.3), cy - length * math.sin(angle + 2.3)),
            (cx + length * math.cos(angle - 2.3), cy - length * math.sin(angle - 2.3)),
        ]
        self.canvas.create_polygon(points, fill=GREEN, outline=BLACK)

        # Legend
        legend_text = f"Map size: {self.grid_width * TILE_SIZE} px x {self.grid_height * TILE_SIZE} px"
        padding = 4
        font = ("Arial", 10, "bold")
        text_id = self.canvas.create_text(padding, padding, anchor="nw", text=legend_text, font=font)
        bbox = self.canvas.bbox(text_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            self.canvas.create_rectangle(
                x1 - padding, y1 - padding,
                x2 + padding, y2 + padding,
                fill="white", outline="black", stipple="gray50"
            )
            self.canvas.lift(text_id)

    def update(self):
        self.draw_grid()
        if self.courier.moving:
            self.courier.move()
            self.root.after(70, self.update)

    def random_map(self):
        self.grid = generate_random_map(self.grid_width, self.grid_height)
        self.random_positions()

    def random_positions(self):
        self.start = random_position(self.grid)
        self.goal = random_position(self.grid)
        self.courier = Courier(*self.start)
        self.update()

    def play(self):
        self.courier.path = a_star(self.grid, (self.courier.x, self.courier.y), self.goal)
        if self.courier.path:
            self.courier.moving = True
            self.update()
        else:
            messagebox.showinfo("Info", "Tidak ditemukan jalur dari posisi saat ini ke tujuan.")

    def reset_position(self):
        self.courier = Courier(*self.start)
        self.courier.moving = False
        self.update()

    def load_map(self):
        try:
            filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if filepath:
                img = Image.open(filepath).convert('RGB')
                w, h = img.size
                grid_w = w // TILE_SIZE
                grid_h = h // TILE_SIZE

                self.grid_width = grid_w
                self.grid_height = grid_h

                grid = []
                for y in range(grid_h):
                    row = []
                    for x in range(grid_w):
                        r, g, b = img.getpixel((x * TILE_SIZE, y * TILE_SIZE))
                        if 90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150:
                            row.append(0)
                        else:
                            row.append(1)
                    grid.append(row)

                self.grid = grid
                self.start = random_position(self.grid)
                self.goal = random_position(self.grid)
                self.courier = Courier(*self.start)

                # Jangan set ukuran canvas paksa, biarkan pack expand yang atur
                self.update()
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    app = App(root)
    root.mainloop()
