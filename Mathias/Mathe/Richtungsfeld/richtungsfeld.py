import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import sympy as sp
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

class DirectionFieldPlotter:
    def __init__(self, root):
        self.root = root
        self.root.title("Direction Field Plotter")
        self.root.geometry("1400x850")
        
        # Dark mode state
        self.dark_mode = False
        
        # Default values
        self.function_str = "x + y"
        self.x_min = -5
        self.x_max = 5
        self.y_min = -5
        self.y_max = 5
        self.x_steps = 20
        self.y_steps = 20
        self.colorbar = None  # Track colorbar to prevent duplication
        
        self.setup_ui()
        self.apply_theme()
        self.plot_direction_field()
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with title and dark mode toggle
        top_bar = tk.Frame(main_frame, height=60)
        top_bar.pack(fill=tk.X, padx=20, pady=(20, 10))
        top_bar.pack_propagate(False)
        
        title_label = tk.Label(top_bar, text="Richtungsfeld Plotter", 
                               font=("Segoe UI", 20, "bold"))
        title_label.pack(side=tk.LEFT)
        
        self.theme_button = tk.Button(top_bar, text="🌙", font=("Segoe UI", 16),
                                      command=self.toggle_theme, 
                                      relief=tk.FLAT, cursor="hand2",
                                      padx=15, pady=5)
        self.theme_button.pack(side=tk.RIGHT)
        
        # Control panel in a card-like frame (smaller height)
        control_card = tk.Frame(main_frame, relief=tk.FLAT, height=200)
        control_card.pack(fill=tk.X, padx=20, pady=10)
        control_card.pack_propagate(True)
        
        # Function input section
        func_frame = tk.Frame(control_card)
        func_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(func_frame, text="Differentialgleichung", 
                font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 8))
        
        self.func_entry = tk.Entry(func_frame, font=("Segoe UI", 11), 
                                   relief=tk.FLAT, bd=2)
        self.func_entry.insert(0, self.function_str)
        self.func_entry.pack(fill=tk.X, ipady=8)
        
        self.converted_label = tk.Label(func_frame, text="", 
                                        font=("Segoe UI", 10, "italic"),
                                        anchor=tk.W)
        self.converted_label.pack(fill=tk.X, pady=(5, 0))
        
        # Parameters grid
        params_frame = tk.Frame(control_card)
        params_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # X Range
        x_frame = tk.Frame(params_frame)
        x_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        tk.Label(x_frame, text="X-Bereich", 
                font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        x_inputs = tk.Frame(x_frame)
        x_inputs.pack(fill=tk.X)
        
        self.x_min_entry = tk.Entry(x_inputs, font=("Segoe UI", 10), 
                                    width=8, relief=tk.FLAT, bd=2)
        self.x_min_entry.insert(0, str(self.x_min))
        self.x_min_entry.pack(side=tk.LEFT, ipady=5)
        
        tk.Label(x_inputs, text=" bis ", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        self.x_max_entry = tk.Entry(x_inputs, font=("Segoe UI", 10), 
                                    width=8, relief=tk.FLAT, bd=2)
        self.x_max_entry.insert(0, str(self.x_max))
        self.x_max_entry.pack(side=tk.LEFT, ipady=5)
        
        tk.Label(x_inputs, text=" Schritte: ", 
                font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 0))
        
        self.x_steps_entry = tk.Entry(x_inputs, font=("Segoe UI", 10), 
                                      width=6, relief=tk.FLAT, bd=2)
        self.x_steps_entry.insert(0, str(self.x_steps))
        self.x_steps_entry.pack(side=tk.LEFT, ipady=5)
        
        # Y Range
        y_frame = tk.Frame(params_frame)
        y_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(y_frame, text="Y-Bereich", 
                font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        y_inputs = tk.Frame(y_frame)
        y_inputs.pack(fill=tk.X)
        
        self.y_min_entry = tk.Entry(y_inputs, font=("Segoe UI", 10), 
                                    width=8, relief=tk.FLAT, bd=2)
        self.y_min_entry.insert(0, str(self.y_min))
        self.y_min_entry.pack(side=tk.LEFT, ipady=5)
        
        tk.Label(y_inputs, text=" bis ", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        self.y_max_entry = tk.Entry(y_inputs, font=("Segoe UI", 10), 
                                    width=8, relief=tk.FLAT, bd=2)
        self.y_max_entry.insert(0, str(self.y_max))
        self.y_max_entry.pack(side=tk.LEFT, ipady=5)
        
        tk.Label(y_inputs, text=" Schritte: ", 
                font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 0))
        
        self.y_steps_entry = tk.Entry(y_inputs, font=("Segoe UI", 10), 
                                      width=6, relief=tk.FLAT, bd=2)
        self.y_steps_entry.insert(0, str(self.y_steps))
        self.y_steps_entry.pack(side=tk.LEFT, ipady=5)
        
        # Buttons
        button_frame = tk.Frame(control_card)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.plot_button = tk.Button(button_frame, text="Aktualisieren", 
                                     command=self.update_plot,
                                     font=("Segoe UI", 10, "bold"),
                                     relief=tk.FLAT, cursor="hand2",
                                     padx=25, pady=10)
        self.plot_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.table_button = tk.Button(button_frame, text="Wertetabelle", 
                                      command=self.show_value_table,
                                      font=("Segoe UI", 10),
                                      relief=tk.FLAT, cursor="hand2",
                                      padx=25, pady=10)
        self.table_button.pack(side=tk.LEFT)
        
        # Plot canvas
        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.fig = Figure(figsize=(12, 7))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Store all widgets for theme switching
        self.widgets = {
            'main_frame': main_frame,
            'top_bar': top_bar,
            'title_label': title_label,
            'control_card': control_card,
            'func_frame': func_frame,
            'params_frame': params_frame,
            'x_frame': x_frame,
            'y_frame': y_frame,
            'button_frame': button_frame,
            'plot_frame': plot_frame,
            'x_inputs': x_inputs,
            'y_inputs': y_inputs
        }
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.plot_direction_field()
    
    def apply_theme(self):
        """Apply current theme to all widgets"""
        if self.dark_mode:
            # Dark mode colors
            bg = "#1e1e1e"
            card_bg = "#2d2d2d"
            fg = "#e0e0e0"
            entry_bg = "#3d3d3d"
            entry_fg = "#ffffff"
            button_bg = "#0d7377"
            button_fg = "#ffffff"
            button_hover = "#14a0a6"
            self.theme_button.config(text="☀️")
            plot_bg = "#2d2d2d"
            plot_fg = "#e0e0e0"
        else:
            # Light mode colors
            bg = "#f5f5f5"
            card_bg = "#ffffff"
            fg = "#333333"
            entry_bg = "#ffffff"
            entry_fg = "#333333"
            button_bg = "#0d7377"
            button_fg = "#ffffff"
            button_hover = "#14a0a6"
            self.theme_button.config(text="🌙")
            plot_bg = "#ffffff"
            plot_fg = "#333333"
        
        # Apply to root and main widgets
        self.root.config(bg=bg)
        self.widgets['main_frame'].config(bg=bg)
        self.widgets['top_bar'].config(bg=bg)
        self.widgets['title_label'].config(bg=bg, fg=fg)
        self.widgets['control_card'].config(bg=card_bg)
        self.widgets['func_frame'].config(bg=card_bg)
        self.widgets['params_frame'].config(bg=card_bg)
        self.widgets['x_frame'].config(bg=card_bg)
        self.widgets['y_frame'].config(bg=card_bg)
        self.widgets['button_frame'].config(bg=card_bg)
        self.widgets['plot_frame'].config(bg=bg)
        self.widgets['x_inputs'].config(bg=card_bg)
        self.widgets['y_inputs'].config(bg=card_bg)
        
        # Apply to all labels in control card
        for widget in self.widgets['func_frame'].winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=card_bg, fg=fg)
        
        for frame in [self.widgets['x_frame'], self.widgets['y_frame']]:
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(bg=card_bg, fg=fg)
                elif isinstance(widget, tk.Frame):
                    widget.config(bg=card_bg)
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label):
                            child.config(bg=card_bg, fg=fg)
        
        # Apply to entries
        for entry in [self.func_entry, self.x_min_entry, self.x_max_entry, 
                     self.y_min_entry, self.y_max_entry, self.x_steps_entry, 
                     self.y_steps_entry]:
            entry.config(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        
        # Apply to buttons
        self.plot_button.config(bg=button_bg, fg=button_fg, activebackground=button_hover)
        self.table_button.config(bg=card_bg, fg=fg, activebackground=entry_bg)
        self.theme_button.config(bg=card_bg, fg=fg, activebackground=entry_bg)
        
        # Apply to matplotlib
        self.fig.patch.set_facecolor(plot_bg)
        self.ax.set_facecolor(plot_bg)
        self.ax.tick_params(colors=plot_fg)
        self.ax.xaxis.label.set_color(plot_fg)
        self.ax.yaxis.label.set_color(plot_fg)
        self.ax.title.set_color(plot_fg)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(plot_fg)
        
        self.canvas.draw()
    
    def parse_function(self, func_str):
        """Parse and convert function to y' = ... form, handling various input formats"""
        x, y = sp.symbols('x y')
        y_prime = sp.Symbol("y'")
        
        func_str = func_str.strip()
        
        try:
            # Replace ^ with ** for exponentiation
            func_str = func_str.replace("^", "**")
            
            # Replace common derivative notations
            func_str = func_str.replace("y'", "yprime")
            func_str = func_str.replace("dy/dx", "yprime")
            func_str = func_str.replace("dy", "yprime")
            
            # Add support for e and pi
            func_str = func_str.replace("pi", "PI")
            
            yprime = sp.Symbol('yprime')
            PI = sp.pi
            e = sp.E
            
            # Define log function for custom base support
            def log(base, value):
                return sp.log(value, base)
            
            # Parse the expression
            if "=" in func_str:
                left, right = func_str.split("=", 1)
                left_expr = sp.sympify(left.strip())
                right_expr = sp.sympify(right.strip())
                equation = sp.Eq(left_expr, right_expr)
                
                # Solve for y'
                solution = sp.solve(equation, yprime)
                if solution:
                    expr = solution[0]
                else:
                    raise ValueError("Konnte nicht nach y' auflösen")
            else:
                # Assume it's already in the form y' = expression
                expr = sp.sympify(func_str)
            
            # Convert to string for display
            converted_str = f"y' = {expr}"
            self.converted_label.config(text=f"Umgeformt: {converted_str}")
            
            # Return lambda function - ensure it returns float/numpy array
            func = sp.lambdify((x, y), expr, modules=['numpy'])

            
            # Wrapper to ensure output is float
            def safe_func(x_val, y_val):
                result = np.array(func(x_val, y_val), dtype=float)
                return result

            
            return safe_func
            
        except Exception as e:
            raise ValueError(f"Konnte Funktion nicht parsen: {str(e)}")
    
    def update_plot(self):
        """Update plot with current parameters"""
        try:
            self.function_str = self.func_entry.get()
            self.x_min = float(self.x_min_entry.get())
            self.x_max = float(self.x_max_entry.get())
            self.y_min = float(self.y_min_entry.get())
            self.y_max = float(self.y_max_entry.get())
            self.x_steps = int(self.x_steps_entry.get())
            self.y_steps = int(self.y_steps_entry.get())
            
            self.plot_direction_field()
        except Exception as e:
            self.show_error(f"Fehler: {str(e)}")
    
    def plot_direction_field(self):
        """Plot the direction field with colored slopes"""
        self.ax.clear()
        
        # Clear any existing colorbars
        if hasattr(self, 'colorbar') and self.colorbar:
            self.colorbar.remove()
            self.colorbar = None
        
        try:
            func = self.parse_function(self.function_str)
            
            # Create grid
            x = np.linspace(self.x_min, self.x_max, self.x_steps)
            y = np.linspace(self.y_min, self.y_max, self.y_steps)
            X, Y = np.meshgrid(x, y)
            
            # Calculate slopes
            with np.errstate(divide='ignore', invalid='ignore'):
                slopes = func(X, Y)
            
            # Ensure slopes is float array
            slopes = np.asarray(slopes, dtype=np.float64)
            
            # Normalize slopes for color mapping
            slopes_flat = slopes.flatten()
            valid_slopes = slopes_flat[np.isfinite(slopes_flat)]
            
            if len(valid_slopes) > 0:
                norm = Normalize(vmin=np.percentile(valid_slopes, 5), 
                               vmax=np.percentile(valid_slopes, 95))
                cmap = plt.cm.RdYlBu_r
                sm = ScalarMappable(norm=norm, cmap=cmap)
                
                # Calculate direction vectors
                dx = 1
                dy = slopes
                
                # Normalize vector lengths
                magnitude = np.sqrt(dx**2 + dy**2)
                with np.errstate(divide='ignore', invalid='ignore'):
                    dx = dx / magnitude * 0.3
                    dy = dy / magnitude * 0.3
                
                # Plot each arrow with color based on slope
                for i in range(X.shape[0]):
                    for j in range(X.shape[1]):
                        if np.isfinite(slopes[i, j]):
                            color = cmap(norm(slopes[i, j]))
                            self.ax.arrow(X[i, j], Y[i, j], dx[i, j], dy[i, j],
                                        head_width=0.15, head_length=0.15,
                                        fc=color, ec=color, alpha=0.7,
                                        length_includes_head=True)
                
                # Add colorbar (store reference to remove later)
                self.colorbar = self.fig.colorbar(sm, ax=self.ax)
                self.colorbar.set_label('Steigung', rotation=270, labelpad=20)
                
                if self.dark_mode:
                    self.colorbar.ax.yaxis.label.set_color('#e0e0e0')
                    self.colorbar.ax.tick_params(colors='#e0e0e0')
            
            self.ax.set_xlabel('x')
            self.ax.set_ylabel('y')
            self.ax.set_title('Richtungsfeld')
            self.ax.grid(True, alpha=0.3)
            self.ax.set_xlim(self.x_min, self.x_max)
            self.ax.set_ylim(self.y_min, self.y_max)
           
            
        except Exception as e:
            self.show_error(f"Fehler beim Plotten: {str(e)}")
    
    def show_value_table(self):
        """Display value table in new window"""
        try:
            func = self.parse_function(self.function_str)
            
            # Create table window
            table_window = tk.Toplevel(self.root)
            table_window.title("Wertetabelle")
            table_window.geometry("700x600")
            
            if self.dark_mode:
                table_window.config(bg="#1e1e1e")
                text_bg = "#2d2d2d"
                text_fg = "#e0e0e0"
            else:
                table_window.config(bg="#f5f5f5")
                text_bg = "#ffffff"
                text_fg = "#333333"
            
            # Create text widget with scrollbar
            text_widget = scrolledtext.ScrolledText(table_window, wrap=tk.NONE, 
                                                    font=('Consolas', 10),
                                                    bg=text_bg, fg=text_fg)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Generate table
            x = np.linspace(self.x_min, self.x_max, self.x_steps)
            y = np.linspace(self.y_min, self.y_max, self.y_steps)
            
            # Header
            text_widget.insert(tk.END, f"Wertetabelle\n")
            text_widget.insert(tk.END, "=" * 70 + "\n\n")
            y_prime = "y' (Steigung)"
            text_widget.insert(tk.END, f"{'x':>10} | {'y':>10} | {y_prime:>20}\n")
            text_widget.insert(tk.END, "-" * 70 + "\n")
            
            # Calculate and display values
            X, Y = np.meshgrid(x, y)
            slopes = func(X, Y)
            
            count = 0
            for i in range(len(y)):
                for j in range(len(x)):
                    if np.isfinite(slopes[i, j]):
                        text_widget.insert(tk.END, 
                            f"{X[i, j]:10.3f} | {Y[i, j]:10.3f} | {slopes[i, j]:20.6f}\n")
                        count += 1
                        if count > 300:
                            text_widget.insert(tk.END, "\n... (zu viele Werte, nur erste 300 angezeigt)")
                            break
                if count > 300:
                    break
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            self.show_error(f"Fehler bei Wertetabelle: {str(e)}")
    
    def show_error(self, message):
        """Show error message in a popup"""
        error_window = tk.Toplevel(self.root)
        error_window.title("Fehler")
        error_window.geometry("450x120")
        
        if self.dark_mode:
            error_window.config(bg="#1e1e1e")
            label_bg = "#1e1e1e"
            label_fg = "#e0e0e0"
            button_bg = "#2d2d2d"
        else:
            error_window.config(bg="#ffffff")
            label_bg = "#ffffff"
            label_fg = "#333333"
            button_bg = "#f5f5f5"
        
        label = tk.Label(error_window, text=message, wraplength=400,
                        bg=label_bg, fg=label_fg, font=("Segoe UI", 10))
        label.pack(pady=20, padx=20)
        
        button = tk.Button(error_window, text="OK", command=error_window.destroy,
                          font=("Segoe UI", 10), bg=button_bg, fg=label_fg,
                          relief=tk.FLAT, cursor="hand2", padx=20, pady=8)
        button.pack(pady=10)

def main():
    root = tk.Tk()
    app = DirectionFieldPlotter(root)
    root.mainloop()

if __name__ == "__main__":
    main()