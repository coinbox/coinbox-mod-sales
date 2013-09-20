import cbpos
from cbpos.modules import BaseModuleMetadata

class ModuleMetadata(BaseModuleMetadata):
    base_name = 'sales'
    version = '0.1.0'
    display_name = 'Sales and Debt Module'
    dependencies = (
        ('base', '0.1'),
        ('currency', '0.1'),
        ('auth', '0.1'),
        ('stock', '0.1'),
        ('customer', '0.1'),
    )
    config_defaults = tuple()
