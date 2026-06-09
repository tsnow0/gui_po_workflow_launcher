import pymysql
import pandas as pd
import numpy as np
from datetime import date, datetime
import warnings
from pathlib import Path
import sys

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
                            ssl=False # PyMySQL uses ssl= instead of ssl_disabled
                           )

    return conn

# ===============================================================================
def load_query_df(filename, conn, parse_month=False):
    with open(filename, "r") as f:
        df = pd.read_sql(f.read(), conn)
    if parse_month and "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"])
    return df

# ===============================================================================
def get_data(conn):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Replacement Part Order Prompt"

    print('Getting reorder products Data')
    reorder_point_df = load_query_df(folder / "reorder_products.sql", conn)
    print('Getting inventory Data')
    inventory_df = load_query_df(folder / "inventory.sql", conn)
    print('Getting on order data')
    po_data = load_query_df(folder / "on_order.sql", conn)
    print('Getting backorders Data')
    backorders_df = load_query_df(folder / "backorders.sql", conn)

    print('Combine data - outer join to make sure we arent missing any products')
    df = reorder_point_df.merge(inventory_df, how='outer', on='product')
    df = df.merge(po_data, how='outer', on='product')
    df = df.merge(backorders_df, how='outer', on='product')

    return df

# ===============================================================================
def clean_data(df):
    df['max'] = df['max'].fillna(0)
    df['inventory_quantity'] = df['inventory_quantity'].fillna(0)
    df['po_quantity'] = df['po_quantity'].fillna(0)
    df['backorder_quantity'] = df['backorder_quantity'].fillna(0)

# ===============================================================================
def missing_reorder_points(df, notify):
    missing_reorder_point_df = df[(df['max'] == 0) | (df['min'].isna())]
    df = df[~df['product'].isin(missing_reorder_point_df['product'])]

    if not missing_reorder_point_df.empty:
        # put in csv and save to downloads folder
        downloads_path = Path.home() / "Downloads"
        filename = f'missing_reorder_points_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.csv'
        missing_reorder_point_df.to_csv(downloads_path / filename, index=False)

        # print message to user - process will still run but these skus aren't going to be included
        if notify:
            notify(f"Warning: There are {len(missing_reorder_point_df)} products with a max reorder point of 0."
                  f"\nThese products have been exported to your Downloads folder and will not be included in the order prompt."
                  f"\nUse the Export and Import buttons to update the reorder points then rerun the order prompt if needed."
                  f"\nClick OK to Continue")
        else:
            print(f"Warning: There are {len(missing_reorder_point_df)} products with a max reorder point of 0."
                  f"\nThese products have been exported to your Downloads folder and will not be included in the order prompt."
                  f"\nUse the Export and Import buttons to update the reorder points then rerun the order prompt if needed."
                  f"\nClick OK to Continue")

    return df
# ===============================================================================
def order_prompt(df):
    # remaining inventory is current inventory + purchase orders - backorders
    df['remaining_inventory'] = df['inventory_quantity'] + df['po_quantity'] - df['backorder_quantity']

    # if remaining inventory is below the min reorder point, 'low', if above the max reorder point, 'high', else 'in range'
    df['reorder_status'] = np.where(df['remaining_inventory'] < df['min'], 'low', np.where(df['remaining_inventory'] > df['max'], 'high', 'in range'))

    # if the item is active, and the reorder status is low, then check if min is available, if so, order min, if not, order enough to reach max, else 0
    df['order_quantity'] = np.where((df['reorder_status'] == 'low') & (df['item_status'] == 'ACTIVE'), np.maximum(0, df['max'] - df['remaining_inventory']), 0)

    return df

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
    filename = f"Replacement_Parts_Order_Prompt{'_TEST ' if test else ''}_{timestamp}.xlsx"
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
def main(test, output_flag, notify):
    warnings.simplefilter('ignore')
    host_read = connections.host_read
    host_dev = connections.host_dev
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    user = connections.username
    password = connections.password

    print('Get data and merge together')
    if test:
        conn = connect(host_dev, database_hq, user, password)
    else:
        conn = connect(host_read, database_hq, user, password)
    df = get_data(conn)

    print('Fill nulls')
    clean_data(df)

    print('Check for missing reorder points')
    df = missing_reorder_points(df, notify)

    print('Determine if order is needed')
    df = order_prompt(df)

    print('Output Data')
    if output_flag:
        order_steps_export(df, test)

    print('Done')
# ===============================================================================
if __name__ == '__main__':
    test = False
    output_flag = True
    main(test, output_flag, notify=False)
