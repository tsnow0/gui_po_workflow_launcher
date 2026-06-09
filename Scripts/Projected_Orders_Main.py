#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
import traceback
import socket
import pymysql
import pandas as pd
import math
import warnings
import requests
from datetime import datetime, date
from pathlib import Path
import sys
import Projected_Orders
import ETA_Update

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
def load_query_df(filename, conn, parse_month=False):
    with open(filename, "r") as f:
        df = pd.read_sql(f.read(), conn)
    if parse_month and "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"])
    return df

# ===============================================================================
def filter_and_rename(df, filter_col, filter_val, rename_map, drop=True):
    sub = df[df[filter_col] == filter_val].copy()
    sub.rename(columns=rename_map, inplace=True)
    if drop:
        sub.drop(columns=[filter_col], inplace=True)
    return sub

# ===============================================================================
# def get_safety_stock_data(conn_read):
#     print('Getting Safety Stock Data')
#
#     base_dir = Path(__file__).resolve().parent
#     folder = base_dir.parent / "Queries" / "Safety_Stock"
#
#     sales_df = load_query_df(folder / "sales_query.sql", conn_read)
#     demand_df = load_query_df(folder / "demand_query.sql", conn_read)
#     product_vendor_df = load_query_df(folder / "product_vendor_query.sql", conn_read)
#
#     # load excel files
#     base_dir = Path("../../../../../../Project Files/Analysis_Projects/Safety_Stock/Input").resolve()
#     service_rate_df = pd.read_excel(base_dir / "Service_Rate.xlsx")
#     lead_time_df = pd.read_excel(base_dir / "Lead_Days.xlsx")
#
#     return sales_df, lead_time_df, demand_df, product_vendor_df, service_rate_df

# ===============================================================================
def get_projected_orders_data(conn):
    print('Getting Projected Orders Data')

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Projected_Orders"

    # load queries
    product_df = load_query_df(folder / "product_query.sql", conn, parse_month=True)
    evr_inventory_df = load_query_df(folder / "inventory_query.sql", conn, parse_month=True)
    di_inventory_df = load_query_df(folder / "amazon_inventory_query.sql", conn, parse_month=True)
    cg_inventory_df = load_query_df(folder / "castlegate_inventory_query.sql", conn, parse_month=True)
    way_demand_split_df = load_query_df(folder / "way_demand_split_query.sql", conn)
    forecast_df = load_query_df(folder / "forecast_query.sql", conn, parse_month=True)
    di_forecast_df = load_query_df(folder / "amazon_di_forecast_query.sql", conn, parse_month=True)
    safety_stock_df = load_query_df(folder / "safety_stock_query.sql", conn)
    evr_po_df = load_query_df(folder / "po_query.sql", conn, parse_month=True)
    di_po_df = load_query_df(folder / "di_po_query.sql", conn, parse_month=True)
    lead_time_df = load_query_df(folder / "lead_time_query.sql", conn)
    backorder_df = load_query_df(folder / "backorder_query.sql", conn)
    total_amazon_po_df = load_query_df(folder / "amazon_di_po_query.sql", conn, parse_month=True)

    # split dfs - filter and rename function
    us_di_inventory_df = filter_and_rename(di_inventory_df, "ochannel_id", 27, {"di_inventory_quantity": "us_di_inventory_quantity"})
    ca_di_inventory_df = filter_and_rename(di_inventory_df, "ochannel_id", 31, {"di_inventory_quantity": "ca_di_inventory_quantity"})

    amazon_ds_forecast_df = filter_and_rename(forecast_df, "channel", "amazon", {"demand_quantity": "amazon_ds_demand_quantity"})
    way_forecast_df = filter_and_rename(forecast_df, "channel", "wayfair", {})

    # evr forecast is everything except amazon and wayfair
    evr_forecast_df = forecast_df[~forecast_df["channel"].isin(["amazon", "wayfair"])].drop(columns=["channel"]).rename(columns={"demand_quantity": "evr_demand_quantity"})

    us_di_forecast_df = filter_and_rename(di_forecast_df, "country", "US", {"di_demand_quantity": "us_di_demand_quantity"})
    ca_di_forecast_df = filter_and_rename(di_forecast_df, "country", "CA", {"di_demand_quantity": "ca_di_demand_quantity"})

    us_di_po_df = filter_and_rename(di_po_df, "opo_prefix", "AMZ", {"di_po_quantity": "us_di_po_quantity"})
    ca_di_po_df = filter_and_rename(di_po_df, "opo_prefix", "AMC", {"di_po_quantity": "ca_di_po_quantity"})
    cg_po_df = filter_and_rename(di_po_df, "opo_prefix", "WAY", {"di_po_quantity": "cg_po_quantity"})

    # extra column for lead time
    lead_time_df['avg_lead_months'] = lead_time_df['avg_lead_days'].apply(lambda x: math.ceil(x / 30.44) if pd.notna(x) else None)

    return product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df, lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df, us_di_forecast_df, ca_di_forecast_df, backorder_df, cg_inventory_df, cg_po_df, way_demand_split_df, way_forecast_df, total_amazon_po_df

# ===============================================================================
def select_test():
    # Available options ['safety_stock', 'lead_time']
    test = ['safety_stock']

    return test

# ===============================================================================
def safety_stock_parameters(test):
    # 1 = Uncertainty in demand, 2 = Uncertainty in Lead Time, 3 = Uncertainty in Lead Time & Demand (Independent), 4 = Uncertainty in Lead Time & Demand (Dependent)
    return [1, 2, 3] if test else 3

# ===============================================================================
def main(test, output_flag):

    warnings.simplefilter('ignore')
    host_read = connections.host_read
    host_dev = connections.host_dev
    host_write = connections.host_write
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    user = connections.username
    password = connections.password

    try:
        print('=' * 50)
        print('Running ETA Script')
        ETA_Update.main()
    except Exception:
        error_details = traceback.format_exc()
        send_teams_failure("analytics_projected_orders/ETA", error_details)
        # raise  # re-raise so Task Scheduler logs the failure too

    # try:
    #     print('=' * 50)
    #     print('Running Safety Stock Script')
    #     ss_method = safety_stock_parameters(test)
    #     conn_read = connect(host_read, database_hq, user, password)
    #     sales_df, lead_time_df, demand_df, product_vendor_df, service_rate_df = get_safety_stock_data(conn_read)
    #     conn_read.close()
    #     Safety_Stock.main(sales_df, lead_time_df, demand_df, product_vendor_df, service_rate_df, ss_method, test)
    # except Exception:
    #     error_details = traceback.format_exc()
    #     send_teams_failure("analytics_projected_orders/Safety_Stock", error_details)
    #     raise  # re-raise so Task Scheduler logs the failure too

    try:
        print('=' * 50)
        print('Running Projected Orders Script')
        if test:
            conn = connect(host_dev, database_hq, user, password)
        else:
            conn = connect(host_read, database_hq, user, password)
        product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df, lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df, us_di_forecasts_df, ca_di_forecasts_df, backorder_df, cg_inventory_df, cg_po_df, way_demand_split_df, way_forecast_df, total_amazon_po_df = get_projected_orders_data(conn)
        conn.close()
        Projected_Orders.main(host_read, host_dev, host_write, database_hq, user, password, product_df, evr_inventory_df, amazon_ds_forecast_df, evr_forecast_df, safety_stock_df, lead_time_df, evr_po_df, us_di_po_df, ca_di_po_df, us_di_inventory_df, ca_di_inventory_df, us_di_forecasts_df, ca_di_forecasts_df, backorder_df, cg_inventory_df, cg_po_df, way_demand_split_df, way_forecast_df, total_amazon_po_df, test, output_flag)
        print('Done')
        print('=' * 50)
    except Exception:
        error_details = traceback.format_exc()
        send_teams_failure("analytics_projected_orders/Projected_Orders", error_details)
        # raise  # re-raise so Task Scheduler logs the failure too


# ===============================================================================
if __name__ == '__main__':
    test = False
    output_flag = True if (date.today()).weekday() == 0 else False # if monday, output file, else don't

    main(test, output_flag)
