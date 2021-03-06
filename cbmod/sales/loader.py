from pydispatch import dispatcher

import cbpos
from cbpos.modules import BaseModuleLoader

class ModuleLoader(BaseModuleLoader):
    def load_models(self):
        from cbmod.sales.models import Ticket, TicketLine
        return [Ticket, TicketLine]

    def test_models(self):
        from cbmod.sales.models import Ticket, TicketLine
    
        session = cbpos.database.session()
    
        from cbmod.currency.models import Currency
        from cbmod.auth.models import User
        from cbmod.customer.models import Customer
    
        cu1 = session.query(Currency).filter_by(id="LBP").one()
        cu2 = session.query(Currency).filter_by(id="USD").one()
        
        c1 = session.query(Customer).filter_by(id=1).one()
        
        u1 = session.query(User).filter_by(id=1).one()
    
        t1 = Ticket(discount=0, currency=cu1, user=u1, customer=None, comment='Test ticket 1')
        t2 = Ticket(discount=30, currency=cu2, user=u1, customer=c1, comment='Test ticket 2')
    
        from cbmod.stock.models import Product
        
        p1 = session.query(Product).filter_by(id=1).one()
    
        tl1 = TicketLine(description='Ticketline 1-1', sell_price=2000, amount=1, discount=0, is_edited=False, ticket=t1, product=None)
        tl2 = TicketLine(description='Ticketline 1-2', sell_price=4500, amount=1, discount=0, is_edited=False, ticket=t1, product=None)
        tl3 = TicketLine(description='Ticketline 1-3 edited from p1', sell_price=5000, amount=2, discount=0, is_edited=True, ticket=t1, product=p1)
        tl4 = TicketLine(description='Ticketline 2-1', sell_price=5, amount=12, discount=0, is_edited=False, ticket=t2, product=None)
        tl5 = TicketLine(description='Ticketline 2-2 ewWeErRtTyYuUiIoOpP', sell_price=1.5, amount=12, discount=0, is_edited=True, ticket=t2, product=p1)
        
        [session.add(tl) for tl in (tl1, tl2, tl3, tl4, tl5)]
        session.commit()

    def init(self):
        dispatcher.send(signal='printing-register-function', sender='sales',
                        function='print-ticket')
        
        return True

    def menu(self):
        from cbpos.interface import MenuItem
        from cbmod.sales.views import SalesPage # DebtsPage
        
        """
                 MenuItem('debts', parent='main',
                          label=cbpos.tr.sales_('Debts'),
                          icon=cbpos.res.sales('images/menu-debts.png'),
                          rel=0,
                          priority=4,
                          page=DebtsPage
                          )
        """
        
        return [[],
                [MenuItem('sales', parent='main',
                          label=cbpos.tr.sales_('Sales'),
                          icon=cbpos.res.sales('images/menu-sales.png'),
                          rel=0,
                          priority=5,
                          page=SalesPage
                          )
                 ]
                ]
