import os
import datetime
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QDialog, QFormLayout, QFileDialog, QProgressBar,
    QMessageBox, QApplication, QSplitter, QTabWidget
)
from PySide6.QtGui import QIcon, QFont, QPixmap

from app.core.db import get_db_connection
from app.core.settings_service import get_setting, set_setting
import app.core.log_service as log_service
from app.core.project_scanner import scan_project, sanitize_folder_name
from app.core.render_queue import RenderQueue
from app.ui.theme import DARK_THEME_STYLE, STATUS_STYLES
from app.core.diagnostics import run_preflight_checks, export_diagnostics_zip, create_demo_project

class FirstRunWizard(QDialog):
    """Step-by-step first run configuration wizard."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asistente de Configuración Inicial - IP Blender Tool")
        self.setMinimumSize(550, 420)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header Title
        title_lbl = QLabel("¡Bienvenido a IP Blender Tool!")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Antes de empezar, necesitamos configurar las rutas principales del sistema. "
            "Esto solo tardará un momento."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        layout.addWidget(desc_lbl)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        form = QFormLayout()
        form.setSpacing(15)

        # 1. Blender Path
        self.blender_edit = QLineEdit(get_setting("blender_path"))
        self.blender_btn = QPushButton("Examinar...")
        self.blender_btn.clicked.connect(self.browse_blender)
        blender_layout = QHBoxLayout()
        blender_layout.addWidget(self.blender_edit)
        blender_layout.addWidget(self.blender_btn)
        form.addRow("Ruta de Blender.exe:", blender_layout)

        # 2. FFmpeg Path
        self.ffmpeg_edit = QLineEdit(get_setting("ffmpeg_path"))
        self.ffmpeg_btn = QPushButton("Examinar...")
        self.ffmpeg_btn.clicked.connect(self.browse_ffmpeg)
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_edit)
        ffmpeg_layout.addWidget(self.ffmpeg_btn)
        form.addRow("Ruta de FFmpeg.exe:", ffmpeg_layout)

        # 3. Projects Root Folder
        self.projects_root_edit = QLineEdit(get_setting("projects_root"))
        self.projects_root_btn = QPushButton("Examinar...")
        self.projects_root_btn.clicked.connect(self.browse_projects_root)
        projects_layout = QHBoxLayout()
        projects_layout.addWidget(self.projects_root_edit)
        projects_layout.addWidget(self.projects_root_btn)
        form.addRow("Carpeta de proyectos:", projects_layout)

        layout.addLayout(form)

        # Spacer
        layout.addStretch()

        # Action buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Salir")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.finish_btn = QPushButton("Completar Configuración")
        self.finish_btn.setObjectName("primaryButton")
        self.finish_btn.clicked.connect(self.finish_configuration)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.finish_btn)
        layout.addLayout(btn_layout)

    def browse_blender(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona Ejecutable de Blender",
            self.blender_edit.text() or "C:\\Program Files\\Blender Foundation",
            "Ejecutables (*.exe);;Todos los archivos (*.*)"
        )
        if path:
            self.blender_edit.setText(os.path.normpath(path))

    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona Ejecutable de FFmpeg",
            self.ffmpeg_edit.text() or "ffmpeg",
            "Ejecutables (*.exe);;Todos los archivos (*.*)"
        )
        if path:
            self.ffmpeg_edit.setText(os.path.normpath(path))

    def browse_projects_root(self):
        path = QFileDialog.getExistingDirectory(
            self, "Selecciona Carpeta de Proyectos",
            self.projects_root_edit.text() or "C:\\"
        )
        if path:
            self.projects_root_edit.setText(os.path.normpath(path))

    def finish_configuration(self):
        blender_path = self.blender_edit.text().strip()
        ffmpeg_path = self.ffmpeg_edit.text().strip()
        projects_root = self.projects_root_edit.text().strip()

        # Validations
        if not blender_path or not os.path.exists(blender_path):
            QMessageBox.warning(
                self, "Blender no encontrado",
                "Por favor, selecciona una ruta válida para blender.exe antes de continuar."
            )
            return

        if not projects_root or not os.path.exists(projects_root):
            QMessageBox.warning(
                self, "Directorio no encontrado",
                "Por favor, selecciona una carpeta de proyectos válida antes de continuar."
            )
            return

        # Save settings
        set_setting("blender_path", blender_path)
        set_setting("ffmpeg_path", ffmpeg_path or "ffmpeg")
        set_setting("projects_root", projects_root)
        set_setting("base_dir", projects_root) # Keep base_dir synced with projects_root for compatibility
        
        # Sync with profiles
        from app.core.settings_service import get_profiles, set_profiles
        profiles = get_profiles()
        if "IP Legacy" in profiles:
            profiles["IP Legacy"]["projects_root"] = projects_root
        if "Manual" in profiles:
            profiles["Manual"]["projects_root"] = projects_root
        set_profiles(profiles)
        
        set_setting("first_run_completed", True)

        self.accept()

class SettingsDialog(QDialog):
    """Configuration popup dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustes del Sistema - IP Blender Tool")
        self.setMinimumWidth(500)
        self.setStyleSheet(DARK_THEME_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # 1. Base Project Directory
        self.base_dir_edit = QLineEdit(get_setting("base_dir"))
        self.base_dir_btn = QPushButton("Examinar...")
        self.base_dir_btn.clicked.connect(self.browse_base_dir)
        
        base_layout = QHBoxLayout()
        base_layout.addWidget(self.base_dir_edit)
        base_layout.addWidget(self.base_dir_btn)
        form.addRow("Carpeta base de proyectos:", base_layout)
        
        # 2. Blender Executable
        self.blender_path_edit = QLineEdit(get_setting("blender_path"))
        self.blender_path_btn = QPushButton("Examinar...")
        self.blender_path_btn.clicked.connect(self.browse_blender)
        
        blender_layout = QHBoxLayout()
        blender_layout.addWidget(self.blender_path_edit)
        blender_layout.addWidget(self.blender_path_btn)
        form.addRow("Ruta de Blender.exe:", blender_layout)
        
        # 3. FFmpeg Executable
        self.ffmpeg_path_edit = QLineEdit(get_setting("ffmpeg_path"))
        self.ffmpeg_path_btn = QPushButton("Examinar...")
        self.ffmpeg_path_btn.clicked.connect(self.browse_ffmpeg)
        
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(self.ffmpeg_path_edit)
        ffmpeg_layout.addWidget(self.ffmpeg_path_btn)
        form.addRow("Ruta de FFmpeg.exe:", ffmpeg_layout)
        
        # 3b. Naming Style
        self.naming_style_combo = QComboBox()
        self.naming_style_combo.addItems(["Profesional (v001)", "Simple (01)"])
        current_style = get_setting("naming_style", "professional")
        if current_style == "simple":
            self.naming_style_combo.setCurrentText("Simple (01)")
        else:
            self.naming_style_combo.setCurrentText("Profesional (v001)")
        form.addRow("Estilo de nombres:", self.naming_style_combo)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        form.addRow(divider)
        
        # 4. Telegram Notifications
        self.tel_enabled_cb = QCheckBox("Activar notificaciones por Telegram")
        self.tel_enabled_cb.setChecked(get_setting("telegram_enabled", "False").lower() == "true")
        form.addRow("", self.tel_enabled_cb)
        
        self.tel_token_edit = QLineEdit(get_setting("telegram_token"))
        form.addRow("Token Bot de Telegram:", self.tel_token_edit)
        
        self.tel_chat_edit = QLineEdit(get_setting("telegram_chat_id"))
        form.addRow("Chat ID de Telegram:", self.tel_chat_edit)
        
        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setFrameShadow(QFrame.Sunken)
        form.addRow(divider2)
        
        # 5. Discord Notifications
        self.disc_enabled_cb = QCheckBox("Activar notificaciones por Discord")
        self.disc_enabled_cb.setChecked(get_setting("discord_enabled", "False").lower() == "true")
        form.addRow("", self.disc_enabled_cb)
        
        self.disc_webhook_edit = QLineEdit(get_setting("discord_webhook"))
        form.addRow("Webhook URL de Discord:", self.disc_webhook_edit)
        
        layout.addLayout(form)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar Ajustes")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addSpacing(15)
        layout.addLayout(btn_layout)

    def browse_base_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Selecciona Carpeta Base de Proyectos", self.base_dir_edit.text())
        if path:
            self.base_dir_edit.setText(os.path.normpath(path))

    def browse_blender(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona Ejecutable de Blender", self.blender_path_edit.text(), "Ejecutables (*.exe);;Todos los archivos (*.*)")
        if path:
            self.blender_path_edit.setText(os.path.normpath(path))

    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona Ejecutable de FFmpeg", self.ffmpeg_path_edit.text(), "Ejecutables (*.exe);;Todos los archivos (*.*)")
        if path:
            self.ffmpeg_path_edit.setText(os.path.normpath(path))

    def save_settings(self):
        set_setting("base_dir", self.base_dir_edit.text())
        set_setting("blender_path", self.blender_path_edit.text())
        set_setting("ffmpeg_path", self.ffmpeg_path_edit.text())
        
        # Save naming style
        selected_style = "professional"
        if self.naming_style_combo.currentText() == "Simple (01)":
            selected_style = "simple"
        set_setting("naming_style", selected_style)
        
        set_setting("telegram_enabled", str(self.tel_enabled_cb.isChecked()))
        set_setting("telegram_token", self.tel_token_edit.text())
        set_setting("telegram_chat_id", self.tel_chat_edit.text())
        set_setting("discord_enabled", str(self.disc_enabled_cb.isChecked()))
        set_setting("discord_webhook", self.disc_webhook_edit.text())
        
        self.accept()


class MainWindow(QMainWindow):
    # Thread-safe log listener signal
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP Blender Tool")
        self.setMinimumSize(950, 750)
        self.setStyleSheet(DARK_THEME_STYLE)
        
        # System status state variables
        self.scanned_project_id = None
        self.scanned_snapshots = []
        self.camera_checkboxes = []  # tuple: (cam_name, blend_path, snapshot_id, main_cb, montage_cb)
        
        # Initialize rendering queue thread
        self.queue_thread = RenderQueue()
        self.queue_thread.job_started.connect(self.on_job_started)
        self.queue_thread.job_progress.connect(self.on_job_progress)
        self.queue_thread.job_log.connect(self.on_job_log)
        self.queue_thread.job_finished.connect(self.on_job_finished)
        self.queue_thread.queue_state_changed.connect(self.on_queue_state_changed)
        
        self.setup_ui()
        self.load_settings()
        
        # Connect log listener to thread-safe signal
        log_service.register_log_listener(self.on_system_log)
        self.log_signal.connect(self.append_log_to_console)
        
        # Load initial queue from SQLite
        self.refresh_queue_table()
        
        # Start queue thread (it will go to Stop/Idle loop until activated)
        self.queue_thread.start()
        
        # Check first run status on startup
        self.check_first_run_status()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header Title Area
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        title_lbl = QLabel("IP Blender Tool")
        title_lbl.setObjectName("headerTitle")
        subtitle_lbl = QLabel("Render Queue & Automation for Blender")
        subtitle_lbl.setObjectName("subtitle")
        title_v.addWidget(title_lbl)
        title_v.addWidget(subtitle_lbl)
        
        settings_btn = QPushButton("⚙ Ajustes")
        settings_btn.clicked.connect(self.open_settings)
        
        header.addLayout(title_v)
        header.addStretch()
        header.addWidget(settings_btn)
        main_layout.addLayout(header)

        # Main Splitter splits Left (Parameters/Checklist) and Right (Queue/Logs)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # ================= LEFT PANEL =================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        # 1. Project Loader with Tabbed Interface
        proj_frame = QFrame()
        proj_frame.setObjectName("sectionFrame")
        proj_layout = QVBoxLayout(proj_frame)
        
        proj_title = QLabel("1. Proyecto a Cargar")
        proj_title.setObjectName("sectionTitle")
        proj_layout.addWidget(proj_title)
        
        self.mode_tab_widget = QTabWidget()
        self.mode_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2d2d34;
                border-radius: 4px;
                background-color: #1a1a1f;
                padding: 5px;
            }
            QTabBar::tab {
                background: #27272a;
                color: #a1a1aa;
                padding: 6px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1a1a1f;
                color: #0da2ff;
                font-weight: bold;
            }
        """)
        
        # TAB 1: Legacy (ID)
        tab_legacy = QWidget()
        tab_legacy_layout = QVBoxLayout(tab_legacy)
        tab_legacy_layout.setContentsMargins(5, 5, 5, 5)
        
        legacy_input_layout = QHBoxLayout()
        self.proj_input = QLineEdit()
        self.proj_input.setPlaceholderText("Ej: 0024")
        self.proj_input.returnPressed.connect(self.scan_project_folder)
        
        self.scan_btn_legacy = QPushButton("🔍 Escanear ID")
        self.scan_btn_legacy.clicked.connect(self.scan_project_folder)
        legacy_input_layout.addWidget(self.proj_input)
        legacy_input_layout.addWidget(self.scan_btn_legacy)
        tab_legacy_layout.addLayout(legacy_input_layout)
        
        self.mode_tab_widget.addTab(tab_legacy, "ID Legacy")
        
        # TAB 2: Carpeta Manual
        tab_folder = QWidget()
        tab_folder_layout = QVBoxLayout(tab_folder)
        tab_folder_layout.setContentsMargins(5, 5, 5, 5)
        
        folder_form = QFormLayout()
        folder_form.setSpacing(6)
        
        self.manual_folder_edit = QLineEdit()
        self.manual_folder_edit.setPlaceholderText("Selecciona carpeta de proyecto...")
        self.manual_folder_btn = QPushButton("Examinar...")
        self.manual_folder_btn.clicked.connect(self.browse_manual_folder)
        
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.manual_folder_edit)
        folder_row.addWidget(self.manual_folder_btn)
        folder_form.addRow("Carpeta:", folder_row)
        
        self.manual_out_edit = QLineEdit()
        self.manual_out_edit.setPlaceholderText("Opcional: carpeta de renders...")
        self.manual_out_btn = QPushButton("Examinar...")
        self.manual_out_btn.clicked.connect(self.browse_manual_out)
        
        out_row = QHBoxLayout()
        out_row.addWidget(self.manual_out_edit)
        out_row.addWidget(self.manual_out_btn)
        folder_form.addRow("Destino:", out_row)
        
        tab_folder_layout.addLayout(folder_form)
        
        self.scan_btn_folder = QPushButton("🔍 Escanear Carpeta")
        self.scan_btn_folder.clicked.connect(self.scan_project_folder)
        tab_folder_layout.addWidget(self.scan_btn_folder)
        
        self.mode_tab_widget.addTab(tab_folder, "Carpeta")
        
        # TAB 3: Archivo Único
        tab_file = QWidget()
        tab_file_layout = QVBoxLayout(tab_file)
        tab_file_layout.setContentsMargins(5, 5, 5, 5)
        
        file_form = QFormLayout()
        file_form.setSpacing(6)
        
        self.single_blend_edit = QLineEdit()
        self.single_blend_edit.setPlaceholderText("Selecciona archivo .blend...")
        self.single_blend_btn = QPushButton("Examinar...")
        self.single_blend_btn.clicked.connect(self.browse_single_blend)
        
        file_row = QHBoxLayout()
        file_row.addWidget(self.single_blend_edit)
        file_row.addWidget(self.single_blend_btn)
        file_form.addRow("Archivo:", file_row)
        
        self.single_out_edit = QLineEdit()
        self.single_out_edit.setPlaceholderText("Opcional: carpeta de renders...")
        self.single_out_btn = QPushButton("Examinar...")
        self.single_out_btn.clicked.connect(self.browse_single_out)
        
        s_out_row = QHBoxLayout()
        s_out_row.addWidget(self.single_out_edit)
        s_out_row.addWidget(self.single_out_btn)
        file_form.addRow("Destino:", s_out_row)
        
        tab_file_layout.addLayout(file_form)
        
        self.scan_btn_file = QPushButton("🔍 Escanear Archivo")
        self.scan_btn_file.clicked.connect(self.scan_project_folder)
        tab_file_layout.addWidget(self.scan_btn_file)
        
        self.mode_tab_widget.addTab(tab_file, "Archivo Blend")
        
        # Connect tab change to update settings active_mode
        self.mode_tab_widget.currentChanged.connect(self.on_mode_tab_changed)
        
        proj_layout.addWidget(self.mode_tab_widget)
        
        self.proj_status_lbl = QLabel("Estado: Ningún proyecto cargado")
        self.proj_status_lbl.setStyleSheet("color: #71717a;")
        proj_layout.addWidget(self.proj_status_lbl)
        
        self.blend_file_lbl = QLabel("Archivo: N/D")
        self.blend_file_lbl.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        self.blend_file_lbl.setWordWrap(True)
        proj_layout.addWidget(self.blend_file_lbl)
        
        left_layout.addWidget(proj_frame)
        
        # 2. Camera Selection Card
        cam_frame = QFrame()
        cam_frame.setObjectName("sectionFrame")
        self.cam_layout = QVBoxLayout(cam_frame)
        
        cam_title = QLabel("2. Cámaras Detectadas")
        cam_title.setObjectName("sectionTitle")
        self.cam_layout.addWidget(cam_title)
        
        self.cam_scroll_widget = QWidget()
        self.cam_scroll_layout = QVBoxLayout(self.cam_scroll_widget)
        self.cam_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.cam_scroll_layout.setSpacing(8)
        
        self.no_cams_lbl = QLabel("Escanea un proyecto para listar las cámaras.")
        self.no_cams_lbl.setStyleSheet("color: #71717a; font-style: italic;")
        self.cam_scroll_layout.addWidget(self.no_cams_lbl)
        
        self.cam_layout.addWidget(self.cam_scroll_widget)
        self.cam_layout.addStretch()
        left_layout.addWidget(cam_frame)
        
        # 3. Output Quality Profile
        quality_frame = QFrame()
        quality_frame.setObjectName("sectionFrame")
        quality_layout = QVBoxLayout(quality_frame)
        
        q_title = QLabel("3. Calidad de Salida")
        q_title.setObjectName("sectionTitle")
        quality_layout.addWidget(q_title)
        
        form_q = QFormLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Borrador", "Cliente", "Final"])
        self.profile_combo.setCurrentText("Cliente")
        form_q.addRow("Perfil de calidad:", self.profile_combo)
        
        self.res_pct_combo = QComboBox()
        self.res_pct_combo.addItems(["50%", "100%", "150%", "200%"])
        self.res_pct_combo.setCurrentText("100%")
        form_q.addRow("Resolución de cámara:", self.res_pct_combo)
        
        quality_layout.addLayout(form_q)
        
        # Add to Queue Button
        self.add_queue_btn = QPushButton("➕ Añadir a Cola")
        self.add_queue_btn.setObjectName("primaryButton")
        self.add_queue_btn.clicked.connect(self.add_selected_to_queue)
        quality_layout.addWidget(self.add_queue_btn)
        
        left_layout.addWidget(quality_frame)
        
        # 4. Diagnostics and Utilities Collapsible Panel
        diag_frame = QFrame()
        diag_frame.setObjectName("sectionFrame")
        diag_layout = QVBoxLayout(diag_frame)
        
        self.diag_toggle_btn = QPushButton("▼ Diagnósticos y Utilidades")
        self.diag_toggle_btn.clicked.connect(self.toggle_diag_visibility)
        diag_layout.addWidget(self.diag_toggle_btn)
        
        self.diag_container = QWidget()
        self.diag_container.setVisible(False)
        diag_c_layout = QVBoxLayout(self.diag_container)
        diag_c_layout.setContentsMargins(0, 5, 0, 0)
        diag_c_layout.setSpacing(8)
        
        self.preflight_btn = QPushButton("🔍 Ejecutar Preflight Checks")
        self.preflight_btn.clicked.connect(self.run_preflight_diagnostics)
        diag_c_layout.addWidget(self.preflight_btn)
        
        self.include_db_chk = QCheckBox("Incluir base de datos (sanitizada)")
        self.include_db_chk.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        diag_c_layout.addWidget(self.include_db_chk)
        
        self.zip_btn = QPushButton("📦 Exportar ZIP de Diagnóstico")
        self.zip_btn.clicked.connect(self.export_diagnostics_zip)
        diag_c_layout.addWidget(self.zip_btn)
        
        self.demo_btn = QPushButton("🎮 Generar Proyecto Demo")
        self.demo_btn.clicked.connect(self.generate_demo_project_ui)
        diag_c_layout.addWidget(self.demo_btn)
        
        diag_layout.addWidget(self.diag_container)
        left_layout.addWidget(diag_frame)
        
        left_layout.addStretch()
        
        main_splitter.addWidget(left_widget)

        # ================= RIGHT PANEL =================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # 4. Render Queue Area
        queue_frame = QFrame()
        queue_frame.setObjectName("sectionFrame")
        queue_layout = QVBoxLayout(queue_frame)
        
        queue_title = QLabel("Cola de Trabajos")
        queue_title.setObjectName("sectionTitle")
        queue_layout.addWidget(queue_title)
        
        # Queue Table
        self.queue_table = QTableWidget(0, 5)
        self.queue_table.setHorizontalHeaderLabels(["Proyecto", "Cámara / Trabajo", "Perfil", "Resolución", "Estado"])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.setAlternatingRowColors(True)
        queue_layout.addWidget(self.queue_table)
        
        # Progress Bar
        self.queue_progress = QProgressBar()
        self.queue_progress.setValue(0)
        self.queue_progress.setVisible(False)
        queue_layout.addWidget(self.queue_progress)
        
        # Queue Controls
        ctrl_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Iniciar Cola")
        self.start_btn.clicked.connect(self.start_render_queue)
        
        self.pause_btn = QPushButton("⏸ Pausar")
        self.pause_btn.clicked.connect(self.pause_render_queue)
        self.pause_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("🛑 Cancelar Actual")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.clicked.connect(self.cancel_current_job)
        self.cancel_btn.setEnabled(False)
        
        self.clear_queue_btn = QPushButton("🗑 Limpiar Cola")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        
        self.open_renders_btn = QPushButton("📂 Renders")
        self.open_renders_btn.clicked.connect(self.open_output_folder)
        
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.pause_btn)
        ctrl_layout.addWidget(self.cancel_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.clear_queue_btn)
        ctrl_layout.addWidget(self.open_renders_btn)
        queue_layout.addLayout(ctrl_layout)
        
        # Action upon completion
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Al finalizar cola:"))
        self.completion_action_combo = QComboBox()
        self.completion_action_combo.addItems(["No hacer nada", "Apagar PC", "Suspender PC"])
        # Connect settings change
        self.completion_action_combo.currentTextChanged.connect(self.on_completion_action_changed)
        action_layout.addWidget(self.completion_action_combo)
        action_layout.addStretch()
        queue_layout.addLayout(action_layout)
        
        right_layout.addWidget(queue_frame)
        
        # Collapsible Console Panel
        console_frame = QFrame()
        console_layout = QVBoxLayout(console_frame)
        console_layout.setContentsMargins(5, 5, 5, 5)
        console_layout.setSpacing(5)
        
        self.console_toggle_btn = QPushButton("▼ Mostrar Consola Técnica")
        self.console_toggle_btn.clicked.connect(self.toggle_console_visibility)
        console_layout.addWidget(self.console_toggle_btn)
        
        self.console_box = QTextEdit()
        self.console_box.setObjectName("consoleBox")
        self.console_box.setReadOnly(True)
        self.console_box.setVisible(False)
        console_layout.addWidget(self.console_box)
        
        right_layout.addWidget(console_frame)
        
        main_splitter.addWidget(right_widget)
        
        # Set initial splitter sizes
        main_splitter.setSizes([320, 630])
        main_layout.addWidget(main_splitter)

    def load_settings(self):
        """Loads non-dialog configuration variables to the widgets."""
        action = get_setting("shutdown_on_complete", "none")
        if action == "shutdown":
            self.completion_action_combo.setCurrentText("Apagar PC")
        elif action == "sleep":
            self.completion_action_combo.setCurrentText("Suspender PC")
        else:
            self.completion_action_combo.setCurrentText("No hacer nada")
            
        active_mode = get_setting("active_mode", "IP_LEGACY")
        modes = ["IP_LEGACY", "MANUAL_FOLDER", "SINGLE_BLEND"]
        if active_mode in modes:
            self.mode_tab_widget.setCurrentIndex(modes.index(active_mode))

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def on_completion_action_changed(self, text):
        if text == "Apagar PC":
            set_setting("shutdown_on_complete", "shutdown")
        elif text == "Suspender PC":
            set_setting("shutdown_on_complete", "sleep")
        else:
            set_setting("shutdown_on_complete", "none")

    def toggle_console_visibility(self):
        is_visible = self.console_box.isVisible()
        self.console_box.setVisible(not is_visible)
        if is_visible:
            self.console_toggle_btn.setText("▼ Mostrar Consola Técnica")
        else:
            self.console_toggle_btn.setText("▲ Ocultar Consola Técnica")

    @Slot(str)
    def on_system_log(self, message):
        """Called from other threads, emits thread-safe signal to GUI."""
        self.log_signal.emit(message)

    @Slot(str)
    def append_log_to_console(self, text):
        self.console_box.append(text)
        # Keep buffer size reasonable
        cursor = self.console_box.textCursor()
        self.console_box.moveCursor(cursor.End)

    def browse_manual_folder(self):
        projects_root = get_setting("projects_root")
        path = QFileDialog.getExistingDirectory(self, "Selecciona Carpeta de Proyecto", projects_root)
        if path:
            self.manual_folder_edit.setText(os.path.normpath(path))
            
    def browse_manual_out(self):
        projects_root = get_setting("projects_root")
        path = QFileDialog.getExistingDirectory(self, "Selecciona Carpeta de Renders Destino", projects_root)
        if path:
            self.manual_out_edit.setText(os.path.normpath(path))
            
    def browse_single_blend(self):
        projects_root = get_setting("projects_root")
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona Archivo Blender", projects_root, "Blender (*.blend)")
        if path:
            self.single_blend_edit.setText(os.path.normpath(path))
            
    def browse_single_out(self):
        projects_root = get_setting("projects_root")
        path = QFileDialog.getExistingDirectory(self, "Selecciona Carpeta de Renders Destino", projects_root)
        if path:
            self.single_out_edit.setText(os.path.normpath(path))
            
    def on_mode_tab_changed(self, index):
        modes = ["IP_LEGACY", "MANUAL_FOLDER", "SINGLE_BLEND"]
        if 0 <= index < len(modes):
            set_setting("active_mode", modes[index])

    def toggle_diag_visibility(self):
        is_visible = self.diag_container.isVisible()
        self.diag_container.setVisible(not is_visible)
        if is_visible:
            self.diag_toggle_btn.setText("▼ Diagnósticos y Utilidades")
        else:
            self.diag_toggle_btn.setText("▲ Ocultar Diagnósticos")

    def run_preflight_diagnostics(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            results = run_preflight_checks()
            QApplication.restoreOverrideCursor()
            
            # Format results nicely for user
            msg = "=== RESULTADOS DEL PRE-FLIGHT ===\n\n"
            
            b = results["blender"]
            msg += f"1. Blender: {'✅ OK' if b['ok'] else '❌ ERROR'}\n"
            msg += f"   Detalle: {b['version']}\n"
            if b['err']:
                msg += f"   Error: {b['err']}\n"
            msg += "\n"
            
            f = results["ffmpeg"]
            msg += f"2. FFmpeg: {'✅ OK' if f['ok'] else '❌ ERROR'}\n"
            msg += f"   Detalle: {f['version']}\n"
            if f['err']:
                msg += f"   Error: {f['err']}\n"
            msg += "\n"
            
            d = results["db"]
            msg += f"3. Base de Datos: {'✅ OK' if d['ok'] else '❌ ERROR'}\n"
            msg += f"   Ruta: {d['path']}\n"
            if d['err']:
                msg += f"   Info: {d['err']}\n"
            msg += "\n"
            
            p = results["permissions"]
            msg += f"4. Permisos de escritura: {'✅ OK' if p['ok'] else '❌ ERROR'}\n"
            if p['err']:
                msg += f"   Error: {p['err']}\n"
            
            QMessageBox.information(self, "Pre-flight Diagnostics", msg)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Error de diagnóstico", f"Error inesperado al ejecutar diagnósticos: {e}")

    def export_diagnostics_zip(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar ZIP de Diagnóstico",
            os.path.expanduser("~/Desktop/ip_blender_tool_diagnostic.zip"),
            "ZIP Files (*.zip)"
        )
        if not path:
            return
            
        QApplication.setOverrideCursor(Qt.WaitCursor)
        success, err = export_diagnostics_zip(path, self.include_db_chk.isChecked())
        QApplication.restoreOverrideCursor()
        
        if success:
            QMessageBox.information(
                self, "Exportación exitosa",
                f"El paquete de diagnóstico se ha exportado correctamente en:\n{path}"
            )
        else:
            QMessageBox.critical(
                self, "Error de exportación",
                f"No se pudo crear el paquete de diagnóstico: {err}"
            )

    def generate_demo_project_ui(self):
        reply = QMessageBox.question(
            self, "Generar Proyecto Demo",
            "¿Deseas generar un proyecto demo en tu carpeta de proyectos?\n"
            "Esto creará una escena Blender básica y archivos de montaje para pruebas.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
            
        QApplication.setOverrideCursor(Qt.WaitCursor)
        success, detail = create_demo_project()
        QApplication.restoreOverrideCursor()
        
        if success:
            if detail == "partial_no_blender":
                QMessageBox.warning(
                    self, "Proyecto Demo Parcial",
                    "Se ha creado la estructura de carpetas del proyecto demo en tu carpeta de proyectos,\n"
                    "pero NO se pudieron generar los archivos .blend de prueba porque no se encontró Blender.\n\n"
                    "Por favor, configura la ruta de Blender en Ajustes y vuelve a intentarlo para generar los archivos."
                )
            else:
                # Set the Legacy tab and populate '0000'
                self.mode_tab_widget.setCurrentIndex(0) # Legacy tab
                self.proj_input.setText("0000")
                self.scan_project_folder()
                QMessageBox.information(
                    self, "Proyecto Demo Creado",
                    f"El proyecto demo se ha creado correctamente en:\n{detail}\n\n"
                    "Se ha cargado automáticamente en el gestor para que puedas probarlo."
                )
        else:
            QMessageBox.critical(
                self, "Error al crear demo",
                f"No se pudo generar el proyecto demo:\n{detail}"
            )

    def scan_project_folder(self):
        index = self.mode_tab_widget.currentIndex()
        
        if index == 0: # Legacy
            identifier = self.proj_input.text().strip()
            mode = "IP_LEGACY"
            custom_output_dir = None
            if not identifier:
                QMessageBox.warning(self, "Proyecto vacío", "Por favor, introduce el número de proyecto.")
                return
        elif index == 1: # Carpeta Manual
            identifier = self.manual_folder_edit.text().strip()
            mode = "MANUAL_FOLDER"
            custom_output_dir = self.manual_out_edit.text().strip() or None
            if not identifier:
                QMessageBox.warning(self, "Ruta vacía", "Por favor, selecciona una carpeta de proyecto.")
                return
        elif index == 2: # Archivo Único
            identifier = self.single_blend_edit.text().strip()
            mode = "SINGLE_BLEND"
            custom_output_dir = self.single_out_edit.text().strip() or None
            if not identifier:
                QMessageBox.warning(self, "Archivo vacío", "Por favor, selecciona un archivo .blend.")
                return
        else:
            return
            
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.proj_status_lbl.setText("Estado: Escaneando...")
        self.proj_status_lbl.setStyleSheet("color: #e4e4e7;")
        
        # Clear camera widget
        for i in reversed(range(self.cam_scroll_layout.count())):
            widget = self.cam_scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.camera_checkboxes.clear()

        try:
            project_id, snapshots = scan_project(identifier, mode=mode, custom_output_dir=custom_output_dir)
            self.scanned_project_id = project_id
            self.scanned_snapshots = snapshots
            
            # Reset Wait Cursor
            QApplication.restoreOverrideCursor()
            
            if not snapshots:
                self.proj_status_lbl.setText("Estado: Error al escanear (.blend no válidos)")
                self.proj_status_lbl.setStyleSheet("color: #ef4444;")
                return

            # Display first project details
            first_snap = snapshots[0]
            
            # Show "Modo Demo / Simulado" if demo project and Blender is missing
            is_demo = (identifier == "0000" or "0000" in identifier)
            from app.core.settings_service import get_setting
            blender_path = get_setting("blender_path")
            blender_exists = blender_path and os.path.exists(blender_path)
            
            if is_demo and not blender_exists:
                self.proj_status_lbl.setText("Estado: Listo (Modo Demo / Simulado)")
                self.proj_status_lbl.setStyleSheet("color: #3b82f6;")  # Soft Blue
            else:
                self.proj_status_lbl.setText(f"Estado: Listo. {len(snapshots)} archivos detectados.")
                self.proj_status_lbl.setStyleSheet("color: #10b981;")  # Green
                
            self.blend_file_lbl.setText(f"Carpeta: {os.path.basename(os.path.dirname(first_snap['blend_file']))}")
            
            # Show warnings if any
            warning_msg = []
            for snap in snapshots:
                if snap.get("missing_assets"):
                    warning_msg.append(f"⚠️ Texturas faltantes en {os.path.basename(snap['blend_file'])}")
            
            if warning_msg:
                self.proj_status_lbl.setText(f"Estado: Listo ({len(warning_msg)} advertencias)")
                self.proj_status_lbl.setStyleSheet("color: #f59e0b;")
                # Append to console
                for warn in warning_msg:
                    log_service.warning(warn, first_snap.get("current_scene", "Scene"))

            # Build camera checkboxes
            for metadata in snapshots:
                blend_path = metadata["blend_path"]
                snapshot_id = metadata["snapshot_id"]
                has_montage_file = bool(metadata.get("montage_path"))
                
                # Check for camera lists
                for camera in metadata["cameras"]:
                    cam_name = camera["name"]
                    is_active = camera["active"]
                    
                    cam_row = QWidget()
                    cam_row_layout = QHBoxLayout(cam_row)
                    cam_row_layout.setContentsMargins(5, 2, 5, 2)
                    
                    # 1. Main check
                    main_cb = QCheckBox(f"{cam_name} ({os.path.basename(blend_path)})")
                    main_cb.setChecked(is_active)  # Check by default if active camera
                    
                    # 2. Montage checkbox
                    montage_cb = QCheckBox("+ Montaje")
                    montage_cb.setChecked(has_montage_file)
                    is_animation = metadata["frame_start"] != metadata["frame_end"]
                    if is_animation:
                        montage_cb.setText("+ Video MP4")
                        montage_cb.setChecked(True)
                    
                    cam_row_layout.addWidget(main_cb, 3)
                    cam_row_layout.addWidget(montage_cb, 1)
                    
                    self.cam_scroll_layout.addWidget(cam_row)
                    self.camera_checkboxes.append((cam_name, blend_path, snapshot_id, main_cb, montage_cb, is_animation))

        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.proj_status_lbl.setText("Estado: Error al escanear")
            self.proj_status_lbl.setStyleSheet("color: #ef4444;")
            self.blend_file_lbl.setText(f"Error: {e}")
            QMessageBox.critical(self, "Error de Ingesta", f"No se pudo cargar el proyecto: {e}")

    def add_selected_to_queue(self):
        if not self.scanned_project_id:
            QMessageBox.warning(self, "Sin proyecto", "Por favor, carga y escanea un proyecto primero.")
            return
            
        selected_count = 0
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read profile and resolution percentage
        profile = self.profile_combo.currentText()
        res_pct = int(self.res_pct_combo.currentText().replace("%", ""))
        
        for cam_name, blend_path, snapshot_id, main_cb, montage_cb, is_animation in self.camera_checkboxes:
            if main_cb.isChecked():
                # Fetch metadata snapshot details
                cursor.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,))
                snapshot = cursor.fetchone()
                
                # Check for framing
                frame_start = snapshot["frame_start"]
                frame_end = snapshot["frame_end"]
                
                # If montage is checked but it's a still, it will render PNG first, then run update_compositor script.
                # If it's an animation, it will render PNG frames, then compile MP4.
                job_type = "SINGLE_CAMERA_STILL"
                if is_animation:
                    job_type = "SINGLE_CAMERA_ANIMATION"
                
                # Render output directory resolved in scanner
                cursor.execute("SELECT output_path FROM projects WHERE id = ?", (self.scanned_project_id,))
                output_root = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO jobs (
                        project_id, snapshot_id, job_type, scene_name, camera_name,
                        frame_start, frame_end, output_root, output_pattern, blend_path,
                        profile, resolution_percent, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.scanned_project_id, snapshot_id, job_type, snapshot["scene_name"], cam_name,
                    frame_start, frame_end, output_root, blend_path, blend_path,
                    profile, res_pct, "Pending"
                ))
                selected_count += 1
                
        conn.commit()
        conn.close()
        
        if selected_count > 0:
            log_service.info(f"Añadidos {selected_count} trabajos a la cola de renders.")
            self.refresh_queue_table()
        else:
            QMessageBox.warning(self, "Selección vacía", "No has marcado ninguna cámara para añadir.")

    def refresh_queue_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.id, p.project_code, j.camera_name, j.profile, j.resolution_percent, j.status
            FROM jobs j
            JOIN projects p ON j.project_id = p.id
            WHERE j.status != 'Completed_Archived' -- Optional archiving
            ORDER BY j.status = 'Running' DESC, j.status = 'Pending' DESC, j.id ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.queue_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.queue_table.insertRow(i)
            
            self.queue_table.setItem(i, 0, QTableWidgetItem(row["project_code"]))
            self.queue_table.setItem(i, 1, QTableWidgetItem(row["camera_name"] or "Timeline"))
            self.queue_table.setItem(i, 2, QTableWidgetItem(row["profile"]))
            self.queue_table.setItem(i, 3, QTableWidgetItem(f"{row['resolution_percent']}%"))
            
            status_item = QTableWidgetItem(row["status"])
            status_style = STATUS_STYLES.get(row["status"], "color: white;")
            status_widget = QLabel(row["status"])
            status_widget.setStyleSheet(status_style + " padding-left: 5px;")
            status_widget.setAlignment(Qt.AlignVCenter)
            self.queue_table.setCellWidget(i, 4, status_widget)

    def start_render_queue(self):
        self.queue_thread.start_queue()

    def pause_render_queue(self):
        self.queue_thread.pause_queue()

    def cancel_current_job(self):
        self.queue_thread.cancel_current_job()

    def clear_queue(self):
        reply = QMessageBox.question(
            self, "Limpiar cola",
            "¿Estás seguro de que quieres borrar todos los trabajos de la cola?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = get_db_connection()
            # Clear jobs that are not Running
            conn.execute("DELETE FROM jobs WHERE status != 'Running'")
            conn.commit()
            conn.close()
            self.refresh_queue_table()

    def open_output_folder(self):
        """Opens the output folder of the currently selected or scanned project."""
        target_dir = get_setting("base_dir")
        if self.scanned_project_id:
            conn = get_db_connection()
            row = conn.execute("SELECT output_path FROM projects WHERE id = ?", (self.scanned_project_id,)).fetchone()
            conn.close()
            if row and os.path.exists(row[0]):
                target_dir = row[0]
                
        os.startfile(target_dir)

    # ================= QUEUE THREAD SLOTS =================
    @Slot(int, str)
    def on_job_started(self, job_id, label):
        self.refresh_queue_table()
        self.queue_progress.setVisible(True)
        self.queue_progress.setValue(0)
        self.queue_progress.setFormat(f"{label}: %p%")

    @Slot(int, int)
    def on_job_progress(self, job_id, percent):
        self.queue_progress.setValue(percent)

    @Slot(int, str)
    def on_job_log(self, job_id, line):
        # We also feed individual job lines to our text area
        pass

    @Slot(int, str, str)
    def on_job_finished(self, job_id, status, output_file):
        self.queue_progress.setVisible(False)
        self.refresh_queue_table()

    @Slot(str)
    def on_queue_state_changed(self, state):
        if state == "Running":
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.clear_queue_btn.setEnabled(False)
        elif state == "Paused":
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶ Reanudar Cola")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.clear_queue_btn.setEnabled(True)
        else: # Stopped
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶ Iniciar Cola")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.clear_queue_btn.setEnabled(True)

    def check_first_run_status(self):
        from app.core.settings_service import get_setting_bool
        completed = get_setting_bool("first_run_completed", False)
        
        # Verify Blender path exists as well
        blender_bin = get_setting("blender_path")
        has_blender = bool(blender_bin and os.path.exists(blender_bin))
        
        if not completed or not has_blender:
            self.scan_btn_legacy.setEnabled(False)
            self.scan_btn_folder.setEnabled(False)
            self.scan_btn_file.setEnabled(False)
            self.add_queue_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.proj_status_lbl.setText("⚠️ Configuración incompleta. Ve a Ajustes.")
            self.proj_status_lbl.setStyleSheet("color: #ef4444; font-weight: bold;")
            return False
        else:
            self.scan_btn_legacy.setEnabled(True)
            self.scan_btn_folder.setEnabled(True)
            self.scan_btn_file.setEnabled(True)
            self.add_queue_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            # Reset status label style to normal
            self.proj_status_lbl.setText("Estado: Listo")
            self.proj_status_lbl.setStyleSheet("color: #10b981;")
            return True

    def showEvent(self, event):
        super().showEvent(event)
        from app.core.settings_service import get_setting_bool
        if not get_setting_bool("first_run_completed", False):
            wizard = FirstRunWizard(self)
            if wizard.exec() == QDialog.Accepted:
                self.check_first_run_status()
                self.load_settings()

    def closeEvent(self, event):
        """Safely shuts down background thread on close."""
        log_service.unregister_log_listener(self.on_system_log)
        self.queue_thread.stop_thread()
        event.accept()
