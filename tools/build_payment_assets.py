#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

from qr_svg import make_svg


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
    (output_dir / "plain-text-qr.svg").write_text(make_svg(plain_text.strip(), label="Plain text payment QR code"), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Wrote {output_dir / 'index.html'}")
    print(f"Wrote {output_dir / 'plain-text-qr-payload.txt'}")
    print(f"Wrote {output_dir / 'plain-text-qr.svg'}")

    if args.page_url:
        page_url = args.page_url.strip()
        (output_dir / "payment-page-url.txt").write_text(page_url + "\n", encoding="utf-8")
        (output_dir / "payment-page-qr.svg").write_text(make_svg(page_url, label="Hosted payment page QR code"), encoding="utf-8")
        print(f"Wrote {output_dir / 'payment-page-url.txt'}")
        print(f"Wrote {output_dir / 'payment-page-qr.svg'}")


if __name__ == "__main__":
    main()
