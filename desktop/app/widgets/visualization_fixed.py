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
import os

matplotlib.use('Qt5Agg')

class AnalyticsFetchThread(QThread):
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
            rows_resp = self.api_client.get_dataset_rows(self.dataset_id, limit=self.limit, offset=self.offset)
            payload['rows'] = rows_resp
            try:
                payload['quality'] = self.api_client.get_quality_metrics(self.dataset_id)
            except Exception:
                payload['quality'] = None
        except Exception as e:
            payload['error'] = str(e)
        self.loaded.emit(payload)


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.current_palette = 'viridis'
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        self.axes.set_axis_off()
        self.fig.patch.set_alpha(0)
        self.axes.patch.set_alpha(0)

    def clear(self):
        self.axes.clear()
        self.axes.set_axis_off()
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        self.draw()

    def update_chart_style(self):
        self.axes.set_facecolor('white')
        self.fig.patch.set_facecolor('white')
        for spine in self.axes.spines.values():
            spine.set_color('#e5e7eb')
            spine.set_linewidth(1)
        if hasattr(self.axes, 'xaxis') and hasattr(self.axes, 'yaxis'):
            self.axes.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color='#9ca3af')
            self.axes.tick_params(colors='#6b7280', labelsize=10)
        if self.axes.get_title():
            self.axes.set_title(self.axes.get_title(), fontsize=14, fontweight='600', color='#1f2937', pad=20)
        if self.axes.get_xlabel():
            self.axes.set_xlabel(self.axes.get_xlabel(), fontsize=11, color='#4b5563')
        if self.axes.get_ylabel():
            self.axes.set_ylabel(self.axes.get_ylabel(), fontsize=11, color='#4b5563')

    def export_chart(self, filename):
        if filename.endswith('.png'):
            self.fig.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        elif filename.endswith('.pdf'):
            self.fig.savefig(filename, bbox_inches='tight', facecolor='white')
        elif filename.endswith('.svg'):
            self.fig.savefig(filename, bbox_inches='tight', facecolor='white')
        else:
            raise ValueError("Unsupported file format. Use .png, .pdf, or .svg")

    def _prepare_axes(self, title="", xlabel="", ylabel=""):
        self.axes.set_axis_on()
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.update_chart_style()

    def line_chart(self, x, y, title="", xlabel="", ylabel=""):
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        self.axes.plot(x, y, color='#3b82f6', linewidth=2)
        self.draw()

    def bar_chart(self, labels, values, title="", xlabel="", ylabel=""):
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        self.axes.bar(labels, values, color='#3b82f6', alpha=0.9)
        self.axes.tick_params(axis='x', rotation=30)
        self.draw()

    def scatter_plot(self, x, y, title="", xlabel="", ylabel=""):
        self.axes.clear()
        self._prepare_axes(title, xlabel, ylabel)
        self.axes.scatter(x, y, s=30, alpha=0.7, color='#3b82f6', edgecolors='none')
        self.draw()

    def histogram(self, data, title="", xlabel=""):
        self.axes.clear()
        self._prepare_axes(title, xlabel, "Frequency")
        self.axes.hist(data, bins=20, color='#3b82f6', alpha=0.7, edgecolor='white')
        self.draw()

    def box_plot(self, data, title="", ylabel=""):
        self.axes.clear()
        self._prepare_axes(title, "", ylabel)
        self.axes.boxplot(
            data,
            vert=True,
            patch_artist=True,
            boxprops=dict(facecolor='#3b82f6', alpha=0.35, edgecolor='#2563eb'),
            medianprops=dict(color='#1f2937', linewidth=2),
            whiskerprops=dict(color='#6b7280'),
            capprops=dict(color='#6b7280'),
            flierprops=dict(marker='o', markerfacecolor='#ef4444', markersize=4, markeredgecolor='none', alpha=0.6),
        )
        self.draw()

    def heatmap(self, matrix, labels, title=""):
        self.axes.clear()
        self.axes.set_axis_on()
        im = self.axes.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
        self.axes.set_xticks(range(len(labels)))
        self.axes.set_yticks(range(len(labels)))
        self.axes.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
        self.axes.set_yticklabels(labels, fontsize=9)
        self.axes.set_title(title)
        self.fig.colorbar(im, ax=self.axes, fraction=0.046, pad=0.04)
        self.update_chart_style()
        self.draw()

    def donut_chart(self, labels, values, title=""):
        self.axes.clear()
        self.axes.set_axis_on()
        colors = plt.cm.get_cmap(self.current_palette)(np.linspace(0.2, 0.9, len(values)))
        wedges, _ = self.axes.pie(values, startangle=90, colors=colors)
        centre = plt.Circle((0, 0), 0.70, fc='white')
        self.axes.add_artist(centre)
        self.axes.legend(wedges, labels, loc='center left', bbox_to_anchor=(1.0, 0.5), fontsize=9)
        self.axes.set_title(title)
        self.draw()


class VisualizationWidget(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_dataset = None
        self.current_palette = 'modern'
        self.analytics_thread = None
        self._analytics_rows = []
        self.init_ui()
        self.apply_modern_styling()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        self.controls_panel = self.create_controls_panel()
        main_layout.addWidget(self.controls_panel)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        splitter.addWidget(self.canvas)
        
        self.analytics_panel = self.create_analytics_panel()
        splitter.addWidget(self.analytics_panel)
        
        splitter.setStretchFactor(0, 1)  # Canvas - takes remaining space
        splitter.setStretchFactor(1, 0)  # Analytics panel - fixed width
        splitter.setSizes([800, 400])
        
        main_layout.addWidget(splitter)
        self.canvas.current_palette = self.current_palette

    def create_controls_panel(self):
        panel = QFrame()
        panel.setFixedHeight(120)
        panel.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e5e7eb; border-radius: 12px; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # Chart Type
        chart_type_layout = QVBoxLayout()
        chart_type_layout.setContentsMargins(0, 0, 0, 0)
        chart_type_layout.setSpacing(4)
        chart_type_label = QLabel("Chart Type")
        chart_type_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #6b7280;")
        chart_type_layout.addWidget(chart_type_label)
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItem("Line Chart", "line")
        self.viz_type_combo.addItem("Bar Chart", "bar")
        self.viz_type_combo.addItem("Scatter Plot", "scatter")
        self.viz_type_combo.addItem("Histogram", "hist")
        self.viz_type_combo.addItem("Box Plot", "box")
        self.viz_type_combo.addItem("Heatmap", "heatmap")
        self.viz_type_combo.addItem("Donut Chart", "donut")
        self.viz_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        chart_type_layout.addWidget(self.viz_type_combo)
        controls_layout.addLayout(chart_type_layout)
        
        # X-Axis
        x_axis_layout = QVBoxLayout()
        x_axis_layout.setContentsMargins(0, 0, 0, 0)
        x_axis_layout.setSpacing(4)
        x_axis_label = QLabel("X-Axis")
        x_axis_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #6b7280;")
        x_axis_layout.addWidget(x_axis_label)
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.setMinimumWidth(120)
        x_axis_layout.addWidget(self.x_axis_combo)
        controls_layout.addLayout(x_axis_layout)
        
        # Y-Axis
        y_axis_layout = QVBoxLayout()
        y_axis_layout.setContentsMargins(0, 0, 0, 0)
        y_axis_layout.setSpacing(4)
        y_axis_label = QLabel("Y-Axis")
        y_axis_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #6b7280;")
        y_axis_layout.addWidget(y_axis_label)
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.setMinimumWidth(120)
        y_axis_layout.addWidget(self.y_axis_combo)
        controls_layout.addLayout(y_axis_layout)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(self.update_chart)
        button_layout.addWidget(self.update_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_chart)
        button_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_chart)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.set_controls_enabled(False)
        return panel

    def create_analytics_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(360)
        scroll.setMaximumWidth(480)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #f8fafc; border: none; }")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        def section(title, subtitle):
            frame = QFrame()
            frame.setStyleSheet("QFrame { background-color: #ffffff; border: 2px solid #e5e7eb; border-radius: 12px; }")
            l = QVBoxLayout(frame)
            l.setContentsMargins(12, 12, 12, 12)
            l.setSpacing(8)
            row = QHBoxLayout()
            t = QLabel(title)
            t.setStyleSheet("font-size: 14px; font-weight: 700; color: #1f2937;")
            row.addWidget(t)
            row.addStretch()
            s = QLabel(subtitle)
            s.setStyleSheet("font-size: 11px; color: #6b7280;")
            row.addWidget(s)
            l.addLayout(row)
            return frame, l
        
        self.summary_frame, summary_layout = section("Summary Stats", "Key numeric metrics")
        self.summary_grid = QGridLayout()
        self.summary_grid.setContentsMargins(0, 0, 0, 0)
        self.summary_grid.setHorizontalSpacing(8)
        self.summary_grid.setVerticalSpacing(8)
        summary_layout.addLayout(self.summary_grid)
        
        self.insights_frame, insights_layout = section("Insights", "Auto-generated observations")
        self.insights_label = QLabel("Select a dataset to see insights")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("font-size: 12px; color: #374151;")
        insights_layout.addWidget(self.insights_label)
        
        self.outliers_frame, out_layout = section("Outliers by Metric", "IQR rule per numeric column")
        self.outliers_grid = QGridLayout()
        self.outliers_grid.setContentsMargins(0, 0, 0, 0)
        self.outliers_grid.setHorizontalSpacing(8)
        self.outliers_grid.setVerticalSpacing(8)
        out_layout.addLayout(self.outliers_grid)
        
        layout.addWidget(self.summary_frame)
        layout.addWidget(self.insights_frame)
        layout.addWidget(self.outliers_frame)
        layout.addStretch()
        
        scroll.setWidget(container)
        return scroll

    def apply_modern_styling(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif; font-size: 12px; color: #1f2937; background-color: #ffffff; }
            QComboBox { background-color: #ffffff; border: 2px solid #e5e7eb; border-radius: 8px; padding: 6px 12px; font-size: 12px; min-height: 20px; }
            QComboBox:hover { border-color: #d1d5db; }
            QComboBox:focus { border-color: #3b82f6; outline: none; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #6b7280; margin-right: 4px; }
            QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 600; min-height: 22px; }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #e5e7eb; color: #9ca3af; }
            QLabel { color: #1f2937; }
            QFrame { background-color: #ffffff; border-color: #e5e7eb; }
        """)

    def on_chart_type_changed(self, chart_type):
        """Handle chart type change - update UI based on selected chart"""
        chart_data = self.viz_type_combo.currentData()
        
        # Enable/disable axis selectors based on chart type
        if chart_data in ['hist', 'box']:
            # These charts only need Y-axis
            self.x_axis_combo.setEnabled(False)
            self.y_axis_combo.setEnabled(True)
        elif chart_data in ['heatmap', 'donut']:
            # These charts don't use traditional axes
            self.x_axis_combo.setEnabled(False)
            self.y_axis_combo.setEnabled(False)
        else:
            # Line, bar, scatter need both axes
            self.x_axis_combo.setEnabled(True)
            self.y_axis_combo.setEnabled(True)

    def load_dataset(self, dataset):
        """Load a dataset and populate column selectors"""
        self.current_dataset = dataset
        try:
            if not isinstance(self.current_dataset, dict):
                raise ValueError("Invalid dataset")

            # Many list endpoints return only id/filename/etc.
            # If summary_json isn't present, fetch it from backend.
            summary = self.current_dataset.get("summary_json")
            dataset_id = self.current_dataset.get("id")
            if (not isinstance(summary, dict)) and dataset_id and self.api_client is not None:
                health = self.api_client.get_dataset_health(dataset_id)
                summary = (health.get("summary_json") or health.get("summary") or {})
                if isinstance(summary, dict):
                    self.current_dataset["summary_json"] = summary

            summary = self.current_dataset.get("summary_json") or {}
            cols = summary.get("numeric_columns")
            if not cols:
                av = summary.get("averages") or {}
                if isinstance(av, dict):
                    cols = list(av.keys())
            if not cols:
                raise ValueError("No numeric columns available")

            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            self.x_axis_combo.addItems(cols)
            self.y_axis_combo.addItems(cols)
            self.set_controls_enabled(True)
            
            # Start analytics fetch
            self.update_chart()
            self._start_analytics()
            
        except Exception as e:
            self.set_controls_enabled(False)
            QMessageBox.critical(self, "No Data", f"Dataset not loaded: {str(e)}")

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable all controls"""
        self.viz_type_combo.setEnabled(enabled)
        self.x_axis_combo.setEnabled(enabled)
        self.y_axis_combo.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)
        if hasattr(self, 'canvas'):
            self.canvas.current_palette = self.current_palette

    def _start_analytics(self):
        """Start fetching analytics data in background thread"""
        dataset_id = self.current_dataset.get('id') if isinstance(self.current_dataset, dict) else None
        if not dataset_id or self.api_client is None:
            self._render_analytics_error('No dataset id or API client')
            return
        
        self._render_analytics_loading()
        if self.analytics_thread is not None and self.analytics_thread.isRunning():
            try:
                self.analytics_thread.terminate()
            except Exception:
                pass
        
        self.analytics_thread = AnalyticsFetchThread(self.api_client, dataset_id, limit=500, offset=0, parent=self)
        self.analytics_thread.loaded.connect(self._on_analytics_loaded)
        self.analytics_thread.start()

    def _render_analytics_loading(self):
        """Show loading state for analytics"""
        self.insights_label.setText('Loading analytics...')
        self.insights_label.setTextFormat(Qt.PlainText)
        self._clear_grid(self.summary_grid)
        self._clear_grid(self.outliers_grid)

    def _render_analytics_error(self, message):
        """Show error state for analytics"""
        self.insights_label.setText(f'Analytics unavailable: {message}')
        self.insights_label.setTextFormat(Qt.PlainText)
        self._clear_grid(self.summary_grid)
        self._clear_grid(self.outliers_grid)

    def _clear_grid(self, grid):
        """Clear all widgets from a grid layout"""
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _to_float(self, v):
        """Convert value to float, handling various input types"""
        if isinstance(v, (int, float)):
            return float(v) if np.isfinite(v) else None
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                n = float(s)
                return n if np.isfinite(n) else None
            except Exception:
                return None
        return None

    def _quartiles(self, vals):
        """Calculate quartiles from a list of values"""
        v = [x for x in vals if isinstance(x, (int, float)) and np.isfinite(x)]
        if not v:
            return {'min': 0.0, 'q1': 0.0, 'q2': 0.0, 'q3': 0.0, 'max': 0.0}
        v.sort()
        arr = np.array(v, dtype=float)
        q1 = float(np.percentile(arr, 25, method='linear'))
        q2 = float(np.percentile(arr, 50, method='linear'))
        q3 = float(np.percentile(arr, 75, method='linear'))
        return {'min': float(arr[0]), 'q1': q1, 'q2': q2, 'q3': q3, 'max': float(arr[-1])}

    def _on_analytics_loaded(self, payload):
        """Process loaded analytics data"""
        err = payload.get('error')
        if err:
            self._render_analytics_error(err)
            return
        
        rows_resp = payload.get('rows') or {}
        rows = rows_resp.get('rows') or []
        self._analytics_rows = rows
        
        summary = (self.current_dataset or {}).get('summary_json') or {}
        numeric_cols = summary.get('numeric_columns') or []
        if not numeric_cols and rows:
            keys = list(rows[0].keys())
            id_like = {'Record', 'record', 'id', 'ID', 'index', 'Index'}
            for k in keys:
                if k in id_like:
                    continue
                if any(self._to_float(r.get(k)) is not None for r in rows):
                    numeric_cols.append(k)
        
        stats_map = self._compute_stats(rows, numeric_cols, payload.get('quality'))
        corr = self._compute_corr(rows, numeric_cols)
        outliers_by_col = self._compute_outliers(rows, numeric_cols)
        insights = self._build_insights(rows, numeric_cols, stats_map, corr, outliers_by_col)
        
        self._render_summary(stats_map)
        self._render_outliers(outliers_by_col)
        
        if insights:
            html = '<ul style="margin-left:16px;">' + ''.join([f'<li>{self._escape_html(t)}</li>' for t in insights]) + '</ul>'
            self.insights_label.setTextFormat(Qt.RichText)
            self.insights_label.setText(html)
        else:
            self.insights_label.setTextFormat(Qt.PlainText)
            self.insights_label.setText('No significant insights detected.')

    def _compute_stats(self, rows, numeric_cols, quality_payload=None):
        """Compute summary statistics for numeric columns"""
        missing_map = None
        if isinstance(quality_payload, dict):
            qm = quality_payload.get('quality_metrics')
            if isinstance(qm, dict):
                missing_map = qm.get('missing_values')
        
        total = len(rows) if rows else 0
        out = {}
        for col in numeric_cols:
            vals = []
            for r in rows:
                f = self._to_float(r.get(col))
                if f is not None:
                    vals.append(f)
            q = self._quartiles(vals)
            mean_v = float(np.mean(vals)) if vals else 0.0
            std_v = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            missing = max(0, total - len(vals))
            if isinstance(missing_map, dict) and isinstance(missing_map.get(col), int):
                missing = missing_map.get(col)
            out[col] = {
                'mean': mean_v,
                'median': q['q2'],
                'min': q['min'],
                'max': q['max'],
                'std': std_v,
                'n': max(0, total - missing) if total else len(vals),
                'missing': missing,
                'total': total,
            }
        return out

    def _compute_corr(self, rows, numeric_cols):
        """Compute correlation matrix for numeric columns"""
        if not rows or len(numeric_cols) < 2:
            return {'order': numeric_cols, 'matrix': []}
        data = []
        for r in rows:
            row_vals = []
            ok = True
            for c in numeric_cols:
                f = self._to_float(r.get(c))
                if f is None:
                    ok = False
                    break
                row_vals.append(f)
            if ok:
                data.append(row_vals)
        if len(data) < 2:
            return {'order': numeric_cols, 'matrix': []}
        arr = np.array(data, dtype=float)
        corr = np.corrcoef(arr, rowvar=False)
        return {'order': numeric_cols, 'matrix': corr.tolist()}

    def _compute_outliers(self, rows, numeric_cols):
        """Detect outliers using IQR method"""
        out = {}
        for col in numeric_cols:
            vals = []
            for r in rows:
                f = self._to_float(r.get(col))
                if f is not None:
                    vals.append(f)
            if len(vals) < 4:
                out[col] = {'lb': 0.0, 'ub': 0.0, 'values': []}
                continue
            q = self._quartiles(vals)
            iqr = q['q3'] - q['q1']
            lb = q['q1'] - 1.5 * iqr
            ub = q['q3'] + 1.5 * iqr
            ovals = [v for v in vals if v < lb or v > ub]
            ovals.sort(key=lambda v: max(abs(v - lb), abs(v - ub)), reverse=True)
            out[col] = {'lb': lb, 'ub': ub, 'values': ovals[:8], 'count': len(ovals)}
        return out

    def _build_insights(self, rows, numeric_cols, stats_map, corr, outliers_by_col):
        """Generate automatic insights from data analysis"""
        items = []
        if not numeric_cols:
            return items
        
        cols = [c for c in numeric_cols if c in stats_map]
        if cols:
            max_var = max(cols, key=lambda c: stats_map[c].get('std') or 0.0)
            max_mean = max(cols, key=lambda c: stats_map[c].get('mean') or 0.0)
            if (stats_map[max_var].get('std') or 0.0) > 0:
                items.append(f"Highest variability: {max_var} (std = {stats_map[max_var]['std']:.2f})")
            if (stats_map[max_mean].get('mean') or 0.0) != 0:
                items.append(f"Largest mean value: {max_mean} (mean = {stats_map[max_mean]['mean']:.2f})")
            
            cv_cols = [c for c in cols if abs(stats_map[c].get('mean') or 0.0) > 1e-9]
            if cv_cols:
                cv = {c: abs((stats_map[c].get('std') or 0.0) / (stats_map[c].get('mean') or 1.0)) for c in cv_cols}
                hi = max(cv_cols, key=lambda c: cv[c])
                lo = min(cv_cols, key=lambda c: cv[c])
                items.append(f"Most volatile by CV: {hi} (CV = {cv[hi]:.2f})")
                items.append(f"Most stable by CV: {lo} (CV = {cv[lo]:.2f})")
        
        # Skewness
        skew_map = {}
        for c in numeric_cols:
            vals = [self._to_float(r.get(c)) for r in rows]
            vals = [x for x in vals if x is not None]
            if len(vals) >= 3:
                try:
                    skew_map[c] = float(stats.skew(vals, bias=False))
                except Exception:
                    skew_map[c] = 0.0
        if skew_map:
            top = max(skew_map.keys(), key=lambda c: abs(skew_map[c]))
            if abs(skew_map[top]) > 0.5:
                items.append(f"Most skewed: {top} (skew = {skew_map[top]:.2f})")
        
        # Correlations
        if corr.get('matrix') and corr.get('order') and len(corr['order']) > 1:
            order = corr['order']
            m = corr['matrix']
            best_pos = (0, 1, float(m[0][1]))
            best_neg = (0, 1, float(m[0][1]))
            for i in range(len(order)):
                for j in range(i + 1, len(order)):
                    r = float(m[i][j])
                    if r > best_pos[2]:
                        best_pos = (i, j, r)
                    if r < best_neg[2]:
                        best_neg = (i, j, r)
            if best_pos[2] > 0:
                items.append(f"Top positive correlation: {order[best_pos[0]]} vs {order[best_pos[1]]} (r={best_pos[2]:.2f})")
            if best_neg[2] < 0:
                items.append(f"Top negative correlation: {order[best_neg[0]]} vs {order[best_neg[1]]} (r={best_neg[2]:.2f})")
        
        # Outliers
        top_out = None
        for c, meta in outliers_by_col.items():
            cnt = int(meta.get('count') or 0)
            if top_out is None or cnt > top_out[1]:
                top_out = (c, cnt)
        if top_out and top_out[1] > 0:
            pct = (top_out[1] / max(1, len(rows))) * 100
            items.append(f"Outlier-heavy: {top_out[0]} ({top_out[1]} points, {pct:.1f}% of rows)")
        
        return items

    def _escape_html(self, s):
        """Escape HTML special characters"""
        return (str(s)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#039;'))

    def _stat_card(self, col, s):
        """Create a statistics card widget"""
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #f8fafc; border: 2px solid #e5e7eb; border-radius: 10px; }")
        l = QVBoxLayout(card)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(6)
        
        name = QLabel(col)
        name.setStyleSheet("font-size: 12px; font-weight: 700; color: #1f2937;")
        l.addWidget(name)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        l.addLayout(grid)
        
        def cell(r, c, label, value):
            w = QWidget()
            box = QVBoxLayout(w)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(0)
            a = QLabel(label)
            a.setStyleSheet("font-size: 11px; color: #6b7280;")
            b = QLabel(value)
            b.setStyleSheet("font-size: 11px; font-weight: 700; color: #111827;")
            box.addWidget(a)
            box.addWidget(b)
            grid.addWidget(w, r, c)
        
        cell(0, 0, 'Mean', f"{s['mean']:.2f}")
        cell(0, 1, 'Median', f"{s['median']:.2f}")
        cell(1, 0, 'Min', f"{s['min']:.2f}")
        cell(1, 1, 'Max', f"{s['max']:.2f}")
        cell(2, 0, 'Std', f"{s['std']:.2f}")
        cell(2, 1, 'N', f"{int(s['n'])}")
        cell(3, 0, 'Missing', f"{int(s['missing'])}")
        
        return card

    def _render_summary(self, stats_map):
        """Render summary statistics in the analytics panel"""
        self._clear_grid(self.summary_grid)
        cols = list(stats_map.keys())
        for i, c in enumerate(cols[:6]):
            card = self._stat_card(c, stats_map[c])
            self.summary_grid.addWidget(card, i // 2, i % 2)

    def _outlier_card(self, col, meta):
        """Create an outlier information card widget"""
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #ffffff; border: 2px solid #e5e7eb; border-radius: 10px; }")
        l = QVBoxLayout(card)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(6)
        
        row = QHBoxLayout()
        name = QLabel(col)
        name.setStyleSheet("font-size: 12px; font-weight: 700; color: #111827;")
        row.addWidget(name)
        row.addStretch()
        
        badge = QLabel(f"{int(meta.get('count') or 0)} outliers")
        badge.setStyleSheet("font-size: 10px; padding: 2px 8px; border-radius: 10px; background-color: #fef2f2; color: #dc2626; border: 1px solid #fecaca;")
        row.addWidget(badge)
        l.addLayout(row)
        
        bounds = QLabel(f"Bounds: [{float(meta.get('lb') or 0.0):.2f}, {float(meta.get('ub') or 0.0):.2f}]")
        bounds.setStyleSheet("font-size: 10px; color: #6b7280;")
        l.addWidget(bounds)
        
        vals = meta.get('values') or []
        if not vals:
            none = QLabel('None detected')
            none.setStyleSheet("font-size: 11px; color: #6b7280;")
            l.addWidget(none)
        else:
            for v in vals:
                t = QLabel(f"Value: {float(v):.2f}")
                t.setStyleSheet("font-size: 11px; color: #111827;")
                l.addWidget(t)
        
        return card

    def _render_outliers(self, outliers_by_col):
        """Render outlier information in the analytics panel"""
        self._clear_grid(self.outliers_grid)
        cols = list(outliers_by_col.keys())
        for i, c in enumerate(cols[:6]):
            card = self._outlier_card(c, outliers_by_col[c])
            self.outliers_grid.addWidget(card, i // 2, i % 2)

    def _sample(self, column_name, n=50):
        """Generate sample data for visualization when backend data is not available"""
        if not self.current_dataset:
            return np.random.normal(50, 15, n)
        
        summary = self.current_dataset.get("summary_json") or {}
        averages = summary.get("averages") or {}
        
        if column_name in averages:
            mean = averages[column_name]
            std = 15
            mins = summary.get("min") or {}
            maxs = summary.get("max") or {}
            if column_name in mins and column_name in maxs:
                std = (maxs[column_name] - mins[column_name]) / 6
            return np.clip(np.random.normal(mean, std, n), mins.get(column_name, mean-3*std), maxs.get(column_name, mean+3*std))
        else:
            return np.random.normal(50, 15, n)

    def update_chart(self):
        """Update the chart based on current selections"""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Data", "Dataset not loaded")
            return

        try:
            chart = self.viz_type_combo.currentData()
            x = self.x_axis_combo.currentText()
            y = self.y_axis_combo.currentText()

            if chart in ["line", "scatter"]:
                xd = self._sample(x)
                yd = self._sample(y)
                if chart == "line":
                    self.canvas.line_chart(xd, yd, f"{y} vs {x}", x, y)
                else:
                    self.canvas.scatter_plot(xd, yd, f"{y} vs {x}", x, y)

            elif chart == "bar":
                yd = self._sample(y, 10)
                labels = [f"C{i+1}" for i in range(len(yd))]
                self.canvas.bar_chart(labels, yd, y, "Category", y)

            elif chart == "hist":
                yd = self._sample(y, 200)
                self.canvas.histogram(yd, f"Histogram of {y}", y)

            elif chart == "box":
                yd = self._sample(y, 200)
                self.canvas.box_plot(yd, f"Box Plot of {y}", y)

            elif chart == "heatmap":
                summary = (self.current_dataset.get("summary_json") or {})
                cols = summary.get("numeric_columns")
                if not cols:
                    av = summary.get("averages") or {}
                    cols = list(av.keys()) if isinstance(av, dict) else []
                if not cols:
                    raise ValueError("No numeric columns for heatmap")
                data = np.array([self._sample(c, 100) for c in cols]).T
                corr = np.corrcoef(data, rowvar=False)
                self.canvas.heatmap(corr, cols, "Correlation Heatmap")

            elif chart == "donut":
                yd = self._sample(y, 5)
                labels = [f"R{i+1}" for i in range(len(yd))]
                self.canvas.donut_chart(labels, yd, f"Donut: {y}")
        except Exception as e:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {str(e)}")

    def clear_chart(self):
        """Clear the current chart"""
        self.canvas.clear()

    def export_chart(self):
        """Export the current chart to a file"""
        if not self.current_dataset:
            QMessageBox.warning(self, "No Data", "Dataset not loaded")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            "chart.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )
        if not file_path:
            return
        try:
            self.canvas.export_chart(file_path)
            QMessageBox.information(self, "Success", f"Chart exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export chart: {str(e)}")