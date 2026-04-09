# Changelog

All notable changes to Focus Recorder will be documented in this file.

## [0.1.0] - 2026-04-09

### Added
- Initial release
- Screen recording with focus tracking
- Dynamic zoom following cursor
- Mouse click detection and highlighting
- Configurable zoom level and smoothness
- Adjustable FPS (24-60)
- Export modes:
  - Full screen (16:9)
  - TikTok vertical (9:16)
  - Both formats simultaneously
- Cross-platform support (Windows, Linux, macOS)
- PyQt6 GUI interface
- Real-time recording status
- Progress bar for video rendering

### Features
- Smart camera movement following cursor
- Automatic video directory creation
- Timestamp-based file naming
- FFmpeg integration for video encoding
- Platform-specific optimizations:
  - DXCam for Windows (faster capture)
  - MSS for Linux/macOS (universal fallback)
