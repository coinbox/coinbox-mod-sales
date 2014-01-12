import cbpos

import cbmod.base.models.common as common

from sqlalchemy import func, Table, Column, Integer, String, Float, Boolean, MetaData, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method, Comparator

from cbmod.currency.models import CurrencyValue

class TicketLine(cbpos.database.Base, common.Item):
    __tablename__ = 'ticketlines'

    id = Column(Integer, primary_key=True)
    _description = Column('description', String(255), nullable=False, default='')
    _sell_price = Column('sell_price', CurrencyValue(), nullable=False, default=0)
    amount = Column(Integer, nullable=False, default=1)
    discount = Column(Integer, nullable=False, default=0)
    taxes = Column(CurrencyValue(), nullable=False, default=0)
    _is_edited = Column('is_edited', Boolean, nullable=False, default=False)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    
    ticket = relationship("Ticket", backref=backref("ticketlines", cascade="all, delete-orphan"))
    _product = relationship("Product", backref="ticketlines")

    @hybrid_property
    def display(self):
        return unicode(self.ticket.id)+'/'+unicode(self.id)
    
    @display.expression
    def display(self):
        return func.concat(self.ticket.id, '/', self.id)

    @hybrid_property
    def product(self):
        return self._product
    
    @product.setter
    def product(self, p):
        if p is None:
            self._product = None
            self._is_edited = False
        else:
            self._description = p.name
            # Does not set the sell price!
            # It might need to be converted
            #self._sell_price = p.sell_price
            self._product = p
            self._is_edited = False

    @hybrid_property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, value):
        self._description = value
        if self._product is not None and not self._is_edited and value != self._product.name:
            self._is_edited = True

    @hybrid_property
    def sell_price(self):
        return self._sell_price
    
    @sell_price.setter
    def sell_price(self, value):
        self._sell_price = value
        if self._product is not None and not self._is_edited and value != self._product.sell_price:
            self._is_edited = True

    @hybrid_property
    def is_edited(self):
        return self._is_edited
    
    @is_edited.setter
    def is_edited(self, value):
        if value:
            self._is_edited = value
        else:
            # Cannot set it to not edited, if it is marked as edited
            pass

    @hybrid_property
    def total(self):
        """
        Returns the total, including taxes and discounts.
        """
        return (self.taxes + self.sell_price * self.amount) * (100-self.discount)/100
    
    @total.expression
    def total(self):
        return (self.taxes + self.sell_price * self.amount) * (100-self.discount)/100
    
    @hybrid_property
    def subtotal(self):
        """
        Returns the subtotal, excluding any taxes or discounts, e.g. net total.
        """
        return self.amount*self.sell_price
    
    @subtotal.expression
    def subtotal(self):
        return self.amount*self.sell_price

    def __repr__(self):
        return "<TicketLine %s in Ticket #%s>" % (self.id, self.ticket.id)
