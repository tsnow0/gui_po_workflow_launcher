# --- NOTES ---
# save GUI in the following filepath: \\fileserver\public\Analytics\Python GUI Applications\Order Prompt and Containerization

from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import sys
from datetime import datetime, date
from pathlib import Path
import Projected_Orders_Main
import replacement_parts_order_prompts
import reorder_point_export
import reorder_point_import
import Order_Tool_wCG
import Containerization


# ----------------------------------------------------------------------------------------------------------------------
def show_info_msg(msg):
    Messagebox.show_info(msg, 'Info')

# ----------------------------------------------------------------------------------------------------------------------
def show_error_msg(msg):
    Messagebox.show_error(msg, 'Error')

# Projected Order Prompt -----------------------------------------------------------------------------------------------
def run_order_prompt():
    try:
        test = True if test_var.get() else False
        output_flag = True if output_var.get() else False

        # run script
        Projected_Orders_Main.main(test, output_flag)

        # output directory
        base_dir = Path(r"\\fileserver\public\Reports\Purchasing\Projected_Orders")
        today = date.today()
        subfolder = base_dir / str(today.year) / str(today.month)

        # show completion message
        if output_flag:
            if test:
                show_info_msg(f'Test Order Prompt Completed.\nFile is available here: {subfolder}')
            else:
                show_info_msg(f'Order Prompt Completed.\nFile is available here: {subfolder}')
        else:
            if test:
                show_info_msg('Test Order Prompt Completed. No output file was generated based on the selected parameters.')
            else:
                show_info_msg('Order Prompt Completed. No output file was generated based on the selected parameters.')

    except Exception as e:
        show_error_msg(f'An error occurred while running the order prompt.\nPlease contact Analytics with this error: {e}')

# PO Order Tool---------------------------------------------------------------------------------------------------------
def run_po_tool():
    try:
        test = True if test_var.get() else False

        # run script
        Order_Tool_wCG.main(test)

        # show completion message
        curyear = datetime.now().strftime("%Y")
        folder_path = f"//fileserver/public/Purchasing/EVEREST PO/{curyear}/Purchase Order Tool"
        if test:
            show_info_msg(f'Test PO Tool Process Completed.\nFile is available here: {folder_path}')
        else:
            show_info_msg(f'PO Tool Process Completed.\nFile is available here: {folder_path}')

    except Exception as e:
        show_error_msg(f'An error occurred while running the PO Order Tool.\nPlease contact Analytics with this error: {e}')

# Containerization------------------------------------------------------------------------------------------------------
def run_containerization():
    try:
        # Get File
        filename = filedialog.askopenfilename(
            initialdir="C:/Downloads",
            title="Open a file",
            filetype=(("excel files", "*.xlsx"), ("All Files", ""))
        )
        if not filename:
            return
        filename = r"{}".format(filename)
        # print(filename)

        # run script
        Containerization.main(filename)

        # show completion message
        curyear = datetime.now().strftime("%Y")
        curdate = datetime.now().strftime("%Y.%m.%d")
        folder = f"//fileserver/public/Purchasing/EVEREST PO/{curyear}"
        subfolder = f"{folder}/{curdate}"
        show_info_msg(f'Containerization on imported file completed. \nFile is available here: {subfolder}')

    except Exception as e:
        show_error_msg(f'An error occurred while containerizing the file.\nPlease contact Analytics with this error: {e}')

# RP Order Prompt-----------------------------------------------------------------------------------------
def run_rp_order_prompt():
    try:
        test = True if test_var.get() else False

        # run script
        replacement_parts_order_prompts.main(test, show_info_msg)

        # show completion message
        base_dir = Path(r"\\fileserver\public\Reports\Purchasing\Projected_Orders")
        today = date.today()
        subfolder = base_dir / str(today.year) / str(today.month)
        if test:
            show_info_msg(f'Test Replacement Part Order Prompt Completed.\nFile is available here: {subfolder}')
        else:
            show_info_msg(f'Replacement Part Order Prompt Completed.\nFile is available here: {subfolder}')

    except Exception as e:
        show_error_msg(f'An error occurred while running the replacement part order prompt.\nPlease contact Analytics with this error: {e}')

# Export Reorder Point CSV----------------------------------------------------------------------------------------------
def run_reorder_point_export():
    try:
        reorder_point_export.main()
        show_info_msg('The reorder point csv file is in your Downloads folder.'
                      '\nUse the Import Reorder Points button to update reorder points for the next replacement part order prompt')

    except Exception as e:
        show_error_msg(f'An error occurred while downloading the reorder point file.\nPlease contact Analytics with this error: {e}')

# Import Reorder Point CSV ---------------------------------------------------------------------------------------------
def run_reorder_point_import():
    try:
        test = True if test_var.get() else False

        # Get File
        filename = filedialog.askopenfilename(
            initialdir="C:/Downloads",
            title="Open a file",
            filetype=(("csv files", "*.csv"), ("All Files", ""))
        )
        if not filename:
            return

        # get filename
        filename = r"{}".format(filename)
        print(filename)

        # run script
        reorder_point_import.main(test, filename)

        # show completion message
        if test:
            show_info_msg(f'Test Reorder Point file has been successfully uploaded to the database.'
                          f'\n Re-run the Replacement Part Order Prompt with Test selected to use this updated data if needed.')
        else:
            show_info_msg(f'Reorder Point file has been successfully uploaded to the database.'
                          f'\n Re-run the Replacement Part Order Prompt if needed.')

    except Exception as e:
        show_error_msg(f'An error occurred while importing the reorder point file. \nPlease contact Analytics with this error: {e}')

# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    print(sys.executable)

    # Create main Window
    root = ttk.Window(themename='solar')
    root.title('Order Prompt and Containerization GUI')
    root.iconbitmap(r'\\fileserver\public\Analytics\Icons and Logos\e icon 2.ico')
    root.iconbitmap(default=r'\\fileserver\public\Analytics\Icons and Logos\e icon 2.ico')

    # Parameters label
    param_lbl = ttk.Label(root, text='Parameters', font=('Arial', 15))
    param_lbl.pack(pady=10)

    # top row frame (holds test and output parameters)
    top_row = ttk.Frame(root)
    top_row.pack(pady=5)

    # row 1 - column 1 - output file
    output_var = ttk.BooleanVar(value=True)
    output_cb = ttk.Checkbutton(top_row, text='Output Order Prompt Files', bootstyle='primary.Roundtoggle.Toolbutton', variable=output_var)
    output_cb.pack(side="left", pady=10)


    # row 1 - column 2 - test
    test_var = ttk.BooleanVar()
    test_cb = ttk.Checkbutton(top_row, text='Test', bootstyle='primary.Roundtoggle.Toolbutton', variable=test_var)
    test_cb.pack(side="left", padx=20, pady=10)

    # General label
    general_lbl = ttk.Label(root, text='General', font=('Arial', 15))
    general_lbl.pack(pady=10)

    # middle row frame (holds order prompt, po order tool, and containerization)
    mid_row = ttk.Frame(root)
    mid_row.pack(pady=5)

    # row 2 - column 1 - order prompt
    col1 = ttk.Frame(mid_row)
    col1.pack(side="left", padx=15)
    order_prompt_btn = ttk.Button(col1, text='Run Order Prompt (about 10 min)', bootstyle='warning', width=30, command=run_order_prompt)
    order_prompt_btn.pack(pady=10, ipady=5)

    # row 2 - column 2 - po order tool
    col2 = ttk.Frame(mid_row)
    col2.pack(side="left", padx=15)
    po_order_tool_btn = ttk.Button(col2, text='Run PO Order Tool', bootstyle='success', width=30, command=run_po_tool)
    po_order_tool_btn.pack(pady=10, ipady=5)

    # row 2 - column 3 - containerization
    col3 = ttk.Frame(mid_row)
    col3.pack(side="left", padx=15)
    containerization_btn = ttk.Button(col3, text='Import File for Containerization', bootstyle='danger', width=30, command=run_containerization)
    containerization_btn.pack(pady=10, ipady=5)

    # Replacement Parts label
    rp_order_lbl = ttk.Label(root, text='Replacement Parts', font=('Arial', 15))
    rp_order_lbl.pack(pady=10)

    # Bottom Frame (holds replacement part functions)
    rp_buttons_frame = ttk.Frame(root)
    rp_buttons_frame.pack(pady=15)

    # row 3 - column 1 - replacement part order prompt
    rp_order_btn = ttk.Button(rp_buttons_frame, text='Run RP Order Prompt', bootstyle="info", width=25, command=run_rp_order_prompt)
    rp_order_btn.pack(side="left", padx=15, pady=10, ipady=5)

    # row 2 - column 2 - export reorder points
    reorder_point_export_btn = ttk.Button(rp_buttons_frame, text='Export Reorder Points', bootstyle="secondary", width=25, command=run_reorder_point_export)
    reorder_point_export_btn.pack(side="left", padx=15, pady=10, ipady=5)

    # row 3 - column 3 - import reorder points
    reorder_point_import_btn = ttk.Button(rp_buttons_frame, text='Import Reorder Points', bootstyle="secondary", width=25, command=run_reorder_point_import)
    reorder_point_import_btn.pack(side="left", padx=15, pady=10, ipady=5)

    root.mainloop()
