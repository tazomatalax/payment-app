#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

import qrcode
from qrcode.image.svg import SvgPathImage


LABELS = {
    "accountName": "Account name",
    "accountNumber": "Account number",
    "reference": "Reference",
    "amount": "Amount",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the hosted payment page and QR assets.")
    parser.add_argument("--config", default="payment-details.json", help="Path to the private payment details JSON file.")
    parser.add_argument("--template", default="index.html", help="Path to the tracked HTML template.")
    parser.add_argument("--output-dir", default="build", help="Directory to write generated files into.")
    parser.add_argument("--page-url", help="Public hosted page URL to encode into payment-page-qr.svg.")
    return parser.parse_args()


def load_details(config_path: Path) -> dict[str, str]:
    details = json.loads(config_path.read_text(encoding="utf-8"))
    required = ["accountName", "accountNumber", "reference"]
    missing = [key for key in required if not str(details.get(key, "")).strip()]
    if missing:
        raise SystemExit(f"Missing required keys in {config_path}: {', '.join(missing)}")
    return {key: str(value).strip() for key, value in details.items()}


def render_rows(details: dict[str, str]) -> str:
    rows = []
    for key in ("accountName", "accountNumber", "reference", "amount"):
        value = details.get(key, "").strip()
        if not value:
            continue
        label = LABELS[key]
        rows.append(
            "      <article class=\"row\">\n"
            "        <div>\n"
            f"          <span class=\"label\">{escape(label)}</span>\n"
            f"          <div class=\"value\">{escape(value)}</div>\n"
            "        </div>\n"
            f"        <button type=\"button\" data-copy-value=\"{escape(value, quote=True)}\" data-copy-label=\"{escape(label, quote=True)}\">Copy</button>\n"
            "      </article>"
        )
    return "\n".join(rows)


def render_plain_text(details: dict[str, str]) -> str:
    lines = [
        "PAYMENT DETAILS",
        "",
        f"Account name: {details['accountName']}",
        f"Account number: {details['accountNumber']}",
        f"Reference: {details['reference']}",
    ]
    if details.get("amount", "").strip():
        lines.append(f"Amount: {details['amount']}")
    lines.extend(["", "Thank you!"])
    return "\n".join(lines) + "\n"


def render_print_sign(page_url: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Payment QR</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: #fff;
      color: #111827;
    }}

    main {{
      width: min(100%, 816px);
      min-height: 100vh;
      margin: 0 auto;
      display: grid;
      place-items: center;
      padding: 32px;
    }}

    .sign {{
      width: 100%;
      max-width: 720px;
      padding: 40px;
      border: 3px solid #111827;
      border-radius: 24px;
      text-align: center;
    }}

    h1 {{
      margin: 0 0 12px;
      font-size: 3rem;
      line-height: 1;
      letter-spacing: -0.05em;
    }}

    p {{
      margin: 0;
      font-size: 1.4rem;
      font-weight: 700;
    }}

    img {{
      display: block;
      width: min(100%, 420px);
      margin: 28px auto;
    }}

    .small {{
      margin-top: 8px;
      font-size: 0.95rem;
      font-weight: 500;
      color: #4b5563;
      overflow-wrap: anywhere;
    }}

    @media print {{
      main {{
        width: auto;
        min-height: auto;
        padding: 0;
      }}

      .sign {{
        max-width: none;
        border-width: 2px;
        border-radius: 0;
        break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="sign">
      <h1>Pay Here</h1>
      <p>Scan. Copy. Pay.</p>
      <img src="payment-page-qr.png" alt="Payment QR code">
      <p class="small">{escape(page_url)}</p>
    </section>
  </main>
</body>
</html>
"""


def make_qr(payload: str) -> qrcode.QRCode:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=16,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr


def write_qr_svg(payload: str, output_path: Path) -> None:
    qr = make_qr(payload)
    image = qr.make_image(image_factory=SvgPathImage)
    output_path.write_text(image.to_string(encoding="unicode"), encoding="utf-8")


def write_qr_png(payload: str, output_path: Path) -> None:
    qr = make_qr(payload)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(output_path)


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    config_path = (root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    template_path = (root / args.template).resolve() if not Path(args.template).is_absolute() else Path(args.template)
    output_dir = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)

    details = load_details(config_path)
    template = template_path.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    html = template.replace("__DETAIL_ROWS__", render_rows(details))
    plain_text = render_plain_text(details)

    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "plain-text-qr-payload.txt").write_text(plain_text, encoding="utf-8")
    write_qr_svg(plain_text.strip(), output_dir / "plain-text-qr.svg")
    write_qr_png(plain_text.strip(), output_dir / "plain-text-qr.png")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Wrote {output_dir / 'index.html'}")
    print(f"Wrote {output_dir / 'plain-text-qr-payload.txt'}")
    print(f"Wrote {output_dir / 'plain-text-qr.svg'}")
    print(f"Wrote {output_dir / 'plain-text-qr.png'}")

    if args.page_url:
        page_url = args.page_url.strip()
        (output_dir / "payment-page-url.txt").write_text(page_url + "\n", encoding="utf-8")
        write_qr_svg(page_url, output_dir / "payment-page-qr.svg")
        write_qr_png(page_url, output_dir / "payment-page-qr.png")
        (output_dir / "payment-page-print.html").write_text(render_print_sign(page_url), encoding="utf-8")
        print(f"Wrote {output_dir / 'payment-page-url.txt'}")
        print(f"Wrote {output_dir / 'payment-page-qr.svg'}")
        print(f"Wrote {output_dir / 'payment-page-qr.png'}")
        print(f"Wrote {output_dir / 'payment-page-print.html'}")


if __name__ == "__main__":
    main()
