import os
import pytest
from unittest.mock import MagicMock
from omniagent.ui.slash_commands import handle_slash_command
from omniagent.core.state import state

@pytest.fixture
def mock_console():
    console = MagicMock()
    return console

@pytest.fixture
def mock_session():
    session = MagicMock()
    return session

@pytest.fixture
def mock_cli_module():
    return MagicMock()

def test_handle_slash_command_about(mock_console, mock_session, mock_cli_module):
    handled = handle_slash_command("/about", ["/about"], mock_console, mock_session, mock_cli_module)
    assert handled is True
    mock_console.print.assert_any_call("[dim]Inspired by the Gemini CLI. Powered by CrewAI & Ollama.[/dim]")

def test_handle_slash_command_vim_toggle(mock_console, mock_session, mock_cli_module):
    initial_mode = state.vim_mode
    handled = handle_slash_command("/vim", ["/vim"], mock_console, mock_session, mock_cli_module)
    assert handled is True
    assert state.vim_mode != initial_mode

def test_handle_slash_command_init_workspace(tmp_path, mock_console, mock_session, mock_cli_module):
    # Temporarily change directory to tmp_path to test workspace init safely
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        handled = handle_slash_command("/init", ["/init"], mock_console, mock_session, mock_cli_module)
        assert handled is True
        
        workspace_dir = os.path.join(tmp_path, ".omniagent")
        session_file = os.path.join(workspace_dir, "session.json")
        
        assert os.path.exists(workspace_dir)
        assert os.path.exists(session_file)
    finally:
        os.chdir(original_dir)

def test_handle_slash_command_cd(tmp_path, mock_console, mock_session, mock_cli_module):
    original_dir = os.getcwd()
    
    try:
        handled = handle_slash_command("/cd", ["/cd", str(tmp_path)], mock_console, mock_session, mock_cli_module)
        assert handled is True
        assert os.getcwd() == str(tmp_path)
    finally:
        os.chdir(original_dir)

def test_handle_slash_command_unknown(mock_console, mock_session, mock_cli_module):
    handled = handle_slash_command("/unknown_command_fake", ["/unknown_command_fake"], mock_console, mock_session, mock_cli_module)
    assert handled is False
