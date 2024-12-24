import sys
import sqlite3
from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
        QTreeView, QFrame, QTextEdit, QPushButton, QDialog, QFormLayout,
        QLineEdit, QDialogButtonBox, QSizePolicy, QStackedLayout, QGroupBox, QMessageBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from PyQt5.QtCore import Qt, QSortFilterProxyModel

int_validator = QIntValidator(0, 2000000)

class DatabaseManager:
    def __init__(self, db_name="pycash.db"):
        self.connection = sqlite3.connect(db_name)
        self._create_table()

    def _create_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)
        self.connection.commit()

    def update_stock_products(self, param):
        cursor = self.connection.cursor()
        cursor.executemany("UPDATE products SET stock = stock - ? WHERE id = ?", 
                           [(stock, id_) for stock, id_ in param]
        )
        self.connection.commit()

    def fetch_products(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM products")
        return cursor.fetchall()

    def add_product(self, name, price, stock):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
        self.connection.commit()

    def fetch_products_limited(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name, stock FROM products WHERE stock < 5")
        return cursor.fetchall()

    def delete_products(self, product_id):
        cursor = self.connection.cursor()
        # cursor.executemany("DELETE FROM products WHERE id = ?", [(id_,) for id_ in ids])
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.connection.commit()

    def close(self):
        self.connection.close()

class ProductManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.db_manager = DatabaseManager()

        self._setup_ui()
        self._setup_model()
        self._setup_connections()

        self._sync_products()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)

        self.productList = QGroupBox("Daftar Produk", self)
        self.treeView = QTreeView(self)

        self.operateWidget = QWidget(self)
        self.operateLayout = QHBoxLayout(self.operateWidget)

        self.addButton = QPushButton("Tambah", self)
        self.removeButton = QPushButton("Hapus", self)

        self.operateLayout.addWidget(self.addButton)
        self.operateLayout.addWidget(self.removeButton)

        self.productLayout = QVBoxLayout(self.productList)
        self.productLayout.addWidget(self.treeView)
        self.productLayout.addWidget(self.operateWidget)

        self.productStock = QGroupBox("Product Stock Limited", self)
        self.productStockLayout = QVBoxLayout(self.productStock)
        self.stockTreeView = QTreeView(self)

        self.productStockLayout.addWidget(self.stockTreeView)

        self.layout.addWidget(self.productList)
        self.layout.addWidget(self.productStock)

    def _show_add_product_dialog(self):
        dialog = AddNewProduct(self)

        if dialog.exec_() == QDialog.Accepted:
            result = dialog.getData()

            self.db_manager.add_product(result[0], result[1], result[2])
            self._sync_products()

    def _setup_model(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Price", "Stock"])

        self.treeView.setModel(self.model)
        self.treeView.setSortingEnabled(True)
        self.treeView.resizeColumnToContents(0)

        self.modelStock = QStandardItemModel()
        self.modelStock.setHorizontalHeaderLabels(["Nama", "Stock"])
        self.stockTreeView.setModel(self.modelStock)

    def _setup_connections(self):
        self.addButton.clicked.connect(self._show_add_product_dialog)
        self.removeButton.clicked.connect(self.delete_selected_products)

    def delete_selected_products(self):
        # selected_ids = []

        # for index in range(self.model.rowCount()):
        #     item = self.model.item(index, 0)
        #     if item.checkState() == Qt.Checked:
        #         selected_ids.append(item.data(Qt.UserRole))

        # if selected_ids:
        #     self.db_manager.delete_products(selected_ids)
        #     self._sync_products()

        selected_indexes = self.treeView.selectionModel().selectedIndexes()

        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Pilih salah satu produk yang mau dihapus")
            return

        selected_row = selected_indexes[0].row()
        id_ = self.model.item(selected_row, 0).data(Qt.UserRole)

        self.model.removeRow(selected_row)
        self.db_manager.delete_products(id_)

        self._sync_products()

    def _sync_products(self):
        self.model.removeRows(0, self.model.rowCount())
        self.modelStock.removeRows(0, self.modelStock.rowCount())

        products = self.db_manager.fetch_products()
        products_limited = self.db_manager.fetch_products_limited()

        for product in products:
            id_, name, price, stock = product

            items = [QStandardItem(name), QStandardItem(str(int(price))), QStandardItem(str(stock))]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            items[0].setData(id_, Qt.UserRole)

            self.model.appendRow(items)


        for product in products_limited:
            id_, name, stock = product

            items_limited = [QStandardItem(name), QStandardItem(str(stock))]

            for item in items_limited:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            items_limited[0].setData(id_, Qt.UserRole)

            self.modelStock.appendRow(items_limited)

class AddNewProduct(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Tambah Produk Baru")
        self.setupUI()
        self.connections()

    def setupUI(self):
        layout = QFormLayout(self)

        self.nameLineEdit = QLineEdit(self)
        self.priceLineEdit = QLineEdit(self)
        self.stockLineEdit = QLineEdit(self)

        self.priceLineEdit.setValidator(int_validator)
        self.stockLineEdit.setValidator(int_validator)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        layout.addRow("Nama Produk", self.nameLineEdit)
        layout.addRow("Harga Produk", self.priceLineEdit)
        layout.addRow("Stok Produk", self.stockLineEdit)
        layout.addWidget(self.buttons)

    def getData(self):
        row = [ self.nameLineEdit.text(),
                self.priceLineEdit.text(),
                self.stockLineEdit.text()
              ]

        return row

    def connections(self):
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Product")
        self._setup_ui()
        self.connections()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # TOP SIDE ---------------------------------------------
        topFrame = QFrame(self)
        topFrameLayout = QHBoxLayout(topFrame)

        self.product_name = QLineEdit(self)
        self.product_name.setPlaceholderText("Pilih Produk")
        self.product_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.product_name.setReadOnly(True)

        self.set_product_button = QPushButton("+", self)

        topFrameLayout.addWidget(self.product_name)
        topFrameLayout.addWidget(self.set_product_button)

        # MIDDLE SIDE -------------------------------------------
        middleFrame = QFrame(self)
        middleFrameLayout = QFormLayout(middleFrame)

        self.price = QLineEdit("0")
        self.price.setReadOnly(True)

        self.stock = QLineEdit("1")

        middleFrameLayout.addRow("Harga", self.price)
        middleFrameLayout.addRow("Jumlah", self.stock)

        # BUTTON SIDE -------------------------------------------
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.get_data)
        buttons.rejected.connect(self.reject)
        
        # SET MAIN LAYOUT ---------------------------------------
        layout.addWidget(topFrame)
        layout.addWidget(middleFrame)
        layout.addWidget(buttons)

    def connections(self):
        self.set_product_button.clicked.connect(self.show_choose_product_dialog)

    def get_data(self):
        # return self.name_input.text(), self.price_input.text(), self.stock_input.text()

        id_, name, price, stock = self.product
        amount_stock = int(self.stock.text())

        if amount_stock > stock:
            QMessageBox.warning(self, "Error", "Stok barang kurang.")
            return

        if amount_stock <= 0:
            QMessageBox.warning(self, "Error", "Jumlah tidak boleh kurang atau sama dengan 0")
            return

        self.accept()

    def show_choose_product_dialog(self):
        dialog = ProductChooseDialog(self)

        if dialog.exec_() == QDialog.Accepted:
            self.product = dialog.selected_product
            id_, name, price, stock = dialog.selected_product  # Get the selected product
            self.product_name.setText(name)  # Set the product name in the QTextEdit
            self.price.setText(str(int(price)))

class ProductChooseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.selected_product = None  # To store the selected product details

        self.setWindowTitle("Choose Product")
        self.resize(600, 400)

        self.setup_ui()
        self.setup_model()
        self.setup_connections()
        self.load_products()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Cari nama produk")
        self.layout.addWidget(self.search_bar)

        self.tree_view = QTreeView(self)
        self.layout.addWidget(self.tree_view)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.layout.addWidget(self.button_box)

    def setup_model(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Nama", "Harga", "Stock"])

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)

    def setup_connections(self):
        self.search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.button_box.accepted.connect(self.on_ok_button_clicked)
        self.button_box.rejected.connect(self.reject)

    def load_products(self):
        self.model.removeRows(0, self.model.rowCount())

        products = self.db_manager.fetch_products()

        for product in products:
            id_, name, price, stock = product
            row = [
                QStandardItem(name),
                QStandardItem(f"{int(price)}"),
                QStandardItem(str(stock)),
            ]

            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            row[0].setData(id_, Qt.UserRole)  # Store product ID in the first column

            self.model.appendRow(row)

    def on_ok_button_clicked(self):
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()

        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Pilih salah satu produk.")
            return

        selected_row = selected_indexes[0].row()
        id_ = self.model.item(selected_row, 0).data(Qt.UserRole)
        name = self.model.item(selected_row, 0).text()
        price = int(self.model.item(selected_row, 1).text())
        stock = int(self.model.item(selected_row, 2).text())

        self.selected_product = (id_, name, price, stock)  # Store the selected product
        self.accept()  # Close the dialog with an accepted state




class Transaction(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


        self.db_manager = DatabaseManager()

        self._info = QLabel("Pas", self)

        self._setup_ui()
        self._setup_model()
        self._setup_connections()

    def _setup_ui(self):
        """Initialize the user interface components."""
        self.total = QLineEdit("0", self)
        self.total.setReadOnly(True)

        self.treeView = QTreeView(self)
        self.treeView.setSortingEnabled(True)

        bottomFrame = QFrame(self)
        bottomFrameLayout = QFormLayout(bottomFrame)

        self.payTextEdit = QLineEdit("0", self)
        self.changeTextEdit = QLineEdit("0", self)
        self.changeTextEdit.setReadOnly(True)

        bottomFrameLayout.addRow("Total", self.total)
        bottomFrameLayout.addRow("Bayar", self.payTextEdit)
        bottomFrameLayout.addRow(self._info, self.changeTextEdit)

        self.addProduct = QPushButton("Tambah", self)
        self.removeProduct = QPushButton("Hapus", self)
        self.confirm = QPushButton("Konfirmasi", self)

        operationLayout = QHBoxLayout()
        operationLayout.addWidget(self.addProduct)
        operationLayout.addWidget(self.removeProduct)
        operationLayout.addWidget(self.confirm)

        operationFrame = QFrame(self)
        operationFrame.setLayout(operationLayout)

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.treeView)
        mainLayout.addWidget(bottomFrame)
        mainLayout.addWidget(operationFrame)

        self.setLayout(mainLayout)

    def _setup_model(self):
        """Setup the model for the QTreeView."""
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Nama Produk", "Harga", "Jumlah", "Total"])
        self.treeView.setModel(self.model)
        self.treeView.resizeColumnToContents(0)

    def _setup_connections(self):
        """Connect UI components to their respective methods."""
        self.addProduct.clicked.connect(self.show_add_product_dialog)
        self.removeProduct.clicked.connect(self.delete_product)
        self.confirm.clicked.connect(self.on_confirm_clicked)
        self.payTextEdit.textChanged.connect(self.update_total)

    def on_confirm_clicked(self):
        selected_ids = []

        for index in range(self.model.rowCount()):
            item = self.model.item(index, 3)

            id_ = self.model.item(index, 0).data(Qt.UserRole)
            jumlah = item.text()

            selected_ids.append([jumlah, id_])

            # print("? | ?", (id_, jumlah))
        
        self.db_manager.update_stock_products(selected_ids)

    def show_add_product_dialog(self):
        """Show a dialog to add a product to the transaction."""
        dialog = AddProductDialog(self)

        if dialog.exec_() == QDialog.Accepted:
            id_, name, price, stock = dialog.product

            jumlah = int(dialog.stock.text())
            total = price * jumlah

            row = [ QStandardItem(name), 
                    QStandardItem(str(price)), 
                    QStandardItem(str(jumlah)), 
                    QStandardItem(str(total)) 
                   ]

            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            row[0].setData(id_, Qt.UserRole)

            self.model.appendRow(row)

        self.update_total()

    def delete_product(self):
        """Delete selected products from the transaction."""
        rows_to_remove = []

        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)
            if item.checkState() == Qt.Checked:
                rows_to_remove.append(row)

        for row in reversed(rows_to_remove):
            self.model.removeRow(row)

        self.update_total()

    def update_total(self):
        totalValue = 0
        bayar = 0

        if self.payTextEdit.text() != '':
            bayar = int(self.payTextEdit.text())
        
        if self.payTextEdit.text() == '':
            bayar = 0

        for index in range(self.model.rowCount()):
            totalValue += int(self.model.item(index, 3).text())

        self.total.setText(str(totalValue))

        if bayar == totalValue:
            self._info.setText("Pas")
        elif bayar > totalValue:
            self._info.setText("Kembalian")
        elif bayar < totalValue:
            self._info.setText("Kurang")

        result = totalValue - bayar

        if result < 0:
            result *= -1

        self.changeTextEdit.setText(str(result))


class Panel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.productButton = QPushButton("P", self)
        self.transactionButton = QPushButton("T", self)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.productButton)
        self.mainLayout.addWidget(self.transactionButton)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyCash")

        self._setup_ui()
        self._connection()

    def _setup_ui(self):
        self.centralWidget = QWidget(self)
        self.centralLayout = QHBoxLayout(self.centralWidget)

        self.panel = Panel(self)

        self.transaction = Transaction()
        self.productManager = ProductManager()

        self.secondaryWidget = QWidget(self)
        self.stackedLayout = QStackedLayout(self.secondaryWidget)

        self.stackedLayout.addWidget(self.transaction)
        self.stackedLayout.addWidget(self.productManager)

        self.centralLayout.addWidget(self.panel)
        self.centralLayout.addWidget(self.secondaryWidget)

        self.setCentralWidget(self.centralWidget)

    def _connection(self):
        self.panel.transactionButton.clicked.connect(lambda: self.stackedLayout.setCurrentIndex(0))
        self.panel.productButton.clicked.connect(lambda: self.stackedLayout.setCurrentIndex(1))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("PyCash")
    window.show()

    sys.exit(app.exec_())
