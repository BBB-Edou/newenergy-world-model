"""Generate a tiny, reproducible L1 demo PDF. No energy physics is encoded."""

from __future__ import annotations

from pathlib import Path

import pymupdf


def _draw_table(page: pymupdf.Page, x0: float, y0: float, rows: list[list[str]], widths: list[float]) -> None:
    row_height = 24
    x_positions = [x0]
    for width in widths:
        x_positions.append(x_positions[-1] + width)
    for row_index in range(len(rows) + 1):
        y = y0 + row_index * row_height
        page.draw_line((x0, y), (x_positions[-1], y), color=(0, 0, 0), width=0.7)
    for x in x_positions:
        page.draw_line((x, y0), (x, y0 + len(rows) * row_height), color=(0, 0, 0), width=0.7)
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            page.insert_text((x_positions[column_index] + 6, y0 + row_index * row_height + 16), value, fontsize=10, fontname="helv")


def main() -> None:
    output = Path(__file__).with_name("demo.pdf")
    document = pymupdf.open()

    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "1 System Overview", fontsize=20, fontname="helv")
    page.insert_text((72, 110), "This demo document describes a generic renewable energy system.", fontsize=11, fontname="helv")
    page.insert_text((72, 152), "1.1 Wind System", fontsize=15, fontname="helv")
    page.insert_text((72, 182), "Wind generation is represented as a placeholder component in this demo.", fontsize=11, fontname="helv")

    table_page = document.new_page(width=595, height=842)
    table_page.insert_text((72, 72), "2 Data Table", fontsize=20, fontname="helv")
    table_page.insert_text((72, 108), "The following Battery values are demo-only and must not be treated as thesis data.", fontsize=11, fontname="helv")
    _draw_table(
        table_page,
        72,
        140,
        [
            ["Entity", "Parameter", "Value", "Unit"],
            ["Battery", "Capacity", "200", "kWh"],
            ["Battery", "Efficiency", "0.95", "-"],
        ],
        [70, 150, 90, 90],
    )
    table_page.insert_text((72, 250), "End of L1 demo document.", fontsize=11, fontname="helv")

    component_lines = [
        "3 Renewable Components",
        "Wind has entity_type=renewable_source.",
        "PV has entity_type=renewable_source.",
        "Battery has entity_type=storage.",
        "Grid has entity_type=grid_connection.",
        "Load has entity_type=demand.",
        "Wind.rated_power = 100 kW.",
        "PV.rated_power = 80 kW.",
        "Battery.capacity = 200 kWh.",
        "Battery.max_charge_power = 50 kW.",
        "Battery.max_discharge_power = 50 kW.",
        "Battery.SOC_min = 20 %.",
        "Battery.SOC_max = 90 %.",
        "Battery.SOC = 50 %.",
        "Grid.max_import_power = 150 kW.",
        "Load.demand = 120 kW.",
        "4 Relations: Wind -> Load; PV -> Load; Battery -> Load; Grid -> Load.",
        "5 Processes: generation, charging, discharging, grid_purchase, load_consumption.",
        "6 Constraint: SOC_min <= Battery.SOC <= SOC_max.",
        "7 Objective: minimize operating_cost.",
    ]
    for index, line in enumerate(component_lines):
        table_page.insert_text((72, 290 + index * 22), line, fontsize=15 if index == 0 else 11, fontname="helv")

    document.save(output, garbage=4, deflate=True)
    document.close()
    print(output.resolve())


if __name__ == "__main__":
    main()