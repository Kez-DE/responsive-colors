"""Check rendered breakpoints with Chrome; run: python3 test-responsive.py."""
import html
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE = (ROOT / "index.html").read_text()

with tempfile.TemporaryDirectory() as temporary:
    for width in (375, 771, 772, 997, 998, 1440):
        columns = 3 if width >= 998 else 2 if width >= 772 else 1
        script = f"""
        <script>
        addEventListener('load', () => {{
          const cards = [...document.querySelectorAll('main > div')];
          const images = [...document.images];
          const boxes = cards.map(card => card.getBoundingClientRect());
          const columns = boxes.filter(box => Math.abs(box.top - boxes[0].top) < 1).length;
          const expectedWidth = innerWidth * ({columns} === 3 ? .30 : .45);
          const checks = [
            innerWidth === {width}, cards.length === 9, columns === {columns},
            images.every(image => image.complete && image.naturalWidth > 0),
            document.documentElement.scrollWidth <= innerWidth,
            innerWidth < 772 || boxes.every(box => Math.abs(box.width - expectedWidth) < 1),
            innerWidth < 772 || images.every(image => image.getBoundingClientRect().height <= innerHeight * .30 + 1)
          ];
          parent.document.body.insertAdjacentHTML('beforeend', '<pre>' + (checks.every(Boolean) ? 'PASS' : 'FAIL ' + checks) + '</pre>');
        }});
        </script>"""
        page = Path(temporary) / "check.html"
        content = PAGE.replace("<head>", f'<head><base href="{ROOT.as_uri()}/">') + script
        page.write_text(f'<iframe style="border:0;width:{width}px;height:900px" srcdoc="{html.escape(content, quote=True)}"></iframe>')
        result = subprocess.run([
            CHROME, "--headless", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={temporary}/chrome", "--window-size=1600,1000",
            "--virtual-time-budget=3000", "--dump-dom", page.as_uri()
        ], capture_output=True, text=True, check=True, timeout=30)
        assert "<pre>PASS</pre>" in result.stdout, html.unescape(result.stdout)
        print(f"PASS: {width}px, {columns} column(s), images loaded, no horizontal overflow")
