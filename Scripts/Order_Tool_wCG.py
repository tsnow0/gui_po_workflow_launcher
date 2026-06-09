#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
import pandas as pd
import shutil
import warnings
import openpyxl
from datetime import datetime
from pathlib import Path
import sys
import pymysql
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
                                   password=password)

    return conn

# ===============================================================================
#import Raw amazon file
def get_cadence_data(filename):
    cadence_df = pd.read_excel(filename,engine='openpyxl')
    cadence_df = cadence_df[['oproduct_sku','Order Cadence']]

    return cadence_df

# ===============================================================================
# Get data from sql files
def get_order_tool_data(conn_read):
    print("Getting Data")
    # Base directory relative to this script
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries"  # ../Queries

    # Load each SQL file
    order_tool_path = folder / "order_tool_data.sql"
    vendor_info_path = folder / "vendor_info.sql"
    inventory_info_path = folder / "inventory_info_query.sql"
    inventory_path = folder / "inventory.sql"

    with open(order_tool_path, "r") as query:
        order_tool_df = pd.read_sql(query.read(), conn_read)
    with open(vendor_info_path, "r") as query:
        vendor_info = pd.read_sql(query.read(), conn_read)
    with open(inventory_info_path, "r") as query:
        inventory_info = pd.read_sql(query.read(), conn_read)
    with open(inventory_path, "r") as query:
        inventory = pd.read_sql(query.read(), conn_read)

    return order_tool_df, inventory
# ===============================================================================
def combine_dataframes(order_tool_df, cadence_df,inventory, test):
    print('Combining Dataframes')

    print(cadence_df.columns)
    # Get today's date
    today = datetime.now()

    # Replace day with 1 to get the first day of the month
    first_day = today.replace(day=1,hour=0, minute=0, second=0, microsecond=0)
    # first_day = pd.to_datetime(first_day)
    print(first_day)

    # merge two datasets
    order_tool_df = order_tool_df.merge(cadence_df, left_on=['SKU'], right_on=['oproduct_sku'], how='left')
    order_tool_df = order_tool_df.merge(inventory, on=['SKU'], how='left')

    order_tool_df['OrderMonth'] = pd.to_datetime(order_tool_df['OrderMonth'])
    order_tool_df = order_tool_df.drop(columns=['oproduct_sku'])
    order_tool_df= order_tool_df.fillna(value={'Order Cadence': 'NA', 'VendorCode': 'NA', 'Category': 'NA', 'Parent': 'NA', 'Tier': 'NA', 'Hold Status': 'NA', 'SKU': 'NA', 'MinOrder': 0, 'ContQuant': 0, 'CBM': 0, 'EVR OrderQty': 0, 'CG OrderQty': 0, 'LandedCost': 0, 'CA_Inv': 0, 'SC_Inv': 0})

    # make Monthly & quarterly  & None datasets
    monthly_df = order_tool_df[order_tool_df['Order Cadence'].isin(['Monthly','Every 2 weeks'])]
    # data_export(monthly_df,"monthly")
    monthly_df = monthly_df[(monthly_df['EVR OrderQty'] + monthly_df['CG OrderQty']) > 0]
    monthly_df = monthly_df[monthly_df['OrderMonth'] == first_day]
    monthly_df['OrderMonth'] = monthly_df['OrderMonth'].dt.date
    monthly_df = monthly_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty','CA_Inv','SC_Inv']]
    monthly_inv = monthly_df[['SC_Inv','CA_Inv']]
    monthly_df = monthly_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty']]

    # Quartely
    quarterly_df = order_tool_df[order_tool_df['Order Cadence'].isin(['Quarterly'])]
    quarterly_df = quarterly_df[(quarterly_df['EVR OrderQty'] + quarterly_df['CG OrderQty']) > 0]
    quarterly_df['OrderMonth'] = quarterly_df['OrderMonth'].dt.date
    quarterly_df = quarterly_df.groupby(['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'CA_Inv', 'SC_Inv'])[['EVR OrderQty', 'CG OrderQty']].sum().reset_index()
    # quarterly_df['CBM'] = None
    quarterly_df = quarterly_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty', 'CA_Inv', 'SC_Inv']]
    quarterly_inv = quarterly_df[['SC_Inv','CA_Inv']]
    quarterly_df = quarterly_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty']]
    # quarterly_df = quarterly_df[quarterly_df['OrderMonth'].isin([month1,month2,month3])]

    # None
    none_df = order_tool_df[(order_tool_df['EVR OrderQty'] + order_tool_df['CG OrderQty']) <= 0]
    # data_export(none_df,"nonebeforesum")
    none_df = none_df.groupby(['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'CA_Inv', 'SC_Inv'])[['EVR OrderQty', 'CG OrderQty']].sum().reset_index()
    # data_export(none_df,"noneaftersum")
    # none_df['CBM'] = None
    # none_df['ContPer'] = 0
    none_df = none_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty', 'CA_Inv', 'SC_Inv']]
    none_inv = none_df[['SC_Inv','CA_Inv']]
    none_df = none_df[['Order Cadence', 'VendorCode', 'Category', 'Parent', 'Tier', 'Hold Status', 'SKU', 'MinOrder', 'ContQuant', 'CBM', 'LandedCost', 'EVR OrderQty', 'CG OrderQty']]

    order_tool_df['OrderMonth'] = order_tool_df['OrderMonth'].dt.date

    # data_export(order_tool_df,"all")
    # data_export(quarterly_df,"quarterly")
    # data_export(monthly_df,"monthly")
    # data_export(none_df,"none")

    output_report('//fileserver/public/Purchasing/Purchase Order Tool Template v2.xlsx', monthly_df, quarterly_df, none_df, order_tool_df, monthly_inv, quarterly_inv, none_inv, test)

    # return monthly_df

# ===============================================================================
def output_report(template_filepath, monthly, quarterly, none, all_data, monthly_inv, quarterly_inv, none_inv, test):
    print('Exporting Data summary to File')
    # Load your existing Excel file
    outpath = '//fileserver/public/Purchasing/EVEREST PO/2026/Purchase Order Tool'
    curyear =  datetime.now().strftime("%Y")
    # curmonth =  datetime.now().strftime("%m")
    curdate = datetime.now().strftime("%Y.%m.%d")

    # Copy ordertool Template
    original_file = "//fileserver/public/Purchasing/Purchase Order Tool Template v2.xlsx"

    new_file = f"{outpath}/Purchase Order Tool {curdate}{' TEST' if test else ''}.xlsx"
    shutil.copy(original_file, new_file)

    # Load the existing workbook
    book = load_workbook(template_filepath)

    # Use 'a' mode and specify that you don't want to overwrite
    with pd.ExcelWriter(new_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:

        # Write the DataFrame starting from that row
        monthly.to_excel(writer, sheet_name='Monthly', startrow=6, startcol=0, index=False, header=False)
        monthly_inv.to_excel(writer, sheet_name='Monthly', startrow=6, startcol=19, index=False, header=False)
        quarterly.to_excel(writer, sheet_name='Quarterly', startrow=6, startcol=0, index=False, header=False)
        quarterly_inv.to_excel(writer, sheet_name='Quarterly', startrow=6, startcol=19, index=False, header=False)
        none.to_excel(writer, sheet_name='Not Ordered', startrow=6, startcol=0, index=False, header=False)
        none_inv.to_excel(writer, sheet_name='Not Ordered', startrow=6, startcol=19, index=False, header=False)
        all_data.to_excel(writer, sheet_name='Data', startrow=1, startcol=0, index=False, header=True)

    # 1. Open the workbook
    file_path = new_file
    wb = load_workbook(file_path)

    # 2. Loop through each sheet
    for sheet in wb.worksheets:
        max_row = sheet.max_row

        # Find the last non-empty cell in Column A
        last_real_row = 0
        for row in range(max_row, 0, -1):  # Scan backwards
            if sheet.cell(row=row, column=1).value not in (None, ''):
                last_real_row = row
                break

        # 3. Delete all rows after the last real row
        if last_real_row < max_row:
            sheet.delete_rows(last_real_row + 1, max_row - last_real_row)
            print(f"Sheet '{sheet.title}': Deleted rows {last_real_row + 1} to {max_row}")

        # 4. Move cursor to A5
        sheet.sheet_view.selection = [openpyxl.worksheet.views.Selection(activeCell="A5", sqref="A5")]


    # 4. Save the workbook
    wb.save(file_path)



# ===============================================================================
def data_export(out_df, name):
    print('Exporting Data to File')

    documents = Path.home() / "Documents"
    folder = documents / f"{name}.xlsx"

    with pd.ExcelWriter(folder, engine='xlsxwriter') as writer:
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
def main(test):
    #
    # NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
    #
    warnings.simplefilter('ignore')
    host_read = connections.host_read
    host_dev = connections.host_dev
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    username = connections.username
    password = connections.password
    if test:
        conn_read = connect(host_dev, database_hq, username, password)
    else:
        conn_read = connect(host_read, database_hq, username, password)
    order_tool_df, inventory = get_order_tool_data(conn_read)
    print(order_tool_df)
    conn_read.close()
    cadence_df = get_cadence_data("//Fileserver/public/Purchasing/EVEREST PO/Order Cadence v01.xlsx")
    print(cadence_df)
    combine_dataframes(order_tool_df, cadence_df, inventory, test)

# ===============================================================================
if __name__ == '__main__':
    test = False
    main(test)