from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button


DATA_FILE = Path("data") / "data.txv"

REF_TORQUE = 0.0
TOLERANCE = 0.05
DROP_THRESHOLD = 0.05
WINDOW_SIZE = 500

current_data = pd.DataFrame()
previous_data = pd.DataFrame()

history_offset = 0
live_mode = True


def load_txv_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Soubor neexistuje: {path.resolve()}")
        return pd.DataFrame()

    df = pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        decimal=",",
        engine="python"
    )

    df.columns = [
        "time_ms",
        "rpm_smooth",
        "torque",
        "rpm_actual",
        "dc_link",
        "current",
        "output_voltage"
    ]

    return df


def detect_torque_drop(df: pd.DataFrame):
    if len(df) < 2:
        return "ČEKÁM NA DATA"

    current = df["torque"].iloc[-1]
    previous = df["torque"].iloc[-2]
    diff = current - previous

    if diff < -DROP_THRESHOLD:
        return "SKOKOVÝ POKLES MOMENTU"

    if current < REF_TORQUE - TOLERANCE:
        return "MOMENT POD REFERENCÍ"

    if current > REF_TORQUE + TOLERANCE:
        return "MOMENT NAD REFERENCÍ"

    return "OK"


def get_window(df: pd.DataFrame) -> pd.DataFrame:
    global history_offset

    if df.empty:
        return df

    end = len(df) - history_offset
    start = max(0, end - WINDOW_SIZE)

    if end <= 0:
        return pd.DataFrame()

    return df.iloc[start:end]


def redraw():
    ax1.clear()
    ax2.clear()

    ax1.set_facecolor("#c0c0c0")

    view_current = get_window(current_data)
    view_previous = get_window(previous_data)

    if view_current.empty:
        ax1.set_title("Čekám na data...")
        return

    x_current = range(len(view_current))

    # předchozí hodnoty - vybledlé
    if not view_previous.empty:
        x_prev = range(len(view_previous))

        ax1.plot(
            x_prev,
            view_previous["rpm_smooth"],
            color="magenta",
            linewidth=1,
            alpha=0.25,
            label="rpm předchozí"
        )

        ax2.plot(
            x_prev,
            view_previous["torque"],
            color="blue",
            linewidth=1,
            alpha=0.25,
            label="Moment předchozí"
        )

    # aktuální hodnoty - silné
    ax1.plot(
        x_current,
        view_current["rpm_smooth"],
        color="magenta",
        linewidth=1.5,
        label="rpm aktuální"
    )

    ax2.plot(
        x_current,
        view_current["torque"],
        color="blue",
        linewidth=1.5,
        label="Moment aktuální [Nm]"
    )

    # zvýraznění nových bodů oproti předchozímu načtení
    if not previous_data.empty and len(current_data) > len(previous_data):
        added = len(current_data) - len(previous_data)
        added_view_count = min(added, len(view_current))

        xs = list(range(len(view_current) - added_view_count, len(view_current)))

        ax1.scatter(
            xs,
            view_current["rpm_smooth"].tail(added_view_count),
            color="magenta",
            s=18,
            label="nové rpm"
        )

        ax2.scatter(
            xs,
            view_current["torque"].tail(added_view_count),
            color="red",
            s=22,
            label="nový moment"
        )

    ax2.axhline(REF_TORQUE, linestyle="--", linewidth=1, label="Reference")
    ax2.axhline(REF_TORQUE + TOLERANCE, linestyle=":", linewidth=1)
    ax2.axhline(REF_TORQUE - TOLERANCE, linestyle=":", linewidth=1)

    state = detect_torque_drop(view_current)

    mode_text = "LIVE" if live_mode else f"HISTORIE offset {history_offset}"

    ax1.set_title(
        f"Online měření data/data.txv | {mode_text} | Stav: {state} | řádků: {len(current_data)}"
    )

    ax1.set_xlabel("Vzorky")
    ax1.set_ylabel("rpm")
    ax2.set_ylabel("Moment [Nm]")

    ax1.grid(True)

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")


def update(frame):
    global current_data, previous_data, history_offset

    df = load_txv_file(DATA_FILE)

    if df.empty:
        return

    if current_data.empty or len(df) != len(current_data):
        previous_data = current_data.copy()
        current_data = df.copy()

        if live_mode:
            history_offset = 0

        print(f"Načteno řádků: {len(current_data)}")

    redraw()


def go_back(event):
    global history_offset, live_mode

    if current_data.empty:
        return

    live_mode = False
    history_offset += WINDOW_SIZE

    max_offset = max(0, len(current_data) - WINDOW_SIZE)
    history_offset = min(history_offset, max_offset)

    redraw()
    plt.draw()


def go_forward(event):
    global history_offset, live_mode

    if current_data.empty:
        return

    history_offset -= WINDOW_SIZE

    if history_offset <= 0:
        history_offset = 0
        live_mode = True

    redraw()
    plt.draw()


def go_live(event):
    global history_offset, live_mode

    history_offset = 0
    live_mode = True

    redraw()
    plt.draw()


fig, ax1 = plt.subplots(figsize=(13, 6))
ax2 = ax1.twinx()

plt.subplots_adjust(bottom=0.18)

button_back_ax = plt.axes([0.30, 0.04, 0.12, 0.06])
button_forward_ax = plt.axes([0.44, 0.04, 0.12, 0.06])
button_live_ax = plt.axes([0.58, 0.04, 0.12, 0.06])

button_back = Button(button_back_ax, "← Historie")
button_forward = Button(button_forward_ax, "Historie →")
button_live = Button(button_live_ax, "LIVE")

button_back.on_clicked(go_back)
button_forward.on_clicked(go_forward)
button_live.on_clicked(go_live)

update(0)

ani = FuncAnimation(
    fig,
    update,
    interval=1000,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()