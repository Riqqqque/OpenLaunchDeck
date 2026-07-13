from __future__ import annotations

import ctypes
import sys
import time
from dataclasses import dataclass
from ctypes import wintypes

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from . import native_acceleration
from .actions.registry import create_default_registry
from .audio.audio_engine import AudioEngine
from .devices.launchpad_mini_mk3 import LaunchpadMiniMk3
from .logging_setup import configure_logging, shutdown_logging
from .paths import ensure_user_dirs
from .services.action_runner import ActionRunner
from .services.dangerous_confirm import DangerousConfirmService
from .services.lighting_service import LightingService
from .services.performance_monitor import PerformanceMonitor
from .services.profile_service import ProfileService
from .services.settings_service import SettingsService
from .services.startup_service import StartupService
from .single_instance import (
    COMMAND_BACKGROUND,
    LaunchOptions,
    SingleInstanceServer,
    notify_existing_instance,
    parse_launch_options,
)
from .ui.icons import app_icon
from .ui.main_window import MainWindow
from .version import APP_NAME

ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
HIGH_PRIORITY_CLASS = 0x00000080
NORMAL_PRIORITY_CLASS = 0x00000020
REALTIME_PRIORITY_CLASS = 0x00000100
PRIORITY_CLASSES_TO_NORMALIZE = {
    ABOVE_NORMAL_PRIORITY_CLASS,
    HIGH_PRIORITY_CLASS,
    REALTIME_PRIORITY_CLASS,
}
PRIORITY_STARTUP_RECHECK_DELAYS_MS = (100, 500, 1_000, 2_000, 5_000)
PRIORITY_GUARD_INTERVAL_MS = 60_000


def _kernel32_priority_api() -> object:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel.GetPriorityClass.restype = wintypes.DWORD
    kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.SetPriorityClass.restype = wintypes.BOOL
    return kernel


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Rique.OpenLaunchDeck")
    except Exception:
        pass


def _set_windows_process_priority(kernel32: object | None = None, logger: object | None = None) -> bool:
    if sys.platform != "win32":
        return False
    using_real_kernel = kernel32 is None
    try:
        kernel = kernel32 or _kernel32_priority_api()
        process = kernel.GetCurrentProcess()
        current_priority = int(kernel.GetPriorityClass(process))
        target_priority = NORMAL_PRIORITY_CLASS
        if current_priority == target_priority or current_priority not in PRIORITY_CLASSES_TO_NORMALIZE:
            return False
        if using_real_kernel:
            ctypes.set_last_error(0)
        if not kernel.SetPriorityClass(process, target_priority):
            if logger:
                error_code = ctypes.get_last_error() if using_real_kernel else None
                if error_code:
                    logger.warning("Could not set process priority to Normal. Windows error: %s", error_code)
                else:
                    logger.warning("Could not set process priority to Normal.")
            return False
        if logger:
            logger.info("Adjusted process priority from %s to Normal.", current_priority)
        return True
    except Exception:
        if logger:
            logger.exception("Could not adjust process priority.")
        return False


def start_windows_priority_guard(app: QApplication, logger: object | None = None) -> QTimer | None:
    if sys.platform != "win32":
        return None
    _set_windows_process_priority(logger=logger)
    for delay_ms in PRIORITY_STARTUP_RECHECK_DELAYS_MS:
        QTimer.singleShot(delay_ms, lambda: _set_windows_process_priority(logger=logger))
    timer = QTimer(app)
    timer.setTimerType(Qt.TimerType.VeryCoarseTimer)
    timer.setInterval(PRIORITY_GUARD_INTERVAL_MS)
    timer.timeout.connect(lambda: _set_windows_process_priority(logger=logger))
    timer.start()
    return timer


@dataclass(slots=True)
class AppServices:
    settings_service: SettingsService
    profile_service: ProfileService
    audio_engine: AudioEngine
    lighting_service: LightingService
    device: LaunchpadMiniMk3
    action_runner: ActionRunner
    action_registry: object
    logger: object
    performance_monitor: PerformanceMonitor
    startup_service: StartupService


def build_services() -> AppServices:
    start = time.perf_counter()
    ensure_user_dirs()
    settings_service = SettingsService()
    logger = configure_logging(settings_service.settings.midi_debug_logging)
    logger.info("Starting %s", APP_NAME)
    if settings_service.load_warning:
        logger.warning("%s", settings_service.load_warning)
    startup_service = StartupService(logger=logger)
    if getattr(sys, "frozen", False):
        startup_service.sync(settings_service.settings.launch_at_startup)
    native_acceleration.configure(settings_service.settings.use_native_acceleration, logger)
    performance_monitor = PerformanceMonitor(logger, settings_service.settings.enable_performance_logging)
    profile_service = ProfileService(logger=logger)
    profile_service.set_current_profile(settings_service.settings.default_profile)
    audio_engine = AudioEngine(
        logger=logger,
        global_volume=settings_service.settings.soundboard_global_volume,
        default_output_device_id=settings_service.settings.soundboard_default_output_device,
        voice_chat_output_device_id=settings_service.settings.soundboard_voice_chat_output_device,
        monitor_voice_chat_routes=settings_service.settings.soundboard_monitor_voice_chat,
        voice_route_microphone_enabled=settings_service.settings.soundboard_voice_route_microphone_enabled,
        voice_route_microphone_device_id=settings_service.settings.soundboard_voice_route_microphone_device,
        voice_route_microphone_volume=settings_service.settings.soundboard_voice_route_microphone_volume,
        performance_logging_enabled=settings_service.settings.enable_performance_logging,
        performance_monitor=performance_monitor,
    )
    if settings_service.settings.soundboard_voice_route_microphone_enabled:
        audio_engine.refresh_voice_route_microphone()
    device = LaunchpadMiniMk3(logger=logger, performance_monitor=performance_monitor)
    lighting_service = LightingService(
        device=device,
        logger=logger,
        performance_monitor=performance_monitor,
        async_output=True,
    )
    registry = create_default_registry()
    action_runner = ActionRunner(
        registry=registry,
        profile_service=profile_service,
        dangerous_service=DangerousConfirmService(),
        audio_engine=audio_engine,
        lighting_service=lighting_service,
        device_manager=device,
        settings_service=settings_service,
        logger=logger,
        performance_monitor=performance_monitor,
    )
    performance_monitor.record_since("app_startup_build_services", start)
    return AppServices(
        settings_service=settings_service,
        profile_service=profile_service,
        audio_engine=audio_engine,
        lighting_service=lighting_service,
        device=device,
        action_runner=action_runner,
        action_registry=registry,
        logger=logger,
        performance_monitor=performance_monitor,
        startup_service=startup_service,
    )


def show_initial_window_state(window: MainWindow, start_minimized: bool) -> None:
    if not start_minimized:
        window.show()
        return
    if window.should_keep_running_in_background():
        window.hide()
        return
    window.showMinimized()


def resolve_start_minimized(settings_start_minimized: bool, launch_options: LaunchOptions) -> bool:
    if launch_options.start_minimized_override is not None:
        return launch_options.start_minimized_override
    return settings_start_minimized


def handle_single_instance_command(window: MainWindow, command: str) -> None:
    if command == COMMAND_BACKGROUND:
        return
    window.restore_from_tray()


def run() -> int:
    start = time.perf_counter()
    launch_options = parse_launch_options(sys.argv)
    _set_windows_app_user_model_id()
    _set_windows_process_priority()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setWindowIcon(app_icon())
    if notify_existing_instance(launch_options.command):
        return 0
    single_instance = SingleInstanceServer(parent=app)
    single_instance_listening = single_instance.listen()
    try:
        services = build_services()
    except Exception as exc:
        single_instance.close()
        QMessageBox.critical(
            None,
            APP_NAME,
            f"OpenLaunchDeck could not start. Check that the AppData folder is writable.\n\n{exc}",
        )
        return 1
    _set_windows_process_priority(logger=services.logger)
    single_instance.set_logger(services.logger)
    if not single_instance_listening:
        services.logger.warning("Single-instance startup handling is unavailable.")
    priority_guard = start_windows_priority_guard(app, services.logger)
    try:
        with services.performance_monitor.measure("app_startup_main_window"):
            window = MainWindow(services)
        single_instance.set_command_handler(lambda command: handle_single_instance_command(window, command))
        _set_windows_process_priority(logger=services.logger)
        show_initial_window_state(
            window,
            resolve_start_minimized(services.settings_service.settings.start_minimized, launch_options),
        )
        _set_windows_process_priority(logger=services.logger)
        services.performance_monitor.record_since("app_startup_to_initial_state", start)
        result = app.exec()
    except Exception:
        services.logger.exception("Fatal application error.")
        return 1
    finally:
        services.action_runner.shutdown()
        services.lighting_service.shutdown()
        services.audio_engine.shutdown()
        services.device.close()
        if priority_guard:
            priority_guard.stop()
        single_instance.close()
        shutdown_logging(services.logger)
    return result
