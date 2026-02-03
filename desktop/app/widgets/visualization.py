import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGridLayout, QFrame,
                             QScrollArea, QSplitter, QMessageBox, QApplication,
                             QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont
from scipy import stats
from collections import Counter
import os
import logging

matplotlib.use('Qt5Agg')

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared style constants  (eliminates duplicated stylesheet strings)
# ---------------------------------------------------------------------------
CARD_STYLESHEET = "QFrame { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }"

# IQR multiplier used for outlier detection
IQR_MULTIPLIER = 1.5

# Minimum fraction of rows a category value must represent to get its own
# slice in the donut chart; smaller values are collapsed into "Other".
DONUT_MIN_SLICE_FRACTION = 0.02

# Maximum number of named slices before "Other" bucketing kicks in.
DONUT_MAX_SLICES = 8


# ===========================================================================
# Background thread – fetches rows + quality metrics without blocking the UI
# ===========================================================================
class AnalyticsFetchThread(QThread):
    """Emits *loaded* with a dict containing rows, quality metrics, or an error string."""
    loaded = pyqtSignal(dict)

    def __init__(self, api_client, dataset_id, limit=500, offset=0, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.dataset_id = dataset_id
        self.limit = limit
        self.offset = offset

    def run(self):
        payload = {'rows': None, 'quality': None, 'error': None}
        try:
            rows_resp = self.api_client.get_dataset_rows(
                self.dataset_id, limit=self.limit, offset=self.offset
            )
            payload['rows'] = rows_resp
            try:
                payload['quality'] = self.api_client.get_quality_metrics(self.dataset_id)
            except Exception:
                payload['quality'] = None          # quality is best-effort
        except Exception as exc:
            payload['error'] = str(exc)
        self.loaded.emit(payload)


# ===========================================================================
# Matplotlib canvas – owns every chart type and export logic
# ===========================================================================
class MplCanvas(FigureCanvas):
    """A FigureCanvas that lives inside a Qt layout and exposes typed chart helpers."""

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.current_palette = 'viridis'
        # Default margins tuned for label visibility
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, wspace=0, hspace=0)
        self.axes.set_axis_off()
        self.fig.patch.set_facecolor('white')
        self.axes.patch.set_facecolor('white')

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def clear(self):
        """Reset axes to the blank, axis-off state."""
        self.axes.clear()
        self.axes.set_axis_off()
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, wspace=0, hspace=0)
        self.draw()

    def update_chart_style(self):
        """Apply the shared visual theme (spines, grid, ticks, labels) to the current axes."""
        self.axes.set_facecolor('white')
        self.fig.patch.set_facecolor('white')

        for spine in self.axes.spines.values():
            spine.set_color('#e5e7eb')
            spine.set_linewidth(1)
            spine.set_visible(True)

        self.axes.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color='#9ca3af')
        self.axes.tick_params(colors='#374151', labelsize=10, which='both',
                              length=4, width=1, direction='out')

        if self.axes.get_title():
            self.axes.set_title(self.axes.get_title(), fontsize=14, fontweight='600',
                                color='#1f2937', pad=15)
        if self.axes.get_xlabel():
            self.axes.set_xlabel(self.axes.get_xlabel(), fontsize=11,
                                 color='#374151', fontweight='500')
        if self.axes.get_ylabel():
            self.axes.set_ylabel(self.axes.get_ylabel(), fontsize=11,
                                 color='#374151', fontweight='500')

        self.fig.tight_layout(pad=1.5)

    # ------------------------------------------------------------------
    # Export  (savefig infers format from the extension automatically)
    # ------------------------------------------------------------------
    def export_chart(self, filename):
        """Save the current figure to *filename*. Supported: .png, .pdf, .svg."""
        supported = ('.png', '.pdf', '.svg')
        if not filename.endswith(supported):
            raise ValueError(f"Unsupported file format. Use one of {supported}")
        dpi = 300 if filename.endswith('.png') else None          # high-res for raster only
        self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')

    # ------------------------------------------------------------------
    # Shared axes setup
    # ------------------------------------------------------------------
    def _prepare_axes(self, title="", xlabel="", ylabel=""):
        """Turn axes on and stamp title / labels before styling."""
        self.axes.set_axis_on()
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.update_chart_style()

    # ------------------------------------------------------------------
    # Chart types
    # ------------------------------------------------------------------
    def line_chart(self, x_data, y_data, title="", xlabel="", ylabel=""):
        """Render a styled line chart."""
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        self.axes.plot(x_data, y_data, color='#3b82f6', linewidth=2,
                       marker='o', markersize=4, alpha=0.8)
        self.fig.tight_layout(pad=1.5)
        self.draw()

    def bar_chart(self, labels, values, title="", xlabel="", ylabel=""):
        """Render a bar chart with value labels on top of each bar."""
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        bars = self.axes.bar(labels, values, color='#3b82f6', alpha=0.9, edgecolor='#2563eb')
        self.axes.tick_params(axis='x', rotation=45, labelsize=9)

        for bar in bars:
            height = bar.get_height()
            self.axes.text(bar.get_x() + bar.get_width() / 2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=9, color='#374151')

        self.fig.tight_layout(pad=1.5)
        self.draw()

    def scatter_plot(self, x_data, y_data, title="", xlabel="", ylabel=""):
        """Render a scatter plot."""
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        self.axes.scatter(x_data, y_data, s=50, alpha=0.6, color='#3b82f6',
                          edgecolors='#1e40af', linewidths=1)
        self.fig.tight_layout(pad=1.5)
        self.draw()

    def histogram(self, data, title="", xlabel=""):
        """Render a histogram with per-bin count labels."""
        self.axes.clear()
        self._prepare_axes(title, xlabel, "Frequency")
        _n, _bins, patches = self.axes.hist(
            data, bins=20, color='#3b82f6', alpha=0.7,
            edgecolor='#1e40af', linewidth=1.2
        )

        for patch in patches:
            height = patch.get_height()
            if height > 0:
                self.axes.text(patch.get_x() + patch.get_width() / 2., height,
                               f'{int(height)}',
                               ha='center', va='bottom', fontsize=8, color='#374151')

        self.fig.tight_layout(pad=1.5)
        self.draw()

    def box_plot(self, data, title="", ylabel=""):
        """Render a box plot with a summary-stats annotation."""
        self.axes.clear()
        self._prepare_axes(title, "", ylabel)

        self.axes.boxplot(
            data, vert=True, patch_artist=True,
            boxprops=dict(facecolor='#3b82f6', alpha=0.5, edgecolor='#2563eb', linewidth=1.5),
            medianprops=dict(color='#1f2937', linewidth=2),
            whiskerprops=dict(color='#6b7280', linewidth=1.5),
            capprops=dict(color='#6b7280', linewidth=1.5),
            flierprops=dict(marker='o', markerfacecolor='#ef4444', markersize=6,
                            markeredgecolor='#dc2626', alpha=0.6),
        )

        # Annotation box – positioned at 115 % of axes width so it clears the plot
        stats_text = f"Median: {np.median(data):.2f}\nMean: {np.mean(data):.2f}"
        self.axes.text(1.15, 0.5, stats_text, transform=self.axes.transAxes,
                       fontsize=10, verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor='#f3f4f6', alpha=0.8, edgecolor='#e5e7eb'))

        self.fig.tight_layout(pad=1.5)
        self.draw()

    def heatmap(self, matrix, labels, title=""):
        """Render a correlation heatmap with cell-value annotations."""
        self.axes.clear()
        self.axes.set_axis_on()

        # Validate inputs
        if matrix is None or len(matrix) == 0:
            self.axes.text(0.5, 0.5, 'No data to display',
                           ha='center', va='center', fontsize=12, color='#6b7280')
            self.axes.set_title(title, fontsize=14, fontweight='600', color='#1f2937', pad=15)
            self.draw()
            return

        if len(labels) != len(matrix):
            logger.warning(f"Labels count ({len(labels)}) doesn't match matrix size ({len(matrix)})")
            # Adjust labels to match matrix size
            if len(labels) > len(matrix):
                labels = labels[:len(matrix)]
            else:
                labels = labels + [f"Col{i}" for i in range(len(matrix) - len(labels))]

        try:
            im = self.axes.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')

            self.axes.set_xticks(range(len(labels)))
            self.axes.set_yticks(range(len(labels)))
            self.axes.set_xticklabels(labels, rotation=45, ha='right', fontsize=9, color='#374151')
            self.axes.set_yticklabels(labels, fontsize=9, color='#374151')

            for row_idx in range(len(labels)):
                for col_idx in range(len(labels)):
                    cell_value = matrix[row_idx][col_idx]
                    text_color = "white" if abs(cell_value) > 0.5 else "black"
                    self.axes.text(col_idx, row_idx, f'{cell_value:.2f}',
                                   ha="center", va="center", color=text_color,
                                   fontsize=8, fontweight='600')

            self.axes.set_title(title, fontsize=14, fontweight='600', color='#1f2937', pad=15)

            # Colorbar: fraction=0.046 / pad=0.04 keep it narrow and close to the axes
            cbar = self.fig.colorbar(im, ax=self.axes, fraction=0.046, pad=0.04)
            cbar.ax.tick_params(labelsize=9, colors='#374151')

            self.fig.tight_layout(pad=1.5)
            self.draw()
            
        except Exception as e:
            logger.error(f"Error rendering heatmap: {e}")
            self.axes.clear()
            self.axes.text(0.5, 0.5, f'Error rendering heatmap:\n{str(e)}',
                           ha='center', va='center', fontsize=10, color='#dc2626')
            self.axes.set_title(title, fontsize=14, fontweight='600', color='#1f2937', pad=15)
            self.draw()

    def donut_chart(self, labels, values, title=""):
        """Render a donut chart from pre-aggregated categorical labels and counts."""
        self.axes.clear()
        self.axes.set_axis_on()

        # Filter out zero-count slices
        non_zero_mask = np.array(values) > 0
        if not any(non_zero_mask):
            self.axes.text(0.5, 0.5, 'No data to display',
                           ha='center', va='center', fontsize=12, color='#6b7280')
            self.axes.set_title(title, fontsize=14, fontweight='600', color='#1f2937', pad=15)
            self.draw()
            return

        labels  = [labels[i]  for i in range(len(labels))  if non_zero_mask[i]]
        values  = [values[i]  for i in range(len(values))  if non_zero_mask[i]]

        # Colour palette with graceful fallback
        try:
            cmap = plt.cm.get_cmap(self.current_palette)
        except (ValueError, KeyError):
            cmap = plt.cm.get_cmap('viridis')
        colors = cmap(np.linspace(0.2, 0.9, len(values)))

        total = sum(values)
        percentages = [v / total * 100 for v in values]

        def _autopct(pct):
            """Only label slices > 5 % to avoid clutter."""
            return f'{pct:.1f}%' if pct > 5 else ''

        wedges, _texts, _autotexts = self.axes.pie(
            values,
            labels=None,
            autopct=_autopct,
            startangle=90,
            colors=colors,
            textprops={'fontsize': 9, 'color': 'white', 'fontweight': '700'},
            pctdistance=0.85,   # distance of percentage labels from centre
        )

        # Punch the donut hole  (radius 0.70 gives a comfortable ring width)
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        self.axes.add_artist(centre_circle)

        # Legend with absolute counts and percentages
        legend_labels = [
            f'{labels[i]} ({int(values[i])} – {percentages[i]:.1f}%)'
            for i in range(len(labels))
        ]
        self.axes.legend(wedges, legend_labels,
                         loc='center left',
                         bbox_to_anchor=(1.0, 0.5),
                         fontsize=9, frameon=True, fancybox=True, shadow=False,
                         title='Distribution')

        self.axes.set_title(title, fontsize=14, fontweight='600', color='#1f2937', pad=15)
        self.axes.axis('equal')
        self.fig.tight_layout(pad=1.5)
        self.draw()


# ===========================================================================
# Main widget – UI, data loading, chart orchestration, report generation
# ===========================================================================
class VisualizationWidget(QWidget):
    """Top-level widget that hosts the chart canvas, control panel, and analytics sidebar."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client       = api_client
        self.current_dataset  = None
        self.current_palette  = 'viridis'
        self.analytics_thread = None
        self._analytics_rows  = []
        self.init_ui()
        self.apply_modern_styling()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.controls_panel = self._create_controls_panel()
        main_layout.addWidget(self.controls_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        splitter.addWidget(self.canvas)

        self.analytics_panel = self._create_analytics_panel()
        splitter.addWidget(self.analytics_panel)

        splitter.setStretchFactor(0, 1)   # canvas – fills remaining space
        splitter.setStretchFactor(1, 0)   # analytics sidebar – fixed width
        splitter.setSizes([800, 400])

        main_layout.addWidget(splitter)
        self.canvas.current_palette = self.current_palette

    # ------------------------------------------------------------------
    # Controls panel  (chart-type, axis selectors, action buttons)
    # ------------------------------------------------------------------
    def _make_labeled_combo(self, label_text, min_width=None):
        """Factory: returns (QVBoxLayout, QComboBox) for a labelled dropdown."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 11px; font-weight: 600; color: #6b7280;")
        layout.addWidget(label)

        combo = QComboBox()
        if min_width:
            combo.setMinimumWidth(min_width)
        layout.addWidget(combo)
        return layout, combo

    def _create_controls_panel(self):
        panel = QFrame()
        panel.setFixedHeight(120)
        panel.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e5e7eb; border-radius: 12px; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Chart-type selector
        chart_type_layout, self.viz_type_combo = self._make_labeled_combo("Chart Type")
        for display_name, key in [("Line Chart", "line"), ("Bar Chart", "bar"),
                                  ("Scatter Plot", "scatter"), ("Histogram", "hist"),
                                  ("Box Plot", "box"), ("Heatmap", "heatmap"),
                                  ("Donut Chart", "donut")]:
            self.viz_type_combo.addItem(display_name, key)
        self.viz_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        controls_layout.addLayout(chart_type_layout)

        # X-axis selector
        x_axis_layout, self.x_axis_combo = self._make_labeled_combo("X-Axis", min_width=120)
        controls_layout.addLayout(x_axis_layout)

        # Y-axis selector
        y_axis_layout, self.y_axis_combo = self._make_labeled_combo("Y-Axis", min_width=120)
        controls_layout.addLayout(y_axis_layout)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.update_btn  = QPushButton("Update")
        self.clear_btn   = QPushButton("Clear")
        self.export_btn  = QPushButton("Export")
        self.report_btn  = QPushButton("Generate Report")

        self.update_btn.clicked.connect(self.update_chart)
        self.clear_btn.clicked.connect(self.clear_chart)
        self.export_btn.clicked.connect(self.export_chart)
        self.report_btn.clicked.connect(self.generate_report)

        for btn in (self.update_btn, self.clear_btn, self.export_btn, self.report_btn):
            button_layout.addWidget(btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.set_controls_enabled(False)
        return panel

    # ------------------------------------------------------------------
    # Analytics sidebar
    # ------------------------------------------------------------------
    def _create_analytics_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(360)
        scroll.setMaximumWidth(480)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #f8fafc; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        def _section(title, subtitle):
            """Helper: creates a titled, bordered section frame + its inner layout."""
            frame = QFrame()
            frame.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }")
            inner = QVBoxLayout(frame)
            inner.setContentsMargins(10, 10, 10, 10)
            inner.setSpacing(6)

            header_row = QHBoxLayout()
            header_row.setSpacing(4)

            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #1f2937;")
            header_row.addWidget(title_label)
            header_row.addStretch()

            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 9px; color: #6b7280;")
            header_row.addWidget(subtitle_label)

            inner.addLayout(header_row)
            return frame, inner

        # Summary section
        self.summary_frame, summary_layout = _section("Summary Stats", "Key numeric metrics")
        self.summary_grid = QGridLayout()
        self.summary_grid.setContentsMargins(0, 0, 0, 0)
        self.summary_grid.setHorizontalSpacing(6)
        self.summary_grid.setVerticalSpacing(6)
        summary_layout.addLayout(self.summary_grid)

        # Insights section
        self.insights_frame, insights_layout = _section("Insights", "Auto-generated observations")
        self.insights_label = QLabel("Select a dataset to see insights")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("font-size: 11px; color: #374151;")
        insights_layout.addWidget(self.insights_label)

        # Outliers section
        self.outliers_frame, outliers_layout = _section("Outliers by Metric", "IQR rule per numeric column")
        self.outliers_grid = QGridLayout()
        self.outliers_grid.setContentsMargins(0, 0, 0, 0)
        self.outliers_grid.setHorizontalSpacing(6)
        self.outliers_grid.setVerticalSpacing(6)
        outliers_layout.addLayout(self.outliers_grid)

        layout.addWidget(self.summary_frame)
        layout.addWidget(self.insights_frame)
        layout.addWidget(self.outliers_frame)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # ------------------------------------------------------------------
    # Global stylesheet
    # ------------------------------------------------------------------
    def apply_modern_styling(self):
        self.setStyleSheet("""
            QWidget            { font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                                 font-size: 12px; color: #1f2937; background-color: #ffffff; }
            QComboBox          { background-color: #ffffff; border: 2px solid #e5e7eb; border-radius: 8px;
                                 padding: 6px 12px; font-size: 12px; min-height: 20px; }
            QComboBox:hover    { border-color: #d1d5db; }
            QComboBox:focus    { border-color: #3b82f6; outline: none; }
            QComboBox::drop-down  { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent;
                                    border-right: 4px solid transparent;
                                    border-top: 4px solid #6b7280; margin-right: 4px; }
            QPushButton        { background-color: #3b82f6; color: white; border: none; border-radius: 8px;
                                 padding: 6px 12px; font-size: 11px; font-weight: 600; min-height: 22px; }
            QPushButton:hover  { background-color: #2563eb; }
            QPushButton:pressed{ background-color: #1d4ed8; }
            QPushButton:disabled{ background-color: #e5e7eb; color: #9ca3af; }
            QLabel             { color: #1f2937; }
            QFrame             { background-color: #ffffff; border-color: #e5e7eb; }
        """)

    # ==================================================================
    # Chart-type change handler
    # ==================================================================
    def on_chart_type_changed(self, _text):
        """Enable/disable axis selectors and repopulate them based on the chosen chart type."""
        chart_key = self.viz_type_combo.currentData()

        if chart_key == "donut":
            # Donut needs only a single categorical column selector
            self.x_axis_combo.setEnabled(False)
            categorical_cols = self._get_categorical_columns()
            self.y_axis_combo.clear()
            self.y_axis_combo.addItems(categorical_cols if categorical_cols else ["(no categorical columns)"])
            self.y_axis_combo.setEnabled(bool(categorical_cols))

        elif chart_key in ("hist", "box"):
            self.x_axis_combo.setEnabled(False)
            self._repopulate_numeric_combos()
            self.y_axis_combo.setEnabled(True)

        elif chart_key == "heatmap":
            self.x_axis_combo.setEnabled(False)
            self.y_axis_combo.setEnabled(False)

        else:                                  # line, bar, scatter
            self._repopulate_numeric_combos()
            self.x_axis_combo.setEnabled(True)
            self.y_axis_combo.setEnabled(True)

    # ==================================================================
    # Dataset loading
    # ==================================================================
    def load_dataset(self, dataset):
        """Validate *dataset*, resolve numeric columns, and kick off the analytics thread."""
        self.current_dataset = dataset
        try:
            if not isinstance(self.current_dataset, dict):
                raise ValueError("Invalid dataset")

            # Ensure summary_json is present; fetch from health endpoint if missing
            summary = self.current_dataset.get("summary_json")
            dataset_id = self.current_dataset.get("id")
            if not isinstance(summary, dict) and dataset_id and self.api_client is not None:
                health  = self.api_client.get_dataset_health(dataset_id)
                summary = health.get("summary_json") or health.get("summary") or {}
                if isinstance(summary, dict):
                    self.current_dataset["summary_json"] = summary

            summary = self.current_dataset.get("summary_json") or {}
            numeric_cols = summary.get("numeric_columns")
            if not numeric_cols:
                averages = summary.get("averages") or {}
                if isinstance(averages, dict):
                    numeric_cols = list(averages.keys())
            if not numeric_cols:
                raise ValueError("No numeric columns available")

            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            self.x_axis_combo.addItems(numeric_cols)
            self.y_axis_combo.addItems(numeric_cols)
            self.set_controls_enabled(True)

            self._start_analytics()          # chart auto-updates once data arrives

        except Exception as exc:
            self.set_controls_enabled(False)
            QMessageBox.critical(self, "No Data", f"Dataset not loaded: {exc}")

    # ==================================================================
    # Controls state
    # ==================================================================
    def set_controls_enabled(self, enabled: bool):
        """Bulk-enable or bulk-disable every interactive control."""
        for widget in (self.viz_type_combo, self.x_axis_combo, self.y_axis_combo,
                       self.update_btn, self.clear_btn, self.export_btn, self.report_btn):
            widget.setEnabled(enabled)
        if hasattr(self, 'canvas'):
            self.canvas.current_palette = self.current_palette

    # ==================================================================
    # Analytics thread lifecycle
    # ==================================================================
    def _start_analytics(self):
        """Launch (or restart) the background fetch thread."""
        dataset_id = self.current_dataset.get('id') if isinstance(self.current_dataset, dict) else None
        if not dataset_id or self.api_client is None:
            self._render_analytics_error('No dataset id or API client')
            return

        self._render_analytics_loading()

        # Wait for any previous thread to finish gracefully instead of terminating
        if self.analytics_thread is not None and self.analytics_thread.isRunning():
            logger.debug("Previous analytics thread still running – waiting for it to finish.")
            self.analytics_thread.wait(timeout=2000)   # 2 s grace period

        self.analytics_thread = AnalyticsFetchThread(
            self.api_client, dataset_id, limit=500, offset=0, parent=self
        )
        self.analytics_thread.loaded.connect(self._on_analytics_loaded)
        self.analytics_thread.start()

    # ==================================================================
    # Analytics panel rendering helpers
    # ==================================================================
    def _render_analytics_loading(self):
        """Show a 'loading' placeholder in the insights area."""
        self.insights_label.setText('Loading analytics...')
        self.insights_label.setTextFormat(Qt.PlainText)
        self.insights_label.setStyleSheet("font-size: 11px; color: #374151; padding: 4px;")
        self._clear_grid(self.summary_grid)
        self._clear_grid(self.outliers_grid)

    def _render_analytics_error(self, message):
        """Show an error message in the insights area."""
        self.insights_label.setText(f'Analytics unavailable: {message}')
        self.insights_label.setTextFormat(Qt.PlainText)
        self.insights_label.setStyleSheet("font-size: 11px; color: #dc2626; padding: 4px;")
        self._clear_grid(self.summary_grid)
        self._clear_grid(self.outliers_grid)

    @staticmethod
    def _clear_grid(grid):
        """Remove every widget from a QGridLayout."""
        while grid.count():
            item   = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    # ==================================================================
    # Low-level data helpers
    # ==================================================================
    @staticmethod
    def _to_float(value):
        """Safely coerce *value* to float; returns None on failure or non-finite result."""
        if isinstance(value, (int, float)):
            return float(value) if np.isfinite(value) else None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in ('nan', 'null', 'none', ''):
                return None
            try:
                number = float(stripped)
                return number if np.isfinite(number) else None
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def _quartiles(values):
        """Return min / Q1 / Q2 / Q3 / max for a list of numeric values."""
        clean = [x for x in values if isinstance(x, (int, float)) and np.isfinite(x)]
        if not clean:
            return {'min': 0.0, 'q1': 0.0, 'q2': 0.0, 'q3': 0.0, 'max': 0.0}
        arr = np.array(sorted(clean), dtype=float)
        return {
            'min': float(arr[0]),
            'q1':  float(np.percentile(arr, 25, method='linear')),
            'q2':  float(np.percentile(arr, 50, method='linear')),
            'q3':  float(np.percentile(arr, 75, method='linear')),
            'max': float(arr[-1]),
        }

    def _get_categorical_columns(self):
        """Inspect loaded rows and return column names whose values are mostly non-numeric.

        A column is considered categorical when more than 50 % of its non-empty
        values cannot be parsed as a float.
        """
        if not self._analytics_rows:
            return []

        categorical_cols = []
        for key in self._analytics_rows[0].keys():
            non_numeric_count = sum(
                1 for row in self._analytics_rows
                if self._to_float(row.get(key)) is None
                and row.get(key) not in (None, "", "nan", "null", "NaN")
            )
            if non_numeric_count > len(self._analytics_rows) * 0.5:
                categorical_cols.append(key)
        return categorical_cols

    def _repopulate_numeric_combos(self):
        """Re-fill X / Y combo boxes with numeric columns (e.g. after leaving donut mode)."""
        summary      = (self.current_dataset or {}).get("summary_json") or {}
        numeric_cols = summary.get("numeric_columns") or list((summary.get("averages") or {}).keys())

        prev_x = self.x_axis_combo.currentText()
        prev_y = self.y_axis_combo.currentText()

        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        self.x_axis_combo.addItems(numeric_cols)
        self.y_axis_combo.addItems(numeric_cols)

        # Restore previous selection when possible
        if prev_x in numeric_cols:
            self.x_axis_combo.setCurrentText(prev_x)
        if prev_y in numeric_cols:
            self.y_axis_combo.setCurrentText(prev_y)

    # ==================================================================
    # Analytics slot – processes the thread payload
    # ==================================================================
    def _on_analytics_loaded(self, payload):
        """Slot called when AnalyticsFetchThread finishes.  Computes stats, renders panels, and triggers the first chart."""
        error = payload.get('error')
        if error:
            self._render_analytics_error(error)
            return

        rows_resp            = payload.get('rows') or {}
        self._analytics_rows = rows_resp.get('rows') or []

        summary      = (self.current_dataset or {}).get('summary_json') or {}
        numeric_cols = summary.get('numeric_columns') or []

        # If summary didn't list numeric cols, sniff them from the first row
        if not numeric_cols and self._analytics_rows:
            id_like_keys = {'Record', 'record', 'id', 'ID', 'index', 'Index'}
            for key in self._analytics_rows[0].keys():
                if key in id_like_keys:
                    continue
                if any(self._to_float(row.get(key)) is not None for row in self._analytics_rows):
                    numeric_cols.append(key)

        # --- compute everything once and reuse across render calls ---
        stats_map        = self._compute_stats(self._analytics_rows, numeric_cols, payload.get('quality'))
        corr_data        = self._compute_corr(self._analytics_rows, numeric_cols)
        outliers_by_col  = self._compute_outliers(self._analytics_rows, numeric_cols)
        insights         = self._build_insights(self._analytics_rows, numeric_cols, stats_map, corr_data, outliers_by_col)

        self._render_summary(stats_map)
        self._render_outliers(outliers_by_col)
        self._render_insights(insights)

        # Auto-update chart now that real data is available
        self.update_chart()

    # ==================================================================
    # Insights rendering (extracted from the old _on_analytics_loaded)
    # ==================================================================
    def _render_insights(self, insights):
        """Populate the insights label with an HTML bullet list, or a 'none' message."""
        if insights:
            items_html = ''.join(
                f'<li style="margin-bottom:4px;color:#111827;font-size:11px;font-weight:500;">'
                f'{self._escape_html(text)}</li>'
                for text in insights
            )
            html = (
                '<div style="padding:4px;">'
                '<ul style="margin:0;padding-left:18px;line-height:1.8;">'
                f'{items_html}</ul></div>'
            )
            self.insights_label.setTextFormat(Qt.RichText)
            self.insights_label.setText(html)
            self.insights_label.setStyleSheet("font-size: 11px; color: #111827;")
        else:
            self.insights_label.setTextFormat(Qt.PlainText)
            self.insights_label.setText('No significant insights detected.')
            self.insights_label.setStyleSheet("font-size: 11px; color: #6b7280; padding: 4px;")

    # ==================================================================
    # Statistics computation
    # ==================================================================
    def _compute_stats(self, rows, numeric_cols, quality_payload=None):
        """Return {col: {mean, median, min, max, std, n, missing, total}} for every numeric column."""
        # Pull per-column missing counts from quality endpoint when available
        missing_map = None
        if isinstance(quality_payload, dict):
            quality_metrics = quality_payload.get('quality_metrics')
            if isinstance(quality_metrics, dict):
                missing_map = quality_metrics.get('missing_values')

        total = len(rows) if rows else 0
        result = {}

        for col in numeric_cols:
            col_values = [v for v in (self._to_float(row.get(col)) for row in rows) if v is not None]
            quartile_data = self._quartiles(col_values)
            mean_value  = float(np.mean(col_values))            if col_values        else 0.0
            std_value   = float(np.std(col_values, ddof=1))     if len(col_values) > 1 else 0.0
            missing     = max(0, total - len(col_values))

            # Quality-endpoint value takes precedence when present
            if isinstance(missing_map, dict) and isinstance(missing_map.get(col), int):
                missing = missing_map[col]

            result[col] = {
                'mean':    mean_value,
                'median':  quartile_data['q2'],
                'min':     quartile_data['min'],
                'max':     quartile_data['max'],
                'std':     std_value,
                'n':       max(0, total - missing) if total else len(col_values),
                'missing': missing,
                'total':   total,
            }
        return result

    def _compute_corr(self, rows, numeric_cols):
        """Build a correlation matrix (numpy) for the given numeric columns.

        Returns ``{'order': [...], 'matrix': [[...]]}``; matrix is empty when
        fewer than two complete rows are available.
        """
        if not rows or len(numeric_cols) < 2:
            return {'order': numeric_cols, 'matrix': []}

        # Keep only rows where every numeric column has a value
        clean_rows = []
        for row in rows:
            row_values = []
            all_present = True
            for col in numeric_cols:
                value = self._to_float(row.get(col))
                if value is None:
                    all_present = False
                    break
                row_values.append(value)
            if all_present:
                clean_rows.append(row_values)

        if len(clean_rows) < 2:
            return {'order': numeric_cols, 'matrix': []}

        arr  = np.array(clean_rows, dtype=float)
        corr = np.corrcoef(arr, rowvar=False)
        return {'order': numeric_cols, 'matrix': corr.tolist()}

    def _compute_outliers(self, rows, numeric_cols):
        """Detect outliers per column using the IQR method (factor = IQR_MULTIPLIER)."""
        result = {}
        for col in numeric_cols:
            col_values = [v for v in (self._to_float(row.get(col)) for row in rows) if v is not None]

            if len(col_values) < 4:          # not enough data to compute quartiles reliably
                result[col] = {'lb': 0.0, 'ub': 0.0, 'values': [], 'count': 0}
                continue

            quartile_data = self._quartiles(col_values)
            iqr           = quartile_data['q3'] - quartile_data['q1']
            lower_bound   = quartile_data['q1'] - IQR_MULTIPLIER * iqr
            upper_bound   = quartile_data['q3'] + IQR_MULTIPLIER * iqr

            outlier_values = sorted(
                (v for v in col_values if v < lower_bound or v > upper_bound),
                key=lambda v: max(abs(v - lower_bound), abs(v - upper_bound)),
                reverse=True,
            )

            result[col] = {
                'lb':     lower_bound,
                'ub':     upper_bound,
                'values': outlier_values[:8],   # keep at most 8 for display
                'count':  len(outlier_values),
            }
        return result

    # ==================================================================
    # Insight generation
    # ==================================================================
    def _build_insights(self, rows, numeric_cols, stats_map, corr_data, outliers_by_col):
        """Return a list of human-readable insight strings derived from the computed analytics."""
        items = []
        if not numeric_cols:
            return items

        # --- variability & magnitude ---
        cols_in_map = [col for col in numeric_cols if col in stats_map]
        if cols_in_map:
            most_variable = max(cols_in_map, key=lambda col: stats_map[col].get('std') or 0.0)
            largest_mean  = max(cols_in_map, key=lambda col: stats_map[col].get('mean') or 0.0)

            if (stats_map[most_variable].get('std') or 0.0) > 0:
                items.append(f"Highest variability: {most_variable} (std = {stats_map[most_variable]['std']:.2f})")
            if (stats_map[largest_mean].get('mean') or 0.0) != 0:
                items.append(f"Largest mean value: {largest_mean} (mean = {stats_map[largest_mean]['mean']:.2f})")

            # Coefficient of variation (skip columns with near-zero mean)
            cv_eligible = [col for col in cols_in_map if abs(stats_map[col].get('mean') or 0.0) > 1e-9]
            if cv_eligible:
                cv_map = {
                    col: abs((stats_map[col].get('std') or 0.0) / (stats_map[col].get('mean') or 1.0))
                    for col in cv_eligible
                }
                most_volatile = max(cv_eligible, key=lambda col: cv_map[col])
                most_stable   = min(cv_eligible, key=lambda col: cv_map[col])
                items.append(f"Most volatile by CV: {most_volatile} (CV = {cv_map[most_volatile]:.2f})")
                items.append(f"Most stable by CV: {most_stable} (CV = {cv_map[most_stable]:.2f})")

        # --- skewness ---
        skew_map = {}
        for col in numeric_cols:
            col_values = [v for v in (self._to_float(row.get(col)) for row in rows) if v is not None]
            if len(col_values) >= 3:
                try:
                    skew_map[col] = float(stats.skew(col_values, bias=False))
                except Exception:
                    skew_map[col] = 0.0
        if skew_map:
            most_skewed = max(skew_map, key=lambda col: abs(skew_map[col]))
            if abs(skew_map[most_skewed]) > 0.5:
                items.append(f"Most skewed: {most_skewed} (skew = {skew_map[most_skewed]:.2f})")

        # --- correlations ---
        if corr_data.get('matrix') and corr_data.get('order') and len(corr_data['order']) > 1:
            order  = corr_data['order']
            matrix = corr_data['matrix']

            best_pos = (0, 1, float(matrix[0][1]))
            best_neg = (0, 1, float(matrix[0][1]))

            for i in range(len(order)):
                for j in range(i + 1, len(order)):
                    r_value = float(matrix[i][j])
                    if r_value > best_pos[2]:
                        best_pos = (i, j, r_value)
                    if r_value < best_neg[2]:
                        best_neg = (i, j, r_value)

            if best_pos[2] > 0:
                items.append(f"Top positive correlation: {order[best_pos[0]]} vs {order[best_pos[1]]} (r={best_pos[2]:.2f})")
            if best_neg[2] < 0:
                items.append(f"Top negative correlation: {order[best_neg[0]]} vs {order[best_neg[1]]} (r={best_neg[2]:.2f})")

        # --- outlier summary ---
        top_outlier_col = None
        for col, meta in outliers_by_col.items():
            count = int(meta.get('count') or 0)
            if top_outlier_col is None or count > top_outlier_col[1]:
                top_outlier_col = (col, count)
        if top_outlier_col and top_outlier_col[1] > 0:
            pct = (top_outlier_col[1] / max(1, len(rows))) * 100
            items.append(f"Outlier-heavy: {top_outlier_col[0]} ({top_outlier_col[1]} points, {pct:.1f}% of rows)")

        return items

    # ==================================================================
    # Card / widget builders for the analytics sidebar
    # ==================================================================
    @staticmethod
    def _escape_html(text):
        """Escape HTML special characters to prevent injection in RichText labels."""
        return (str(text)
                .replace('&',  '&amp;')
                .replace('<',  '&lt;')
                .replace('>',  '&gt;')
                .replace('"',  '&quot;')
                .replace("'",  '&#039;'))

    def _stat_card(self, col_name, stat_dict):
        """Build a small card widget showing summary stats for one column."""
        card = QFrame()
        card.setStyleSheet(CARD_STYLESHEET)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(4)

        # Column-name header
        name_label = QLabel(col_name)
        name_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #1f2937;")
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)

        # 3x2 grid of metric cells
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        grid.setContentsMargins(0, 2, 0, 0)
        card_layout.addLayout(grid)

        def _add_cell(row, col, label_text, value_text):
            """Insert a tiny label + value pair into the grid."""
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(1)

            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 9px; color: #6b7280;")
            val = QLabel(value_text)
            val.setStyleSheet("font-size: 11px; font-weight: 700; color: #111827;")

            cell_layout.addWidget(lbl)
            cell_layout.addWidget(val)
            grid.addWidget(cell_widget, row, col)

        _add_cell(0, 0, 'Mean',   f"{stat_dict['mean']:.2f}")
        _add_cell(0, 1, 'Median', f"{stat_dict['median']:.2f}")
        _add_cell(1, 0, 'Min',    f"{stat_dict['min']:.2f}")
        _add_cell(1, 1, 'Max',    f"{stat_dict['max']:.2f}")
        _add_cell(2, 0, 'Std',    f"{stat_dict['std']:.2f}")
        _add_cell(2, 1, 'N',      f"{int(stat_dict['n'])}")

        if stat_dict['missing'] > 0:
            missing_label = QLabel(f"Missing: {int(stat_dict['missing'])}")
            missing_label.setStyleSheet("font-size: 9px; color: #6b7280; margin-top: 2px;")
            card_layout.addWidget(missing_label)

        return card

    def _render_summary(self, stats_map):
        """Populate the summary grid with up to 6 stat cards."""
        self._clear_grid(self.summary_grid)
        for idx, col_name in enumerate(list(stats_map.keys())[:6]):
            card = self._stat_card(col_name, stats_map[col_name])
            self.summary_grid.addWidget(card, idx // 2, idx % 2)

    def _outlier_card(self, col_name, meta):
        """Build a card that shows the IQR bounds and a count badge for one column."""
        card = QFrame()
        card.setStyleSheet(CARD_STYLESHEET)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(4)

        # Header row: name + badge
        header_row = QHBoxLayout()
        header_row.setSpacing(4)

        name_label = QLabel(col_name)
        name_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #111827;")
        name_label.setWordWrap(True)
        header_row.addWidget(name_label)
        header_row.addStretch()

        count = int(meta.get('count') or 0)
        badge_text = f"{count} outlier{'s' if count != 1 else ''}"
        badge = QLabel(badge_text)
        if count > 0:
            badge.setStyleSheet(
                "font-size:9px; padding:2px 6px; border-radius:8px; "
                "background-color:#fef2f2; color:#dc2626; border:1px solid #fecaca; font-weight:600;"
            )
        else:
            badge.setStyleSheet(
                "font-size:9px; padding:2px 6px; border-radius:8px; "
                "background-color:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; font-weight:600;"
            )
        header_row.addWidget(badge)
        card_layout.addLayout(header_row)

        # IQR bounds
        lower_bound = float(meta.get('lb') or 0.0)
        upper_bound = float(meta.get('ub') or 0.0)
        bounds_label = QLabel(f"Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
        bounds_label.setStyleSheet("font-size: 9px; color: #6b7280;")
        card_layout.addWidget(bounds_label)

        # Outlier values (or "None detected")
        outlier_values = meta.get('values') or []
        if not outlier_values:
            none_label = QLabel('None detected')
            none_label.setStyleSheet("font-size: 10px; color: #6b7280;")
            card_layout.addWidget(none_label)
        else:
            # Show the most extreme value; badge already communicates total count
            extreme_label = QLabel(f"Most extreme: {float(outlier_values[0]):.2f}")
            extreme_label.setStyleSheet("font-size: 10px; color: #dc2626; font-weight: 600;")
            card_layout.addWidget(extreme_label)

        return card

    def _render_outliers(self, outliers_by_col):
        """Populate the outliers grid with up to 6 outlier cards."""
        self._clear_grid(self.outliers_grid)
        for idx, col_name in enumerate(list(outliers_by_col.keys())[:6]):
            card = self._outlier_card(col_name, outliers_by_col[col_name])
            self.outliers_grid.addWidget(card, idx // 2, idx % 2)

    # ==================================================================
    # Column-data accessors
    # ==================================================================
    def _get_column_data(self, column_name, max_rows=None):
        """Extract numeric values for *column_name* from the loaded rows.

        Falls back to synthetic sample data when the backend has not yet
        delivered real rows.  When *max_rows* is set and the data is longer,
        values are evenly sub-sampled to keep charts responsive.
        """
        if not self._analytics_rows:
            return self._generate_sample_data(column_name, max_rows or 50)

        data = [v for v in (self._to_float(row.get(column_name)) for row in self._analytics_rows) if v is not None]

        if not data:
            return self._generate_sample_data(column_name, max_rows or 50)

        # Convert to numpy array and filter out invalid values
        data_array = np.array(data, dtype=float)
        
        # Remove NaN and infinite values
        finite_mask = np.isfinite(data_array)
        if not np.any(finite_mask):
            logger.warning(f"Column '{column_name}' contains no finite values")
            return self._generate_sample_data(column_name, max_rows or 50)
        
        data_array = data_array[finite_mask]

        if max_rows and len(data_array) > max_rows:
            step = len(data_array) / max_rows
            data_array = data_array[[int(i * step) for i in range(max_rows)]]

        return data_array

    def _generate_sample_data(self, column_name, n=50):
        """Synthesise plausible sample data from the dataset summary when real rows are unavailable.

        Uses the column's known mean, min, and max to parameterise a clipped
        normal distribution; falls back to N(50, 15) when no summary exists.
        """
        if not self.current_dataset:
            return np.random.normal(50, 15, n)

        summary  = self.current_dataset.get("summary_json") or {}
        averages = summary.get("averages") or {}

        if column_name in averages:
            mean = averages[column_name]
            mins = summary.get("min") or {}
            maxs = summary.get("max") or {}
            # Estimate std from the range (approx 6-sigma covers 99.7 %)
            std  = (maxs.get(column_name, mean + 45) - mins.get(column_name, mean - 45)) / 6
            return np.clip(
                np.random.normal(mean, std, n),
                mins.get(column_name, mean - 3 * std),
                maxs.get(column_name, mean + 3 * std),
            )

        return np.random.normal(50, 15, n)

    # ==================================================================
    # Chart update / clear / export
    # ==================================================================
    def update_chart(self):
        """Re-render the chart canvas based on the current combo-box selections."""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Data", "Dataset not loaded")
            return

        try:
            chart_key = self.viz_type_combo.currentData()
            x_col     = self.x_axis_combo.currentText()
            y_col     = self.y_axis_combo.currentText()

            if chart_key in ("line", "scatter"):
                x_data = self._get_column_data(x_col, 100)
                y_data = self._get_column_data(y_col, 100)
                min_len = min(len(x_data), len(y_data))
                x_data, y_data = x_data[:min_len], y_data[:min_len]

                if chart_key == "line":
                    order  = np.argsort(x_data)     # sort by x for a sensible line
                    x_data = x_data[order]
                    y_data = y_data[order]
                    self.canvas.line_chart(x_data, y_data, f"{y_col} vs {x_col}", x_col, y_col)
                else:
                    self.canvas.scatter_plot(x_data, y_data, f"{y_col} vs {x_col}", x_col, y_col)

            elif chart_key == "bar":
                y_data = self._get_column_data(y_col, 15)
                labels = [f"Sample {i + 1}" for i in range(len(y_data))]
                self.canvas.bar_chart(labels, y_data, f"Bar Chart: {y_col}", "Samples", y_col)

            elif chart_key == "hist":
                self.canvas.histogram(self._get_column_data(y_col, 500), f"Distribution of {y_col}", y_col)

            elif chart_key == "box":
                self.canvas.box_plot(self._get_column_data(y_col, 500), f"Box Plot of {y_col}", y_col)

            elif chart_key == "heatmap":
                self._render_heatmap_chart()

            elif chart_key == "donut":
                self._render_donut_chart()

        except Exception as exc:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {exc}")
            logger.exception("Chart render error")

    def _render_heatmap_chart(self):
        """Build the correlation matrix from loaded data and hand it to the canvas."""
        summary      = self.current_dataset.get("summary_json") or {}
        numeric_cols = summary.get("numeric_columns") or list((summary.get("averages") or {}).keys())
        
        if not numeric_cols or len(numeric_cols) < 2:
            raise ValueError(f"Need at least 2 numeric columns for heatmap. Found: {numeric_cols}")

        col_arrays = []
        valid_cols = []
        
        for col in numeric_cols:
            try:
                data = self._get_column_data(col, 200)
                
                if len(data) >= 2 and np.any(np.isfinite(data)):
                    col_arrays.append(data)
                    valid_cols.append(col)
            except Exception as e:
                logger.warning(f"Failed to get data for column '{col}': {e}")
        
        if not col_arrays or len(col_arrays) < 2:
            raise ValueError(f"Need at least 2 valid columns with data. Valid columns: {valid_cols}")

        # Trim all columns to the shortest length so the matrix is rectangular
        min_len    = min(len(arr) for arr in col_arrays)
        if min_len < 2:
            raise ValueError(f"Insufficient data points. Minimum length: {min_len}")
            
        col_arrays = [arr[:min_len] for arr in col_arrays]

        try:
            matrix = np.corrcoef(np.array(col_arrays).T, rowvar=False)
            
            # Check for valid correlation matrix
            if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
                raise ValueError("Correlation matrix contains invalid values (NaN/inf)")
                
            self.canvas.heatmap(matrix, valid_cols, "Correlation Heatmap")
            
        except Exception as e:
            raise ValueError(f"Failed to compute correlation matrix: {e}")

    def _render_donut_chart(self):
        """Aggregate categorical-column frequencies and pass them to the canvas.

        Slices that represent less than DONUT_MIN_SLICE_FRACTION of total rows
        are collapsed into an 'Other' bucket once DONUT_MAX_SLICES named
        slices have been emitted.
        """
        col = self.y_axis_combo.currentText()
        if not col or col == "(no categorical columns)":
            QMessageBox.warning(self, "No Data", "No categorical columns available for the donut chart.")
            return

        # Count raw frequencies
        frequency_counter = Counter()
        for row in self._analytics_rows:
            value = row.get(col)
            if value not in (None, "", "nan", "null", "NaN"):
                frequency_counter[str(value)] += 1

        if not frequency_counter:
            QMessageBox.warning(self, "No Data", f"No values found in column '{col}'.")
            return

        # Build label / value lists, bucketing rare slices into "Other"
        labels, values, other_count = [], [], 0
        total_rows = len(self._analytics_rows) or 1

        for label, count in frequency_counter.most_common():
            if count / total_rows < DONUT_MIN_SLICE_FRACTION and len(labels) >= DONUT_MAX_SLICES:
                other_count += count
            else:
                labels.append(label)
                values.append(count)

        if other_count:
            labels.append("Other")
            values.append(other_count)

        self.canvas.donut_chart(labels, values, f"Distribution of {col}")

    def clear_chart(self):
        """Reset the canvas to a blank state."""
        self.canvas.clear()

    def export_chart(self):
        """Prompt the user for a file path and export the current chart."""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Data", "Dataset not loaded")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", "chart.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )
        if not file_path:
            return

        try:
            self.canvas.export_chart(file_path)
            QMessageBox.information(self, "Success", f"Chart exported to {file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to export chart: {exc}")

    # ==================================================================
    # PDF report generation  (split into focused section builders)
    # ==================================================================
    def generate_report(self):
        """Entry point: ask for a path, then delegate to section builders."""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Report", "Please load a dataset first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "analytics_report.pdf",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return

        try:
            # Fail fast if reportlab is missing
            from reportlab.platypus import SimpleDocTemplate
            from reportlab.lib.pagesizes import A4

            doc   = SimpleDocTemplate(file_path, pagesize=A4)
            story = self._build_report_story()
            doc.build(story)

            # Clean up any temp chart PNGs that were written during story assembly
            for temp_path in getattr(self, '_last_report_temp_paths', []):
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except OSError:
                    pass

            QMessageBox.information(self, "Success",
                                    f"Report generated successfully!\n\nSaved to: {file_path}")

        except ImportError:
            QMessageBox.critical(self, "Missing Dependency",
                                 "ReportLab is required for PDF generation.\n\n"
                                 "Install it with:  pip install reportlab")
        except Exception as exc:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {exc}")
            logger.exception("Report generation error")

    # ------------------------------------------------------------------
    # Report story assembly
    # ------------------------------------------------------------------
    def _build_report_story(self):
        """Return the full list of ReportLab flowables that make up the PDF."""
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Spacer, PageBreak
        from reportlab.lib.units import inch

        styles = getSampleStyleSheet()
        custom_styles = self._report_custom_styles(styles)

        story = []
        story += self._report_title_section(styles, custom_styles)
        story.append(Spacer(1, 0.3 * inch))
        story += self._report_overview_section(custom_styles)
        story.append(Spacer(1, 0.3 * inch))

        # Sections that need the raw row data
        if self._analytics_rows:
            summary      = self.current_dataset.get('summary_json', {})
            numeric_cols = summary.get('numeric_columns', [])

            if numeric_cols:
                # Compute once; reuse in stats, insights, and outliers sections
                stats_map       = self._compute_stats(self._analytics_rows, numeric_cols, None)
                corr_data       = self._compute_corr(self._analytics_rows, numeric_cols)
                outliers_by_col = self._compute_outliers(self._analytics_rows, numeric_cols)
                insights        = self._build_insights(self._analytics_rows, numeric_cols,
                                                       stats_map, corr_data, outliers_by_col)

                story += self._report_stats_section(stats_map, styles, custom_styles)
                story += self._report_insights_section(insights, styles, custom_styles)
                story += self._report_outliers_section(outliers_by_col, styles, custom_styles)

        story.append(PageBreak())
        story += self._report_visualizations_section(styles, custom_styles)

        return story

    # ------------------------------------------------------------------
    # Shared report styles
    # ------------------------------------------------------------------
    @staticmethod
    def _report_custom_styles(base_styles):
        """Create and return the custom ParagraphStyle instances used across the report."""
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER

        return {
            'title': ParagraphStyle(
                'CustomTitle', parent=base_styles['Heading1'],
                fontSize=24, textColor=colors.HexColor('#1f2937'),
                spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold',
            ),
            'heading': ParagraphStyle(
                'CustomHeading', parent=base_styles['Heading2'],
                fontSize=16, textColor=colors.HexColor('#374151'),
                spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold',
            ),
            'subheading': ParagraphStyle(
                'CustomSubHeading', parent=base_styles['Heading3'],
                fontSize=12, textColor=colors.HexColor('#6b7280'),
                spaceAfter=8, fontName='Helvetica-Bold',
            ),
        }

    # ------------------------------------------------------------------
    # Individual report sections
    # ------------------------------------------------------------------
    def _report_title_section(self, base_styles, custom_styles):
        """Title + generated-at timestamp."""
        from reportlab.platypus import Paragraph
        from datetime import datetime

        dataset_name = self.current_dataset.get('filename', 'Dataset')
        return [
            Paragraph(f"Analytics Report: {dataset_name}", custom_styles['title']),
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", base_styles['Normal']),
        ]

    def _report_overview_section(self, custom_styles):
        """Dataset-overview table."""
        from reportlab.platypus import Paragraph, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        summary      = self.current_dataset.get('summary_json', {})
        dataset_name = self.current_dataset.get('filename', 'Dataset')

        overview_data = [
            ['Property',          'Value'],
            ['Dataset Name',      dataset_name],
            ['Total Rows',        str(summary.get('row_count', 'N/A'))],
            ['Total Columns',     str(summary.get('column_count', 'N/A'))],
            ['Numeric Columns',   str(len(summary.get('numeric_columns', [])))],
        ]

        table = Table(overview_data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0),  colors.HexColor('#3b82f6')),
            ('TEXTCOLOR',    (0, 0), (-1, 0),  colors.whitesmoke),
            ('ALIGN',        (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, 0),  12),
            ('BOTTOMPADDING',(0, 0), (-1, 0),  12),
            ('BACKGROUND',   (0, 1), (-1, -1), colors.white),
            ('GRID',         (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE',     (0, 1), (-1, -1), 10),
            ('PADDING',      (0, 0), (-1, -1), 8),
        ]))

        return [Paragraph("Dataset Overview", custom_styles['heading']), table]

    def _report_stats_section(self, stats_map, base_styles, custom_styles):
        """Per-column summary-statistics tables (up to 6 columns)."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        flowables = [Paragraph("Summary Statistics", custom_styles['heading'])]

        for col_name, col_stats in list(stats_map.items())[:6]:
            flowables.append(Paragraph(col_name, custom_styles['subheading']))

            table_data = [
                ['Metric',  'Value'],
                ['Mean',    f"{col_stats['mean']:.2f}"],
                ['Median',  f"{col_stats['median']:.2f}"],
                ['Std Dev', f"{col_stats['std']:.2f}"],
                ['Min',     f"{col_stats['min']:.2f}"],
                ['Max',     f"{col_stats['max']:.2f}"],
                ['Count',   f"{int(col_stats['n'])}"],
                ['Missing', f"{int(col_stats['missing'])}"],
            ]

            table = Table(table_data, colWidths=[2 * inch, 2 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0),  colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR',  (0, 0), (-1, 0),  colors.HexColor('#374151')),
                ('ALIGN',      (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME',   (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('PADDING',    (0, 0), (-1, -1), 6),
            ]))

            flowables.append(table)
            flowables.append(Spacer(1, 0.15 * inch))

        flowables.append(Spacer(1, 0.2 * inch))
        return flowables

    def _report_insights_section(self, insights, base_styles, custom_styles):
        """Bullet list of auto-generated insights."""
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import inch

        flowables = [Paragraph("Key Insights", custom_styles['heading'])]

        if insights:
            for insight in insights:
                flowables.append(Paragraph(f"• {insight}", base_styles['Normal']))
                flowables.append(Spacer(1, 0.1 * inch))
        else:
            flowables.append(Paragraph("No significant insights detected.", base_styles['Normal']))

        flowables.append(Spacer(1, 0.3 * inch))
        return flowables

    def _report_outliers_section(self, outliers_by_col, base_styles, custom_styles):
        """Per-column outlier tables (only columns that actually have outliers)."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        flowables = [Paragraph("Outlier Analysis", custom_styles['heading'])]

        for col_name, meta in list(outliers_by_col.items())[:6]:
            count = int(meta.get('count', 0))
            if count == 0:
                continue

            flowables.append(Paragraph(f"{col_name} – {count} outliers", custom_styles['subheading']))

            table_data = [
                ['Property',      'Value'],
                ['Lower Bound',   f"{float(meta.get('lb', 0.0)):.2f}"],
                ['Upper Bound',   f"{float(meta.get('ub', 0.0)):.2f}"],
                ['Outlier Count', str(count)],
            ]
            sample_values = meta.get('values', [])
            if sample_values:
                table_data.append(['Sample Values', ', '.join(f"{v:.2f}" for v in sample_values[:5])])

            table = Table(table_data, colWidths=[2 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0),  colors.HexColor('#fef2f2')),
                ('TEXTCOLOR',  (0, 0), (-1, 0),  colors.HexColor('#dc2626')),
                ('ALIGN',      (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME',   (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca')),
                ('PADDING',    (0, 0), (-1, -1), 6),
            ]))

            flowables.append(table)
            flowables.append(Spacer(1, 0.15 * inch))

        flowables.append(Spacer(1, 0.3 * inch))
        return flowables

    def _report_visualizations_section(self, base_styles, custom_styles):
        """Generate chart PNGs into temp files and embed them in the PDF."""
        import tempfile
        from reportlab.platypus import Paragraph, Spacer, Image
        from reportlab.lib.units import inch

        flowables   = [Paragraph("Visualizations", custom_styles['heading'])]
        summary     = self.current_dataset.get('summary_json', {})
        numeric_cols = summary.get('numeric_columns', [])
        temp_paths  = []                     # track for cleanup

        if numeric_cols and len(numeric_cols) >= 2:
            y_col = numeric_cols[0]
            x_col = numeric_cols[1]

            chart_specs = [
                ('hist',    'Histogram',            lambda: self.canvas.histogram(self._get_column_data(y_col, 500), f"Distribution of {y_col}", y_col)),
                ('box',     'Box Plot',             lambda: self.canvas.box_plot(self._get_column_data(y_col, 500), f"Box Plot of {y_col}", y_col)),
                ('scatter', 'Scatter Plot',         lambda: self._draw_scatter_for_report(x_col, y_col)),
                ('heatmap', 'Correlation Heatmap',  lambda: self._draw_heatmap_for_report(numeric_cols)),
            ]

            for chart_id, chart_title, draw_fn in chart_specs:
                temp_path = os.path.join(tempfile.gettempdir(), f'chart_{chart_id}_{os.getpid()}.png')
                temp_paths.append(temp_path)
                try:
                    draw_fn()
                    self.canvas.export_chart(temp_path)

                    if os.path.exists(temp_path):
                        flowables.append(Paragraph(chart_title, custom_styles['subheading']))
                        flowables.append(Image(temp_path, width=5 * inch, height=3.5 * inch))
                        flowables.append(Spacer(1, 0.3 * inch))

                except Exception as exc:
                    logger.warning("Skipping chart '%s' in report: %s", chart_title, exc)

        # Store paths so generate_report() can clean up after doc.build()
        self._last_report_temp_paths = temp_paths
        return flowables

    # Helper methods kept separate so the lambda list above stays readable
    def _draw_scatter_for_report(self, x_col, y_col):
        """Render a scatter plot sized for the report."""
        x_data = self._get_column_data(x_col, 100)
        y_data = self._get_column_data(y_col, 100)
        min_len = min(len(x_data), len(y_data))
        self.canvas.scatter_plot(x_data[:min_len], y_data[:min_len],
                                 f"{y_col} vs {x_col}", x_col, y_col)

    def _draw_heatmap_for_report(self, numeric_cols):
        """Render a correlation heatmap sized for the report (max 6 columns)."""
        cols_to_use = numeric_cols[:6]
        col_arrays  = [self._get_column_data(col, 200) for col in cols_to_use]
        min_len     = min(len(arr) for arr in col_arrays)
        col_arrays  = [arr[:min_len] for arr in col_arrays]
        matrix      = np.corrcoef(np.array(col_arrays).T, rowvar=False)
        self.canvas.heatmap(matrix, cols_to_use, "Correlation Matrix")
