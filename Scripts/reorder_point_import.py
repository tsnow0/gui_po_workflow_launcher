import pymysql
import pandas as pd
from pathlib import Path
import sys
import warnings

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
def upload_data(df, conn_write):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    root = base if hasattr(sys, "_MEIPASS") else base.parent
    folder = root / "Queries" / "Replacement Part Order Prompt"
    upload_list = df.to_dict('records')
    with open(folder / 'upload_reorder_points.sql', 'r') as query:
        cursor = conn_write.cursor()
        cursor.executemany(query.read(), upload_list)
        conn_write.commit()
        cursor.close()

# ===============================================================================
def main(test, filename):
    warnings.simplefilter('ignore')
    host_write = connections.host_write
    host_dev = connections.host_dev
    database_hq = connections.database_hq
    # cred = kr.get_credential('hq_db', None)
    # user = cred.username
    # password = cred.password
    user = connections.username
    password = connections.password

    # read file
    df = pd.read_csv(filename)

    # upload data
    if test:
        conn_write = connect(host_dev, database_hq, user, password)
    else:
        conn_write = connect(host_write, database_hq, user, password)
    upload_data(df, conn_write)
    print('done')
# ===============================================================================
if __name__ == '__main__':
    test = False
    filename = r"C:\Users\tori.snow\Downloads\update one reorder point.csv"
    main(test, filename)
