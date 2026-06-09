#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
import pymysql
import pandas as pd
import numpy as np
from datetime import date, datetime
import warnings
from pathlib import Path
import sys
import depletion_logic
import projected_sales
import current_month_demand_adj

# ===============================================================================
def connect(host, database, user, password):
    conn = pymysql.connect(host=host,
                            database=database,
                            user=user,
                            password=password,
                            ssl=False  # PyMySQL uses ssl= instead of ssl_disabled
                           )

    return conn

# ===============================================================================
def remove_missing_information(df):
    missing_data_df = df[df.isna().any(axis=1)]
    df = df[~df.isna().any(axis=1)]
    # Export folder
    export_dir = Path("C:/Project Files/EverRest_US/Database/Projected_Orders/Output").resolve()
    if not export_dir.exists():
        print(f"Please make sure {export_dir} exists")
    else:
        missing_data_df.to_excel(export_dir / "Missing_Data.xlsx", index=False)

    df['current_date'] = df['current_date'].astype(int)
    df['month_date'] = df['month_date'].astype(int)

    return df

# ===============================================================================
def split_wayfair_forecasts(demand_split_df, forecast_df):
    demand_split_df = demand_split_df.pivot(index='oproduct_id', columns='fulfillment', values='demand_split')

    forecast_df = forecast_df.merge(demand_split_df, how='left', on='oproduct_id')

    # if demand split is missing, assume 100 percent DS
    mask = forecast_df['DS'].isnull() & forecast_df['CG'].isnull()
    forecast_df.loc[mask, 'DS'] = 1
    forecast_df.loc[mask, 'CG'] = 0

    # add columns for wayfair di and drophsip forecasts
    forecast_df['way_ds_demand_quantity'] = round(forecast_df['demand_quantity'] * forecast_df['DS'])
    forecast_df['way_di_demand_quantity'] = round(forecast_df['demand_quantity'] * forecast_df['CG'])
    way_ds_forecast_df = forecast_df[['oproduct_id', 'month', 'way_ds_demand_quantity']]
    way_di_forecast_df = forecast_df[['oproduct_id', 'month', 'way_di_demand_quantity']]

    return way_ds_forecast_df, way_di_forecast_df

# ===============================================================================
def combine_dataframes(product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df,
                       lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df,
                       us_di_forecasts_df, ca_di_forecasts_df, backorder_df, cg_inventory_df, cg_po_df,
                       way_ds_forecast_df, way_di_forecasts_df, total_amazon_po_df):

    df = product_df

    # dfs that merge on product id and month
    df_list = [evr_inventory_df, us_di_inventory_df, ca_di_inventory_df, cg_inventory_df,
               evr_po_df, us_di_po_df, ca_di_po_df, cg_po_df, amazon_ds_forecast_df, evr_forecast_df,
               way_ds_forecast_df, us_di_forecasts_df, ca_di_forecasts_df, way_di_forecasts_df, total_amazon_po_df]
    for i in range(0, len(df_list)):
        df = pd.merge(df, df_list[i], on=['oproduct_id', 'month'], how='left')

    # dfs that merge on just product id
    df_list = [backorder_df, safety_stock_df]
    for i in range(0, len(df_list)):
        df = pd.merge(df, df_list[i], on=['oproduct_id'], how='left')

    # merge on vendor
    df = df.merge(lead_time_df, on='vendor_number', how='left')

    # fill NaN values with 0
    df['amazon_ds_demand_quantity'] = df['amazon_ds_demand_quantity'].fillna(0)
    df['evr_demand_quantity'] = df['evr_demand_quantity'].fillna(0)
    df['us_di_demand_quantity'] = df['us_di_demand_quantity'].fillna(0)
    df['ca_di_demand_quantity'] = df['ca_di_demand_quantity'].fillna(0)
    df['way_ds_demand_quantity'] = df['way_ds_demand_quantity'].fillna(0)
    df['way_di_demand_quantity'] = df['way_di_demand_quantity'].fillna(0)
    df['backorder_quantity'] = df['backorder_quantity'].fillna(0)
    df['evr_inventory_quantity'] = df['evr_inventory_quantity'].fillna(0)
    df['us_di_inventory_quantity'] = df['us_di_inventory_quantity'].fillna(0)
    df['ca_di_inventory_quantity'] = df['ca_di_inventory_quantity'].fillna(0)
    df['cg_inventory_quantity'] = df['cg_inventory_quantity'].fillna(0)
    df['evr_po_quantity'] = df['evr_po_quantity'].fillna(0)
    df['us_di_po_quantity'] = df['us_di_po_quantity'].fillna(0)
    df['ca_di_po_quantity'] = df['ca_di_po_quantity'].fillna(0)
    df['cg_po_quantity'] = df['cg_po_quantity'].fillna(0)
    df['safety_stock_quantity'] = df['safety_stock_quantity'].fillna(0)
    df['amazon_projected_sales_po_quantity'] = df['amazon_projected_sales_po_quantity'].fillna(0)

    return df

# ===============================================================================
def projected_orders(df):
    df_list = []
    df['evr_order_quantity'] = np.nan
    df['cg_order_quantity'] = np.nan
    df['order_date'] = np.nan
    df['safety_stock_order_quantity'] = np.nan
    df['demand_order_quantity'] = np.nan
    safety_stock_ordered = False
    previous_product = 0
    today = date.today()
    back_order_placed = 0  # This flag is used to identify when the back order quantity has been accounted for in an order
    evr_beginning_inventory = 0
    us_di_beginning_inventory = 0
    ca_di_beginning_inventory = 0
    cg_beginning_inventory = 0

    # For the current month, adjust the demand quantity and di demand quantity based on the remaining days in the month
    current_month_demand_adj.main(df, today)

    for index, row in df.iterrows():
        # determine if we are calculating projected orders for the next product. If we are, resets the inventory levels
        if row['oproduct_id'] == previous_product:
            # beginning inventory is assigned at the end of this function to account for safety stock
            pass
        else:
            previous_product = row['oproduct_id']
            evr_beginning_inventory = row['evr_inventory_quantity']
            us_di_beginning_inventory = row['us_di_inventory_quantity']
            ca_di_beginning_inventory = row['ca_di_inventory_quantity']
            cg_beginning_inventory = row['cg_inventory_quantity']
            back_order_placed = 0

        # add order date and make sure 'month' at the first of the month
        row['order_date'] = (pd.Timestamp(row['month']) - pd.DateOffset(months=int(row['avg_lead_months']))).replace(day=1).date()
        row['month'] = row['month'].replace(day=1)

        # run depletion logic
        df, index, row, total_evr_demand, evr_demand, us_di_demand, ca_di_demand, way_di_demand, evr_end_inventory, us_di_end_inventory, ca_di_end_inventory, cg_end_inventory, amazon_ds_pct, way_ds_pct, evr_pct = depletion_logic.main(df, index, row, evr_beginning_inventory, us_di_beginning_inventory, ca_di_beginning_inventory, cg_beginning_inventory, 'projected orders')

        back_order_quantity = row['backorder_quantity']

        # If an order would be placed within the lead days set the order quantity
        # to zero because we would not be able to get a PO to our warehouse in time
        # Also set the safety stock ordered flag to zero since it will not prompt an order
        if row['order_date'] < (date.today()).replace(day=1):
            row['evr_order_quantity'] = 0
            row['cg_order_quantity'] = 0
            row['safety_stock_order_quantity'] = 0
            back_order_quantity = 0
        # This is used to add the back order quantity to the first order that is placed
        elif (row['order_date'] >= (date.today()).replace(day=1)) & (back_order_placed == 0) & (evr_end_inventory < back_order_quantity):
            row['evr_order_quantity'] = row['evr_order_quantity'] + (back_order_quantity - max(evr_end_inventory, 0))
            evr_end_inventory = evr_end_inventory - back_order_quantity
            evr_end_inventory = max(evr_end_inventory, 0)
            back_order_placed = 1
        elif (row['order_date'] >= (date.today()).replace(day=1)) & (back_order_placed == 0) & (evr_end_inventory >= back_order_quantity):
            evr_end_inventory = evr_end_inventory - back_order_quantity
            back_order_placed = 1
        else:
            back_order_quantity = 0
        if row['evr_order_quantity'] < 0:
            row['evr_order_quantity'] = 0
            row['safety_stock_order_quantity'] = 0

        row['demand_order_quantity'] = row['evr_order_quantity'] - row['safety_stock_order_quantity']  # split order quantity between demand and safety stock (not really used but its stored in the db table

        # make sure order quantities are whole numbers
        row['evr_order_quantity'] = round(row['evr_order_quantity'], 0)
        row['cg_order_quantity'] = round(row['cg_order_quantity'], 0)

        # update columns and add final demand for output dfs
        df.loc[index, [
            'order_date',
            'month',
            'safety_stock_order_quantity',
            'demand_order_quantity',
            'evr_order_quantity',
            'cg_order_quantity',
            'evr_final_demand',
            'way_di_final_demand'
        ]] = [
            row['order_date'],
            row['month'],
            row['safety_stock_order_quantity'],
            row['demand_order_quantity'],
            row['evr_order_quantity'],
            row['cg_order_quantity'],
            evr_demand,
            way_di_demand
        ]

        # add EVR and CG inventory + po as column for later projected sales calculations
        df.loc[index, 'evr_total_inventory'] = evr_beginning_inventory + row['evr_po_quantity']
        df.loc[index, 'cg_total_inventory'] = cg_beginning_inventory + row['cg_po_quantity']

        # Create steps output
        df_dom = pd.DataFrame([{'Type': 'Domestic', 'Product': row['oproduct_sku'], 'Product_ID': row['oproduct_id'],
                                'Month': row['month'], 'Order Month': row['order_date'], 'Inventory': evr_beginning_inventory,
                                'PO': row['evr_po_quantity'], 'Original Demand': total_evr_demand, 'Final Demand': evr_demand,
                                'Back Order': back_order_quantity, 'SS': row['safety_stock_quantity'], 'End Inventory': evr_end_inventory,
                                'Order Qty': row['evr_order_quantity']}])
        df_us_di = pd.DataFrame([{'Type': 'Direct Import - US', 'Product': row['oproduct_sku'], 'Product_ID': row['oproduct_id'],
                                  'Month': row['month'], 'Order Month': row['order_date'], 'Inventory': us_di_beginning_inventory,
                                  'PO': row['us_di_po_quantity'], 'Original Demand': row['us_di_demand_quantity_adj'],
                                  'Final Demand': us_di_demand, 'Back Order': 0, 'SS': 0, 'End Inventory': us_di_end_inventory,
                                  'Order Qty': 0}])
        df_ca_di = pd.DataFrame([{'Type': 'Direct Import - CA', 'Product': row['oproduct_sku'], 'Product_ID': row['oproduct_id'],
                                  'Month': row['month'], 'Order Month': row['order_date'], 'Inventory': ca_di_beginning_inventory,
                                  'PO': row['ca_di_po_quantity'], 'Original Demand': row['ca_di_demand_quantity_adj'],
                                  'Final Demand': ca_di_demand, 'Back Order': 0, 'SS': 0, 'End Inventory': ca_di_end_inventory,
                                  'Order Qty': 0}])
        df_cg_di = pd.DataFrame([{'Type': 'Direct Import - CG', 'Product': row['oproduct_sku'], 'Product_ID': row['oproduct_id'],
                                  'Month': row['month'], 'Order Month': row['order_date'], 'Inventory': cg_beginning_inventory,
                                  'PO': row['cg_po_quantity'], 'Original Demand': row['way_di_demand_quantity_adj'],
                                  'Final Demand': way_di_demand, 'Back Order': 0, 'SS': 0, 'End Inventory': cg_end_inventory,
                                  'Order Qty': row['cg_order_quantity']}])

        # Append DataFrames to the list
        df_list.append(df_dom)
        df_list.append(df_us_di)
        df_list.append(df_ca_di)
        df_list.append(df_cg_di)

        # if evr ending inventory is less than safety stock and the order date is not in the past, update next month's evr beginning inventory to be safety stock
        if (evr_end_inventory < row['safety_stock_quantity']) & (row['order_date'] >= (date.today()).replace(day=1)):
            evr_beginning_inventory = row['safety_stock_quantity']
        else:
            evr_beginning_inventory = evr_end_inventory
            us_di_beginning_inventory = us_di_end_inventory
            ca_di_beginning_inventory = ca_di_end_inventory
            cg_beginning_inventory = cg_end_inventory

    # Concatenate all DataFrames
    steps_df = pd.concat(df_list, ignore_index=True)

    return df, steps_df

# ===============================================================================
def add_location(df):
    # split df into evr and cg, add location, then combine back together
    evr_df = df[['oproduct_id', 'order_date', 'month', 'safety_stock_order_quantity', 'demand_order_quantity', 'evr_order_quantity']]
    evr_df['location'] = 'EVR'
    evr_df = evr_df.rename(columns={'evr_order_quantity': 'order_quantity'})
    cg_df = df[['oproduct_id', 'order_date', 'month', 'safety_stock_order_quantity', 'demand_order_quantity', 'cg_order_quantity']]
    cg_df['location'] = 'CG'
    cg_df = cg_df.rename(columns={'cg_order_quantity': 'order_quantity'})

    combined_df = pd.concat([evr_df, cg_df], ignore_index=True)

    return combined_df

# ===============================================================================
def truncate_table(conn_write):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"
    with open(folder / 'truncate_projected_orders_query.sql', 'r') as query:
        cursor = conn_write.cursor()
        cursor.execute(query.read())
        conn_write.commit()
        cursor.close()
    with open(folder / 'truncate_projected_sales_with_order_prompts_query.sql', 'r') as query:
        cursor = conn_write.cursor()
        cursor.execute(query.read())
        conn_write.commit()
        cursor.close()

# ===============================================================================
def upload_projected_orders(df, conn_write):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"
    upload_list = df.to_dict('records')
    with open(folder / 'upload_query.sql', 'r') as query:
        cursor = conn_write.cursor()
        cursor.executemany(query.read(), upload_list)
        conn_write.commit()
        cursor.close()

# ===============================================================================
def get_projected_orders_data(conn_read):
    print('Getting Projected Orders Data')
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"
    with open(folder / 'projected_orders_query.sql', 'r') as query:
        projected_orders_df = pd.read_sql(query.read(), conn_read)

    return projected_orders_df

# ===============================================================================
def data_export(projected_orders_df, test):
    print('Exporting Data to File')

    # Base directory
    base_dir = Path(r"\\fileserver\public\Reports\Purchasing\Projected_Orders")
    today = date.today()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Create subfolder by year/month
    subfolder = base_dir / str(today.year) / str(today.month)
    subfolder.mkdir(parents=True, exist_ok=True)

    # Build full file path
    filename = f"Projected_Orders{'_TEST ' if test else ''}_{timestamp}.xlsx"
    filepath = subfolder / filename

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        projected_orders_df.to_excel(excel_writer=writer, sheet_name='Data', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Data']
        for col_num, col_name in enumerate(projected_orders_df.columns):
            column_len = len(col_name) + 10
            worksheet.set_column(col_num, col_num, column_len)
        (max_row, max_col) = projected_orders_df.shape
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        worksheet.freeze_panes(1, 0)
        workbook.set_properties({'author': 'Analytics'})
        workbook.read_only_recommended()
    writer.close()

# ===============================================================================
def order_steps_export(df, test):
    print('Exporting Data to File')
    # Base directory
    base_dir = Path(r"\\fileserver\public\Reports\Purchasing\Projected_Orders")
    today = date.today()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Create subfolder by year/month
    subfolder = base_dir / str(today.year) / str(today.month)
    subfolder.mkdir(parents=True, exist_ok=True)

    # Build full file path
    filename = f"Projected_Orders_Steps{'_TEST ' if test else ''}_{timestamp}.xlsx"
    filepath = subfolder / filename

    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df.to_excel(excel_writer=writer, sheet_name='Data', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Data']
        for col_num, col_name in enumerate(df.columns):
            column_len = len(col_name) + 10
            worksheet.set_column(col_num, col_num, column_len)
        (max_row, max_col) = df.shape
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        worksheet.freeze_panes(1, 0)
        workbook.set_properties({'author': 'Analytics'})
        workbook.read_only_recommended()
    writer.close()

# ===============================================================================
def upload_projected_sales(df, conn_write):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"
    upload_list = df.to_dict('records')
    with open(folder / 'upload_projected_sales_with_order_prompts.sql', 'r') as query:
        cursor = conn_write.cursor()
        cursor.executemany(query.read(), upload_list)
        conn_write.commit()
        cursor.close()

# ===============================================================================
def main(host_read, host_dev, host_write, database_hq, user, password, product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df, lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df, us_di_forecasts_df, ca_di_forecasts_df, backorder_df, cg_inventory_df, cg_po_df, way_demand_split_df, way_forecast_df, total_amazon_po_df, test, output_flag):
    warnings.simplefilter('ignore')

    print('Split Wayfair forecasts by demand % and add evr line to evr_forecasts')
    way_ds_forecast_df, way_di_forecasts_df = split_wayfair_forecasts(way_demand_split_df, way_forecast_df)

    print('Combining Dataframes')
    df = combine_dataframes(product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df, lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df, us_di_forecasts_df, ca_di_forecasts_df, backorder_df, cg_inventory_df, cg_po_df, way_ds_forecast_df, way_di_forecasts_df, total_amazon_po_df)

    print('Outputting File With Missing Data')
    df = remove_missing_information(df)

    print('Determining Orders')
    df, results_df = projected_orders(df)

    print('Calculating Projected Sales')
    df = projected_sales.main(df, 'projected orders')
    projected_sales_upload_df = df[['oproduct_id', 'end_date', 'non_di_sales', 'di_sales', 'total_projected_sales']]

    print('clean up dates')
    df['month'] = df['month'].dt.strftime('%Y-%m-%d')
    df['end_date'] = df['end_date'].dt.strftime('%Y-%m-%d')
    projected_sales_upload_df['end_date'] = projected_sales_upload_df['end_date'].dt.strftime('%Y-%m-%d')
    results_df['Month'] = results_df['Month'].dt.strftime('%Y-%m-%d')

    print('split df into evr and cg, add location, then combine back together')
    df = add_location(df)

    if not test:
        conn_write = connect(host_write, database_hq, user, password)
        print('Truncating Table')
        truncate_table(conn_write)
        print('Uploading Projected Orders')
        upload_projected_orders(df, conn_write)
        conn_write.close()
        conn_read = connect(host_read, database_hq, user, password)
        projected_orders_df = get_projected_orders_data(conn_read)
        conn_read.close()
        if output_flag:
            data_export(projected_orders_df, test)
            order_steps_export(results_df, test)
        print('Uploading Projected Sales')
        conn_write = connect(host_write, database_hq, user, password)
        upload_projected_sales(projected_sales_upload_df, conn_write)
        conn_write.close()
    elif test:
        conn_write = connect(host_dev, database_hq, user, password)
        print('Truncating Table')
        truncate_table(conn_write)
        print('Uploading Projected Orders')
        upload_projected_orders(df, conn_write)
        conn_write.close()
        conn_read = connect(host_dev, database_hq, user, password)
        projected_orders_df = get_projected_orders_data(conn_read)
        conn_read.close()
        if output_flag:
            data_export(projected_orders_df, test)
            order_steps_export(results_df, test)
        print('Uploading Projected Sales')
        conn_write = connect(host_dev, database_hq, user, password)
        upload_projected_sales(projected_sales_upload_df, conn_write)
        conn_write.close()
