from pydispatch import dispatcher

import cbpos

from cbpos.mod.auth.controllers import user
import cbpos.mod.currency.controllers as currency

from cbpos.mod.sales.models import Ticket, TicketLine

from cbpos.mod.currency.models import Currency

logger = cbpos.get_logger(__name__)

class TicketSelectionException(ValueError):
    def __init__(self):
        super(TicketSelectionException, self).__init__('No ticket selected')

class SalesManager(object):
    
    def __init__(self):
        pass
    
    # Ticket Management
    
    __ticket = None
    @property
    def ticket(self):
        return self.__ticket
    
    @ticket.setter
    def ticket(self, t):
        self.__ticket = t
        self.update_taxes()
    
    def new_ticket(self):
        c = currency.default
        t = Ticket()
        t.update(discount=0, user=user.current, currency=c)
        self.update_taxes()
        return t
    
    def cancel_ticket(self):
        if self.ticket is None:
            raise TicketSelectionException()
        self.ticket.delete()
        self.ticket = None
    
    def close_ticket(self, payment_method, paid):
        if self.ticket is None:
            raise TicketSelectionException()
        self.ticket.pay(str(payment_method), bool(paid))
        self.ticket.closed = True
    
    def list_tickets(self):
        session = cbpos.database.session()
        return session.query(Ticket.display, Ticket).filter(~Ticket.closed)
    
    @property
    def subtotal(self):
        if self.__ticket is None:
            return self.currency.format(0)
        else:
            return self.currency.format(self.ticket.subtotal)
    
    @property
    def taxes(self):
        if self.ticket is None:
            return self.currency.format(0)
        else:
            return self.currency.format(self.ticket.taxes)
    
    @property
    def total(self):
        if self.__ticket is None:
            return self.currency.format(0)
        else:
            return self.currency.format(self.ticket.total)
    
    # Ticket Operations
    
    def add_ticketline(self, data):
        if self.ticket is None:
            raise TicketSelectionException()
        
        tl = TicketLine()
        tl.update(**data)
        
        self.update_taxes()
        
        return tl
    
    def edit_ticketline(self, tl, data):
        if self.ticket is None:
            raise TicketSelectionException()
        
        tl.update(**data)
        
        self.update_taxes()
    
    def remove_ticketline(self, tl):
        if self.ticket is None:
            raise TicketSelectionException()
        
        tl.delete()
        
        self.update_taxes()
    
    def set_ticketline_amount(self, tl, amount, force=False):
        if self.ticket is None:
            raise TicketSelectionException()
        
        new_amount = amount
        if new_amount>0:
            if not force:
                p = tl.product
                if p is not None and p.in_stock and p.quantity<new_amount:
                    raise ValueError("Amount in stock is smaller than set amount")
            tl.update(amount=new_amount)
        else:
            tl.delete()
        
        self.update_taxes()
    
    def add_product(self, p):
        if self.ticket is None:
            raise TicketSelectionException()
        
        self.ticket.addLineFromProduct(p)
        self.update_taxes()
    
    def update_taxes(self):
        dispatcher.send(signal='update-taxes', sender='sales', manager=self)
    
    # Ticket Tools
    
    def list_currencies(self):
        session = cbpos.database.session()
        return session.query(Currency.display, Currency)
    
    __currency = None
    @property
    def currency(self):
        if self.ticket is not None:
            return self.ticket.currency
        elif self.__currency is not None:
            return self.__currency
        else:
            return currency.default
    
    @currency.setter
    def currency(self, c):
        if c is None:
            self.__currency = currency.default
            return
        
        self.__currency = c
        if self.ticket is not None:
            orig_c = self.currency
            for tl in self.ticket.ticketlines:
                tl.update(sell_price=currency.convert(tl.sell_price, orig_c, c))
            self.ticket.update(currency=c)
            
            self.update_taxes()
    
    def is_discount_allowed(self):
        return True
    
    @property
    def discount(self):
        # Returns a value in the range [0-100]
        if self.ticket is None:
            return 0
        else:
            return self.ticket.discount*100
    
    @discount.setter
    def discount(self, value):
        # Value is in the range [0-100]
        if self.ticket is None:
            raise TicketSelectionException()
        
        self.ticket.update(discount=value/100.0)
    
    def list_customers(self):
        pass
    
    @property
    def customer(self):
        if self.ticket is None:
            return None
        else:
            return self.ticket.customer
    
    @customer.setter
    def customer(self, c):
        if self.ticket is None:
            raise TicketSelectionException()
        
        if c is not None:
            self.ticket.update(customer=c, discount=c.discount)
        else:
            self.ticket.update(customer=None, discount=0)
