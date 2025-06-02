import sys
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QFileDialog, QTabWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
import MN

class InteractionDiagramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rectangular Column Concrete Section Interaction Diagram")
        self.initUI()
        self.resize(1200, 800)

    def initUI(self):
        self.canvas = FigureCanvas(plt.figure(figsize=(20, 10)))
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        self.tab_widget = QTabWidget()

        # Input Tab
        input_tab = QWidget()
        input_layout = QVBoxLayout()
        form_layout = QGridLayout()
        self.inputs = {}

        labels = [
            'Width (in)', 'Height (in)', 'Top Clear Cover (in)', 'Bottom Clear Cover (in)',
            'Tie Bar Size', 'Top Long Bar Size', 'Bottom Long Bar Size',
            'Number of Top Bars', 'Number of Bottom Bars', 'fc (ksi)', 'fy (ksi)'
        ]
        keys = ['w', 'h', 'Ctt', 'Cbt', 'Tie_size', 'Top_bar_size', 'Bottom_bar_size', 'Nt', 'Nb', 'fc', 'fy']
        placeholders = ['e.g. 12', 'e.g. 24', 'e.g. 1.5', 'e.g. 1.5', 'e.g. #3 or leave blank', 'e.g. #5', 'e.g. #6', 'e.g. 4', 'e.g. 4', 'e.g. 4', 'e.g. 60']

        for i, (label, key, placeholder) in enumerate(zip(labels, keys, placeholders)):
            form_layout.addWidget(QLabel(label), i, 0)
            self.inputs[key] = QLineEdit()
            self.inputs[key].setPlaceholderText(placeholder)
            form_layout.addWidget(self.inputs[key], i, 1)
        input_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.calc_btn = QPushButton("Calculate Interaction Diagram")
        self.calc_btn.clicked.connect(self.run_calculation)
        button_layout.addWidget(self.calc_btn)
        self.save_btn = QPushButton("Save Plot")
        self.save_btn.clicked.connect(self.save_plot)
        button_layout.addWidget(self.save_btn)
        input_layout.addLayout(button_layout)

        input_tab.setLayout(input_layout)
        self.tab_widget.addTab(input_tab, "Input")

        # Plots Tab
        plots_tab = QWidget()
        plots_layout = QVBoxLayout()
        plots_layout.addWidget(self.toolbar)
        plots_layout.addWidget(self.canvas)
        plots_tab.setLayout(plots_layout)
        self.tab_widget.addTab(plots_tab, "Plots")

        # Results Tab
        results_tab = QWidget()
        results_layout = QVBoxLayout()
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 16px; font-family: Arial;")
        results_layout.addWidget(self.result_label)
        results_tab.setLayout(results_layout)
        self.tab_widget.addTab(results_tab, "Results")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def on_scroll(self, event):
        if event.inaxes is None:
            return
        ax = event.inaxes
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        zoom_factor = 1.2
        if event.button == 'up':
            scale_factor = 1 / zoom_factor
        elif event.button == 'down':
            scale_factor = zoom_factor
        else:
            return
        relx = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        rely = (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
        current_xrange = cur_xlim[1] - cur_xlim[0]
        current_yrange = cur_ylim[1] - cur_ylim[0]
        new_xrange = current_xrange * scale_factor
        new_yrange = current_yrange * scale_factor
        new_left = xdata - relx * new_xrange
        new_right = xdata + (1 - relx) * new_xrange
        new_bottom = ydata - rely * new_yrange
        new_top = ydata + (1 - rely) * new_yrange
        ax.set_xlim(new_left, new_right)
        ax.set_ylim(new_bottom, new_top)
        self.canvas.draw()
    
    def run_calculation(self):
        try:
            # Input parsing
            w = float(self.inputs['w'].text())
            h = float(self.inputs['h'].text())
            Ctt = float(self.inputs['Ctt'].text())
            Cbt = float(self.inputs['Cbt'].text())
            Tie_size = self.inputs['Tie_size'].text().strip()
            if Tie_size == "":
                Tie_d = 0
            else:
                if Tie_size not in MN.BAR_PROPERTIES:
                    raise ValueError("Invalid tie bar size. Choose from " + ", ".join(MN.BAR_PROPERTIES.keys()) + " or leave blank.")
                Tie_d = MN.BAR_PROPERTIES[Tie_size]["diameter"]
            Top_bar_size = self.inputs['Top_bar_size'].text().strip()
            Bottom_bar_size = self.inputs['Bottom_bar_size'].text().strip()
            Nt = int(self.inputs['Nt'].text())
            Nb = int(self.inputs['Nb'].text())
            fc = float(self.inputs['fc'].text())
            fy = float(self.inputs['fy'].text())

            # Input validation
            if any(x <= 0 for x in [w, h, Ctt, Cbt, fc, fy]) or any(x < 0 for x in [Nt, Nb]):
                raise ValueError("All numerical inputs must be positive (or zero for number of bars).")
            if Ctt >= h / 2 or Cbt >= h / 2:
                raise ValueError("Clear covers must be less than half the section height.")
            if fc > 10:
                raise ValueError("Concrete strength (f'c) must not exceed 10 ksi per ACI 318-19.")
            if fy > 80:
                raise ValueError("Steel yield strength (fy) must not exceed 80 ksi per ACI 318-19.")
            if Nt > 0 and Top_bar_size not in MN.BAR_PROPERTIES:
                raise ValueError("Invalid top longitudinal bar size. Choose from " + ", ".join(MN.BAR_PROPERTIES.keys()))
            if Nb > 0 and Bottom_bar_size not in MN.BAR_PROPERTIES:
                raise ValueError("Invalid bottom longitudinal bar size. Choose from " + ", ".join(MN.BAR_PROPERTIES.keys()))

            # Run interaction diagram calculation
            Mrd_full, Nrd_full, Mn_full, Pn_full, key_indices = MN.Interaction_Diagram(w, h, Ctt, Cbt, Tie_d, Top_bar_size, Bottom_bar_size, Nt, Nb, fc, fy)

            # Clear previous figure
            self.canvas.figure.clear()
            fig = self.canvas.figure
            ax1 = fig.add_subplot(121)
            ax2 = fig.add_subplot(122)

            # Define correct labels in the order of key points
            ordered_labels = [
                "Max Compression",
                "Bar Stress = 0",
                "Bar Stress = 0.5fy",
                "Balanced Failure",
                "Tension-Controlled",
                "Pure Bending",
                "Max Tension"
            ]

            # Plot nominal interaction diagram (only key points)
            ax1.plot(Mn_full, Pn_full, 'bo-', label="Nominal Interaction Diagram")
            for i, (x, y) in enumerate(zip(Mn_full, Pn_full)):
                ax1.text(x, y, f"{ordered_labels[i]}\n(Pn={y:.1f}, Mn={x:.1f})",
                         fontsize=8, ha='left' if x < 0 else 'right', va='bottom' if y < 0 else 'top')
            ax1.set_xlabel("Moment, Mn (kip-ft)")
            ax1.set_ylabel("Axial Force, Pn (kip)")
            ax1.set_title("Nominal Interaction Diagram (7 Key Points)")
            ax1.grid(True, linestyle='--', alpha=0.6)
            ax1.legend()

            # Plot factored interaction diagram (only key points)
            ax2.plot(Mrd_full, Nrd_full, 'ro-', label="Factored Interaction Diagram")
            for i, (x, y) in enumerate(zip(Mrd_full, Nrd_full)):
                ax2.text(x, y, f"{ordered_labels[i]}\n(φPn={y:.1f}, φMn={x:.1f})",
                         fontsize=8, ha='left' if x < 0 else 'right', va='bottom' if y < 0 else 'top')
            ax2.set_xlabel("Moment, φMn (kip-ft)")
            ax2.set_ylabel("Axial Force, φPn (kip)")
            ax2.set_title("Factored Interaction Diagram (7 Key Points)")
            ax2.grid(True, linestyle='--', alpha=0.6)
            ax2.legend()

            # Adjust layout and draw
            fig.tight_layout()
            self.canvas.draw()

            # Update results tab
            result_text = "Key Points (Pn, Mn, φPn, φMn):\n"
            for i, (pn, mn, nrd, mrd) in enumerate(zip(Pn_full, Mn_full, Nrd_full, Mrd_full)):
                result_text += (f"{ordered_labels[i]}: "
                              f"Pn={pn:.1f} kips, Mn={mn:.1f} kip-ft, "
                              f"φPn={nrd:.1f} kips, φMn={mrd:.1f} kip-ft\n")
            self.result_label.setText(result_text)

        except ValueError as e:
            QMessageBox.critical(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot As Image", "",
                                                   "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf)",
                                                   options=options)
        if file_path:
            self.canvas.figure.savefig(file_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InteractionDiagramApp()
    window.show()
    sys.exit(app.exec())
