#
#NOTE: IF ANY CHANGES ARE MADE TO THIS SCRIPT, COPY THE NEW VERSION TO THE analytics_order_prompt_containerization_gui REPO
#
from datetime import date
def main(df, index, row, evr_beginning_inventory, us_di_beginning_inventory,
         ca_di_beginning_inventory, cg_beginning_inventory,
         version):

    vendor = row['vendor_number']
    category = row['category']
    order_month = row['order_date']
    first_of_month = (date.today()).replace(day=1)

    # add new beg inventory to dataframe
    df.loc[index, 'beg_evr_inventory_quantity'] = evr_beginning_inventory
    df.loc[index, 'beg_us_di_inventory_quantity'] = us_di_beginning_inventory
    df.loc[index, 'beg_ca_di_inventory_quantity'] = ca_di_beginning_inventory
    df.loc[index, 'beg_cg_inventory_quantity'] = cg_beginning_inventory

    # total evr demand = amazon_ds_demand_quantity_adj + way_ds_demand_quantity_adj + evr_demand_quantity_adj
    total_evr_demand = row['amazon_ds_demand_quantity_adj'] + row['way_ds_demand_quantity_adj'] + row['evr_demand_quantity_adj']
    amazon_ds_pct = row['amazon_ds_demand_quantity_adj'] / total_evr_demand if total_evr_demand > 0 else 0
    way_ds_pct = row['way_ds_demand_quantity_adj'] / total_evr_demand if total_evr_demand > 0 else 0
    evr_pct = row['evr_demand_quantity_adj'] / total_evr_demand if total_evr_demand > 0 else 0

    # calculate ending inventory levels
    evr_end_inventory = evr_beginning_inventory + row['evr_po_quantity'] - total_evr_demand
    us_di_end_inventory = us_di_beginning_inventory + row['us_di_po_quantity'] - row['us_di_demand_quantity_adj']
    ca_di_end_inventory = ca_di_beginning_inventory + row['ca_di_po_quantity'] - row['ca_di_demand_quantity_adj']
    cg_end_inventory = cg_beginning_inventory + row['cg_po_quantity'] - row['way_di_demand_quantity_adj']

    usxtsx_mattress_flag = True if vendor == 'USXTSX' and category == 'Mattress' else False

    # using 'and' instead of '&' in my if statements because 'and' will stop evaluating as soon as it finds a false value (short circuit) while '&' will evaluate all conditions regardless of their truth value. This will make the process more efficient
    # ------------------------------------------- IF 0 OF 4 ARE NEGATIVE -------------------------------------------
    if (evr_end_inventory > 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory > 0) and (cg_end_inventory > 0):
        evr_demand = total_evr_demand
        us_di_demand = row['us_di_demand_quantity_adj']
        ca_di_demand = row['ca_di_demand_quantity_adj']
        way_di_demand = row['way_di_demand_quantity_adj']

        # projected order quantity
        row['evr_order_quantity'] = 0
        row['cg_order_quantity'] = 0

    # ------------------------------------------- IF 1 OF 4 ARE NEGATIVE -------------------------------------------
    # EVR, US, CA, CG

    # if only EVR is negative - shift EVR dropship demand to us di and wayfair if eligible
    elif (evr_end_inventory <= 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory > 0) and (cg_end_inventory > 0):
        # ca di stays same
        ca_di_demand = row['ca_di_demand_quantity_adj']

        # shift evr to us di
        # and update us di end inventory
        evr_demand = round(total_evr_demand + (evr_end_inventory * amazon_ds_pct), 0)
        us_di_demand = round(row['us_di_demand_quantity_adj'] + abs(evr_end_inventory * amazon_ds_pct), 0)
        us_di_end_inventory += min(0, round(evr_end_inventory * amazon_ds_pct, 0))

        # if flag is true, shift wayfair ds demand to wayfair
        if usxtsx_mattress_flag is True:
            evr_demand += round(total_evr_demand + (evr_end_inventory * way_ds_pct), 0)
            way_di_demand = round(row['way_di_demand_quantity_adj'] + abs(evr_end_inventory * way_ds_pct), 0)

            # update cg and evr end inventory
            cg_end_inventory += min(0, round(evr_end_inventory * way_ds_pct, 0))
            evr_end_inventory = round(evr_end_inventory * evr_pct, 0)
        else:
            # wayfair ds demand doesn't shift to wayfair
            way_di_demand = row['way_di_demand_quantity_adj']

            # update evr end inventory since we shifted us di earlier
            evr_end_inventory = round(evr_end_inventory * (evr_pct + way_ds_pct), 0)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = abs(cg_end_inventory) if usxtsx_mattress_flag is True and cg_end_inventory < 0 else 0

    # if only us di is negative - shift us di demand to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory > 0) and (cg_end_inventory > 0):
        # ca di and way di stay the same
        ca_di_demand = row['ca_di_demand_quantity_adj']
        way_di_demand = row['way_di_demand_quantity_adj']

        # shift us di to evr
        evr_demand = total_evr_demand + abs(us_di_end_inventory)
        us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory

        # update evr end inventory
        evr_end_inventory += min(0, us_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = 0

    # if only ca di is negative - shift ca di demand to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory > 0):
        # us di and way di stay same
        us_di_demand = row['us_di_demand_quantity_adj']
        way_di_demand = row['way_di_demand_quantity_adj']

        # shift ca di to evr
        evr_demand = total_evr_demand + abs(ca_di_end_inventory)
        ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory

        # update evr end inventory
        evr_end_inventory += min(0, ca_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = 0

    # if only cg is negative - shift wayfair di demand to EVR if not eligible for cg order
    elif (evr_end_inventory > 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory > 0) and (cg_end_inventory <= 0):
        # us di and ca di stay same
        us_di_demand = row['us_di_demand_quantity_adj']
        ca_di_demand = row['ca_di_demand_quantity_adj']

        # if product is usxtsx mattress and is a future order month, don't shift and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand
            way_di_demand = row['way_di_demand_quantity_adj']

            # projected order quantity
            row['evr_order_quantity'] = 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0

        else:
            # else, shift wayfair di demand to evr and don't prompt cg order
            evr_demand = total_evr_demand + abs(cg_end_inventory)
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            # update evr end inventory
            evr_end_inventory += min(0, cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # ------------------------------------------- IF 2 OF 4 ARE NEGATIVE -------------------------------------------
    # EVR + US, EVR + CA, EVR + CG, US + CA, US + CG, CA + CG

    # if only EVR and US DI are negative - shift wayfair dropship demand to wayfair di, then shift US DI to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory > 0) and (cg_end_inventory > 0):
        # ca di demand stays same
        ca_di_demand = row['ca_di_demand_quantity_adj']

        # first shift way dropship demand to wayfair if eligible
        # and update cg end inventory
        if usxtsx_mattress_flag is True:
            evr_demand = round(total_evr_demand + (evr_end_inventory * way_ds_pct), 0)
            way_di_demand = round(row['way_di_demand_quantity_adj'] + abs(evr_end_inventory * way_ds_pct), 0)
            cg_end_inventory += min(0, round(evr_end_inventory * way_ds_pct, 0))
        else:
            evr_demand = total_evr_demand
            way_di_demand = row['way_di_demand_quantity_adj']

        # then shift US di demand to EVR
        evr_demand += abs(us_di_end_inventory)
        us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory

        # recalculate end inventory
        # keep amazon ds on evr side and add us di inventory to evr
        evr_end_inventory = round(evr_end_inventory * (evr_pct + amazon_ds_pct), 0) + min(0, us_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = abs(cg_end_inventory) if usxtsx_mattress_flag is True and cg_end_inventory < 0 else 0

    # if only EVR and CA DI are negative - shift evr dropship demand to us di and way di, then shift ca di demand to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory > 0):
        # first shift amazon dropship demand to us di
        evr_demand = round(total_evr_demand + (evr_end_inventory * amazon_ds_pct), 0)
        us_di_demand = round(row['us_di_demand_quantity_adj'] + abs(evr_end_inventory * amazon_ds_pct), 0)
        us_di_end_inventory += min(0, round(evr_end_inventory * amazon_ds_pct, 0))

        # if flag is true, shift way dropship demand to wayfair di
        if usxtsx_mattress_flag is True:
            evr_demand += round(total_evr_demand + (evr_end_inventory * way_ds_pct), 0)
            way_di_demand = round(row['way_di_demand_quantity_adj'] + abs(evr_end_inventory * way_ds_pct), 0)
            cg_end_inventory += min(0, round(evr_end_inventory * way_ds_pct, 0))
            evr_end_inventory = round(evr_end_inventory * evr_pct, 0)  # just evr demand
        else:
            # don't shift wayfair ds demand and keep in evr end inventory
            way_di_demand = row['way_di_demand_quantity_adj']
            evr_end_inventory = round(evr_end_inventory * (evr_pct + way_ds_pct), 0)  # evr demand + wayfair ds demand

        # then shift ca di demand to EVR
        evr_demand = evr_demand + abs(ca_di_end_inventory)
        ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
        evr_end_inventory += min(0, ca_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = abs(cg_end_inventory) if usxtsx_mattress_flag is True and cg_end_inventory < 0 else 0

    # if only EVR and CG are negative - shift amazon dropship demand to us di, then shift wayfair di demand to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory > 0) and (cg_end_inventory <= 0):
        # first shift amazon dropship demand to us di
        evr_demand = round(total_evr_demand + (evr_end_inventory * amazon_ds_pct), 0)
        us_di_demand = round(row['us_di_demand_quantity_adj'] + abs(evr_end_inventory * amazon_ds_pct), 0)
        ca_di_demand = row['ca_di_demand_quantity_adj']

        # recalculate end inventory
        us_di_end_inventory += min(0, round(evr_end_inventory * amazon_ds_pct, 0))
        evr_end_inventory = round(evr_end_inventory * evr_pct, 0)  # keep way ds in evr

        # then shift wayfair di demand to EVR if not eligible for cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            # don't shift and prompt cg order
            way_di_demand = row['way_di_demand_quantity_adj']

            # projected order quantity
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        else:
            # else, shift wayfair di demand to evr
            # recalculate end inventory
            evr_demand = evr_demand + abs(cg_end_inventory)
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory
            evr_end_inventory += min(0, cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # if only US and CA DI are negative - shift us di and ca di demand to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory > 0):
        evr_demand = total_evr_demand + (abs(us_di_end_inventory) + abs(ca_di_end_inventory))
        us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
        ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
        way_di_demand = row['way_di_demand_quantity_adj']

        # recalculate end inventory
        evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = 0

    # if only US DI and CG are negative - shift us di and wayfair di demand to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory > 0) and (cg_end_inventory <= 0):
        # if product is usxtsx mattress and is a future order month, only shift us di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(us_di_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj']
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, us_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
        else:
            # else, shift us di and wayfair di demand to EVR and don't prompt cg order
            evr_demand = total_evr_demand + (abs(us_di_end_inventory) + abs(cg_end_inventory))
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj']
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, us_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # if only CA DI and CG are negative - shift ca di and wayfair di demand to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory <= 0):
        # if product is usxtsx mattress and is a future order month, only shift ca di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(ca_di_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj']
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, ca_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
        else:
            # else, shift ca di and wayfair di demand to EVR and don't prompt cg order
            evr_demand = total_evr_demand + (abs(ca_di_end_inventory) + abs(cg_end_inventory))
            us_di_demand = row['us_di_demand_quantity_adj']
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, ca_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # ------------------------------------------- IF 3 OF 4 ARE NEGATIVE -------------------------------------------
    # EVR + US + CA, EVR + US + CG, EVR + CA + CG, US + CA + CG

    # if only EVR, US DI, and CA DI are negative - shift wayfair dropship to wayfair di, then shift us di and ca di demand to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory > 0):
        # shift wayfair dropship demand to wayfair di if eligible
        if usxtsx_mattress_flag is True:
            evr_demand = round(total_evr_demand + (evr_end_inventory * way_ds_pct), 0)
            way_di_demand = round(row['way_di_demand_quantity_adj'] + abs(evr_end_inventory * way_ds_pct), 0)
            cg_end_inventory += min(0, round(evr_end_inventory * way_ds_pct, 0))
            evr_end_inventory = round(evr_end_inventory * (evr_pct + amazon_ds_pct), 0)  # need to keep amazon ds on evr side
        else:
            evr_demand = total_evr_demand
            way_di_demand = row['way_di_demand_quantity_adj']
            # evr end inventory stays same since amazon ds and way ds isn't shifting

        # then shift us di and ca di to EVR
        evr_demand += abs(us_di_end_inventory + ca_di_end_inventory)
        us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
        ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory

        # recalculate end inventory
        evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory)

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = abs(cg_end_inventory) if usxtsx_mattress_flag is True and cg_end_inventory < 0 else 0

    # if only EVR, US DI, and CG are negative - shift us di and wayfair di demand to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory > 0) and (cg_end_inventory <= 0):
        # if product is usxtsx mattress and is a future order month, only shift us di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(us_di_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj']
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, us_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
        else:
            # else, shift us di and way di demand to EVR and don't prompt cg order
            evr_demand = total_evr_demand + (abs(us_di_end_inventory) + abs(cg_end_inventory))
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj']
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, us_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # if only EVR, CA DI, and CG are negative - shift amazon ds demand to US di then shift ca di and wayfair di to EVR
    elif (evr_end_inventory <= 0) and (us_di_end_inventory > 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory <= 0):
        # first shift amazon dropship demand to us di
        evr_demand = round(total_evr_demand + (evr_end_inventory * amazon_ds_pct), 0)
        us_di_demand = round(row['us_di_demand_quantity_adj'] + abs(evr_end_inventory * amazon_ds_pct), 0)

        us_di_end_inventory += min(0, round(evr_end_inventory * amazon_ds_pct, 0))
        evr_end_inventory = round(evr_end_inventory * (evr_pct + way_ds_pct), 0)  # need to keep way ds on evr side

        # then shift ca di and wayfair di to EVR
        # if product is usxtsx mattress and is a future order month, only shift ca di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(ca_di_end_inventory)
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, ca_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
        else:
            # else, shift ca di and wayfair di demand to EVR and don't prompt cg order
            evr_demand = evr_demand + abs(ca_di_end_inventory + cg_end_inventory)
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, ca_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # if only US DI, CA DI, and CG are negative - shift all to EVR
    elif (evr_end_inventory > 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory <= 0):
        # if product is usxtsx mattress and is a future order month, only shift us di and ca di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(us_di_end_inventory) + abs(ca_di_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0

        else:
            # else, shift all to EVR and don't prompt cg order
            evr_demand = total_evr_demand + abs(us_di_end_inventory) + abs(ca_di_end_inventory) + abs(cg_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    # ------------------------------------------- IF 4 OF 4 ARE NEGATIVE -------------------------------------------
    # if all are negative - shift all to EVR
    # same as 'if only US DI, CA DI, and CG are negative' if statement
    elif (evr_end_inventory <= 0) and (us_di_end_inventory <= 0) and (ca_di_end_inventory <= 0) and (cg_end_inventory <= 0):
        # if product is usxtsx mattress and is a future order month, only shift us di and ca di and prompt cg order
        if usxtsx_mattress_flag is True and cg_end_inventory <= 0 and order_month >= first_of_month:
            evr_demand = total_evr_demand + abs(us_di_end_inventory) + abs(ca_di_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj']

            evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = abs(cg_end_inventory) if cg_end_inventory < 0 else 0
        else:
            # else, shift all to EVR
            evr_demand = total_evr_demand + abs(us_di_end_inventory) + abs(ca_di_end_inventory) + abs(cg_end_inventory)
            us_di_demand = row['us_di_demand_quantity_adj'] + us_di_end_inventory
            ca_di_demand = row['ca_di_demand_quantity_adj'] + ca_di_end_inventory
            way_di_demand = row['way_di_demand_quantity_adj'] + cg_end_inventory

            evr_end_inventory += min(0, us_di_end_inventory + ca_di_end_inventory + cg_end_inventory)

            # projected order quantity
            row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
            row['cg_order_quantity'] = 0

    else:  # if all are positive or something other combo not explicit above - no shifting done
        evr_demand = total_evr_demand
        us_di_demand = row['us_di_demand_quantity_adj']
        ca_di_demand = row['ca_di_demand_quantity_adj']
        way_di_demand = row['way_di_demand_quantity_adj']

        # projected order quantity
        row['evr_order_quantity'] = abs(evr_end_inventory) if evr_end_inventory < 0 else 0
        row['cg_order_quantity'] = abs(cg_end_inventory) if usxtsx_mattress_flag is True and cg_end_inventory < 0 else 0

    if version == 'projected orders':
        # If inventory levels are below safety stock order up to safety stock
        if evr_end_inventory < row['safety_stock_quantity']:
            row['evr_order_quantity'] = row['evr_order_quantity'] + (row['safety_stock_quantity'] - max(evr_end_inventory, 0))
            row['safety_stock_evr_order_quantity'] = (row['safety_stock_quantity'] - max(evr_end_inventory, 0))
        else:
            row['safety_stock_evr_order_quantity'] = 0

    # make sure ending inventory levels are not negative
    evr_end_inventory = max(0, evr_end_inventory)
    us_di_end_inventory = max(0, us_di_end_inventory)
    ca_di_end_inventory = max(0, ca_di_end_inventory)
    cg_end_inventory = max(0, cg_end_inventory)

    return df, index, row, total_evr_demand, evr_demand, us_di_demand, ca_di_demand, way_di_demand, evr_end_inventory, us_di_end_inventory, ca_di_end_inventory, cg_end_inventory, amazon_ds_pct, way_ds_pct, evr_pct
