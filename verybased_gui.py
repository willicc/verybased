import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
from playwright.sync_api import sync_playwright # Pastikan ini diimpor

class BasedMemeBot:
    def __init__(self, root=None):
        self.root = root
        self.has_gui = (root is not None)
        self._is_running = False # Gunakan atribut privat untuk kontrol internal
        self.current_address = ""
        self.bot_thread = None # Simpan referensi thread bot

        if self.has_gui:
            self.create_widgets()
        else:
            print("GUI not available. Running in console mode.")
            self.log_message("Console Mode: Logging to console.")

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Based Meme Bot", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Status display
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, text="Status:")
        status_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        status_display = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_display.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Current address display
        self.address_var = tk.StringVar(value="None")
        addr_label = ttk.Label(main_frame, text="Current Address:")
        addr_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        addr_display = ttk.Label(main_frame, textvariable=self.address_var, foreground="green")
        addr_display.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Progress display
        self.progress_var = tk.StringVar(value="0/0")
        progress_label = ttk.Label(main_frame, text="Progress:")
        progress_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        progress_display = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_display.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log box
        log_label = ttk.Label(main_frame, text="Log:")
        log_label.grid(row=6, column=0, sticky=tk.W, pady=(20, 5))

        self.log_text = scrolledtext.ScrolledText(main_frame, width=80, height=20, state=tk.DISABLED)
        self.log_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def log_message(self, message):
        """Add message to log box or print to console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        if self.has_gui:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            # Update GUI
            self.root.update_idletasks()
        else:
            # Print to console if no GUI
            print(log_entry.strip())

    def update_progress(self, current, total):
        """Update progress display"""
        if self.has_gui:
            self.progress_var.set(f"{current}/{total}")
            if total > 0:
                progress = (current / total) * 100
                self.progress_bar['value'] = progress
        else:
            # Optionally print progress to console
            if total > 0:
                percentage = (current / total) * 100
                self.log_message(f"Progress: {current}/{total} ({percentage:.2f}%)")

    def update_status(self, status, address=""):
        """Update status display"""
        if self.has_gui:
            self.status_var.set(status)
            if address:
                # Show first 6 and last 4 chars, protect privacy
                if len(address) > 10:
                    masked_addr = f"{address[:6]}...{address[-4:]}"
                else:
                    masked_addr = address
                self.address_var.set(masked_addr)
            else:
                self.address_var.set("None")
        else:
            # Optionally print status to console
            addr_display = f" (Address: {address})" if address else ""
            self.log_message(f"Status: {status}{addr_display}")

    @property
    def is_running(self):
        """Getter untuk variabel is_running."""
        return self._is_running

    def start_bot(self):
        """Start the bot"""
        if self.has_gui:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

        self._is_running = True # Set internal flag
        self.bot_thread = threading.Thread(target=self.run_bot)
        self.bot_thread.daemon = False # Jangan jadikan daemon agar bisa dijoin
        self.bot_thread.start()

        # Jika GUI tidak ada, tunggu thread selesai di sini atau tangani di main
        if not self.has_gui:
            # Dalam mode konsol, kita tetap ingin menunggu thread bot selesai
            # atau bisa dihentikan. Kita tangani di main().
            pass # Biarkan berjalan, main() akan handle


    def stop_bot(self):
        """Stop the bot"""
        self.log_message("Stopping...")
        self._is_running = False # Set internal flag
        if self.has_gui:
            self.update_status("Stopping")
            # Jangan reset tombol di sini, biarkan run_bot handle itu saat selesai

    def run_bot(self):
        """Main logic for the bot"""
        try:
            # Read addresses file
            try:
                with open('address.txt', 'r') as f:
                    addresses = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                self.log_message("Error: address.txt file not found")
                self.update_status("Error")
                return
            except Exception as e:
                self.log_message(f"File read error: {e}")
                self.update_status("Error")
                return

            if not addresses:
                self.log_message("Error: No valid addresses found in address.txt")
                self.update_status("Error")
                return

            total_addresses = len(addresses)
            self.log_message(f"Found {total_addresses} addresses")
            self.update_progress(0, total_addresses)

            with sync_playwright() as p:
                # Launch browser headless
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                successful_submissions = 0
                failed_submissions = 0

                for index, addr in enumerate(addresses, 1):
                    if not self.is_running: # Gunakan getter
                        self.log_message("Run stopped by user")
                        break

                    self.update_status("Running", addr)
                    self.update_progress(index, total_addresses)

                    self.log_message(f"Processing address {index}/{total_addresses}: {addr[:8]}...{addr[-6:]}")

                    try:
                        # Navigate to the page - Fixed URL
                        self.log_message("  Loading page...")
                        page.goto('https://verybased.meme') # Removed extra space
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(1000)

                        # Wait for and click the image using partial src match
                        self.log_message("  Clicking image...")
                        image_selector = 'img[src*="basememe.png"]'
                        page.wait_for_selector(image_selector, timeout=10000)
                        page.locator(image_selector).click()

                        # Fill invite code
                        self.log_message("  Filling invite code...")
                        invite_input = page.get_by_placeholder('Invite Code')
                        invite_input.fill('basememe')
                        page.wait_for_timeout(1000)

                        # Click Enter Invite Code button
                        page.get_by_role('button', name='Enter Invite Code').click()

                        # Wait for navigation to next page
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(1000)

                        # Click checkbox - Updated selector for robustness
                        self.log_message("  Clicking checkbox...")
                        # Try clicking the container first, which often triggers the checkbox
                        checkbox_container = page.locator('div.MuiStack-root.css-93wled')
                        checkbox_container.click()
                        page.wait_for_timeout(500) # Brief wait


                        # Fill Twitter username
                        self.log_message("  Filling Twitter username...")
                        twitter_input = page.get_by_placeholder('Twitter username')
                        twitter_input.fill('elonmusk')

                        # Fill EVM wallet address
                        self.log_message("  Filling wallet address...")
                        wallet_input = page.get_by_placeholder('EVM wallet address')
                        wallet_input.fill(addr)

                        # Wait 1 second
                        page.wait_for_timeout(1000)

                        # Click Submit
                        self.log_message("  Submitting form...")
                        page.get_by_role('button', name='Submit').click()

                        # Wait for submission
                        page.wait_for_timeout(2000)

                        successful_submissions += 1
                        self.log_message(f"  ✓ Address {addr[:8]}...{addr[-6:]} submitted successfully")

                    except Exception as e:
                        failed_submissions += 1
                        self.log_message(f"  ✗ Address {addr[:8]}...{addr[-6:]} submission failed: {str(e)}")

                    # Wait 1.5 seconds before next iteration if not stopped
                    if index < total_addresses and self.is_running: # Gunakan getter
                        self.log_message("  Waiting...")
                        page.wait_for_timeout(1500)

                # Close browser
                browser.close()

                # Show final results
                self.log_message(f"\nRun completed!")
                self.log_message(f"Successful submissions: {successful_submissions}")
                self.log_message(f"Failed submissions: {failed_submissions}")
                self.log_message(f"Total processed: {successful_submissions + failed_submissions}/{total_addresses}")

                self.update_status("Completed")

        except Exception as e:
            self.log_message(f"An error occurred during run: {str(e)}")
            self.update_status("Error")

        finally:
            # Reset button states if GUI is available
            if self.has_gui:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
            # Reset internal flag
            self._is_running = False # Pastikan flag internal juga direset


def main():
    # Check if a display is available
    if os.environ.get('DISPLAY'):
        # GUI available
        root = tk.Tk()
        app = BasedMemeBot(root)
        root.mainloop()
    else:
        # No GUI available, run in console mode
        app = BasedMemeBot() # Pass None for root
        app.start_bot() # Start the bot thread in console mode

        # --- Perubahan Utama Di Sini ---
        # Tunggu thread bot selesai atau tangani KeyboardInterrupt
        try:
            # Gunakan join() untuk menunggu thread bot selesai
            # Timeout 1 detik agar loop bisa memeriksa KeyboardInterrupt
            while app.bot_thread is not None and app.bot_thread.is_alive():
                 app.bot_thread.join(timeout=1) # Tunggu maksimal 1 detik
                 # Jika loop ini aktif, KeyboardInterrupt akan ditangkap di sini
                 # Jika tidak, program akan terus menunggu

        except KeyboardInterrupt:
            print("\nKeyboard Interrupt received. Stopping bot...")
            app.stop_bot() # Hentikan bot secara lembut
            # Tunggu thread sebentar agar bisa menyelesaikan iterasi saat ini
            if app.bot_thread is not None:
                 app.bot_thread.join(timeout=5) # Tunggu maks 5 detik
            print("Bot stopped by user.")

if __name__ == "__main__":
    main()
