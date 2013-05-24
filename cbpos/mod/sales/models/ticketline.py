import cbpos

import cbpos.mod.base.models.common as common

from sqlalchemy import func, Table, Column, Integer, String, Float, Boolean, MetaData, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method, Comparator

from cbpos.mod.currency.models import CurrencyValue

class TicketLine(cbpos.database.Base, common.Item):
    __tablename__ = 'ticketlines'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False, default='')
    sell_price = Column(CurrencyValue(), nullable=False, default=0)
    amount = Column(Integer, nullable=False, default=1)
    discount = Column(Integer, nullable=False, default=0)
    taxes = Column(CurrencyValue(), nullable=False, default=0)
    is_edited = Column(Boolean, nullable=False, default=False)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    
    ticket = relationship("Ticket", backref=backref("ticketlines", cascade="all, delete-orphan"))
    product = relationship("Product", backref="ticketlines")

    def update(self, **kwargs):
        p = self.product
        if not self.is_edited and p is not None:
            description_edited = ('description' in kwargs and self.description != kwargs['description'])
            price_edited = ('sell_price' in kwargs and self.sell_price != kwargs['sell_price'])
            kwargs.update({'is_edited': (description_edited or price_edited)})
        super(TicketLine, self).update(**kwargs)

    @hybrid_property
    def display(self):
        return unicode(self.ticket.id)+'/'+unicode(self.id)
    
    @display.expression
    def display(self):
        return func.concat(self.ticket.id, '/', self.id)

    @hybrid_property
    def total(self):
        """
        Returns the total, including taxes and discounts.
        """
        return self.amount*self.sell_price*(100-self.discount)/100
    
    @total.expression
    def total(self):
        return self.amount*self.sell_price*(100-self.discount)/100
    
    @hybrid_property
    def subtotal(self):
        """
        Returns the subtotal, excluding any taxes or discounts, e.g. net total.
        """
        return self.amount*self.sell_price
    
    @total.expression
    def subtotal(self):
        return self.amount*self.sell_price

    def __repr__(self):
        return "<TicketLine %s in Ticket #%s>" % (self.id, self.ticket.id)
