import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

class LMSAgent:
    def __init__(self):
        self.lms_url = os.getenv("LMS_URL")
        assert self.lms_url, "Missing URL"

        self.username = os.getenv("LMS_USERNAME")
        assert self.username, "Username not Detected "\
        
        self.password = os.getenv("LMS_PASSWORD")
        assert self.password, "Password not Detected"
    
    async def main(self):
        async with async_playwright() as p:
            browser = None
            try:
              print("\nBrowser login..")
              browser = await p.chromium.launch(headless=False, slow_mo=2000)

              print("\nMake new session..")
              context = await browser.new_context()

              print("\nMaking new tab..")
              page = await context.new_page()

              try:
                print(f"\nLogging in to {self.lms_url}")
                await page.goto(self.lms_url, timeout=15000)
              except PlaywrightTimeoutError:
                print("LMS Timeout.")
                return
              except Exception as e:
                if "ERR_INTERNET_DISCONNECTED" in str(e):
                  print("\nNo internet Connection.")
                else:
                  print(f"Cannot connect to {self.lms_url}. Detail: {e}")
                return
                
              print("\nLogging account in...")
              try:
                # Isi  Email
                await page.get_by_placeholder("Username or email").fill(self.username)

                # Isi Password
                await page.get_by_placeholder("Password").fill(self.password)

                # Klik tombol Log in
                await page.get_by_role("button", name="Log in").click()
              except Exception as e:
                print(f"Error: {e}")
                return
            
              print("\nChecking login...")
              try:
                await page.wait_for_load_state("networkidle")
                if "login" in page.url.lower():
                  print("Login failed")
                  return
              except PlaywrightTimeoutError:
                print("LMS Timeout.")

              print("\nBerhasil masuk ke Dashboard LMS!")

              await asyncio.sleep(5)
              await browser.close()

            except Exception as e:
               print(f"Error: {e}")

            finally:
              if browser:
                print("\nClosing browser...")
                await browser.close()

if __name__ == "__main__":
    agent = LMSAgent()
    asyncio.run(agent.main())

            