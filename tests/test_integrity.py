import unittest
from paper2agent.agents.integrity import IntegrityAgent

class MockSynthesizer:
    def fix(self, code, critique):
        return "# Fixed Code"

class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.agent = IntegrityAgent(MockSynthesizer())
    
    def test_static_check_unsafe_import(self):
        unsafe_code = "import os\nos.system('rm -rf /')"
        self.assertFalse(self.agent.static_check(unsafe_code), "Should reject os.system")
        
    def test_static_check_safe_code(self):
        safe_code = "def add(a, b): return a + b"
        self.assertTrue(self.agent.static_check(safe_code), "Should accept safe code")

if __name__ == '__main__':
    unittest.main()
