#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
import traceback
import socket
from datetime import datetime, timedelta, date
import pymysql
import pandas as pd
import numpy as np
import requests
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
# Connects To The Read DB
# ===============================================================================
def connect_read():
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    user = connections.username
    password = connections.password

    conn = pymysql.connect(host=connections.host_read,
                           database=connections.database_hq,
                           user=user,
                           password=password,
                           ssl=False # PyMySQL uses ssl= instead of ssl_disabled
                            )
    return conn

# ===============================================================================
def send_teams_failure(job_name: str, error_message: str):
    TEAMS_WEBHOOK_URL = ("https://malouf.webhook.office.com/webhookb2/20cb1a2b-"
                        "aa21-4e94-be6f-dbd45eaf4c95@26054319-130d-46cb-99e1-"
                        "c398868999c5/IncomingWebhook/"
                        "9f199010c28440a0b2f10a1f51a5bdbc/85876613-b3de-40b8-"
                        "a035-a0aa5622a313/V2-LWB0XubTZ8v6Ht7fP6Vxh6djUyv5VFcsLRy6RJpUa81")
    """Send a failure notification to Teams via webhook."""
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": f"{job_name} Failed",
        "themeColor": "FF0000",  # Red for failure
        "sections": [{
            "activityTitle": f"❌ Job Failed: {job_name}",
            "facts": [
                {"name": "Server", "value": socket.gethostname()},
                {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            ],
            "text": error_message
        }]
    }
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Teams alert: {e}")

# ===============================================================================
# Connects To The Write DB
# ===============================================================================
def connect_write():
    conn = pymysql.connect(
        host=connections.host_write,
        database=connections.database_analytics,
        user=connections.username,
        password=connections.password,
        ssl=False  # PyMySQL uses ssl= instead of ssl_disabled
    )

    return conn

# ==============================================================================
# Gets data from the data_query and creates the data_list
# ==============================================================================
def get_data(conn_read):
    warnings.filterwarnings('ignore')
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "ETA_Update"
    file = folder / "data_query.sql"
    with open(file, 'r') as query:
        data_df = pd.read_sql_query(query.read(), conn_read)
    # with open(folder + '/wayfair_data_query.sql', 'r') as query:
    #     wayfair_data_df = pd.read_sql_query(query.read(), conn_read)

    return data_df #, wayfair_data_df

# ===============================================================================
# Executes di_query & Stores Data Into Dataframe
# ===============================================================================
def get_amz_containers(conn_read):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    file = root / "Queries" / "ETA_Update" / "amz_query.sql"
    with open(file, 'r') as query:
        amz_df = pd.read_sql_query(query.read(), conn_read)

    return amz_df

# ===============================================================================
# Combines di and data containers
# ===============================================================================
def concat_data(amz_df, data_df): #, wayfair_data_df):
    data_df = pd.concat([amz_df, data_df], ignore_index=True, sort=False)
    data_df = data_df.replace({np.nan: None})
    data_df.drop_duplicates(inplace=True, keep=False)

    return data_df

# ===============================================================================
# Creating the upload list
# ===============================================================================
def calculate_new_eta(data_df):
    today = date.today()
    for index, row in data_df.iterrows():
        production_days = row['production_days']
        dwell = min(row['dwell'], 25)
        if row['transit_time'] is None and row['domestic_flag'] == 1:
            transit = 7
        else:
            transit = row['transit_time']
        if row['cargo_ready'] is None:
            if row['requested_ship'] is None:
                interval = production_days + dwell + transit
                new_eta = today + timedelta(days=interval)
            elif (row['requested_ship'] < today) or (row['requested_ship'] >= today):
                interval = production_days + dwell + transit
                requested_ship_interval = dwell + transit
                new_eta = max(row['requested_ship'] + timedelta(days=requested_ship_interval), today + timedelta(days=interval))
        elif row['cargo_ready'] < today:
            interval = dwell + transit + 7  # adding 7 days as a buffer
            new_eta = today + timedelta(days=interval)
        elif row['cargo_ready'] >= today:
            interval = dwell + transit
            new_eta = row['cargo_ready'] + timedelta(days=interval)
        data_df.at[index, 'new_eta'] = new_eta

    return data_df

# ===============================================================================
def data_export(data_df):
    print('Exporting Data to File')

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    output_dir = base / '../../../../../../Project Files/EverRest_US/Database/ETA_Update/Data/Output'
    output_file = output_dir / 'ETA_Update.xlsx'

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        data_df.to_excel(excel_writer=writer, sheet_name='Data', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Data']
        for col_num, col_name in enumerate(data_df.columns):
            column_len = len(col_name) + 10
            worksheet.set_column(col_num, col_num, column_len)
        (max_row, max_col) = data_df.shape
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        worksheet.freeze_panes(1, 0)
        workbook.set_properties({'author': 'Analytics'})
        workbook.read_only_recommended()
    writer.close()

# ===============================================================================
# Outputs the information from the data_list to the database
# ===============================================================================
def output(conn_write, data_df):
    cursor = conn_write.cursor()
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / 'Queries' / 'ETA_Update'
    file = folder / 'upload_query.sql'
    upload_list = data_df.to_dict('records')
    with open(file, 'r') as query:
        cursor.executemany(query.read(), upload_list)
        conn_write.commit()
    cursor.close()

# ===============================================================================
def main():
    try:
        print('Getting Data From Database...')
        conn_read = connect_read()
        data_df = get_data(conn_read)
        amz_df = get_amz_containers(conn_read)
        conn_read.close()
        data_df = concat_data(amz_df, data_df)
        data_df = calculate_new_eta(data_df)
        # print('Exporting POs to CSV File That Do Not Have A Transit Time')
        # data_export(data_df, og_path)
        print('Uploading Data')
        if not data_df.empty:
            conn_write = connect_write()
            output(conn_write, data_df)
            conn_write.close()
        print('Done')
    except Exception:
        error_details = traceback.format_exc()
        send_teams_failure("analytics_eta_update/ETA Update", error_details)
        raise  # re-raise so Task Scheduler logs the failure too

# ===============================================================================
if __name__ == '__main__':
    main()
