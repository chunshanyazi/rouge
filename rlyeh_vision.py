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
    ('menu', '主菜单按钮'),
    ('start_apoc', '开始肉鸽'),
    ('confirm', '确认/决定'),
    ('cancel', '取消/返回'),
    ('close', '关闭弹窗'),
    ('character', '角色选择'),
    ('stage_normal', '普通关卡'),
    ('stage_elite', '精英关卡'),
    ('stage_boss', 'Boss关卡'),
    ('stage_event', '事件关卡'),
    ('stage_shop', '商店关卡'),
    ('battle_start', '战斗开始'),
    ('battle_speed', '加速/跳过'),
    ('battle_auto', '自动战斗'),
    ('reward', '奖励领取'),
    ('buff', 'Buff增益(恩寵)'),
    ('debuff', 'Debuff减益'),
    ('equipment', '装备选择'),
    ('shop_buy', '商店购买'),
    ('event_choice', '事件选项'),
    ('boss_warning', 'Boss警告'),
    ('victory', '胜利结算'),
    ('defeat', '失败结算'),
    ('restart', '重新开始'),
    ('next_stage', '下一关/继续'),
    ('common', '通用按钮'),
]

ROGUELIKE_PHASES = [
    ('idle', '待机/主菜单'),
    ('entering', '进入肉鸽中'),
    ('char_select', '角色选择阶段'),
    ('stage_select', '关卡选择阶段'),
    ('battle_loading', '战斗加载中'),
    ('battle_active', '战斗进行中'),
    ('battle_end', '战斗结算中'),
    ('reward_collect', '领取奖励'),
    ('buff_select', 'Buff选择阶段'),
    ('debuff_select', 'Debuff选择阶段'),
    ('equip_select', '装备选择阶段'),
    ('shop_phase', '商店阶段'),
    ('event_phase', '事件阶段'),
    ('boss_prep', 'Boss准备阶段'),
    ('victory_screen', '胜利画面'),
    ('defeat_screen', '失败画面'),
    ('final_clear', '最终通关'),
    ('restarting', '重新开始中'),
]

DEFAULT_PHASE_PRIORITY = {
    'idle': ['menu', 'start_apoc', 'common'],
    'entering': ['confirm', 'close', 'common'],
    'char_select': ['character', 'confirm', 'common'],
    'stage_select': ['stage_boss', 'stage_elite', 'stage_normal', 'stage_event', 'stage_shop', 'confirm', 'common'],
    'battle_loading': ['battle_start', 'confirm', 'common'],
    'battle_active': ['battle_speed', 'battle_auto', 'common'],
    'battle_end': ['reward', 'next_stage', 'confirm', 'common'],
    'reward_collect': ['reward', 'confirm', 'close', 'common'],
    'buff_select': ['buff', 'confirm', 'common'],
    'debuff_select': ['debuff', 'confirm', 'common'],
    'equip_select': ['equipment', 'confirm', 'common'],
    'shop_phase': ['shop_buy', 'close', 'next_stage', 'common'],
    'event_phase': ['event_choice', 'confirm', 'common'],
    'boss_prep': ['confirm', 'battle_start', 'common'],
    'victory_screen': ['reward', 'next_stage', 'confirm', 'restart', 'common'],
    'defeat_screen': ['restart', 'confirm', 'close', 'common'],
    'final_clear': ['restart', 'confirm', 'reward', 'close', 'common'],
    'restarting': ['confirm', 'start_apoc', 'common'],
}

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
            'auto_restart': True,
            'max_runs': 99,
            'prefer_elite': True,
            'prefer_boss': True,
            'stage_priority': {
                'stage_boss': 10,
                'stage_elite': 8,
                'stage_event': 6,
                'stage_shop': 5,
                'stage_normal': 3,
            },
            'buff_priority': 2,
            'debuff_priority': 3,
            'equipment_priority': 4,
            'character_priority': 1,
        }
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'roguelike_settings' not in config:
                    config['roguelike_settings'] = default_config['roguelike_settings']
                else:
                    rog = config['roguelike_settings']
                    def_rog = default_config['roguelike_settings']
                    for k, v in def_rog.items():
                        if k not in rog:
                            rog[k] = v
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
    def __init__(self, config, log_callback, status_callback=None):
        self.config = config
        self.log = log_callback
        self.status_callback = status_callback
        self.running = False
        self.priorities = load_priorities()
        self.current_phase = 'idle'
        self.phase_history = []
        self.battle_count = 0
        self.run_count = 0
        self.stage_level = 0
        self.missing_counter = 0
        self.max_missing = 10
    
    def set_phase(self, phase):
        if phase != self.current_phase:
            self.phase_history.append((self.current_phase, time.time()))
            if len(self.phase_history) > 50:
                self.phase_history.pop(0)
            self.current_phase = phase
            self.log(f"阶段切换: {phase}")
            if self.status_callback:
                self.status_callback(phase)
    
    def get_template_priority(self, template_path):
        filename = os.path.basename(template_path)
        category = os.path.basename(os.path.dirname(template_path))
        key = f"{category}/{filename}"
        return self.priorities.get(key, 1)
    
    def find_image(self, template_path, confidence=None, region=None):
        if confidence is None:
            confidence = self.config.get('confidence', 0.8)
        
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            template = cv2.imread(template_path)
            if template is None:
                return None
            
            th, tw = template.shape[:2]
            sh, sw = screenshot_cv.shape[:2]
            if th > sh or tw > sw:
                return None
            
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                if region:
                    center_x += region[0]
                    center_y += region[1]
                return (center_x, center_y, max_val)
            
            return None
        except Exception as e:
            return None
    
    def find_all_in_folder(self, folder_name, confidence=None):
        folder_path = os.path.join(TEMPLATE_DIR, folder_name)
        if not os.path.exists(folder_path):
            return []
        
        matches = []
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                template_path = os.path.join(folder_path, filename)
                result = self.find_image(template_path, confidence)
                if result:
                    x, y, conf = result
                    priority = self.get_template_priority(template_path)
                    score = conf * (1 + priority * 0.1)
                    matches.append({
                        'score': score,
                        'x': x,
                        'y': y,
                        'confidence': conf,
                        'filename': filename,
                        'priority': priority,
                        'category': folder_name
                    })
        
        if matches:
            matches.sort(key=lambda m: m['score'], reverse=True)
        
        return matches
    
    def find_best_in_folder(self, folder_name, confidence=None):
        matches = self.find_all_in_folder(folder_name, confidence)
        if matches:
            return matches[0]
        return None
    
    def find_best_across_folders(self, folder_list, confidence=None):
        all_matches = []
        for folder in folder_list:
            matches = self.find_all_in_folder(folder, confidence)
            all_matches.extend(matches)
        
        if all_matches:
            all_matches.sort(key=lambda m: m['score'], reverse=True)
            return all_matches[0]
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
            self.log(f"找到[{folder_name}]: {result['filename']} (置信度:{result['confidence']:.2f} 优先级:{result['priority']})")
            return self.click_at(result['x'], result['y'])
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
    
    def detect_phase(self):
        phase_checks = [
            ('defeat_screen', ['defeat']),
            ('victory_screen', ['victory']),
            ('boss_prep', ['boss_warning']),
            ('reward_collect', ['reward']),
            ('buff_select', ['buff']),
            ('debuff_select', ['debuff']),
            ('equip_select', ['equipment']),
            ('shop_phase', ['shop_buy', 'stage_shop']),
            ('event_phase', ['event_choice', 'stage_event']),
            ('char_select', ['character']),
            ('stage_select', ['stage_normal', 'stage_elite', 'stage_boss', 'stage_event', 'stage_shop']),
            ('battle_active', ['battle_speed', 'battle_auto']),
            ('final_clear', ['restart', 'victory']),
            ('idle', ['menu', 'start_apoc']),
        ]
        
        for phase, folders in phase_checks:
            for folder in folders:
                if self.is_image_present(folder):
                    return phase
        
        return None
    
    def action_for_phase(self, phase):
        rog = self.config.get('roguelike_settings', {})
        phase_order = DEFAULT_PHASE_PRIORITY.get(phase, ['common'])
        
        if phase == 'stage_select':
            stage_prio = rog.get('stage_priority', {})
            stage_folders = ['stage_boss', 'stage_elite', 'stage_event', 'stage_shop', 'stage_normal']
            stage_folders.sort(key=lambda f: stage_prio.get(f, 1), reverse=True)
            phase_order = stage_folders + ['confirm', 'next_stage', 'common']
        
        for folder in phase_order:
            result = self.find_best_in_folder(folder)
            if result:
                self.log(f"[{phase}] 点击: {result['filename']} ({folder})")
                self.click_at(result['x'], result['y'])
                self.missing_counter = 0
                return True
        
        self.missing_counter += 1
        return False
    
    def roguelike_loop(self):
        self.log("=== 肉鸽模式自动脚本启动 ===")
        self.battle_count = 0
        self.run_count = 0
        self.missing_counter = 0
        self.set_phase('idle')
        
        rog = self.config.get('roguelike_settings', {})
        max_runs = rog.get('max_runs', 99)
        auto_restart = rog.get('auto_restart', True)
        
        try:
            while self.running and self.run_count < max_runs:
                detected = self.detect_phase()
                
                if detected and detected != self.current_phase:
                    self.set_phase(detected)
                    self.missing_counter = 0
                
                if detected == 'defeat_screen' or detected == 'final_clear':
                    self.run_count += 1
                    self.log(f"=== 第{self.run_count}轮结束 ===")
                    if not auto_restart and self.run_count >= max_runs:
                        break
                    self.set_phase('restarting')
                
                if detected == 'victory_screen':
                    self.battle_count += 1
                    self.log(f"第{self.battle_count}场战斗胜利")
                
                action_taken = self.action_for_phase(self.current_phase)
                
                if not action_taken:
                    if self.missing_counter >= self.max_missing:
                        self.log(f"连续{self.max_missing}次未找到目标，尝试返回上一阶段...")
                        self.missing_counter = 0
                        self.find_and_click('close')
                        time.sleep(1)
                        self.find_and_click('cancel')
                        time.sleep(1)
                        if self.phase_history:
                            prev_phase, _ = self.phase_history[-1]
                            self.log(f"尝试返回阶段: {prev_phase}")
                    else:
                        time.sleep(2)
                else:
                    time.sleep(1.5)
                
                time.sleep(0.5)
        
        except Exception as e:
            self.log(f"错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        
        self.log("=== 肉鸽模式脚本结束 ===")
        self.set_phase('idle')

class RlyehBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RlyehBot - 肉鸽模式自动脚本 (Vision)")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        ensure_dirs()
        self.config = load_config()
        self.bot = ImageBot(self.config, self.log, self.update_phase_display)
        self.running = False
        self.thread = None
        self.battles = 0
        self.priorities = load_priorities()
        self.current_template_category = 'menu'
        self.current_phase = 'idle'
        
        self.create_widgets()
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.roguelike_tab = ttk.Frame(self.notebook)
        self.capture_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text=" 主页 ")
        self.notebook.add(self.roguelike_tab, text=" 肉鸽流程 ")
        self.notebook.add(self.capture_tab, text=" 模板管理 ")
        self.notebook.add(self.settings_tab, text=" 设置 ")
        
        self.create_main_tab()
        self.create_roguelike_tab()
        self.create_capture_tab()
        self.create_settings_tab()
    
    def create_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="RlyehBot - 肉鸽模式自动脚本", font=("Microsoft YaHei", 16, "bold"))
        title.pack(pady=(0, 10))
        
        info_frame = ttk.LabelFrame(main_frame, text=" 运行状态 ", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(info_frame, text="状态: 就绪", foreground="blue", font=("Microsoft YaHei", 11))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.phase_label = ttk.Label(info_frame, text="当前阶段: 待机", foreground="purple", font=("Microsoft YaHei", 11))
        self.phase_label.pack(side=tk.LEFT, padx=20)
        
        self.battles_label = ttk.Label(info_frame, text="战斗数: 0")
        self.battles_label.pack(side=tk.RIGHT, padx=5)
        
        func_frame = ttk.LabelFrame(main_frame, text=" 功能开关 ", padding="10")
        func_frame.pack(fill=tk.X, pady=5)
        
        self.auto_battle_var = tk.BooleanVar(value=self.config['auto_battle'])
        ttk.Checkbutton(func_frame, text="自动战斗", variable=self.auto_battle_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.auto_event_var = tk.BooleanVar(value=self.config['auto_event'])
        ttk.Checkbutton(func_frame, text="自动事件", variable=self.auto_event_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        self.auto_rewards_var = tk.BooleanVar(value=self.config['auto_rewards'])
        ttk.Checkbutton(func_frame, text="自动领奖", variable=self.auto_rewards_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        
        self.roguelike_enabled_var = tk.BooleanVar(value=self.config.get('roguelike_settings', {}).get('enabled', True))
        ttk.Checkbutton(func_frame, text="肉鸽自动选择", variable=self.roguelike_enabled_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.auto_restart_var = tk.BooleanVar(value=self.config.get('roguelike_settings', {}).get('auto_restart', True))
        ttk.Checkbutton(func_frame, text="自动重开", variable=self.auto_restart_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(ctrl_frame, text="启动肉鸽脚本", command=self.start_roguelike)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="停止脚本", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.screenshot_btn = ttk.Button(ctrl_frame, text="全屏截图", command=self.take_full_screenshot)
        self.screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(ctrl_frame, text="打开模板文件夹", command=self.open_template_dir).pack(side=tk.LEFT, padx=5)
        
        guide_frame = ttk.LabelFrame(main_frame, text=" 使用说明 ", padding="10")
        guide_frame.pack(fill=tk.X, pady=5)
        
        guide_text = (
            "使用步骤：\n"
            "1. 打开游戏并登录，进入肉鸽模式界面\n"
            "2. 切换到【模板管理】标签页，截取各个按钮的模板\n"
            "3. 为每个模板设置优先级（数字越大越优先选择）\n"
            "4. 在【设置】中调整识别置信度和各类选择优先级\n"
            "5. 回到【主页】点击【启动肉鸽脚本】开始运行\n"
            "\n"
            "模板分类说明：\n"
            "  - menu/start_apoc: 主菜单和进入肉鸽的按钮\n"
            "  - character: 角色选择界面的角色卡片\n"
            "  - stage_*: 关卡选择（普通/精英/Boss/事件/商店）\n"
            "  - buff/debuff: 增益/减益效果选择（恩寵）\n"
            "  - equipment: 装备/神器选择\n"
            "  - confirm/close/cancel: 通用确认/关闭/取消按钮\n"
            "  - victory/defeat/restart: 胜利/失败/重开按钮\n"
        )
        ttk.Label(guide_frame, text=guide_text, justify=tk.LEFT, font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        
        log_frame = ttk.LabelFrame(main_frame, text=" 运行日志 ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_roguelike_tab(self):
        rog_frame = ttk.Frame(self.roguelike_tab, padding="10")
        rog_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(rog_frame, text="肉鸽模式流程设置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        
        flow_frame = ttk.LabelFrame(rog_frame, text=" 完整流程说明 ", padding="10")
        flow_frame.pack(fill=tk.X, pady=5)
        
        flow_text = (
            "肉鸽模式完整流程：\n"
            "  1. 主菜单 → 点击进入肉鸽模式\n"
            "  2. 开始确认 → 确认开始挑战\n"
            "  3. 角色选择 → 选择出战角色（如需）\n"
            "  4. 关卡选择 → 选择路线（Boss/精英/普通/事件/商店）\n"
            "  5. 战斗中 → 自动战斗，可加速\n"
            "  6. 战斗结算 → 领取奖励\n"
            "  7. Buff/Debuff选择 → 选择恩寵效果\n"
            "  8. 装备选择 → 选择获得的装备\n"
            "  9. 重复步骤4-8直到Boss关\n"
            "  10. Boss战 → 击败最终Boss\n"
            "  11. 通关结算 → 领取通关奖励\n"
            "  12. 自动重开 → 重新开始新一轮\n"
        )
        ttk.Label(flow_frame, text=flow_text, justify=tk.LEFT, font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        
        stage_prio_frame = ttk.LabelFrame(rog_frame, text=" 关卡选择优先级 ", padding="10")
        stage_prio_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stage_prio_frame, text="数字越大越优先选择 (1-10)").grid(row=0, column=0, columnspan=5, sticky=tk.W, padx=5, pady=3)
        
        stage_prio = self.config.get('roguelike_settings', {}).get('stage_priority', {})
        
        ttk.Label(stage_prio_frame, text="Boss关:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=3)
        self.stage_boss_prio_var = tk.IntVar(value=stage_prio.get('stage_boss', 10))
        ttk.Spinbox(stage_prio_frame, from_=1, to=10, textvariable=self.stage_boss_prio_var, width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(stage_prio_frame, text="精英关:").grid(row=1, column=2, sticky=tk.E, padx=5, pady=3)
        self.stage_elite_prio_var = tk.IntVar(value=stage_prio.get('stage_elite', 8))
        ttk.Spinbox(stage_prio_frame, from_=1, to=10, textvariable=self.stage_elite_prio_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(stage_prio_frame, text="事件关:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.stage_event_prio_var = tk.IntVar(value=stage_prio.get('stage_event', 6))
        ttk.Spinbox(stage_prio_frame, from_=1, to=10, textvariable=self.stage_event_prio_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(stage_prio_frame, text="商店关:").grid(row=2, column=2, sticky=tk.E, padx=5, pady=3)
        self.stage_shop_prio_var = tk.IntVar(value=stage_prio.get('stage_shop', 5))
        ttk.Spinbox(stage_prio_frame, from_=1, to=10, textvariable=self.stage_shop_prio_var, width=5).grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(stage_prio_frame, text="普通关:").grid(row=1, column=4, sticky=tk.E, padx=5, pady=3)
        self.stage_normal_prio_var = tk.IntVar(value=stage_prio.get('stage_normal', 3))
        ttk.Spinbox(stage_prio_frame, from_=1, to=10, textvariable=self.stage_normal_prio_var, width=5).grid(row=1, column=5, sticky=tk.W, padx=5, pady=3)
        
        phase_frame = ttk.LabelFrame(rog_frame, text=" 当前阶段状态 ", padding="10")
        phase_frame.pack(fill=tk.X, pady=5)
        
        self.phase_detail_label = ttk.Label(phase_frame, text="当前阶段: 待机/主菜单", font=("Microsoft YaHei", 11, "bold"), foreground="purple")
        self.phase_detail_label.pack(anchor=tk.W, padx=5, pady=5)
        
        phase_desc = {
            'idle': '待机/主菜单 - 等待进入肉鸽模式',
            'entering': '进入肉鸽中 - 正在进入肉鸽模式',
            'char_select': '角色选择阶段 - 选择出战角色',
            'stage_select': '关卡选择阶段 - 选择下一个关卡',
            'battle_loading': '战斗加载中 - 正在加载战斗',
            'battle_active': '战斗进行中 - 正在自动战斗',
            'battle_end': '战斗结算中 - 战斗结束领取奖励',
            'reward_collect': '领取奖励 - 点击领取奖励',
            'buff_select': 'Buff选择阶段 - 选择增益效果(恩寵)',
            'debuff_select': 'Debuff选择阶段 - 选择减益效果',
            'equip_select': '装备选择阶段 - 选择获得的装备',
            'shop_phase': '商店阶段 - 在商店购买物品',
            'event_phase': '事件阶段 - 处理随机事件',
            'boss_prep': 'Boss准备阶段 - Boss战即将开始',
            'victory_screen': '胜利画面 - 战斗胜利',
            'defeat_screen': '失败画面 - 战斗失败',
            'final_clear': '最终通关 - 肉鸽模式通关',
            'restarting': '重新开始中 - 准备下一轮',
        }
        
        phase_list_frame = ttk.Frame(phase_frame)
        phase_list_frame.pack(fill=tk.X, pady=5)
        
        self.phase_text = scrolledtext.ScrolledText(phase_list_frame, height=6, font=("Consolas", 8), state=tk.DISABLED)
        self.phase_text.pack(fill=tk.X)
        
        self.phase_text.config(state=tk.NORMAL)
        for phase_key, phase_name in ROGUELIKE_PHASES:
            desc = phase_desc.get(phase_key, '')
            self.phase_text.insert(tk.END, f"  {phase_name}: {desc}\n")
        self.phase_text.config(state=tk.DISABLED)
        
        ttk.Button(rog_frame, text="保存肉鸽设置", command=self.save_roguelike_settings).pack(pady=10)
    
    def create_capture_tab(self):
        cap_frame = ttk.Frame(self.capture_tab, padding="10")
        cap_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(cap_frame, text="模板截图与管理", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        cap_tool_frame = ttk.LabelFrame(cap_frame, text=" 截图工具 ", padding="10")
        cap_tool_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cap_tool_frame, text="目标分类:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.cap_category_var = tk.StringVar(value='menu')
        cap_combo = ttk.Combobox(cap_tool_frame, textvariable=self.cap_category_var, state='readonly', width=25)
        cap_combo['values'] = [f"{cat} - {name}" for cat, name in CATEGORIES]
        cap_combo.current(0)
        cap_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        cap_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        self.capture_btn = ttk.Button(cap_tool_frame, text="截图 (3秒延迟)", command=self.start_capture)
        self.capture_btn.grid(row=0, column=2, padx=10, pady=5)
        
        self.open_template_btn = ttk.Button(cap_tool_frame, text="打开模板文件夹", command=self.open_template_dir)
        self.open_template_btn.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(cap_tool_frame, text="使用方法: 点击按钮后3秒内切换到游戏，用鼠标拖拽框选按钮区域", 
                  foreground="gray").grid(row=1, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
        
        list_frame = ttk.LabelFrame(cap_frame, text=" 模板列表 ", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        list_toolbar = ttk.Frame(list_frame)
        list_toolbar.pack(fill=tk.X, pady=3)
        
        ttk.Label(list_toolbar, text="查看分类:").pack(side=tk.LEFT, padx=3)
        
        self.view_category_var = tk.StringVar(value='menu')
        view_combo = ttk.Combobox(list_toolbar, textvariable=self.view_category_var, state='readonly', width=20)
        view_combo['values'] = [f"{cat} - {name}" for cat, name in CATEGORIES]
        view_combo.current(0)
        view_combo.pack(side=tk.LEFT, padx=3)
        view_combo.bind('<<ComboboxSelected>>', self.refresh_template_list)
        
        ttk.Button(list_toolbar, text="刷新", command=self.refresh_template_list).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="设置优先级", command=self.set_template_priority).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="删除", command=self.delete_template).pack(side=tk.LEFT, padx=3)
        ttk.Button(list_toolbar, text="重命名", command=self.rename_template).pack(side=tk.LEFT, padx=3)
        
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.template_tree = ttk.Treeview(tree_frame, columns=("priority", "size"), show="tree headings")
        self.template_tree.heading("#0", text="模板文件名")
        self.template_tree.heading("priority", text="优先级")
        self.template_tree.heading("size", text="大小")
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
        
        ttk.Label(settings_frame, text="全局设置", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        param_frame = ttk.LabelFrame(settings_frame, text=" 识别参数 ", padding="10")
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="置信度 (0.5-1.0):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.confidence_var = tk.DoubleVar(value=self.config.get('confidence', 0.8))
        ttk.Scale(param_frame, from_=0.5, to=1.0, variable=self.confidence_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.confidence_label = ttk.Label(param_frame, text=f"{self.config.get('confidence', 0.8):.2f}")
        self.confidence_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.confidence_var.trace_add("write", lambda *args: self.confidence_label.config(text=f"{self.confidence_var.get():.2f}"))
        
        ttk.Label(param_frame, text="战斗延迟 (秒):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.battle_delay_var = tk.StringVar(value=str(self.config.get('battle_delay', 3)))
        ttk.Entry(param_frame, textvariable=self.battle_delay_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(param_frame, text="点击延迟 (秒):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.click_delay_var = tk.StringVar(value=str(self.config.get('click_delay', 0.8)))
        ttk.Entry(param_frame, textvariable=self.click_delay_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        rog_frame = ttk.LabelFrame(settings_frame, text=" 肉鸽设置 ", padding="10")
        rog_frame.pack(fill=tk.X, pady=5)
        
        rog = self.config.get('roguelike_settings', {})
        
        ttk.Label(rog_frame, text="最大轮数:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=3)
        self.max_runs_var = tk.IntVar(value=rog.get('max_runs', 99))
        ttk.Spinbox(rog_frame, from_=1, to=999, textvariable=self.max_runs_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Buff选择优先级:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=3)
        self.buff_priority_var = tk.IntVar(value=rog.get('buff_priority', 2))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.buff_priority_var, width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Debuff选择优先级:").grid(row=1, column=2, sticky=tk.E, padx=5, pady=3)
        self.debuff_priority_var = tk.IntVar(value=rog.get('debuff_priority', 3))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.debuff_priority_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="装备选择优先级:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.equip_priority_var = tk.IntVar(value=rog.get('equipment_priority', 4))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.equip_priority_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="角色选择优先级:").grid(row=2, column=2, sticky=tk.E, padx=5, pady=3)
        self.char_priority_var = tk.IntVar(value=rog.get('character_priority', 1))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.char_priority_var, width=5).grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)
        
        save_frame = ttk.Frame(settings_frame)
        save_frame.pack(fill=tk.X, pady=20)
        
        self.save_btn = ttk.Button(save_frame, text="保存所有设置", command=self.save_settings)
        self.save_btn.pack(side=tk.LEFT, padx=5)
    
    def log(self, message):
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)
    
    def update_phase_display(self, phase):
        phase_names = dict(ROGUELIKE_PHASES)
        phase_name = phase_names.get(phase, phase)
        self.current_phase = phase
        def _update():
            self.phase_label.config(text=f"当前阶段: {phase_name}")
            self.phase_detail_label.config(text=f"当前阶段: {phase_name}")
        self.root.after(0, _update)
    
    def open_template_dir(self):
        try:
            os.startfile(TEMPLATE_DIR)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
    
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
            messagebox.showerror("错误", f"截图失败: {str(e)}")
    
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
            messagebox.showinfo("成功", f"模板已保存:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
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
            messagebox.showwarning("警告", "请先选择一个模板")
            return
        
        key = f"{cat}/{filename}"
        current = self.priorities.get(key, 1)
        
        new_priority = simpledialog.askinteger("设置优先级", 
                                                f"设置模板 [{filename}] 的优先级\n(1-10, 数字越大越优先匹配):",
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
            messagebox.showwarning("警告", "请先选择一个模板")
            return
        
        if not messagebox.askyesno("确认", f"确定删除 {filename}?"):
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
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def rename_template(self):
        cat, filename = self.get_selected_template()
        if not filename:
            messagebox.showwarning("警告", "请先选择一个模板")
            return
        
        new_name = simpledialog.askstring("重命名", "新名称 (不含扩展名):",
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
            messagebox.showerror("错误", f"重命名失败: {str(e)}")
    
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
        messagebox.showinfo("截图", f"已保存到:\n{save_path}")
    
    def save_roguelike_settings(self):
        rog = self.config.get('roguelike_settings', {})
        rog['stage_priority'] = {
            'stage_boss': self.stage_boss_prio_var.get(),
            'stage_elite': self.stage_elite_prio_var.get(),
            'stage_event': self.stage_event_prio_var.get(),
            'stage_shop': self.stage_shop_prio_var.get(),
            'stage_normal': self.stage_normal_prio_var.get(),
        }
        self.config['roguelike_settings'] = rog
        save_config(self.config)
        self.bot.config = self.config
        self.log("肉鸽设置已保存")
        messagebox.showinfo("成功", "肉鸽设置已保存！")
    
    def save_settings(self):
        self.config['confidence'] = self.confidence_var.get()
        self.config['battle_delay'] = float(self.battle_delay_var.get())
        self.config['click_delay'] = float(self.click_delay_var.get())
        self.config['auto_battle'] = self.auto_battle_var.get()
        self.config['auto_event'] = self.auto_event_var.get()
        self.config['auto_rewards'] = self.auto_rewards_var.get()
        
        rog = self.config.get('roguelike_settings', {})
        rog['enabled'] = self.roguelike_enabled_var.get()
        rog['auto_restart'] = self.auto_restart_var.get()
        rog['max_runs'] = self.max_runs_var.get()
        rog['buff_priority'] = self.buff_priority_var.get()
        rog['debuff_priority'] = self.debuff_priority_var.get()
        rog['equipment_priority'] = self.equip_priority_var.get()
        rog['character_priority'] = self.char_priority_var.get()
        rog['stage_priority'] = {
            'stage_boss': self.stage_boss_prio_var.get(),
            'stage_elite': self.stage_elite_prio_var.get(),
            'stage_event': self.stage_event_prio_var.get(),
            'stage_shop': self.stage_shop_prio_var.get(),
            'stage_normal': self.stage_normal_prio_var.get(),
        }
        self.config['roguelike_settings'] = rog
        
        save_config(self.config)
        self.bot.config = self.config
        messagebox.showinfo("成功", "所有设置已保存！")
    
    def start_roguelike(self):
        if not self.roguelike_enabled_var.get():
            if not messagebox.askyesno("确认", "肉鸽自动选择未启用，是否仍要启动？"):
                return
        
        self.running = True
        self.bot.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 运行中", foreground="green")
        
        self.thread = threading.Thread(target=self.bot.roguelike_loop, daemon=True)
        self.thread.start()
    
    def stop_bot(self):
        self.running = False
        self.bot.running = False
        self.log("正在停止脚本...")
        self.status_label.config(text="状态: 停止中", foreground="orange")
    
    def on_bot_stopped(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="状态: 已停止", foreground="red")
        self.log("脚本已停止。")

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
