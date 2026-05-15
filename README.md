# Payment Page

This repo now focuses on two things only:

1. A simple hosted payment page with copy buttons.
2. A plain-text backup QR code.

The old embedded-HTML QR experiment has been removed.

## Public repo model

This repo is set up to be published directly from the `main` branch with GitHub Pages.

Important: if you put real payment details in this repo and push them, those details are public in both the live page and the git history.

## Files that matter

- `index.html` - tracked template for the hosted page.
- `payment-details.json` - tracked payment details used for the live site build.
- `payment-details.example.json` - example config file.
- `tools/build_payment_assets.py` - builds the hosted page and QR files into `build/`.
- `requirements.txt` - Python packages for reliable QR generation and local QR verification.

## Local setup

Edit `payment-details.json` with your values:

```json
{
  "accountName": "YOUR ACCOUNT NAME",
  "accountNumber": "12-3456-7890123-00",
  "reference": "GARAGE SALE",
  "amount": ""
}
```

`amount` can be left blank if buyers choose the amount themselves.

When you push changes to `payment-details.json` on `main`, the live page updates automatically because `index.html` reads that file directly.

## Build locally

Install the QR tooling once:

```bash
python3 -m pip install -r requirements.txt
```

```bash
python3 tools/build_payment_assets.py --config payment-details.json
```

That generates:

- `build/index.html`
- `build/plain-text-qr-payload.txt`
- `build/plain-text-qr.svg`
- `build/plain-text-qr.png`

If you also know the final hosted page URL, add it to generate a QR for the hosted page itself:

```bash
python3 tools/build_payment_assets.py --config payment-details.json --page-url https://YOUR-USERNAME.github.io/YOUR-PAGES-REPO/
```

That also generates:

- `build/payment-page-url.txt`
- `build/payment-page-qr.svg`
- `build/payment-page-qr.png`
- `build/payment-page-print.html`

## GitHub Pages

This repo is intended to be published from branch `main` and folder `/root`.

Your Pages URL will be:

```text
https://YOUR-USERNAME.github.io/payment-app/
```

## Preview

After running the build step, open `build/index.html` in a browser.

## Update the live page

To replace the placeholder values with your real details and publish them live:

1. Edit `payment-details.json`.
2. Put in your real `accountName`, `accountNumber`, `reference`, and optional `amount`.
3. Save the file.
4. Commit and push it:

```bash
git add payment-details.json
git commit -m "Update payment details"
git push origin main
```

5. Wait about a minute, then open:

```text
https://tazomatalax.github.io/payment-app/
```

If you want fresh printable QR files for the same live page, run:

```bash
python3 -m pip install -r requirements.txt
python3 tools/build_payment_assets.py --config payment-details.json --page-url https://tazomatalax.github.io/payment-app/
```

Then print:

- `build/payment-page-print.html`
