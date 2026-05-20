import concurrent.futures
import logging

from flask import Blueprint, render_template, request

from .database import save_notification, save_search
from .notifications import send_notification
from .scraper import get_price_amazon, get_price_croma, get_price_flipkart


main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main.app_errorhandler(404)
def page_not_found(error):
    logger.warning(f"404 Not Found: {request.path}")
    return render_template("index.html"), 404


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("index.html")

    product_name = request.form.get("product", "")
    if not product_name:
        return render_template("index.html")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            flipkart_future = executor.submit(get_price_flipkart, product_name)
            amazon_future = executor.submit(get_price_amazon, product_name)
            croma_future = executor.submit(get_price_croma, product_name)

            flipkart_price, flipkart_url = flipkart_future.result()
            amazon_price, amazon_url = amazon_future.result()
            croma_price, croma_url = croma_future.result()

        prices = [
            (flipkart_price, flipkart_url, "Flipkart"),
            (amazon_price, amazon_url, "Amazon"),
            (croma_price, croma_url, "Croma"),
        ]
        prices = [p for p in prices if p[0] is not None]

        if not prices:
            logger.warning("No prices found for the product.")
            save_search(product_name, flipkart_price, amazon_price, croma_price, None, None)
            return render_template(
                "results.html",
                product=product_name,
                error="No prices found for the product.",
            )

        min_price, min_url, min_site = min(prices, key=lambda x: x[0])
        logger.info(f"Best price found on {min_site}: Rs.{min_price}")
        save_search(product_name, flipkart_price, amazon_price, croma_price, min_site, min_url)

        return render_template(
            "results.html",
            product=product_name,
            flipkart_price=flipkart_price,
            amazon_price=amazon_price,
            croma_price=croma_price,
            flipkart_url=flipkart_url,
            amazon_url=amazon_url,
            croma_url=croma_url,
            min_url=min_url,
            min_site=min_site,
        )
    except Exception as e:
        logger.error(f"Error during search operation: {e}")
        return render_template(
            "results.html",
            product=product_name,
            error="An unexpected error occurred during the search.",
        )


@main.route("/notify", methods=["GET", "POST"])
def notify():
    if request.method == "GET":
        return render_template("index.html")

    try:
        product_name = request.form.get("product", "")
        user_price = float(request.form.get("price", 0))
        user_contact = request.form.get("contact", "")

        if not product_name or not user_contact:
            return render_template(
                "notify.html",
                product=product_name,
                user_price=user_price,
                user_contact=user_contact,
                error="Product and email are required.",
            )

        flipkart_price = request.form.get("flipkart_price")
        amazon_price = request.form.get("amazon_price")
        croma_price = request.form.get("croma_price")

        parsed_prices = {
            "Flipkart": _parse_optional_float(flipkart_price),
            "Amazon": _parse_optional_float(amazon_price),
            "Croma": _parse_optional_float(croma_price),
        }

        for site, price in parsed_prices.items():
            if price is not None:
                logger.info(f"Checking {site} notification price: Rs.{price}")
                send_notification(product_name, price, user_price, user_contact)

        save_notification(
            product_name,
            user_price,
            user_contact,
            parsed_prices["Flipkart"],
            parsed_prices["Amazon"],
            parsed_prices["Croma"],
        )

        logger.info(
            f"Notifications processed for '{product_name}' at desired price Rs.{user_price} to {user_contact}."
        )
        return render_template(
            "notify.html",
            product=product_name,
            user_price=user_price,
            user_contact=user_contact,
        )
    except ValueError as e:
        logger.error(f"Invalid input values: {e}")
        return render_template("notify.html", error="Please provide valid price and email values.")
    except Exception as e:
        logger.error(f"Error during notification process: {e}")
        return render_template("notify.html", error="An unexpected error occurred while setting up notifications.")


def _parse_optional_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        logger.error(f"Invalid price value: {value}")
        return None
