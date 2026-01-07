"""Tests for __main__ entry point module."""

import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO


def test_main_no_args_starts_web_app():
    """Test that running without arguments starts the web application."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv to simulate no arguments
    with patch.object(sys, 'argv', ['waqtracker']):
        # Mock create_app and its run method
        with patch('waqtracker.__main__.create_app') as mock_create_app:
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            
            # Mock stdout to capture print statements
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Call main and expect it to try to run the app
                main()
                
                # Verify create_app was called
                mock_create_app.assert_called_once()
                
                # Verify app.run was called with correct parameters
                mock_app.run.assert_called_once()
                call_kwargs = mock_app.run.call_args.kwargs
                assert call_kwargs['host'] == '127.0.0.1'
                assert call_kwargs['port'] == 5000
                assert call_kwargs['debug'] is False  # Default when FLASK_DEBUG not set
                
                # Verify startup message was printed
                output = mock_stdout.getvalue()
                assert "Starting waqtracker web application" in output
                assert "http://localhost:5000" in output


def test_main_with_args_runs_cli():
    """Test that running with arguments invokes the CLI."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv to simulate CLI arguments
    with patch.object(sys, 'argv', ['waqtracker', '--version']):
        # Mock the cli function
        with patch('waqtracker.__main__.cli') as mock_cli:
            # Call main
            main()
            
            # Verify cli was called
            mock_cli.assert_called_once()


def test_main_help_message_frozen_mode():
    """Test that help message shows correct CLI name in frozen mode."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv and sys.frozen
    with patch.object(sys, 'argv', ['waqtracker']):
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, 'executable', '/path/to/waqtracker'):
                # Mock create_app and its run method
                with patch('waqtracker.__main__.create_app') as mock_create_app:
                    mock_app = MagicMock()
                    mock_create_app.return_value = mock_app
                    
                    # Mock stdout to capture print statements
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        main()
                        
                        # Verify message shows executable name, not "waqt"
                        output = mock_stdout.getvalue()
                        assert "waqtracker <command>" in output


def test_main_help_message_package_mode():
    """Test that help message shows 'waqt' in package mode."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv (single element = no args, package mode)
    with patch.object(sys, 'argv', ['waqtracker']):
        # Mock frozen attribute as not existing (package mode)
        with patch.object(sys, 'frozen', False, create=True):
            with patch('waqtracker.__main__.create_app') as mock_create_app:
                mock_app = MagicMock()
                mock_create_app.return_value = mock_app
                
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    main()
                    
                    output = mock_stdout.getvalue()
                    assert "waqt <command>" in output


def test_main_error_handling():
    """Test that errors during app creation are handled gracefully."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv to simulate no arguments
    with patch.object(sys, 'argv', ['waqtracker']):
        # Mock create_app to raise an exception
        with patch('waqtracker.__main__.create_app') as mock_create_app:
            mock_create_app.side_effect = Exception("Database connection failed")
            
            # Mock stderr and stdout
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with patch('sys.stdout', new_callable=StringIO):
                    # Expect sys.exit to be called
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    # Verify exit code is 1
                    assert exc_info.value.code == 1
                    
                    # Verify error message was printed to stderr
                    error_output = mock_stderr.getvalue()
                    assert "Error starting application" in error_output
                    assert "Database connection failed" in error_output


def test_main_debug_mode_from_env():
    """Test that debug mode is enabled when FLASK_DEBUG is set."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv
    with patch.object(sys, 'argv', ['waqtracker']):
        # Mock environment variable
        with patch.dict('os.environ', {'FLASK_DEBUG': 'true'}):
            # Mock create_app
            with patch('waqtracker.__main__.create_app') as mock_create_app:
                mock_app = MagicMock()
                mock_create_app.return_value = mock_app
                
                with patch('sys.stdout', new_callable=StringIO):
                    main()
                    
                    # Verify app.run was called with debug=True
                    call_kwargs = mock_app.run.call_args.kwargs
                    assert call_kwargs['debug'] is True


def test_main_host_binding():
    """Test that Flask binds to localhost only for security."""
    from waqtracker.__main__ import main
    
    # Mock sys.argv
    with patch.object(sys, 'argv', ['waqtracker']):
        # Mock create_app
        with patch('waqtracker.__main__.create_app') as mock_create_app:
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            
            with patch('sys.stdout', new_callable=StringIO):
                main()
                
                # Verify app.run was called with host='127.0.0.1' (not 0.0.0.0)
                call_kwargs = mock_app.run.call_args.kwargs
                assert call_kwargs['host'] == '127.0.0.1'
                assert call_kwargs['host'] != '0.0.0.0'
