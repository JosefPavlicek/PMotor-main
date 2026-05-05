from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


DATA_FILE = Path("data") / "data.txv"

REF_TORQUE = 0.0
TOLERANCE = 0.05
DROP_THRESHOLD = 0.05
MAX_POINTS = 1000

all_data = pd.DataFrame()


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


fig, ax1 = plt.subplots(figsize=(13, 6))
ax2 = ax1.twinx()


def update(frame):
    global all_data

    try:
        print("Kontroluji soubor:", DATA_FILE.resolve())

        df = load_txv_file(DATA_FILE)
        print("Načteno řádků:", len(df))

        if df.empty:
            return

        all_data = df.copy()
        view = all_data.tail(MAX_POINTS)

        state = detect_torque_drop(view)
        x = range(len(view))

        ax1.clear()
        ax2.clear()

        ax1.set_facecolor("#c0c0c0")

        ax1.plot(x, view["rpm_smooth"], color="magenta", linewidth=1, label="rpm")
        ax2.plot(x, view["torque"], color="blue", linewidth=1, label="Moment [Nm]")

        ax2.axhline(REF_TORQUE, linestyle="--", linewidth=1, label="Reference")
        ax2.axhline(REF_TORQUE + TOLERANCE, linestyle=":", linewidth=1)
        ax2.axhline(REF_TORQUE - TOLERANCE, linestyle=":", linewidth=1)

        ax1.set_title(
            f"Online měření data/data.txv | Stav: {state} | řádků: {len(df)}"
        )
        ax1.set_xlabel("Vzorky")
        ax1.set_ylabel("rpm")
        ax2.set_ylabel("Moment [Nm]")

        ax1.grid(True)

        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")

    except Exception as e:
        print("CHYBA V UPDATE:", e)


update(0)

ani = FuncAnimation(
    fig,
    update,
    interval=1000,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()