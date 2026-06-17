import sys
import math
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QSlider,
    QGroupBox,
    QFormLayout,
)


class PursuitCanvas(QWidget):
    def __init__(self):
        super().__init__()

        self.v = 2.0
        self.u = 1.0
        self.l = 5.0
        self.dt = 0.01
        self.scale = 70.0

        self.is_running = False
        self.finished = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)

        self.setMinimumSize(900, 650)
        self.reset_simulation()

    def reset_simulation(self):
        self.t = 0.0

        self.Ax = 0.0
        self.Ay = 0.0

        self.Bx = 0.0
        self.By = self.l

        self.path_A = [(self.Ax, self.Ay)]
        self.path_B = [(self.Bx, self.By)]

        self.meeting_distance = 0.02
        self.finished = False

        self.update()

    def set_parameters(self, v, u, l):
        self.pause()

        self.v = float(v)
        self.u = float(u)
        self.l = float(l)

        self.reset_simulation()

    def set_scale_value(self, scale):
        self.scale = float(scale)
        self.update()

    def start(self):
        if self.u >= self.v:
            self.is_running = False
            self.timer.stop()
            self.update()
            return

        if not self.finished:
            self.is_running = True
            self.timer.start(16)

    def pause(self):
        self.is_running = False
        self.timer.stop()

    def step(self):
        if self.finished:
            self.pause()
            return

        dx = self.Bx - self.Ax
        dy = self.By - self.Ay
        distance = math.hypot(dx, dy)

        if distance <= self.meeting_distance:
            self.finished = True
            self.pause()
            self.update()
            return

        direction_x = dx / distance
        direction_y = dy / distance

        velocity_A_x = self.v * direction_x
        velocity_A_y = self.v * direction_y

        velocity_B_x = self.u
        velocity_B_y = 0.0

        self.Ax += velocity_A_x * self.dt
        self.Ay += velocity_A_y * self.dt

        self.Bx += velocity_B_x * self.dt
        self.By += velocity_B_y * self.dt

        self.t += self.dt

        self.path_A.append((self.Ax, self.Ay))
        self.path_B.append((self.Bx, self.By))

        self.update()

    def world_to_screen(self, x, y):
        center_x = self.width() * 0.5
        center_y = self.height() * 0.58

        screen_x = center_x + x * self.scale
        screen_y = center_y - y * self.scale

        return QPointF(screen_x, screen_y)

    def draw_grid(self, painter):
        center = self.world_to_screen(0.0, 0.0)

        painter.setPen(QPen(QColor(220, 220, 220), 1))

        step_screen = self.scale

        x = center.x()
        while x < self.width():
            painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
            x += step_screen

        x = center.x() - step_screen
        while x > 0:
            painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
            x -= step_screen

        y = center.y()
        while y < self.height():
            painter.drawLine(QPointF(0, y), QPointF(self.width(), y))
            y += step_screen

        y = center.y() - step_screen
        while y > 0:
            painter.drawLine(QPointF(0, y), QPointF(self.width(), y))
            y -= step_screen

        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawLine(QPointF(0, center.y()), QPointF(self.width(), center.y()))
        painter.drawLine(QPointF(center.x(), 0), QPointF(center.x(), self.height()))

    def draw_polyline(self, painter, points, color, width):
        if len(points) < 2:
            return

        painter.setPen(QPen(color, width))

        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            painter.drawLine(self.world_to_screen(x1, y1), self.world_to_screen(x2, y2))

    def draw_arrow(self, painter, start_x, start_y, vector_x, vector_y, color, label):
        arrow_factor = 0.55

        start = self.world_to_screen(start_x, start_y)
        end = self.world_to_screen(
            start_x + vector_x * arrow_factor,
            start_y + vector_y * arrow_factor,
        )

        painter.setPen(QPen(color, 3))
        painter.drawLine(start, end)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.hypot(dx, dy)

        if length < 1e-9:
            return

        ux = dx / length
        uy = dy / length

        head_len = 14.0
        head_width = 7.0

        left = QPointF(
            end.x() - head_len * ux + head_width * uy,
            end.y() - head_len * uy - head_width * ux,
        )

        right = QPointF(
            end.x() - head_len * ux - head_width * uy,
            end.y() - head_len * uy + head_width * ux,
        )

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1))
        painter.drawPolygon(QPolygonF([end, left, right]))

        painter.setPen(QPen(color, 2))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(QPointF(end.x() + 8, end.y() - 8), label)

    def draw_info_panel(self, painter, distance):
        panel = QRectF(15, 15, 390, 150)

        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.drawRoundedRect(panel, 10, 10)

        painter.setPen(QPen(QColor(30, 30, 30)))
        painter.setFont(QFont("Arial", 11))

        if self.u < self.v:
            theory_time = self.l * self.v / (self.v * self.v - self.u * self.u)
            theory_text = f"T theory = {theory_time:.4f}"
        else:
            theory_text = "T theory does not exist for u >= v"

        status = "finished" if self.finished else ("running" if self.is_running else "paused")

        lines = [
            f"status = {status}",
            f"t = {self.t:.4f}",
            f"|AB| = {distance:.4f}",
            f"v = {self.v:.4f}, u = {self.u:.4f}, l = {self.l:.4f}",
            theory_text,
            "A's velocity is always aimed at current B",
        ]

        y = 40
        for line in lines:
            painter.drawText(30, y, line)
            y += 20

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(245, 246, 250))

        self.draw_grid(painter)

        self.draw_polyline(painter, self.path_A, QColor(30, 100, 220), 3)
        self.draw_polyline(painter, self.path_B, QColor(220, 120, 30), 3)

        A_screen = self.world_to_screen(self.Ax, self.Ay)
        B_screen = self.world_to_screen(self.Bx, self.By)

        painter.setPen(QPen(QColor(70, 70, 70), 2, Qt.DashLine))
        painter.drawLine(A_screen, B_screen)

        painter.setBrush(QBrush(QColor(30, 100, 220)))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(A_screen, 8, 8)

        painter.setBrush(QBrush(QColor(220, 120, 30)))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(B_screen, 8, 8)

        painter.setFont(QFont("Arial", 12, QFont.Bold))

        painter.setPen(QPen(QColor(30, 100, 220)))
        painter.drawText(QPointF(A_screen.x() + 10, A_screen.y() - 10), "A")

        painter.setPen(QPen(QColor(220, 120, 30)))
        painter.drawText(QPointF(B_screen.x() + 10, B_screen.y() - 10), "B")

        dx = self.Bx - self.Ax
        dy = self.By - self.Ay
        distance = math.hypot(dx, dy)

        if distance > 1e-9:
            velocity_A_x = self.v * dx / distance
            velocity_A_y = self.v * dy / distance
        else:
            velocity_A_x = 0.0
            velocity_A_y = 0.0

        self.draw_arrow(
            painter,
            self.Ax,
            self.Ay,
            velocity_A_x,
            velocity_A_y,
            QColor(30, 100, 220),
            "v_A",
        )

        self.draw_arrow(
            painter,
            self.Bx,
            self.By,
            self.u,
            0.0,
            QColor(220, 120, 30),
            "u_B",
        )

        self.draw_info_panel(painter, distance)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pursuit simulation: A aims at B")

        self.canvas = PursuitCanvas()

        self.v_spin = QDoubleSpinBox()
        self.v_spin.setRange(0.1, 20.0)
        self.v_spin.setSingleStep(0.1)
        self.v_spin.setValue(2.0)

        self.u_spin = QDoubleSpinBox()
        self.u_spin.setRange(0.0, 19.9)
        self.u_spin.setSingleStep(0.1)
        self.u_spin.setValue(1.0)

        self.l_spin = QDoubleSpinBox()
        self.l_spin.setRange(0.1, 100.0)
        self.l_spin.setSingleStep(0.5)
        self.l_spin.setValue(5.0)

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(20, 180)
        self.scale_slider.setValue(70)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply parameters")

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #aa0000;")

        self.start_button.clicked.connect(self.canvas.start)
        self.pause_button.clicked.connect(self.canvas.pause)
        self.reset_button.clicked.connect(self.canvas.reset_simulation)
        self.apply_button.clicked.connect(self.apply_parameters)
        self.scale_slider.valueChanged.connect(self.canvas.set_scale_value)

        controls_group = QGroupBox("Controls")
        form = QFormLayout()
        form.addRow("v: speed of A", self.v_spin)
        form.addRow("u: speed of B", self.u_spin)
        form.addRow("l: initial distance", self.l_spin)
        form.addRow("Scale", self.scale_slider)
        controls_group.setLayout(form)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addWidget(self.apply_button)

        explanation = QLabel(
            "Initial state: A = (0, 0), B = (0, l). "
            "B moves right with speed u. "
            "A moves with constant speed v, and its velocity vector is always aimed at B."
        )
        explanation.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(explanation)
        layout.addWidget(controls_group)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.message_label)

        central = QWidget()
        central.setLayout(layout)

        self.setCentralWidget(central)

    def apply_parameters(self):
        v = self.v_spin.value()
        u = self.u_spin.value()
        l = self.l_spin.value()

        if u >= v:
            self.message_label.setText("Ошибка параметров: нужно u < v, иначе точка A не догоняет точку B.")
            self.canvas.pause()
            return

        self.message_label.setText("")
        self.canvas.set_parameters(v=v, u=u, l=l)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1100, 850)
    window.show()
    sys.exit(app.exec())