import os

class W2WConfig(object):
    def __init__(self, key, password, account_number=None, meter_number=None, freight_account_number=None,
                    integrator_id=None, wsdl_path=None, express_region_code=None, use_test_server=False, proxy=None):
        self.key = key

CONFIG_OBJ = W2WConfig(key=os.getenv('W2W_TOKEN_007'))