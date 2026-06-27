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
        'click_delay': 0.8
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
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
        self.root.title("RlyehBot - 邪神戦記ルルイエ少女隊")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.config = load_config()
        self.driver = None
        self.running = False
        self.thread = None
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
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
        
        ttk.Label(func_frame, text="最大战斗次数:").grid(row=1, column=1, sticky=tk.E, padx=5, pady=3)
        self.max_battles_var = tk.StringVar(value=str(self.config['max_battles']))
        ttk.Entry(func_frame, textvariable=self.max_battles_var, width=8).grid(row=1, column=2, sticky=tk.W, padx=5, pady=3)
        
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
            
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
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
            messagebox.showerror("错误", "无法连接到Chrome！\n\n请用调试模式启动Chrome：\n1. 关闭所有Chrome窗口\n2. 按Win+R\n3. 输入: chrome.exe --remote-debugging-port=9222")
        except Exception as e:
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
        
        battle_buttons = [
            "戦闘開始",
            "スタート",
            "開始",
            "挑戦",
            "次へ"
        ]
        
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
        save_config(self.config)
        
        try:
            while self.running and battles < max_battles:
                self.collect_rewards()
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