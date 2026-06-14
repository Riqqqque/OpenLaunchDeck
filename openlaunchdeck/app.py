from __future__ import annotations

import ctypes
import sys
import time
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from . import native_acceleration
from .actions.registry import create_default_registry
from .audio.audio_engine import AudioEngine
from .devices.launchpad_mini_mk3 import LaunchpadMiniMk3
from .logging_setup import configure_logging
from .paths import ensure_user_dirs
from .services.action_runner import ActionRunner
from .services.dangerous_confirm import DangerousConfirmService
from .services.lighting_service import LightingService
from .services.performance_monitor import PerformanceMonitor
from .services.profile_service import ProfileService
from .services.settings_service import SettingsService
from .services.startup_service import StartupService
from .ui.icons import app_icon
from .ui.main_window import MainWindow
from .version import APP_NAME


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Rique.OpenLaunchDeck")
    except Exception:
        pass


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
    startup_service = StartupService(logger=logger)
    if getattr(sys, "frozen", False):
        startup_service.sync(settings_service.settings.launch_at_startup)
    native_acceleration.configure(settings_service.settings.use_native_acceleration, logger)
    performance_monitor = PerformanceMonitor(logger, settings_service.settings.enable_performance_logging)
    profile_service = ProfileService(logger=logger)
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


def run() -> int:
    start = time.perf_counter()
    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setWindowIcon(app_icon())
    services = build_services()
    try:
        with services.performance_monitor.measure("app_startup_main_window"):
            window = MainWindow(services)
        window.show()
        services.performance_monitor.record_since("app_startup_to_window_shown", start)
        if services.settings_service.settings.start_minimized:
            if window.should_keep_running_in_background():
                window.hide()
            else:
                window.showMinimized()
        result = app.exec()
    except Exception:
        services.logger.exception("Fatal application error.")
        return 1
    finally:
        services.audio_engine.shutdown()
        services.lighting_service.shutdown()
        services.action_runner.shutdown()
        services.device.close()
    return result
