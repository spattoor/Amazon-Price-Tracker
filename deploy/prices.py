"""Bounded price extraction; no browser automation or arbitrary URL fetching."""
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import io
import re
from urllib.parse import urlsplit, urljoin
import requests
from bs4 import BeautifulSoup

BOOKS = 'https://books.toscrape.com/'


def read_page(url, session=None):
    session = session or requests
    with session.get(url, timeout=(4, 12), allow_redirects=False, stream=True,
                     headers={'User-Agent': 'PortfolioPriceTracker/1.0 (educational demo)'}) as response:
        if response.status_code != 200:
            raise ValueError(f'Source unavailable (HTTP {response.status_code}). No price was recorded.')
        payload = bytearray()
        for chunk in response.iter_content(32768):
            payload.extend(chunk)
            if len(payload) > 2 * 1024 * 1024:
                raise ValueError('Source response exceeded its size limit.')
    text = payload.decode('utf-8', errors='replace')
    if any(t in text.lower() for t in ('validatecaptcha', 'robot check', 'enter the characters you see')):
        raise ValueError('The source returned a robot check. No price was recorded; this demo does not bypass it.')
    return text


def amount(text):
    cleaned = re.sub(r'[^0-9.,]', '', text).replace(',', '')
    try:
        value = Decimal(cleaned)
    except InvalidOperation as error:
        raise ValueError('No valid price in the source.') from error
    if not value.is_finite() or not 0 < value < 10000000:
        raise ValueError('No valid positive price in the source.')
    return float(value)


def parse_books(html, observed_at=None):
    soup = BeautifulSoup(html, 'html.parser')
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    records = []
    for article in soup.select('article.product_pod')[:20]:
        link, price = article.select_one('h3 a'), article.select_one('.price_color')
        if not link or not price:
            continue
        title = link.get('title') or link.get_text(' ', strip=True)
        target = urljoin(BOOKS, link.get('href', ''))
        if urlsplit(target).netloc != 'books.toscrape.com':
            continue
        try:
            parsed = amount(price.get_text())
        except ValueError:
            continue
        records.append({'title': title[:300], 'price': parsed, 'currency': 'GBP', 'url': target,
                        'source': 'Books to Scrape sandbox', 'observed_at': observed_at})
    if not records:
        raise ValueError('No valid sandbox prices found. The source may have changed.')
    return records


def normalize_asin(value):
    value = value.strip()
    if re.fullmatch(r'[A-Za-z0-9]{10}', value):
        return value.upper()
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or parsed.netloc.lower() not in ('amazon.com', 'www.amazon.com'):
        raise ValueError('Enter a ten-character ASIN or an HTTPS amazon.com product link.')
    match = re.search(r'/(?:dp|gp/product)/([A-Za-z0-9]{10})(?:[/?]|$)', parsed.path)
    if not match:
        raise ValueError('The link must contain /dp/ASIN or /gp/product/ASIN.')
    return match.group(1).upper()


def parse_amazon(html, asin):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select_one('#productTitle')
    price = soup.select_one('#corePrice_feature_div .a-price .a-offscreen, #corePriceDisplay_desktop_feature_div .a-price .a-offscreen')
    if not title or not price or '$' not in price.get_text():
        raise ValueError('No supported USD product price found. Amazon may block automated requests or require a location/sign-in. No price was recorded.')
    return {'title': title.get_text(' ', strip=True)[:300], 'price': amount(price.get_text()),
            'currency': 'USD', 'url': 'https://www.amazon.com/dp/' + normalize_asin(asin),
            'source': 'Amazon.com product page', 'observed_at': datetime.now(timezone.utc).isoformat()}


def fetch_books():
    return parse_books(read_page(BOOKS))


def fetch_amazon(value):
    asin = normalize_asin(value)
    return parse_amazon(read_page('https://www.amazon.com/dp/' + asin), asin)


def csv_export(records):
    output = io.StringIO(newline='')
    columns = ['observed_at', 'title', 'price', 'currency', 'source', 'url']
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for record in records:
        safe = {k: ("'" + v if isinstance(v, str) and v[:1] in '=+-@' else v) for k, v in record.items() if k in columns}
        writer.writerow(safe)
    return output.getvalue()
