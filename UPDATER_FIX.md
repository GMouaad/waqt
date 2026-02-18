# Fix for Windows Update File Access Error

## Problem
Users encountered the following error when running `waqt update` on Windows:
```
[WinError 32] The process cannot access the file because it is being used by another process
```

This error occurred because Windows locks executable files while they are running, preventing in-place updates.

## Solution

### 1. Retry Logic with Exponential Backoff
Added `_retry_file_operation()` function that:
- Attempts file operations up to 5 times by default
- Uses exponential backoff (0.1s, 0.2s, 0.4s, 0.8s, 1.6s)
- Catches `OSError` and `PermissionError`
- Provides clear error messages when retries are exhausted

### 2. Windows-Specific Update Strategy
On Windows, the update process now:
1. Downloads and extracts the new version to a temporary directory
2. Creates a backup of the current executable
3. Generates a batch script (`waqt_update.bat`) that:
   - Waits 2 seconds for the current process to exit
   - Replaces the executable with the new version
   - Falls back to the backup if replacement fails
   - Self-deletes after completion
4. Launches the batch script in a detached process
5. Informs the user to close the program to complete the update

### 3. Unix Systems
On Unix systems (Linux, macOS), the update applies immediately with retry logic since these systems allow replacing running executables.

## Testing

### Unit Tests
Added comprehensive tests in `tests/test_updater.py`:
- `TestRetryLogic`: Tests for retry behavior with various scenarios
- `TestWindowsUpdateScript`: Tests for Windows batch script generation

### Manual Testing
To manually test the fix on Windows:
1. Build a frozen executable using the instructions from README.md (typically involves PyInstaller with appropriate flags)
2. Run the executable: `dist/waqt.exe`
3. Attempt an update: `dist/waqt.exe update check`
4. If an update is available: `dist/waqt.exe update install`
5. Verify that:
   - The update prepares successfully
   - A batch script is created
   - The script launches in a separate window
   - Closing the main program triggers the update
   - The new version is installed correctly

## User Experience

### Before Fix
```
❌ Error during update: [WinError 32] The process cannot access the file...
```

### After Fix (Windows)
```
✓ Update prepared for version 0.2.0

The update will be applied when you close this program.
Launching update script...

Please close this window to complete the update.
```

### After Fix (Unix)
```
Installing update...
✓ Successfully updated to version 0.2.0
```

## Technical Details

### Retry Parameters
- `max_retries`: 5 attempts
- `initial_delay`: 0.1 seconds
- Backoff multiplier: 2x (exponential)
- Total max wait time: ~3.1 seconds

### Windows Batch Script
The generated script (`waqt_update.bat`) includes:
- 2-second delay to ensure process exit
- Error handling with backup restoration
- Silent operation (output redirected to nul)
- Automatic cleanup on success

### Security Considerations
- Backup file is created before any modification
- Failed updates automatically restore the backup
- The batch script validates file operations before cleanup
- Uses standard Windows commands (no external tools required)

## Future Improvements
- Add progress indication during retry attempts
- Optionally keep the batch script for debugging
- Add logging of update operations
- Consider using Windows Restart Manager API for more robust updates
