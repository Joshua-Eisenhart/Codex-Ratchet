# S6 STUB_ON_COMPLETE_PATH — expected to trip.
def load_data():
    raise NotImplementedError

def use_load():
    return load_data()

def parse_data():
    # TODO: implement parser
    return None

def use_parse():
    result = parse_data()
    return result

def scan_data():
    pass

def use_scan():
    return scan_data()
