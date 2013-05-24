from PySide import QtGui, QtCore

import cbpos

import babel.numbers

logger = cbpos.get_logger(__name__)

class TotalPanel(QtGui.QFrame):
    
    def __init__(self, manager):
        super(TotalPanel, self).__init__()
        
        self.manager = manager
        
        self.subtotal = QtGui.QLabel('-')
        self.tax = QtGui.QLabel('-')
        self.total = QtGui.QLabel('-')
        
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel(cbpos.tr.sales._("Subtotal")), 0, 0)
        layout.addWidget(self.subtotal, 0, 1)
        layout.addWidget(QtGui.QLabel(cbpos.tr.sales._("Tax")), 1, 0)
        layout.addWidget(self.tax, 1, 1)
        layout.addWidget(QtGui.QLabel(cbpos.tr.sales._("Total")), 2, 0)
        layout.addWidget(self.total, 2, 1)
        
        layout.setColumnStretch(0, 1)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.setLayout(layout)
    
    def updateValues(self):
        subtotal = self.manager.currency_display(self.manager.subtotal)
        taxes = self.manager.currency_display(self.manager.taxes)
        total = self.manager.currency_display(self.manager.total)
        
        self.subtotal.setText(subtotal)
        self.tax.setText(taxes)
        self.total.setText(total)

class LogoPanel(QtGui.QFrame):
    
    def __init__(self, manager):
        super(LogoPanel, self).__init__()
        
        self.manager = manager
        
        self.text = QtGui.QLabel('This is the STORE!')
        
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.text)
        
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.setLayout(layout)

class TicketTable(QtGui.QTableWidget):
    
    lineDeleted = QtCore.Signal('QVariant')
    
    def __init__(self, manager):
        super(TicketTable, self).__init__()
        
        self.manager = manager
        
        self.setColumnCount(7)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setShowGrid(False)
        
    def empty(self):
        self.clearContents()
        self.setRowCount(0)
        self.resizeColumnsToContents()

    def fill(self):
        t = self.manager.ticket
        if t is None:
            self.empty()
            return
        
        tls = list(t.ticketlines)
        tc = t.currency
        
        self.setRowCount(len(tls))
        # This is important so that the row numbers do not change while adding 2 items on the same line
        self.setSortingEnabled(False)
        
        icon = QtGui.QIcon.fromTheme('edit-delete')
        for row, tl in enumerate(tls):
            cols = (
                    ('* ' if tl.is_edited else ''),
                    tl.description,
                    self.manager.currency_display(tl.sell_price),
                    u'x{}'.format(babel.numbers.format_number(tl.amount, locale=cbpos.locale)),
                    babel.numbers.format_percent(tl.discount, locale=cbpos.locale),
                    self.manager.currency_display(tl.total)
                    )
            
            for col, item_text in enumerate(cols):
                table_item = QtGui.QTableWidgetItem(item_text)
                table_item.setData(QtCore.Qt.UserRole+1, tl)
                # Items are not enabled
                table_item.setFlags(table_item.flags() ^ QtCore.Qt.ItemIsEditable)
                self.setItem(row, col, table_item)
            
            # Check if the icon is available, or fall back to text
            if icon.isNull():
                controls_item = QtGui.QPushButton(cbpos.tr.sales._('Delete'))
            else:
                controls_item = QtGui.QPushButton()
                controls_item.setIcon(icon)
            
            controls_item.callback = lambda a=tl: self.onDelete(a)
            controls_item.pressed.connect(controls_item.callback)
            self.setCellWidget(row, col+1, controls_item)
        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(True)
    
    def currentLine(self):
        item = self.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole+1)
    
    def onDelete(self, line):
        self.lineDeleted.emit(line)
