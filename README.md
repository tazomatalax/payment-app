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
- `tools/qr_svg.py` - no-dependency QR generator used by the build script.

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

```bash
python3 tools/build_payment_assets.py --config payment-details.json
```

That generates:

- `build/index.html`
- `build/plain-text-qr-payload.txt`
- `build/plain-text-qr.svg`

If you also know the final hosted page URL, add it to generate a QR for the hosted page itself:

```bash
python3 tools/build_payment_assets.py --config payment-details.json --page-url https://YOUR-USERNAME.github.io/YOUR-PAGES-REPO/
```

That also generates:

- `build/payment-page-url.txt`
- `build/payment-page-qr.svg`

## GitHub Pages

This repo is intended to be published from branch `main` and folder `/root`.

Your Pages URL will be:

```text
https://YOUR-USERNAME.github.io/payment-app/
```

## Preview

After running the build step, open `build/index.html` in a browser.
