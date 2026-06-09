#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
import numpy as np
import pandas as pd

def main(df, version):
    print('Calculate projected sales')
    if version == 'depletions':
        df['evr_min_demand'] = np.maximum(np.minimum(df['evr_total_inventory'], df['evr_demand_quantity']), 0)
        df['way_di_min_demand'] = np.maximum(np.minimum(df['cg_total_inventory'], df['way_di_demand_quantity']), 0)  # don't need to add wayfair ds demand as that is already in evr_demand_quantity
        df['total_projected_sales'] = df['evr_min_demand'] + df['way_di_min_demand'] + df['amazon_projected_sales_po_quantity']
        df['non_di_sales'] = df['evr_min_demand']
        df['di_sales'] = df['way_di_min_demand'] + df['amazon_projected_sales_po_quantity']
    else:
        df['end_date'] = df['month'] + pd.offsets.MonthEnd(0)
        df['evr_min_demand'] = df['evr_final_demand']
        df['way_di_min_demand'] = df['way_di_final_demand']  # don't need to add wayfair ds demand as that is already in evr_demand_quantity
        df['total_projected_sales'] = df['evr_min_demand'] + df['way_di_min_demand'] + df['amazon_projected_sales_po_quantity']
        df['non_di_sales'] = df['evr_min_demand']
        df['di_sales'] = df['way_di_min_demand'] + df['amazon_projected_sales_po_quantity']

    # remove nan values
    df = df.replace({np.nan: None})

    return df
