import tkinter as tk
from tkinter import messagebox, filedialog
import random
import math
from queue import PriorityQueue
from PIL import Image, ImageTk

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

TILE_SIZE = 10 # Fixed size

GRAY = "#666666"
WHITE = "#FFFFFF"
BLACK = "#000000"
YELLOW = "#FFFF00"
RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def generate_random_map(grid_width, grid_height):
    return [[0 if random.random() < 0.85 else 1 for _ in range(grid_width)] for _ in range(grid_height)]

def is_walkable(grid, x, y):
    return 0 <= x < len(grid[0]) and 0 <= y < len(grid) and grid[y][x] == 0

def line_of_sight(grid, start, end):
    """Check if there's a clear line of sight between two points using Bresenham's algorithm"""
    x0, y0 = start
    x1, y1 = end
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    
    err = dx - dy
    
    x, y = x0, y0
    
    while True:
        # Check if current position is walkable
        if not is_walkable(grid, x, y):
            return False
            
        if x == x1 and y == y1:
            break
            
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x += sx
            
        if e2 < dx:
            err += dx
            y += sy
    
    return True

def a_star(grid, start, goal):
    def heuristic(a, b):
        # Manhattan distance for grid-based movement
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    
    # 8-direction movement (cardinal + diagonal)
    directions = [
        # Cardinal directions (4)
        (0, -1), (1, 0), (0, 1), (-1, 0),
        # Diagonal directions (4)
        (-1, -1), (-1, 1), (1, -1), (1, 1)
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
            
            # For diagonal moves, check if path is clear
            if abs(dx) == 1 and abs(dy) == 1:
                # Check both adjacent cells for diagonal movement
                if not (is_walkable(grid, current[0] + dx, current[1]) and 
                       is_walkable(grid, current[0], current[1] + dy)):
                    continue
                move_cost = math.sqrt(2)
            else:
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
        self.speed = 0.15  # Reduced speed for more precise movement
        self.current_pos = (float(x), float(y))  # Float position for smooth animation
        self.has_pickup = False  # Status apakah sudah mengambil pickup
        self.current_target = None  # Target saat ini (pickup atau goal)
        
    def move(self):
        if self.path and self.target_index < len(self.path):
            target = self.path[self.target_index]
            dx = target[0] - self.current_pos[0]
            dy = target[1] - self.current_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < self.speed:
                self.current_pos = (float(target[0]), float(target[1]))
                self.target_index += 1
            else:
                # Smooth movement with smaller steps
                direction_x = dx / distance
                direction_y = dy / distance
                new_x = self.current_pos[0] + direction_x * self.speed
                new_y = self.current_pos[1] + direction_y * self.speed
                self.current_pos = (new_x, new_y)
                self.angle = math.atan2(-direction_y, direction_x)
            
            # Update grid position
            self.x, self.y = int(round(self.current_pos[0])), int(round(self.current_pos[1]))
        else:
            self.moving = False

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Courier Tkinter - Pickup & Delivery System")
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

        # Separate random position buttons
        self.random_courier_btn = tk.Button(self.controls_frame, text="Acak Kurir", command=self.random_courier_position, state=tk.DISABLED)
        self.random_courier_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.random_destinations_btn = tk.Button(self.controls_frame, text="Acak Tujuan", command=self.random_destinations, state=tk.DISABLED)
        self.random_destinations_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_btn = tk.Button(self.controls_frame, text="Play", command=self.play, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.reset_btn = tk.Button(self.controls_frame, text="Reset Posisi", command=self.reset_position, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.load_btn = tk.Button(self.controls_frame, text="Load Map", command=self.load_map)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.speed_scale = tk.Scale(self.controls_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                                  label="Speed", command=self.set_speed, state=tk.DISABLED)
        self.speed_scale.set(3)  # Lower default speed
        self.speed_scale.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid = []
        self.start = (0, 0)
        self.pickup = (0, 0)  # Bendera kuning - pickup point
        self.goal = (0, 0)    # Bendera merah - delivery point
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
        # Adjusted speed range for better control
        self.courier.speed = float(value) / 20  # More granular speed control

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

        # Draw start, pickup, goal, and courier
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



        # Pickup point - Yellow flag
        px, py = self.pickup
        cx = offset_x + px*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + py*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        self.canvas.create_line(cx, cy - 10*scale_y, cx, cy + 10*scale_y, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10*scale_y), (cx + 10*scale_x, cy)], fill=YELLOW, outline=BLACK)

        # Goal - Red flag
        gx, gy = self.goal
        cx = offset_x + gx*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + gy*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        self.canvas.create_line(cx, cy - 10*scale_y, cx, cy + 10*scale_y, fill=BLACK, width=3)
        self.canvas.create_polygon([(cx, cy), (cx, cy - 10*scale_y), (cx + 10*scale_x, cy)], fill=RED, outline=BLACK)

        # Courier - Green triangle, changes color if has pickup
        courier_color = GREEN if not self.courier.has_pickup else "#FFD700"  # Gold color when has pickup
        cx = offset_x + self.courier.current_pos[0]*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
        cy = offset_y + self.courier.current_pos[1]*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
        length = TILE_SIZE * max(scale_x, scale_y) // 1
        angle = self.courier.angle
        points = [
            (cx + length * math.cos(angle), cy - length * math.sin(angle)),
            (cx + length * math.cos(angle + 2.3), cy - length * math.sin(angle + 2.3)),
            (cx + length * math.cos(angle - 2.3), cy - length * math.sin(angle - 2.3)),
        ]
        self.canvas.create_polygon(points, fill=courier_color, outline=BLACK)

        # Draw path if it exists
        if self.courier.path:
            path_points = []
            for point in [self.courier.current_pos] + self.courier.path[self.courier.target_index:]:
                px, py = point
                cx = offset_x + px*TILE_SIZE*scale_x + TILE_SIZE*scale_x//2
                cy = offset_y + py*TILE_SIZE*scale_y + TILE_SIZE*scale_y//2
                path_points.append((cx, cy))
            
            if len(path_points) > 1:
                path_color = GREEN if not self.courier.has_pickup else "#FFD700"
                self.canvas.create_line(path_points, fill=path_color, width=2, dash=(4, 2))

        # Legend
        if self.grid:  # Only show legend if map is loaded
            status = "Mencari Pickup" if not self.courier.has_pickup else "Mengirim ke Tujuan"
            legend_text = f"Map size: {self.grid_width * TILE_SIZE} px x {self.grid_height * TILE_SIZE} px | Status: {status}"
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
            
            # Check if courier reached pickup point
            courier_pos = (int(round(self.courier.current_pos[0])), int(round(self.courier.current_pos[1])))
            
            # If courier reached pickup and doesn't have pickup yet
            if not self.courier.has_pickup and courier_pos == self.pickup and not self.courier.moving:
                self.courier.has_pickup = True
                messagebox.showinfo("Info", "Pickup berhasil! Sekarang menuju ke tujuan.")
                # Calculate path to goal
                self.courier.path = a_star(self.grid, courier_pos, self.goal)
                if self.courier.path:
                    self.courier.moving = True
                    self.courier.target_index = 0
                    self.courier.current_target = "goal"
                else:
                    messagebox.showerror("Error", "Tidak ada jalur dari pickup ke tujuan!")
            
            # If courier reached goal with pickup
            elif self.courier.has_pickup and courier_pos == self.goal and not self.courier.moving:
                messagebox.showinfo("Success", "Delivery berhasil diselesaikan!")
                self.courier.moving = False
            
            self.root.after(16, self.update)  # 60 FPS for smoother animation

    def random_courier_position(self):
        """Set random position for courier only"""
        if not self.grid:
            return
            
        new_position = random_position(self.grid)
        self.start = new_position
        self.courier = Courier(*new_position)
        self.courier.has_pickup = False
        self.update()

    def random_destinations(self):
        """Set random positions for both pickup (yellow) and goal (red) flags"""
        if not self.grid:
            return
            
        # Generate two different random positions
        self.pickup = random_position(self.grid)
        
        # Make sure goal is different from pickup
        while True:
            self.goal = random_position(self.grid)
            if self.goal != self.pickup:
                break
                
        self.update()

    def play(self):
        if not self.grid:
            return
        
        # Reset courier pickup status
        self.courier.has_pickup = False
        current_pos = (int(self.courier.current_pos[0]), int(self.courier.current_pos[1]))
        
        # First, find path to pickup point
        self.courier.path = a_star(self.grid, current_pos, self.pickup)
        if self.courier.path:
            self.courier.moving = True
            self.courier.target_index = 0
            self.courier.current_target = "pickup"
            self.update()
        else:
            messagebox.showinfo("Info", "Tidak ada jalur dari posisi saat ini ke pickup point.")

    def reset_position(self):
        if not self.grid:
            return
            
        self.courier = Courier(*self.start)
        self.courier.moving = False
        self.courier.has_pickup = False
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
                
                # Create walkability grid with improved detection
                grid = []
                for y in range(self.grid_height):
                    row = []
                    for x in range(self.grid_width):
                        # Sample multiple pixels within each tile for better accuracy
                        walkable_pixels = 0
                        total_pixels = 0
                        
                        for dy in range(TILE_SIZE):
                            for dx in range(TILE_SIZE):
                                pixel_x = x * TILE_SIZE + dx
                                pixel_y = y * TILE_SIZE + dy
                                
                                if pixel_x < w and pixel_y < h:
                                    r, g, b = self.map_image.getpixel((pixel_x, pixel_y))
                                    total_pixels += 1
                                    
                                    # Check if in gray range (90-150) - walkable
                                    if 90 <= r <= g <= 150 and 90 <= g <= 150 and 90 <= b <= 150:
                                        walkable_pixels += 1
                        
                        # If more than 30% of pixels in tile are walkable, consider tile walkable
                        if total_pixels > 0 and walkable_pixels / total_pixels > 0.2:
                            row.append(0)  # Walkable
                        else:
                            row.append(1)  # Obstacle
                            
                    grid.append(row)
                
                self.grid = grid
                self.start = random_position(self.grid)
                
                # Generate different positions for pickup and goal
                self.pickup = random_position(self.grid)
                while True:
                    self.goal = random_position(self.grid)
                    if self.goal != self.pickup:
                        break
                
                self.courier = Courier(*self.start)
                
                # Enable all buttons
                self.random_courier_btn.config(state=tk.NORMAL)
                self.random_destinations_btn.config(state=tk.NORMAL)
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