import tkinter as tk
from tkinter import messagebox, filedialog
import random
import math
from queue import PriorityQueue
from PIL import Image, ImageTk

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

TILE_SIZE = 10  # Fixed size

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
        # Euclidean distance for more accurate diagonal movement
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    
    # 16-direction movement (including diagonals and knight moves)
    directions = [
        # Cardinal directions (4)
        (0, -1), (1, 0), (0, 1), (-1, 0),
        # Diagonal directions (4)
        (-1, -1), (-1, 1), (1, -1), (1, 1),
        # Knight moves (8)
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    
    while not open_set.empty():
        _, current = open_set.get()
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]
        
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            
            # Skip if neighbor is not walkable
            if not is_walkable(grid, *neighbor):
                continue
                
            # Movement cost based on direction
            if abs(dx) == 1 and abs(dy) == 1:  # Diagonal
                move_cost = math.sqrt(2)
            elif abs(dx) + abs(dy) == 3:  # Knight move
                move_cost = math.sqrt(5)  # sqrt(1^2 + 2^2)
            else:  # Cardinal direction
                move_cost = 1
                
            tentative_g = g_score[current] + move_cost
            
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
        self.target_index = 0
        self.speed = 0.2  # Movement speed (0-1)
        self.current_pos = (x, y)  # Float position for smooth animation
        
    def move(self):
        if self.path and self.target_index < len(self.path):
            target = self.path[self.target_index]
            dx = target[0] - self.current_pos[0]
            dy = target[1] - self.current_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < self.speed:
                self.current_pos = target
                self.target_index += 1
            else:
                # Smooth movement
                direction_x = dx / distance
                direction_y = dy / distance
                self.current_pos = (
                    self.current_pos[0] + direction_x * self.speed,
                    self.current_pos[1] + direction_y * self.speed
                )
                self.angle = math.atan2(-direction_y, direction_x)
            
            # Update grid position
            self.x, self.y = int(round(self.current_pos[0])), int(round(self.current_pos[1]))
        else:
            self.moving = False

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Courier Tkinter - 16 Direction Pathfinding")

        self.map_width_px = WINDOW_WIDTH
        self.map_height_px = WINDOW_HEIGHT
        self.grid_width = 0  # Will be set when loading map
        self.grid_height = 0  # Will be set when loading map

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg=WHITE)
        self.canvas.pack(side='top', fill='both', expand=True)

        self.controls_frame = tk.Frame(self.main_frame, height=50)
        self.controls_frame.pack(side='bottom', fill='x')

        self.pos_btn = tk.Button(self.controls_frame, text="Random Positions", command=self.random_positions, state=tk.DISABLED)
        self.pos_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_btn = tk.Button(self.controls_frame, text="Play", command=self.play, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.reset_btn = tk.Button(self.controls_frame, text="Reset Position", command=self.reset_position, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.load_btn = tk.Button(self.controls_frame, text="Load Map", command=self.load_map)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.speed_scale = tk.Scale(self.controls_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                                  label="Speed", command=self.set_speed, state=tk.DISABLED)
        self.speed_scale.set(5)
        self.speed_scale.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid = []
        self.start = (0, 0)
        self.goal = (0, 0)
        self.courier = Courier(0, 0)
        self.map_image = None
        self.map_photo = None

        self.root.bind("<Configure>", lambda e: self.update())
        self.root.minsize(500, 350)

        # Show initial message
        self.show_initial_message()

    def show_initial_message(self):
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        text = "Please load a map to begin"
        self.canvas.create_text(canvas_w//2, canvas_h//2, text=text, font=("Arial", 16), fill=BLACK)

    def set_speed(self, value):
        self.courier.speed = float(value) / 10

    def draw_grid(self):
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if not self.grid:  # If no map loaded
            self.show_initial_message()
            return
            
        if self.map_photo:
            # Draw loaded map
            self.canvas.create_image(
                (canvas_w - self.map_photo.width()) // 2,
                (canvas_h - self.map_photo.height()) // 2,
                anchor=tk.NW, image=self.map_photo
            )
        else:
            # Draw default grid
            map_w = self.grid_width * TILE_SIZE
            map_h = self.grid_height * TILE_SIZE
            offset_x = max((canvas_w - map_w) // 2, 0)
            offset_y = max((canvas_h - map_h) // 2, 0)

            # Draw walkable area as plain white background
            self.canvas.create_rectangle(
                offset_x, 
                offset_y,
                offset_x + map_w,
                offset_y + map_h,
                fill=WHITE, outline=WHITE
            )

            # Draw obstacles as gray blocks without grid lines
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if self.grid[y][x] == 1:  # obstacle
                        self.canvas.create_rectangle(
                            offset_x + x*TILE_SIZE,
                            offset_y + y*TILE_SIZE,
                            offset_x + (x+1)*TILE_SIZE,
                            offset_y + (y+1)*TILE_SIZE,
                            fill=GRAY, outline=GRAY
                        )

        # Draw start, goal, and courier
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if self.map_photo:
            offset_x = (canvas_w - self.map_photo.width()) // 2
            offset_y = (canvas_h - self.map_photo.height()) // 2
            scale_x = self.map_photo.width() / (self.grid_width * TILE_SIZE)
            scale_y = self.map_photo.height() / (self.grid_height * TILE_SIZE)
        else:
            map_w = self.grid_width * TILE_SIZE
            map_h = self.grid_height * TILE_SIZE
            offset_x = max((canvas_w - map_w) // 2, 0)
            offset_y = max((canvas_h - map_h) // 2, 0)
            scale_x = scale_y = 1

        # Start
        sx, sy = self.start
        cx = offset_x + sx*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + sy*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        self.canvas.create_line(cx, cy - 10*scale_y, cx, cy + 10*scale_y, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10*scale_y), (cx + 10*scale_x, cy)], fill=YELLOW, outline=BLACK)

        # Goal
        gx, gy = self.goal
        cx = offset_x + gx*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + gy*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        self.canvas.create_line(cx, cy - 10*scale_y, cx, cy + 10*scale_y, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10*scale_y), (cx + 10*scale_x, cy)], fill=RED, outline=BLACK)

        # Courier
        cx = offset_x + self.courier.current_pos[0]*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + self.courier.current_pos[1]*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        length = TILE_SIZE * max(scale_x, scale_y) // 2
        angle = self.courier.angle
        points = [
            (cx + length * math.cos(angle), cy - length * math.sin(angle)),
            (cx + length * math.cos(angle + 2.3), cy - length * math.sin(angle + 2.3)),
            (cx + length * math.cos(angle - 2.3), cy - length * math.sin(angle - 2.3)),
        ]
        self.canvas.create_polygon(points, fill=GREEN, outline=BLACK)

        # Draw path if it exists
        if self.courier.path:
            path_points = []
            for point in [self.courier.current_pos] + self.courier.path[self.courier.target_index:]:
                px, py = point
                cx = offset_x + px*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
                cy = offset_y + py*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
                path_points.append((cx, cy))
            
            if len(path_points) > 1:
                self.canvas.create_line(path_points, fill=GREEN, width=2, dash=(4, 2))

        # Legend
        if self.grid:  # Only show legend if map is loaded
            legend_text = f"Map size: {self.grid_width * TILE_SIZE} px x {self.grid_height * TILE_SIZE} px | 16-direction pathfinding"
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
            self.root.after(20, self.update)  # Faster update for smoother animation

    def random_positions(self):
        if not self.grid:
            return
            
        self.start = random_position(self.grid)
        self.goal = random_position(self.grid)
        self.courier = Courier(*self.start)
        self.update()

    def play(self):
        if not self.grid:
            return
            
        self.courier.path = a_star(self.grid, (int(self.courier.current_pos[0]), int(self.courier.current_pos[1])), self.goal)
        if self.courier.path:
            self.courier.moving = True
            self.courier.target_index = 0
            self.update()
        else:
            messagebox.showinfo("Info", "No path found from current position to goal.")

    def reset_position(self):
        if not self.grid:
            return
            
        self.courier = Courier(*self.start)
        self.courier.moving = False
        self.update()

    def load_map(self):
        try:
            filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if filepath:
                img = Image.open(filepath).convert('RGB')
                w, h = img.size
                
                # Save original image for display
                self.map_image = img
                self.map_photo = ImageTk.PhotoImage(self.map_image)
                
                # Calculate grid size based on image dimensions
                self.grid_width = w // TILE_SIZE
                self.grid_height = h // TILE_SIZE
                
                # Create walkability grid
                grid = []
                for y in range(self.grid_height):
                    row = []
                    for x in range(self.grid_width):
                        # Get pixel color at tile center
                        pixel_x = x * TILE_SIZE + TILE_SIZE // 2
                        pixel_y = y * TILE_SIZE + TILE_SIZE // 2
                        pixel_x = min(pixel_x, w-1)
                        pixel_y = min(pixel_y, h-1)
                        r, g, b = self.map_image.getpixel((pixel_x, pixel_y))
                        
                        # Check if in gray range (90-150)
                        if 90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150:
                            row.append(0)  # Walkable
                        else:
                            row.append(1)  # Obstacle
                    grid.append(row)
                
                self.grid = grid
                self.start = random_position(self.grid)
                self.goal = random_position(self.grid)
                self.courier = Courier(*self.start)
                
                # Enable all buttons
                self.pos_btn.config(state=tk.NORMAL)
                self.play_btn.config(state=tk.NORMAL)
                self.reset_btn.config(state=tk.NORMAL)
                self.speed_scale.config(state=tk.NORMAL)
                
                self.update()
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    app = App(root)
    root.mainloop()