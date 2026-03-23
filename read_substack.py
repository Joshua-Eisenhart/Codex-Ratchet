import urllib.request
from html.parser import HTMLParser
import ssl

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_p = False

    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'h1', 'h2', 'h3', 'li', 'span', 'blockquote']:
            self.in_p = True

    def handle_endtag(self, tag):
        if tag in ['p', 'h1', 'h2', 'h3', 'li', 'span', 'blockquote']:
            self.in_p = False
            self.text.append("\n")

    def handle_data(self, data):
        if self.in_p:
            d = data.strip()
            if d:
                self.text.append(d)

url = "https://substack.com/home/post/p-189067354"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
    # Substack puts the main content inside a JSON blob or raw HTML.
    parser = MyHTMLParser()
    parser.feed(html)
    
    with open("substack_extracted.txt", "w") as f:
        f.write(" ".join(parser.text))
    print("Success")
except Exception as e:
    print(f"Error: {e}")
