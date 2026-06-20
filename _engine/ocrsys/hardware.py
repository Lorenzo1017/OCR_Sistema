import os
import platform
import shutil
import subprocess

# Soglie pensate per il modello locale qwen2.5:7b (~5GB in RAM durante l'uso).
MIN_RAM_GB = 8
RACC_RAM_GB = 16
MIN_DISK_GB = 10   # modello ~5GB + documenti + margine


def ram_gb():
    """RAM totale in GB, cross-platform. None se non determinabile."""
    s = platform.system()
    try:
        if s == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) / 1024 / 1024
        elif s == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"])
            return int(out) / (1024 ** 3)
        elif s == "Windows":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys / (1024 ** 3)
    except Exception:
        return None
    return None


def disk_free_gb(path):
    try:
        return shutil.disk_usage(str(path)).free / (1024 ** 3)
    except Exception:
        return None


def report(base):
    return {
        "os": platform.system(),
        "cpu": os.cpu_count(),
        "ram_gb": ram_gb(),
        "disk_free_gb": disk_free_gb(base),
    }


def valuta(rep):
    """Ritorna (problemi, avvisi). problemi = sotto i minimi (rischio non funzioni);
    avvisi = sufficiente ma non ideale."""
    problemi, avvisi = [], []
    ram = rep.get("ram_gb")
    if ram is not None:
        if ram < MIN_RAM_GB:
            problemi.append(
                f"RAM {ram:.0f}GB sotto i {MIN_RAM_GB}GB minimi: il modello 7B "
                f"potrebbe non caricarsi. Valuta un modello piu' piccolo."
            )
        elif ram < RACC_RAM_GB:
            avvisi.append(
                f"RAM {ram:.0f}GB: sufficiente, ma {RACC_RAM_GB}GB consigliati. "
                f"Chiudi app pesanti durante l'elaborazione."
            )
    disk = rep.get("disk_free_gb")
    if disk is not None and disk < MIN_DISK_GB:
        problemi.append(
            f"Spazio libero {disk:.0f}GB sotto i {MIN_DISK_GB}GB: serve spazio "
            f"per il modello (~5GB) e i documenti."
        )
    cpu = rep.get("cpu")
    if cpu is not None and cpu < 4:
        avvisi.append(f"{cpu} core CPU: l'OCR sara' piu' lento (consigliati 4+).")
    return problemi, avvisi
