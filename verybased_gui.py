import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

class BasedMemeBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Based Meme Bot")
        self.root.geometry("800x600")
        
        # 控制变量
        self.is_running = False
        self.current_address = ""
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="Based Meme Bot", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, text="状态:")
        status_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        status_display = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_display.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 当前地址显示
        self.address_var = tk.StringVar(value="无")
        addr_label = ttk.Label(main_frame, text="当前地址:")
        addr_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        addr_display = ttk.Label(main_frame, textvariable=self.address_var, foreground="green")
        addr_display.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 进度显示
        self.progress_var = tk.StringVar(value="0/0")
        progress_label = ttk.Label(main_frame, text="进度:")
        progress_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        progress_display = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_display.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始运行", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志框
        log_label = ttk.Label(main_frame, text="运行日志:")
        log_label.grid(row=6, column=0, sticky=tk.W, pady=(20, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, width=80, height=20, state=tk.DISABLED)
        self.log_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def log_message(self, message):
        """添加消息到日志框"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 更新GUI
        self.root.update_idletasks()
    
    def update_progress(self, current, total):
        """更新进度显示"""
        self.progress_var.set(f"{current}/{total}")
        if total > 0:
            progress = (current / total) * 100
            self.progress_bar['value'] = progress
    
    def update_status(self, status, address=""):
        """更新状态显示"""
        self.status_var.set(status)
        if address:
            # 显示前6位和后4位，保护隐私
            if len(address) > 10:
                masked_addr = f"{address[:6]}...{address[-4:]}"
            else:
                masked_addr = address
            self.address_var.set(masked_addr)
        else:
            self.address_var.set("无")
    
    def start_bot(self):
        """开始运行机器人"""
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 在新线程中运行机器人
        bot_thread = threading.Thread(target=self.run_bot)
        bot_thread.daemon = True
        bot_thread.start()
    
    def stop_bot(self):
        """停止机器人"""
        self.is_running = False
        self.log_message("正在停止...")
        self.update_status("正在停止")
    
    def run_bot(self):
        """运行机器人的主逻辑"""
        try:
            # 读取地址文件
            try:
                with open('address.txt', 'r') as f:
                    addresses = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                self.log_message("错误: 找不到 address.txt 文件")
                self.update_status("错误")
                return
            except Exception as e:
                self.log_message(f"读取文件错误: {e}")
                self.update_status("错误")
                return
            
            if not addresses:
                self.log_message("错误: address.txt 文件中没有找到有效的地址")
                self.update_status("错误")
                return
            
            total_addresses = len(addresses)
            self.log_message(f"找到 {total_addresses} 个地址")
            self.update_progress(0, total_addresses)
            
            with sync_playwright() as p:
                # 无头模式
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                successful_submissions = 0
                failed_submissions = 0
                
                for index, addr in enumerate(addresses, 1):
                    if not self.is_running:
                        self.log_message("运行被用户停止")
                        break
                    
                    self.update_status("运行中", addr)
                    self.update_progress(index, total_addresses)
                    
                    self.log_message(f"处理地址 {index}/{total_addresses}: {addr[:8]}...{addr[-6:]}")
                    
                    try:
                        # Go to the page
                        self.log_message("  正在加载页面...")
                        page.goto('https://verybased.meme')
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(1000)
                        
                        # Wait for and click the image using partial src match
                        self.log_message("  正在点击图片...")
                        image_selector = 'img[src*="basememe.png"]'
                        page.wait_for_selector(image_selector, timeout=10000)
                        page.locator(image_selector).click()
                        
                        # Fill invite code
                        self.log_message("  正在填写邀请码...")
                        invite_input = page.get_by_placeholder('Invite Code')
                        invite_input.fill('basememe')
                        page.wait_for_timeout(1000)
                        
                        # Click Enter Invite Code button
                        page.get_by_role('button', name='Enter Invite Code').click()
                        
                        # Wait for navigation to next page
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(1000)
                        
                        # 点击复选框
                        self.log_message("  正在勾选复选框...")
                        checkbox_container = page.locator('div.MuiStack-root.css-93wled')
                        checkbox_container.click()
                        
                        # Wait a bit to ensure the click registers
                        page.wait_for_timeout(500)
                        
                        # Fill Twitter username
                        self.log_message("  正在填写Twitter用户名...")
                        twitter_input = page.get_by_placeholder('Twitter username')
                        twitter_input.fill('elonmusk')
                        
                        # Fill EVM wallet address
                        self.log_message("  正在填写钱包地址...")
                        wallet_input = page.get_by_placeholder('EVM wallet address')
                        wallet_input.fill(addr)
                        
                        # Wait 1 second
                        page.wait_for_timeout(1000)
                        
                        # Click Submit
                        self.log_message("  正在提交表单...")
                        page.get_by_role('button', name='Submit').click()
                        
                        # 等待提交完成
                        page.wait_for_timeout(2000)
                        
                        successful_submissions += 1
                        self.log_message(f"  ✓ 地址 {addr[:8]}...{addr[-6:]} 提交成功")
                        
                    except Exception as e:
                        failed_submissions += 1
                        self.log_message(f"  ✗ 地址 {addr[:8]}...{addr[-6:]} 提交失败: {str(e)}")
                    
                    # 等待1-2秒再进行下一个
                    if index < total_addresses and self.is_running:
                        self.log_message("  等待中...")
                        page.wait_for_timeout(1500)
                
                # 关闭浏览器
                browser.close()
                
                # 显示最终结果
                self.log_message(f"\n运行完成!")
                self.log_message(f"成功提交: {successful_submissions}")
                self.log_message(f"失败提交: {failed_submissions}")
                self.log_message(f"总计处理: {successful_submissions + failed_submissions}/{total_addresses}")
                
                self.update_status("完成")
                
        except Exception as e:
            self.log_message(f"运行过程中发生错误: {str(e)}")
            self.update_status("错误")
        
        finally:
            # 重置按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_running = False

def main():
    root = tk.Tk()
    app = BasedMemeBot(root)
    root.mainloop()

if __name__ == "__main__":
    main()
