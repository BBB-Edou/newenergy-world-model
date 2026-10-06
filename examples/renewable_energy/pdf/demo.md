<!-- page: 1 -->

# 1 System Overview

This demo document describes a generic renewable energy system.

## 1.1 Wind System

Wind generation is represented as a placeholder component in this demo.

<!-- page: 2 -->

# 2 Data Table

The following Battery values are demo-only and must not be treated as thesis data.

| Entity | Parameter | Value | Unit |
| --- | --- | ---: | --- |
| Battery | Capacity | 200 | kWh |
| Battery | Efficiency | 0.95 | - |

End of L1 demo document.

# 3 Renewable Components

Wind has entity_type=renewable_source.

PV has entity_type=renewable_source.

Battery has entity_type=storage.

Grid has entity_type=grid_connection.

Load has entity_type=demand.

Wind.rated_power = 100 kW.

PV.rated_power = 80 kW.

Battery.capacity = 200 kWh.

Battery.max_charge_power = 50 kW.

Battery.max_discharge_power = 50 kW.

Battery.SOC_min = 20 %.

Battery.SOC_max = 90 %.

Battery.SOC = 50 %.

Grid.max_import_power = 150 kW.

Load.demand = 120 kW.

# 4 Relations: Wind -> Load; PV -> Load; Battery -> Load; Grid -> Load.

# 5 Processes: generation, charging, discharging, grid_purchase, load_consumption.

# 6 Constraint: SOC_min <= Battery.SOC <= SOC_max.

# 7 Objective: minimize operating_cost.
