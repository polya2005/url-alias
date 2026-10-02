#!./.venv/bin/python3.14

from argparse import ArgumentParser
from string import Template
import json
import yaml
from jsonschema import validate, ValidationError

# Web-related declarations
html_template = Template(
    r'<!DOCTYPE html><html lang="en"><head><style>:root{background-color: #0a0a0a;color: #f5f5f5;font-family: Arial, sans-serif;}</style><meta charset="UTF-8" http-equiv="refresh" content="0;url=$url"/><title>$alias</title></head><body>Click <a href="$url" style="color: #22d3de; text-decoration: none;">here</a> to be redirected.</body></html>'
)

BASE_URL = "polya2005.github.io/url-alias/"


def main():
    # Argument parsing
    parser = ArgumentParser(description="Generate HTML files for URL aliases.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output."
    )
    parser.add_argument(
        "--aliases",
        type=str,
        default="aliases.yaml",
        help="Path to the aliases YAML file.",
    )
    parser.add_argument(
        "--no-qr",
        action="store_true",
        help="Do not generate QR code images for the aliases, even if specified in the YAML file.",
    )
    parser.add_argument(
        "--qr-dir", type=str, default="qr", help="Directory to save QR code images."
    )
    parser.add_argument(
        "--remove-outdated",
        action="store_true",
        help="Remove outdated HTML and QR code files.",
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean outdated files without generating new ones. Implies --remove-outdated.",
    )
    args = parser.parse_args()
    if args.verbose:

        def log(*args, **kwargs):
            print(*args, **kwargs)

    else:

        def log(*args, **kwargs):
            pass

    with open(args.aliases, "r") as f:
        aliases = yaml.safe_load(f)

    log(f"Loaded {len(aliases)} aliases from {args.aliases}")

    with open("aliases_schema.json", "r") as f:
        schema = json.load(f)

    log(f"Loaded schema from aliases_schema.json")
    try:
        validate(instance=aliases, schema=schema)
    except ValidationError as e:
        # Print the error message and exit, regardless of verbosity
        print(f"Validation error: {e.message}")
        exit(1)

    log("Validation successful.")

    if not args.clean_only:
        if args.no_qr:
            log("QR code generation is disabled.")

            def generate_qr_code(alias):
                pass

        else:
            import qrcode
            import os

            def generate_qr_code(alias):
                qr = qrcode.QRCode(
                    version=2,
                    error_correction=qrcode.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(f"{BASE_URL}{alias}.html")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                os.makedirs(args.qr_dir, exist_ok=True)
                img_path = os.path.join(args.qr_dir, f"{alias}.png")
                with open(img_path, "wb") as f:
                    img.save(f)
                log(f"Generated QR code for {alias} at {img_path}")

        for record in aliases:
            alias = record["alias"]
            url = record["url"]
            html_content = html_template.safe_substitute({"url": url})
            with open(f"{alias}.html", "w") as f:
                f.write(html_content)
            log(f"Generated {alias}.html for URL: {url}")
            if record["qr"]:
                generate_qr_code(alias)
    if args.remove_outdated or args.clean_only:
        import os
        import glob

        # Remove outdated HTML files
        for html_file in glob.glob("*.html"):
            alias_name = os.path.splitext(html_file)[0]
            if not any(record["alias"] == alias_name for record in aliases):
                os.remove(html_file)
                log(f"Removed outdated HTML file: {html_file}")

        # Remove outdated QR code images
        if not args.no_qr:
            for qr_file in glob.glob(f"{args.qr_dir}/*.png"):
                alias_name = os.path.basename(qr_file).replace(".png", "")
                if not any(record["alias"] == alias_name for record in aliases):
                    os.remove(qr_file)
                    log(f"Removed outdated QR code image: {qr_file}")


if __name__ == "__main__":
    main()
