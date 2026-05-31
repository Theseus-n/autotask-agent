import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from playwright.async_api import async_playwright


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

class LMSAgent:
    def __init__(self):
        self.lms_url = os.getenv("LMS_URL")
        self.username = os.getenv("LMS_USERNAME")
        self.password = os.getenv("LMS_PASSWORD")
    
    async def run_workflow(self):
        async with async_playwright() as p:
            print("Browser login..")
            browser = await p.chromium.launch(headless=False, slow_mo=2000)
            print("Browser make context..")
            context = await browser.new_context()
            print("Making page login..")
            page = await context.new_page()

            print(f"Logging in to {self.lms_url}")
            await page.goto(self.lms_url)

            print("Logging account in...")
            await page.fill("#username", self.username)
            # Isi  Email 
            await page.fill('#username', self.username)
            # Isi Password
            await page.fill('#password', self.password)
            # Klik tombol Log in
            await page.click('button:has-text("Log in")')

            await page.wait_for_load_state("networkidle")
            print("Berhasil masuk ke Dashboard LMS!")

            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    agent = LMSAgent()
    asyncio.run(agent.run_workflow())

            