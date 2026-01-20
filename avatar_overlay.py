#!/usr/bin/env python3
"""
Avatar Overlay - Visual coding agent companion
A transparent, always-on-top overlay that shows an animated character
responding to file system and log activity.
"""

import sys
import os
import re
import time
import argparse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum, auto

from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QObject
from PySide6.QtGui import QMovie, QMouseEvent, QAction, QKeyEvent

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


# =============================================================================
# State Machine
# =============================================================================

class State(Enum):
    """Avatar states in priority order (higher value = higher priority)."""
    IDLE = 0
    THINKING = 1
    TYPING = 2
    RUNNING = 3
    SUCCESS = 4
    ERROR = 5


@dataclass
class StateTimestamps:
    """Tracks the last occurrence time of each state trigger."""
    last_fs_activity: float = 0.0
    last_log_activity: float = 0.0
    last_running: float = 0.0
    last_success: float = 0.0
    last_error: float = 0.0


@dataclass
class StateConfig:
    """Configuration for state timing thresholds."""
    error_duration: float = 6.0
    success_duration: float = 4.0
    running_duration: float = 3.0
    typing_threshold: float = 1.2
    thinking_threshold: float = 8.0


class StateResolver:
    """Resolves the current state based on timestamps and thresholds."""
    
    def __init__(self, config: Optional[StateConfig] = None):
        self.config = config or StateConfig()
        self.timestamps = StateTimestamps()
    
    def resolve(self) -> State:
        """Determine the current state based on timestamps."""
        now = time.time()
        cfg = self.config
        ts = self.timestamps
        
        # Priority order: error > success > running > typing > thinking > idle
        if now - ts.last_error < cfg.error_duration:
            return State.ERROR
        if now - ts.last_success < cfg.success_duration:
            return State.SUCCESS
        if now - ts.last_running < cfg.running_duration:
            return State.RUNNING
        if now - ts.last_fs_activity < cfg.typing_threshold:
            return State.TYPING
        
        last_activity = max(ts.last_fs_activity, ts.last_log_activity)
        if now - last_activity < cfg.thinking_threshold:
            return State.THINKING
        
        return State.IDLE
    
    def on_fs_activity(self):
        """Called when file system activity is detected."""
        self.timestamps.last_fs_activity = time.time()
    
    def on_log_activity(self):
        """Called when log activity is detected."""
        self.timestamps.last_log_activity = time.time()
    
    def on_running(self):
        """Called when 'running' pattern is detected in log."""
        self.timestamps.last_running = time.time()
        self.on_log_activity()
    
    def on_success(self):
        """Called when 'success' pattern is detected in log."""
        self.timestamps.last_success = time.time()
        self.on_log_activity()
    
    def on_error(self):
        """Called when 'error' pattern is detected in log."""
        self.timestamps.last_error = time.time()
        self.on_log_activity()


# =============================================================================
# File System Watcher
# =============================================================================

class FSEventSignaler(QObject):
    """Qt signal emitter for file system events."""
    activity = Signal()


class ProjectWatcher(FileSystemEventHandler):
    """Watches project directory for file changes."""
    
    DEFAULT_EXCLUDES = {
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".venv", "venv",
        ".pytest_cache", ".mypy_cache",
        "dist", "build", ".next", ".nuxt",
    }
    
    def __init__(self, signaler: FSEventSignaler, excludes: Optional[set] = None):
        super().__init__()
        self.signaler = signaler
        self.excludes = excludes or self.DEFAULT_EXCLUDES
    
    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        parts = Path(path).parts
        return any(part in self.excludes for part in parts)
    
    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        if event.is_directory:
            return
        if self._should_ignore(event.src_path):
            return
        self.signaler.activity.emit()


# =============================================================================
# Log Watcher
# =============================================================================

class LogPatterns:
    """Regex patterns for log parsing."""
    RUNNING = re.compile(
        r"running|executing|pytest|npm test|pnpm test|yarn test|build|compile|install",
        re.IGNORECASE
    )
    ERROR = re.compile(
        r"error|failed|exception|traceback|fatal",
        re.IGNORECASE
    )
    SUCCESS = re.compile(
        r"success|passed|done|completed|finished",
        re.IGNORECASE
    )


class LogTailer:
    """Tails a log file and emits signals based on content."""
    
    def __init__(self, log_path: str, state_resolver: StateResolver):
        self.log_path = Path(log_path)
        self.state_resolver = state_resolver
        self.position = 0
        
        # Initialize position to end of file if it exists
        if self.log_path.exists():
            self.position = self.log_path.stat().st_size
    
    def check(self):
        """Check for new log content."""
        if not self.log_path.exists():
            return
        
        try:
            current_size = self.log_path.stat().st_size
            
            # File was truncated/rotated
            if current_size < self.position:
                self.position = 0
            
            if current_size > self.position:
                with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self.position)
                    new_content = f.read()
                    self.position = f.tell()
                    self._analyze(new_content)
        except Exception:
            pass  # Silently ignore errors (robustness requirement)
    
    def _analyze(self, content: str):
        """Analyze log content and trigger state changes."""
        if LogPatterns.ERROR.search(content):
            self.state_resolver.on_error()
        elif LogPatterns.SUCCESS.search(content):
            self.state_resolver.on_success()
        elif LogPatterns.RUNNING.search(content):
            self.state_resolver.on_running()
        else:
            self.state_resolver.on_log_activity()


# =============================================================================
# Overlay UI
# =============================================================================

class AvatarOverlay(QWidget):
    """The main overlay window with animated avatar."""
    
    def __init__(self, assets_dir: str, default_character: Optional[str] = None):
        super().__init__()
        self.assets_dir = Path(assets_dir)
        self.current_state: Optional[State] = None
        self.current_character: Optional[str] = None
        self.movies: dict[State, QMovie] = {}
        self.characters: list[str] = []
        self._drag_start_pos: Optional[QPoint] = None
        self._dragging: bool = False
        
        self._setup_window()
        self._discover_characters()
        
        # Set initial character
        if default_character and default_character in self.characters:
            self._load_character(default_character)
        elif self.characters:
            self._load_character(self.characters[0])
        
        self._setup_ui()
    
    def _setup_window(self):
        """Configure window properties for overlay behavior."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(256, 256)
        
        # Position at bottom-right of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 280, screen.height() - 320)
    
    def _discover_characters(self):
        """Discover available character packs in assets directory."""
        self.characters = []
        if not self.assets_dir.exists():
            print(f"Warning: Assets directory not found: {self.assets_dir}")
            return
        
        for path in sorted(self.assets_dir.iterdir()):
            if path.is_dir():
                # Check if it has at least one state gif
                has_assets = any(
                    (path / f"{s.name.lower()}.gif").exists() 
                    for s in State
                )
                if has_assets:
                    self.characters.append(path.name)
        
        if not self.characters:
            print(f"Warning: No character packs found in {self.assets_dir}")
    
    def _load_character(self, character_name: str):
        """Load animation assets for a specific character."""
        if character_name not in self.characters:
            print(f"Warning: Character '{character_name}' not found")
            return
        
        # Stop and clear current movies
        for movie in self.movies.values():
            movie.stop()
        self.movies.clear()
        
        self.current_character = character_name
        char_dir = self.assets_dir / character_name
        
        for state in State:
            gif_path = char_dir / f"{state.name.lower()}.gif"
            if gif_path.exists():
                movie = QMovie(str(gif_path))
                movie.setCacheMode(QMovie.CacheMode.CacheAll)
                self.movies[state] = movie
            else:
                print(f"Warning: Missing asset {gif_path}")
        
        # Re-apply current state if any
        if self.current_state and hasattr(self, 'label'):
            old_state = self.current_state
            self.current_state = None
            self.set_state(old_state)
    
    def switch_character(self, character_name: str):
        """Switch to a different character pack."""
        if character_name == self.current_character:
            return
        self._load_character(character_name)
        print(f"Switched to character: {character_name}")
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Let the window handle mouse events for dragging/context menu.
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.label)
    
    def set_state(self, state: State):
        """Change the displayed animation to match the state."""
        if state == self.current_state:
            return
        
        self.current_state = state
        
        if state in self.movies:
            movie = self.movies[state]
            self.label.setMovie(movie)
            movie.start()

    def showEvent(self, event):
        """Ensure window stays on top when shown."""
        super().showEvent(event)
        self.raise_()
        
    
    # Drag handling - WSLg compatible
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.raise_()
            if self.windowHandle() and self.windowHandle().startSystemMove():
                event.accept()
                return
            # Store the offset from widget origin to click position
            self._drag_start_pos = event.position().toPoint()
            self._dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate new position based on global cursor position
            try:
                # Try globalPosition first (Qt6 preferred)
                global_pos = event.globalPosition().toPoint()
            except:
                # Fallback for compatibility
                global_pos = event.globalPos()
            
            new_pos = global_pos - self._drag_start_pos
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        event.accept()
    
    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    # Keyboard navigation (for WSLg where drag doesn't work)
    def keyPressEvent(self, event: QKeyEvent):
        """Move window with arrow keys."""
        step = 20  # pixels to move per keypress
        pos = self.pos()
        
        if event.key() == Qt.Key.Key_Left:
            self.move(pos.x() - step, pos.y())
        elif event.key() == Qt.Key.Key_Right:
            self.move(pos.x() + step, pos.y())
        elif event.key() == Qt.Key.Key_Up:
            self.move(pos.x(), pos.y() - step)
        elif event.key() == Qt.Key.Key_Down:
            self.move(pos.x(), pos.y() + step)
        elif event.key() == Qt.Key.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)
    
    # Context menu for position presets
    def _show_context_menu(self, pos: QPoint):
        """Show right-click context menu."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #4a90a4;
            }
            QMenu::item:checked {
                font-weight: bold;
            }
        """)
        
        screen = QApplication.primaryScreen().geometry()
        
        # Character switcher
        if len(self.characters) > 1:
            char_menu = menu.addMenu("🎭 キャラ切替")
            
            def make_char_action(char_name: str):
                action = QAction(char_name, self)
                action.setCheckable(True)
                action.setChecked(char_name == self.current_character)
                action.triggered.connect(
                    lambda checked=False, c=char_name: self.switch_character(c)
                )
                return action
            
            for char in self.characters:
                char_menu.addAction(make_char_action(char))
            
            menu.addSeparator()
        
        # Position presets
        positions_menu = menu.addMenu("📍 位置を移動")
        
        def make_move_action(name: str, x: int, y: int):
            action = QAction(name, self)
            # Use default args to capture values properly (Python closure fix)
            action.triggered.connect(lambda checked=False, px=x, py=y: self.move(px, py))
            return action
        
        positions_menu.addAction(make_move_action("↗ 右上", screen.width() - 280, 40))
        positions_menu.addAction(make_move_action("↘ 右下", screen.width() - 280, screen.height() - 320))
        positions_menu.addAction(make_move_action("↖ 左上", 20, 40))
        positions_menu.addAction(make_move_action("↙ 左下", 20, screen.height() - 320))
        positions_menu.addAction(make_move_action("⬜ 中央", (screen.width() - 256) // 2, (screen.height() - 256) // 2))
        
        menu.addSeparator()
        
        # Keyboard hint
        hint_action = QAction("⌨ 矢印キーで微調整", self)
        hint_action.setEnabled(False)
        menu.addAction(hint_action)
        
        menu.addSeparator()
        
        # Quit
        quit_action = QAction("❌ 終了", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        menu.exec(pos)


# =============================================================================
# Application Controller
# =============================================================================

class AvatarApp:
    """Main application controller."""
    
    def __init__(
        self,
        project_dir: str,
        assets_dir: str,
        log_path: Optional[str] = None,
        excludes: Optional[set] = None,
    ):
        self.project_dir = Path(project_dir)
        self.assets_dir = Path(assets_dir)
        self.log_path = log_path
        self.excludes = excludes
        
        # Components
        self.state_resolver = StateResolver()
        self.fs_signaler = FSEventSignaler()
        self.log_tailer: Optional[LogTailer] = None
        self.observer: Optional[Observer] = None
        self.overlay: Optional[AvatarOverlay] = None
        
        # Timers
        self.state_timer: Optional[QTimer] = None
        self.log_timer: Optional[QTimer] = None
        self.keep_on_top_timer: Optional[QTimer] = None
    
    def start(self, app: QApplication):
        """Start all components."""
        # Create overlay
        self.overlay = AvatarOverlay(str(self.assets_dir))
        self.overlay.show()
        self.overlay.set_state(State.IDLE)
        
        # Set up file system watcher
        self.fs_signaler.activity.connect(self.state_resolver.on_fs_activity)
        watcher = ProjectWatcher(self.fs_signaler, self.excludes)
        self.observer = Observer()
        self.observer.schedule(watcher, str(self.project_dir), recursive=True)
        self.observer.start()
        
        # Set up log tailer if log path provided
        if self.log_path:
            self.log_tailer = LogTailer(self.log_path, self.state_resolver)
            self.log_timer = QTimer()
            self.log_timer.timeout.connect(self.log_tailer.check)
            self.log_timer.start(500)  # Check every 500ms
        
        # Set up state update timer
        self.state_timer = QTimer()
        self.state_timer.timeout.connect(self._update_state)
        self.state_timer.start(200)  # Update every 200ms
        
        # Set up keep-on-top timer to ensure overlay stays visible
        self.keep_on_top_timer = QTimer()
        self.keep_on_top_timer.timeout.connect(self._keep_on_top)
        self.keep_on_top_timer.start(2000)  # Raise every 2 seconds
    
    def _update_state(self):
        """Update the overlay state."""
        if self.overlay:
            state = self.state_resolver.resolve()
            self.overlay.set_state(state)
    
    def _keep_on_top(self):
        """Periodically raise the overlay to keep it on top."""
        if self.overlay:
            self.overlay.raise_()
    
    def stop(self):
        """Stop all components."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.state_timer:
            self.state_timer.stop()
        if self.log_timer:
            self.log_timer.stop()
        if self.keep_on_top_timer:
            self.keep_on_top_timer.stop()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Avatar Overlay - Visual coding agent companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python avatar_overlay.py /path/to/project /path/to/assets
  python avatar_overlay.py . ./assets --log agent.log
  python avatar_overlay.py ~/myproject ~/avatar/assets --exclude .cache,tmp
        """
    )
    parser.add_argument(
        "project_dir",
        help="Directory to watch for file changes"
    )
    parser.add_argument(
        "assets_dir",
        help="Directory containing animation assets (idle.gif, thinking.gif, etc.)"
    )
    parser.add_argument(
        "--log", "-l",
        dest="log_path",
        help="Optional log file to monitor for status detection"
    )
    parser.add_argument(
        "--exclude", "-e",
        help="Comma-separated list of additional directories to exclude"
    )
    
    args = parser.parse_args()
    
    # Parse excludes
    excludes = None
    if args.exclude:
        excludes = set(args.exclude.split(","))
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # Create and start avatar app
    avatar_app = AvatarApp(
        project_dir=args.project_dir,
        assets_dir=args.assets_dir,
        log_path=args.log_path,
        excludes=excludes,
    )
    avatar_app.start(app)
    
    # Run
    try:
        sys.exit(app.exec())
    finally:
        avatar_app.stop()


if __name__ == "__main__":
    main()
