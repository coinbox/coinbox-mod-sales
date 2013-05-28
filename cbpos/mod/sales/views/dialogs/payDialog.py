from PySide import QtGui, QtCore

import cbpos
import sys

logger = cbpos.get_logger(__name__)

class PayDialog(QtGui.QDialog):
    def __init__(self, manager):
        super(PayDialog, self).__init__()

        self.manager = manager
        
        assert self.manager.ticket is not None, 'Ticket in PayDialog is None'

        self.value = self.manager.ticket.total
        self.currency = self.manager.currency
        self.customer = self.manager.ticket.customer
        self.payment = None
        
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.setTabsClosable(False)
        self.tabs.setIconSize(QtCore.QSize(32, 32))
        
        self.due = QtGui.QLineEdit()
        self.due.setReadOnly(True)
        
        tab_bar = self.tabs.tabBar()
        selected = None
        panels = (CashPage(self),
                  ChequePage(self),
                  CardPage(self),
                  VoucherPage(self),
                  FreePage(self),
                  DebtPage(self)
                  )
        
        payment_methods = self.manager.payment_methods
        
        for p, page in enumerate(panels):
            self.tabs.addTab(page, page.icon, page.label)
            if not page.isAllowed() or page.payment[0] not in payment_methods:
                tab_bar.setTabEnabled(p+1, False)
            elif selected is None:
                # Select the first enabled page
                selected = p
                self.tabs.setCurrentIndex(p)

        buttonBox = QtGui.QDialogButtonBox()
        
        self.okBtn = buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        self.okBtn.pressed.connect(self.onOkButton)
        
        self.printBtn = buttonBox.addButton(cbpos.tr.sales._("Print"), QtGui.QDialogButtonBox.ActionRole)
        self.printBtn.pressed.connect(self.onPrintButton)
        
        self.cancelBtn = buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        self.cancelBtn.pressed.connect(self.onCancelButton)
        
        valueLayout = QtGui.QHBoxLayout()
        valueLayout.addWidget(QtGui.QLabel(cbpos.tr.sales._("Due Total")))
        valueLayout.addWidget(self.due)
        
        layout = QtGui.QVBoxLayout()
        layout.addLayout(valueLayout)
        layout.addWidget(self.tabs)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)
        
        self.due.setText(self.currency.format(self.value))

    def onPrintButton(self):
        from cbpos.mod.base.controllers.printer import PrinterManager, Printer, TablePrintJob
        man = PrinterManager()
        printer = man.prompt("test")
        
        if printer is None:
            return
        
        tc = self.manager.ticket.currency
        
        job = TablePrintJob(data=[(tl.description, tl.amount, tc.format(tl.total)) for tl in self.manager.ticket.ticketlines],
                            headers=("Description", "Qty", "Total"),
                            footers=("", "Total:", tc.format(self.manager.ticket.total))
                            )
        
        job.header = "TEL: 04/534031 - 04/534032"
        job.footer = "THANK YOU FOR UR VISIT"
        
        printer.preview(job)

    def onOkButton(self):
        page = self.tabs.currentWidget()
        if page.paymentOk():
            self.payment = page.payment
            self.close()
    
    def onCancelButton(self):
        self.payment = None
        self.close()

class AbstractPage(QtGui.QWidget):
    def __init__(self, dialog):
        super(AbstractPage, self).__init__()
        
        self.dialog = dialog
        self.manager = self.dialog.manager
        
        if self.icon_path is not None:
            self.icon = QtGui.QIcon(self.icon_path)
        else:
            self.icon = QtGui.QIcon()
    
    @property
    def label(self):
        return None
    
    @property
    def payment(self):
        return (None, None)

    @property
    def icon_path(self):
        return None
    
    def isAllowed(self):
        return True

    def paymentOk(self):
        return False

class CashPage(AbstractPage):
    def __init__(self, dialog):
        super(CashPage, self).__init__(dialog)
        
        self.given = QtGui.QDoubleSpinBox()
        self.given.setRange(0, sys.maxint)
        self.given.valueChanged.connect(self.onGivenValueChanged)
        
        self.change = QtGui.QLineEdit()
        self.change.setReadOnly(True)
        
        form = QtGui.QFormLayout()
        form.addRow(cbpos.tr.sales._("Given"), self.given)
        form.addRow(cbpos.tr.sales._("Change"), self.change)
        
        self.setLayout(form)
        
        self.givenValue = self.dialog.value
        self.changeValue = 0

        self.given.setValue(self.givenValue)
        self.change.setText(self.manager.currency_display(self.changeValue))

    @property
    def label(self):
        return cbpos.tr.sales._("Cash")
    
    @property
    def payment(self):
        return ("cash", True)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-cash.png')

    def paymentOk(self):
        if self.givenValue < self.dialog.value:
            message = cbpos.tr.sales._('Not enough. {value} remaining.').format(
                        value=self.manager.currency_display(-self.changeValue))
            QtGui.QMessageBox.warning(self, cbpos.tr.sales._('Pay ticket'), message)
            return False
        elif self.givenValue > self.dialog.value:
            message = cbpos.tr.sales._('Return change: {value}.').format(
                        value=self.manager.currency_display(self.changeValue))
            QtGui.QMessageBox.warning(self, cbpos.tr.sales._('Pay Ticket'), message)
            return True
        else:
            return True

    def onGivenValueChanged(self):
        try:
            from decimal import Decimal
            self.givenValue = Decimal(self.given.value())
        except Exception as e:
            self.givenValue = 0
            logger.error(e)
        self.changeValue = self.givenValue-self.dialog.value
        
        # TODO: use rounding to closest unit
        
        self.change.setText(self.manager.currency_display(self.changeValue))

class ChequePage(AbstractPage):
    @property
    def label(self):
        return cbpos.tr.sales._("Cheque")
    
    @property
    def payment(self):
        return ("cheque", True)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-cheque.png')

    def paymentOk(self):
        return True

class VoucherPage(CashPage):
    def __init__(self, dialog):
        AbstractPage.__init__(self, dialog)

        self.given = QtGui.QDoubleSpinBox()
        self.given.setRange(0, sys.maxint)
        self.given.valueChanged.connect(self.onGivenValueChanged)
        
        self.change = QtGui.QLineEdit()
        self.change.setReadOnly(True)
        
        form = QtGui.QFormLayout()
        form.addRow(cbpos.tr.sales._("Voucher Value"), self.given)
        form.addRow(cbpos.tr.sales._("Change"), self.change)
        
        self.setLayout(form)
        
        self.givenValue = self.dialog.value
        self.changeValue = 0

        self.given.setValue(self.givenValue)
        self.change.setText(self.manager.currency_display(self.changeValue))
    
    @property
    def label(self):
        return cbpos.tr.sales._("Voucher")
    
    @property
    def payment(self):
        return ("voucher", True)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-voucher.png')

class CardPage(AbstractPage):
    @property
    def label(self):
        return cbpos.tr.sales._("Card")
    
    @property
    def payment(self):
        return ("card", True)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-card.png')

    def isAllowed(self):
        return False

    def paymentOk(self):
        return False

class FreePage(AbstractPage):
    @property
    def label(self):
        return cbpos.tr.sales._("Free")
    
    @property
    def payment(self):
        return ("free", False)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-free.png')

    def isAllowed(self):
        return self.dialog.customer is not None

    def paymentOk(self):
        return True

class DebtPage(AbstractPage):
    
    def __init__(self, dialog):
        super(DebtPage, self).__init__(dialog)

        self.debt = QtGui.QLineEdit()
        self.debt.setReadOnly(True)
        
        self.name = QtGui.QLineEdit()
        self.name.setReadOnly(True)
        
        self.maxDebt = QtGui.QLineEdit()
        self.maxDebt.setReadOnly(True)
        
        self.currentDebt = QtGui.QLineEdit()
        self.currentDebt.setReadOnly(True)
        
        form = QtGui.QFormLayout()
        rows = ((cbpos.tr.sales._("Debt"), self.debt),
                (cbpos.tr.sales._("Customer"), self.name),
                (cbpos.tr.sales._("Max Debt"), self.maxDebt),
                (cbpos.tr.sales._("Current Debt"), self.currentDebt))
        
        [form.addRow(*row) for row in rows]
        
        self.setLayout(form)

        self.debt.setText(self.manager.currency_display(self.dialog.value))
        c = self.dialog.customer
        if c is not None:
            cc = c.currency
            self.name.setText(c.name)
            if c.max_debt is None:
                self.maxDebt.setText("")
            else:
                self.maxDebt.setText(cc.format(c.max_debt))
            self.currentDebt.setText(cc.format(c.debt))

    @property
    def label(self):
        return cbpos.tr.sales._("Debt")
    
    @property
    def payment(self):
        return ("debt", False)
    
    @property
    def icon_path(self):
        return cbpos.res.sales('images/pay-debt.png')

    def isAllowed(self):
        return self.dialog.customer is not None

    def paymentOk(self):
        if self.dialog.customer is not None:
            return True
