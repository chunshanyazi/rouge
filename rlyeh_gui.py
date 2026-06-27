# -*- coding: utf-8 -*-
import time
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidArgumentException

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    default_config = {
        'chrome_debug_port': 9222,
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
            'character_priority': 1,
            'debuff_options': ['毒', '麻痺', '沉默', '混乱', '衰弱', '呪い', '暗闇', '拘束', '恐怖', 'スタン'],
            'buff_options': ['攻撃力UP', '防御力UP', '回復', '速度UP', 'クリティカル', '連続攻撃', '能力向上', 'HP回復', 'SP回復', '攻撃強化', '防御強化'],
            'equipment_options': ['武器', '防具', 'アクセ', 'アイテム', '装備', '刻印', 'スキル'],
            'stage_options': ['1区', '2区', '3区', '4区', '5区', 'エリア', 'ステージ', 'フロア', '階'],
            'character_options': ['Tank', 'Healer', 'DPS', 'Support', '前衛', '後衛', '攻撃', '防御', '回復', '補助']
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

class RlyehBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("邪神戦記ルルイエ少女隊 - 挂机工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        self.config = load_config()
        self.driver = None
        self.running = False
        self.thread = None
        
        self.create_widgets()
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_tab = ttk.Frame(self.notebook)
        self.roguelike_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text=" 主功能 ")
        self.notebook.add(self.roguelike_tab, text=" 肉鸽设置 ")
        
        self.create_main_tab()
        self.create_roguelike_tab()
    
    def create_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="邪神戦記ルルイエ少女隊", font=("Microsoft YaHei", 16, "bold"))
        title.pack(pady=(0, 10))
        
        conn_frame = ttk.LabelFrame(main_frame, text=" 连接设置 ", padding="10")
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="Chrome调试端口:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar(value=str(self.config['chrome_debug_port']))
        ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="连接浏览器", command=self.connect_browser)
        self.connect_btn.grid(row=0, column=2, padx=10, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="状态: 未连接", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
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
        
        self.start_btn = ttk.Button(ctrl_frame, text="开始挂机", command=self.start_bot, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(ctrl_frame, text="停止挂机", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.battles_label = ttk.Label(ctrl_frame, text="战斗次数: 0")
        self.battles_label.pack(side=tk.RIGHT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text=" 日志 ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_roguelike_tab(self):
        rog_frame = ttk.Frame(self.roguelike_tab, padding="10")
        rog_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(rog_frame, text="肉鸽选项优先级设置（数字越大优先级越高）", font=("Microsoft YaHei", 12, "bold")).pack(pady=(0, 10))
        
        priority_frame = ttk.LabelFrame(rog_frame, text=" 优先级设置 ", padding="10")
        priority_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(priority_frame, text="关卡选择优先级:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.stage_priority_var = tk.IntVar(value=self.config.get('roguelike_settings', {}).get('stage_priority', 1))
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.stage_priority_var, width=5).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(priority_frame, text="角色选择优先级:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.char_priority_var = tk.IntVar(value=self.config.get('roguelike_settings', {}).get('character_priority', 1))
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.char_priority_var, width=5).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(priority_frame, text="Buff选择优先级:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.buff_priority_var = tk.IntVar(value=self.config.get('roguelike_settings', {}).get('buff_priority', 2))
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.buff_priority_var, width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(priority_frame, text="Debuff选择优先级:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.debuff_priority_var = tk.IntVar(value=self.config.get('roguelike_settings', {}).get('debuff_priority', 3))
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.debuff_priority_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(priority_frame, text="装备选择优先级:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.equip_priority_var = tk.IntVar(value=self.config.get('roguelike_settings', {}).get('equipment_priority', 4))
        ttk.Spinbox(priority_frame, from_=1, to=10, textvariable=self.equip_priority_var, width=5).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        options_frame = ttk.LabelFrame(rog_frame, text=" 选项文本设置（请根据游戏内实际文本填写） ", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(options_frame, text="Debuff选项（逗号分隔）:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        debuff_default = ','.join(self.config.get('roguelike_settings', {}).get('debuff_options', ['毒', '麻痺', '沉默']))
        self.debuff_entry = ttk.Entry(options_frame, width=50)
        self.debuff_entry.insert(0, debuff_default)
        self.debuff_entry.grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(options_frame, text="Buff选项（逗号分隔）:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        buff_default = ','.join(self.config.get('roguelike_settings', {}).get('buff_options', ['攻撃力UP', '防御力UP', '回復']))
        self.buff_entry = ttk.Entry(options_frame, width=50)
        self.buff_entry.insert(0, buff_default)
        self.buff_entry.grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(options_frame, text="装备选项（逗号分隔）:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        equip_default = ','.join(self.config.get('roguelike_settings', {}).get('equipment_options', ['武器', '防具', 'アクセ']))
        self.equip_entry = ttk.Entry(options_frame, width=50)
        self.equip_entry.insert(0, equip_default)
        self.equip_entry.grid(row=2, column=1, padx=5, pady=3)
        
        ttk.Label(options_frame, text="关卡选项（逗号分隔）:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        stage_default = ','.join(self.config.get('roguelike_settings', {}).get('stage_options', ['1区', '2区', '3区']))
        self.stage_entry = ttk.Entry(options_frame, width=50)
        self.stage_entry.insert(0, stage_default)
        self.stage_entry.grid(row=3, column=1, padx=5, pady=3)
        
        ttk.Label(options_frame, text="角色选项（逗号分隔）:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=3)
        char_default = ','.join(self.config.get('roguelike_settings', {}).get('character_options', ['Tank', 'Healer', 'DPS']))
        self.char_entry = ttk.Entry(options_frame, width=50)
        self.char_entry.insert(0, char_default)
        self.char_entry.grid(row=4, column=1, padx=5, pady=3)
        
        ttk.Label(options_frame, text="战斗选项（逗号分隔）:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=3)
        battle_default = ','.join(self.config.get('roguelike_settings', {}).get('battle_options', ['戦闘', '战斗', '進む']))
        self.battle_entry = ttk.Entry(options_frame, width=50)
        self.battle_entry.insert(0, battle_default)
        self.battle_entry.grid(row=5, column=1, padx=5, pady=3)
        
        save_frame = ttk.Frame(rog_frame)
        save_frame.pack(fill=tk.X, pady=10)
        
        self.save_btn = ttk.Button(save_frame, text="保存设置", command=self.save_roguelike_settings)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(save_frame, text="重置默认", command=self.reset_roguelike_settings)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
    
    def save_roguelike_settings(self):
        rog = self.config.get('roguelike_settings', {})
        
        rog['stage_priority'] = self.stage_priority_var.get()
        rog['character_priority'] = self.char_priority_var.get()
        rog['buff_priority'] = self.buff_priority_var.get()
        rog['debuff_priority'] = self.debuff_priority_var.get()
        rog['equipment_priority'] = self.equip_priority_var.get()
        
        rog['debuff_options'] = [x.strip() for x in self.debuff_entry.get().split(',') if x.strip()]
        rog['buff_options'] = [x.strip() for x in self.buff_entry.get().split(',') if x.strip()]
        rog['equipment_options'] = [x.strip() for x in self.equip_entry.get().split(',') if x.strip()]
        rog['stage_options'] = [x.strip() for x in self.stage_entry.get().split(',') if x.strip()]
        rog['character_options'] = [x.strip() for x in self.char_entry.get().split(',') if x.strip()]
        rog['battle_options'] = [x.strip() for x in self.battle_entry.get().split(',') if x.strip()]
        
        self.config['roguelike_settings'] = rog
        save_config(self.config)
        messagebox.showinfo("提示", "设置已保存！")
    
    def reset_roguelike_settings(self):
        self.stage_priority_var.set(1)
        self.char_priority_var.set(1)
        self.buff_priority_var.set(2)
        self.debuff_priority_var.set(3)
        self.equip_priority_var.set(4)
        self.debuff_entry.delete(0, tk.END)
        self.debuff_entry.insert(0, "毒,麻痺,沉默,混乱,衰弱,呪い,暗闇,拘束,恐怖,スタン")
        self.buff_entry.delete(0, tk.END)
        self.buff_entry.insert(0, "攻撃力UP,防御力UP,回復,速度UP,クリティカル,連続攻撃,能力向上,HP回復,SP回復,攻撃強化,防御強化")
        self.equip_entry.delete(0, tk.END)
        self.equip_entry.insert(0, "武器,防具,アクセ,アイテム,装備,刻印,スキル")
        self.stage_entry.delete(0, tk.END)
        self.stage_entry.insert(0, "1区,2区,3区,4区,5区,エリア,ステージ,フロア,階")
        self.char_entry.delete(0, tk.END)
        self.char_entry.insert(0, "Tank,Healer,DPS,Support,前衛,後衛,攻撃,防御,回復,補助")
        self.battle_entry.delete(0, tk.END)
        self.battle_entry.insert(0, "出撃,戦闘開始,スタート,開始,挑戦,次へ,GO,進む,探索")
        messagebox.showinfo("提示", "已重置为默认设置")
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def connect_browser(self):
        try:
            port = int(self.port_var.get())
            self.config['chrome_debug_port'] = port
            save_config(self.config)
            
            self.status_label.config(text="状态: 正在连接...", foreground="orange")
            self.root.update()
            
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:
                messagebox.showerror("连接失败", f"无法连接到端口 {port}\n\n请先运行 start_chrome_debug.bat\n\n或者手动启动Chrome：\n1. 关闭所有Chrome窗口\n2. 按Win+R\n3. 输入: chrome.exe --remote-debugging-port={port}")
                self.status_label.config(text="状态: 未连接", foreground="red")
                return
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.status_label.config(text="状态: 已连接", foreground="green")
            self.start_btn.config(state=tk.NORMAL)
            self.connect_btn.config(state=tk.DISABLED)
            self.log("浏览器连接成功！")
            
            try:
                self.log(f"当前页面: {self.driver.title}")
            except:
                pass
                
        except InvalidArgumentException:
            messagebox.showerror("错误", f"无法连接到Chrome！\n\n请先运行 start_chrome_debug.bat\n\n或者手动启动Chrome：\n1. 关闭所有Chrome窗口\n2. 按Win+R\n3. 输入: chrome.exe --remote-debugging-port={self.port_var.get()}")
        except Exception as e:
            self.status_label.config(text="状态: 未连接", foreground="red")
            messagebox.showerror("错误", f"连接失败: {str(e)}")
    
    def safe_click(self, element, delay=None):
        if delay is None:
            delay = self.config['click_delay']
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).pause(delay * 0.3).click().perform()
            time.sleep(delay)
            return True
        except:
            return False
    
    def click_by_text(self, text, timeout=3):
        try:
            xpath = f"//*[contains(text(), '{text}')]"
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            return self.safe_click(element)
        except:
            return False
    
    def is_element_visible(self, xpath):
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.is_displayed()
        except:
            return False
    
    def get_all_visible_texts(self):
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(),'')]")
            texts = []
            for el in elements:
                if el.is_displayed() and el.text.strip():
                    texts.append(el.text.strip())
            return texts
        except:
            return []
    
    def select_by_priority(self, options_list):
        rog = self.config.get('roguelike_settings', {})
        
        priority_map = {
            'stage': rog.get('stage_priority', 1),
            'character': rog.get('character_priority', 1),
            'buff': rog.get('buff_priority', 2),
            'debuff': rog.get('debuff_priority', 3),
            'equipment': rog.get('equipment_priority', 4)
        }
        
        if options_list[0] in rog.get('stage_options', []):
            category = 'stage'
        elif options_list[0] in rog.get('character_options', []):
            category = 'character'
        elif options_list[0] in rog.get('buff_options', []):
            category = 'buff'
        elif options_list[0] in rog.get('debuff_options', []):
            category = 'debuff'
        elif options_list[0] in rog.get('equipment_options', []):
            category = 'equipment'
        else:
            return random.choice(options_list) if options_list else None
        
        priority = priority_map.get(category, 1)
        
        high_priority = [opt for opt in options_list if any(p in opt for p in ['攻撃力UP', '防御力UP', '回復', '武器', '防具'])]
        if high_priority:
            return high_priority[0]
        
        return options_list[0] if options_list else None
    
    def collect_rewards(self):
        if not self.auto_rewards_var.get():
            return
        
        reward_buttons = ["受け取る", "一括受取", "受取"]
        for btn in reward_buttons:
            if self.click_by_text(btn, timeout=1):
                self.log(f"点击了: {btn}")
                time.sleep(1)
                self.click_by_text("閉じる", timeout=2)
                time.sleep(0.5)
    
    def select_roguelike_option(self):
        rog = self.config.get('roguelike_settings', {})
        if not rog.get('enabled', True):
            return False
        
        all_texts = self.get_all_visible_texts()
        if not all_texts:
            return False
        
        rog_options = (
            rog.get('stage_options', []) +
            rog.get('character_options', []) +
            rog.get('buff_options', []) +
            rog.get('debuff_options', []) +
            rog.get('equipment_options', []) +
            rog.get('battle_options', [])
        )
        
        for text in all_texts:
            if text in rog_options:
                if self.click_by_text(text, timeout=1):
                    self.log(f"选择: {text}")
                    time.sleep(1)
                    
                    self.click_by_text("決定", timeout=2)
                    time.sleep(0.5)
                    self.click_by_text("はい", timeout=2)
                    time.sleep(0.5)
                    self.click_by_text("OK", timeout=2)
                    time.sleep(0.5)
                    return True
        
        return False
    
    def select_event(self):
        if not self.auto_event_var.get():
            return
        
        events = [
            ("戦闘", "战斗"),
            ("宝箱", "宝箱"),
            ("回復", "恢复"),
            ("商店", "商店"),
            ("休息", "休息"),
            ("イベント", "事件")
        ]
        
        for jp_text, cn_name in events:
            xpath = f"//*[contains(text(), '{jp_text}')]"
            if self.is_element_visible(xpath):
                if self.click_by_text(jp_text, timeout=1):
                    self.log(f"选择事件: {cn_name}")
                    time.sleep(2)
                    
                    self.click_by_text("決定", timeout=2)
                    time.sleep(1)
                    self.click_by_text("はい", timeout=2)
                    time.sleep(1)
                    return True
        return False
    
    def start_battle(self):
        if not self.auto_battle_var.get():
            return False
        
        rog = self.config.get('roguelike_settings', {})
        battle_buttons = rog.get('battle_options', ["出撃", "戦闘開始", "スタート", "開始", "挑戦", "次へ", "GO"])
        
        for btn in battle_buttons:
            if self.click_by_text(btn, timeout=1):
                self.log(f"开始战斗: {btn}")
                time.sleep(3)
                return True
        return False
    
    def wait_battle_finish(self):
        self.log("等待战斗结束...")
        
        finish_signals = [
            "戦闘終了",
            "クリア",
            "勝利",
            "敗北",
            "リトライ",
            "次のステージ",
            "結果"
        ]
        
        timeout = 180
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.running:
                return "stopped"
            
            for signal in finish_signals:
                xpath = f"//*[contains(text(), '{signal}')]"
                if self.is_element_visible(xpath):
                    self.log(f"战斗结束: {signal}")
                    
                    if signal in ["敗北", "リトライ"]:
                        self.click_by_text("リトライ", timeout=2)
                        time.sleep(2)
                        return "retry"
                    
                    for close_btn in ["閉じる", "次へ", "次のステージ", "受け取る"]:
                        self.click_by_text(close_btn, timeout=2)
                        time.sleep(1)
                    
                    return "success"
            
            time.sleep(2)
        
        return "timeout"
    
    def bot_loop(self):
        self.log("挂机开始！")
        battles = 0
        max_battles = int(self.max_battles_var.get())
        
        self.config['auto_battle'] = self.auto_battle_var.get()
        self.config['auto_event'] = self.auto_event_var.get()
        self.config['auto_rewards'] = self.auto_rewards_var.get()
        self.config['max_battles'] = max_battles
        rog = self.config.get('roguelike_settings', {})
        rog['enabled'] = self.roguelike_enabled_var.get()
        save_config(self.config)
        
        try:
            while self.running and battles < max_battles:
                self.collect_rewards()
                time.sleep(1)
                
                if rog.get('enabled', True):
                    self.select_roguelike_option()
                    time.sleep(1)
                
                self.select_event()
                time.sleep(1)
                
                if self.start_battle():
                    result = self.wait_battle_finish()
                    
                    if result == "success":
                        battles += 1
                        self.root.after(0, lambda: self.battles_label.config(text=f"战斗次数: {battles}"))
                        self.log(f"战斗 {battles} 完成！")
                    elif result == "retry":
                        self.log("重新尝试战斗...")
                    elif result == "stopped":
                        break
                    elif result == "timeout":
                        self.log("战斗超时，继续...")
                else:
                    self.log("未找到战斗按钮，再次检查...")
                    time.sleep(5)
                
                time.sleep(self.config['battle_delay'])
        
        except Exception as e:
            self.log(f"错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.running = False
            self.root.after(0, self.on_bot_stopped)
    
    def start_bot(self):
        if self.driver is None:
            messagebox.showwarning("警告", "请先连接浏览器！")
            return
        
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.thread.start()
    
    def stop_bot(self):
        self.running = False
        self.log("正在停止挂机...")
    
    def on_bot_stopped(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
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
