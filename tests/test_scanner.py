from paper2agent.modules.scanner import CodeScanner
import os

scanner = CodeScanner()
test_dir = "legacy_archive/templates"
results = scanner.scan(test_dir)

print(f"Scanned {test_dir}")
print(f"Found {len(results)} files.")
for res in results:
    print(f"- {res['path']} ({res['type']})")

if len(results) > 0:
    print("Scanner Test: SUCCESS")
else:
    print("Scanner Test: FAILURE")
