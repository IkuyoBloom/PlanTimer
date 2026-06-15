import sys
import os
import json
import subprocess
import winsound

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QListWidgetItem,
                             QAbstractButton, QPushButton, QLabel,
                             QMessageBox, QDialog, QLineEdit, QComboBox,
                             QCheckBox, QSpinBox, QFileDialog,
                             QSystemTrayIcon, QMenu, QFrame, QStackedWidget,
                             QProxyStyle, QStyle, QStyleOptionButton)
from PyQt6.QtCore import QTimer, QTime, Qt, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QAction, QFont, QBrush,
                         QPen, QPainterPath)
from datetime import datetime, timedelta


# ==================== 路径配置 ====================

def _get_base_dir():
    """获取应用根目录。

    PyInstaller 打包后 __file__ 指向临时解压目录，改用 sys.executable 定位。
    开发环境（源码运行）则继续使用 __file__。
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller / Nuitka 打包环境
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def ensure_data_dir():
    """确保 data 目录存在，并在首次运行时创建默认配置文件。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'start_to_tray': True}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


# ==================== 全局样式 ====================

STYLESHEET = """
/* ── 全局 ── */
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── 列表 ── */
QListWidget {
    background-color: #252525;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 4px;
    outline: none;
    font-size: 13px;
}
QListWidget::item {
    background-color: #2d2d2d;
    border-radius: 8px;
    margin: 3px 4px;
    padding: 10px 12px;
    color: #d0d0d0;
}
QListWidget::item:hover {
    background-color: #353535;
}
QListWidget::item:selected {
    background-color: #3a3a3a;
    color: #ffffff;
}

/* ── 按钮 ── */
QPushButton {
    background-color: #2d2d2d;
    color: #c0c0c0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #383838;
    border-color: #505050;
}
QPushButton:pressed {
    background-color: #333333;
}
QPushButton#btn_settings {
    background-color: transparent;
    border: 1px solid #3a3a3a;
    color: #888888;
    font-size: 16px;
    padding: 4px 10px;
    border-radius: 6px;
}
QPushButton#btn_settings:hover {
    background-color: #2d2d2d;
    color: #c0c0c0;
}
QPushButton#btn_add {
    background-color: transparent;
    border: 1px solid #3a3a3a;
    color: #ffffff;
    font-size: 13px;
    padding: 5px 14px;
    border-radius: 6px;
}
QPushButton#btn_add:hover {
    background-color: #2d2d2d;
    color: #c0c0c0;
}

/* ── 标签 ── */
QLabel {
    color: #b0b0b0;
}
QLabel#title_label {
    font-size: 18px;
    font-weight: bold;
    color: #e0e0e0;
}
QLabel#clock_label {
    font-size: 13px;
    color: #888888;
    padding-right: 8px;
}
QLabel#empty_hint {
    font-size: 15px;
    color: #555555;
}
QLabel#status_bar_label {
    font-size: 12px;
    color: #777777;
    padding: 6px 12px;
}
QLabel#next_run_label {
    font-size: 12px;
    color: #999999;
    padding: 6px 12px;
}

/* ── 输入框 ── */
QLineEdit, QSpinBox {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e0e0e0;
    selection-background-color: #404040;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: #505050;
}

/* ── 复选框 ── */
QCheckBox {
    color: #c0c0c0;
    spacing: 8px;
}
QCheckBox:disabled {
    color: #555555;
}

/* ── 进度条 ── */
QProgressBar {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #505050;
    border-radius: 4px;
}

/* ── 菜单 ── */
QMenu {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 32px 6px 16px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: #3a3a3a;
}
QMenu::separator {
    height: 1px;
    background-color: #3a3a3a;
    margin: 4px 8px;
}

/* ── 滚动条 ── */
QScrollBar:vertical {
    background: #252525;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3a3a3a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #505050;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── 任务列表自定义项 ── */
QLabel#task_name_label {
    color: #e0e0e0;
}
QLabel#task_meta_label {
    color: #999999;
    font-size: 12px;
}
QLabel#task_stat_label {
    color: #777777;
    font-size: 11px;
}

/* ── 列表项容器调整 ── */
QListWidget::item {
    background-color: #2d2d2d;
    border-radius: 10px;
    margin: 3px 4px;
    padding: 2px 0px;
    color: #d0d0d0;
}
"""


# ==================== 数据模型 ====================

def format_relative_time(dt_str: str) -> str:
    """将 ISO 格式时间字符串转为相对时间显示"""
    if not dt_str:
        return "从未执行"
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        return dt_str
    now = datetime.now()
    delta = now - dt
    if delta.total_seconds() < 0:
        return "刚刚"
    seconds = delta.total_seconds()
    if seconds < 60:
        return "刚刚"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}分钟前"
    hours = minutes // 60
    if hours < 24:
        if dt.date() == now.date():
            return f"今天 {dt.strftime('%H:%M')}"
        yesterday = (now - timedelta(days=1)).date()
        if dt.date() == yesterday:
            return f"昨天 {dt.strftime('%H:%M')}"
        return f"{hours}小时前"
    days = hours // 24
    if days < 7:
        return f"{days}天前"
    return dt.strftime("%m-%d %H:%M")


class Task:
    def __init__(self, id, name, program_path, run_time, enabled=True, repeat_days=None, args="",
                 last_executed=None, execution_count=0, run_once=False,
                 notify_before_seconds=0, notify_sound_enabled=False, notify_sound_path=""):
        self.id = id
        self.name = name
        self.program_path = program_path
        self.run_time = run_time
        self.enabled = enabled
        self.repeat_days = repeat_days if repeat_days else [True] * 7
        self.args = args
        self.last_executed = last_executed
        self.execution_count = execution_count
        self.run_once = run_once
        self.notify_before_seconds = notify_before_seconds
        self.notify_sound_enabled = notify_sound_enabled
        self.notify_sound_path = notify_sound_path

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'program_path': self.program_path,
            'run_time': self.run_time,
            'enabled': self.enabled,
            'repeat_days': self.repeat_days,
            'args': self.args,
            'last_executed': self.last_executed,
            'execution_count': self.execution_count,
            'run_once': self.run_once,
            'notify_before_seconds': self.notify_before_seconds,
            'notify_sound_enabled': self.notify_sound_enabled,
            'notify_sound_path': self.notify_sound_path
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data['id'],
            data['name'],
            data['program_path'],
            data['run_time'],
            data.get('enabled', True),
            data.get('repeat_days', [True] * 7),
            data.get('args', ''),
            data.get('last_executed', None),
            data.get('execution_count', 0),
            data.get('run_once', False),
            data.get('notify_before_seconds', 0),
            data.get('notify_sound_enabled', False),
            data.get('notify_sound_path', '')
        )


class TaskManager:
    def __init__(self):
        self.tasks = []
        self.timers = {}
        self.load_tasks()

    def load_tasks(self):
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []

    def save_tasks(self):
        ensure_data_dir()
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump([task.to_dict() for task in self.tasks], f, ensure_ascii=False, indent=2)

    def add_task(self, task):
        self.tasks.append(task)
        self.save_tasks()

    def update_task(self, task_id, updated_task):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks[i] = updated_task
                break
        self.save_tasks()

    def delete_task(self, task_id):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        if task_id in self.timers:
            self.timers[task_id].stop()
            del self.timers[task_id]
        self.save_tasks()

    def get_task_by_id(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None


# ==================== 设置管理 ====================

class AppSettings:
    """应用设置：静默启动（启动时不显示主窗口，直接进入托盘）"""

    def __init__(self):
        self.start_to_tray = True  # 默认静默启动
        self.load()

    def load(self):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                self.start_to_tray = data.get('start_to_tray', True)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self):
        ensure_data_dir()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'start_to_tray': self.start_to_tray
            }, f, ensure_ascii=False, indent=2)

    def set_start_to_tray(self, enabled: bool):
        self.start_to_tray = enabled
        self.save()


# ==================== 设置对话框 ====================

class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumWidth(320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        self.chk_tray = QCheckBox("启动时最小化到系统托盘")
        self.chk_tray.setChecked(self.settings.start_to_tray)
        layout.addWidget(self.chk_tray)

        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_settings)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def save_settings(self):
        tray = self.chk_tray.isChecked()
        self.settings.set_start_to_tray(tray)
        self.accept()


# ==================== 复选框自定义样式 ====================

class CheckBoxStyle(QProxyStyle):
    """自定义 QCheckBox indicator 绘制：绿色底 + 白色勾号"""

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            opt = option  # QStyleOptionButton
            rect = self.subElementRect(
                QStyle.SubElement.SE_CheckBoxIndicator, opt, widget
            )
            disabled = not (opt.state & QStyle.StateFlag.State_Enabled)

            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 背景
            painter.setPen(Qt.PenStyle.NoPen)
            if opt.state & QStyle.StateFlag.State_On:
                painter.setBrush(QColor("#3a6b3a") if disabled else QColor("#4CAF50"))
            else:
                painter.setBrush(QColor("#1a1a1a") if disabled else QColor("#252525"))
            painter.drawRoundedRect(rect, 4, 4)

            # 边框
            if opt.state & QStyle.StateFlag.State_On:
                painter.setPen(QPen(QColor("#3a6b3a") if disabled else QColor("#4CAF50"), 1))
            else:
                painter.setPen(QPen(QColor("#333333") if disabled else QColor("#505050"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 4, 4)

            # 勾号
            if opt.state & QStyle.StateFlag.State_On:
                pen_color = QColor("#888888") if disabled else QColor("white")
                pen = QPen(pen_color, 2)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                x, y = rect.x(), rect.y()
                w, h = rect.width(), rect.height()
                path = QPainterPath()
                path.moveTo(x + w * 0.2, y + h * 0.5)
                path.lineTo(x + w * 0.45, y + h * 0.75)
                path.lineTo(x + w * 0.8, y + h * 0.3)
                painter.drawPath(path)

            painter.restore()
        else:
            super().drawPrimitive(element, option, painter, widget)


# ==================== iOS 风格无限滚轮 ====================

class InfiniteWheel(QWidget):
    """iOS 风格单列无限滚轮选择器 — 按住拖拽滑动"""

    valueChanged = pyqtSignal(int)

    # 外观常量
    ITEM_HEIGHT = 36
    VISIBLE_COUNT = 5
    WHEEL_WIDTH = 70
    WHEEL_HEIGHT = ITEM_HEIGHT * VISIBLE_COUNT

    def __init__(self, min_val=0, max_val=23, current=0,
                 formatter=None, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.formatter = formatter or (lambda v: f"{v:02d}")

        # ── 拖拽状态 ──
        self._float_value = float(current)   # 连续位置（无界）
        self._pressed = False
        self._start_y = 0.0
        self._start_float = 0.0
        self._last_emitted = self.value      # 上一次发射的整数值

        # ── 松手回弹动画 ──
        self._snap_timer = QTimer(self)
        self._snap_timer.setInterval(16)
        self._snap_timer.timeout.connect(self._tick_snap)
        self._snap_start = 0.0
        self._snap_target = 0.0
        self._snap_t = 0.0
        self._snapping = False

        self.setFixedSize(self.WHEEL_WIDTH, self.WHEEL_HEIGHT)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setMouseTracking(True)

    # ────── 值属性 ──────

    @property
    def value(self) -> int:
        """当前选中整数值（已 wrap）"""
        return self._wrap(int(round(self._float_value)))

    def value_(self) -> int:
        return self.value

    def setValue(self, v, animated=True):
        """设置值为 v（内部转为 float 后如有动画则回弹到该值）"""
        vf = float(v)
        if animated:
            self._animate_to(vf)
        else:
            self._float_value = vf
            self._update_and_emit()
            self.update()

    # ────── 回弹动画 ──────

    def _animate_to(self, target: float):
        self._snap_start = self._float_value
        self._snap_target = target
        self._snap_t = 0.0
        self._snapping = True
        self._snap_timer.start()

    def _tick_snap(self):
        self._snap_t += 0.08
        if self._snap_t >= 1.0:
            self._snap_t = 1.0
            self._float_value = self._snap_target
            self._snapping = False
            self._snap_timer.stop()
        else:
            t = self._snap_t
            eased = 1.0 - (1.0 - t) ** 3  # ease-out cubic
            self._float_value = self._snap_start + (self._snap_target - self._snap_start) * eased
        self._update_and_emit()
        self.update()

    def _update_and_emit(self):
        v = self.value
        if v != self._last_emitted:
            self._last_emitted = v
            self.valueChanged.emit(v)

    # ────── 拖拽事件 ──────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._snap_timer.stop()
            self._snapping = False
            self._start_y = event.position().y()
            self._start_float = self._float_value
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if not self._pressed:
            return
        dy = event.position().y() - self._start_y
        # 上划(鼠标↑)数值增大，下划(鼠标↓)数值减小
        self._float_value = self._start_float - dy / self.ITEM_HEIGHT
        self._update_and_emit()
        self.update()

    def mouseReleaseEvent(self, event):
        if not self._pressed:
            return
        self._pressed = False
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        # 松手回弹到最近整数
        self._animate_to(float(round(self._float_value)))

    # ────── 绘制 ──────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        center_y = h / 2.0

        center_val = round(self._float_value)   # 对齐到整值的"中心值"（无界）
        offset_px = (self._float_value - center_val) * self.ITEM_HEIGHT

        half_visible = self.VISIBLE_COUNT // 2

        for i in range(-half_visible, half_visible + 1):
            raw = center_val + i
            idx = self._wrap(raw)
            text = self.formatter(idx)

            y = center_y + i * self.ITEM_HEIGHT - offset_px
            dist = abs(y - center_y) / self.ITEM_HEIGHT
            if dist > half_visible + 0.5:
                continue

            font_size = max(10, 18 - dist * 3)
            color = QColor("#d0d0d0")
            if dist < 0.5:
                color = QColor("#ffffff")
            elif dist < 1.2:
                color = QColor("#aaaaaa")
            else:
                color = QColor("#666666")

            font = QFont("Microsoft YaHei")
            font.setPointSizeF(font_size)
            p.setFont(font)
            p.setPen(color)

            text_rect = QRectF(0, y - self.ITEM_HEIGHT / 2, w, self.ITEM_HEIGHT)
            p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # 横线分隔
        pen = QPen(QColor("#3a3a3a"), 1)
        p.setPen(pen)
        p.drawLine(0, int(center_y - self.ITEM_HEIGHT / 2), w,
                   int(center_y - self.ITEM_HEIGHT / 2))
        p.drawLine(0, int(center_y + self.ITEM_HEIGHT / 2), w,
                   int(center_y + self.ITEM_HEIGHT / 2))

        p.end()

    def _wrap(self, v: int) -> int:
        r = self.max_val - self.min_val + 1
        return ((v - self.min_val) % r) + self.min_val


class IOSTimePicker(QWidget):
    """iOS 风格三列时间选择器 (时:分:秒)"""

    timeChanged = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        self.hour_wheel = InfiniteWheel(0, 23, 0)
        self.min_wheel = InfiniteWheel(0, 59, 0)
        self.sec_wheel = InfiniteWheel(0, 59, 0)

        for w in (self.hour_wheel, self.min_wheel, self.sec_wheel):
            w.valueChanged.connect(self._on_value_changed)

        sep1 = QLabel(":")
        sep1.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        sep1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep2 = QLabel(":")
        sep2.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        sep2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(self.hour_wheel)
        layout.addWidget(sep1)
        layout.addWidget(self.min_wheel)
        layout.addWidget(sep2)
        layout.addWidget(self.sec_wheel)
        layout.addStretch()

    def _on_value_changed(self, _val):
        self.timeChanged.emit(self.time())

    def time(self) -> QTime:
        return QTime(self.hour_wheel.value,
                     self.min_wheel.value,
                     self.sec_wheel.value)

    def setTime(self, t: QTime):
        for w in (self.hour_wheel, self.min_wheel, self.sec_wheel):
            w._snap_timer.stop()
            w._snapping = False
        self.hour_wheel.setValue(t.hour(), animated=False)
        self.min_wheel.setValue(t.minute(), animated=False)
        self.sec_wheel.setValue(t.second(), animated=False)
        self.update()

    def current_time(self) -> QTime:
        return self.time()


# ==================== 任务编辑对话框 ====================

class TaskEditDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("添加任务" if not task else "编辑任务")
        self.task = task
        self.setMinimumWidth(420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("任务名称")
        layout.addWidget(QLabel("任务名称:"))
        layout.addWidget(self.name_edit)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("程序路径")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_program)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addWidget(QLabel("程序路径:"))
        layout.addLayout(path_layout)

        # 启动参数
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("可选，如 --silent 或 https://example.com")
        layout.addWidget(QLabel("启动参数:"))
        layout.addWidget(self.args_edit)

        self.time_picker = IOSTimePicker()
        layout.addWidget(QLabel("执行时间:"))
        layout.addWidget(self.time_picker)

        days_group = QHBoxLayout()
        self.day_checkboxes = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for day in days:
            cb = QCheckBox(day)
            cb.setChecked(True)
            self.day_checkboxes.append(cb)
            days_group.addWidget(cb)
        layout.addWidget(QLabel("重复日期:"))
        layout.addLayout(days_group)

        sep_run = QFrame()
        sep_run.setFrameShape(QFrame.Shape.HLine)
        sep_run.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(sep_run)

        self.chk_run_once = QCheckBox("单次运行（执行后自动删除）")
        self.chk_run_once.toggled.connect(self._on_run_once_toggled)
        layout.addWidget(self.chk_run_once)

        # ── 提前通知设置 ──
        sep_notify = QFrame()
        sep_notify.setFrameShape(QFrame.Shape.HLine)
        sep_notify.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(sep_notify)

        notify_title = QLabel("提前通知设置")
        notify_title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        layout.addWidget(notify_title)

        # 提前通知时间
        notify_time_layout = QHBoxLayout()
        self.notify_combo = QComboBox()
        notify_options = [
            ("不提前通知", 0),
            ("30秒前", 30),
            ("1分钟前", 60),
            ("2分钟前", 120),
            ("5分钟前", 300),
            ("10分钟前", 600),
            ("15分钟前", 900),
        ]
        for text, sec in notify_options:
            self.notify_combo.addItem(text, sec)
        notify_time_layout.addWidget(QLabel("提前通知:"))
        notify_time_layout.addWidget(self.notify_combo, stretch=1)
        layout.addLayout(notify_time_layout)

        # 提示音开关
        self.chk_notify_sound = QCheckBox("启用提示音")
        self.chk_notify_sound.toggled.connect(self._on_notify_sound_toggled)
        layout.addWidget(self.chk_notify_sound)

        # 提示音文件选择
        sound_path_layout = QHBoxLayout()
        self.sound_path_edit = QLineEdit()
        self.sound_path_edit.setPlaceholderText("选择提示音文件（.wav）")
        self.sound_path_edit.setEnabled(False)
        btn_browse_sound = QPushButton("浏览系统音效\u2026")
        btn_browse_sound.clicked.connect(self.browse_sound)
        btn_browse_sound.setEnabled(False)
        self.btn_browse_sound = btn_browse_sound
        sound_path_layout.addWidget(self.sound_path_edit, stretch=1)
        sound_path_layout.addWidget(btn_browse_sound)
        layout.addLayout(sound_path_layout)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        if self.task:
            self.name_edit.setText(self.task.name)
            self.path_edit.setText(self.task.program_path)
            self.args_edit.setText(self.task.args)
            time_parts = self.task.run_time.split(':')
            self.time_picker.setTime(QTime(int(time_parts[0]), int(time_parts[1]), int(time_parts[2])))
            for i, cb in enumerate(self.day_checkboxes):
                cb.setChecked(self.task.repeat_days[i])
            self.chk_run_once.setChecked(self.task.run_once)
            # 通知设置回填
            for i in range(self.notify_combo.count()):
                if self.notify_combo.itemData(i) == self.task.notify_before_seconds:
                    self.notify_combo.setCurrentIndex(i)
                    break
            self.chk_notify_sound.setChecked(self.task.notify_sound_enabled)
            self.sound_path_edit.setText(self.task.notify_sound_path)

    def browse_program(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择程序", "",
            "可执行/脚本 (*.exe *.py *.pyw *.bat *.cmd *.ps1 *.vbs *.lnk *.jar);;所有文件 (*.*)"
        )
        if file_path:
            self.path_edit.setText(file_path)

    def browse_sound(self):
        """浏览 C:\\Windows\\Media 下的系统提示音文件"""
        media_path = "C:\\Windows\\Media"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择提示音", media_path,
            "音频文件 (*.wav);;所有文件 (*.*)"
        )
        if file_path:
            self.sound_path_edit.setText(file_path)

    def _on_notify_sound_toggled(self, checked: bool):
        self.sound_path_edit.setEnabled(checked)
        self.btn_browse_sound.setEnabled(checked)
        if checked and not self.sound_path_edit.text():
            self.sound_path_edit.setText("C:\\Windows\\Media\\Alarm01.wav")

    def _on_run_once_toggled(self, checked: bool):
        for cb in self.day_checkboxes:
            if checked:
                cb.setChecked(False)
            cb.setEnabled(not checked)

    def get_task_data(self):
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        args = self.args_edit.text().strip()
        run_time = self.time_picker.time().toString("HH:mm:ss")
        # 启用状态由列表中的 toggle 开关控制，这里保持原值或默认启用
        enabled = self.task.enabled if self.task else True
        repeat_days = [cb.isChecked() for cb in self.day_checkboxes]
        run_once = self.chk_run_once.isChecked()

        if not name:
            QMessageBox.warning(self, "警告", "请输入任务名称")
            return None
        if not path:
            QMessageBox.warning(self, "警告", "请选择程序路径")
            return None

        task_id = self.task.id if self.task else str(datetime.now().timestamp())
        notify_before = self.notify_combo.currentData()
        notify_sound_path = self.sound_path_edit.text().strip()
        return Task(task_id, name, path, run_time, enabled, repeat_days, args,
                     run_once=run_once,
                     notify_before_seconds=notify_before,
                     notify_sound_enabled=self.chk_notify_sound.isChecked(),
                     notify_sound_path=notify_sound_path)


class ToggleSwitch(QAbstractButton):
    """iOS 风格滑块开关 —— 自定义绘制轨道 + 圆形滑块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        thumb_d = h - 4           # 滑块直径
        track_h = thumb_d - 4     # 轨道高度
        track_y = (h - track_h) / 2
        track_w = w - 6

        # ── 轨道 ──
        track_rect = QRectF(3, track_y, track_w, track_h)
        painter.setPen(Qt.PenStyle.NoPen)
        if self.isChecked():
            painter.setBrush(QColor("#4CAF50"))
            track_rect = QRectF(0, track_y, w, track_h)
        else:
            painter.setBrush(QColor("#3a3a3a"))
            track_rect = QRectF(0, track_y, w, track_h)
        painter.drawRoundedRect(track_rect, track_h / 2, track_h / 2)

        # ── 滑块 ──
        margin = 2
        if self.isChecked():
            thumb_x = w - thumb_d - margin
        else:
            thumb_x = margin
        thumb_rect = QRectF(thumb_x, 2, thumb_d, thumb_d)
        painter.setBrush(QBrush(QColor("#f0f0f0")))
        painter.drawEllipse(thumb_rect)

        painter.end()

    def hitButton(self, pos):
        return self.rect().contains(pos)


class TaskItemWidget(QWidget):
    """自定义列表项组件：toggle开关 + 任务信息 + 执行统计"""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task_id = task.id
        self.init_ui(task)

    def init_ui(self, task: Task):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # ── 左侧：toggle 开关 ──
        self.toggle_btn = ToggleSwitch()
        self.toggle_btn.setChecked(task.enabled)
        self.toggle_btn.toggled.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

        # ── 中间：任务信息 ──
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        # 第一行：名称 + 时间 + 重复 + 程序
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.name_label = QLabel(task.name)
        self.name_label.setObjectName("task_name_label")
        name_font = self.name_label.font()
        name_font.setPointSize(11)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        row1.addWidget(self.name_label)

        time_label = QLabel(task.run_time)
        time_label.setObjectName("task_meta_label")
        row1.addWidget(time_label)

        day_names_short = ["一", "二", "三", "四", "五", "六", "日"]
        if all(task.repeat_days):
            day_text = "每天"
        elif not any(task.repeat_days):
            day_text = "不重复"
        else:
            active = [day_names_short[i] for i, v in enumerate(task.repeat_days) if v]
            day_text = "周" + "、".join(active)
        day_label = QLabel(day_text)
        day_label.setObjectName("task_meta_label")
        row1.addWidget(day_label)

        prog_name = os.path.basename(task.program_path)
        prog_label = QLabel(prog_name)
        prog_label.setObjectName("task_meta_label")
        row1.addWidget(prog_label)

        if task.args:
            arg_label = QLabel(task.args)
            arg_label.setObjectName("task_meta_label")
            row1.addWidget(arg_label)

        row1.addStretch()
        info_layout.addLayout(row1)

        # 第二行：执行统计
        row2 = QHBoxLayout()
        row2.setSpacing(14)
        row2.setContentsMargins(2, 0, 0, 0)

        self.count_label = QLabel(f"已执行 {task.execution_count} 次")
        self.count_label.setObjectName("task_stat_label")
        row2.addWidget(self.count_label)

        status_note = "" if task.enabled else "  \u00b7  已禁用"
        self.last_label = QLabel(f"最后: {format_relative_time(task.last_executed)}{status_note}")
        self.last_label.setObjectName("task_stat_label")
        row2.addWidget(self.last_label)

        row2.addStretch()
        info_layout.addLayout(row2)

        layout.addLayout(info_layout, stretch=1)

        # 禁用状态的视觉处理
        if not task.enabled:
            self.name_label.setStyleSheet("color: #666666;")

    def _on_toggle(self, checked: bool):
        pass


class TaskDetailDialog(QDialog):
    """任务详情对话框"""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(f"任务详情 \u2014 {task.name}")
        self.setMinimumWidth(460)
        self.setMaximumWidth(560)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel(self.task.name)
        title_font = title.font()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(sep)

        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if all(self.task.repeat_days):
            day_str = "每天"
        elif not any(self.task.repeat_days):
            day_str = "不重复"
        else:
            active = [day_names[i] for i, v in enumerate(self.task.repeat_days) if v]
            day_str = "、".join(active)

        # 通知描述
        if self.task.notify_before_seconds > 0:
            if self.task.notify_before_seconds < 60:
                notify_desc = f"提前 {self.task.notify_before_seconds} 秒通知"
            else:
                notify_desc = f"提前 {self.task.notify_before_seconds // 60} 分钟通知"
            if self.task.notify_sound_enabled and self.task.notify_sound_path:
                notify_desc += "（有提示音）"
            elif self.task.notify_sound_enabled:
                notify_desc += "（提示音文件缺失）"
            else:
                notify_desc += "（无提示音）"
        else:
            notify_desc = "不提前通知"

        fields = [
            ("程序路径", self.task.program_path),
            ("启动参数", self.task.args if self.task.args else "（无）"),
            ("执行时间", self.task.run_time),
            ("重复日期", day_str),
            ("启用状态", "已启用" if self.task.enabled else "已禁用"),
            ("提前通知", notify_desc),
        ]

        for label_text, value_text in fields:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(72)
            lbl.setStyleSheet("color: #888888; font-size: 12px;")
            row.addWidget(lbl)
            val = QLabel(value_text)
            val.setStyleSheet("color: #d0d0d0;")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(sep2)

        stats_title = QLabel("执行统计")
        stats_title.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(stats_title)

        count_label = QLabel(f"累计执行次数：{self.task.execution_count} 次")
        count_label.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(count_label)

        last_label = QLabel(f"上次执行时间：{format_relative_time(self.task.last_executed)}")
        last_label.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(last_label)

        if self.task.last_executed:
            try:
                dt = datetime.fromisoformat(self.task.last_executed)
                abs_label = QLabel(f"（{dt.strftime('%Y-%m-%d %H:%M:%S')}）")
                abs_label.setStyleSheet("color: #777777; font-size: 11px;")
                layout.addWidget(abs_label)
            except ValueError:
                pass

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_edit = QPushButton("编辑任务")
        btn_edit.clicked.connect(lambda: self.done(2))
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)


# ==================== 通知弹窗 ====================

class NotificationSound:
    """播放通知提示音——优先自定义音效，否则用 Windows 默认通知音"""

    @staticmethod
    def play(task: Task):
        if task.notify_sound_enabled and task.notify_sound_path:
            path = task.notify_sound_path
            if os.path.exists(path):
                winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_NOWAIT)
                return
        # 默认 Windows 通知音
        winsound.MessageBeep(winsound.MB_ICONASTERISK)


# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("自动定时器")
        self.setGeometry(100, 100, 860, 620)
        self.setMinimumSize(600, 400)

        self.task_manager = TaskManager()
        self._notified_tasks: set[str] = set()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_tasks)
        self.timer.start(1000)

        app.setStyle(CheckBoxStyle())
        app.setStyleSheet(STYLESHEET)

        self.init_ui()
        self.init_tray()
        self.update_task_list()

    # ────── UI ──────

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer = QVBoxLayout(central_widget)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        # ── 顶部栏 ──
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)

        title = QLabel("自动定时器")
        title.setObjectName("title_label")
        top_bar.addWidget(title)

        top_bar.addStretch()

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("clock_label")
        top_bar.addWidget(self.clock_label)

        btn_add = QPushButton("添加任务")
        btn_add.setObjectName("btn_add")
        btn_add.clicked.connect(self.add_task)
        top_bar.addWidget(btn_add)

        btn_settings = QPushButton("\u2699")
        btn_settings.setObjectName("btn_settings")
        btn_settings.setFixedSize(36, 36)
        btn_settings.setToolTip("设置")
        btn_settings.clicked.connect(self.open_settings)
        top_bar.addWidget(btn_settings)

        outer.addLayout(top_bar)

        # ── 分隔线 ──
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #3a3a3a;")
        outer.addWidget(sep1)

        # ── 任务列表 + 空状态 ──
        self.stack = QStackedWidget()

        # 空状态页
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_hint = QLabel("暂无定时任务\n\n点击下方「添加任务」创建第一个定时任务")
        empty_hint.setObjectName("empty_hint")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_hint)
        self.stack.addWidget(empty_page)  # index 0

        # 列表页
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.on_task_context_menu)
        self.task_list.itemDoubleClicked.connect(self.on_task_double_clicked)
        self.task_list.setMinimumHeight(200)
        self.stack.addWidget(self.task_list)  # index 1

        outer.addWidget(self.stack, stretch=1)

        # ── 底部栏：左下次执行 | 右状态 ──
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 2, 4, 2)

        self.next_run_label = QLabel("下次执行: —")
        self.next_run_label.setObjectName("next_run_label")
        bottom_bar.addWidget(self.next_run_label)

        bottom_bar.addStretch()

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status_bar_label")
        bottom_bar.addWidget(self.status_label)

        outer.addLayout(bottom_bar)

    # ────── 托盘 ──────

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._make_tray_icon())

        tray_menu = QMenu()
        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show_window)
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_show)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setToolTip("自动定时器")
        self.tray_icon.show()

    def _make_tray_icon(self) -> QIcon:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#606060"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.setPen(QColor("#FFFFFF"))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawLine(16, 16, 16, 10)
        painter.drawLine(16, 16, 22, 16)
        painter.end()
        return QIcon(pixmap)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    # ────── 设置 ──────

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()

    # ────── 窗口关闭行为 ──────

    def closeEvent(self, event):
        if self.settings.start_to_tray:
            event.ignore()
            self.hide()
        else:
            self.tray_icon.hide()
            event.accept()

    # ────── 任务列表 ──────

    def update_task_list(self):
        self.task_list.clear()

        if not self.task_manager.tasks:
            self.stack.setCurrentIndex(0)
            self.status_label.setText("暂无任务 — 点击「添加任务」开始")
            return

        self.stack.setCurrentIndex(1)

        for task in self.task_manager.tasks:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, task.id)

            widget = TaskItemWidget(task)
            widget.toggle_btn.toggled.connect(
                lambda checked, tid=task.id: self.on_item_toggled(tid, checked)
            )

            item.setSizeHint(widget.sizeHint() + QSize(0, 6))
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)

    def on_item_toggled(self, task_id: str, enabled: bool):
        task = self.task_manager.get_task_by_id(task_id)
        if task and task.enabled != enabled:
            task.enabled = enabled
            self.task_manager.update_task(task_id, task)
            self.update_task_list()
            if not enabled:
                self._notified_tasks.discard(task_id)
            status = "启用" if enabled else "禁用"
            self.status_label.setText(f"已{status}任务: {task.name}")

    def show_task_detail(self):
        selected = self.task_list.currentItem()
        if not selected:
            return
        task_id = selected.data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if not task:
            return
        dialog = TaskDetailDialog(task, self)
        result = dialog.exec()
        if result == 2:
            self.edit_task()

    def on_task_context_menu(self, pos):
        item = self.task_list.itemAt(pos)
        if not item:
            return
        self.task_list.setCurrentItem(item)

        menu = QMenu(self)
        action_detail = QAction("查看详情", self)
        action_detail.triggered.connect(self.show_task_detail)
        action_edit = QAction("编辑", self)
        action_edit.triggered.connect(self.edit_task)
        action_delete = QAction("删除", self)
        action_delete.triggered.connect(self.delete_task)

        menu.addAction(action_detail)
        menu.addAction(action_edit)
        menu.addSeparator()
        menu.addAction(action_delete)
        menu.exec(self.task_list.mapToGlobal(pos))

    def on_task_double_clicked(self, item):
        if item:
            self.show_task_detail()

    # ────── 任务操作 ──────

    def add_task(self):
        dialog = TaskEditDialog(self)
        if dialog.exec():
            task = dialog.get_task_data()
            if task:
                self.task_manager.add_task(task)
                self.update_task_list()
                self.status_label.setText(f"已添加任务: {task.name}")

    def edit_task(self):
        selected = self.task_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择要编辑的任务")
            return

        task_id = selected.data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            dialog = TaskEditDialog(self, task)
            if dialog.exec():
                updated_task = dialog.get_task_data()
                if updated_task:
                    self.task_manager.update_task(task_id, updated_task)
                    self.update_task_list()
                    self.status_label.setText(f"已更新任务: {updated_task.name}")

    def delete_task(self):
        selected = self.task_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择要删除的任务")
            return

        task_id = selected.data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            reply = QMessageBox.question(self, "确认", f"确定要删除任务 '{task.name}' 吗?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task_id)
                self.update_task_list()
                self.status_label.setText(f"已删除任务: {task.name}")

    def toggle_task(self):
        selected = self.task_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择要操作的任务")
            return

        task_id = selected.data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            task.enabled = not task.enabled
            self.task_manager.update_task(task_id, task)
            self.update_task_list()
            status = "启用" if task.enabled else "禁用"
            self.status_label.setText(f"已{status}任务: {task.name}")

    # ────── 下次执行计算 ──────

    def get_next_run_info(self) -> tuple | None:
        """返回 (任务名, 时间描述) 或 None"""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        today = now.weekday()
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        candidates = []
        for task in self.task_manager.tasks:
            if not task.enabled:
                continue
            for offset in range(8):
                day = (today + offset) % 7
                if task.repeat_days[day]:
                    if offset == 0 and task.run_time > current_time_str:
                        candidates.append((0, task.run_time, task.name))
                        break
                    elif offset > 0:
                        candidates.append((offset, task.run_time, task.name))
                        break

        if not candidates:
            return None

        candidates.sort()
        offset, run_time, name = candidates[0]
        if offset == 0:
            when = f"今天 {run_time}"
        elif offset == 1:
            when = f"明天 {run_time}"
        else:
            target_day = (today + offset) % 7
            when = f"{day_names[target_day]} {run_time}"
        return name, when

    # ────── 定时检查 ──────

    def check_tasks(self):
        now = datetime.now()
        current_time = now.time().strftime("%H:%M:%S")
        current_day = now.weekday()

        self.clock_label.setText(now.strftime("%H:%M:%S"))

        # 清除已过当天执行时间的通知记录（跨天清理）
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        for task_id in list(self._notified_tasks):
            task = self.task_manager.get_task_by_id(task_id)
            if task is None:
                self._notified_tasks.discard(task_id)
                continue
            if not task.repeat_days[current_day]:
                self._notified_tasks.discard(task_id)
                continue
            parts = [int(x) for x in task.run_time.split(":")]
            run_secs = parts[0] * 3600 + parts[1] * 60 + parts[2]
            if current_seconds > run_secs:
                self._notified_tasks.discard(task_id)

        if now.second % 5 == 0:
            result = self.get_next_run_info()
            if result:
                name, when = result
                self.next_run_label.setText(f"下次执行: {name}  —  {when}")
            else:
                self.next_run_label.setText("下次执行: —")

        for task in self.task_manager.tasks:
            if not task.enabled:
                continue
            if not task.repeat_days[current_day]:
                continue
            if task.run_time == current_time:
                self.execute_task(task)
                continue
            # 提前通知检查
            if task.notify_before_seconds > 0 and task.id not in self._notified_tasks:
                parts = [int(x) for x in task.run_time.split(":")]
                run_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                notify_seconds = run_seconds - task.notify_before_seconds
                current_seconds = now.hour * 3600 + now.minute * 60 + now.second
                if notify_seconds >= 0 and notify_seconds <= current_seconds < run_seconds:
                    remaining = run_seconds - current_seconds
                    self._show_task_notification(task, remaining)
                    self._notified_tasks.add(task.id)
                    self.status_label.setText(f"已提醒: {task.name}")

    def _show_task_notification(self, task: Task, remaining: int):
        """使用 Windows 原生托盘气泡通知 + 提示音"""
        # 播放提示音（优先自定义，否则默认 Windows 通知音）
        NotificationSound.play(task)

        # 组装通知文字
        if remaining <= 0:
            time_text = "即将开始执行"
        elif remaining >= 60:
            time_text = f"{remaining // 60} 分 {remaining % 60} 秒后执行"
        else:
            time_text = f"{remaining} 秒后执行"

        self.tray_icon.showMessage("任务提醒", f"「{task.name}」{time_text}", QSystemTrayIcon.MessageIcon.Information, 5000)

    def execute_task(self, task):
        """执行任务。有启动参数时用 subprocess，无参数时用 os.startfile。"""
        self._notified_tasks.discard(task.id)
        try:
            if task.args:
                cmd = f'"{task.program_path}" {task.args}'
                subprocess.Popen(cmd, shell=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW
                                 if sys.platform == 'win32' else 0)
            else:
                os.startfile(task.program_path)
            # 记录执行
            task.last_executed = datetime.now().isoformat()
            task.execution_count += 1
            if task.run_once:
                self.task_manager.delete_task(task.id)
                self.update_task_list()
                self.status_label.setText(f"已执行并删除: {task.name}")
            else:
                self.task_manager.update_task(task.id, task)
                self.status_label.setText(f"已执行: {task.name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行任务失败: {str(e)}")


# ==================== 入口 ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 关键: 防止隐藏窗口时应用退出（托盘应用必须设置）
    app.setQuitOnLastWindowClosed(False)

    ensure_data_dir()
    app_settings = AppSettings()

    window = MainWindow(app_settings)

    if not app_settings.start_to_tray:
        window.show()

    sys.exit(app.exec())