

import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output
from collections import deque


ACTIVITY_1 = [
    {"Process": "P1", "Arrival": 0, "Burst": 5},
    {"Process": "P2", "Arrival": 1, "Burst": 3},
    {"Process": "P3", "Arrival": 2, "Burst": 4},
    {"Process": "P4", "Arrival": 3, "Burst": 2}
]

ACTIVITY_2 = [
    {"Process": "P1", "Arrival": 0, "Burst": 5},
    {"Process": "P2", "Arrival": 1, "Burst": 4},
    {"Process": "P3", "Arrival": 2, "Burst": 3},
    {"Process": "P4", "Arrival": 3, "Burst": 2}
]




def simulate_rr(processes, quantum, overhead=0):

    jobs = {
        p["Process"]: {
            **p,
            "remaining": p["Burst"],
            "first_start": None,
            "completion": None
        }
        for p in processes
    }

    ready = deque()
    added = set()
    timeline = []
    time = 0
    last_process = None

    def add_arrivals(t, exclude=None):
        for p in processes:
            name = p["Process"]

            if (
                p["Arrival"] <= t
                and jobs[name]["remaining"] > 0
                and name not in added
                and name != exclude
            ):
                ready.append(name)
                added.add(name)

    while any(j["remaining"] > 0 for j in jobs.values()):

        add_arrivals(time)

        if not ready:
            time += 1
            timeline.append({
                "start": time - 1,
                "end": time,
                "label": "IDLE",
                "kind": "idle"
            })
            continue

        current = ready.popleft()
        added.discard(current)

        if (
            last_process is not None
            and current != last_process
            and overhead > 0
        ):
            for _ in range(overhead):
                timeline.append({
                    "start": time,
                    "end": time + 1,
                    "label": "CS",
                    "kind": "cs"
                })
                time += 1
                add_arrivals(time)

        if jobs[current]["first_start"] is None:
            jobs[current]["first_start"] = time

        run_time = min(
            quantum,
            jobs[current]["remaining"]
        )

        for _ in range(run_time):

            timeline.append({
                "start": time,
                "end": time + 1,
                "label": current,
                "kind": "run"
            })

            jobs[current]["remaining"] -= 1
            time += 1

            add_arrivals(time, exclude=current)

        if jobs[current]["remaining"] == 0:
            jobs[current]["completion"] = time
        else:
            ready.append(current)
            added.add(current)

        last_process = current



    rows = []

    for p in processes:

        j = jobs[p["Process"]]

        turnaround = (
            j["completion"] - p["Arrival"]
        )

        waiting = turnaround - p["Burst"]

        response = (
            j["first_start"] - p["Arrival"]
        )

        rows.append({
            "Process": p["Process"],
            "Arrival": p["Arrival"],
            "Burst": p["Burst"],
            "Completion": j["completion"],
            "Turnaround": turnaround,
            "Waiting": waiting,
            "Response": response
        })

    table = pd.DataFrame(rows)

    useful = sum(
        x["end"] - x["start"]
        for x in timeline
        if x["kind"] == "run"
    )

    elapsed = timeline[-1]["end"] if timeline else 0

    context_switches = sum(
        a["label"] != b["label"]
        for a, b in zip(
            [x for x in timeline if x["kind"] == "run"],
            [x for x in timeline if x["kind"] == "run"][1:]
        )
    )

    metrics = {
        "Average Waiting Time":
            table["Waiting"].mean(),

        "Average Turnaround Time":
            table["Turnaround"].mean(),

        "Average Response Time":
            table["Response"].mean(),

        "Context Switches":
            context_switches,

        "Total Execution Time":
            elapsed,

        "CPU Efficiency (%)":
            useful / elapsed * 100 if elapsed else 0
    }

    return timeline, table, metrics




def draw_gantt(timeline):

    if not timeline:
        print("Simulation not started.")
        return

    fig, ax = plt.subplots(figsize=(12, 2.5))

    colors = {
        "P1": "skyblue",
        "P2": "lightgreen",
        "P3": "salmon",
        "P4": "plum",
        "CS": "orange",
        "IDLE": "lightgray"
    }

    for item in timeline:

        start = item["start"]
        end = item["end"]
        label = item["label"]

        ax.barh(
            0,
            end - start,
            left=start,
            height=0.5,
            color=colors.get(label, "gray"),
            edgecolor="black"
        )

        ax.text(
            (start + end) / 2,
            0,
            label,
            ha="center",
            va="center"
        )

    ax.set_yticks([])
    ax.set_xlabel("Time (ms)")
    ax.set_xticks(
        range(0, timeline[-1]["end"] + 1)
    )
    ax.set_title("Round Robin Scheduling — Gantt Chart")
    ax.grid(axis="x", linestyle=":")

    plt.tight_layout()
    plt.show()




activity = widgets.Dropdown(
    options=[
        ("Activity 1", "A1"),
        ("Activity 2", "A2")
    ],
    value="A1",
    description="Activity:"
)

quantum = widgets.Dropdown(
    options=[2, 3, 4],
    value=2,
    description="Quantum:"
)

next_button = widgets.Button(
    description="Next 1 ms",
    button_style="primary"
)

play_button = widgets.Button(
    description="Play",
    button_style="success"
)

reset_button = widgets.Button(
    description="Reset"
)

compare_button = widgets.Button(
    description="Compare Quantums",
    button_style="info"
)

output = widgets.Output()
compare_output = widgets.Output()

state = {
    "timeline": [],
    "table": None,
    "metrics": {},
    "step": 0
}




def load_simulation():

    processes = (
        ACTIVITY_1
        if activity.value == "A1"
        else ACTIVITY_2
    )

    overhead = 0 if activity.value == "A1" else 1

    timeline, table, metrics = simulate_rr(
        processes,
        quantum.value,
        overhead
    )

    state["timeline"] = timeline
    state["table"] = table
    state["metrics"] = metrics
    state["step"] = 0

    show_step()


def show_step():

    timeline = state["timeline"]
    step = state["step"]

    with output:

        clear_output(wait=True)

        print("ROUND ROBIN VISUALIZER")
        print("----------------------")

        print("Activity:", activity.label, activity.value)
        print("Time Quantum:", quantum.value, "ms")
        print("Current Time:", step, "ms")

        print("\nGANTT CHART")

        draw_gantt(timeline[:step])

        print("\nPROCESS PERFORMANCE TABLE")

        display(state["table"])

        print("\nPERFORMANCE METRICS")

        display(
            pd.DataFrame(
                [state["metrics"]]
            ).round(2)
        )

        if step >= len(timeline):
            print("\nSimulation completed.")
        else:
            print("\nClick Next 1 ms or Play.")




def next_step(_):

    if state["step"] < len(state["timeline"]):
        state["step"] += 1

    show_step()

import time

def play_simulation(_):

    while state["step"] < len(state["timeline"]):

        state["step"] += 1
        show_step()

        time.sleep(3)




def reset_simulation(_):

    state["step"] = 0
    show_step()


def compare_quantums(_):

    processes = (
        ACTIVITY_1
        if activity.value == "A1"
        else ACTIVITY_2
    )

    overhead = 0 if activity.value == "A1" else 1

    rows = []

    for q in [2, 3, 4]:

        _, table, metrics = simulate_rr(
            processes, q, overhead
        )

        rows.append({
            "Quantum": q,
            "Average Waiting":
                round(metrics["Average Waiting Time"], 2),
            "Average Turnaround":
                round(metrics["Average Turnaround Time"], 2),
            "Average Response":
                round(metrics["Average Response Time"], 2),
            "Context Switches":
                metrics["Context Switches"],
            "CPU Efficiency (%)":
                round(metrics["CPU Efficiency (%)"], 2)
        })

    with compare_output:

        clear_output(wait=True)

        print("QUANTUM COMPARISON")

        display(pd.DataFrame(rows))


def change_setting(change):

    if change["name"] == "value":
        load_simulation()


next_button.on_click(next_step)
play_button.on_click(play_simulation)
reset_button.on_click(reset_simulation)
compare_button.on_click(compare_quantums)

activity.observe(change_setting, names="value")
quantum.observe(change_setting, names="value")




display(
    widgets.VBox([
        widgets.HTML(
            "<h2>Interactive Round Robin Scheduling Visualizer</h2>"
            "<p>Select an activity and quantum, then control the simulation.</p>"
        ),

        widgets.HBox([activity, quantum]),

        widgets.HBox([
            next_button,
            play_button,
            reset_button
        ]),

        output,

        compare_button,
        compare_output
    ])
)
