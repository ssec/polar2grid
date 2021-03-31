def convert_old_p2g_date_frmts(frmt):
    """convert old user p2g date formats"""
    dt_frmts = {"_YYYYMMDD": ":%Y%m%d",
                  "_YYMMDD": ":%y%m%d",
                  "_HHMMSS": ":%H%M%S",
                  "_HHMM": ":%H%M"
                  }
    for old_frmt, new_frmt in dt_frmts.items():
        old_start="start_time{}".format(old_frmt)
        new_start="start_time{}".format(new_frmt)
        frmt = frmt.replace(old_start, new_start)

        old_begin="begin_time{}".format(old_frmt)
        frmt = frmt.replace(old_begin, new_start)

        old_end="end_time{}".format(old_frmt)
        new_end = "end_time{}".format(new_frmt)
        frmt = frmt.replace(old_end, new_end)

    return frmt

def convert_p2g_pattern_to_satpy(output_pattern):
    """convert p2g string patterns to satpy"""

    fmt=output_pattern.replace("begin_time", "")
    replacements = {"satellite": "platform_name",
                    "instrument": "sensor",
                    "product_name": "dataset_id",
                    "begin_time": "start_time",
                    }
    for p2g_kw, satpy_kw in replacements.items():
        fmt = fmt.replace(p2g_kw, satpy_kw)
    fmt = convert_old_p2g_date_frmts(fmt)

    return fmt
