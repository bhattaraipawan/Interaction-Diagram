#Standard Library system for closing of program
import sys
# Matplotlib for plotting
import matplotlib.pyplot as plt
#PyQt6 imports for GUI application and widgets
from PyQt6.QtWidgets import(QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QFileDialog)
# Backend to embed Matplotlib into PyQt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
#MNInteraction actually computes the MN Diagram
import MNInteraction #Import your saved file 

#Defining main application class for the GUI. It is inherited from the QWidget
class InteractionDiagramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rectangular Column Concrete Section Interaction Diagram")
        self.initUI()

    def initUI(self):
        #Main vertical layout to stack the widgets vertically
        layout = QVBoxLayout()

        #Grid Layout to organize form inputs in rows and columns
        form_layout = QGridLayout()
        self.inputs = {}        #Dictionary to store the input fields
        
        #Input labels and their corresponding keys for the user input
        labels = ['Width (in)', 'Height (in)', 'Effective Cover (in)', 'Top Rebar Area (in²)', 'Bottom Rebar Area (in²)', 'fc (ksi)', 'fy (ksi)']
        keys = ['w', 'h', 'ec', 'Ast', 'Asb', 'fc', 'fy']
        
        #placeholders to guide the users in the input boxes
        placeholders = ['e.g. 12', 'e.g. 24', 'e.g. 2.5', 'e.g. 4', 'e.g. 5', 'e.g. 4', 'e.g. 60']
        
        # Create and add label + input field pairs to form layout
        for i, (label, key, placeholders) in enumerate(zip(labels, keys, placeholders)):
            form_layout.addWidget(QLabel(label), i, 0)      # Add label to row i, column 0
            self.inputs[key] = QLineEdit()      # Create a text input field
            self.inputs[key].setPlaceholderText(placeholders)     # Set placeholder text like 'e.g. 12'
            form_layout.addWidget(self.inputs[key], i, 1)       # Add input field to row i, column 1
        layout.addLayout(form_layout)       #Add the grid layout to the main vertical layout

        # Layout for buttons (horizontal)
        button_layout = QHBoxLayout()

        #Button to trigger calculation
        self.calc_btn = QPushButton("Calculate Interaction Diagram")
        self.calc_btn.clicked.connect(self.run_calculation)     #Connect button click to function
        button_layout.addWidget(self.calc_btn)

        # Button to save plot as image
        self.save_btn = QPushButton("Save Plot")
        self.save_btn.clicked.connect(self.save_plot)       #Connect button click to function
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)     #Add button layout to main layout

        # Matplotlib figure canvas embedded in GUI
        self.canvas = FigureCanvas(plt.figure(figsize=(16, 7)))
        layout.addWidget(self.canvas)       #Add canvas to layout

        # Label to display text summary of the results
        self.result_label = QLabel("")
        layout.addWidget(self.result_label)     # Apply final layout to the main window

        self.setLayout(layout)

    def run_calculation(self):
        try:
            # Convert input text values to float
            w = float(self.inputs['w'].text())
            h = float(self.inputs['h'].text())
            ec = float(self.inputs['ec'].text())
            Ast = float(self.inputs['Ast'].text())
            Asb = float(self.inputs['Asb'].text())
            fc = float(self.inputs['fc'].text())
            fy = float(self.inputs['fy'].text())

            # Validation checks for user input values
            if any(x <= 0 for x in [w, h, ec, Ast, Asb, fc, fy]):
                raise ValueError("All input parameters must be positive.")
            if ec >= h / 2:
                raise ValueError("Effective cover must be less than half the section height.")
            Ag = w * h
            if Ast + Asb >= Ag:
                raise ValueError("Total reinforcement area must be less than gross section area.")
            if fc > 10:
                raise ValueError("Concrete strength (f'c) must not exceed 10 ksi per ACI 318-19.")
            if fy > 80:
                raise ValueError("Steel yield strength (fy) must not exceed 80 ksi per ACI 318-19.")
            
        # Show error message if input is invalid
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", str(e))    
            return      # Stop execution

        self.setWindowTitle(f"Rectangular Column - f'c = {fc} ksi, fy = {fy} ksi")

        # Calculate interaction diagram using function from MN.py
        Mrd, Nrd = MNInteraction.Interaction_Diagram(w, h, ec, Ast, Asb, fc, fy)

        # Clear existing plot
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)        # Add new subplot

        # Plot moment vs axial force points, with red circles and connecting line
        ax.plot(Mrd, Nrd, 'r-o', markersize=6, label="Key ACI Points")

        # Labels for each of the 7 standard ACI points
        labels = [
            "Max Compression (P₀)",
            "Bar Stress = 0 (εₛ=0)",
            "Bar Stress = 0.5fy",
            "Balanced Failure (fₛ=fy)",
            "Tension-Controlled (εₛ=0.00507)",
            "Pure Bending (Pₙ=0)",
            "Max Tension"
        ]

        # Annotate each point on the plot with its label and coordinates
        for i, (m, n) in enumerate(zip(Mrd, Nrd)):
            ax.text(m, n, f"{labels[i]}\n({m:.1f}, {n:.1f})", fontsize=8, ha='right')

        # Set axis labels and chart title
        ax.set_xlabel("Moment Resistance, ϕMₙ (kip-ft)")
        ax.set_ylabel("Axial Force Resistance, ϕPₙ (kip)")
        ax.set_title("Interaction Diagram - Tied Rectangular Column (ACI 318-19)")

        # Add grid for better readability
        ax.grid(True, linestyle='--', alpha=0.6)

        # Automatically adjust layout to fit all element
        self.canvas.figure.tight_layout()

        # Render the plot on canvas
        self.canvas.draw()

        # Display summary of key points
        result_text = "Key Points:\n"
        for i in range(len(Mrd)):
            result_text += f"{labels[i]}: M = {Mrd[i]:.1f} kip-ft, N = {Nrd[i]:.1f} kips\n"
        self.result_label.setText(result_text)

    def save_plot(self):
        options = QFileDialog.Options()

        # Open file dialog for user to choose save location and file type
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot As Image", "", "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf)", options=options)
        
        # If file path is selected, save the figure
        if file_path:
            self.canvas.figure.savefig(file_path)

# Entry point of the script
if __name__ == '__main__':
    app = QApplication(sys.argv)        # Create Qt application
    window = InteractionDiagramApp()   # Instantiate your main window     
    window.resize(800, 800)     # Optional window size setting   
    window.show()       # Display the window
    sys.exit(app.exec())        # Start the application event loop
