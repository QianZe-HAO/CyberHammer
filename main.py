import sys
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide6.QtGui import QIcon


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cyber Hammer')
        # set icon
        self.setWindowIcon(QIcon('./icon/cyberhammer.webp'))
        # set window size
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # create a run button
        self.button_run_script = QPushButton('Run PowerShell Script', self)
        # set button height
        self.button_run_script.setFixedHeight(100)
        self.button_run_script.clicked.connect(self.run_script)

        # create a stop button
        self.button_stop_script = QPushButton('Stop Streamlit Script', self)
        self.button_stop_script.setFixedHeight(100)
        self.button_stop_script.clicked.connect(self.stop_script)

        # add button to layout
        layout.addWidget(self.button_run_script)
        layout.addWidget(self.button_stop_script)

        self.setLayout(layout)
        self.show()

    def run_script(self):
        # run the PowerShell script
        script_path = ".\\web_gui\\cyberhammer_web_gui.ps1"
        window_title = "CyberHammerGUI"
        try:
            # use `start` command to open a new terminal window with a specific title and run the script,
            # /k parameter ensures the terminal won't close after running
            command = f'start "{window_title}" cmd /k powershell -NoExit -File "{script_path}"'
            subprocess.run(command, shell=True)
            print("PowerShell script started successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while starting script: {e}")

    def stop_script(self):
        # stop Streamlit script and close the terminal window with the specific title
        try:
            # Stop the Streamlit process
            subprocess.run(
                ["powershell", "-Command", "Stop-Process -Name streamlit -Force"], check=True, shell=True)
            print("Streamlit script stopped successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error occurred while stopping script: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())
