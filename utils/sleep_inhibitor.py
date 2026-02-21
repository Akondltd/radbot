"""
System sleep/hibernate inhibitor for RadBot.

Prevents the OS from sleeping or hibernating while RadBot is actively
running trades. Supports Windows, Linux, and macOS.

Usage:
    inhibitor = SleepInhibitor()
    inhibitor.inhibit()   # Call on app start
    inhibitor.release()   # Call on app close
"""

import sys
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class SleepInhibitor:
    """Cross-platform system sleep/hibernate inhibitor."""

    def __init__(self, reason: str = "RadBot is actively monitoring and executing trades"):
        self._reason = reason
        self._active = False
        self._platform_data = None  # Platform-specific handle/process

    @property
    def is_active(self) -> bool:
        return self._active

    def inhibit(self) -> bool:
        """
        Prevent system from sleeping/hibernating.
        
        Returns:
            True if successfully inhibited, False otherwise.
        """
        if self._active:
            logger.debug("Sleep inhibitor already active")
            return True

        try:
            if sys.platform == 'win32':
                return self._inhibit_windows()
            elif sys.platform == 'darwin':
                return self._inhibit_macos()
            else:
                return self._inhibit_linux()
        except Exception as e:
            logger.warning(f"Failed to inhibit system sleep: {e}")
            return False

    def release(self) -> None:
        """Release the sleep inhibition, allowing the system to sleep normally."""
        if not self._active:
            return

        try:
            if sys.platform == 'win32':
                self._release_windows()
            elif sys.platform == 'darwin':
                self._release_macos()
            else:
                self._release_linux()
        except Exception as e:
            logger.warning(f"Error releasing sleep inhibitor: {e}")
        finally:
            self._active = False
            self._platform_data = None

    # ── Windows ──────────────────────────────────────────────────────

    def _inhibit_windows(self) -> bool:
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001

        # Tell Windows to keep the system awake (display can still turn off)
        result = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )

        if result == 0:
            logger.error("SetThreadExecutionState failed")
            return False

        self._active = True
        logger.info("System sleep inhibited (Windows: SetThreadExecutionState)")
        return True

    def _release_windows(self) -> None:
        import ctypes

        ES_CONTINUOUS = 0x80000000

        # Clear the flags, allowing normal sleep behaviour
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        logger.info("System sleep inhibitor released (Windows)")

    # ── macOS ────────────────────────────────────────────────────────

    def _inhibit_macos(self) -> bool:
        # Use caffeinate subprocess (most reliable, no dependencies)
        try:
            proc = subprocess.Popen(
                ['caffeinate', '-i', '-w', str(subprocess.os.getpid())],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._platform_data = proc
            self._active = True
            logger.info("System sleep inhibited (macOS: caffeinate)")
            return True
        except FileNotFoundError:
            logger.warning("caffeinate not found on macOS")
            return False

    def _release_macos(self) -> None:
        proc: Optional[subprocess.Popen] = self._platform_data
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        logger.info("System sleep inhibitor released (macOS)")

    # ── Linux ────────────────────────────────────────────────────────

    def _inhibit_linux(self) -> bool:
        # Try D-Bus (works on most desktop environments)
        try:
            import dbus
            bus = dbus.SessionBus()
            proxy = bus.get_object(
                'org.freedesktop.ScreenSaver',
                '/org/freedesktop/ScreenSaver'
            )
            iface = dbus.Interface(proxy, 'org.freedesktop.ScreenSaver')
            cookie = iface.Inhibit('RadBot', self._reason)
            self._platform_data = ('dbus', cookie)
            self._active = True
            logger.info("System sleep inhibited (Linux: D-Bus ScreenSaver)")
            return True
        except Exception as e:
            logger.debug(f"D-Bus inhibit failed: {e}")

        # Fallback: systemd-inhibit subprocess
        try:
            proc = subprocess.Popen(
                [
                    'systemd-inhibit',
                    '--what=sleep:idle',
                    '--who=RadBot',
                    f'--reason={self._reason}',
                    '--mode=block',
                    'sleep', 'infinity'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._platform_data = ('systemd', proc)
            self._active = True
            logger.info("System sleep inhibited (Linux: systemd-inhibit)")
            return True
        except FileNotFoundError:
            logger.warning("Neither D-Bus nor systemd-inhibit available on this system")
            return False

    def _release_linux(self) -> None:
        if not self._platform_data:
            return

        method, handle = self._platform_data

        if method == 'dbus':
            try:
                import dbus
                bus = dbus.SessionBus()
                proxy = bus.get_object(
                    'org.freedesktop.ScreenSaver',
                    '/org/freedesktop/ScreenSaver'
                )
                iface = dbus.Interface(proxy, 'org.freedesktop.ScreenSaver')
                iface.UnInhibit(handle)
            except Exception as e:
                logger.debug(f"D-Bus uninhibit error: {e}")

        elif method == 'systemd':
            proc: subprocess.Popen = handle
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)

        logger.info("System sleep inhibitor released (Linux)")
