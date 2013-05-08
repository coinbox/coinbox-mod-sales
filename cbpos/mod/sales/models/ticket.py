import cbpos

import cbpos.mod.base.models.common as common

import cbpos.mod.currency.controllers as currency

from cbpos.mod.stock.models.product import Product
from cbpos.mod.sales.models.ticketline import TicketLine

from sqlalchemy import func, Table, Column, Integer, String, Float, Boolean, Enum, DateTime, MetaData, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method, Comparator

class Ticket(cbpos.database.Base, common.Item):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    date_open = Column(DateTime, nullable=True, default=func.current_timestamp())
    date_close = Column(DateTime, nullable=True)
    payment_method = Column(Enum('cash', 'cheque', 'voucher', 'card', 'free', 'debt'), nullable=True)
    date_paid = Column(DateTime, nullable=True)
    comment = Column(String(255), nullable=True)
    discount = Column(Float, nullable=False, default=0)
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    currency = relationship("Currency", backref="tickets")
    customer = relationship("Customer", backref="tickets")
    user = relationship("User", backref="tickets")

    @hybrid_property
    def paid(self):
        return self.date_paid is not None

    @paid.setter
    def paid(self, value):
        if value:
            self.date_paid = func.now()
        else:
            self.date_paid = None

    @paid.expression
    def paid(cls):
        return cls.date_paid != None

    def pay(self, method, paid=True):
        self.payment_method = method
        self.paid = paid
        session = cbpos.database.session()
        session.commit()
    
    @hybrid_property
    def closed(self):
        return self.date_close is not None

    @closed.setter
    def closed(self, value):
        session = cbpos.database.session()
        if value:
            self.date_close = func.now()
            result = session.query(Product, TicketLine.amount).filter((TicketLine.ticket == self) & \
                                                        (TicketLine.product_id == Product.id) & \
                                                        Product.in_stock).all()
            for p, amount in result:
                p.quantity_out(amount)
        else:
            self.date_close = None
        session.commit()

    @closed.expression
    def closed(cls):
        return cls.date_close != None

    @hybrid_property
    def taxes(self):
        """
        Returns the sum of taxes of all ticketlines
        """
        session = cbpos.database.session()
        total_taxes = session.query(func.sum(TicketLine.taxes)).filter(TicketLine.ticket == self).one()[0]
        return float(total_taxes) if total_taxes is not None else 0 

    @hybrid_property
    def total(self):
        """
        Returns the total, including taxes and discounts.
        """
        session = cbpos.database.session()
        
        query = session.query(func.sum(TicketLine.total), func.sum(TicketLine.taxes))
        query = query.filter(TicketLine.ticket == self)
        total, taxes = query.one()
        
        total = float(total) if total is not None else 0
        taxes = float(taxes) if taxes is not None else 0
        
        return total*(1-self.discount)+taxes
    
    @hybrid_property
    def subtotal(self):
        """
        Returns the subtotal, excluding any taxes or discounts, e.g. net total.
        """
        session = cbpos.database.session()
        total = session.query(func.sum(TicketLine.subtotal)).filter(TicketLine.ticket == self).one()[0]
        return float(total) if total is not None else 0
    
    @hybrid_property
    def display(self):
        return '#%d' % (self.id,)
    
    @display.expression
    def display(self):
        return func.concat('#', self.id)
    
    def addLineFromProduct(self, p):
        session = cbpos.database.session()
        tls = session.query(TicketLine).filter((TicketLine.product == p) & ~TicketLine.is_edited).all()
        if len(tls) > 0:
            tls[0].update(amount=tls[0].amount+1)
        else:
            sell_price = currency.convert(p.price, p.currency, self.currency)
            tl = TicketLine()
            tl.update(description=p.name, sell_price=sell_price, amount=1, discount=0,
                      ticket=self, product=p, is_edited=False)
    
    def __repr__(self):
        return "<Ticket %s>" % (self.id,)
