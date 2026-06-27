# -*- coding: utf-8 -*-
import time
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import pyautogui
import cv2
import numpy as np

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
TEMPLATE_DIR = os.path.join(os.path.join(os.path.expanduser('~')), 'RlyehBotTemplates')

PRIORITY_FILE = os.path.join(TEMPLATE_DIR, 'priorities.json')

CATEGORIES = [
    ('battle', '战斗按钮'),
    ('event', '事件选项'),
    ('reward', '奖励领取'),
    ('buff', 'Buff增益'),
    ('debuff', 'Debuff减益'),
    ('equipment', '装备选择'),
    ('stage', '关卡选择'),
    ('character', '角色选择'),
    ('common', '通用按钮'),
]

def load_config():
    default_config = {
        'confidence': 0.8,
        'auto_battle': True,
        'auto_event': True,
        'auto_rewards': True,
        'max_battles': 999,
        'battle_delay': 3,
        'click_delay': 0.8,
        'roguelike_settings': {
            'enabled': True,
            'debuff_priority': 3,
            'buff_priority': 2,
            'equipment_priority': 4,
            'stage_priority': 1,
            'character_priority': 1
        }
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'roguelike_settings' not in config:
                    config['roguelike_settings'] = default_config['roguelike_settings']
                return config
        except:
            pass
    return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass

def load_priorities():
    if os.path.exists(PRIORITY_FILE):
        try:
            with open(PRIORITY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_priorities(priorities):
    try:
        with open(PRIORITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(priorities, f, indent=2, ensure_ascii=False)
    except:
        pass

def ensure_dirs():
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
    for cat, _ in CATEGORIES:
        cat_dir = os.path.join(TEMPLATE_DIR, cat)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)

class RegionSelector:
    def __init__(self, root, screenshot, callback, category):
        self.root = root
        self.screenshot = screenshot
        self.callback = callback
        self.category = category
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect = None
        self.drawing = False
        
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title("Select Region - Click and drag to select")
        self.toplevel.attributes('-fullscreen', True)
        self.toplevel.attributes('-alpha', 0.8)
        self.toplevel.configure(cursor='cross')
        
        self.canvas = tk.Canvas(self.toplevel, cursor='cross')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.img_tk = ImageTk.PhotoImage(screenshot)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        
        self.info_text = self.canvas.create_text(
            20, 20, anchor=tk.NW,
            text=f"Category: {category}\nDrag to select region\nRight click or ESC to cancel",
            fill='white', font=('Arial', 14, 'bold')
        )
        self.canvas.itemconfig(self.info_text, state='normal')
        
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Button-3>', self.on_cancel)
        self.toplevel.bind('<Escape>', self.on_cancel)
        
        self.toplevel.focus_force()
    
    def on_press(self, event):
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
    
    def on_drag(self, event):
        if self.drawing and self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        if not self.drawing:
            return
        self.drawing = False
        self.end_x = event.x
        self.end_y = event.y
        
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        if x2 - x1 < 5 or y2 - y1 < 5:
            return
        
        self.toplevel.destroy()
        
        cropped = self.screenshot.crop((x1, y1, x2, y2))
        self.callback(cropped, x1, y1, x2, y2)
    
    def on_cancel(self, event=None):
        self.toplevel.destroy()
        self.callback(None, 0, 0, 0, 0)

class ImageBot:
    def __init__(self, config, log_callback):
        self.config = config
        self.log = log_callback
        self.running = False
        self.priorities = load_priorities()
    
    def get_template_priority(self, template_path):
        filename = os.path.basename(template_path)
        category = os.path.basename(os.path.dirname(template_path))
        key = f"{category}/{filename}"
        return self.priorities.get(key, 1)
    
    def find_image(self, template_path, confidence=None, region=None):
        if confidence is None:
            confidence = self.config.get('confidence', 0.8)
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            template = cv2.imread(template_path)
            if template is None:
                return None
            
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y, max_val)
            
            return None
        except Exception as e:
            return None
    
    def find_best_in_folder(self, folder_name, confidence=None):
        folder_path = os.path.join(TEMPLATE_DIR, folder_name)
        if not os.path.exists(folder_path):
            return None
        
        matches = []
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                template_path = os.path.join(folder_path, filename)
                result = self.find_image(template_path, confidence)
                if result:
                    x, y, conf = result
                    priority = self.get_template_priority(template_path)
                    score = conf * (1 + priority * 0.1)
                    matches.append((score, x, y, conf, filename, priority))
        
        if matches:
            matches.sort(key=lambda m: m[0], reverse=True)
            return matches[0]
        
        return None
    
    def click_at(self, x, y, clicks=1, interval=0.2):
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval)
            time.sleep(self.config.get('click_delay', 0.8))
            return True
        except:
            return False
    
    def find_and_click(self, folder_name, confidence=None):
        result = self.find_best_in_folder(folder_name, confidence)
        if result:
            score, x, y, conf, filename, priority = result
            self.log(f"找到: {filename} (置信度:{conf:.2f} 优先级:{priority})")
            return self.click_at(x, y)
        return False
    
    def is_image_present(self, folder_name, confidence=None):
        return self.find_best_in_folder(folder_name, confidence) is not None
    
    def take_screenshot(self, save_path=None):
        try:
            screenshot = pyautogui.screenshot()
            if save_path:
                screenshot.save(save_path)
            return screenshot
        except:
            return None

class RlyehBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RlyehBot - Auto Bot (Vision)")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        ensure_dirs()
        self.config = load_config()
        self.bot = ImageBot(self.config, self.log)
        self.running = False
        self.thread = None
        self.battles = 0
        self.priorities = load_priorities()
        self.current_template_category = 'battle'
        
        self.create_widgets()
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.capture_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text=" Main ")
        self.notebook.add(self.capture_tab, text=" Templates ")
        self.notebook.add(self.settings_tab, text=" Settings ")
        
        self.create_main_tab()
        self.create_capture_tab()
        self.create_settings_tab()
    
    def create_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="RlyehBot - Vision Auto Bot", font=("Microsoft YaHei", 14, "bold"))
        title.pack(pady=(0, 10))
        
        info_frame = ttk.LabelFrame(main_frame, text=" Status ", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(info_frame, text="Status: Ready", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.battles_label = ttk.Label(info_frame, text="Battles: 0")
        self.battles_label.pack(side=tk.RIGHT, padx=5)
        
        func_frame = ttk.LabelFrame(main_frame, text=" Functions ", padding="10")
        func_frame.pack(fill=tk.X, pady=5)
        
        self.auto_battle_var = tk.BooleanVar(value=self.config['auto_battle'])
        ttk.Checkbutton(func_frame, text="Auto Battle", variable=self.auto_battle_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.auto_event_var = tk.BooleanVar(value=self.config['auto_event'])
        ttk.Checkbutton(func_frame, text="Auto Event", variable=self.auto_event_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        self.auto_rewards_var = tk.BooleanVar(value=self.config['auto_rewards'])
        ttk.Checkbutton(func_frame, text="Auto Rewards", variable=self.auto_rewards_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.roguelike_enabled_var = tk.BooleanVar(value=self.config.get('roguelike_settings', {}).get('enabled', True))
        ttk.Checkbutton(func_frame, text="Roguelike Auto Select", variable=self.roguelike_enabled_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(func_frame, text="Max Battles:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.max_battles_var = tk.StringVar(value=str(self.config['max_battles']))
        ttk.Entry(func_frame, textvariable=self.max_battles_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(ctrl_frame, text="Start Bot", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.screenshot_btn = ttk.Button(ctrl_frame, text="Screenshot", command=self.take_full_screenshot)
        self.screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text=" Log ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_capture_tab(self):
        cap_frame = ttk.Frame(self.capture_tab, padding="10")
        cap_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(cap_frame, text="Template Capture & Management", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        cap_tool_frame = ttk.LabelFrame(cap_frame, text=" Capture Tool ", padding="10")
        cap_tool_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cap_tool_frame, text="Target Category:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.cap_category_var = tk.StringVar(value='battle')
        cap_combo = ttk.Combobox(cap_tool_frame, textvariable=self.cap_category_var, state='readonly', width=20)
        cap_combo['values'] = [f"{cat} - {name}" for cat, name in CATEGORIES]
        cap_combo.current(0)
        cap_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        cap_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        self.capture_btn = ttk.Button(cap_tool_frame, text="Capture Region (3s delay)", command=self.start_capture)
        self.capture_btn.grid(row=0, column=2, padx=10, pady=5)
        
        self.open_template_btn = ttk.Button(cap_tool_frame, text="Open Template Folder", command=self.open_template_dir)
        self.open_template_btn.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(cap_tool_frame, text="How to use: Click button, switch to game in 3s, drag to select button region", 
                  foreground="gray").grid(row=1, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        
        list_frame = ttk.LabelFrame(cap_frame, text=" Template List ", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        list_toolbar = ttk.Frame(list_frame)
        list_toolbar.pack(fill=tk.X, pady=3)
        
        ttk.Label(list_toolbar, text="Category:").pack(side=tk.LEFT, padx=3)
        
        self.view_category_var = tk.StringVar(value='battle')
        view_combo = ttk.Combobox(list_toolbar, textvariable=self.view_category_var, state='readonly', width=15)
        view_combo['values'] = [f"{cat} - {name}" for cat, name in CATEGORIES]
        view_combo.current(0)
        view_combo.pack(side=tk.LEFT, padx=3)
        view_combo.bind('<<ComboboxSelected>>', self.refresh_template_list)
        
        ttk.Button(list_toolbar, text="Refresh", command=self.refresh_template_list).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="Set Priority", command=self.set_template_priority).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="Delete", command=self.delete_template).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="Rename", command=self.rename_template).pack(side=tk.LEFT, padx=3)
        
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.template_tree = ttk.Treeview(tree_frame, columns=("priority", "size"), show="tree headings")
        self.template_tree.heading("#0", text="Template")
        self.template_tree.heading("priority", text="Priority")
        self.template_tree.heading("size", text="Size")
        self.template_tree.column("priority", width=80, anchor=tk.CENTER)
        self.template_tree.column("size", width=100, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.template_tree.yview)
        self.template_tree.configure(yscrollcommand=scrollbar.set)
        
        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_tree.bind('<Double-1>', self.on_template_double_click)
        
        self.refresh_template_list()
    
    def create_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text="Settings", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        param_frame = ttk.LabelFrame(settings_frame, text=" Recognition ", padding="10")
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="Confidence (0.5-1.0):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.confidence_var = tk.DoubleVar(value=self.config.get('confidence', 0.8))
        ttk.Scale(param_frame, from_=0.5, to=1.0, variable=self.confidence_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.confidence_label = ttk.Label(param_frame, text=f"{self.config.get('confidence', 0.8):.2f}")
        self.confidence_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.confidence_var.trace_add("write", lambda *args: self.confidence_label.config(text=f"{self.confidence_var.get():.2f}"))
        
        ttk.Label(param_frame, text="Battle Delay (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.battle_delay_var = tk.StringVar(value=str(self.config.get('battle_delay', 3)))
        ttk.Entry(param_frame, textvariable=self.battle_delay_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(param_frame, text="Click Delay (s):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.click_delay_var = tk.StringVar(value=str(self.config.get('click_delay', 0.8)))
        ttk.Entry(param_frame, textvariable=self.click_delay_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        rog_frame = ttk.LabelFrame(settings_frame, text=" Roguelike Priority ", padding="10")
        rog_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rog_frame, text="Higher number = higher priority (1-10)").grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=3)
        
        rog = self.config.get('roguelike_settings', {})
        
        ttk.Label(rog_frame, text="Stage:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=3)
        self.stage_priority_var = tk.IntVar(value=rog.get('stage_priority', 1))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.stage_priority_var, width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Character:").grid(row=1, column=2, sticky=tk.E, padx=5, pady=3)
        self.char_priority_var = tk.IntVar(value=rog.get('character_priority', 1))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.char_priority_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Buff:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.buff_priority_var = tk.IntVar(value=rog.get('buff_priority', 2))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.buff_priority_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Debuff:").grid(row=2, column=2, sticky=tk.E, padx=5, pady=3)
        self.debuff_priority_var = tk.IntVar(value=rog.get('debuff_priority', 3))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.debuff_priority_var, width=5).grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Equipment:").grid(row=3, column=0, sticky=tk.E, padx=5, pady=3)
        self.equip_priority_var = tk.IntVar(value=rog.get('equipment_priority', 4))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.equip_priority_var, width=5).grid(row=3, column=1, sticky=tk.W, padx=5, pady=3)
        
        save_frame = ttk.Frame(settings_frame)
        save_frame.pack(fill=tk.X, pady=20)
        
        self.save_btn = ttk.Button(save_frame, text="Save Settings", command=self.save_settings)
        self.save_btn.pack(side=tk.LEFT, padx=5)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def open_template_dir(self):
        try:
            os.startfile(TEMPLATE_DIR)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {str(e)}")
    
    def on_category_change(self, event):
        selected = self.cap_category_var.get()
        cat = selected.split(' - ')[0] if ' - ' in selected else selected
        self.view_category_var.set(selected)
        self.refresh_template_list()
    
    def start_capture(self):
        selected = self.cap_category_var.get()
        cat = selected.split(' - ')[0] if ' - ' in selected else selected
        
        self.log(f"3秒后开始截图，请切换到游戏窗口...")
        self.root.update()
        
        self.root.after(3000, lambda: self.do_capture(cat))
    
    def do_capture(self, category):
        try:
            screenshot = pyautogui.screenshot()
            selector = RegionSelector(self.root, screenshot, 
                                      lambda img, x1, y1, x2, y2: self.on_capture_complete(img, category),
                                      category)
        except Exception as e:
            messagebox.showerror("Error", f"Capture failed: {str(e)}")
    
    def on_capture_complete(self, cropped_image, category):
        if cropped_image is None:
            self.log("已取消截图")
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{category}_{timestamp}.png"
        filepath = os.path.join(TEMPLATE_DIR, category, filename)
        
        try:
            cropped_image.save(filepath)
            
            key = f"{category}/{filename}"
            self.priorities[key] = 1
            save_priorities(self.priorities)
            
            self.log(f"模板已保存: {filename}")
            self.refresh_template_list()
            messagebox.showinfo("Success", f"Template saved:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}")
    
    def get_view_category(self):
        selected = self.view_category_var.get()
        return selected.split(' - ')[0] if ' - ' in selected else selected
    
    def refresh_template_list(self, event=None):
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)
        
        cat = self.get_view_category()
        cat_path = os.path.join(TEMPLATE_DIR, cat)
        
        if not os.path.exists(cat_path):
            return
        
        files = sorted([f for f in os.listdir(cat_path) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        
        for filename in files:
            filepath = os.path.join(cat_path, filename)
            try:
                size = os.path.getsize(filepath)
                size_str = f"{size/1024:.1f} KB"
                
                key = f"{cat}/{filename}"
                priority = self.priorities.get(key, 1)
                
                self.template_tree.insert("", tk.END, text=filename, values=(priority, size_str))
            except:
                pass
    
    def get_selected_template(self):
        selection = self.template_tree.selection()
        if not selection:
            return None, None
        
        item = selection[0]
        filename = self.template_tree.item(item, "text")
        cat = self.get_view_category()
        return cat, filename
    
    def set_template_priority(self):
        cat, filename = self.get_selected_template()
        if not filename:
            messagebox.showwarning("Warning", "Please select a template first")
            return
        
        key = f"{cat}/{filename}"
        current = self.priorities.get(key, 1)
        
        new_priority = simpledialog.askinteger("Set Priority", 
                                                f"Set priority for {filename}\n(1-10, higher = match first):",
                                                minvalue=1, maxvalue=10, initialvalue=current)
        if new_priority is not None:
            self.priorities[key] = new_priority
            save_priorities(self.priorities)
            self.bot.priorities = self.priorities
            self.refresh_template_list()
            self.log(f"优先级已设置: {filename} = {new_priority}")
    
    def delete_template(self):
        cat, filename = self.get_selected_template()
        if not filename:
            messagebox.showwarning("Warning", "Please select a template first")
            return
        
        if not messagebox.askyesno("Confirm", f"Delete {filename}?"):
            return
        
        filepath = os.path.join(TEMPLATE_DIR, cat, filename)
        try:
            os.remove(filepath)
            
            key = f"{cat}/{filename}"
            if key in self.priorities:
                del self.priorities[key]
                save_priorities(self.priorities)
            
            self.refresh_template_list()
            self.log(f"已删除: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {str(e)}")
    
    def rename_template(self):
        cat, filename = self.get_selected_template()
        if not filename:
            messagebox.showwarning("Warning", "Please select a template first")
            return
        
        new_name = simpledialog.askstring("Rename", "New name (without extension):",
                                          initialvalue=os.path.splitext(filename)[0])
        if not new_name:
            return
        
        ext = os.path.splitext(filename)[1]
        new_filename = new_name + ext
        
        old_path = os.path.join(TEMPLATE_DIR, cat, filename)
        new_path = os.path.join(TEMPLATE_DIR, cat, new_filename)
        
        try:
            os.rename(old_path, new_path)
            
            old_key = f"{cat}/{filename}"
            new_key = f"{cat}/{new_filename}"
            if old_key in self.priorities:
                self.priorities[new_key] = self.priorities[old_key]
                del self.priorities[old_key]
                save_priorities(self.priorities)
            
            self.refresh_template_list()
            self.log(f"已重命名: {filename} -> {new_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Rename failed: {str(e)}")
    
    def on_template_double_click(self, event):
        cat, filename = self.get_selected_template()
        if not filename:
            return
        
        filepath = os.path.join(TEMPLATE_DIR, cat, filename)
        try:
            os.startfile(filepath)
        except:
            pass
    
    def take_full_screenshot(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        save_path = os.path.join(os.path.expanduser('~'), filename)
        self.bot.take_screenshot(save_path)
        messagebox.showinfo("Screenshot", f"Saved to:\n{save_path}")
    
    def save_settings(self):
        self.config['confidence'] = self.confidence_var.get()
        self.config['battle_delay'] = float(self.battle_delay_var.get())
        self.config['click_delay'] = float(self.click_delay_var.get())
        self.config['auto_battle'] = self.auto_battle_var.get()
        self.config['auto_event'] = self.auto_event_var.get()
        self.config['auto_rewards'] = self.auto_rewards_var.get()
        self.config['max_battles'] = int(self.max_battles_var.get())
        
        rog = self.config.get('roguelike_settings', {})
        rog['enabled'] = self.roguelike_enabled_var.get()
        rog['stage_priority'] = self.stage_priority_var.get()
        rog['character_priority'] = self.char_priority_var.get()
        rog['buff_priority'] = self.buff_priority_var.get()
        rog['debuff_priority'] = self.debuff_priority_var.get()
        rog['equipment_priority'] = self.equip_priority_var.get()
        self.config['roguelike_settings'] = rog
        
        save_config(self.config)
        self.bot.config = self.config
        messagebox.showinfo("Saved", "Settings saved!")
    
    def collect_rewards(self):
        if not self.auto_rewards_var.get():
            return False
        if self.bot.find_and_click('reward'):
            self.log("Collecting rewards...")
            time.sleep(1)
            self.bot.find_and_click('common')
            return True
        return False
    
    def select_event(self):
        if not self.auto_event_var.get():
            return False
        if self.bot.find_and_click('event'):
            self.log("Selecting event...")
            time.sleep(1)
            self.bot.find_and_click('common')
            return True
        return False
    
    def select_roguelike_option(self):
        rog = self.config.get('roguelike_settings', {})
        if not rog.get('enabled', True):
            return False
        
        priority_order = [
            ('stage', rog.get('stage_priority', 1)),
            ('character', rog.get('character_priority', 1)),
            ('buff', rog.get('buff_priority', 2)),
            ('debuff', rog.get('debuff_priority', 3)),
            ('equipment', rog.get('equipment_priority', 4)),
        ]
        priority_order.sort(key=lambda x: x[1], reverse=True)
        
        for folder, _ in priority_order:
            if self.bot.find_and_click(folder):
                self.log(f"Roguelike select: {folder}")
                time.sleep(1)
                self.bot.find_and_click('common')
                time.sleep(0.5)
                return True
        
        return False
    
    def start_battle(self):
        if not self.auto_battle_var.get():
            return False
        if self.bot.find_and_click('battle'):
            self.log("Battle started!")
            time.sleep(2)
            return True
        return False
    
    def wait_battle_finish(self):
        self.log("Waiting for battle to finish...")
        timeout = 180
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.running:
                return "stopped"
            
            if self.bot.is_image_present('reward'):
                self.log("Battle finished!")
                self.bot.find_and_click('common')
                time.sleep(1)
                return "success"
            
            if self.bot.is_image_present('battle', confidence=0.85):
                self.log("Battle may have ended, checking...")
                time.sleep(2)
                if self.bot.is_image_present('battle', confidence=0.85):
                    return "success"
            
            time.sleep(3)
        
        return "timeout"
    
    def bot_loop(self):
        self.log("Bot started!")
        self.battles = 0
        max_battles = int(self.max_battles_var.get())
        
        try:
            while self.running and self.battles < max_battles:
                self.collect_rewards()
                time.sleep(1)
                
                self.select_roguelike_option()
                time.sleep(1)
                
                self.select_event()
                time.sleep(1)
                
                if self.start_battle():
                    result = self.wait_battle_finish()
                    
                    if result == "success":
                        self.battles += 1
                        self.root.after(0, lambda: self.battles_label.config(text=f"Battles: {self.battles}"))
                        self.log(f"Battle {self.battles} complete!")
                    elif result == "stopped":
                        break
                    elif result == "timeout":
                        self.log("Battle timeout, continue...")
                else:
                    self.log("No battle button found, checking again...")
                    time.sleep(5)
                
                time.sleep(self.config.get('battle_delay', 3))
        
        except Exception as e:
            self.log(f"Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.running = False
            self.root.after(0, self.on_bot_stopped)
    
    def start_bot(self):
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Running", foreground="green")
        
        self.thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.thread.start()
    
    def stop_bot(self):
        self.running = False
        self.log("Stopping bot...")
        self.status_label.config(text="Status: Stopping", foreground="orange")
    
    def on_bot_stopped(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log("Bot stopped.")

def main():
    root = tk.Tk()
    
    try:
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
    except:
        pass
    
    app = RlyehBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
