import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Скорость течения реки относительно берега
v_river = 2.0

# Скорость лодки относительно воды.
# По условию она в n = 2 раза меньше скорости течения:
# u_boat = v_river / n
n = 2.0
u_boat = v_river / n

# Начальный угол курса лодки к направлению течения, в градусах.
# 0°  — лодка направлена по течению.
# 90° — лодка направлена строго поперек реки.
# 180° — лодка направлена строго против течения.
initial_angle = 120.0

fig, ax = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.22)

ax.set_aspect("equal", adjustable="box")
ax.set_xlim(-2.5, 3.0)
ax.set_ylim(-2.0, 2.5)
ax.grid(True)

ax.set_xlabel("Ось вдоль течения реки")
ax.set_ylabel("Ось поперек реки")
ax.set_title("Сложение скоростей: течение + собственная скорость лодки")

# Вектор течения: всегда направлен вправо
river_arrow = ax.quiver(
    0, 0,
    v_river, 0,
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.008
)

# Вектор собственной скорости лодки относительно воды
boat_arrow = ax.quiver(
    0, 0,
    0, 0,
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.008
)

# Результирующий вектор скорости лодки относительно берега
result_arrow = ax.quiver(
    0, 0,
    0, 0,
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.008
)

# Вспомогательные пунктирные линии для проекций результирующего вектора
projection_x_line, = ax.plot([], [], "--", linewidth=1)
projection_y_line, = ax.plot([], [], "--", linewidth=1)

info_text = ax.text(
    -2.4, 2.25,
    "",
    fontsize=11,
    verticalalignment="top"
)

legend_text = (
    "Векторы:\n"
    "течение реки: v_river\n"
    "лодка относительно воды: u_boat\n"
    "лодка относительно берега: v_result"
)

ax.text(
    -2.4, -1.85,
    legend_text,
    fontsize=10,
    verticalalignment="bottom"
)

slider_ax = plt.axes([0.18, 0.08, 0.65, 0.04])
angle_slider = Slider(
    ax=slider_ax,
    label="Угол курса к течению, градусы",
    valmin=0,
    valmax=180,
    valinit=initial_angle,
    valstep=1
)


def update(angle_degrees):
    angle_radians = np.deg2rad(angle_degrees)

    # Собственная скорость лодки относительно воды.
    # x-компонента отвечает за движение вдоль течения.
    # y-компонента отвечает за движение поперек реки.
    boat_x = u_boat * np.cos(angle_radians)
    boat_y = u_boat * np.sin(angle_radians)

    # Скорость течения имеет компоненты (v_river, 0).
    # Результирующая скорость относительно берега:
    result_x = v_river + boat_x
    result_y = boat_y

    result_speed = np.sqrt(result_x**2 + result_y**2)

    # Угол результирующей скорости к направлению течения
    result_angle = np.rad2deg(np.arctan2(result_y, result_x))

    boat_arrow.set_UVC(boat_x, boat_y)
    result_arrow.set_UVC(result_x, result_y)

    projection_x_line.set_data([0, result_x], [result_y, result_y])
    projection_y_line.set_data([result_x, result_x], [0, result_y])

    info_text.set_text(
        f"v_river = {v_river:.2f}\n"
        f"u_boat = {u_boat:.2f}\n"
        f"угол курса = {angle_degrees:.0f}°\n\n"
        f"u_boat_x = {boat_x:.3f}\n"
        f"u_boat_y = {boat_y:.3f}\n\n"
        f"v_result_x = {result_x:.3f}\n"
        f"v_result_y = {result_y:.3f}\n"
        f"|v_result| = {result_speed:.3f}\n"
        f"угол v_result к течению = {result_angle:.1f}°"
    )

    fig.canvas.draw_idle()


angle_slider.on_changed(update)
update(initial_angle)

plt.show()