import sys
import math
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSlider,
    QGroupBox,
    QFormLayout
)


class SimulationWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.v0 = 25.0
        self.angle_deg = 60.0
        self.angle_rad = math.radians(self.angle_deg)
        self.g = 9.81

        self.target_t = 1.70
        self.t = 0.0
        self.dt = 0.01
        self.t_max = 40.0

        self.scale = 12.0

        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

        self.time_changed_callback = None
        self.info_changed_callback = None

        self.setMinimumSize(1000, 650)

    def set_scale(self, value):
        self.scale = float(value)
        self.update()

    def set_time_from_slider(self, slider_value):
        self.pause()
        self.t = self.t_max * slider_value / 1000.0
        self.update_callbacks()
        self.update()

    def start(self):
        self.timer.start(16)

    def pause(self):
        self.timer.stop()

    def reset(self):
        self.pause()
        self.t = 0.0
        self.update_callbacks()
        self.update()

    def step(self):
        self.t += self.dt

        if self.t > self.t_max:
            self.t = self.t_max
            self.pause()

        self.update_callbacks()
        self.update()

    def update_callbacks(self):
        if self.time_changed_callback is not None:
            slider_value = int(1000.0 * self.t / self.t_max)
            self.time_changed_callback(slider_value)

        if self.info_changed_callback is not None:
            self.info_changed_callback(self.make_info_text())

    def body1_state(self, t):
        x = 0.0
        y = self.v0 * t - 0.5 * self.g * t * t

        vx = 0.0
        vy = self.v0 - self.g * t

        return x, y, vx, vy

    def body2_state(self, t):
        vx0 = self.v0 * math.cos(self.angle_rad)
        vy0 = self.v0 * math.sin(self.angle_rad)

        x = vx0 * t
        y = vy0 * t - 0.5 * self.g * t * t

        vx = vx0
        vy = vy0 - self.g * t

        return x, y, vx, vy

    def distance_between_bodies(self, t):
        x1, y1, _, _ = self.body1_state(t)
        x2, y2, _, _ = self.body2_state(t)

        dx = x2 - x1
        dy = y2 - y1

        return math.sqrt(dx * dx + dy * dy)

    def make_info_text(self):
        x1, y1, vx1, vy1 = self.body1_state(self.t)
        x2, y2, vx2, vy2 = self.body2_state(self.t)

        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)

        target_distance = self.distance_between_bodies(self.target_t)

        return (
            f"t = {self.t:.3f} с\n"
            f"Масштаб = {self.scale:.1f} px/м\n\n"
            f"Тело 1, вертикальный бросок:\n"
            f"x1 = {x1:.3f} м\n"
            f"y1 = {y1:.3f} м\n"
            f"vx1 = {vx1:.3f} м/с\n"
            f"vy1 = {vy1:.3f} м/с\n\n"
            f"Тело 2, бросок под углом 60°:\n"
            f"x2 = {x2:.3f} м\n"
            f"y2 = {y2:.3f} м\n"
            f"vx2 = {vx2:.3f} м/с\n"
            f"vy2 = {vy2:.3f} м/с\n\n"
            f"Относительное положение:\n"
            f"Δx = x2 - x1 = {dx:.3f} м\n"
            f"Δy = y2 - y1 = {dy:.3f} м\n"
            f"S = sqrt(Δx² + Δy²) = {distance:.3f} м\n\n"
            f"Ответ задачи при t = 1.70 с:\n"
            f"S(1.70) = {target_distance:.3f} м"
        )

    def world_to_screen(self, x, y):
        origin_x = 120
        origin_y = self.height() - 90

        screen_x = origin_x + x * self.scale
        screen_y = origin_y - y * self.scale

        return QPointF(screen_x, screen_y)

    def draw_arrow(self, painter, start, vx, vy, color):
        arrow_scale = 0.55

        end = QPointF(
            start.x() + vx * arrow_scale,
            start.y() - vy * arrow_scale
        )

        painter.setPen(QPen(color, 3))
        painter.drawLine(start, end)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

        ux = dx / length
        uy = dy / length

        size = 12

        left = QPointF(
            end.x() - size * ux - size * 0.45 * uy,
            end.y() - size * uy + size * 0.45 * ux
        )

        right = QPointF(
            end.x() - size * ux + size * 0.45 * uy,
            end.y() - size * uy - size * 0.45 * ux
        )

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygonF([end, left, right]))

    def draw_trajectory(self, painter, state_function, max_t, color):
        painter.setPen(QPen(color, 2))

        previous_point = None
        steps = 180

        for i in range(steps + 1):
            t = max_t * i / steps
            x, y, _, _ = state_function(t)
            point = self.world_to_screen(x, y)

            if previous_point is not None:
                painter.drawLine(previous_point, point)

            previous_point = point

    def draw_distance_label(self, painter, p1, p2, distance):
        painter.setPen(QPen(QColor(140, 255, 160), 3))
        painter.drawLine(p1, p2)

        mid_x = (p1.x() + p2.x()) / 2.0
        mid_y = (p1.y() + p2.y()) / 2.0

        text = f"S = {distance:.3f} м"

        painter.setFont(QFont("Arial", 12, QFont.Bold))

        box_width = 130
        box_height = 28
        box_x = mid_x - box_width / 2.0
        box_y = mid_y - box_height - 8

        painter.setBrush(QBrush(QColor(35, 45, 38)))
        painter.setPen(QPen(QColor(140, 255, 160), 2))
        painter.drawRoundedRect(box_x, box_y, box_width, box_height, 8, 8)

        painter.setPen(QColor(220, 255, 225))
        painter.drawText(
            int(box_x),
            int(box_y),
            box_width,
            box_height,
            Qt.AlignCenter,
            text
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(25, 25, 30))

        origin = self.world_to_screen(0, 0)

        painter.setPen(QPen(QColor(120, 120, 130), 1))
        painter.drawLine(50, origin.y(), self.width() - 50, origin.y())
        painter.drawLine(origin.x(), 50, origin.x(), self.height() - 50)

        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.setPen(QColor(240, 240, 240))
        painter.drawText(40, 35, "Задача 1.10: расстояние между двумя телами")

        self.draw_trajectory(painter, self.body1_state, self.t, QColor(90, 180, 255))
        self.draw_trajectory(painter, self.body2_state, self.t, QColor(255, 190, 90))

        x1, y1, vx1, vy1 = self.body1_state(self.t)
        x2, y2, vx2, vy2 = self.body2_state(self.t)

        p1 = self.world_to_screen(x1, y1)
        p2 = self.world_to_screen(x2, y2)

        current_distance = self.distance_between_bodies(self.t)

        self.draw_distance_label(painter, p1, p2, current_distance)

        painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(QColor(90, 180, 255)))
        painter.drawEllipse(p1, 11, 11)

        painter.setBrush(QBrush(QColor(255, 190, 90)))
        painter.drawEllipse(p2, 11, 11)

        self.draw_arrow(painter, p1, vx1, vy1, QColor(100, 220, 255))
        self.draw_arrow(painter, p2, vx2, vy2, QColor(255, 220, 100))

        target_x1, target_y1, _, _ = self.body1_state(self.target_t)
        target_x2, target_y2, _, _ = self.body2_state(self.target_t)

        target_p1 = self.world_to_screen(target_x1, target_y1)
        target_p2 = self.world_to_screen(target_x2, target_y2)

        painter.setPen(QPen(QColor(120, 255, 140), 2, Qt.DashLine))
        painter.drawLine(target_p1, target_p2)

        painter.setBrush(QBrush(QColor(120, 255, 140)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(target_p1, 5, 5)
        painter.drawEllipse(target_p2, 5, 5)

        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor(160, 255, 170))
        painter.drawText(target_p2 + QPointF(10, -10), "положение при t = 1.70 с")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Симуляция задачи 1.10 на PySide6")

        self.simulation = SimulationWidget()

        self.info_label = QLabel(self.simulation.make_info_text())
        self.info_label.setFont(QFont("Consolas", 11))
        self.info_label.setMinimumWidth(330)
        self.info_label.setAlignment(Qt.AlignTop)

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000)
        self.time_slider.setValue(0)

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(4)
        self.scale_slider.setMaximum(30)
        self.scale_slider.setValue(int(self.simulation.scale))

        self.time_value_label = QLabel("0.000 с")
        self.scale_value_label = QLabel(f"{self.simulation.scale:.1f} px/м")

        self.time_slider.valueChanged.connect(self.on_time_slider_changed)
        self.scale_slider.valueChanged.connect(self.on_scale_slider_changed)

        self.simulation.time_changed_callback = self.sync_time_slider
        self.simulation.info_changed_callback = self.update_info_label

        start_button = QPushButton("Старт")
        pause_button = QPushButton("Пауза")
        reset_button = QPushButton("Сброс")

        start_button.clicked.connect(self.simulation.start)
        pause_button.clicked.connect(self.simulation.pause)
        reset_button.clicked.connect(self.simulation.reset)

        controls_box = QGroupBox("Управление")
        controls_layout = QFormLayout()

        controls_layout.addRow("Время:", self.time_slider)
        controls_layout.addRow("Текущее t:", self.time_value_label)
        controls_layout.addRow("Масштаб:", self.scale_slider)
        controls_layout.addRow("Текущий масштаб:", self.scale_value_label)

        controls_box.setLayout(controls_layout)

        buttons = QHBoxLayout()
        buttons.addWidget(start_button)
        buttons.addWidget(pause_button)
        buttons.addWidget(reset_button)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.simulation)
        left_layout.addWidget(controls_box)
        left_layout.addLayout(buttons)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.info_label)

        self.setLayout(main_layout)

    def sync_time_slider(self, slider_value):
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(slider_value)
        self.time_slider.blockSignals(False)

        current_t = self.simulation.t
        self.time_value_label.setText(f"{current_t:.3f} с")

    def update_info_label(self, text):
        self.info_label.setText(text)

    def on_time_slider_changed(self, value):
        self.simulation.set_time_from_slider(value)
        self.time_value_label.setText(f"{self.simulation.t:.3f} с")
        self.info_label.setText(self.simulation.make_info_text())

    def on_scale_slider_changed(self, value):
        self.simulation.set_scale(value)
        self.scale_value_label.setText(f"{self.simulation.scale:.1f} px/м")
        self.info_label.setText(self.simulation.make_info_text())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1400, 780)
    window.show()

    sys.exit(app.exec())