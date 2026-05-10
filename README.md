# Garage sale payment QR options

This workspace contains both recommended QR-code options:

1. `index.html` — a tiny single-file payment page for an `https://` URL QR code.
2. `plain-text-qr-payload.txt` — a backup plain-text QR payload for no-hosting/offline use.

It also includes an experimental third option:

3. `embedded-html-data-url.txt` and `embedded-html-qr.svg` — a `data:text/html` page embedded directly in a QR code so you can test whether your scanners open it.

## Option 1: HTTPS payment page

Edit the `defaultPaymentDetails` object near the bottom of `index.html`:

- `accountName`
- `accountNumber`
- `reference`
- `amount` — leave blank if buyers choose the amount.
- `smsNumber` — leave blank to hide the SMS button.

Host `index.html` somewhere that gives you a normal `https://` URL, then put that URL in your QR code. Good low-friction hosting choices include GitHub Pages, Netlify, Cloudflare Pages, or any static web host.

You can also override the details from the URL query string without editing the file again:

```text
https://example.com/payment/?name=YOUR%20ACCOUNT%20NAME&account=12-3456-7890123-00&ref=GARAGE%20SALE&amount=%245&sms=%2B64000000000
```

Supported query parameters:

- `name` or `accountName`
- `account` or `accountNumber`
- `ref` or `reference`
- `amount`
- `sms`, `smsNumber`, or `phone`

## Option 2: plain-text QR backup

Edit `plain-text-qr-payload.txt`, then encode that exact text into a plain-text QR code. This is less polished than a webpage, but it is highly interoperable because scanners can display it as readable text.

Keep the payload short. Dense QR codes are harder to scan from printed signs, especially in bright light or from a distance.

## Option 3: embedded HTML QR experiment

This is included only so you can test it:

- `embedded-html-source.html` — readable tiny payment page.
- `embedded-html-data-url.txt` — the full one-line `data:text/html` URL payload.
- `embedded-html-qr.svg` — a QR SVG generated from that payload.
- `tools/make_embedded_html_qr.py` — no-dependency generator used to rebuild the SVG.

To test it, open `embedded-html-qr.svg` and scan it with several phone QR scanners. Expect mixed results: some scanners may open the embedded page, while others may show text, search the payload, or refuse to open a `data:` URL.

If you edit `embedded-html-source.html`, rebuild the payload and QR with:

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import quote
html = Path('embedded-html-source.html').read_text(encoding='utf-8').strip()
Path('embedded-html-data-url.txt').write_text('data:text/html;charset=utf-8,' + quote(html, safe='') + '\n', encoding='utf-8')
PY
python3 tools/make_embedded_html_qr.py
```

## Free temporary hosting path: GitHub Pages

GitHub Pages is probably the easiest free option for this because this project is just static files.

1. Create a new GitHub repository, for example `garage-sale-payment`.
2. Upload or push these files to the repository.
3. In GitHub, open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select branch `main` and folder `/root`, then save.
6. Wait for GitHub Pages to publish the site.
7. Your payment page URL will usually look like:

```text
https://YOUR-GITHUB-USERNAME.github.io/garage-sale-payment/
```

Put that HTTPS URL into your main QR code. If you later edit `index.html`, the URL stays the same.

For a more temporary-feeling flow, make the repository private while editing, publish when ready, then disable Pages or delete the repository after the sale.

## Local preview

Open `index.html` directly in a browser, or serve the folder with any static server. No install step is required.
