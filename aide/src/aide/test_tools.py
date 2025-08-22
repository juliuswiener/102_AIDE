import unittest
from unittest.mock import patch
import os
import json
from .tools import command_runner_tool, CONFIG_FILE, SESSION_APPROVALS

class TestCommandRunner(unittest.TestCase):

    def setUp(self):
        # Ensure a clean state before each test
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        SESSION_APPROVALS.clear()

    def tearDown(self):
        # Clean up after each test
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        SESSION_APPROVALS.clear()

    @patch('builtins.input', return_value='y')
    def test_approve_once(self, mock_input):
        """Test one-time approval with 'y'."""
        command = 'echo "hello"'
        result = command_runner_tool.invoke({"command": command})
        self.assertIn("hello", result)
        # Ensure it's not saved to the config
        self.assertFalse(os.path.exists(CONFIG_FILE))
        # Ensure it's not in session approvals
        self.assertNotIn(command, SESSION_APPROVALS)

    @patch('builtins.input', return_value='session')
    def test_approve_session(self, mock_input):
        """Test session-level approval."""
        command = 'echo "session test"'
        # First run, requires approval
        result1 = command_runner_tool.invoke({"command": command})
        self.assertIn("session test", result1)
        self.assertIn(command, SESSION_APPROVALS)
        
        # Second run, should not require approval
        result2 = command_runner_tool.invoke({"command": command})
        self.assertIn("session test", result2)
        # Ensure mock_input was only called once
        mock_input.assert_called_once()

    @patch('builtins.input', return_value='always')
    def test_approve_always(self, mock_input):
        """Test permanent ('always') approval."""
        command = 'echo "always test"'
        # First run, requires approval
        result1 = command_runner_tool.invoke({"command": command})
        self.assertIn("always test", result1)
        
        # Check that the config file was written
        self.assertTrue(os.path.exists(CONFIG_FILE))
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        self.assertEqual(config["approved_commands"][command], "always")

        # Second run, should not require approval
        result2 = command_runner_tool.invoke({"command": command})
        self.assertIn("always test", result2)
        mock_input.assert_called_once()

    @patch('builtins.input', return_value='n')
    def test_deny_execution(self, mock_input):
        """Test denying command execution."""
        command = 'echo "denied"'
        result = command_runner_tool.invoke({"command": command})
        self.assertEqual(result, "Command execution denied by user.")

    def test_pre_approved_command(self):
        """Test running a command that is already approved in the config."""
        command = 'echo "pre-approved"'
        config = {"approved_commands": {command: "always"}}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
            
        # Should not require input
        with patch('builtins.input') as mock_input:
            result = command_runner_tool.invoke({"command": command})
            self.assertIn("pre-approved", result)
            mock_input.assert_not_called()

if __name__ == '__main__':
    unittest.main()
