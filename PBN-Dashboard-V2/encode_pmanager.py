import base64

src_file = "g:/ProjectDemo/manage-pbn-sites/mu-plugins/pbn-manager.src.php"
with open(src_file, "r", encoding="utf-8") as f:
    src = f.read().strip()

# Strip <?php tag because PHP eval() expects raw code without open tag
if src.startswith("<?php"):
    src = src[5:].strip()

b64 = base64.b64encode(src.encode("utf-8")).decode("ascii")
chunks = [b64[i:i+100] for i in range(0, len(b64), 100)]
chunked_str = "\n".join(chunks)

content = f"""<?php
/**
 * Plugin Name: Site Performance & Core Manager
 * Version: 2.2.0
 * Author: Platform Core Engine
 */

if (!defined('ABSPATH')) {{
    exit;
}}

// Security & Integrity Layer - Encoded Core
$c = '{chunked_str}';

eval(base64_decode($c));
"""

targets = [
    "g:/ProjectDemo/manage-pbn-sites/PBN-Dashboard-V2/p-manager.php",
    "g:/ProjectDemo/manage-pbn-sites/PBN-Dashboard-V2/VPS-client/p-manager.php",
    "g:/ProjectDemo/manage-pbn-sites/mu-plugins/pbn-manager.php",
    "g:/ProjectDemo/manage-pbn-sites/mu-plugins/p-manager.php"
]

for t in targets:
    with open(t, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {t}")

print("Done encoding p-manager.php safely!")
