from paper2agent.agents.integrity import IntegrityAgent
from paper2agent.agents.synthesizer import SkillSynthesizer # Assuming this exists or I'll mock it
from unittest.mock import MagicMock

def test_static_check():
    # Mock synthesizer as we just want to test static_check
    synthesizer = MagicMock()
    agent = IntegrityAgent(synthesizer)

    unsafe_codes = [
        "import os\nos.system('ls')",
        "import subprocess",
        "import sys",
        "import shutil",
        "from shutil import rmtree",
        "rmtree('/tmp')",
        "x = '/absolute/path'", 
        "y = \"/another/one\""
    ]

    safe_codes = [
        "print('Hello World')",
        "x = 1 + 1",
        "path = 'relative/path'",
        "import math",
        "import json"
    ]

    print("Testing Unsafe Pattern Detection:")
    for code in unsafe_codes:
        is_safe = agent.static_check(code)
        print(f"Code: {code.strip()} -> Safe: {is_safe}")

    print("\nTesting Safe Pattern Detection:")
    for code in safe_codes:
        is_safe = agent.static_check(code)
        print(f"Code: {code.strip()} -> Safe: {is_safe}")

if __name__ == "__main__":
    test_static_check()
