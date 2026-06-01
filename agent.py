import asyncio
import os
import re

from dotenv import load_dotenv
from openai import OpenAI
from playwright.async_api import Locator, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)


class LMSAgent:
    def __init__(self):
        self.lms_url = os.getenv("LMS_URL")
        assert self.lms_url, "Missing URL"

        self.username = os.getenv("LMS_USERNAME")
        assert self.username, "Username not Detected"

        self.password = os.getenv("LMS_PASSWORD")
        assert self.password, "Password not Detected"

    async def login(self, page: Page):
        try:
            print(f"\nLogging in to {self.lms_url}")
            await page.goto(self.lms_url, timeout=15000)
        except PlaywrightTimeoutError:
            print("LMS Timeout.")
            return False
        except Exception as e:
            if "ERR_INTERNET_DISCONNECTED" in str(e):
                print("\nNo internet Connection.")
            else:
                print(f"Cannot connect to {self.lms_url}. Detail: {e}")
            return False

        print("\nLogging account in...")
        try:
            await page.get_by_placeholder("Username or email").fill(self.username)
            await page.get_by_placeholder("Password").fill(self.password)
            await page.get_by_role("button", name="Log in").click()
        except Exception as e:
            print(f"Error: {e}")
            return False

        print("\nChecking login...")
        try:
            await page.wait_for_load_state("networkidle")
            if "login" in page.url.lower():
                print("Login failed")
                return False
        except PlaywrightTimeoutError:
            print("LMS Timeout.")
            return False

        print("\nBerhasil masuk ke Dashboard LMS!")
        return True

    async def notification(self, page: Page):
        try:
            notification_button = page.get_by_role("button", name=re.compile(r"notification", re.IGNORECASE))

            # For visible is depend on your internet, current default is 10s
            await notification_button.wait_for(state="visible", timeout=10000)
            await notification_button.click()

            # Getting the first notification
            view_all_link = page.get_by_role("link", name="View full notification").first
            await view_all_link.wait_for(state="visible", timeout=3000)
            await view_all_link.click()

            await page.wait_for_load_state("networkidle")
            print("Notification clicked. ")

        except PlaywrightTimeoutError:
            print(
                "\nTimeout error."
            )
            print(
                "Elemen name cannot be found."
            )
        except Exception as e:
            print(f"\nError: {e}")


async def main():
    print("Starting Agent... Goodluck")

    async with async_playwright() as p:
        browser = None
        try:
            print("\nBrowser login..")
            browser = await p.chromium.launch(headless=False, slow_mo=2000)
            context = await browser.new_context()
            page = await context.new_page()

            agent = LMSAgent()

            login_success = await agent.login(page)

            if login_success:
                await agent.notification(page)
                print("Done.. ")
        except PlaywrightTimeoutError as e:
            print(f"\n[ERROR] Waktu habis saat menunggu elemen. Detail: {e}")
        except Exception as e:
            print(f"\n[ERROR] Terjadi kesalahan: {e}")
        finally:
            await asyncio.sleep(3)  
            if browser:
                print("\nClosing browser...")
                await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
