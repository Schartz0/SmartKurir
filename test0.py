import tkinter as tk
from tkinter import messagebox, filedialog
import random
import math
from queue import PriorityQueue
from PIL import Image

# Konstanta
TILE_SIZE = 20
GRID_WIDTH = 50
GRID_HEIGHT = 32
MENU_HEIGHT = 60
CANVAS_WIDTH = TILE_SIZE * GRID_WIDTH
CANVAS_HEIGHT = TILE_SIZE * GRID_HEIGHT

# Warna
GRAY = "#666666"
WHITE = "#FFFFFF"
BLACK = "#000000"
YELLOW = "#FFFF00"
RED = "#FF0000"
GREEN = "#00FF00"

# Utilitas
def generate_random_map():
    return [[0 if random.random() < 0.85 else 1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def is_walkable(grid, x, y):
    return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and grid[y][x] == 0

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

def load_map_from_image(filepath):
    img = Image.open(filepath).convert('RGB')
    width, height = img.size
    if not (1000 <= width <= 1500 and 700 <= height <= 1000):
        raise ValueError("Ukuran gambar harus 1000-1500 px lebar dan 700-1000 px tinggi")

    global GRID_WIDTH, GRID_HEIGHT
    GRID_WIDTH = width // TILE_SIZE
    GRID_HEIGHT = height // TILE_SIZE

    grid = []
    for y in range(GRID_HEIGHT):
        row = []
        for x in range(GRID_WIDTH):
            r, g, b = img.getpixel((x * TILE_SIZE, y * TILE_SIZE))
            if 90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150:
                row.append(0)
            else:
                row.append(1)
        grid.append(row)
    return grid

def random_position(grid):
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
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
            next_x, next_y = self.path.pop(0)
            dx = next_x - self.x
            dy = next_y - self.y
            if dx != 0 or dy != 0:
                self.angle = math.atan2(-dy, dx)
            self.x, self.y = next_x, next_y

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Courier Tkinter")
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=WHITE)
        self.canvas.pack()

        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack(pady=5)

        self.random_btn = tk.Button(self.controls_frame, text="Acak Peta", command=self.random_map)
        self.random_btn.pack(side=tk.LEFT, padx=5)

        self.pos_btn = tk.Button(self.controls_frame, text="Acak Posisi", command=self.random_positions)
        self.pos_btn.pack(side=tk.LEFT, padx=5)

        self.play_btn = tk.Button(self.controls_frame, text="Play", command=self.play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.load_btn = tk.Button(self.controls_frame, text="Load Peta", command=self.load_map)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.grid = generate_random_map()
        self.start = random_position(self.grid)
        self.goal = random_position(self.grid)
        self.courier = Courier(*self.start)

        self.update()

    def draw_grid(self):
        self.canvas.delete("all")
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = GRAY if self.grid[y][x] == 0 else WHITE
                self.canvas.create_rectangle(x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE, fill=color, outline=BLACK)

        # Gambar bendera kuning (start)
        sx, sy = self.start
        cx, cy = sx*TILE_SIZE + TILE_SIZE//2, sy*TILE_SIZE + TILE_SIZE//2
        self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill=BLACK, width=3)
        self.canvas.create_polygon([
            (cx, cy), (cx , cy - 10), (cx +10, cy)
        ], fill=YELLOW, outline=BLACK)

        # Gambar bendera merah (goal)
        gx, gy = self.goal
        cx, cy = gx*TILE_SIZE + TILE_SIZE//2, gy*TILE_SIZE + TILE_SIZE//2
        self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill=BLACK, width=3)
        self.canvas.create_polygon([
            (cx, cy), (cx , cy - 10), (cx +10, cy)
        ], fill=RED, outline=BLACK)

        # Gambar kurir sebagai segitiga
        cx, cy = self.courier.x * TILE_SIZE + TILE_SIZE // 2, self.courier.y * TILE_SIZE + TILE_SIZE // 2
        length = TILE_SIZE // 2
        angle = self.courier.angle
        points = [
            (cx + length * math.cos(angle), cy - length * math.sin(angle)),
            (cx + length * math.cos(angle + 2.3), cy - length * math.sin(angle + 2.3)),
            (cx + length * math.cos(angle - 2.3), cy - length * math.sin(angle - 2.3)),
        ]
        self.canvas.create_polygon(points, fill=GREEN, outline=BLACK)

    def update(self):
        self.draw_grid()
        if self.courier.moving:
            self.courier.move()
            self.root.after(100, self.update)

    def random_map(self):
        self.grid = generate_random_map()
        self.random_positions()

    def random_positions(self):
        self.start = random_position(self.grid)
        self.goal = random_position(self.grid)
        self.courier = Courier(*self.start)
        self.update()

    def play(self):
        self.courier.path = a_star(self.grid, (self.courier.x, self.courier.y), self.goal)
        self.courier.moving = True
        self.update()

    def load_map(self):
        try:
            filepath = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
            if filepath:
                self.grid = load_map_from_image(filepath)
                self.start = random_position(self.grid)
                self.goal = random_position(self.grid)
                self.courier = Courier(*self.start)
                self.update()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
