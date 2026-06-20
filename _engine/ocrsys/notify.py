import platform
import shutil
import subprocess


def _mac(s: str) -> str:
    # dentro stringa AppleScript fra doppi apici: neutralizza \ e "
    return str(s).replace("\\", " ").replace('"', "'").replace("\n", " ")


def _win(s: str) -> str:
    # dentro stringa PowerShell fra apici singoli: raddoppia l'apice singolo
    # (evita rottura/iniezione di comandi da nomi file tipo  '; rm ... )
    return str(s).replace("'", "''").replace("\n", " ")


def notify(title: str, message: str) -> None:
    """Notifica desktop nativa, best-effort, cross-platform.
    Fallisce in silenzio se il sistema non la supporta."""
    system = platform.system()
    try:
        if system == "Darwin":
            t, m = _mac(title), _mac(message)
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{m}" with title "{t}" '
                 f'sound name "Glass"'],
                check=False, capture_output=True,
            )
        elif system == "Linux":
            # argomenti passati come lista -> nessuna shell, nessuna injection
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", str(title), str(message)],
                               check=False, capture_output=True)
        elif system == "Windows":
            title, message = _win(title), _win(message)
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
