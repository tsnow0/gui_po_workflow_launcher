#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#      AND MAKE SURE TO FIX CONNECTIONS IMPORT
#
import numpy as np
import pandas as pd
import warnings
import time as t
import math
import sys
import pymysql
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook

# if running local
# import keyring as kr
# cur_dir = Path(__file__).parent
# sys.path.append(str(cur_dir / '../../../../../../Credentials'))
# import connections

# if running with GUI (keep this as default so it works when any updates are made and copied to the GUI repo)
import connections_for_containerization_gui as connections


# ===============================================================================
def connect(host, database, user, password):
    conn = pymysql.connect(host=host,
                           database=database,
                           user=user,
                           password=password,
                          )

    return conn


# ===============================================================================
# import Raw amazon file ORIGINAl
# def get_suggested_order_data(filename):
#     suggest_orders = pd.read_excel(filename,engine='openpyxl')
#     print(suggest_orders.head())
#
#     return suggested_orders

# ===============================================================================
# import Data from Order tool.
def get_suggested_order_data(filename):
    print("here1")
    monthly_df = pd.read_excel(filename, engine='openpyxl', sheet_name='Monthly', skiprows=5, usecols='A:S')
    quarterly_df = pd.read_excel(filename, engine='openpyxl', sheet_name='Quarterly', skiprows=5, usecols='A:S')
    none_df = pd.read_excel(filename, engine='openpyxl', sheet_name='Not Ordered', skiprows=5, usecols='A:S')


    # data_export1(monthly_df,'monthly_df')


    # Monthly df
    monthly_df_ev = monthly_df[['SKU', 'VendorCode','ContQuant', 'CBM', 'Adjusted EVR Order Quantity', '% East', '% West']][
        monthly_df['Adjusted EVR Order Quantity'] > 0]
    monthly_df_cg = monthly_df[['SKU', 'VendorCode','ContQuant', 'CBM', 'Adjusted CG Order Quantity']][
        monthly_df['Adjusted CG Order Quantity'] > 0]


    # quarterly df
    quarterly_df_ev = quarterly_df[['SKU', 'VendorCode', 'ContQuant', 'CBM','Adjusted EVR Order Quantity', '% East', '% West']][
        quarterly_df['Adjusted EVR Order Quantity'] > 0]
    quarterly_df_cg = quarterly_df[['SKU', 'VendorCode', 'ContQuant', 'CBM','Adjusted CG Order Quantity']][
        quarterly_df['Adjusted CG Order Quantity'] > 0]

    # none df
    none_df_ev = none_df[['SKU', 'VendorCode','ContQuant', 'CBM', 'Adjusted EVR Order Quantity', '% East', '% West']][
        none_df['Adjusted EVR Order Quantity'] > 0]
    none_df_cg = none_df[['SKU', 'VendorCode','ContQuant', 'CBM', 'Adjusted CG Order Quantity']][
        none_df['Adjusted CG Order Quantity'] > 0]
    
    t_sug_order_ev = pd.concat([monthly_df_ev, quarterly_df_ev, none_df_ev])
    t_sug_order_cg = pd.concat([monthly_df_cg, quarterly_df_cg, none_df_cg])



    t_sug_order_east = pd.DataFrame(columns=['oproduct_sku', 'Vendor','ContQuant', 'CBM', 'Location', 'order_quantity'])
    t_sug_order_east['oproduct_sku'] = t_sug_order_ev['SKU']
    t_sug_order_east['Vendor'] = t_sug_order_ev['VendorCode']
    t_sug_order_east['ContQuant'] = t_sug_order_ev['ContQuant']
    t_sug_order_east['CBM'] = t_sug_order_ev['CBM']
    t_sug_order_east['order_quantity'] = np.ceil(t_sug_order_ev['Adjusted EVR Order Quantity'] * t_sug_order_ev['% East'])
    t_sug_order_east['Location'] = 'South Carolina'
    data_export1(t_sug_order_east,'t_sug_order_east')

    t_sug_order_west = pd.DataFrame(columns=['oproduct_sku', 'Vendor', 'ContQuant', 'CBM','Location', 'order_quantity'])
    t_sug_order_west['oproduct_sku'] = t_sug_order_ev['SKU']
    t_sug_order_west['Vendor'] = t_sug_order_ev['VendorCode']
    t_sug_order_west['ContQuant'] = t_sug_order_ev['ContQuant']
    t_sug_order_west['CBM'] = t_sug_order_ev['CBM']
    t_sug_order_west['order_quantity'] = np.ceil(t_sug_order_ev['Adjusted EVR Order Quantity'] * t_sug_order_ev['% West'])
    t_sug_order_west['Location'] = 'California'

    t_sug_order_cg['oproduct_sku'] = t_sug_order_cg['SKU']
    t_sug_order_cg['Vendor'] = t_sug_order_cg['VendorCode']
    t_sug_order_cg['order_quantity'] =t_sug_order_cg['Adjusted CG Order Quantity']
    t_sug_order_cg['Location'] ='Castlegate'
    t_sug_order_cg = t_sug_order_cg[['oproduct_sku', 'Vendor', 'ContQuant', 'CBM','Location','order_quantity']]
    # print(t_sug_order_cg.columns)

    suggested_orders = pd.concat([t_sug_order_east, t_sug_order_west,t_sug_order_cg])
    suggested_orders = suggested_orders[suggested_orders['order_quantity'] > 0]


    data_export1(suggested_orders,'suggested_orders')
    # suggested_orders = pd.concat([suggested_orders, suggested_orders_cg, none_df_ev])


    return suggested_orders


# ===============================================================================
def data_export1(out_df, name):
    filepath = Path('C:/Repositories/Analytics_Repository/Analysis_Projects/Containerization')
    filepath.mkdir(parents=True, exist_ok=True)
    export_path = filepath / f"{name}.xlsx"

    print(f'Exporting {name} to {export_path}')
    with pd.ExcelWriter(export_path, engine='xlsxwriter') as writer:
        out_df.to_excel(excel_writer=writer, sheet_name='Data', index=False)
        worksheet = writer.sheets['Data']
        for col_num, col_name in enumerate(out_df.columns):
            column_len = len(col_name) + 10
            worksheet.set_column(col_num, col_num, column_len)
        (max_row, max_col) = out_df.shape
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        worksheet.freeze_panes(1, 0)
    writer.close()


# ===============================================================================
# Get data from sql files
def get_vendor_data(conn_read):
    print('Getting Data')
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"

    with open(folder / 'vendor_query.sql', 'r') as query:
        vendor_quantities = pd.read_sql(query.read(), conn_read)
        vendor_quantities =vendor_quantities[['ovendor_id', 'Category', 'Parent', 'oproduct_sku', 'opvd_case_pack_qty', 'FOBCost', 'LandedCost']]
    with open(folder / 'vendor_info.sql', 'r') as query:
        vendor_info = pd.read_sql(query.read(), conn_read)
    with open(folder / 'inventory_info_query.sql', 'r') as query:
        inventory_info = pd.read_sql(query.read(), conn_read)
    # rename columns
    vendor_quantities.rename(columns={'ContQuant': 'container_quantity'}, inplace=True)

    return vendor_quantities, vendor_info, inventory_info


# ===============================================================================
def combine_dataframes(vendor_quantities, vendor_info, inventory_info, suggested_order):
    print('Combining Dataframes')
    order_df = suggested_order.merge(inventory_info, on=['Location'], how='left')
    # print(len(order_df))
    order_df = order_df.merge(vendor_quantities, on=['oproduct_sku'], how='left')
    order_df = order_df.merge(vendor_info, on=['ovendor_id'], how='left')

    order_df['container_percentage'] = order_df['order_quantity'] / order_df['ContQuant']
    # Now create sums by category and parent
    category_total = order_df.groupby(['ovendor_code', 'Location', 'Category'])[
        'container_percentage'].sum().reset_index()
    category_total = category_total.rename(columns={'container_percentage': 'Category_Container_Total'})
    parent_total = order_df.groupby(['ovendor_code', 'Location', 'Category', 'Parent'])[
        'container_percentage'].sum().reset_index()

    parent_total = parent_total.rename(columns={'container_percentage': 'Parent_Container_Total'})
    order_df = pd.merge(order_df, category_total, how='left', on=['ovendor_code', 'Location', 'Category'])
    order_df = pd.merge(order_df, parent_total, how='left', on=['ovendor_code', 'Location', 'Category', 'Parent'])
    # add index for location/ vendor
    order_df['lane'] = order_df['ovendor_code'] + '_' + order_df['Location']
    # add in some last variables used to process
    order_df['order_quantity'] = order_df['order_quantity'].round()
    order_df['order_quantity_orig'] = order_df['order_quantity']
    order_df['container_percentage_orig'] = order_df['container_percentage']

    # Now sort to make the process easier
    order_df = order_df.sort_values(
        by=['lane', 'Category_Container_Total', 'Parent_Container_Total', 'container_percentage'],
        ascending=[True, False, False, False])
    order_df.dropna(subset=['ContQuant'], inplace=True)
    order_df['max_lane_container_number'] = 1
    # order_df['container_quantity'] = round(70/order_df['CBM'],0)

    # max_lane_container_number = order_df.groupby(['lane'])['max_lane_container_number'].sum().reset_index()
    # # print(f'{max_lane_container_number[max_lane_container_number['lane'] == 'VMD_California']}')
    # order_df = order_df.merge(max_lane_container_number, on=['lane'], how='left')
    # order_df.rename(columns={'max_lane_container_number_y': 'max_lane_container_number'}, inplace=True)
    # order_df = order_df.drop('max_lane_container_number_x', axis=1)



    order_df = order_df[['oproduct_sku', 'Vendor', 'ContQuant', 'CBM', 'Location', 'order_quantity', 'Category', 'Parent', 'container_percentage', 'lane','max_lane_container_number','opvd_case_pack_qty','FOBCost','LandedCost']]
    data_export1(order_df, 'order_df')
    return order_df


# ===============================================================================
def containerize_full_single_sku(order_df):
    print('First fill out full containers')
    previous_lane = None
    order_df['order_quantity_orig']= order_df['order_quantity']
    container = 1
    container_fill = 0
    max_container_number = 0
    for index, row in order_df.iterrows():
        if row['lane'] == previous_lane:
            pass
        else:
            previous_lane = row['lane']
            container = 1
            container_fill = 0
        remaining_quantity = 0
        remaining_units = True
        container_percentage = row['container_percentage']
        order_quantity = row['order_quantity']
        full_container_quantity = row['ContQuant']

        while container_percentage >= 1:
            order_df.at[index, f"cont_{container}"] = full_container_quantity
            # print(f'index:{index} sku:{order_df.at[index, 'SKUVen']} cont:{container} ')
            # print(full_container_quantity)
            order_quantity = order_quantity - full_container_quantity
            # print(order_quantity)
            container_percentage = order_quantity / full_container_quantity
            # print(container_percentage)
            remaining_quantity = order_quantity
            # print(f'index:{index} sku:{ order_df.at[index,'SKUVen']} cont:{container} ordered:{order_df.at[index, f"cont_{container}"]} qtyleft:{order_quantity}')
            container += 1
        # Now updated values
        if container > 1:
            order_df.at[index, 'container_percentage'] = container_percentage
            order_df.at[index, 'order_quantity'] = order_quantity
            order_df.at[index, 'max_lane_container_number'] = container
            # print(f'{container}')
            # print(f'{order_df.at[index,'container_percentage']}')
            # print(f'{order_df.at[index,'order_quantity']}')

    # extract max container per lane
    max_lane_container_number = order_df.groupby(['lane'])['max_lane_container_number'].max().reset_index()
    print(max_lane_container_number)
    order_df = order_df.merge(max_lane_container_number, on=['lane'], how='left')
    order_df.rename(columns={'max_lane_container_number_y': 'max_lane_container_number'}, inplace=True)
    order_df = order_df.drop('max_lane_container_number_x', axis=1)

    data_export1(order_df, 'order_df')
    return order_df


# ===============================================================================
def containerize_units(order_df):

    print('Mixed Containers Units')
    fill_CBM = 66
    # order_df = order_df[order_df['Vendor'] =='NMF']
    # order_df = order_df[order_df['Location'] =='California']
    # fill_percent = 0.96
    previous_lane = None
    container = 1
    container_fill_CBM = 0
    max_container_number = 0
    for index, row in order_df.iterrows():
        if row['lane'] == previous_lane:
            pass
        else:
            previous_lane = row['lane']
            print(row['lane'])
            container = row['max_lane_container_number']
            container_fill_CBM = 0
        remaining_quantity = 0
        remaining_units = True
        skuCBM = row['CBM']
        order_quantity_cbm = row['order_quantity'] * skuCBM
        # container_percentage = row['container_percentage']
        order_quantity = row['order_quantity']
        while remaining_units is True:
            if (container_fill_CBM + order_quantity_cbm) <= fill_CBM:
                print('Run less than 66 CBM')
                # if (container_fill_CBM + container_percentage) <= fill_percent:
                # if row['lane'] == 'VMD_California':
                #     print(container_percentage)
                # print(F'Main contfill:{container_fill_CBM} ConCBM:{order_quantity_cbm}')
                current_container_quantity = order_quantity + remaining_quantity
                container_fill_CBM = container_fill_CBM + order_quantity_cbm
                # container_fill_CBM = container_fill_CBM + container_percentage
                order_df.at[index, f"cont_{container}"] = current_container_quantity
                print(f"cont_{container}")
                print(f"SKU:{row['oproduct_sku']}, Loc:{row['Location']}, OQ:{current_container_quantity}, QF:{container_fill_CBM}, CQCMB:{order_quantity_cbm}")
            else:
                print('Run more than 66 CBM')
                # Identifies how much remaining room is available in the container
                remaining_CBM = fill_CBM - container_fill_CBM
                print(F'Remaining contfill:{container_fill_CBM} ConPer:{remaining_CBM}')

                # Calculates how much of the remaining order will fit in the container
                current_container_quantity = round(remaining_CBM / skuCBM,0)
                order_df.at[index, f"cont_{container}"] = current_container_quantity
                print(current_container_quantity)
                container_fill_CBM = container_fill_CBM + remaining_CBM

                # Calculates the remaining container CBM that was not put in the container
                left_over_container_CBM = fill_CBM - container_fill_CBM
                print(F'Remaining contfill:{container_fill_CBM} RemainCBM:{remaining_CBM}')

                # Calculates the remaining order quantity that did not fit in the container
                remaining_quantity = round(order_quantity - current_container_quantity,0)
                container += 1
                print(f"SKU:{row['oproduct_sku']}, Loc:{row['Location']}, OQ:{remaining_quantity}, QF:{container_fill_CBM}, Cont:{container}")
            # print(f'SKU:{row['oproduct_sku']}, Loc:{row['Location']}, OQ:{current_container_quantity}, QF:{container_fill_CBM}')
            if remaining_quantity > 0:
                order_quantity = remaining_quantity
                order_quantity_cbm = order_quantity * skuCBM
                container_fill_CBM = 0
                # container_percentage = left_over_container_CBM
                remaining_quantity = 0
                remaining_units = True
                print(order_quantity)
                print(order_quantity_cbm)
            else:
                remaining_units = False
                # container_percentage = fill_percent - container_fill_CBM
            if container > max_container_number:
                max_container_number = container
            order_df.at[index, 'max_lane_container_number'] = container
            print('End fill loop')

        previous_lane = row['lane']

        max_lane_container_number = order_df.groupby(['lane'])['max_lane_container_number'].max().reset_index()
        # print(f'{max_lane_container_number[max_lane_container_number['lane'] == 'VMD_California']}')
        order_df = order_df.merge(max_lane_container_number, on=['lane'], how='left')
        order_df.rename(columns={'max_lane_container_number_y': 'max_lane_container_number'}, inplace=True)
        order_df = order_df.drop('max_lane_container_number_x', axis=1)

    # order_df_test = order_df[['oproduct_sku', 'Vendor', 'Location', 'container_quantity', 'CBM','order_quantity', 'order_quantity_orig', 'cont_1', 'cont_2' ]]

    data_export1(order_df, 'second_run2')

    return order_df, max_container_number


# ===============================================================================
def update_case_pack(order_df, max_container_number):
    print('Adjusting Case Pack Quantities')
    for index, row in order_df.iterrows():
        case_pack = row['opvd_case_pack_qty']
        container_qty = row['ContQuant']
        lane = row['lane']
        if case_pack == 1:
            pass
        else:
            container = 1
            while container <= max_container_number:
                cur_order = row[f'cont_{container}']
                # print(f'inde:{index} {lane} {case_pack} {container_qty}')
                if cur_order < container_qty:
                    # print(f'cont_{container}')
                    # print(f'cur_order: {cur_order}')
                    # print(row['oproduct_sku'])
                    order_df.at[index, f"cont_{container}"] = math.ceil(
                        order_df.at[index, f"cont_{container}"] / case_pack) * case_pack
                container += 1

    data_export1(order_df, 'containerized')
    return order_df

# ===============================================================================
def create_container_percent_columns(order_df, max_container_number):
    print('Calculating Container Percentage Columns')
    container = 1
    while container <= max_container_number:
        order_df[f'cont_cbm_{container}'] = order_df[f'cont_{container}'] * order_df['CBM']
        container += 1

    data_export1(order_df, 'containerized')
    return order_df


# ===============================================================================
def output_clean_datafile(order_df,vendor_info):
    print('Clean up data and output for review')
    order_df = order_df.merge(vendor_info, left_on=['Vendor'], right_on=['ovendor_code'], how='left')
    # Create new folder based on day of order place
    curyear = datetime.now().strftime("%Y")
    # curmonth =  datetime.now().strftime("%m")
    curdate = datetime.now().strftime("%Y.%m.%d")

    # Create some lists
    vendors = order_df['Vendor'].unique().tolist()
    containers_per_vendor = order_df.groupby(['Vendor', 'Location', 'lane'])[
        'max_lane_container_number'].max().reset_index()

    # print(containers_per_vendor.head())
    container_columns = [col for col in order_df.columns if 'cont_' in col]
    columns_to_keep2 = ['lane', 'Location', 'oproduct_sku', 'ContQuant', 'CBM', 'order_quantity_orig', 'Vendor',
                        'ovendor_name', 'ovendor_external_id', 'max_lane_container_number', 'opvd_case_pack_qty']
    columns_to_keep = columns_to_keep2 + container_columns


    print(columns_to_keep)
    print(order_df.columns)
    t_df = order_df[columns_to_keep]

    t_df.rename(columns={'oproduct_sku': 'SKU', 'Vendor': 'Code', 'ovendor_name': 'Name',
                         'ovendor_external_id': 'ExternalID', 'ContQuant': 'Cont_Qty','CBM':'CBM',
                         'opvd_case_pack_qty': 'CasePackQty', 'order_quantity_orig': 'Quantity'}, inplace=True)

    rearranged_columns = ['Location', 'Code', 'Name', 'ExternalID', 'SKU', 'Quantity', 'Cont_Qty', 'CBM', 'CasePackQty']
    # Leave the rest of the columns unchanged
    other_columns = [col for col in t_df.columns if col not in rearranged_columns]
    new_column_order = rearranged_columns + other_columns
    t_df = t_df[new_column_order]
    print('new T_df')
    data_export1(t_df, 't_df')

    for index, row in containers_per_vendor.iterrows():
        previous_vendor = row['Vendor']
        current_location = row['Location']
        folder_path = Path(f"//fileserver/public/Purchasing/EVEREST PO") / str(curyear) / str(curdate)
        folder_path.mkdir(parents=True, exist_ok=True)  # create folder if it doesn't exist

        # filter data
        t_out_df = t_df[t_df['lane'] == row['lane']]
        columns_to_drop = [col for col in container_columns if
                           '_' in col and int(col.split('_')[-1]) > row['max_lane_container_number']]
        t_out_df = t_out_df.drop(columns=columns_to_drop)
        maxcont = row['max_lane_container_number']
        t_out_df = t_out_df.drop(columns=['max_lane_container_number', 'lane'])

        #export if not empty
        if t_out_df.empty is False:
            export_containerized_orders(t_out_df, row['lane'], folder_path, curdate)
            file_path = f"{folder_path}/PO {row['lane']} {curdate}.xlsx"
            update_excel_formulas(file_path, maxcont)
    return order_df


# ===============================================================================
def create_summary_report(order_df):
    """Convert a column number to an Excel column letter."""
    summary_df = order_df
    summary_df['Extended_FOB_Cost'] = summary_df['order_quantity'] * summary_df['FOBCost']
    summary_df['Extended_Landed_Cost'] = summary_df['order_quantity'] * summary_df['LandedCost']

    summary_df1 = summary_df.groupby(['Vendor'])['order_quantity'].sum().reset_index()
    summary_df2 = summary_df.groupby(['Vendor'])['container_percentage'].sum().reset_index()
    summary_df3 = summary_df.groupby(['Vendor'])['Extended_FOB_Cost'].sum().reset_index()
    summary_df4 = summary_df.groupby(['Vendor'])['Extended_Landed_Cost'].sum().reset_index()

    summary_all = summary_df1.merge(summary_df2, on=['Vendor'], how='left')
    summary_all = summary_all.merge(summary_df3, on=['Vendor'], how='left')
    summary_all = summary_all.merge(summary_df4, on=['Vendor'], how='left')

    summary_all.rename(
        columns={'Vendor': 'Vendor', 'container_percentage': 'Containers', 'Extended_FOB_Cost': 'FOB Cost',
                 'Extended_Landed_Cost': 'Landed Cost', 'order_quanity': 'Quantity'}, inplace=True)

    curyear = datetime.now().strftime("%Y")
    # curmonth =  datetime.now().strftime("%m")
    curdate = datetime.now().strftime("%Y.%m.%d")
    data_export_summary(summary_all, curyear, curdate)

    filepath = f"//fileserver/public/Purchasing/EVEREST PO/{curyear}/PO Summary {curdate}.xlsx"
    update_summary_file(filepath)

    return t

# ===============================================================================
def update_excel_formulas(file_path, maxcont):
    print('Exporting Data to File')
    print(file_path)

    wb = load_workbook(file_path)
    ws = wb.active
    print('this')
    max_row = ws.max_row
    max_col = ws.max_column
    last_cont_col = number_to_excel_column(max_col - maxcont)
    print(last_cont_col)
    ws.cell(row=2, column=max_col + 1, value="Remaining")
    for col in range(10, 10 + maxcont):  # Skip header row
        TotColLet = number_to_excel_column(col + maxcont)
        ws.cell(row=1, column=col, value=f"=round(SUM({TotColLet}3:{TotColLet}{max_row}),2)")
        for row in range(3, max_row + 1):
            col_let = number_to_excel_column(col)
            ws.cell(row=row, column=col + maxcont, value=f"=IF(G{row} = {col_let}{row},1,({col_let}{row}*H{row})/66)")
            ws.cell(row=row, column=col + maxcont + 1, value=f"=F{row} - SUM(J{row}:{last_cont_col}{row})")
        # ws[f"R3"] = f"=SUM(G3:AI3)"  # Example: Multiply column C by 2
        # adjust columm width
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name (e.g., 'A', 'B', etc.)
        col_number = col[0].column
        if col_number > 8:
            adjusted_width = 8
        else:
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)  # Adding 2 for some padding
        ws.column_dimensions[column].width = adjusted_width

    # Hide columns
    for col_num in range(10 + maxcont, max_col + 1):
        col_letter = number_to_excel_column(col_num)
        ws.column_dimensions[col_letter].hidden = True
    ws.freeze_panes = "J3"
    wb.save(file_path)


# ===============================================================================
def data_export_summary(order_df, curyear, curdate):
    print('Exporting Data summary to File')
    filepath = Path("//fileserver/public/Purchasing/EVEREST PO") / curyear
    filepath.mkdir(parents=True, exist_ok=True)  # optional
    export_path = filepath / f"PO Summary {curdate}.xlsx"

    with pd.ExcelWriter(export_path, engine="xlsxwriter") as writer:
        order_df.to_excel(excel_writer=writer, sheet_name='Data', index=False, startrow=1)
        worksheet = writer.sheets['Data']
        for col_num, col_name in enumerate(order_df.columns):
            column_len = len(col_name) + 5
            worksheet.set_column(col_num, col_num, column_len)
        # (max_row, max_col) = order_df.shape
        # worksheet.autofilter(0, 0, max_row, max_col - 1)
        # worksheet.freeze_panes(, 0)
    writer.close()


# ===============================================================================
def update_summary_file(file_path):
    print('Exporting Data to File')
    print(file_path)
    wb = load_workbook(file_path)
    ws = wb.active
    # worksheet = writer.sheets['Data']
    max_row = ws.max_row
    max_col = ws.max_column
    ws.cell(row=1, column=2, value=f"=sum(B2:B{max_row})")
    ws.cell(row=1, column=3, value=f"=sum(C2:C{max_row})")
    ws.cell(row=1, column=4, value=f"=sum(D2:D{max_row})")
    ws.cell(row=1, column=5, value=f"=sum(E2:E{max_row})")
    ws['B1'].number_format = '#,##0'  # Format column A as short date
    ws['C1'].number_format = '#,##0.00'  # Format column B as a number with two decimals
    ws['D1'].number_format = '#,##0.00'
    ws['E1'].number_format = '#,##0.00'

    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=6):
        row[1].number_format = '#,##0'
        row[2].number_format = '#,##0.00'  # Format column B as a number with two decimals
        row[3].number_format = '#,##0'
        row[4].number_format = '#,##0'
    ws.freeze_panes = "A3"
    wb.save(file_path)


# ===============================================================================
def export_containerized_orders(df, vendor, folder_path, curdate):
    print('Exporting Data to File')
    export_dir = Path(folder_path)
    export_dir.mkdir(parents=True, exist_ok=True)  # optional safety
    export_path = export_dir / f"PO {vendor} {curdate}.xlsx"

    with pd.ExcelWriter(export_path, engine="xlsxwriter") as writer:
        df.to_excel(excel_writer=writer, sheet_name='Data', index=False, startrow=1)
        wb = writer.book
        ws = writer.sheets['Data']

        for col_num, col_name in enumerate(df.columns):
            column_len = len(col_name) + 5
            ws.set_column(col_num, col_num, column_len)

        ws.freeze_panes(2, 0)
    writer.close()


# ===============================================================================
def number_to_excel_column(n):
    """Convert a column number to an Excel column letter."""
    column = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        column = chr(65 + remainder) + column
    return column

# ============================= ==================================================
def main(filename):
    #
    # NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
    #      AND MAKE SURE TO FIX CONNECTIONS IMPORT
    #
    warnings.simplefilter('ignore')
    host_read = connections.host_read
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    username = connections.username
    password = connections.password
    conn_read = connect(host_read, database_hq, username, password)
    vendor_quantities, vendor_info, inventory_info = get_vendor_data(conn_read)
    conn_read.close()
    # suggested_order = get_suggested_order_data("//fileserver/public/Purchasing/EVEREST PO/2025/Orders to be processed/Purchase_Orders 2025.05.06.xlsx")
    suggested_order = get_suggested_order_data(filename)

    order_df = combine_dataframes(vendor_quantities, vendor_info, inventory_info, suggested_order)
    # # order_df = order_df[order_df['ovendor_code'] == 'VMD']
    order_df = containerize_full_single_sku(order_df)
    order_df, max_container_number = containerize_units(order_df)
    order_df = update_case_pack(order_df, max_container_number)
    order_df = create_container_percent_columns(order_df, max_container_number)
    t=create_summary_report(order_df)
    order_df = output_clean_datafile(order_df,vendor_info)
    # data_export(order_df)


# ===============================================================================
if __name__ == '__main__':
    main(filename="//fileserver/public/Purchasing/EVEREST PO/2026/Purchase Order Tool/Purchase Order Tool 2026.02.19_USE THIS.xlsx")