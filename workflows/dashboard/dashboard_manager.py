#!/usr/bin/env python3
"""
Dashboard process manager - like pm2 for the dashboard server.

Usage:
    uv run python workflows/dashboard/dashboard_manager.py start [--port 5000]
    uv run python workflows/dashboard/dashboard_manager.py stop
    uv run python workflows/dashboard/dashboard_manager.py restart [--port 5000]
    uv run python workflows/dashboard/dashboard_manager.py status
    uv run python workflows/dashboard/dashboard_manager.py logs
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class DashboardManager:
    """Manages the dashboard server process."""

    def __init__(self):
        """Initialize dashboard manager."""
        self.project_root = Path(__file__).parent.parent.parent
        self.pid_file = self.project_root / ".dashboard.pid"
        self.log_file = self.project_root / ".dashboard.log"

    def is_running(self) -> tuple[bool, int | None]:
        """
        Check if dashboard is running.

        Returns:
            Tuple of (is_running, pid)
        """
        if not self.pid_file.exists():
            return False, None

        try:
            pid = int(self.pid_file.read_text().strip())

            # Check if process is actually running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True, pid
            except OSError:
                # Process doesn't exist, clean up stale PID file
                self.pid_file.unlink()
                return False, None

        except (ValueError, FileNotFoundError):
            return False, None

    def start(self, port: int = 5000, host: str = "127.0.0.1"):
        """Start the dashboard server."""
        is_running, pid = self.is_running()

        if is_running:
            print(f"❌ Dashboard is already running (PID: {pid})")
            print(f"   Running at: http://{host}:{port}")
            print(f"   Use 'stop' or 'restart' to manage it")
            return False

        print("🚀 Starting dashboard server...")

        # Start the Streamlit server process
        cmd = [
            "uv",
            "run",
            "streamlit",
            "run",
            "workflows/dashboard/app.py",
            "--server.port",
            str(port),
            "--server.address",
            host,
            "--server.headless",
            "true",
        ]

        # Open log file for output
        log_file = open(self.log_file, "w")

        process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent
        )

        # Save PID
        self.pid_file.write_text(str(process.pid))

        # Give it a moment to start
        time.sleep(2)

        # Check if it actually started
        is_running, pid = self.is_running()

        if is_running:
            print(f"✅ Dashboard started successfully")
            print(f"   PID: {pid}")
            print(f"   URL: http://{host}:{port}")
            print(f"   Logs: {self.log_file}")
            print()
            print("   Commands:")
            print("     uv run python workflows/dashboard/dashboard_manager.py status")
            print("     uv run python workflows/dashboard/dashboard_manager.py logs")
            print("     uv run python workflows/dashboard/dashboard_manager.py stop")
            return True
        else:
            print("❌ Failed to start dashboard")
            print(f"   Check logs: {self.log_file}")
            return False

    def stop(self):
        """Stop the dashboard server."""
        is_running, pid = self.is_running()

        if not is_running:
            print("ℹ️  Dashboard is not running")
            return True

        print(f"🛑 Stopping dashboard (PID: {pid})...")

        try:
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)

            # Wait up to 5 seconds for graceful shutdown
            for _ in range(50):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    # Process is gone
                    break
            else:
                # Still running, force kill
                print("   Forcing shutdown...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)

            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

            print("✅ Dashboard stopped")
            return True

        except OSError as e:
            print(f"❌ Error stopping dashboard: {e}")
            # Clean up PID file anyway
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False

    def restart(self, port: int = 5000, host: str = "127.0.0.1"):
        """Restart the dashboard server."""
        print("🔄 Restarting dashboard...")
        self.stop()
        time.sleep(1)
        return self.start(port, host)

    def status(self):
        """Show dashboard status."""
        is_running, pid = self.is_running()

        print("=" * 60)
        print("Dashboard Status")
        print("=" * 60)

        if is_running:
            print(f"Status: ✅ Running")
            print(f"PID: {pid}")

            # Try to read port from process command line
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as f:
                    cmdline = f.read().decode("utf-8").split("\x00")
                    if "--port" in cmdline:
                        port_idx = cmdline.index("--port")
                        port = cmdline[port_idx + 1]
                        print(f"URL: http://127.0.0.1:{port}")
            except (FileNotFoundError, IndexError, ValueError):
                print("URL: http://127.0.0.1:5000 (default)")

            print(f"Logs: {self.log_file}")
        else:
            print("Status: ❌ Not running")

        print("=" * 60)

    def logs(self, follow: bool = False, lines: int = 50):
        """Show dashboard logs."""
        if not self.log_file.exists():
            print("ℹ️  No logs found (dashboard hasn't been started yet)")
            return

        if follow:
            print(f"📋 Following logs from {self.log_file}")
            print("   Press Ctrl+C to stop")
            print("-" * 60)

            # Use tail -f equivalent
            try:
                subprocess.run(
                    ["tail", "-f", str(self.log_file)],
                    check=True,
                )
            except KeyboardInterrupt:
                print("\n\nStopped following logs")
        else:
            print(f"📋 Last {lines} lines from {self.log_file}")
            print("-" * 60)

            # Read last N lines
            try:
                result = subprocess.run(
                    ["tail", "-n", str(lines), str(self.log_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(result.stdout)
            except subprocess.CalledProcessError:
                # Fallback to Python if tail not available
                with open(self.log_file) as f:
                    all_lines = f.readlines()
                    for line in all_lines[-lines:]:
                        print(line, end="")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dashboard process manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python workflows/dashboard/dashboard_manager.py start
  uv run python workflows/dashboard/dashboard_manager.py start --port 8080
  uv run python workflows/dashboard/dashboard_manager.py stop
  uv run python workflows/dashboard/dashboard_manager.py restart
  uv run python workflows/dashboard/dashboard_manager.py status
  uv run python workflows/dashboard/dashboard_manager.py logs
  uv run python workflows/dashboard/dashboard_manager.py logs --follow
        """,
    )

    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "logs"],
        help="Command to execute",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--follow",
        "-f",
        action="store_true",
        help="Follow log output (for logs command)",
    )

    parser.add_argument(
        "--lines",
        "-n",
        type=int,
        default=50,
        help="Number of log lines to show (default: 50)",
    )

    args = parser.parse_args()

    manager = DashboardManager()

    if args.command == "start":
        success = manager.start(port=args.port, host=args.host)
        sys.exit(0 if success else 1)

    elif args.command == "stop":
        success = manager.stop()
        sys.exit(0 if success else 1)

    elif args.command == "restart":
        success = manager.restart(port=args.port, host=args.host)
        sys.exit(0 if success else 1)

    elif args.command == "status":
        manager.status()
        sys.exit(0)

    elif args.command == "logs":
        manager.logs(follow=args.follow, lines=args.lines)
        sys.exit(0)


if __name__ == "__main__":
    main()
