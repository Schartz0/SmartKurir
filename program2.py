import tkinter as tk
from tkinter import messagebox, filedialog
import random
import math
from queue import PriorityQueue
from PIL import Image, ImageTk

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

TILE_SIZE = 10  # Base tile size

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
        self.root.title("Smart Courier Tkinter - Responsive 16 Direction Pathfinding")
        
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

        # Add fit to window checkbox
        self.fit_to_window = tk.BooleanVar(value=True)
        self.fit_checkbox = tk.Checkbutton(self.controls_frame, text="Fit to Window", 
                                         variable=self.fit_to_window, command=self.update)
        self.fit_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid = []
        self.grid_width = 0
        self.grid_height = 0
        self.start = (0, 0)
        self.goal = (0, 0)
        self.courier = Courier(0, 0)
        self.original_map_image = None
        self.map_photo = None

        # Bind resize event with a small delay to avoid too many updates
        self.resize_after_id = None
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.minsize(500, 350)

        # Show initial message
        self.show_initial_message()

    def on_window_resize(self, event):
        # Only handle main window resize events
        if event.widget == self.root:
            # Cancel previous resize update if pending
            if self.resize_after_id:
                self.root.after_cancel(self.resize_after_id)
            # Schedule update with small delay to avoid too many updates
            self.resize_after_id = self.root.after(100, self.update)

    def calculate_display_dimensions(self):
        """Calculate the dimensions for displaying the map based on canvas size and settings"""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:  # Canvas not yet initialized
            return None, None, None, None, None, None
            
        if not self.grid:
            return None, None, None, None, None, None
            
        # Original map dimensions
        original_map_w = self.grid_width * TILE_SIZE
        original_map_h = self.grid_height * TILE_SIZE
        
        if self.fit_to_window.get():
            # Calculate scale to fit the map in the canvas while maintaining aspect ratio
            padding = 20  # Leave some padding
            available_w = canvas_w - padding
            available_h = canvas_h - padding
            
            scale_x = available_w / original_map_w
            scale_y = available_h / original_map_h
            scale = min(scale_x, scale_y, 1.0)  # Don't scale up beyond original size
            
            display_w = int(original_map_w * scale)
            display_h = int(original_map_h * scale)
        else:
            # Use original size
            scale = 1.0
            display_w = original_map_w
            display_h = original_map_h
        
        # Calculate offset to center the map
        offset_x = max((canvas_w - display_w) // 2, 0)
        offset_y = max((canvas_h - display_h) // 2, 0)
        
        return display_w, display_h, offset_x, offset_y, scale, scale

    def show_initial_message(self):
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w > 1 and canvas_h > 1:  # Only show if canvas is initialized
            text = "Please load a map to begin"
            self.canvas.create_text(canvas_w//2, canvas_h//2, text=text, font=("Arial", 16), fill=BLACK)

    def set_speed(self, value):
        self.courier.speed = float(value) / 10

    def draw_grid(self):
        self.canvas.delete("all")
        
        if not self.grid:  # If no map loaded
            self.show_initial_message()
            return
            
        # Get display dimensions
        display_w, display_h, offset_x, offset_y, scale_x, scale_y = self.calculate_display_dimensions()
        
        if display_w is None:  # Canvas not ready
            return
            
        # Resize and display the map image if available
        if self.original_map_image and self.fit_to_window.get():
            # Resize the image to fit the display dimensions
            resized_image = self.original_map_image.resize((display_w, display_h), Image.Resampling.NEAREST)
            self.map_photo = ImageTk.PhotoImage(resized_image)
        elif self.original_map_image:
            # Use original image size
            self.map_photo = ImageTk.PhotoImage(self.original_map_image)
        
        if self.map_photo:
            # Draw loaded map
            self.canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=self.map_photo)
        else:
            # Draw default grid
            # Draw walkable area as plain white background
            self.canvas.create_rectangle(
                offset_x, offset_y,
                offset_x + display_w,
                offset_y + display_h,
                fill=WHITE, outline=WHITE
            )

            # Draw obstacles as gray blocks
            tile_w = display_w / self.grid_width
            tile_h = display_h / self.grid_height
            
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if self.grid[y][x] == 1:  # obstacle
                        x1 = offset_x + x * tile_w
                        y1 = offset_y + y * tile_h
                        x2 = offset_x + (x + 1) * tile_w
                        y2 = offset_y + (y + 1) * tile_h
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=GRAY, outline=GRAY)

        # Draw start, goal, and courier
        tile_w = display_w / self.grid_width
        tile_h = display_h / self.grid_height
        
        # Start position
        sx, sy = self.start
        cx = offset_x + sx * tile_w + tile_w // 2
        cy = offset_y + sy * tile_h + tile_h // 2
        flag_size = min(tile_w, tile_h) // 2
        self.canvas.create_line(cx, cy - flag_size, cx, cy + flag_size, fill=BLACK, width=2)
        self.canvas.create_polygon([
            (cx, cy), 
            (cx, cy - flag_size), 
            (cx + flag_size, cy - flag_size//2)
        ], fill=YELLOW, outline=BLACK)

        # Goal position
        gx, gy = self.goal
        cx = offset_x + gx * tile_w + tile_w // 2
        cy = offset_y + gy * tile_h + tile_h // 2
        self.canvas.create_line(cx, cy - flag_size, cx, cy + flag_size, fill=BLACK, width=2)
        self.canvas.create_polygon([
            (cx, cy), 
            (cx, cy - flag_size), 
            (cx + flag_size, cy - flag_size//2)
        ], fill=RED, outline=BLACK)

        # Courier
        cx = offset_x + self.courier.current_pos[0] * tile_w + tile_w // 2
        cy = offset_y + self.courier.current_pos[1] * tile_h + tile_h // 2
        courier_size = min(tile_w, tile_h) // 2
        angle = self.courier.angle
        points = [
            (cx + courier_size * math.cos(angle), cy - courier_size * math.sin(angle)),
            (cx + courier_size * math.cos(angle + 2.3), cy - courier_size * math.sin(angle + 2.3)),
            (cx + courier_size * math.cos(angle - 2.3), cy - courier_size * math.sin(angle - 2.3)),
        ]
        self.canvas.create_polygon(points, fill=GREEN, outline=BLACK)

        # Draw path if it exists
        if self.courier.path:
            path_points = []
            for point in [self.courier.current_pos] + self.courier.path[self.courier.target_index:]:
                px, py = point
                path_x = offset_x + px * tile_w + tile_w // 2
                path_y = offset_y + py * tile_h + tile_h // 2
                path_points.append((path_x, path_y))
            
            if len(path_points) > 1:
                self.canvas.create_line(path_points, fill=GREEN, width=2, dash=(4, 2))

        # Legend
        canvas_w = self.canvas.winfo_width()
        legend_text = f"Map: {self.grid_width}x{self.grid_height} | Display: {display_w}x{display_h} | Scale: {scale_x:.2f}"
        padding = 8
        font = ("Arial", 10, "bold")
        
        # Create background for legend
        text_id = self.canvas.create_text(padding, padding, anchor="nw", text=legend_text, font=font, fill=BLACK)
        bbox = self.canvas.bbox(text_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            self.canvas.create_rectangle(
                x1 - padding//2, y1 - padding//2,
                x2 + padding//2, y2 + padding//2,
                fill="white", outline="black", width=1
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
            
        current_pos = (int(self.courier.current_pos[0]), int(self.courier.current_pos[1]))
        self.courier.path = a_star(self.grid, current_pos, self.goal)
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
            filepath = filedialog.askopenfilename(
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
            if filepath:
                # Load and store original image
                img = Image.open(filepath).convert('RGB')
                self.original_map_image = img
                w, h = img.size
                
                # Calculate grid size based on image dimensions
                self.grid_width = w // TILE_SIZE
                self.grid_height = h // TILE_SIZE
                
                # Create walkability grid
                grid = []
                for y in range(self.grid_height):
                    row = []
                    for x in range(self.grid_width):
                        # Get pixel color at tile center
                        pixel_x = min(x * TILE_SIZE + TILE_SIZE // 2, w - 1)
                        pixel_y = min(y * TILE_SIZE + TILE_SIZE // 2, h - 1)
                        r, g, b = img.getpixel((pixel_x, pixel_y))
                        
                        # Check if in gray range (90-150) - walkable
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
            messagebox.showerror("Error", f"Failed to load map: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    app = App(root)
    root.mainloop()