import platform
import shutil
import subprocess


def _safe(s: str) -> str:
    return str(s).replace('"', "'").replace("\n", " ")


def notify(title: str, message: str) -> None:
    """Notifica desktop nativa, best-effort, cross-platform.
    Fallisce in silenzio se il sistema non la supporta."""
    title, message = _safe(title), _safe(message)
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}" '
                 f'sound name "Glass"'],
                check=False, capture_output=True,
            )
        elif system == "Linux":
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", title, message],
                               check=False, capture_output=True)
        elif system == "Windows":
            # Toast via PowerShell (nessuna dipendenza esterna).
            ps = (
                "[Windows.UI.Notifications.ToastNotificationManager, "
                "Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null;"
                "$t=[Windows.UI.Notifications.ToastNotificationManager]::"
                "GetTemplateContent("
                "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
                f"$t.GetElementsByTagName('text').Item(0).AppendChild("
                f"$t.CreateTextNode('{title}')) | Out-Null;"
                f"$t.GetElementsByTagName('text').Item(1).AppendChild("
                f"$t.CreateTextNode('{message}')) | Out-Null;"
                "$n=[Windows.UI.Notifications.ToastNotification]::new($t);"
                "[Windows.UI.Notifications.ToastNotificationManager]::"
                "CreateToastNotifier('OCR Sistema').Show($n);"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           check=False, capture_output=True)
    except Exception:
        pass
