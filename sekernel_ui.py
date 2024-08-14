import sys
import threading
from PyQt5.QtWidgets import QApplication, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QRadioButton, QButtonGroup, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout, QAction, QMenu, QSizePolicy, QMainWindow, QTextBrowser
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt, QPropertyAnimation, QPoint, QEasingCurve, QSequentialAnimationGroup, QSize
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QIcon, QMovie, QColor
from llama_cpp import Llama
import kernel
import plugins
import os
import markdown
import webbrowser  # For opening links in a web browser
from pyqtspinner.spinner import WaitingSpinner

# List class
class MyList(list):
    pass

class WorkerSignals(QObject):
    # Define a signal to emit the completion text
    text_ready = pyqtSignal(str)

class TypingEffect(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        username = os.getenv('USERNAME')
        self.setWindowIcon(QtGui.QIcon('perp_logo.ico'))
        self.setWindowTitle("SeKernel UI" + "-" + "You are currently logged in as: " + username)
        self.setGeometry(100, 100, 800, 600)
        #self.setStyleSheet("background-image: url('logo.png'); background-position: relative; color: orange; font-weight: bold")
        # Create a QLabel to hold the GIF
        # Create a QLabel for the GIF
        self.gif_label = QLabel(self)
        # Load the GIF
        self.movie = QMovie('Gal1.gif')
        self.gif_label.setMovie(self.movie)
        # Start the GIF animation
        self.movie.start()
        # Center the GIF within the QLabel
        self.gif_label.setAlignment(Qt.AlignRight)
        # Set the QLabel size to the GIF size
        self.gif_label.setFixedSize(self.movie.currentImage().size())
        self.initUI()

        # Create widgets
    def initUI(self):
        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(50)
        self.input_edit.setPlaceholderText("Enter your prompt...")
        self.input_edit.setToolTip("Feel free to enter your prompt")
        self.input_edit.setStyleSheet("""
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                stop: 0 rgba(255, 255, 255, 100), 
                                stop: 1 rgba(100, 0, 255, 255));
    color: orange;
    font-weight: bold;
    font-size: 20px;
    border-style: outset;
    border-width: 2px;
    border-radius: 7px;
    border-color: beige;
    padding: 5px;
""")
        self.submit_button = QPushButton("Send🐱")
        #self.submit_button.setIcon(QIcon("submit.png"))
        #self.submit_button.setIconSize(QSize(48, 48))
        self.submit_button.setToolTip("Click the submit button to view the options >")
        self.submit_button.clicked.connect(self.start_typing)
        self.submit_button.setStyleSheet("""
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                stop: 0 rgba(255, 255, 255, 100), 
                                stop: 1 rgba(100, 0, 255, 255));
    color: orange;
    font-weight: bold;
    font-size: 20px;
    border-style: outset;
    border-width: 2px;
    border-radius: 7px;
    border-color: beige;
    padding: 5px;
""")
        
        self.qmenu = QMenu()
        self.qmenu.setStyleSheet("""
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                stop: 0 rgba(255, 255, 255, 100), 
                                stop: 1 rgba(100, 0, 255, 255));
    color: orange;
    font-weight: bold;
    font-size: 20px;
    border-style: outset;
    border-width: 2px;
    border-radius: 7px;
    border-color: beige;
    padding: 5px;
""")
        self.checkbox0 = QCheckBox("🗄🌊🏄‍♂️")
        self.checkbox0.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
        self.checkbox0.setToolTip("Check the box to search the internet.")

        # Add actions to the QMenu
        self.action1 = QAction("Internet-connected Chat", self)

        # Set default action
        self.selected_action = None

        self.submit_button.setMenu(self.qmenu)

        # Connect actions to slots
        self.action1.triggered.connect(lambda: self.start_typing("action1"))
        # Add actions to the menu
        self.qmenu.addAction(self.action1)
        self.text_edit = QTextBrowser()
        self.text_edit.setHtml('')  # Initialize with empty HTML
        #self.text_edit.setReadOnly(True)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
        # Set the background color
        self.text_edit.setStyleSheet("""
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                stop: 0 rgba(255, 255, 255, 100), 
                                stop: 1 rgba(100, 0, 255, 255));
    color: orange;
    font-weight: bold;
    font-size: 20px;
    border-style: outset;
    border-width: 2px;
    border-radius: 7px;
    border-color: beige;
    padding: 5px;
""")

        # Create layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.submit_button)

        list_layout = QHBoxLayout()
        list_layout.addWidget(self.text_edit)

        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.checkbox0)

        main_layout = QVBoxLayout()
        main_layout.addLayout(radio_layout)
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(input_layout)
        #self.setLayout(main_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Initialize typing variables
        self.text_buffer = ""
        self.current_index = 0
        self.buffer = ""
        self.text_to_type = ""  # Initialize to avoid AttributeError

        # Set up the QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.type_next_character)

        # Connect anchorClicked signal to a slot
        self.text_edit.anchorClicked.connect(self.open_link)

        # Create a worker signal object
        self.signals = WorkerSignals()
        self.signals.text_ready.connect(self.handle_text_ready)

        # Initialize lists
        self.my_list2 = MyList()
        self.my_list2 = kernel.chatTemplate(plugin=plugins.defaultPlugin())
        

    def start_typing(self, action):
        # Start a new thread to handle the Llama API call
        self.spinner = WaitingSpinner(
            self, 
            True, 
            True, 
            Qt.ApplicationModal, 
            color=QColor("orange"), 
            roundness=457.53,
            fade=48.30,
            lines=3,
            line_length=23.80,
            line_width=19.10,
            radius=30,
            )
        self.spinner.start() # starts spinning
        self.timer.stop()  # Stop any ongoing typing effect
        threading.Thread(target=self.fetch_text_from_llama, args=(action,)).start()

    def fetch_text_from_llama(self, action):
        if action == "action1" and self.checkbox0.isChecked():
            selected_list = self.my_list2
            client = Llama(
                model_path=kernel.model(),
                n_ctx=4096
                )
            question = self.input_edit.text()
            searchPrompt = plugins.searchPlugin(output=question)
            self.my_list2 = kernel.shopTemplate(prompt=question, plugin=plugins.defaultPlugin(), context=searchPrompt)

            # Add the user's question to the history
            self.my_list2.append({"role": "user", "content": question})

            completion = client.create_chat_completion(
                messages=self.my_list2,
                # temperature=0.7,
                #stream=True,
            )
            

            self.signals.text_ready.emit(completion['choices'][0]['message']['content'])
        
        elif action == "action1":
            selected_list = self.my_list2
            client = Llama(
                model_path=kernel.model(),
                n_ctx=4096
                )
            question = self.input_edit.text()

            # Add the user's question to the history
            self.my_list2.append({"role": "user", "content": question})

            completion = client.create_chat_completion(
                messages=self.my_list2,
                # temperature=0.7,
                #stream=True,
            )
            

            self.signals.text_ready.emit(completion['choices'][0]['message']['content'])
            
    def handle_text_ready(self, text):
        if self.spinner:
            self.spinner.stop()
        # Convert Markdown text to HTML
        html_text = markdown.markdown(text)
        # Initialize typing effect for the new text
        self.text_to_type = html_text
        self.current_index = 0
        self.buffer = ""
        self.text_buffer = self.text_edit.toHtml()  # Store existing HTML for buffer management

        # Append new content with Markdown formatting converted to HTML
        user_text = f"<p>User: {self.input_edit.toPlainText()}</p>"
        self.text_edit.setHtml(self.text_buffer + user_text + "<p>Assistant: </p>")
        
        self.timer.start(100)  # Start typing effect with a timeout of 100ms

    def type_next_character(self):
        if self.current_index < len(self.text_to_type):
            self.buffer += self.text_to_type[self.current_index]
            self.current_index += 1
            # Render the current buffer
            self.text_edit.setHtml(self.text_buffer + "<p>User🧛‍♂️: </p>" + self.input_edit.toPlainText() + "<p>Assistant🧛‍♀️: " + self.buffer + "</p>")
            self.scroll_to_bottom()  # Optional, if you want to scroll automatically
        else:
            self.timer.stop()

    def scroll_to_bottom(self):
        # Scroll QTextBrowser to the bottom
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def open_link(self, url):
        # Open the clicked link in the default web browser
        webbrowser.open(url.toString())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TypingEffect()
    #window.resize(400, 200)
    window.show()
    sys.exit(app.exec_())