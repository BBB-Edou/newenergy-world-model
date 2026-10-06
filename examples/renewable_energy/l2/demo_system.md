# Renewable Energy System Demo

> Example/demo only. These values are not formal thesis data.

## Wind

Wind.rated_power = 100 kW.

## PV

PV.rated_power = 80 kW.

## Battery

Battery.capacity = 200 kWh.
Battery.max_charge_power = 50 kW.
Battery.max_discharge_power = 50 kW.
Battery.SOC_min = 20 %.
Battery.SOC_max = 90 %.
Battery.SOC = 50 %.

## Grid

Grid.max_import_power = 150 kW.

## Load

Load.demand = 120 kW.

## Relations

Wind -> Load.
PV -> Load.
Battery -> Load.
Grid -> Load.

## Processes

generation, charging, discharging, grid_purchase, load_consumption.

## Constraint

SOC_min <= Battery.SOC <= SOC_max.

## Objective

minimize operating_cost.