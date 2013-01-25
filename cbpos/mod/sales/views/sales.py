from PySide import QtGui, QtCore

import cbpos

from cbpos.mod.auth.controllers import user
import cbpos.mod.currency.controllers as currency
from cbpos.mod.sales.models import Ticket, TicketLine

from cbpos.mod.stock.models import Product
from cbpos.mod.currency.models import Currency

from cbpos.mod.stock.views.widgets import ProductCatalog
from cbpos.mod.customer.views.dialogs import CustomerChooserDialog

from cbpos.mod.sales.views.dialogs import EditDialog, PayDialog
from cbpos.mod.sales.views.widgets import TotalPanel, LogoPanel, TicketTable

class SalesPage(QtGui.QWidget):
    def __init__(self):
        super(SalesPage, self).__init__()
        
        self.customer = QtGui.QLineEdit()
        self.customer.setReadOnly(True)
        self.customer.setPlaceholderText(cbpos.tr.sales._('No customer selected'))
        
        self.customerBtn = QtGui.QPushButton(cbpos.tr.sales._('Choose'))
        
        self.tickets = QtGui.QComboBox()
        self.tickets.setEditable(False)
        
        self.newTicketBtn = QtGui.QPushButton(cbpos.tr.sales._("New"))
        
        self.ticketTable = TicketTable()
        
        self.currency = QtGui.QComboBox()
        self.currency.setEditable(False)
        
        self.discount = QtGui.QDoubleSpinBox()
        self.discount.setRange(0, 100)
        self.discount.setSuffix('%')
        
        self.total = TotalPanel()
        
        self.logo = LogoPanel()
        
        self.catalogLbl = QtGui.QLabel(cbpos.tr.sales._("Choose a product"))
        self.catalog = ProductCatalog()
        
        self.payBtn = QtGui.QPushButton(cbpos.tr.sales._("Pay"))
        self.cancelBtn = QtGui.QPushButton(cbpos.tr.sales._("Cancel"))
        
        layout = QtGui.QVBoxLayout()
        
        topOptions = QtGui.QHBoxLayout()
        topOptions.addWidget(self.customer)
        topOptions.addWidget(self.customerBtn)
        topOptions.addWidget(self.tickets)
        topOptions.addWidget(self.newTicketBtn)
        
        topOptions.setStretch(0, 1)
        topOptions.setStretch(1, 0)
        topOptions.setStretch(2, 1)
        topOptions.setStretch(3, 0)
        
        bottomOptions = QtGui.QHBoxLayout()
        bottomOptions.addWidget(self.currency)
        bottomOptions.addStretch(1)
        bottomOptions.addWidget(self.discount)
        
        bottomOptions.setStretch(0, 1)
        bottomOptions.setStretch(1, 1)
        bottomOptions.setStretch(2, 0)
        
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.payBtn)
        buttons.addWidget(self.cancelBtn)
        
        buttons.setStretch(0, 1)
        buttons.setStretch(1, 1)
        
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        size_policy.setVerticalStretch(1)
        size_policy.setHorizontalStretch(1)
        self.payBtn.setSizePolicy(size_policy)
        self.cancelBtn.setSizePolicy(QtGui.QSizePolicy(size_policy))
        
        left = QtGui.QVBoxLayout()
        left.addLayout(topOptions)
        left.addWidget(self.ticketTable)
        left.addLayout(bottomOptions)
        
        right = QtGui.QVBoxLayout()
        right.addWidget(self.logo)
        right.addWidget(self.catalogLbl)
        right.addWidget(self.catalog)
        
        top = QtGui.QHBoxLayout()
        top.addLayout(left)
        top.addLayout(right)
        
        bottom = QtGui.QHBoxLayout()
        bottom.addWidget(self.total)
        bottom.addLayout(buttons)
        
        bottom.setStretch(0, 1)
        bottom.setStretch(1, 1)
        
        layout.addLayout(top)
        layout.addLayout(bottom)
        
        self.setLayout(layout)
        
        # Signals
        self.customerBtn.pressed.connect(self.onCustomerButton)
        self.tickets.activated[int].connect(self.onTicketChanged)
        self.newTicketBtn.pressed.connect(self.onNewTicketButton)
        
        #self.ticketTable.currentCellChanged.connect(self.onTicketlineItemChanged)
        #self.ticketTable.cellDoubleClicked.connect(self.onTicketlineItemActivate)
        self.ticketTable.lineDeleted.connect(self.onTicketlineDeleted)
        
        self.currency.activated[int].connect(self.onCurrencyChanged)
        self.discount.valueChanged.connect(self.onDiscountValueChanged)
        
        self.payBtn.pressed.connect(self.onCloseTicketButton)
        self.cancelBtn.pressed.connect(self.onCancelTicketButton)
        
        self.catalog.childSelected.connect(self.onProductCatalogItemActivate)
        
        self.setCurrentTicket(None)
        
    def populate(self):
        session = cbpos.database.session()
        
        tc = self.ticket.currency if self.ticket is not None else currency.default
        items = session.query(Currency.display, Currency).all()
        self.currency.clear()
        for i, item in enumerate(items):
            self.currency.addItem(*item)
            if item[1] == tc:
                self.currency.setCurrentIndex(i)

        ts = session.query(Ticket).filter(~Ticket.closed).all()
        self.tickets.clear()
        for i, t in enumerate(ts):
            label = 'Ticket #%s' % (t.id,)
            self.tickets.addItem(label, t)
        try:
            i = ts.index(self.ticket)
        except ValueError:
            i = -1
        self.tickets.setCurrentIndex(i)

        if self.ticket is None:
            self.customer.setText('')
            self.discount.setValue(0)
            self.total.setValue(tc.format(0), "0%", tc.format(0))
            
            self.ticketTable.empty()
        else:
            c = self.ticket.customer
            self.customer.setText('' if c is None else c.name)
            self.discount.setValue(self.ticket.discount*100.0)
            self.total.setValue(tc.format(self.ticket.subtotal), "0%", tc.format(self.ticket.total))
            
            self.ticketTable.fill(self.ticket)

    def setCurrentTicket(self, t):
        self.ticket = t
        
        enabled = t is not None
        self.currency.setEnabled(enabled)
        self.customer.setEnabled(enabled)
        self.customerBtn.setEnabled(enabled)
        self.discount.setEnabled(enabled)
        self.payBtn.setEnabled(enabled)
        self.cancelBtn.setEnabled(enabled)
        self.populate()

    def _doCheckCurrentTicket(self):
        if self.ticket is None:
            QtGui.QMessageBox.warning(self, 'No ticket', 'Select a ticket.')
            return None
        else:
            return self.ticket

    def _doCheckCurrentTicketline(self):
        item = self.ticketTable.currentItem()
        if item is None:
            QtGui.QMessageBox.warning(self, 'No ticketline', 'Select a ticketline.')
            return None
        else:
            return item.data(QtCore.Qt.UserRole+1)

    def _doChangeAmount(self, inc):
        t = self._doCheckCurrentTicket()
        tl = self._doCheckCurrentTicketline()
        if t and tl:
            new_amount = tl.amount+inc
            if new_amount>0:
                p = tl.product
                if p is not None and p.in_stock and p.quantity<new_amount:
                    QtGui.QMessageBox.warning(self, 'Warning', 'Amount exceeds the product quantity in stock!')
                tl.update(amount=new_amount)
            else:
                tl.delete()
                self.enableTicketlineActions()
            self.populate()

    #####################
    #########   #########
    ##     onEvent     ##
    #########   #########
    #####################
    
    def onNewTicketButton(self):
        def_c = currency.get_default()
        t = Ticket()
        t.update(discount=0, user=user.current, currency=def_c)
        self.setCurrentTicket(t)
    
    def onCloseTicketButton(self):
        t = self._doCheckCurrentTicket()
        if t:
            dlg = PayDialog(t.total, t.currency, t.customer)
            dlg.exec_()
            if dlg.payment is not None:
                payment_method, paid = dlg.payment
                t.pay(str(payment_method), bool(paid))
                t.closed = True
                self.setCurrentTicket(None)
    
    def onCancelTicketButton(self):
        t = self._doCheckCurrentTicket()
        if t:
            t.delete()
            self.setCurrentTicket(None)
    
    def onTicketChanged(self, index):
        t = self.tickets.itemData(index)
        self.setCurrentTicket(t)
    
    def onTicketlineItemChanged(self, currentRow, currentColumn, previousRow, previousColumn):
        self.enableTicketlineActions()
    
    def onNewTicketlineButton(self):
        t = self._doCheckCurrentTicket()
        if t:
            data = {'description': '', 'amount': 1, 'sell_price': 0, 'discount': 0, 'ticket': t,
                    'product': None, 'is_edited': False}
            _init_data = data.copy()
            dlg = EditDialog(data)
            dlg.exec_()
            if data != _init_data:
                tl = TicketLine()
                tl.update(**data)
                self.populate()
    
    def onEditTicketlineButton(self):
        t = self._doCheckCurrentTicket()
        tl = self._doCheckCurrentTicketline()
        if t and tl:
            data = {'description': '', 'sell_price': 0, 'amount': 1, 'discount': 0, 'product': None, 'is_edited': False}
            tl.fillDict(data)
            _init_data = data.copy()
            dlg = EditDialog(data)
            dlg.exec_()
            if data != _init_data:
                tl.update(**data)
                self.populate()
    
    def onPlusTicketlineButton(self):
        self._doChangeAmount(+1)
    
    def onMinusTicketlineButton(self):
        self._doChangeAmount(-1)

    def onTicketlineDeleted(self, tl):
        tl.delete()
        self.populate()

    def onProductCatalogItemActivate(self, p):
        if p is not None:
            t = self._doCheckCurrentTicket()
            if t:
                t.addLineFromProduct(p)
                self.populate()

    def onCustomerButton(self):
        t = self._doCheckCurrentTicket()
        if not t:
            return
        dlg = CustomerChooserDialog()
        dlg.setCustomer(self.ticket.customer)
        dlg.exec_()
        if dlg.result() == QtGui.QDialog.Accepted:
            c = dlg.customer
            if c is not None:
                t.update(customer=c, discount=c.discount)
            else:
                t.update(customer=None, discount=0)
            self.populate()

    def onCurrencyChanged(self, index):
        t = self._doCheckCurrentTicket()
        if t:
            tc = t.currency
            index = self.currency.currentIndex()
            c = self.currency.itemData(index)
            if len(t.ticketlines) == 0:
                t.update(currency=c)
            else:
                reply = QtGui.QMessageBox.question(self, 'Change Currency', 'Change sell prices accordingly?',
                                                   QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.No:
                    t.update(currency=c)
                elif reply == QtGui.QMessageBox.Yes:
                    for tl in t.ticketlines:
                        tl.update(sell_price=currency.convert(tl.sell_price, tc, c))
                    t.update(currency=c)
            self.setCurrentTicket(t)
    
    def onDiscountValueChanged(self):
        value = self.discount.value()
        t = self._doCheckCurrentTicket()
        if t:
            t.update(discount=value/100.0)
        self.populate()
