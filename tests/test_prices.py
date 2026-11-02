import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
import unittest
from prices import normalize_asin, parse_books, parse_amazon, csv_export


class PricesTest(unittest.TestCase):
    def test_url_validation_prevents_arbitrary_fetches(self):
        for text in ['http://127.0.0.1/', 'https://amazon.com.evil.test/dp/B000000001', 'https://user@amazon.com/dp/B000000001', 'https://www.amazon.com/']:
            with self.assertRaises(ValueError): normalize_asin(text)
        self.assertEqual(normalize_asin('https://www.amazon.com/name/dp/B000000001?tag=example'), 'B000000001')

    def test_sandbox_currency_prices_and_provenance(self):
        rows = parse_books('<article class="product_pod"><h3><a href="catalogue/demo/index.html" title="Demo book">Book</a></h3><p class="price_color">£12.34</p></article>', '2026-11-02T00:00:00Z')
        self.assertEqual((rows[0]['price'],rows[0]['currency']), (12.34,'GBP'))
        self.assertEqual(rows[0]['url'], 'https://books.toscrape.com/catalogue/demo/index.html')
        self.assertEqual(rows[0]['observed_at'], '2026-11-02T00:00:00Z')

    def test_missing_price_never_becomes_zero(self):
        with self.assertRaises(ValueError): parse_books('<html>temporarily unavailable</html>')
        with self.assertRaises(ValueError): parse_amazon('<div id="productTitle">Name</div>', 'B000000001')

    def test_fractional_usd_price(self):
        row = parse_amazon('<span id="productTitle">Demo</span><div id="corePrice_feature_div"><span class="a-price"><span class="a-offscreen">$1,234.56</span></span></div>', 'B000000001')
        self.assertEqual((row['price'],row['currency']), (1234.56,'USD'))

    def test_csv_formula_injection_escaped(self):
        csv = csv_export([{'title':'=HYPERLINK("bad")', 'price': 12.3, 'currency':'GBP'}])
        self.assertIn("'=HYPERLINK",csv)


if __name__ == '__main__': unittest.main()
