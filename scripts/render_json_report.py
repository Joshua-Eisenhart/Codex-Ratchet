
import json
import argparse
import os

def json_to_html(data):
    """
    Recursively converts a JSON object to an HTML string.
    """
    if isinstance(data, dict):
        html = "<table>"
        for key, value in data.items():
            html += f"<tr><td><strong>{key}</strong></td><td>{json_to_html(value)}</td></tr>"
        html += "</table>"
        return html
    elif isinstance(data, list):
        html = "<ul>"
        for item in data:
            html += f"<li>{json_to_html(item)}</li>"
        html += "</ul>"
        return html
    else:
        return str(data)

def main():
    """
    Main function to parse arguments and generate the HTML report.
    """
    parser = argparse.ArgumentParser(description="Convert a JSON file to an HTML report.")
    parser.add_argument("json_file", help="Path to the JSON file.")
    args = parser.parse_args()

    if not os.path.exists(args.json_file):
        print(f"Error: File not found at {args.json_file}")
        return

    with open(args.json_file, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {args.json_file}")
            return

    html_content = f"""
    <html>
    <head>
        <title>JSON Report</title>
        <style>
            body {{ font-family: sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            td, th {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            ul {{ list-style-type: none; padding-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>JSON Report</h1>
        {json_to_html(data)}
    </body>
    </html>
    """

    html_file_path = os.path.splitext(args.json_file)[0] + ".html"
    with open(html_file_path, 'w') as f:
        f.write(html_content)

    print(f"Successfully generated HTML report at {html_file_path}")

if __name__ == "__main__":
    main()
