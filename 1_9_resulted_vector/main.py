import sys
import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class BoatVectorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("1.9 — Движение лодки в течении")
        self.resize(1320, 820)

        self.v_river = 2.0
        self.n_ratio = 2.0
        self.angle_degrees = 120.0
        self.view_radius = 3.2
        self.vector_width = 0.010

        self.figure = Figure(figsize=(7.2, 7.2))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.river_speed_spin = QDoubleSpinBox()
        self.river_speed_spin.setRange(0.1, 20.0)
        self.river_speed_spin.setSingleStep(0.1)
        self.river_speed_spin.setValue(self.v_river)
        self.river_speed_spin.valueChanged.connect(self.update_river_speed)

        self.ratio_spin = QDoubleSpinBox()
        self.ratio_spin.setRange(1.1, 10.0)
        self.ratio_spin.setSingleStep(0.1)
        self.ratio_spin.setValue(self.n_ratio)
        self.ratio_spin.valueChanged.connect(self.update_ratio)

        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(0, 180)
        self.angle_slider.setValue(int(self.angle_degrees))
        self.angle_slider.valueChanged.connect(self.update_angle_from_slider)

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(0.0, 180.0)
        self.angle_spin.setSingleStep(1.0)
        self.angle_spin.setValue(self.angle_degrees)
        self.angle_spin.valueChanged.connect(self.update_angle_from_spin)

        self.reset_button = QPushButton("Сбросить")
        self.reset_button.clicked.connect(self.reset)

        self.optimal_button = QPushButton("Показать минимум сноса")
        self.optimal_button.clicked.connect(self.set_optimal_angle)

        self.boat_speed_label = QLabel()
        self.result_speed_label = QLabel()
        self.result_angle_label = QLabel()
        self.result_x_label = QLabel()
        self.result_y_label = QLabel()
        self.drift_ratio_label = QLabel()
        self.interpretation_label = QLabel()
        self.interpretation_label.setWordWrap(True)
        self.interpretation_label.setObjectName("ExplanationLabel")

        self.build_layout()
        self.apply_style()
        self.redraw()

    def build_layout(self):
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(18)

        plot_panel = QFrame()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(14, 14, 14, 14)
        plot_layout.addWidget(self.canvas)

        control_panel = QFrame()
        control_panel.setFixedWidth(390)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(14)

        title = QLabel("Лодка и течение")
        title.setObjectName("TitleLabel")

        subtitle = QLabel(
            "Плоская векторная модель движения лодки относительно берега. "
            "Скорости складываются как векторы: течение + собственная скорость лодки."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("SubtitleLabel")

        task_text = QLabel(
            "Условие задачи\n\n"
            "Лодка движется относительно воды со скоростью, которая в "
            "<b>n = 2.0</b> раза меньше скорости течения реки. "
            "Нужно определить, под каким углом к направлению течения следует "
            "держать курс, чтобы течение снесло лодку как можно меньше."
        )
        task_text.setWordWrap(True)
        task_text.setObjectName("TaskLabel")

        control_layout.addWidget(title)
        control_layout.addWidget(subtitle)
        control_layout.addWidget(task_text)

        control_layout.addWidget(QLabel("Скорость течения"))
        control_layout.addWidget(self.river_speed_spin)

        control_layout.addWidget(QLabel("Во сколько раз лодка медленнее течения"))
        control_layout.addWidget(self.ratio_spin)

        control_layout.addWidget(QLabel("Угол курса к направлению течения"))
        control_layout.addWidget(self.angle_slider)
        control_layout.addWidget(self.angle_spin)

        control_layout.addWidget(self.boat_speed_label)
        control_layout.addWidget(self.result_speed_label)
        control_layout.addWidget(self.result_angle_label)
        control_layout.addWidget(self.result_x_label)
        control_layout.addWidget(self.result_y_label)
        control_layout.addWidget(self.drift_ratio_label)

        control_layout.addWidget(self.optimal_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addWidget(self.interpretation_label)
        control_layout.addStretch()

        root_layout.addWidget(plot_panel, stretch=1)
        root_layout.addWidget(control_panel)

        self.setCentralWidget(central)

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827;
            }

            QFrame {
                background-color: #111827;
                border: none;
            }

            QLabel {
                color: #E5E7EB;
                font-size: 14px;
            }

            QLabel#TitleLabel {
                color: #FFFFFF;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#SubtitleLabel {
                color: #A5B4FC;
                font-size: 14px;
            }

            QLabel#TaskLabel {
                color: #E2E8F0;
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 16px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.45;
            }

            QLabel#ExplanationLabel {
                color: #CBD5E1;
                background-color: #1F2937;
                border-radius: 14px;
                padding: 14px;
                font-size: 13px;
            }

            QDoubleSpinBox {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }

            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 11px;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #6366F1;
            }

            QPushButton:pressed {
                background-color: #4338CA;
            }

            QSlider::groove:horizontal {
                height: 8px;
                background: #374151;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
                background: #A5B4FC;
            }
        """)

    def get_vectors(self):
        u_boat = self.v_river / self.n_ratio
        angle_radians = np.deg2rad(self.angle_degrees)

        river = np.array([self.v_river, 0.0])
        boat = np.array([u_boat * np.cos(angle_radians), u_boat * np.sin(angle_radians)])
        result = river + boat
        return u_boat, river, boat, result

    def redraw(self):
        u_boat, river, boat, result = self.get_vectors()

        self.ax.clear()
        self.figure.patch.set_facecolor("#111827")
        self.ax.set_facecolor("#0B1120")

        self.ax.set_title("Сложение скоростей на плоскости", color="#F9FAFB", fontsize=16, pad=14)
        self.ax.set_xlabel("Ось вдоль течения", color="#E5E7EB")
        self.ax.set_ylabel("Ось поперёк реки", color="#E5E7EB")
        self.ax.tick_params(colors="#CBD5E1")
        self.ax.grid(True, alpha=0.22, color="#64748B")
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlim(-self.view_radius, self.view_radius + max(1.0, self.v_river * 0.7))
        self.ax.set_ylim(-self.view_radius, self.view_radius)

        self.ax.axhline(0, color="#334155", linewidth=1.2)
        self.ax.axvline(0, color="#334155", linewidth=1.2)

        self.ax.quiver(
            0, 0, river[0], river[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=self.vector_width,
            headwidth=6,
            headlength=7,
            headaxislength=6,
            color="#3B82F6",
            alpha=0.95,
            label="Течение реки"
        )

        self.ax.quiver(
            0, 0, boat[0], boat[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=self.vector_width,
            headwidth=6,
            headlength=7,
            headaxislength=6,
            color="#F97316",
            alpha=0.98,
            label="Скорость лодки"
        )

        self.ax.quiver(
            0, 0, result[0], result[1],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=self.vector_width,
            headwidth=6,
            headlength=7,
            headaxislength=6,
            color="#22C55E",
            alpha=0.98,
            label="Скорость относительно берега"
        )

        self.ax.plot([0, result[0]], [result[1], result[1]], "--", color="#94A3B8", linewidth=1.6, alpha=0.75)
        self.ax.plot([result[0], result[0]], [0, result[1]], "--", color="#94A3B8", linewidth=1.6, alpha=0.75)
        self.ax.scatter([0], [0], s=44, color="#F8FAFC", zorder=5)

        result_speed = float(np.linalg.norm(result))
        result_angle = float(np.rad2deg(np.arctan2(result[1], result[0])))
        drift_per_cross = result[0] / result[1] if abs(result[1]) > 1e-9 else None

        legend = self.ax.legend(loc="upper right", facecolor="#1F2937", edgecolor="#374151")
        for text in legend.get_texts():
            text.set_color("#F9FAFB")

        self.boat_speed_label.setText(f"Скорость лодки относительно воды: {u_boat:.3f}")
        self.result_speed_label.setText(f"Скорость лодки относительно берега: {result_speed:.3f}")
        self.result_angle_label.setText(f"Угол результирующего движения: {result_angle:.2f}°")
        self.result_x_label.setText(f"Снос по течению: {result[0]:.3f}")
        self.result_y_label.setText(f"Поперечная составляющая: {result[1]:.3f}")

        if drift_per_cross is None:
            self.drift_ratio_label.setText("Отношение сноса к переправе: не определено")
        else:
            self.drift_ratio_label.setText(f"Отношение сноса к переправе: {drift_per_cross:.3f}")

        optimal_angle = 180.0
        if self.angle_degrees == 180.0:
            interpretation = (
                "Минимальный снос достигается при курсе строго против течения: "
                "x-компонента собственной скорости лодки максимально уменьшает унос вниз по реке."
            )
        elif 90.0 < self.angle_degrees < 180.0:
            interpretation = (
                "Лодка идёт частично поперёк реки и частично против течения. "
                "Снос уменьшается по мере приближения угла к 180°."
            )
        elif self.angle_degrees == 90.0:
            interpretation = (
                "Курс строго поперёк реки даёт максимальную поперечную скорость, "
                "но течение полностью добавляет снос вдоль берега."
            )
        else:
            interpretation = (
                "При углах меньше 90° лодка частично направлена по течению, "
                "поэтому снос только усиливается."
            )

        self.interpretation_label.setText(
            f"{interpretation}\n\n"
            f"Для данной модели минимум сноса достигается при угле {optimal_angle:.0f}°."
        )

        self.canvas.draw()

    def update_river_speed(self, value):
        self.v_river = float(value)
        self.redraw()

    def update_ratio(self, value):
        self.n_ratio = float(value)
        self.redraw()

    def update_angle_from_slider(self, value):
        self.angle_degrees = float(value)
        self.angle_spin.blockSignals(True)
        self.angle_spin.setValue(self.angle_degrees)
        self.angle_spin.blockSignals(False)
        self.redraw()

    def update_angle_from_spin(self, value):
        self.angle_degrees = float(value)
        self.angle_slider.blockSignals(True)
        self.angle_slider.setValue(int(round(self.angle_degrees)))
        self.angle_slider.blockSignals(False)
        self.redraw()

    def set_optimal_angle(self):
        self.angle_degrees = 180.0
        self.angle_slider.blockSignals(True)
        self.angle_spin.blockSignals(True)
        self.angle_slider.setValue(180)
        self.angle_spin.setValue(180.0)
        self.angle_slider.blockSignals(False)
        self.angle_spin.blockSignals(False)
        self.redraw()

    def reset(self):
        self.v_river = 2.0
        self.n_ratio = 2.0
        self.angle_degrees = 120.0

        self.river_speed_spin.setValue(self.v_river)
        self.ratio_spin.setValue(self.n_ratio)
        self.angle_slider.setValue(int(self.angle_degrees))
        self.angle_spin.setValue(self.angle_degrees)
        self.redraw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BoatVectorApp()
    window.show()
    sys.exit(app.exec())
