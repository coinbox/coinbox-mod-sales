from PySide import QtGui, QtCore

import cbpos

from cbpos.mod.sales.controllers import SalesManager, TicketSelectionException

from cbpos.mod.stock.views.widgets import ProductCatalog
from cbpos.mod.customer.views.dialogs import CustomerChooserDialog

from cbpos.mod.sales.views.dialogs import EditDialog, PayDialog
from cbpos.mod.sales.views.widgets import TotalPanel, LogoPanel, TicketTable

class SalesPage(QtGui.QWidget):
    def __init__(self):
        super(SalesPage, self).__init__()
        
        self.manager = SalesManager()
        
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
        self.discount.setRange(0.0, 100.0)
        self.discount.setSingleStep(5.0)
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
        self.discount.editingFinished.connect(self.onDiscountValueChanged)
        
        self.payBtn.pressed.connect(self.onCloseTicketButton)
        self.cancelBtn.pressed.connect(self.onCancelTicketButton)
        
        self.catalog.childSelected.connect(self.onProductCatalogItemActivate)
        
        self.setCurrentTicket(None)
        
    def populate(self):
        
        # Set the Ticket field
        t = self.manager.ticket
        selected_index = -1
        
        self.tickets.clear()
        for i, (label, item) in enumerate(self.manager.list_tickets()):
            self.tickets.addItem(label, item)
            if item == t:
                selected_index = i
        self.tickets.setCurrentIndex(selected_index)
        
        # Set the Currency field
        tc = self.manager.currency
        self.currency.clear()
        for i, (label, item) in enumerate(self.manager.list_currencies()):
            self.currency.addItem(label, item)
            if item == tc:
                self.currency.setCurrentIndex(i)

        # Set the Customer field
        if self.manager.customer is None:
            self.customer.setText("")
        else:
            self.customer.setText(self.manager.customer.display)
        
        # Set the Discount field
        self.discount.setValue(self.manager.discount)
        
        # Set the Total field
        self.total.setValue(self.manager.subtotal, self.manager.taxes, self.manager.total)

        # Fill the ticketlines table
        if self.manager.ticket is None:
            self.ticketTable.empty()
        else:
            self.ticketTable.fill(self.manager.ticket)

    def setCurrentTicket(self, t):
        self.manager.ticket = t
        
        enabled = t is not None
        self.currency.setEnabled(enabled)
        self.customer.setEnabled(enabled)
        self.customerBtn.setEnabled(enabled)
        self.discount.setEnabled(enabled)
        self.payBtn.setEnabled(enabled)
        self.cancelBtn.setEnabled(enabled)
        
        self.populate()

    def warnTicketSelection(self):
        QtGui.QMessageBox.warning(self, cbpos.tr.sales._('No ticket'), cbpos.tr.sales._('Select a ticket.'))
    
    def warnTicketlineSelection(self):
        QtGui.QMessageBox.warning(self, cbpos.tr.sales._('No ticketline'), cbpos.tr.sales._('Select a ticketline.'))

    def addAmount(self, inc):
        if self.manager.ticket is None:
            self.warnTicketSelection()
            return
        
        tl = self.ticketTable.currentLine()
        if tl is None:
            self.warnTicketlineSelection()
            return
        
        try:
            self.manager.set_ticketline_amount(tl.amount+inc)
        except ValueError as e:
            QtGui.QMessageBox.warning(self, 'Warning', 'Amount exceeds the product quantity in stock!')
            self.manager.set_ticketline_amount(tl.amount+inc, force=True)
        #self.enableTicketlineActions()
        self.populate()

    #####################
    #########   #########
    ##     onEvent     ##
    #########   #########
    #####################
    
    def onNewTicketButton(self):
        self.setCurrentTicket(self.manager.new_ticket())
    
    def onCloseTicketButton(self):
        t = self.manager.ticket
        if t is None:
            self.warnTicketSelection()
            return
        
        dlg = PayDialog(t.total, t.currency, t.customer)
        dlg.exec_()
        if dlg.payment is not None:
            payment_method, paid = dlg.payment
            self.manager.close_ticket(payment_method, paid)
            self.setCurrentTicket(None)
    
    def onCancelTicketButton(self):
        try:
            self.manager.cancel_ticket()
        except TicketSelectionException as e:
            self.warnTicketSelection()
        else:
            self.setCurrentTicket(None)
    
    def onTicketChanged(self, index):
        t = self.tickets.itemData(index)
        self.setCurrentTicket(t)
    
    def onTicketlineItemChanged(self, currentRow, currentColumn, previousRow, previousColumn):
        self.enableTicketlineActions()
    
    def onNewTicketlineButton(self):
        t = self.manager.ticket
        if t is None:
            self.warnTicketSelection()
            return
        
        data = {'description': '', 'amount': 1, 'sell_price': 0, 'discount': 0, 'ticket': t,
                'product': None, 'is_edited': False}
        _init_data = data.copy()
        dlg = EditDialog(data)
        dlg.exec_()
        if data != _init_data:
            self.manager.add_ticketline(data)
            self.populate()
    
    def onEditTicketlineButton(self):
        t = self.manager.ticket
        if t is None:
            self.warnTicketSelection()
            return
        
        tl = self.ticketTable.currentLine()
        if tl is None:
            self.warnTicketlineSelection()
            return
        
        data = {'description': '', 'sell_price': 0, 'amount': 1, 'discount': 0, 'product': None, 'is_edited': False}
        tl.fillDict(data)
        _init_data = data.copy()
        dlg = EditDialog(data)
        dlg.exec_()
        if data != _init_data:
            self.manager.add_ticketline(data)
            self.populate()
    
    def onPlusTicketlineButton(self):
        self.addAmount(+1)
    
    def onMinusTicketlineButton(self):
        self.addAmount(-1)

    def onTicketlineDeleted(self, tl):
        try:
            self.manager.remove_ticketline(tl)
        except TicketSelectionException as e:
            self.warnTicketSelection()
        finally:
            self.populate()

    def onProductCatalogItemActivate(self, p):
        if p is not None:
            try:
                self.manager.add_product(p)
            except TicketSelectionException as e:
                self.warnTicketSelection()
            finally:
                self.populate()

    def onCustomerButton(self):
        t = self.manager.ticket
        if t is None:
            self.warnTicketSelection()
            return
        
        dlg = CustomerChooserDialog()
        dlg.setCustomer(t.customer)
        dlg.exec_()
        if dlg.result() == QtGui.QDialog.Accepted:
            self.manager.customer = dlg.customer
            self.populate()

    def onCurrencyChanged(self, index):
        index = self.currency.currentIndex()
        c = self.currency.itemData(index)
        
        try:
            self.manager.currency = c
        except TicketSelectionException as e:
            self.warnTicketSelection()
        else:
            self.populate()
    
    def onDiscountValueChanged(self):
        value = self.discount.value()
        try:
            self.manager.discount = value
        except TicketSelectionException as e:
            self.warnTicketSelection()
        else:
            self.populate()
