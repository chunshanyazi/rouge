import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class RlyehShoujotaiBot:
    def __init__(self, config_path='config.json'):
        self.config = self.load_config(config_path)
        self.driver = None
        self.wait = None
        self.running = False
        
    def load_config(self, path):
        default_config = {
            'game_url': 'https://play.games.dmm.co.jp/game/rlyehshoujotai_x_783592',
            'dmm_id': '',
            'dmm_password': '',
            'proxy_port': 7890,
            'auto_login': True,
            'auto_battle': True,
            'auto_event': True,
            'auto_daily': True,
            'auto_rewards': True,
            'target_stage': 'story',
            'max_battles': 100,
            'battle_delay': 2,
            'click_delay': 0.5,
            'debug_mode': False,
            'headless': False,
            'remote_debug_port': 9222,
            'chrome_path': ''
        }
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        return default_config
    
    def save_config(self, path='config.json'):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def init_browser(self):
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if self.config.get('proxy_port'):
            proxy = f'127.0.0.1:{self.config["proxy_port"]}'
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        
        debug_port = self.config.get('remote_debug_port', 9222)
        chrome_options.add_argument(f'--remote-debugging-port={debug_port}')
        chrome_options.add_argument(f'--remote-debugging-address=0.0.0.0')
        
        if self.config.get('headless'):
            chrome_options.add_argument('--headless=new')
        
        chrome_path = self.config.get('chrome_path')
        
        try:
            print("正在启动Chrome浏览器...")
            if chrome_path and os.path.exists(chrome_path):
                service = Service(executable_path=chrome_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.set_page_load_timeout(30)
            print("Chrome浏览器启动成功！")
        except Exception as e:
            print(f"\n浏览器启动失败: {e}")
            print("\n可能的原因：")
            print("1. Chrome路径不正确")
            print("2. Chrome版本与Selenium不兼容")
            print("3. 需要更新Chrome或Selenium")
            print("\n建议：")
            print("1. 确认Chrome路径是否正确")
            print("2. 在config.json中修改chrome_path")
            print("3. 运行: pip install --upgrade selenium")
            raise
        
        print(f"\n远程调试地址: http://localhost:{debug_port}")
        print(f"请在你的本地浏览器中打开上面的地址，即可看到脚本控制的Chrome窗口")
        print(f"打开后可以手动登录DMM账号\n")
    
    def safe_click(self, element, delay=0.5):
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).pause(delay).click().perform()
            time.sleep(delay)
            return True
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Click error: {e}")
            return False
    
    def wait_and_click(self, by, value, timeout=10):
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, value)))
            return self.safe_click(element)
        except TimeoutException:
            if self.config['debug_mode']:
                print(f"Wait and click timeout for: {value}")
            return False
    
    def wait_for_element(self, by, value, timeout=10):
        try:
            return self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            if self.config['debug_mode']:
                print(f"Wait for element timeout for: {value}")
            return None
    
    def click_by_text(self, text, timeout=10):
        try:
            xpath = f"//*[text()='{text}']"
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            return self.safe_click(element)
        except TimeoutException:
            if self.config['debug_mode']:
                print(f"Click by text timeout for: {text}")
            return False
    
    def click_by_contains_text(self, text, timeout=10):
        try:
            xpath = f"//*[contains(text(), '{text}')]"
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            return self.safe_click(element)
        except TimeoutException:
            if self.config['debug_mode']:
                print(f"Click by contains text timeout for: {text}")
            return False
    
    def enter_text(self, by, value, text):
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            element.clear()
            element.send_keys(text)
            time.sleep(0.5)
            return True
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Enter text error: {e}")
            return False
    
    def handle_popup(self):
        popup_selectors = [
            (By.XPATH, "//button[contains(text(), '閉じる')]"),
            (By.XPATH, "//button[contains(text(), 'Close')]"),
            (By.XPATH, "//button[contains(text(), 'OK')]"),
            (By.XPATH, "//button[contains(text(), '了解')]"),
            (By.XPATH, "//*[@class='close']"),
            (By.XPATH, "//*[@class='popup-close']")
        ]
        
        for by, selector in popup_selectors:
            try:
                element = self.driver.find_element(by, selector)
                if element.is_displayed():
                    self.safe_click(element)
                    return True
            except NoSuchElementException:
                continue
        return False
    
    def login_dmm(self):
        if not self.config['auto_login'] or not self.config['dmm_id'] or not self.config['dmm_password']:
            print("自动登录未配置，进入手动登录模式")
            return self.manual_login()
        
        try:
            print("开始DMM自动登录...")
            self.driver.get('https://www.dmm.com/my/-/login/')
            time.sleep(3)
            
            self.handle_popup()
            
            self.enter_text(By.ID, 'login_id', self.config['dmm_id'])
            self.enter_text(By.ID, 'password', self.config['dmm_password'])
            
            self.wait_and_click(By.ID, 'login_button')
            time.sleep(5)
            
            if "ログイン" in self.driver.title:
                print("自动登录失败，切换到手动登录")
                return self.manual_login()
            
            print("DMM登录成功")
            return True
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Login error: {e}")
            print("自动登录失败，切换到手动登录")
            return self.manual_login()
    
    def manual_login(self):
        print("\n" + "="*50)
        print("请在打开的浏览器中手动完成以下操作：")
        print("1. 登录你的 DMM 账号")
        print("2. 确保已经进入游戏页面")
        print("3. 完成后回到这里按 Enter 键继续")
        print("="*50 + "\n")
        
        try:
            self.driver.get('https://www.dmm.com/my/-/login/')
        except:
            pass
        
        input("按 Enter 继续...")
        print("登录确认完成，继续执行...")
        return True
    
    def enter_game(self):
        try:
            if self.config['game_url'] not in self.driver.current_url:
                print("进入游戏...")
                self.driver.get(self.config['game_url'])
                time.sleep(10)
            else:
                print("已在游戏页面，跳过导航")
            
            self.handle_popup()
            
            if self.wait_for_element(By.XPATH, "//*[contains(text(), 'スタート')]"):
                self.click_by_text('スタート')
                time.sleep(5)
            
            print("游戏加载完成")
            return True
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Enter game error: {e}")
            return False
    
    def collect_rewards(self):
        if not self.config['auto_rewards']:
            return
        
        print("领取奖励...")
        
        reward_selectors = [
            ("メール", "//*[contains(text(), 'メール')]"),
            ("プレゼント", "//*[contains(text(), 'プレゼント')]"),
            ("報酬", "//*[contains(text(), '報酬')]"),
            ("受け取り", "//*[contains(text(), '受け取り')]")
        ]
        
        for name, selector in reward_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    self.safe_click(element)
                    time.sleep(2)
                    self.click_by_text('受け取る')
                    time.sleep(2)
                    self.click_by_text('閉じる')
                    time.sleep(1)
                    print(f"已领取{name}奖励")
            except NoSuchElementException:
                continue
    
    def complete_daily_tasks(self):
        if not self.config['auto_daily']:
            return
        
        print("完成日常任务...")
        
        daily_selectors = [
            ("デイリー", "//*[contains(text(), 'デイリー')]"),
            ("ミッション", "//*[contains(text(), 'ミッション')]"),
            ("派遣", "//*[contains(text(), '派遣')]")
        ]
        
        for name, selector in daily_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    self.safe_click(element)
                    time.sleep(3)
                    
                    if name == '派遣':
                        self.click_by_text('完了')
                        time.sleep(1)
                        self.click_by_text('派遣')
                        time.sleep(1)
                        self.click_by_text('スキップ')
                    else:
                        self.click_by_text('受け取る')
                        time.sleep(1)
                    
                    self.click_by_text('戻る')
                    time.sleep(1)
                    print(f"已完成{name}任务")
            except NoSuchElementException:
                continue
    
    def select_event_choice(self):
        if not self.config['auto_event']:
            return
        
        event_choices = [
            ("戦闘", 1),
            ("宝箱", 2),
            ("商店", 3),
            ("休息", 4),
            ("イベント", 5)
        ]
        
        try:
            for text, priority in event_choices:
                xpath = f"//*[contains(text(), '{text}')]"
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    if element.is_displayed():
                        self.safe_click(element)
                        time.sleep(3)
                        print(f"选择了事件: {text}")
                        return
                except NoSuchElementException:
                    continue
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Event choice error: {e}")
    
    def start_battle(self):
        if not self.config['auto_battle']:
            return False
        
        print("开始战斗...")
        
        battle_buttons = [
            "戦闘開始",
            "スタート",
            "開始",
            "次のステージ",
            "挑戦"
        ]
        
        for button_text in battle_buttons:
            if self.click_by_contains_text(button_text):
                time.sleep(3)
                return True
        
        return False
    
    def wait_battle_finish(self):
        print("等待战斗结束...")
        
        finish_selectors = [
            "戦闘終了",
            "勝利",
            "敗北",
            "クリア",
            "リトライ",
            "次のステージ"
        ]
        
        timeout = 120
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            for text in finish_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
                    if element.is_displayed():
                        if text in ["リトライ", "敗北"]:
                            print("战斗失败，重新挑战")
                            self.safe_click(element)
                            time.sleep(5)
                            return "retry"
                        else:
                            self.safe_click(element)
                            time.sleep(3)
                            return "success"
                except NoSuchElementException:
                    continue
            
            time.sleep(2)
        
        print("战斗超时")
        return "timeout"
    
    def auto_battle_loop(self):
        print("开始自动战斗循环...")
        battles_completed = 0
        
        while self.running and battles_completed < self.config['max_battles']:
            self.collect_rewards()
            self.complete_daily_tasks()
            self.select_event_choice()
            
            if not self.start_battle():
                print("找不到战斗按钮，尝试寻找其他入口")
                time.sleep(5)
                continue
            
            result = self.wait_battle_finish()
            
            if result == "success":
                battles_completed += 1
                print(f"战斗完成: {battles_completed}/{self.config['max_battles']}")
            elif result == "retry":
                print("重新挑战中...")
            elif result == "timeout":
                print("战斗超时，继续循环")
            
            time.sleep(self.config['battle_delay'])
    
    def run(self):
        self.running = True
        
        try:
            print("初始化浏览器...")
            self.init_browser()
            
            if not self.login_dmm():
                print("请手动完成登录，然后按Enter继续...")
                input()
            
            if not self.enter_game():
                print("请手动进入游戏，然后按Enter继续...")
                input()
            
            self.auto_battle_loop()
            
        except KeyboardInterrupt:
            print("脚本已停止")
        except Exception as e:
            if self.config['debug_mode']:
                print(f"运行错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            if self.driver:
                self.driver.quit()
            print("脚本结束")

if __name__ == "__main__":
    bot = RlyehShoujotaiBot()
    
    mode = "手动登录" if (not bot.config['auto_login'] or not bot.config['dmm_id'] or not bot.config['dmm_password']) else "自动登录"
    print(f"启动模式: {mode}")
    print(f"游戏地址: {bot.config['game_url']}")
    print()
    
    bot.run()