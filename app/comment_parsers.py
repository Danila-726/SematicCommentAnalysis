from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

def parse_rutube_comments(
        url: str,
        headless: bool = True,
        driver_path: str = "chromedriver.exe",
        scroll_pause: float = 1.5,
        max_scroll_attempts: int = 20
) -> list:

    options = webdriver.ChromeOptions()
    # if headless:
    #     options.add_argument("--headless")
    # options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    driver.set_window_size(1200, 800)

    parsed_comments = []
    new_expand_button_cnt = 0

    try:
        driver.get(url)
        driver.execute_script("document.body.style.zoom = '50%'")
        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     'button.wdp-popup-module__icon.wdp-onboardings-inventory-module__closeIcon[aria-label="Закрыть"]')
                )
            )

            WebDriverWait(driver, 5).until(EC.visibility_of(close_button))
            driver.execute_script("arguments[0].scrollIntoView(true);", close_button)
            driver.execute_script("arguments[0].click();", close_button)
            print("▶ Всплывающее окно успешно закрыто")
            time.sleep(1.5)
        except Exception as e:
            print(f"⚠ Не удалось закрыть попап: {str(e)}")

        WebDriverWait(driver, random.uniform(0, 10)).until(
            EC.presence_of_element_located((By.CLASS_NAME, "wdp-comment-item-module__comment-item"))
        )

        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0

        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(scroll_pause + random.uniform(0, 2.0))

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1

        expand_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            ".wdp-comments-answers-button-module__expand-button:not(.wdp-comments-answers-button-module__expand-button-open)"
        )

        for button in expand_buttons:
            try:
                btn = button.find_element(
                    By.CSS_SELECTOR,
                    "button[class*='freyja_char-base-button__text-blue']"
                )
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(btn))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(btn))
                driver.execute_script("arguments[0].click();", btn)
                ans_cnt = int(btn.text.split()[1])

                new_expand_button_cnt += (ans_cnt - 1) // 10

                time.sleep(0.5 + random.uniform(0, 0.5))

            except Exception as e:
                print(f"⚠ Ошибка при раскрытии ответов: {str(e)}")

        comments = driver.find_elements(By.CLASS_NAME, "wdp-comment-item-module__comment-item")

        new_expand_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "[class~=wdp-comment-item-module__second-level-container]:not([class*=' '])"
        )

        print("len buttons: ", len(new_expand_buttons))

        while new_expand_button_cnt  > 0:
            for button in new_expand_buttons:
                btn = button.find_elements(By.CSS_SELECTOR, "button[class*='char-base-button__contained-darked']")
                if len(btn) != 0:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(btn[0]))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn[0])
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(btn[0]))
                    driver.execute_script("arguments[0].click();", btn[0])
                    new_expand_button_cnt -= 1

                    time.sleep(0.5 + random.uniform(0, 0.5))
            if check_hide_comments(new_expand_buttons, 'char-base-button__contained-darked'): break

        comments = driver.find_elements(By.CLASS_NAME, "wdp-comment-item-module__comment-item")

        for comment in comments:
            try:
                text = comment.get_attribute("aria-label")
                if text and text.strip():
                    parsed_comments.append(text.strip())
            except Exception as e:
                print(f"Ошибка парсинга комментария: {str(e)}")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        driver.quit()
        return parsed_comments

def check_hide_comments(expand_buttons, container):
    for button in expand_buttons:
        btn = button.find_elements(By.CSS_SELECTOR, f"button[class*={container}]")
        if len(btn) != 0:
            return False
    return True

