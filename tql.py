#!/usr/bin/env python3
"""
Professional MySQL Database Management Application
A comprehensive database management tool with Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import mysql.connector
from mysql.connector import Error
import json
import os
import csv
import pandas as pd
from datetime import datetime
import re
import threading
import queue
import hashlib
import sqlite3
from pathlib import Path

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.mysql_manager'
        self.config_file = self.config_dir / 'config.json'
        self.projects_file = self.config_dir / 'projects.json'
        self.users_db = self.config_dir / 'users.db'
        
        self._ensure_config_dir()
        self._init_users_db()
        
    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        
    def _init_users_db(self):
        """Initialize users database"""
        conn = sqlite3.connect(self.users_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def load_config(self):
        """Load application configuration with comprehensive error handling"""
        # Define default configuration structure
        default_config = {
            'mysql': {
                'host': 'localhost',
                'port': 3306,
                'username': 'root',
                'password': ''
            },
            'appearance': {
                'theme': 'Light',
                'font_size': 10
            },
            'editor': {
                'auto_complete': True,
                'syntax_highlighting': True
            },
            'current_user': None
        }

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)

        # If config file doesn't exist, create it with defaults
        if not self.config_file.exists():
            self.save_config(default_config)
            return default_config

        try:
            # Load existing config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
                # Verify config is a dictionary
                if not isinstance(config, dict):
                    raise ValueError("Invalid config format - must be a dictionary")
                
                # Create a new config dictionary to store validated values
                validated_config = {}
                
                # Validate each section
                for section, default_values in default_config.items():
                    if not isinstance(default_values, dict):
                        # Skip if default_values isn't a dict (shouldn't happen with our structure)
                        continue
                    
                    # Initialize section in validated config
                    validated_config[section] = {}
                    
                    # Get the existing section or use empty dict if not present/invalid
                    existing_section = config.get(section)
                    if not isinstance(existing_section, dict):
                        existing_section = {}
                    
                    # Validate each key in the section
                    for key, default_value in default_values.items():
                        # Use existing value if valid, otherwise use default
                        if key in existing_section:
                            validated_config[section][key] = existing_section[key]
                        else:
                            validated_config[section][key] = default_value
                
                return validated_config
                
        except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
            print(f"Error loading config: {e}. Using default configuration.")
            # Save the default config to repair any corrupted file
            self.save_config(default_config)
            return default_config

    def save_config(self, config):
        """Save configuration to file with error handling"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def load_projects(self):
        """Load recent projects"""
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
        
    def save_projects(self, projects):
        """Save recent projects"""
        with open(self.projects_file, 'w') as f:
            json.dump(projects, f, indent=4)

class ThemeManager:
    """Manages application themes"""
    
    THEMES = {
        'Light': {
            'bg': '#f8f4e8',          # Warm cream background (softer than pure white)
            'fg': '#333333',          # Dark gray for primary text (better contrast than pure black)
            'select_bg': '#0078d4',   # Kept your blue for consistency with dark theme
            'select_fg': '#ffffff',   # White text on selection (high contrast)
            'entry_bg': '#ffffff',    # Slightly brighter than bg for input fields
            'entry_fg': '#222222',    # Darker gray for input text
            'button_bg': '#e8e2d0',   # Light cream-gray buttons (softer than #f0f0f0)
            'button_fg': '#333333',   # Dark gray button text
            'text_bg': '#f8f4e8',     # Matches background for consistency
            'text_fg': '#333333',     # Primary text color
            'menu_bg': '#e8e2d0',     # Subtle cream-gray menu background
            'menu_fg': '#333333'      # Dark gray menu text
        },
        'Dark': {
            # Your existing colors
            'bg': '#2d2d2d',            # Dark background
            'fg': "#5e5e5e",            # Mid-gray foreground
            'select_bg': '#0078d4',     # Bright blue selection
            'select_fg': '#ffffff',     # White selection text
            'entry_bg': '#404040',      # Input field background
            'entry_fg': "#636363",      # Input field text
            'button_bg': '#404040',     # Button background
            'button_fg': "#959595",     # Button text
            'text_bg': "#343434",       # Text background
            'text_fg': "#ffffff",       # Text foreground
            'menu_bg': '#404040',       # Menu background
            'menu_fg': "#5d5d5d",      # Menu text
        },
        'Blue': {
            'bg': "#365A88",
            'fg': '#ffffff',
            'select_bg': '#4a90e2',
            'select_fg': '#ffffff',
            'entry_bg': '#2d4f73',
            'entry_fg': '#ffffff',
            'button_bg': '#2d4f73',
            'button_fg': '#ffffff',
            'text_bg': '#1e3a5f',
            'text_fg': '#ffffff',
            'menu_bg': '#2d4f73',
            'menu_fg': '#ffffff'
        }
    }

    def __init__(self, app):
        self.app = app
        self.current_theme = 'Dark'
        
    def apply_theme(self, theme_name):
        """Apply theme to the application"""
        if theme_name not in self.THEMES:
            return
            
        self.current_theme = theme_name
        theme = self.THEMES[theme_name]
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for different widgets
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['button_bg'], foreground=theme['button_fg'])
        style.configure('TFrame', background=theme['bg'])
        style.configure('TNotebook', background=theme['bg'])
        style.configure('TNotebook.Tab', background=theme['button_bg'], foreground=theme['button_fg'])
        style.configure('Treeview', background=theme['text_bg'], foreground=theme['text_fg'])
        style.configure('Treeview.Heading', background=theme['button_bg'], foreground=theme['button_fg'])
        
        # Update main window
        if hasattr(self.app, 'root'):
            self.app.root.configure(bg=theme['bg'])

class SQLHighlighter:
    """SQL syntax highlighting for text widgets"""
    
    KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER',
        'DROP', 'TABLE', 'DATABASE', 'INDEX', 'VIEW', 'PROCEDURE', 'FUNCTION',
        'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS', 'AND', 'OR', 'NOT',
        'NULL', 'IS', 'IN', 'BETWEEN', 'LIKE', 'ORDER', 'BY', 'GROUP', 'HAVING',
        'LIMIT', 'OFFSET', 'UNION', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'
    ]
    
    def __init__(self, text_widget, theme_manager):
        self.text_widget = text_widget
        self.theme_manager = theme_manager
        self._configure_tags()
        
    def _configure_tags(self):
        """Configure text tags for syntax highlighting"""
        self.text_widget.tag_configure('keyword', foreground='#0000FF', font=('Courier', 10, 'bold'))
        self.text_widget.tag_configure('string', foreground='#008000', font=('Courier', 10, 'italic'))
        self.text_widget.tag_configure('comment', foreground='#808080', font=('Courier', 10, 'italic'))
        self.text_widget.tag_configure('number', foreground='#FF6600', font=('Courier', 10, 'bold'))
        
    def highlight(self, event=None):
        """Apply syntax highlighting to the text"""
        content = self.text_widget.get('1.0', tk.END)
        
        # Clear existing tags
        for tag in ['keyword', 'string', 'comment', 'number']:
            self.text_widget.tag_remove(tag, '1.0', tk.END)
            
        # Highlight keywords
        for keyword in self.KEYWORDS:
            start = '1.0'
            while True:
                pos = self.text_widget.search(r'\b' + keyword + r'\b', start, tk.END, regexp=True, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.text_widget.tag_add('keyword', pos, end)
                start = end
                
        # Highlight strings
        for pattern, tag in [
            (r"'[^']*'", 'string'),
            (r'"[^"]*"', 'string'),
            (r'--.*$', 'comment'),
            (r'/\*.*?\*/', 'comment'),
            (r'\b\d+\.?\d*\b', 'number')
        ]:
            start = '1.0'
            while True:
                match = self.text_widget.search(pattern, start, tk.END, regexp=True)
                if not match:
                    break
                match_end = self.text_widget.search(pattern, match, tk.END, regexp=True)
                if match_end:
                    end_line = int(match_end.split('.')[0])
                    end_char = int(match_end.split('.')[1]) + len(self.text_widget.get(match_end, f"{end_line}.end"))
                    end = f"{end_line}.{end_char}"
                else:
                    end = f"{match}+{len(pattern)}c"
                self.text_widget.tag_add(tag, match, end)
                start = end

class DatabaseManager:
    """Manages MySQL database connections and operations"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.current_database = None
        
    def connect(self, database=None):
        """Connect to MySQL server"""
        try:
            connection_params = {
                'host': self.config['mysql']['host'],
                'port': self.config['mysql']['port'],
                'user': self.config['mysql']['username'],
                'password': self.config['mysql']['password']
            }
            
            if database:
                connection_params['database'] = database
                
            self.connection = mysql.connector.connect(**connection_params)
            self.current_database = database
            return True
        except Error as e:
            messagebox.showerror("Connection Error", f"Failed to connect to MySQL: {str(e)}")
            return False
            
    def disconnect(self):
        """Disconnect from MySQL server"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            self.current_database = None
            
    def execute_query(self, query, params=None, fetch=True):
        """Execute SQL query"""
        if not self.connection or not self.connection.is_connected():
            raise Exception("Not connected to database")
            
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            
            if fetch and cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return {'columns': columns, 'rows': rows, 'rowcount': cursor.rowcount}
            else:
                self.connection.commit()
                return {'rowcount': cursor.rowcount}
        finally:
            cursor.close()
            
    def get_databases(self):
        """Get list of databases"""
        result = self.execute_query("SHOW DATABASES")
        return [row[0] for row in result['rows']]
        
    def get_tables(self):
        """Get list of tables in current database"""
        if not self.current_database:
            return []
        result = self.execute_query("SHOW TABLES")
        return [row[0] for row in result['rows']]
        
    def get_table_structure(self, table_name):
        """Get table structure"""
        result = self.execute_query(f"DESCRIBE {table_name}")
        return result
        
    def create_database(self, db_name):
        """Create new database"""
        self.execute_query(f"CREATE DATABASE IF NOT EXISTS `{db_name}`", fetch=False)
        
    def create_sample_table(self, db_name):
        """Create sample table with data"""
        self.execute_query(f"USE `{db_name}`", fetch=False)
        
        # Create sample table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            age INT,
            grade CHAR(1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_query(create_table_query, fetch=False)
        
        # Insert sample data
        sample_data = [
            ('John Doe', 'john@example.com', 20, 'A'),
            ('Jane Smith', 'jane@example.com', 19, 'B'),
            ('Bob Johnson', 'bob@example.com', 21, 'A'),
            ('Alice Brown', 'alice@example.com', 18, 'C'),
            ('Charlie Wilson', 'charlie@example.com', 22, 'B')
        ]
        
        insert_query = "INSERT IGNORE INTO students (name, email, age, grade) VALUES (%s, %s, %s, %s)"
        cursor = self.connection.cursor()
        try:
            cursor.executemany(insert_query, sample_data)
            self.connection.commit()
        finally:
            cursor.close()

class QueryHistoryManager:
    """Manages query history and favorites"""
    
    def __init__(self, config_dir):
        self.history_file = config_dir / 'query_history.json'
        self.favorites_file = config_dir / 'query_favorites.json'
        
    def add_to_history(self, query, database=None):
        """Add query to history"""
        history = self.load_history()
        entry = {
            'query': query,
            'database': database,
            'timestamp': datetime.now().isoformat(),
            'execution_time': None
        }
        
        # Remove duplicates and limit history size
        history = [h for h in history if h['query'] != query]
        history.insert(0, entry)
        history = history[:100]  # Keep last 100 queries
        
        self.save_history(history)
        
    def load_history(self):
        """Load query history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
        
    def save_history(self, history):
        """Save query history"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)
            
    def add_favorite(self, name, query, database=None):
        """Add query to favorites"""
        favorites = self.load_favorites()
        favorite = {
            'name': name,
            'query': query,
            'database': database,
            'created_at': datetime.now().isoformat()
        }
        favorites.append(favorite)
        self.save_favorites(favorites)
        
    def load_favorites(self):
        """Load favorite queries"""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
        
    def save_favorites(self, favorites):
        """Save favorite queries"""
        with open(self.favorites_file, 'w') as f:
            json.dump(favorites, f, indent=4)

class LoginDialog:
    """User login dialog"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.result = None
        
    def show(self):
        """Show login dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Login")
        dialog.geometry("300x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"300x200+{x}+{y}")
        
        # Create form
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(frame, width=25)
        username_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(frame, width=25, show="*")
        password_entry.grid(row=1, column=1, pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def login():
            username = username_entry.get()
            password = password_entry.get()
            
            if self.authenticate(username, password):
                self.result = username
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Invalid username or password")
                
        def create_account():
            CreateUserDialog(dialog, self.config_manager).show()
            
        ttk.Button(button_frame, text="Login", command=login).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Account", command=create_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        username_entry.focus()
        dialog.wait_window()
        return self.result
        
    def authenticate(self, username, password):
        """Authenticate user"""
        conn = sqlite3.connect(self.config_manager.users_db)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password_hash = ?", 
                      (username, password_hash))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None

class CreateUserDialog:
    """Create user account dialog"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        
    def show(self):
        """Show create user dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create Account")
        dialog.geometry("300x250")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"300x250+{x}+{y}")
        
        # Create form
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(frame, width=25)
        username_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(frame, width=25, show="*")
        password_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_entry = ttk.Entry(frame, width=25, show="*")
        confirm_entry.grid(row=2, column=1, pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def create():
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
                
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
                
            if self.create_user(username, password):
                messagebox.showinfo("Success", "Account created successfully")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Username already exists")
                
        ttk.Button(button_frame, text="Create", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        username_entry.focus()
        dialog.wait_window()
        
    def create_user(self, username, password):
        """Create new user account"""
        conn = sqlite3.connect(self.config_manager.users_db)
        cursor = conn.cursor()
        
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                          (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

class MySQLDatabaseManager:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Professional MySQL Database Manager")
        self.root.geometry("1200x800")
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.theme_manager = ThemeManager(self)
        self.db_manager = DatabaseManager(self.config)
        self.query_history = QueryHistoryManager(self.config_manager.config_dir)
        
        # Apply theme
        self.theme_manager.apply_theme(self.config['appearance']['theme'])
        
        # Current user
        self.current_user = None
        
        # Show login if user management is enabled
        if not self.authenticate_user():
            self.root.destroy()
            return
            
        # Initialize UI
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()
        
        # Start with home screen
        self.show_home_screen()
        
    def authenticate_user(self):
        """Authenticate user or skip if no users exist"""
        conn = sqlite3.connect(self.config_manager.users_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        if user_count == 0:
            # No users exist, create default admin
            self.create_default_admin()
            return True
            
        # Show login dialog
        login_dialog = LoginDialog(self.root, self.config_manager)
        self.current_user = login_dialog.show()
        
        if self.current_user:
            self.config['current_user'] = self.current_user
            self.config_manager.save_config(self.config)
            return True
            
        return False
        
    def change_theme(self, theme_name):
        """Change application theme"""
        if theme_name in self.theme_manager.THEMES:
            self.theme_manager.apply_theme(theme_name)
        else:
            messagebox.showerror("Error", f"Theme '{theme_name}' not found.")

    def create_default_admin(self):
        """Create default admin user"""
        conn = sqlite3.connect(self.config_manager.users_db)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256("admin".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                      ("admin", password_hash, "admin"))
        conn.commit()
        conn.close()
        
        self.current_user = "admin"
        
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        for theme in self.theme_manager.THEMES.keys():
            theme_menu.add_command(label=theme, command=lambda t=theme: self.change_theme(t))
            
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Query History", command=self.show_query_history)
        tools_menu.add_command(label="Table Designer", command=self.show_table_designer)
        tools_menu.add_command(label="Relationship Viewer", command=self.show_relationship_viewer)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_main_interface(self):
        """Create main interface"""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for different screens
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.user_label = ttk.Label(self.status_frame, text=f"User: {self.current_user}", relief=tk.SUNKEN)
        self.user_label.pack(side=tk.RIGHT)
        
    def show_home_screen(self):
        """Show home screen"""
        # Clear notebook
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
            
        # Home frame
        home_frame = ttk.Frame(self.notebook)
        self.notebook.add(home_frame, text="Home")
        
        # Title
        title_label = ttk.Label(home_frame, text="MySQL Database Manager", 
                               font=('Arial', 24, 'bold'))
        title_label.pack(pady=20)
        
        # Buttons frame
        buttons_frame = ttk.Frame(home_frame)
        buttons_frame.pack(pady=20)
        
        # New Project button
        new_project_btn = ttk.Button(buttons_frame, text="Create New Project", 
                                    command=self.new_project, width=20)
        new_project_btn.pack(pady=10)
        
        # Open Project button
        open_project_btn = ttk.Button(buttons_frame, text="Open Project", 
                                     command=self.open_project, width=20)
        open_project_btn.pack(pady=10)
        
        # Recent Projects
        recent_frame = ttk.LabelFrame(home_frame, text="Recent Projects", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Recent projects list
        self.recent_listbox = tk.Listbox(recent_frame)
        self.recent_listbox.pack(fill=tk.BOTH, expand=True)
        self.recent_listbox.bind('<Double-1>', self.open_recent_project)
        
        # Load recent projects
        self.load_recent_projects()
        
    def load_recent_projects(self):
        """Load and display recent projects"""
        self.recent_listbox.delete(0, tk.END)
        projects = self.config_manager.load_projects()
        
        for project in projects:
            display_text = f"{project['name']} - {project['host']}:{project.get('port', 3306)}"
            self.recent_listbox.insert(tk.END, display_text)
            
    def new_project(self):
        """Create new project"""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Project")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Project name
        ttk.Label(frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(frame, width=30)
        name_entry.grid(row=0, column=1, pady=5)
        
        # Database name
        ttk.Label(frame, text="Database Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        db_entry = ttk.Entry(frame, width=30)
        db_entry.grid(row=1, column=1, pady=5)
        
        # MySQL settings
        ttk.Label(frame, text="Host:").grid(row=2, column=0, sticky=tk.W, pady=5)
        host_entry = ttk.Entry(frame, width=30)
        host_entry.insert(0, self.config['mysql']['host'])
        host_entry.grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Port:").grid(row=3, column=0, sticky=tk.W, pady=5)
        port_entry = ttk.Entry(frame, width=30)
        port_entry.insert(0, str(self.config['mysql']['port']))
        port_entry.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Username:").grid(row=4, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(frame, width=30)
        user_entry.insert(0, self.config['mysql']['username'])
        user_entry.grid(row=4, column=1, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=5, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(frame, width=30, show="*")
        pass_entry.insert(0, self.config['mysql']['password'])
        pass_entry.grid(row=5, column=1, pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        def create():
            project_name = name_entry.get()
            db_name = db_entry.get()
            host = host_entry.get()
            port = int(port_entry.get())
            username = user_entry.get()
            password = pass_entry.get()
            
            if not project_name or not db_name:
                messagebox.showerror("Error", "Please fill in all required fields")
                return
                
            # Update config with new connection settings
            self.config['mysql'].update({
                'host': host,
                'port': port,
                'username': username,
                'password': password
            })
            
            # Create database manager with new settings
            temp_db_manager = DatabaseManager(self.config)
            
            if temp_db_manager.connect():
                try:
                    # Create database
                    temp_db_manager.create_database(db_name)
                    temp_db_manager.disconnect()
                    
                    # Connect to new database
                    if temp_db_manager.connect(db_name):
                        # Create sample table
                        temp_db_manager.create_sample_table(db_name)
                        temp_db_manager.disconnect()
                        
                        # Add to recent projects
                        self.add_to_recent_projects(project_name, db_name, host, port)
                        
                        # Update main db manager
                        self.db_manager = temp_db_manager
                        
                        # Show main screen
                        self.show_main_screen(db_name)
                        
                        dialog.destroy()
                        self.update_status(f"Created project: {project_name}")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create project: {str(e)}")
            else:
                messagebox.showerror("Error", "Failed to connect to MySQL server")
                
        ttk.Button(button_frame, text="Create", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        name_entry.focus()
        
    def open_project(self):
        """Open existing project"""
        if not self.db_manager.connect():
            return
            
        try:
            databases = self.db_manager.get_databases()
            self.db_manager.disconnect()
            
            # Show database selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Open Project")
            dialog.geometry("300x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Select Database:").pack(pady=5)
            
            db_listbox = tk.Listbox(frame)
            db_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
            
            for db in databases:
                if db not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                    db_listbox.insert(tk.END, db)
                    
            def open_selected():
                selection = db_listbox.curselection()
                if selection:
                    db_name = db_listbox.get(selection[0])
                    self.show_main_screen(db_name)
                    dialog.destroy()
                    
            button_frame = ttk.Frame(frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Open", command=open_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get database list: {str(e)}")
            
    def open_recent_project(self, event):
        """Open recent project from list"""
        selection = self.recent_listbox.curselection()
        if selection:
            projects = self.config_manager.load_projects()
            project = projects[selection[0]]
            
            # Update config with project settings
            self.config['mysql'].update({
                'host': project['host'],
                'port': project.get('port', 3306),
                'username': project.get('username', 'root'),
                'password': project.get('password', '')
            })
            
            self.db_manager = DatabaseManager(self.config)
            self.show_main_screen(project['database'])
            
    def add_to_recent_projects(self, name, database, host, port):
        """Add project to recent projects list"""
        projects = self.config_manager.load_projects()
        
        new_project = {
            'name': name,
            'database': database,
            'host': host,
            'port': port,
            'username': self.config['mysql']['username'],
            'password': self.config['mysql']['password'],
            'last_opened': datetime.now().isoformat()
        }
        
        # Remove existing project with same database
        projects = [p for p in projects if p['database'] != database]
        projects.insert(0, new_project)
        projects = projects[:10]  # Keep only 10 recent projects
        
        self.config_manager.save_projects(projects)
        self.load_recent_projects()
        
    def show_main_screen(self, database_name):
        """Show main database management screen"""
        if not self.db_manager.connect(database_name):
            return
            
        # Clear notebook
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
            
        # Create main tabs
        self.create_query_tab()
        self.create_tables_tab()
        self.create_data_tab()
        
        self.update_status(f"Connected to database: {database_name}")
        
    def create_query_tab(self):
        """Create SQL query tab"""
        query_frame = ttk.Frame(self.notebook)
        self.notebook.add(query_frame, text="SQL Query")
        
        # Create paned window for query editor and results
        paned = ttk.PanedWindow(query_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Query editor frame
        editor_frame = ttk.Frame(paned)
        paned.add(editor_frame, weight=1)
        
        # Toolbar
        toolbar = ttk.Frame(editor_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="Execute", command=self.execute_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear", command=self.clear_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save Query", command=self.save_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load Query", command=self.load_query).pack(side=tk.LEFT, padx=2)
        
        # Query editor
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        self.query_text = tk.Text(editor_container, height=10, wrap=tk.NONE, 
                                 font=('Courier', self.config['appearance']['font_size']))
        
        # Scrollbars for query editor
        query_v_scroll = ttk.Scrollbar(editor_container, orient=tk.VERTICAL, command=self.query_text.yview)
        query_h_scroll = ttk.Scrollbar(editor_container, orient=tk.HORIZONTAL, command=self.query_text.xview)
        self.query_text.configure(yscrollcommand=query_v_scroll.set, xscrollcommand=query_h_scroll.set)
        
        self.query_text.grid(row=0, column=0, sticky='nsew')
        query_v_scroll.grid(row=0, column=1, sticky='ns')
        query_h_scroll.grid(row=1, column=0, sticky='ew')
        
        editor_container.grid_rowconfigure(0, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)
        
        # Initialize syntax highlighter
        self.sql_highlighter = SQLHighlighter(self.query_text, self.theme_manager)
        self.query_text.bind('<KeyRelease>', self.sql_highlighter.highlight)
        
        # Results frame
        results_frame = ttk.Frame(paned)
        paned.add(results_frame, weight=2)
        
        # Results toolbar
        results_toolbar = ttk.Frame(results_frame)
        results_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(results_toolbar, text="Results:").pack(side=tk.LEFT)
        ttk.Button(results_toolbar, text="Export Results", command=self.export_results).pack(side=tk.RIGHT, padx=2)
        
        # Results treeview
        self.results_tree = ttk.Treeview(results_frame)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Results scrollbars
        results_v_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        results_h_scroll = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=results_v_scroll.set, xscrollcommand=results_h_scroll.set)
        
        results_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        results_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_tables_tab(self):
        """Create tables management tab"""
        tables_frame = ttk.Frame(self.notebook)
        self.notebook.add(tables_frame, text="Tables")
        
        # Create paned window
        paned = ttk.PanedWindow(tables_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tables list frame
        tables_list_frame = ttk.LabelFrame(paned, text="Tables", padding="5")
        paned.add(tables_list_frame, weight=1)
        
        # Tables listbox
        self.tables_listbox = tk.Listbox(tables_list_frame)
        self.tables_listbox.pack(fill=tk.BOTH, expand=True)
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        
        # Refresh tables button
        ttk.Button(tables_list_frame, text="Refresh", command=self.refresh_tables).pack(pady=5)
        
        # Table info frame
        table_info_frame = ttk.LabelFrame(paned, text="Table Structure", padding="5")
        paned.add(table_info_frame, weight=2)
        
        # Table structure treeview
        self.table_structure_tree = ttk.Treeview(table_info_frame, columns=('Type', 'Null', 'Key', 'Default', 'Extra'), show='tree headings')
        self.table_structure_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure columns
        self.table_structure_tree.heading('#0', text='Column')
        self.table_structure_tree.heading('Type', text='Type')
        self.table_structure_tree.heading('Null', text='Null')
        self.table_structure_tree.heading('Key', text='Key')
        self.table_structure_tree.heading('Default', text='Default')
        self.table_structure_tree.heading('Extra', text='Extra')
        
        # Load tables
        self.refresh_tables()
        
    def create_data_tab(self):
        """Create data viewing/editing tab"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data View")
        
        # Toolbar
        toolbar = ttk.Frame(data_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(toolbar, text="Table:").pack(side=tk.LEFT, padx=5)
        
        self.table_combo = ttk.Combobox(toolbar, state="readonly", width=20)
        self.table_combo.pack(side=tk.LEFT, padx=5)
        self.table_combo.bind('<<ComboboxSelected>>', self.load_table_data)
        
        ttk.Button(toolbar, text="Refresh", command=self.refresh_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Add Row", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete Row", command=self.delete_row).pack(side=tk.LEFT, padx=5)
        
        # Data treeview
        self.data_tree = ttk.Treeview(data_frame)
        self.data_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Data scrollbars
        data_v_scroll = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        data_h_scroll = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=data_v_scroll.set, xscrollcommand=data_h_scroll.set)
        
        # Update table combo
        self.refresh_table_combo()
        
    def execute_query(self):
        """Execute SQL query"""
        query = self.query_text.get('1.0', tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a query")
            return
            
        try:
            start_time = datetime.now()
            result = self.db_manager.execute_query(query)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Add to history
            self.query_history.add_to_history(query, self.db_manager.current_database)
            
            # Clear previous results
            self.results_tree.delete(*self.results_tree.get_children())
            
            if 'columns' in result:
                # Configure columns
                self.results_tree['columns'] = result['columns']
                self.results_tree['show'] = 'headings'
                
                for col in result['columns']:
                    self.results_tree.heading(col, text=col)
                    self.results_tree.column(col, width=100)
                    
                # Insert data
                for row in result['rows']:
                    self.results_tree.insert('', tk.END, values=row)
                    
                status_msg = f"Query executed successfully. {len(result['rows'])} rows returned in {execution_time:.3f}s"
            else:
                status_msg = f"Query executed successfully. {result['rowcount']} rows affected in {execution_time:.3f}s"
                
            self.update_status(status_msg)
            
        except Exception as e:
            messagebox.showerror("Query Error", str(e))
            self.update_status(f"Query failed: {str(e)}")
            
    def clear_query(self):
        """Clear query editor"""
        self.query_text.delete('1.0', tk.END)
        
    def save_query(self):
        """Save current query as favorite"""
        query = self.query_text.get('1.0', tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "No query to save")
            return
            
        name = simpledialog.askstring("Save Query", "Enter a name for this query:")
        if name:
            self.query_history.add_favorite(name, query, self.db_manager.current_database)
            messagebox.showinfo("Success", "Query saved successfully")
            
    def load_query(self):
        """Load saved query"""
        favorites = self.query_history.load_favorites()
        if not favorites:
            messagebox.showinfo("Info", "No saved queries found")
            return
            
        # Show favorites dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Query")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Favorites list
        favorites_tree = ttk.Treeview(frame, columns=('Database', 'Created'), show='tree headings')
        favorites_tree.pack(fill=tk.BOTH, expand=True)
        
        favorites_tree.heading('#0', text='Name')
        favorites_tree.heading('Database', text='Database')
        favorites_tree.heading('Created', text='Created')
        
        for fav in favorites:
            created = datetime.fromisoformat(fav['created_at']).strftime('%Y-%m-%d %H:%M')
            favorites_tree.insert('', tk.END, text=fav['name'], 
                                values=(fav.get('database', 'N/A'), created))
                                
        def load_selected():
            selection = favorites_tree.selection()
            if selection:
                item = favorites_tree.item(selection[0])
                name = item['text']
                selected_fav = next(f for f in favorites if f['name'] == name)
                self.query_text.delete('1.0', tk.END)
                self.query_text.insert('1.0', selected_fav['query'])
                dialog.destroy()
                
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def refresh_tables(self):
        """Refresh tables list"""
        try:
            tables = self.db_manager.get_tables()
            self.tables_listbox.delete(0, tk.END)
            
            for table in tables:
                self.tables_listbox.insert(tk.END, table)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tables: {str(e)}")
            
    def on_table_select(self, event):
        """Handle table selection"""
        selection = self.tables_listbox.curselection()
        if selection:
            table_name = self.tables_listbox.get(selection[0])
            self.load_table_structure(table_name)
            
    def load_table_structure(self, table_name):
        """Load table structure"""
        try:
            result = self.db_manager.get_table_structure(table_name)
            
            # Clear previous structure
            self.table_structure_tree.delete(*self.table_structure_tree.get_children())
            
            # Insert structure data
            for row in result['rows']:
                self.table_structure_tree.insert('', tk.END, text=row[0], 
                                                values=row[1:])
                                                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table structure: {str(e)}")
            
    def refresh_table_combo(self):
        """Refresh table combo box"""
        try:
            tables = self.db_manager.get_tables()
            self.table_combo['values'] = tables
            if tables:
                self.table_combo.set(tables[0])
                self.load_table_data()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tables: {str(e)}")
            
    def load_table_data(self, event=None):
        """Load data for selected table"""
        table_name = self.table_combo.get()
        if not table_name:
            return
            
        try:
            query = f"SELECT * FROM `{table_name}` LIMIT 1000"
            result = self.db_manager.execute_query(query)
            
            # Clear previous data
            self.data_tree.delete(*self.data_tree.get_children())
            
            if 'columns' in result:
                # Configure columns
                self.data_tree['columns'] = result['columns']
                self.data_tree['show'] = 'headings'
                
                for col in result['columns']:
                    self.data_tree.heading(col, text=col)
                    self.data_tree.column(col, width=100)
                    
                # Insert data
                for row in result['rows']:
                    self.data_tree.insert('', tk.END, values=row)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table data: {str(e)}")
            
    def refresh_data(self):
        """Refresh current table data"""
        self.load_table_data()
        
    def add_row(self):
        """Add new row to table"""
        table_name = self.table_combo.get()
        if not table_name:
            messagebox.showwarning("Warning", "Please select a table")
            return
            
        # Get table structure to create input dialog
        try:
            structure = self.db_manager.get_table_structure(table_name)
            columns = [row[0] for row in structure['rows'] if row[5] != 'auto_increment']
            
            # Create input dialog
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Add Row to {table_name}")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            entries = {}
            for i, col in enumerate(columns):
                ttk.Label(frame, text=f"{col}:").grid(row=i, column=0, sticky=tk.W, pady=2)
                entry = ttk.Entry(frame, width=30)
                entry.grid(row=i, column=1, pady=2)
                entries[col] = entry
                
            def insert_row():
                values = []
                placeholders = []
                
                for col in columns:
                    value = entries[col].get()
                    if value:
                        values.append(value)
                        placeholders.append('%s')
                    else:
                        placeholders.append('NULL')
                        
                if values:
                    query = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    try:
                        self.db_manager.execute_query(query, values, fetch=False)
                        messagebox.showinfo("Success", "Row added successfully")
                        dialog.destroy()
                        self.refresh_data()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to add row: {str(e)}")
                        
            button_frame = ttk.Frame(frame)
            button_frame.grid(row=len(columns), column=0, columnspan=2, pady=20)
            
            ttk.Button(button_frame, text="Add", command=insert_row).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get table structure: {str(e)}")
            
    def delete_row(self):
        """Delete selected row from table"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected row?"):
            # Implementation would require primary key identification
            messagebox.showinfo("Info", "Delete functionality requires primary key implementation")
            
    def export_results(self):
        """Export query results to file"""
        if not self.results_tree.get_children():
            messagebox.showwarning("Warning", "No results to export")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Get data from treeview
                columns = [self.results_tree.heading(col)['text'] for col in self.results_tree['columns']]
                data = []
                
                for child in self.results_tree.get_children():
                    row = [self.results_tree.item(child)['values'][i] for i in range(len(columns))]
                    data.append(row)
                    
                if filename.endswith('.xlsx'):
                    # Export to Excel
                    df = pd.DataFrame(data, columns=columns)
                    df.to_excel(filename, index=False)
                else:
                    # Export to CSV
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows(data)
                        
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")
                
    def import_data(self):
        """Import data from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            # Implementation for data import
            messagebox.showinfo("Info", "Import functionality would be implemented here")
            
    def export_data(self):
        """Export database data"""
        # Implementation for database export
        messagebox.showinfo("Info", "Export functionality would be implemented here")
        
    def show_preferences(self):
        """Show preferences dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Preferences")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Database settings tab
        db_frame = ttk.Frame(notebook)
        notebook.add(db_frame, text="Database")
        
        db_content = ttk.Frame(db_frame, padding="20")
        db_content.pack(fill=tk.BOTH, expand=True)
        
        # MySQL settings
        ttk.Label(db_content, text="MySQL Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        host_entry = ttk.Entry(db_content, width=30)
        host_entry.insert(0, self.config['mysql']['host'])
        host_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(db_content, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        port_entry = ttk.Entry(db_content, width=30)        
        port_entry.insert(0, str(self.config['mysql']['port']))
        port_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(db_content, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(db_content, width=30)
        user_entry.insert(0, self.config['mysql']['username'])
        user_entry.grid(row=2, column=1, pady=5)
        
        ttk.Label(db_content, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(db_content, width=30, show="*")
        pass_entry.insert(0, self.config['mysql']['password'])
        pass_entry.grid(row=3, column=1, pady=5)
        
        # Appearance settings tab
        app_frame = ttk.Frame(notebook)
        notebook.add(app_frame, text="Appearance")
        
        app_content = ttk.Frame(app_frame, padding="20")
        app_content.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(app_content, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(value=self.config['appearance']['theme'])
        theme_combo = ttk.Combobox(app_content, textvariable=theme_var, state="readonly")
        theme_combo['values'] = list(self.theme_manager.THEMES.keys())
        theme_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(app_content, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        font_size_var = tk.StringVar(value=str(self.config['appearance']['font_size']))
        font_spin = ttk.Spinbox(app_content, from_=8, to=20, textvariable=font_size_var, width=5)
        font_spin.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Editor settings tab
        editor_frame = ttk.Frame(notebook)
        notebook.add(editor_frame, text="Editor")
        
        editor_content = ttk.Frame(editor_frame, padding="20")
        editor_content.pack(fill=tk.BOTH, expand=True)
        
        auto_complete_var = tk.BooleanVar(value=self.config['editor']['auto_complete'])
        auto_complete_cb = ttk.Checkbutton(editor_content, text="Enable Auto-complete", 
                                          variable=auto_complete_var)
        auto_complete_cb.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        syntax_highlight_var = tk.BooleanVar(value=self.config['editor']['syntax_highlighting'])
        syntax_highlight_cb = ttk.Checkbutton(editor_content, text="Enable Syntax Highlighting", 
                                             variable=syntax_highlight_var)
        syntax_highlight_cb.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_preferences():
            # Update database settings
            self.config['mysql']['host'] = host_entry.get()
            self.config['mysql']['port'] = int(port_entry.get())
            self.config['mysql']['username'] = user_entry.get()
            self.config['mysql']['password'] = pass_entry.get()
            
            # Update appearance settings
            self.config['appearance']['theme'] = theme_var.get()
            self.config['appearance']['font_size'] = int(font_size_var.get())
            
            # Update editor settings
            self.config['editor']['auto_complete'] = auto_complete_var.get()
            self.config['editor']['syntax_highlighting'] = syntax_highlight_var.get()
            
            # Save config
            self.config_manager.save_config(self.config)
            
            # Apply theme
            self.theme_manager.apply_theme(theme_var.get())
            
            # Update font size in query editor
            if hasattr(self, 'query_text'):
                self.query_text.configure(font=('Courier', int(font_size_var.get())))
            
            dialog.destroy()
            messagebox.showinfo("Preferences Saved", "Preferences have been updated")
            
        ttk.Button(button_frame, text="Save", command=save_preferences).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def show_query_history(self):
        """Show query history dialog"""
        history = self.query_history.load_history()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Query History")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for history
        history_tree = ttk.Treeview(frame, columns=('Database', 'Timestamp'), show='tree headings')
        history_tree.pack(fill=tk.BOTH, expand=True)
        
        history_tree.heading('#0', text='Query')
        history_tree.heading('Database', text='Database')
        history_tree.heading('Timestamp', text='Timestamp')
        
        history_tree.column('#0', width=400)
        history_tree.column('Database', width=150)
        history_tree.column('Timestamp', width=150)
        
        # Add history items
        for item in history:
            timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')
            query_short = (item['query'][:100] + '...') if len(item['query']) > 100 else item['query']
            history_tree.insert('', tk.END, text=query_short, 
                                values=(item.get('database', 'N/A'), timestamp),
                                tags=('full_query',))
            history_tree.tag_configure('full_query', font=('Courier', 9))
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def load_query():
            selection = history_tree.selection()
            if selection:
                item = history_tree.item(selection[0])
                query_index = history_tree.index(selection[0])
                full_query = history[query_index]['query']
                
                if hasattr(self, 'query_text'):
                    self.query_text.delete('1.0', tk.END)
                    self.query_text.insert('1.0', full_query)
                    
                dialog.destroy()
                
        def delete_query():
            selection = history_tree.selection()
            if selection:
                if messagebox.askyesno("Confirm", "Delete selected query from history?"):
                    item_index = history_tree.index(selection[0])
                    history.pop(item_index)
                    self.query_history.save_history(history)
                    history_tree.delete(selection[0])
                    
        ttk.Button(button_frame, text="Load", command=load_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=delete_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def show_table_designer(self):
        """Show table designer interface"""
        if not self.db_manager.connection or not self.db_manager.connection.is_connected():
            messagebox.showerror("Error", "Not connected to a database")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Table Designer")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Table name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Table Name:").pack(side=tk.LEFT)
        table_name_var = tk.StringVar()
        table_name_entry = ttk.Entry(name_frame, textvariable=table_name_var, width=30)
        table_name_entry.pack(side=tk.LEFT, padx=5)
        
        # Columns frame
        columns_frame = ttk.LabelFrame(main_frame, text="Columns")
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview for columns
        columns_tree = ttk.Treeview(columns_frame, columns=('Type', 'Size', 'PK', 'NN', 'Default'), show='tree headings')
        columns_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns_tree.heading('#0', text='Name')
        columns_tree.heading('Type', text='Type')
        columns_tree.heading('Size', text='Size')
        columns_tree.heading('PK', text='PK')
        columns_tree.heading('NN', text='NN')
        columns_tree.heading('Default', text='Default')
        
        columns_tree.column('#0', width=150)
        columns_tree.column('Type', width=100)
        columns_tree.column('Size', width=50)
        columns_tree.column('PK', width=30)
        columns_tree.column('NN', width=30)
        columns_tree.column('Default', width=100)
        
        # Column actions
        col_btn_frame = ttk.Frame(columns_frame)
        col_btn_frame.pack(fill=tk.X, pady=5)
        
        def add_column():
            col_dialog = tk.Toplevel(dialog)
            col_dialog.title("Add Column")
            col_dialog.geometry("400x300")
            col_dialog.transient(dialog)
            col_dialog.grab_set()
            
            frame = ttk.Frame(col_dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Column Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            col_name_var = tk.StringVar()
            col_name_entry = ttk.Entry(frame, textvariable=col_name_var)
            col_name_entry.grid(row=0, column=1, pady=5)
            
            ttk.Label(frame, text="Data Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
            type_var = tk.StringVar(value="VARCHAR")
            type_combo = ttk.Combobox(frame, textvariable=type_var, state="readonly")
            type_combo['values'] = ["INT", "VARCHAR", "TEXT", "DATE", "DATETIME", "FLOAT", "DOUBLE", "BOOLEAN"]
            type_combo.grid(row=1, column=1, pady=5)
            
            ttk.Label(frame, text="Size/Length:").grid(row=2, column=0, sticky=tk.W, pady=5)
            size_var = tk.StringVar(value="255")
            size_entry = ttk.Entry(frame, textvariable=size_var)
            size_entry.grid(row=2, column=1, pady=5)
            
            pk_var = tk.BooleanVar()
            nn_var = tk.BooleanVar()
            default_var = tk.StringVar()
            
            ttk.Checkbutton(frame, text="Primary Key", variable=pk_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
            ttk.Checkbutton(frame, text="Not Null", variable=nn_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
            
            ttk.Label(frame, text="Default Value:").grid(row=5, column=0, sticky=tk.W, pady=5)
            ttk.Entry(frame, textvariable=default_var).grid(row=5, column=1, pady=5)
            
            def save_column():
                name = col_name_var.get().strip()
                if not name:
                    messagebox.showerror("Error", "Column name is required")
                    return
                    
                # Add to treeview
                columns_tree.insert('', tk.END, text=name, values=(
                    type_var.get(),
                    size_var.get(),
                    "PK" if pk_var.get() else "",
                    "NN" if nn_var.get() else "",
                    default_var.get()
                ))
                col_dialog.destroy()
                
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
            
            ttk.Button(btn_frame, text="Save", command=save_column).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=col_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        def remove_column():
            selection = columns_tree.selection()
            if selection:
                columns_tree.delete(selection[0])
                
        ttk.Button(col_btn_frame, text="Add Column", command=add_column).pack(side=tk.LEFT, padx=5)
        ttk.Button(col_btn_frame, text="Remove Selected", command=remove_column).pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def create_table():
            table_name = table_name_var.get().strip()
            if not table_name:
                messagebox.showerror("Error", "Table name is required")
                return
                
            if not columns_tree.get_children():
                messagebox.showerror("Error", "At least one column is required")
                return
                
            # Build CREATE TABLE statement
            columns = []
            primary_keys = []
            
            for child in columns_tree.get_children():
                item = columns_tree.item(child)
                name = item['text']
                values = item['values']
                col_def = f"`{name}` {values[0]}"
                
                # Add size if applicable
                if values[0] in ["VARCHAR", "CHAR"] and values[1]:
                    col_def += f"({values[1]})"
                
                # Add constraints
                if values[2]:  # Primary Key
                    primary_keys.append(f"`{name}`")
                    col_def += " NOT NULL"
                elif values[3]:  # Not Null
                    col_def += " NOT NULL"
                    
                if values[4]:  # Default value
                    col_def += f" DEFAULT '{values[4]}'"
                
                columns.append(col_def)
            
            # Add primary key constraint if any
            if primary_keys:
                columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
            
            # Create the table
            try:
                cursor = self.db_manager.connection.cursor()
                create_stmt = f"CREATE TABLE `{table_name}` (\n  " + ",\n  ".join(columns) + "\n)"
                cursor.execute(create_stmt)
                self.db_manager.connection.commit()
                
                messagebox.showinfo("Success", f"Table '{table_name}' created successfully")
                dialog.destroy()
                
                # Refresh tables list
                self.refresh_tables()
                self.refresh_table_combo()
                
            except Error as e:
                messagebox.showerror("Database Error", f"Failed to create table: {str(e)}")
        
        ttk.Button(button_frame, text="Create Table", command=create_table).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def show_relationship_viewer(self):
        """Show database relationship viewer"""
        if not self.db_manager.connection or not self.db_manager.connection.is_connected():
            messagebox.showerror("Error", "Not connected to a database")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Database Relationship Viewer")
        dialog.geometry("1000x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        try:
            # Get foreign key relationships
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT 
                    TABLE_NAME, 
                    COLUMN_NAME, 
                    REFERENCED_TABLE_NAME, 
                    REFERENCED_COLUMN_NAME 
                FROM 
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE 
                    TABLE_SCHEMA = %s AND 
                    REFERENCED_TABLE_NAME IS NOT NULL
            """, (self.db_manager.current_database,))
            
            relationships = cursor.fetchall()
            
            if not relationships:
                messagebox.showinfo("Info", "No foreign key relationships found in this database")
                return
                
            # Create treeview
            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            tree = ttk.Treeview(tree_frame, columns=('Column', 'References', 'Referenced Column'), show='tree headings')
            tree.pack(fill=tk.BOTH, expand=True)
            
            tree.heading('#0', text='Table')
            tree.heading('Column', text='Column')
            tree.heading('References', text='References')
            tree.heading('Referenced Column', text='Referenced Column')
            
            # Group relationships by table
            table_relations = {}
            for rel in relationships:
                table_name, column_name, ref_table, ref_column = rel
                if table_name not in table_relations:
                    table_relations[table_name] = []
                table_relations[table_name].append((column_name, ref_table, ref_column))
            
            # Add to treeview
            for table, relations in table_relations.items():
                table_node = tree.insert('', tk.END, text=table, values=('', '', ''))
                for col, ref_table, ref_col in relations:
                    tree.insert(table_node, tk.END, text='', values=(col, ref_table, ref_col))
                    
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to get relationships: {str(e)}")
            
    def show_about(self):
        """Show about dialog"""
        about_text = (
            "Professional MySQL Database Manager\n"
            "Version 1.0\n\n"
            "A comprehensive database management tool\n"
            "with advanced features for database administrators\n\n"
            "© 2023 Database Solutions Inc."
        )
        
        messagebox.showinfo("About", about_text)
        
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MySQLDatabaseManager()
    app.run()