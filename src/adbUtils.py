import subprocess
from pathlib import Path
import models
import config
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

#已知的模拟器ADB端口列表，程序会自动扫描并连接这些端口上的模拟器设备。
SIMULATORS: Dict[str, int] = {
    "网易 MuMu": 7555,
    "夜神": 62001,
    "逍遥安卓": 21503,
    "雷电": 5555,
    "蓝叠": 5555,
    "腾讯手游助手": 5555,
    "Genymotion": 5555,
    "Android Studio (AVD)": 5554,
    "天天模拟器": 6555,
    "海马玩": 26944,
    "iTools": 54001,
    "安卓模拟器大师": 54001,
}

LOCALHOST = "127.0.0.1"
CONNECT_TIMEOUT = 1.0

DEVICE_DB_PATH = "/data/data/com.kuangxiangciweimao.novel/databases/novelCiwei"
DEVICE_KEY_DIR = "/data/data/com.kuangxiangciweimao.novel/files/Y2hlcy8"
DEVICE_BOOKS_DIR = "/data/data/com.kuangxiangciweimao.novel/files/novelCiwei/reader/booksnew"
APP_DATA_DIR = "/data/data/com.kuangxiangciweimao.novel"
APP_PACKAGE = "com.kuangxiangciweimao.novel" 
SDCARD_TMP = "/sdcard/cwmd_adb_tmp"

_device_serial: str = ""

def _adb(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run adb command with device serial if known."""
    if _device_serial:
        cmd = ["adb", "-s", _device_serial] + cmd
    else:
        cmd = ["adb"] + cmd
    return subprocess.run(cmd, capture_output=True, text=True)


def adb(cmd: str) -> subprocess.CompletedProcess:
    return _adb(["shell", f"{cmd}"])

def _try_connect_adb_fast(host: str, port: int, timeout: float = CONNECT_TIMEOUT) -> bool:
    """快速尝试连接网络 ADB（无预检，直接 adb connect）。"""
    target = f"{host}:{port}"
    try:
        res = subprocess.run(
            ["adb", "connect", target],
            capture_output=True, text=True, timeout=timeout
        )
        output = res.stdout.lower()
        return "connected" in output or "already connected" in output
    except Exception:
        return False

def _preDetect() -> None:
    """并发扫描模拟器端口，打印连接状态表格，并尝试连接。"""
    models.Print.info("[INFO]正在扫描模拟器...")

    # 用线程池并发连接所有端口
    results: Dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=len(SIMULATORS)) as executor:
        future_map = {
            executor.submit(_try_connect_adb_fast, LOCALHOST, port): name
            for name, port in SIMULATORS.items()
        }
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                success = future.result()
            except Exception:
                success = False
            results[name] = success

    # 按原顺序打印表格
    models.Print.warn("[INFO]扫描结果如下：")
    print(f"{'模拟器名称':<20}{'连接状态':<10}")
    print("-" * 30)
    for name in SIMULATORS:
        status = "成功" if results.get(name, False) else "失败"
        print(f"{name:<20}{status:<10}")

def _check_device_app(serial: str) -> bool:
    """检查设备是否安装刺猬猫应用（无需 root）"""
    try:
        res = subprocess.run(
            ["adb", "-s", serial, "shell", f"pm list packages {APP_PACKAGE}"],
            capture_output=True, text=True, timeout=3
        )
        return APP_PACKAGE in res.stdout
    except Exception:
        return False

def _detect_device() -> Tuple[str, bool]:
    """
    自动检测设备，打印设备表格，并返回选中的 (设备序列号, 是否有 app)。
    选择优先级：有 app 的设备 > 第一个可用设备 > 无设备（返回空字符串）。
    """
    # 0. 扫描并连接模拟器
    _preDetect()
    # 1. 获取所有在线设备
    proc = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines: List[str] = proc.stdout.strip().split("\n")[1:]
    devices: List[str] = [l.split("\t")[0] for l in lines if "\tdevice" in l]

    if not devices:
        print("未检测到任何设备。")
        return "", False

    # 2. 逐个检测 app（不再检测 root）
    info: List[Tuple[str, bool]] = []   # (serial, has_app)
    for serial in devices:
        has_app = _check_device_app(serial)  # 忽略 root，直接检查 app
        info.append((serial, has_app))

    # 3. 打印表格
    models.Print.warn("[INFO]测试结果如下：")
    print(f"{'Device':<24}{'Ciweimao':<12}")
    print("-" * 36)
    for serial, has_app in info:
        print(f"{serial:<24}{'Yes' if has_app else 'No':<12}")

    # 4. 按优先级选择设备（优先有 app 的）
    for serial, has_app in info:
        if has_app:
            return serial, has_app
    # 其次返回第一个设备（若有）
    if devices:
        return devices[0], False
    return "", False

def check_adb() -> None:
    """检查并确认 adb 设备"""
    global _device_serial

    # 用户是否指定了设备
    specified: str = config.setting.adb.device if hasattr(config.setting.adb, "device") else ""
    
    if specified:
        _device_serial = specified
        if not _check_device_app(specified):
            models.Print.err("[ERR] 设备未安装刺猬猫应用，请确认模拟器已安装并开启 adb 调试")
            raise RuntimeError("app not available")
    else:
        serial, hasApp = _detect_device()
        if not serial:
            models.Print.err("[ERR] 未检测到 adb 设备，请确认模拟器已开启 adb 调试")
            raise RuntimeError("adb device not found")
        if not hasApp:
            models.Print.err("[ERR] 设备未安装刺猬猫应用，请确认模拟器已安装并开启 adb 调试")
            raise RuntimeError("app not available")
        _device_serial = serial

    models.Print.info(f"[INFO] adb 设备已连接：{_device_serial}")

def pull_db():
    local_db = Path("data/novelCiwei.db")
    # 清除旧文件（支持文件或目录）
    if local_db.exists():
        if local_db.is_dir():
            import shutil
            shutil.rmtree(local_db)
        else:
            local_db.unlink()

    models.Print.info("[INFO] 正在从设备拉取数据库文件...")

    # 1. 将设备上的单个数据库文件复制到临时路径（sdcard 可读）
    temp_file = f"{SDCARD_TMP}_db"   # 用唯一临时文件名，避免与旧 key 混淆
    adb(f"cp '{DEVICE_DB_PATH}' '{temp_file}'")

    # 2. 拉取临时文件到本地
    r = _adb(["pull", temp_file, str(local_db)])

    # 3. 清理临时文件
    adb(f"rm -f '{temp_file}'")

    if r.returncode != 0:
        models.Print.err(f"[ERR] 拉取数据库文件失败：{r.stderr}")
        raise RuntimeError("pull db failed")
    models.Print.info(f"[INFO] 数据库文件拉取完成")

def pull_keys():
    local_key = Path("data/key")
    # Key files are session-specific and must be re-pulled each run.
    if local_key.exists():
        import shutil
        shutil.rmtree(local_key)

    models.Print.info("[INFO] 正在从设备拉取密钥文件...")
    local_key.mkdir(parents=True, exist_ok=True)

    adb(f"cp -r '{DEVICE_KEY_DIR}' '{SDCARD_TMP}_key'")
    r = _adb(["pull", f"{SDCARD_TMP}_key/.", str(local_key)])
    adb(f"rm -rf '{SDCARD_TMP}_key'")

    if r.returncode != 0:
        models.Print.err(f"[ERR] 拉取密钥文件失败：{r.stderr}")
        raise RuntimeError("pull keys failed")
    models.Print.info(f"[INFO] 密钥文件拉取完成")


def pull_book(book_id: int):
    # Encrypted Text files are session-specific and must be re-pulled each run.
    local_dir = Path("data") / str(book_id)
    if local_dir.exists():
        import shutil
        shutil.rmtree(local_dir)

    models.Print.info(f"[INFO] 正在从设备拉取 {book_id} 的加密章节...")
    local_dir.mkdir(parents=True, exist_ok=True)

    src = f"{DEVICE_BOOKS_DIR}/{book_id}"
    tmp = f"{SDCARD_TMP}_{book_id}"
    adb(f"cp -r '{src}' '{tmp}'")
    r = _adb(["pull", f"{tmp}/.", str(local_dir)])
    adb(f"rm -rf '{tmp}'")

    if r.returncode != 0:
        models.Print.err(f"[ERR] 拉取 {book_id} 失败：{r.stderr}")
        raise RuntimeError(f"pull book {book_id} failed")
    models.Print.info(f"[INFO] {book_id} 章节拉取完成")


def list_books():
    r = adb(f"ls '{DEVICE_BOOKS_DIR}'")
    if r.returncode != 0:
        models.Print.err(f"[ERR] 无法列出设备上的书籍目录：{r.stderr}")
        return []
    ids = [line.strip() for line in r.stdout.split("\n") if line.strip().isdigit()]
    return ids
