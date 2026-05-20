import logging
import os
import re
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


logger = logging.getLogger(__name__)


def normalize_product_name(product_name):
    normalized = re.sub(r"[^a-zA-Z0-9\s]", "", product_name.lower()).strip()
    normalized = re.sub(r"\s+", "+", normalized)
    return normalized


def parse_price_value(price_text):
    if not price_text:
        return None

    text = price_text.replace(",", "")
    text = re.sub(r"[\u20B9$\u20AC\u00A3\u00A5]", " ", text)
    text = re.sub(r"(?i)\b(RS\.?|INR|USD|EUR|GBP|JPY|CAD|AUD|AED|SGD|US)\b", " ", text)

    if re.search(r"\bto\b", text.lower()):
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def create_webdriver():
    try:
        options = Options()
        options.set_capability("pageLoadStrategy", "eager")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install(), log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Failed to create ChromeDriver: {e}")
        raise


def get_price_flipkart(product_name):
    wd = None
    try:
        wd = create_webdriver()
        wait = WebDriverWait(wd, 20)
        query = quote_plus(product_name)
        search_url = f"https://www.flipkart.com/search?q={query}"
        wd.get(search_url)
        logger.info(f"Searching for '{product_name}' on Flipkart")

        try:
            try:
                wd.execute_script(
                    """
                    const selectors = ['button._2KpZ6l._2doB4z', 'button[aria-label*=Close]'];
                    for (const s of selectors) {
                        const btn = document.querySelector(s);
                        if (btn) { btn.click(); break; }
                    }
                    """
                )
            except Exception:
                pass

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            price_selectors = [
                (By.CSS_SELECTOR, "div.Nx9bqj"),
                (By.CSS_SELECTOR, "div._30jeq3"),
                (By.CSS_SELECTOR, "div._30jeq3._1_WHN1"),
                (By.XPATH, "//div[contains(@class, 'Nx9bqj')]"),
                (By.XPATH, "//div[contains(text(), '\u20B9') or contains(text(), 'Rs.')]"),
            ]

            for by, selector in price_selectors:
                elements = wd.find_elements(by, selector)
                for elem in elements:
                    price_val = parse_price_value(elem.text.strip())
                    if price_val is not None:
                        logger.info(f"Flipkart Price: Rs.{price_val}")
                        return price_val, search_url

            logger.warning("Flipkart: No price found")
            return None, None
        except TimeoutException:
            logger.warning("Flipkart: Page load timeout")
            return None, None
        except (ValueError, IndexError) as e:
            logger.warning(f"Flipkart: Parse error - {e}")
            return None, None
    except Exception as e:
        logger.error(f"Flipkart Error: {e}")
        return None, None
    finally:
        if wd:
            try:
                wd.quit()
            except Exception:
                pass


def get_price_amazon(product_name):
    wd = None
    try:
        wd = create_webdriver()
        wait = WebDriverWait(wd, 15)
        query = quote_plus(product_name)
        search_url = f"https://www.amazon.in/s?k={query}"
        wd.get(search_url)
        logger.info(f"Searching for '{product_name}' on Amazon")
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'a-price')]")))

            price_selectors = [
                (By.CSS_SELECTOR, ".a-price-whole"),
                (By.XPATH, "//span[@class='a-price-whole']"),
                (By.XPATH, "//span[contains(@class, 'a-price-whole')]"),
                (By.XPATH, "//span[contains(text(), '\u20B9')]"),
            ]

            for by, selector in price_selectors:
                elements = wd.find_elements(by, selector)
                for elem in elements:
                    price = parse_price_value(elem.text.strip())
                    if price is not None:
                        logger.info(f"Amazon Price: Rs.{price}")
                        return price, search_url

            logger.warning("Amazon: No price found")
            return None, None
        except TimeoutException:
            logger.warning("Amazon: Page load timeout")
            return None, None
        except ValueError as e:
            logger.warning(f"Amazon: Parse error - {e}")
            return None, None
    except Exception as e:
        logger.error(f"Amazon Error: {e}")
        return None, None
    finally:
        if wd:
            try:
                wd.quit()
            except Exception:
                pass


def get_price_croma(product_name):
    wd = None
    try:
        wd = create_webdriver()
        wait = WebDriverWait(wd, 15)
        query = quote_plus(product_name)
        search_url = f"https://www.croma.com/searchB?q={query}%3Arelevance"

        try:
            wd.get(search_url)
        except TimeoutException:
            logger.info("Croma: Slow page load, trying to parse current DOM")

        logger.info(f"Searching for '{product_name}' on Croma")

        try:
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "li.product-item, .product-item, .cp-product, .amount")
                    )
                )
            except TimeoutException:
                pass

            price_selectors = [
                (By.CSS_SELECTOR, "span.amount"),
                (By.CSS_SELECTOR, "span.new-price"),
                (By.CSS_SELECTOR, "div.amount"),
                (By.XPATH, "//span[contains(text(), '\u20B9')]"),
                (By.XPATH, "//div[contains(text(), '\u20B9')]"),
            ]

            for by, selector in price_selectors:
                elements = wd.find_elements(by, selector)
                for elem in elements:
                    text = elem.text.strip()
                    price = parse_price_value(text)
                    if price is not None:
                        logger.info(f"Croma Price: Rs.{price} (raw text: {text})")
                        return price, search_url

            html = wd.page_source or ""
            for pattern in [
                r"(?:\u20B9|INR|RS\.?)\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
                r'"price"\s*:\s*"([0-9]+(?:\.[0-9]+)?)"',
            ]:
                match = re.search(pattern, html, flags=re.IGNORECASE)
                if not match:
                    continue
                try:
                    amount = float(match.group(1).replace(",", ""))
                except ValueError:
                    continue
                if amount > 0:
                    logger.info(f"Croma Price (HTML fallback): Rs.{amount}")
                    return amount, search_url

            logger.warning("Croma: No price found")
            return None, None
        except (ValueError, IndexError) as e:
            logger.warning(f"Croma: Parse error - {e}")
            return None, None
    except Exception as e:
        logger.error(f"Croma Error: {e}")
        return None, None
    finally:
        if wd:
            try:
                wd.quit()
            except Exception:
                pass
