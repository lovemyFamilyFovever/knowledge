# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"E:/GitHub/knowledge")
from app.app import create_app

app = create_app()
c = app.test_client()
r = c.get("/", follow_redirects=True)
html = r.get_data(as_text=True)
print("status:", r.status_code)
print("has dom-caret:", "dom-caret" in html)
print("has data-dom:", "data-dom=" in html)
print("count 'class=\"dom-caret\"':", html.count('class="dom-caret"'))
print("count 'data-dom=':", html.count("data-dom="))
print("has .subs css class usage:", 'class="subs"' in html)
print("final url path contains /browse/:", "/browse/" in r.request.path)
