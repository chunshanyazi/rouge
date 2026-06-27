# -*- coding: utf-8 -*-
import time
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pyautogui
import cv2
import numpy as np

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

def load_config():
    default_config = {
        'confidence': 0.8,
        'auto_battle': True,
        'auto_event': True,
        'auto_rewards': True,
        'max_battles': 999,
        'battle_delay': 3,
        'click_delay': 0.8,
        'search_region': None,
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

def ensure_template_dir():
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
    categories = ['battle', 'event', 'reward', 'buff', 'debuff', 'equipment', 'stage', 'character', 'common']
    for cat in categories:
        cat_dir = os.path.join(TEMPLATE_DIR, cat)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)

class ImageBot:
    def __init__(self, config, log_callback):
        self.config = config
        self.log = log_callback
        self.running = False
    
    def find_image(self, template_path, confidence=None, region=None):
        if confidence is None:
            confidence = self.config.get('confidence', 0.8)
        
        if region is None:
            region = self.config.get('search_region', None)
        
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
            self.log(f"图像识别错误: {str(e)}")
            return None
    
    def find_any_in_folder(self, folder_name, confidence=None):
        folder_path = os.path.join(TEMPLATE_DIR, folder_name)
        if not os.path.exists(folder_path):
            return None
        
        best_match = None
        best_conf = 0
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                template_path = os.path.join(folder_path, filename)
                result = self.find_image(template_path, confidence)
                if result and result[2] > best_conf:
                    best_match = result
                    best_conf = result[2]
        
        return best_match
    
    def click_at(self, x, y, clicks=1, interval=0.2):
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval)
            time.sleep(self.config.get('click_delay', 0.8))
            return True
        except Exception as e:
            self.log(f"点击错误: {str(e)}")
            return False
    
    def find_and_click(self, folder_name, confidence=None):
        result = self.find_any_in_folder(folder_name, confidence)
        if result:
            x, y, conf = result
            self.log(f"找到目标 ({folder_name}): 置信度 {conf:.2f}, 位置 ({x}, {y})")
            return self.click_at(x, y)
        return False
    
    def is_image_present(self, folder_name, confidence=None):
        result = self.find_any_in_folder(folder_name, confidence)
        return result is not None
    
    def take_screenshot(self, save_path=None):
        try:
            screenshot = pyautogui.screenshot()
            if save_path:
                screenshot.save(save_path)
                self.log(f"截图已保存: {save_path}")
            return screenshot
        except Exception as e:
            self.log(f"截图错误: {str(e)}")
            return None

class RlyehBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("邪神戦記ルルイエ少女隊 - 挂机工具 (图像识别版)")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        ensure_template_dir()
        self.config = load_config()
        self.bot = ImageBot(self.config, self.log)
        self.running = False
        self.thread = None
        self.battles = 0
        
        self.create_widgets()
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.template_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text=" 主功能 ")
        self.notebook.add(self.template_tab, text=" 模板管理 ")
        self.notebook.add(self.settings_tab, text=" 设置 ")
        
        self.create_main_tab()
        self.create_template_tab()
        self.create_settings_tab()
    
    def create_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="邪神戦記ルルイエ少女隊 - 图像识别挂机", font=("Microsoft YaHei", 14, "bold"))
        title.pack(pady=(0, 10))
        
        info_frame = ttk.LabelFrame(main_frame, text=" 状态 ", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(info_frame, text="状态: 就绪", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.battles_label = ttk.Label(info_frame, text="战斗次数: 0")
        self.battles_label.pack(side=tk.RIGHT, padx=5)
        
        func_frame = ttk.LabelFrame(main_frame, text=" 功能选项 ", padding="10")
        func_frame.pack(fill=tk.X, pady=5)
        
        self.auto_battle_var = tk.BooleanVar(value=self.config['auto_battle'])
        ttk.Checkbutton(func_frame, text="自动战斗", variable=self.auto_battle_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.auto_event_var = tk.BooleanVar(value=self.config['auto_event'])
        ttk.Checkbutton(func_frame, text="自动选事件", variable=self.auto_event_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        self.auto_rewards_var = tk.BooleanVar(value=self.config['auto_rewards'])
        ttk.Checkbutton(func_frame, text="自动领奖励", variable=self.auto_rewards_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        
        self.roguelike_enabled_var = tk.BooleanVar(value=self.config.get('roguelike_settings', {}).get('enabled', True))
        ttk.Checkbutton(func_frame, text="肉鸽自动选择", variable=self.roguelike_enabled_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(func_frame, text="最大战斗次数:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.max_battles_var = tk.StringVar(value=str(self.config['max_battles']))
        ttk.Entry(func_frame, textvariable=self.max_battles_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(ctrl_frame, text="开始挂机", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="停止挂机", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.screenshot_btn = ttk.Button(ctrl_frame, text="截图", command=self.take_screenshot)
        self.screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text=" 日志 ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_template_tab(self):
        template_frame = ttk.Frame(self.template_tab, padding="10")
        template_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(template_frame, text="模板图片管理", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        info_text = """使用说明：
1. 把游戏窗口放在屏幕上（不要最小化）
2. 点击"截图"按钮保存当前屏幕
3. 用截图软件裁剪出你要识别的按钮/图标
4. 保存到对应的 templates 文件夹里
5. 支持 PNG、JPG 格式

文件夹说明：
battle/     - 战斗开始按钮（出撃、戦闘開始等）
event/      - 事件选项（宝箱、商店、休息等）
reward/     - 奖励领取按钮
buff/       - Buff增益选项
debuff/     - Debuff减益选项
equipment/  - 装备选择
stage/      - 关卡选择
character/  - 角色选择
common/     - 通用按钮（确定、关闭、返回等）
"""
        info_label = ttk.Label(template_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=5, anchor=tk.W)
        
        btn_frame = ttk.Frame(template_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.open_template_btn = ttk.Button(btn_frame, text="打开模板文件夹", command=self.open_template_dir)
        self.open_template_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_template_btn = ttk.Button(btn_frame, text="刷新模板列表", command=self.refresh_template_list)
        self.refresh_template_btn.pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(template_frame, text=" 模板列表 ", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.template_tree = ttk.Treeview(list_frame, columns=("count",), show="tree headings")
        self.template_tree.heading("#0", text="分类")
        self.template_tree.heading("count", text="图片数量")
        self.template_tree.column("count", width=100, anchor=tk.CENTER)
        self.template_tree.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_template_list()
    
    def create_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text="参数设置", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        param_frame = ttk.LabelFrame(settings_frame, text=" 识别参数 ", padding="10")
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="识别置信度 (0.5-1.0):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.confidence_var = tk.DoubleVar(value=self.config.get('confidence', 0.8))
        ttk.Scale(param_frame, from_=0.5, to=1.0, variable=self.confidence_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.confidence_label = ttk.Label(param_frame, text=f"{self.config.get('confidence', 0.8):.2f}")
        self.confidence_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.confidence_var.trace_add("write", lambda *args: self.confidence_label.config(text=f"{self.confidence_var.get():.2f}"))
        
        ttk.Label(param_frame, text="战斗间隔 (秒):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.battle_delay_var = tk.StringVar(value=str(self.config.get('battle_delay', 3)))
        ttk.Entry(param_frame, textvariable=self.battle_delay_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(param_frame, text="点击延迟 (秒):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.click_delay_var = tk.StringVar(value=str(self.config.get('click_delay', 0.8)))
        ttk.Entry(param_frame, textvariable=self.click_delay_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        rog_frame = ttk.LabelFrame(settings_frame, text=" 肉鸽优先级 ", padding="10")
        rog_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rog_frame, text="数字越大优先级越高（1-10）").grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=3)
        
        rog = self.config.get('roguelike_settings', {})
        
        ttk.Label(rog_frame, text="关卡选择:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=3)
        self.stage_priority_var = tk.IntVar(value=rog.get('stage_priority', 1))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.stage_priority_var, width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="角色选择:").grid(row=1, column=2, sticky=tk.E, padx=5, pady=3)
        self.char_priority_var = tk.IntVar(value=rog.get('character_priority', 1))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.char_priority_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Buff选择:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=3)
        self.buff_priority_var = tk.IntVar(value=rog.get('buff_priority', 2))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.buff_priority_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="Debuff选择:").grid(row=2, column=2, sticky=tk.E, padx=5, pady=3)
        self.debuff_priority_var = tk.IntVar(value=rog.get('debuff_priority', 3))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.debuff_priority_var, width=5).grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)
        
        ttk.Label(rog_frame, text="装备选择:").grid(row=3, column=0, sticky=tk.E, padx=5, pady=3)
        self.equip_priority_var = tk.IntVar(value=rog.get('equipment_priority', 4))
        ttk.Spinbox(rog_frame, from_=1, to=10, textvariable=self.equip_priority_var, width=5).grid(row=3, column=1, sticky=tk.W, padx=5, pady=3)
        
        save_frame = ttk.Frame(settings_frame)
        save_frame.pack(fill=tk.X, pady=20)
        
        self.save_btn = ttk.Button(save_frame, text="保存设置", command=self.save_settings)
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
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
    
    def refresh_template_list(self):
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)
        
        categories = ['battle', 'event', 'reward', 'buff', 'debuff', 'equipment', 'stage', 'character', 'common']
        cat_names = {
            'battle': '战斗按钮',
            'event': '事件选项',
            'reward': '奖励领取',
            'buff': 'Buff增益',
            'debuff': 'Debuff减益',
            'equipment': '装备选择',
            'stage': '关卡选择',
            'character': '角色选择',
            'common': '通用按钮'
        }
        
        for cat in categories:
            cat_path = os.path.join(TEMPLATE_DIR, cat)
            count = 0
            if os.path.exists(cat_path):
                count = len([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
            self.template_tree.insert("", tk.END, text=f"{cat_names[cat]} ({cat})", values=(count,), open=False)
    
    def take_screenshot(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        self.bot.take_screenshot(save_path)
        messagebox.showinfo("截图完成", f"截图已保存到:\n{save_path}\n\n请用画图工具裁剪出按钮，保存到 templates 对应文件夹。")
    
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
        messagebox.showinfo("提示", "设置已保存！")
    
    def collect_rewards(self):
        if not self.auto_rewards_var.get():
            return False
        if self.bot.find_and_click('reward'):
            self.log("领取奖励...")
            time.sleep(1)
            self.bot.find_and_click('common')
            return True
        return False
    
    def select_event(self):
        if not self.auto_event_var.get():
            return False
        if self.bot.find_and_click('event'):
            self.log("选择事件...")
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
                self.log(f"选择肉鸽选项: {folder}")
                time.sleep(1)
                self.bot.find_and_click('common')
                time.sleep(0.5)
                return True
        
        return False
    
    def start_battle(self):
        if not self.auto_battle_var.get():
            return False
        if self.bot.find_and_click('battle'):
            self.log("开始战斗！")
            time.sleep(2)
            return True
        return False
    
    def wait_battle_finish(self):
        self.log("等待战斗结束...")
        timeout = 180
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.running:
                return "stopped"
            
            if self.bot.is_image_present('reward'):
                self.log("战斗结束！")
                self.bot.find_and_click('common')
                time.sleep(1)
                return "success"
            
            if self.bot.is_image_present('battle', confidence=0.85):
                self.log("战斗可能结束，检查中...")
                time.sleep(2)
                if self.bot.is_image_present('battle', confidence=0.85):
                    return "success"
            
            time.sleep(3)
        
        return "timeout"
    
    def bot_loop(self):
        self.log("挂机开始！")
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
                        self.root.after(0, lambda: self.battles_label.config(text=f"战斗次数: {self.battles}"))
                        self.log(f"战斗 {self.battles} 完成！")
                    elif result == "stopped":
                        break
                    elif result == "timeout":
                        self.log("战斗超时，继续...")
                else:
                    self.log("未找到战斗按钮，再次检查...")
                    time.sleep(5)
                
                time.sleep(self.config.get('battle_delay', 3))
        
        except Exception as e:
            self.log(f"错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.running = False
            self.root.after(0, self.on_bot_stopped)
    
    def start_bot(self):
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态: 运行中", foreground="green")
        
        self.thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.thread.start()
    
    def stop_bot(self):
        self.running = False
        self.log("正在停止挂机...")
        self.status_label.config(text="状态: 停止中", foreground="orange")
    
    def on_bot_stopped(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="状态: 已停止", foreground="red")
        self.log("挂机已停止。")

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
