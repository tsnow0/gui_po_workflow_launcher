#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
from datetime import datetime
import numpy as np

def main(df, today):
    this_month = datetime(today.year, today.month, 1)
    df['days_in_month'] = df['month'].dt.daysinmonth
    df['current_day'] = today.day
    df['remaining_days'] = np.where(df['month'] == this_month, df['days_in_month'] - df['current_day'], df['days_in_month'])
    df['remaining_days_%'] = df['remaining_days'] / df['days_in_month']
    df['amazon_ds_demand_quantity_adj'] = np.where(df['month'] == this_month, (df['amazon_ds_demand_quantity'] * df['remaining_days_%']), df['amazon_ds_demand_quantity'])
    df['evr_demand_quantity_adj'] = np.where(df['month'] == this_month, round(df['evr_demand_quantity'] * df['remaining_days_%']), df['evr_demand_quantity'])
    df['way_ds_demand_quantity_adj'] = np.where(df['month'] == this_month, round(df['way_ds_demand_quantity'] * df['remaining_days_%']), df['way_ds_demand_quantity'])
    df['us_di_demand_quantity_adj'] = np.where(df['month'] == this_month, round(df['us_di_demand_quantity'] * df['remaining_days_%']), df['us_di_demand_quantity'])
    df['ca_di_demand_quantity_adj'] = np.where(df['month'] == this_month, round(df['ca_di_demand_quantity'] * df['remaining_days_%']), df['ca_di_demand_quantity'])
    df['way_di_demand_quantity_adj'] = np.where(df['month'] == this_month, round(df['way_di_demand_quantity'] * df['remaining_days_%']), df['way_di_demand_quantity'])