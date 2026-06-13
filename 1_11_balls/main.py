import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QPointF


class SimulationWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.v1 = 3.0
        self.v2 = 4.0
        self.g = 9.81

        self.t = 0.0
        self.dt = 0.01
        self.running = False

        self.t_perp = math.sqrt(self.v1 * self.v2) / self.g
        self.distance_perp = (self.v1 + self.v2) * self.t_perp

        self.t_max = self.t_perp * 1.8

        self.margin = 70
        self.scale = 120

        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

        self.setMinimumSize(900, 600)

    def start(self):
        self.running = True
        self.timer.start(16)

    def pause(self):
        self.running = False
        self.timer.stop()

    def reset(self):
        self.pause()
        self.t = 0.0
        self.update()

    def step(self):
        self.t += self.dt
        if self.t > self.t_max:
            self.t = 0.0
        self.update()

    def physics_state(self, t):
        x1 = self.v1 * t
        y1 = -0.5 * self.g * t * t

        x2 = -self.v2 * t
        y2 = -0.5 * self.g * t * t

        u1x = self.v1
        u1y = -self.g * t

        u2x = -self.v2
        u2y = -self.g * t

        dot = u1x * u2x + u1y * u2y
        distance = abs(x1 - x2)

        return x1, y1, x2, y2, u1x, u1y, u2x, u2y, dot, distance

    def world_to_screen(self, x, y):
        center_x = self.width() / 2
        top_y = 120

        screen_x = center_x + x * self.scale
        screen_y = top_y - y * self.scale

        return QPointF(screen_x, screen_y)

    def draw_arrow(self, painter, start, vector_x, vector_y, color):
        length_scale = 16

        end = QPointF(
            start.x() + vector_x * length_scale,
            start.y() - vector_y * length_scale
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

        arrow_size = 12

        left = QPointF(
            end.x() - arrow_size * ux - arrow_size * 0.45 * uy,
            end.y() - arrow_size * uy + arrow_size * 0.45 * ux
        )

        right = QPointF(
            end.x() - arrow_size * ux + arrow_size * 0.45 * uy,
            end.y() - arrow_size * uy - arrow_size * 0.45 * ux
        )

        painter.setBrush(QBrush(color))
        painter.drawPolygon(QPolygonF([end, left, right]))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(25, 25, 30))

        axis_pen = QPen(QColor(110, 110, 120), 1)
        painter.setPen(axis_pen)

        origin = self.world_to_screen(0, 0)

        painter.drawLine(40, origin.y(), self.width() - 40, origin.y())
        painter.drawLine(origin.x(), 60, origin.x(), self.height() - 80)

        painter.setFont(QFont("Arial", 11))
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(20, 35, "Симуляция: два шарика брошены горизонтально в противоположные стороны")

        x1, y1, x2, y2, u1x, u1y, u2x, u2y, dot, distance = self.physics_state(self.t)

        painter.setPen(QPen(QColor(80, 170, 255), 2))
        previous = None
        steps = 120
        for i in range(steps + 1):
            t = self.t * i / steps
            tx1, ty1, *_ = self.physics_state(t)
            point = self.world_to_screen(tx1, ty1)
            if previous is not None:
                painter.drawLine(previous, point)
            previous = point

        painter.setPen(QPen(QColor(255, 180, 80), 2))
        previous = None
        for i in range(steps + 1):
            t = self.t * i / steps
            _, _, tx2, ty2, *_ = self.physics_state(t)
            point = self.world_to_screen(tx2, ty2)
            if previous is not None:
                painter.drawLine(previous, point)
            previous = point

        p1 = self.world_to_screen(x1, y1)
        p2 = self.world_to_screen(x2, y2)

        painter.setBrush(QBrush(QColor(80, 170, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(p1, 12, 12)

        painter.setBrush(QBrush(QColor(255, 180, 80)))
        painter.drawEllipse(p2, 12, 12)

        self.draw_arrow(painter, p1, u1x, u1y, QColor(80, 220, 255))
        self.draw_arrow(painter, p2, u2x, u2y, QColor(255, 210, 80))

        if abs(self.t - self.t_perp) < 0.015:
            painter.setPen(QPen(QColor(100, 255, 130), 3))
            painter.drawLine(p1, p2)

            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.setPen(QColor(100, 255, 130))
            painter.drawText(40, self.height() - 45, "Скорости сейчас взаимно перпендикулярны")

        perp_x1, perp_y1, perp_x2, perp_y2, *_ = self.physics_state(self.t_perp)
        pp1 = self.world_to_screen(perp_x1, perp_y1)
        pp2 = self.world_to_screen(perp_x2, perp_y2)

        painter.setPen(QPen(QColor(100, 255, 130), 1, Qt.DashLine))
        painter.drawLine(pp1, pp2)

        painter.setBrush(QBrush(QColor(100, 255, 130)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(pp1, 5, 5)
        painter.drawEllipse(pp2, 5, 5)

        painter.setFont(QFont("Consolas", 12))
        painter.setPen(QColor(240, 240, 240))

        text = (
            f"t = {self.t:.3f} с\n"
            f"v₁ = ({u1x:.2f}, {u1y:.2f}) м/с\n"
            f"v₂ = ({u2x:.2f}, {u2y:.2f}) м/с\n"
            f"v₁·v₂ = {dot:.3f}\n"
            f"S(t) = {distance:.3f} м\n\n"
            f"t⊥ = sqrt(v₁·v₂) / g = {self.t_perp:.4f} с\n"
            f"S⊥ = (v₁ + v₂)t⊥ = {self.distance_perp:.4f} м"
        )

        painter.drawText(40, 70, text)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Два шарика: симуляция на PySide6")

        self.simulation = SimulationWidget()

        self.info_label = QLabel(
            "Первый шарик летит вправо со скоростью 3 м/с, второй — влево со скоростью 4 м/с. "
            "Вертикальная скорость у обоих появляется из-за одного и того же ускорения g."
        )

        self.info_label.setWordWrap(True)

        self.start_button = QPushButton("Старт")
        self.pause_button = QPushButton("Пауза")
        self.reset_button = QPushButton("Сброс")

        self.start_button.clicked.connect(self.simulation.start)
        self.pause_button.clicked.connect(self.simulation.pause)
        self.reset_button.clicked.connect(self.simulation.reset)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.reset_button)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.simulation)
        layout.addLayout(buttons)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1000, 750)
    window.show()

    sys.exit(app.exec())