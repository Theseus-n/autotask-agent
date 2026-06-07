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
            print("LMS Timeout. Check your connection")
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
            # Punching the notification button from tracking the css named fa-bell
            notification_button = page.locator("i.fa-bell").first

            # Waiting result..
            await notification_button.wait_for(state="visible", timeout=10000)
            await notification_button.click()

            await page.locator("div.content-item-container.notification").first.wait_for(state="visible", timeout=5000)

            notification_items = await page.locator("div.content-item-container.notification").all()
            print("Checking notif")

            if not notification_items:
                print("There is no notification")
                return False
        
            notification_result = []

            for i in range(len(notification_items)):
                if i > 0:
                    await notification_button.click()
                    await page.locator("div.content-item-container.notification").nth(i).wait_for(state="visible", timeout=3000)

                current_item = page.locator("div.content-item-container.notification").nth(i)
                view_link = current_item.get_by_role("link", name="View full notification")
                await view_link.click()

                await page.wait_for_load_state("networkidle")

                link_task = page.locator("div.content a").nth(-1)
                print(f"Current task get!")

                link_course = page.locator("div.content a").nth(0)
                print(f"Current course get!")

                name_task = (await link_task.text_content()).strip()
                print(f"Current name get! {name_task}")

                name_course = (await link_course.text_content()).strip()
                print(f"Current course get! {name_course}")
                
                result = f"Task info: {name_task} from Course: {name_course}"
                notification_result.append(result)

                await page.go_back()
                await notification_button.wait_for(state="attached")

            return notification_result

        except PlaywrightTimeoutError:
            print("\nTimeout error.\nElemen name cannot be found.")
            return False
        except Exception as e:
            print(f"\nError: {e}")
            return False

    async def course_query(self, page:Page):
        container_locator = page.locator("[role='list']")

        try: 
            await container_locator.wait_for(state="visible", timeout=8000)
        except PlaywrightTimeoutError:
            print("Cannot find container")
            return False
        
        items_locator = container_locator.locator("[role='listitem']")

        await items_locator.first.wait_for(state="attached", timeout = 5000)
        items = await items_locator.all()

        courses = {}

        if not items:
            print("Tidak ada mata kuliah")
            return False
        
        for i in items:
            link_locator = i.locator("a.aalink").first

            if await link_locator.count() > 0:
                href = await link_locator.get_attribute("href")
                raw = await link_locator.inner_text()
                text = re.sub(r'(?i)course\s+name', '', raw).strip() if raw else ""

                if text and href:
                    courses[text] = href
        
        if not courses:
            print("There is no courses")
            return False
        
        print("\n=== DAFTAR MATA KULIAH YANG DITEMUKAN ===")
        for index, course_name in enumerate(courses.keys(), 1):
            print(f"{index}. {course_name}")

        chosen_course = input("\nMasukkan nama mata kuliah: ").strip()

        if chosen_course in courses:
            target_url = courses[chosen_course]

            print(f"\nNavigasi ke: {target_url}")
            await page.goto(target_url, timeout=15000)
            await page.wait_for_load_state("networkidle")
            print(f"Berhasil masuk ke halaman mata kuliah!")
            return True
        else:
            print(f"Mata kuliah '{chosen_course}' tidak ditemukan di dalam dictionary hasil query.")
            return False


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
                # await agent.notification(page)

                await agent.course_query(page)
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
