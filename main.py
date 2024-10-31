import sys
from PyQt5.QtWidgets import QApplication
from wifiSearchController import WifiScannerController

def main():
    app = QApplication(sys.argv)
    controller = WifiScannerController()
    controller.view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
