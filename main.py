import sys
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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
from numpy.char import center


class StarExpansionApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Star Expansion Model")
        self.resize(1250, 780)

        self.star_count = 335
        self.n_index = 0

        self.k = 0.12
        self.time = 0.0
        self.dt = 0.03
        self.speed_multiplier = 1.0

        self.view_radius = 20.0
        self.vector_scale = 4.0

        rng = np.random.default_rng(12)
        center = np.array([30, -30])

        sigma = 40
        self.initial_positions = rng.normal(loc=center, scale=sigma, size=(self.star_count, 2))

        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.animate)

        self.figure = Figure(figsize=(7, 7))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.reference_box = QComboBox()
        self.reference_box.addItem("View from the Sun", "sun")
        self.reference_box.addItem("View from star N", "star_n")
        self.reference_box.currentIndexChanged.connect(self.redraw)

        self.k_spin = QDoubleSpinBox()
        self.k_spin.setRange(0.01, 0.50)
        self.k_spin.setSingleStep(0.01)
        self.k_spin.setValue(self.k)
        self.k_spin.valueChanged.connect(self.update_k)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(25)
        self.speed_slider.valueChanged.connect(self.update_speed)

        self.view_radius_slider = QSlider(Qt.Horizontal)
        self.view_radius_slider.setRange(5, 200)
        self.view_radius_slider.setValue(int(self.view_radius))
        self.view_radius_slider.valueChanged.connect(self.update_view_radius)

        self.vector_scale_slider = QSlider(Qt.Horizontal)
        self.vector_scale_slider.setRange(1, 40)
        self.vector_scale_slider.setValue(int(self.vector_scale))
        self.vector_scale_slider.valueChanged.connect(self.update_vector_scale)

        self.show_vectors_checkbox = QCheckBox("Show velocity vectors")
        self.show_vectors_checkbox.setChecked(True)
        self.show_vectors_checkbox.stateChanged.connect(self.redraw)

        self.auto_scale_checkbox = QCheckBox("Auto scale axes")
        self.auto_scale_checkbox.setChecked(False)
        self.auto_scale_checkbox.stateChanged.connect(self.redraw)

        self.time_label = QLabel("t = 0.00")
        self.radius_label = QLabel(f"View radius = {self.view_radius:.0f}")
        self.vector_label = QLabel(f"Vector scale = {self.vector_scale:.0f}")
        self.mode_label = QLabel("Model: v = k · r")

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_animation)

        self.step_button = QPushButton("Step forward")
        self.step_button.clicked.connect(self.step_forward)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)

        self.zoom_in_button = QPushButton("Zoom in")
        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button = QPushButton("Zoom out")
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.build_layout()
        self.apply_style()
        self.redraw()

    def build_layout(self):
        central = QWidget()
        root_layout = QHBoxLayout(central)

        plot_panel = QFrame()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.addWidget(self.canvas)

        control_panel = QFrame()
        control_panel.setFixedWidth(350)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(14)

        title = QLabel("Expansion Simulator")
        title.setObjectName("TitleLabel")

        subtitle = QLabel(
            "The simulation shows star motion in two reference frames: "
            "from the Sun and from a selected star N."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("SubtitleLabel")

        control_layout.addWidget(title)
        control_layout.addWidget(subtitle)

        control_layout.addWidget(QLabel("Reference frame"))
        control_layout.addWidget(self.reference_box)

        control_layout.addWidget(QLabel("Expansion coefficient k"))
        control_layout.addWidget(self.k_spin)

        control_layout.addWidget(QLabel("Animation speed"))
        control_layout.addWidget(self.speed_slider)

        control_layout.addWidget(QLabel("View radius"))
        control_layout.addWidget(self.view_radius_slider)
        control_layout.addWidget(self.radius_label)

        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.zoom_in_button)
        zoom_layout.addWidget(self.zoom_out_button)
        control_layout.addLayout(zoom_layout)

        control_layout.addWidget(self.auto_scale_checkbox)

        control_layout.addWidget(QLabel("Velocity vector scale"))
        control_layout.addWidget(self.vector_scale_slider)
        control_layout.addWidget(self.vector_label)
        control_layout.addWidget(self.show_vectors_checkbox)

        control_layout.addWidget(self.time_label)
        control_layout.addWidget(self.mode_label)

        control_layout.addSpacing(8)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.step_button)
        control_layout.addWidget(self.reset_button)

        explanation = QLabel(
            "Velocity vectors:\n"
            "vᵢ = k · rᵢ\n\n"
            "Sun frame:\n"
            "rᵢ is measured from the Sun\n\n"
            "Star N frame:\n"
            "r'ᵢ = rᵢ - r_N\n"
            "v'ᵢ = vᵢ - v_N\n\n"
            "The arrows show velocity in the currently selected reference frame."
        )
        explanation.setWordWrap(True)
        explanation.setObjectName("ExplanationLabel")

        control_layout.addSpacing(10)
        control_layout.addWidget(explanation)
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

            QLabel#ExplanationLabel {
                color: #CBD5E1;
                background-color: #1F2937;
                border-radius: 14px;
                padding: 14px;
                font-family: Menlo;
                font-size: 12px;
            }

            QCheckBox {
                color: #E5E7EB;
                font-size: 14px;
            }

            QComboBox, QDoubleSpinBox {
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

    def get_positions_and_velocities(self):
        positions = self.initial_positions * np.exp(self.k * self.time)
        velocities = self.k * positions
        return positions, velocities

    def get_visible_data(self):
        positions, velocities = self.get_positions_and_velocities()
        frame = self.reference_box.currentData()

        if frame == "star_n":
            n_position = positions[self.n_index].copy()
            n_velocity = velocities[self.n_index].copy()

            visible_positions = positions - n_position
            visible_velocities = velocities - n_velocity
            sun_position = -n_position
            title = "View from star N"
        else:
            visible_positions = positions
            visible_velocities = velocities
            sun_position = np.array([0.0, 0.0])
            title = "View from the Sun"

        return visible_positions, visible_velocities, sun_position, title

    def redraw(self):
        positions, velocities, sun_position, title = self.get_visible_data()

        self.ax.clear()
        self.figure.patch.set_facecolor("#111827")
        self.ax.set_facecolor("#0B1120")

        self.ax.set_title(title, color="#F9FAFB", fontsize=16, pad=14)
        self.ax.set_xlabel("x", color="#E5E7EB")
        self.ax.set_ylabel("y", color="#E5E7EB")

        self.ax.tick_params(colors="#CBD5E1")
        self.ax.grid(True, alpha=0.25)
        self.ax.set_aspect("equal", adjustable="box")

        if self.auto_scale_checkbox.isChecked():
            max_abs = max(
                12.0,
                float(np.max(np.abs(positions))) + 3.0,
                float(np.max(np.abs(sun_position))) + 3.0,
            )
        else:
            max_abs = self.view_radius

        self.ax.set_xlim(-max_abs, max_abs)
        self.ax.set_ylim(-max_abs, max_abs)

        self.ax.scatter(
            positions[:, 0],
            positions[:, 1],
            s=48,
            label="Stars",
            alpha=0.9
        )

        self.ax.scatter(
            positions[self.n_index, 0],
            positions[self.n_index, 1],
            s=190,
            marker="*",
            label="Star N"
        )

        self.ax.scatter(
            sun_position[0],
            sun_position[1],
            s=160,
            marker="o",
            label="Sun"
        )

        if self.show_vectors_checkbox.isChecked():
            visible_vector_lengths = velocities * self.vector_scale

        self.ax.quiver(
            positions[:, 0],
            positions[:, 1],
            visible_vector_lengths[:, 0],
            visible_vector_lengths[:, 1],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=0.006,
            headwidth=4,
            headlength=6,
            headaxislength=5,
            alpha=0.95,
            color="#FBBF24",
            label="Velocity vectors"
        )

        legend = self.ax.legend(loc="upper right", facecolor="#1F2937", edgecolor="#374151")
        for text in legend.get_texts():
            text.set_color("#F9FAFB")

        self.time_label.setText(f"t = {self.time:.2f}")
        self.radius_label.setText(f"View radius = {self.view_radius:.0f}")
        self.vector_label.setText(f"Vector scale = {self.vector_scale:.0f}")
        self.canvas.draw()

    def update_k(self, value):
        self.k = float(value)
        self.redraw()

    def update_speed(self, value):
        self.speed_multiplier = value / 25.0

    def update_view_radius(self, value):
        self.view_radius = float(value)
        self.redraw()

    def update_vector_scale(self, value):
        self.vector_scale = float(value)
        self.redraw()

    def zoom_in(self):
        self.view_radius = max(5.0, self.view_radius * 0.8)
        self.view_radius_slider.setValue(int(self.view_radius))
        self.redraw()

    def zoom_out(self):
        self.view_radius = min(200.0, self.view_radius * 1.25)
        self.view_radius_slider.setValue(int(self.view_radius))
        self.redraw()

    def animate(self):
        self.time += self.dt * self.speed_multiplier
        self.redraw()

    def toggle_animation(self):
        if self.timer.isActive():
            self.timer.stop()
            self.start_button.setText("Start")
        else:
            self.timer.start()
            self.start_button.setText("Pause")

    def step_forward(self):
        self.time += self.dt * self.speed_multiplier
        self.redraw()

    def reset(self):
        self.timer.stop()
        self.start_button.setText("Start")
        self.time = 0.0
        self.redraw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StarExpansionApp()
    window.show()
    sys.exit(app.exec())