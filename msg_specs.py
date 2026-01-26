field_07_spec = {
"01":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2, "desc": "Month"},
"02":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2, "desc": "Day"},
"03":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 6, "desc": "Time"},
}

field_12_spec = {
"01":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2, "desc": "Year"},
"02":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2, "desc": "Month"},
"03":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2, "desc": "Day"},
"04":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 6, "desc": "Time"},
}


field_55_spec = {
"00":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 12, "desc": "ICC Header"},
"01":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 16, "desc": "Application Cryptogram"},
"02":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 2, "max_len": 99, "desc": "Issuer Application Data (IAD)"},
"03":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 8,  "desc": "Unpredictable Number"},
"04":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 4,  "desc": "ATC"},
"05":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 10, "desc": "Terminal Verification Results (TVR)"},
"06":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 6,  "desc": "Transaction Date"},
"07":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2,  "desc": "Transaction Type"},
"08":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 12, "desc": "Amount Authorized"},
"09":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 4,  "desc": "Transaction Currency Code"},
"10":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 4,  "desc": "Terminal Country Code"},
"11":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 4,  "desc": "Application Interchange Profile (AIP)"},
"12":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 12, "desc": "Amount, Other"},
"13":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2,  "desc": "Application PAN Sequence Number"},
"14":  {"data_enc": "ascii", "len_enc": "ascii", "len_type": 0, "max_len": 2,  "desc": "Cryptogram Information Data (CID)"},
}

spec = {
"h":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 0,   "desc": "Message Header"},
"t":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 4,   "desc": "Message Type"},
"p":      {"data_enc": "b",     "len_enc": "cp500", "len_type": 0, "max_len": 8,   "desc": "Bitmap, Primary"},
"1":      {"data_enc": "b",     "len_enc": "cp500", "len_type": 0, "max_len": 8,   "desc": "Bitmap, Secondary"},
"2":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 19,  "desc": "Primary Account Number (PAN)"},
"3":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 6,   "desc": "Processing Code"},
"4":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 12,  "desc": "Amount, Transaction"},
"7":      {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 10,  "desc": "Date And Time, Transmission", "sub_field_specs": field_07_spec}, 
"11":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 6,   "desc": "System Trace Audit Number"},
"12":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 12,  "desc": "Date and Time, Local Transaction", "sub_field_specs": field_12_spec},
"14":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 4,   "desc": "Date, Expiration"},
"19":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 3,   "desc": "Acquiring Institution Country Code"},
"22":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 12,  "desc": "Point Of Service Data Code"},
"24":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 3,   "desc": "Function Code"},
"25":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 4,   "desc": "Message Reason Code"},
"26":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 4,   "desc": "Card Acceptor Business Code"},
"27":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 1,   "desc": "Approval Code Length"},
"31":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 15,  "desc": "Acquirer Reference"},
"32":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 11,  "desc": "Acquiring Institution ID Code"},
"33":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 11,  "desc": "Forwarding Institution ID Code"},
"35":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 99,  "desc": "Track 2 Data"},
"37":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 12,  "desc": "Retrieval Reference Number"},
"38":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 6,   "desc": "Approval Code"},
"39":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 3,   "desc": "Action Code"},
"41":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 8,   "desc": "Card Acceptor Terminal ID"},
"42":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 15,  "desc": "Card Acceptor ID Code"},
"43":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 2, "max_len": 99,  "desc": "Card Acceptor Name/Location"},
"49":     {"data_enc": "cp500", "len_enc": "cp500", "len_type": 0, "max_len": 3,   "desc": "Currency Code, Transaction"},
"55":     {"data_enc": "b",     "len_enc": "cp500", "len_type": 3, "max_len": 999, "desc": "ICC data", "sub_field_specs": field_55_spec},
}



