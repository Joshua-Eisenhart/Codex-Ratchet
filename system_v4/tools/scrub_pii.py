import subprocess
import os

target = "/Users/joshuaeisenhart"
replacement = "/home/ratchet"

out = subprocess.check_output(["git", "ls-files"]).decode('utf-8')
files = out.strip().split("\n")

count = 0
for f in files:
    if os.path.exists(f) and os.path.isfile(f):
        try:
            with open(f, "r", encoding="utf-8") as file:
                content = file.read()
            if target in content:
                content = content.replace(target, replacement)
                with open(f, "w", encoding="utf-8") as file:
                    file.write(content)
                count += 1
        except Exception:
            pass # ignore binaries or non-utf8
            
print(f"Scrubbed {count} tracked files for PII targeting {target} -> {replacement}")
