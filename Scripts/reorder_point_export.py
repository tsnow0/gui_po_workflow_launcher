import pymysql
import pandas as pd
from datetime import datetime
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
def get_data(conn_read):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Replacement Part Order Prompt"

    print('Getting reorder products Data')
    reorder_point_df = load_query_df(folder / "reorder_products.sql", conn_read)

    return reorder_point_df

# ===============================================================================
def order_steps_export(df):
    print("Exporting Data to File")
    downloads_path = Path.home() / "Downloads"
    filename = f"rp_reorder_points_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    df.to_csv(downloads_path / filename, index=False)

# ===============================================================================
def main():
    warnings.simplefilter('ignore')
    host_read = connections.host_read
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    user = connections.username
    password = connections.password

    print('Get data and merge together')
    conn_read = connect(host_read, database_hq, user, password)
    df = get_data(conn_read)

    print('Output Data')
    order_steps_export(df)

    print('Done')
# ===============================================================================
if __name__ == '__main__':
    main()
