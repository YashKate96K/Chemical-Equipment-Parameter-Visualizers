import os
import sys
import json
import requests
import tempfile
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QFileDialog, QTextEdit, QPushButton, QLabel, QVBoxLayout, QWidget,
    QListWidget, QMessageBox, QDialog, QScrollArea
)
from PyQt5.QtGui import QPixmap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

API_BASE = os.getenv('DESKTOP_API_BASE_URL', 'http://localhost:8000/api')
API_TOKEN = os.getenv('DESKTOP_API_TOKEN', '')

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chemical Equipment Visualizer')
        self.resize(800, 600)

        self.upload_btn = QPushButton('Upload CSV')
        self.upload_btn.clicked.connect(self.upload_csv)
        self.gen_pdf_btn = QPushButton('Generate PDF of Selected')
        self.gen_pdf_btn.clicked.connect(self.generate_pdf)
        self.health_btn = QPushButton('Open Dashboard Overview')
        self.health_btn.clicked.connect(self.open_health_overview)

        self.summary_box = QTextEdit(); self.summary_box.setReadOnly(True)
        self.list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Actions'))
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.gen_pdf_btn)
        layout.addWidget(self.health_btn)
        layout.addWidget(QLabel('Summary JSON'))
        layout.addWidget(self.summary_box)
        layout.addWidget(QLabel('Last 5 Datasets'))
        layout.addWidget(self.list)
        self.setLayout(layout)

        self.refresh_list()

    def headers(self):
        h = {}
        if API_TOKEN:
            h['Authorization'] = f'Token {API_TOKEN}'
        return h

    def refresh_list(self):
        try:
            resp = requests.get(f'{API_BASE}/datasets/', headers=self.headers(), timeout=15)
            resp.raise_for_status()
            self.list.clear()
            for item in resp.json():
                self.list.addItem(f"{item['id']}: {item.get('filename','')} ")
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load datasets: {e}')

    def upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Data File', '', 'Data Files (*.csv *.xlsx)')
        if not path: return
        try:
            with open(path, 'rb') as f:
                ext = os.path.splitext(path)[1].lower()
                mime = 'text/csv' if ext == '.csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                files = {'file': (os.path.basename(path), f, mime)}
                resp = requests.post(f'{API_BASE}/upload/', files=files, headers=self.headers(), timeout=30)
            if resp.status_code >= 400:
                QMessageBox.warning(self, 'Error', resp.text)
                return
            data = resp.json()
            self.summary_box.setPlainText(json.dumps(data['summary_json'], indent=2))
            self.plot_averages(data['summary_json'])
            self.refresh_list()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

    def plot_averages(self, summary):
        av = summary.get('averages', {})
        labels = list(av.keys())
        values = [av[k] for k in labels]
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(labels, values, color=['#3b82f6', '#10b981', '#f59e0b'])
        ax.set_title('Average Parameters')
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        # In a simple MVP we just save alongside the exe dir for quick view
        out_path = os.path.join(os.path.dirname(__file__), 'averages.png')
        with open(out_path, 'wb') as f: f.write(buf.read())
        plt.close(fig)

    def generate_pdf(self):
        current = self.list.currentItem()
        if not current:
            QMessageBox.information(self, 'Info', 'Select a dataset in the list')
            return
        dataset_id = current.text().split(':')[0]
        try:
            resp = requests.get(f'{API_BASE}/datasets/{dataset_id}/report/', headers=self.headers(), timeout=30)
            resp.raise_for_status()
            out_path, _ = QFileDialog.getSaveFileName(self, 'Save Report', f'dataset_{dataset_id}_report.pdf', 'PDF (*.pdf)')
            if out_path:
                with open(out_path, 'wb') as f:
                    f.write(resp.content)
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

    def open_health_overview(self):
        current = self.list.currentItem()
        if not current:
            QMessageBox.information(self, 'Info', 'Select a dataset in the list')
            return
        dataset_id = current.text().split(':')[0]
        try:
            resp = requests.get(f'{API_BASE}/datasets/{dataset_id}/health/', headers=self.headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load dashboard data: {e}')
            return

        # Build figures
        paths = []
        tmp = tempfile.gettempdir()

        # 1) Averages bar (all numeric)
        av = (data.get('summary') or {}).get('averages', {})
        if av:
            labels = list(av.keys()); values = [av[k] for k in labels]
            fig, ax = plt.subplots(figsize=(5,3))
            ax.bar(labels, values, color=['#2563eb','#16a34a','#fb923c','#a855f7','#06b6d4']*(len(labels)//5+1))
            ax.set_title('Averages (All Numeric Columns)')
            ax.tick_params(axis='x', rotation=30)
            p = os.path.join(tmp, f'ds_{dataset_id}_avg.png')
            fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
            paths.append(p)

        # 2) Clusters scatter (Flowrate vs Pressure)
        cl = data.get('clustering') or {}
        if cl.get('k', 0) > 0:
            rows_by_id = {r['Record']: r for r in (data.get('rows') or [])}
            sets = [[] for _ in range(cl['k'])]
            for idx, rec_id in enumerate(cl.get('rec_ids', [])):
                label = cl.get('labels', [0])[idx]
                r = rows_by_id.get(rec_id)
                if not r: continue
                x = r.get('Flowrate'); y = r.get('Pressure')
                if isinstance(x,(int,float)) and isinstance(y,(int,float)):
                    sets[label].append((x,y))
            fig, ax = plt.subplots(figsize=(5,3))
            colors = ['#2563eb','#16a34a','#fb923c','#a855f7']
            for i, pts in enumerate(sets):
                if not pts: continue
                xs, ys = zip(*pts)
                ax.scatter(xs, ys, s=20, color=colors[i%4], label=f'Cluster {i+1}')
            ax.set_xlabel('Flowrate'); ax.set_ylabel('Pressure'); ax.set_title('Clusters (K-Means)')
            ax.legend(loc='best')
            p = os.path.join(tmp, f'ds_{dataset_id}_clusters.png')
            fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
            paths.append(p)

        # 3) Correlation heatmap
        corr = data.get('correlations') or {}
        mat = corr.get('matrix') or []
        order = corr.get('order') or []
        if mat and order:
            fig, ax = plt.subplots(figsize=(max(4, len(order)*0.6), 4))
            cax = ax.imshow(mat, vmin=-1, vmax=1, cmap='coolwarm')
            ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=45, ha='right')
            ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
            ax.set_title('Correlation Heatmap')
            fig.colorbar(cax, ax=ax, shrink=0.8)
            p = os.path.join(tmp, f'ds_{dataset_id}_corr.png')
            fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
            paths.append(p)

        if not paths:
            QMessageBox.information(self, 'Info', 'No charts available for this dataset')
            return

        # Show dialog with images
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Dashboard Overview — Dataset {dataset_id}')
        vbox = QVBoxLayout()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        holder = QWidget(); hv = QVBoxLayout(holder)
        for p in paths:
            lbl = QLabel()
            lbl.setPixmap(QPixmap(p))
            hv.addWidget(lbl)
        scroll.setWidget(holder)
        vbox.addWidget(scroll)
        dlg.setLayout(vbox)
        dlg.resize(720, 560)
        dlg.exec_()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = App(); w.show()
    sys.exit(app.exec_())
