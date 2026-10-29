"""Offline consistency checks for the static GitHub Pages website."""
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"
BASE = "https://modassarislam37.github.io/funnel-engineering-system-github-ready-v5/"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.meta = {}
        self.title = False
        self.heading1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.heading1 += 1
        if tag in ("a", "link", "script", "img"):
            for k in ("href", "src"):
                if a.get(k):
                    self.refs.append(a[k])
        if tag == "meta":
            key = a.get("name", a.get("property"))
            if key:
                self.meta[key] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.meta["canonical"] = a.get("href", "")

class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "index.html").read_text(encoding="utf-8")
        cls.page = PageParser()
        cls.page.feed(cls.html)

    def test_required_meta(self):
        self.assertEqual(self.page.heading1, 1)
        self.assertEqual(self.page.meta.get("canonical"), BASE)
        self.assertTrue(self.page.meta.get("description"))
        self.assertEqual(self.page.meta.get("og:url"), BASE)
        self.assertIn('"@type": "SoftwareSourceCode"', self.html)

    def test_local_links_and_anchors(self):
        for ref in self.page.refs:
            if ref.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            if ref.startswith("#"):
                self.assertIn(ref[1:], self.page.ids, ref)
                continue
            self.assertTrue((SITE / ref.split("#")[0]).is_file(), ref)

    def test_sitemap_and_robots(self):
        self.assertIn(BASE, (SITE / "sitemap.xml").read_text())
        robots = (SITE / "robots.txt").read_text()
        self.assertIn("Sitemap: " + BASE + "sitemap.xml", robots)

    def test_interactions_are_implemented(self):
        js = (SITE / "assets/site.js").read_text()
        self.assertIn("addEventListener", js)
        self.assertIn("--dry-run", js)
        self.assertIn("clipboard.writeText", js)

if __name__ == "__main__":
    unittest.main()
