"""
Module to manage the CommitReport BarView
"""

from os import path

from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox,\
                            QTreeWidgetItem, QComboBox, QHeaderView
from PyQt5.QtCore import Qt

from varats.gui.views.ui_CRBarView import Ui_Form
from varats.data.data_manager import VDM
from varats.data.commit_report import CommitReport, CommitReportMeta, CommitMap


class CRBarView(QWidget, Ui_Form):
    """
    Bar view for commit reports
    """
    __GRP_CR = "CommitReport"
    __OPT_CR_MR = "Merge reports"
    __OPT_CR_RORDER = "Report Order"
    __OPT_CR_CMAP = "Commit map"

    __OPT_SCF = "Show CF graph"
    __OPT_SDF = "Show DF graph"

    def __init__(self):
        super(CRBarView, self).__init__()

        self.commit_reports = []
        self.commit_report_merged_meta = CommitReportMeta()
        self.current_report = None
        self.c_map = None
        self.loading_files = 0

        self.setupUi(self)
        self.plot_up.set_cf_plot(True)
        self.plot_up.hide()
        self.plot_down.set_cf_plot(False)
        self.plot_down.hide()

        self.loadCRButton.clicked.connect(self.load_commit_report)
        self.__setup_options()
        self.treeWidget.itemChanged.connect(self._update_option)

        self.fileSlider.sliderReleased.connect(self._slider_moved)
        self.fileSlider.setTickPosition(2)
        self._adjust_slider()

        self._update_report_order()

    def load_commit_report(self):
        """
        Load new CommitReport from file_path.
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Load CommitReport file", "",
            "Yaml Files (*.yaml *.yml);;All Files (*)", options=options)

        for file_path in file_paths:
            if not path.isfile(file_path):
                err = QMessageBox()
                err.setIcon(QMessageBox.Warning)
                err.setWindowTitle("File not found.")
                err.setText("Could not find selected file.")
                err.setStandardButtons(QMessageBox.Ok)
                err.exec_()
                return

            if not (file_path.endswith(".yaml")
                    or file_path.endswith(".yml")):
                err = QMessageBox()
                err.setIcon(QMessageBox.Warning)
                err.setWindowTitle("Wrong File ending.")
                err.setText("File seems not to be a yaml file.")
                err.setStandardButtons(QMessageBox.Ok)
                err.exec_()
                return

        for file_path in file_paths:
            skip = False
            for current_report in self.commit_reports:
                # skip files that were loaded bevor
                if current_report.path == file_path:
                    skip = True
                    continue
            if skip:
                continue
            self.loading_files += 1
            self.statusLabel.setText("Loading files... " +
                                     str(self.loading_files))
            VDM.load_data_class(file_path, CommitReport,
                                self._set_new_commit_report)

    def _update_option(self, item, col):
        text = item.text(0)
        if text == self.__OPT_CR_MR:
            self._draw_plots()
        elif text == self.__OPT_SCF:
            self.enable_cf_plot(item.checkState(1))
        elif text == self.__OPT_SDF:
            self.enable_df_plot(item.checkState(1))
        elif text == self.__OPT_CR_RORDER:
            self._update_report_order()
        elif text == self.__OPT_CR_CMAP:
            print(item.text(1))
            c_map_path = item.text(1)
            if path.isfile(c_map_path):
                self.c_map = CommitMap(c_map_path)
            else:
                self.c_map = None
            self._update_report_order()
        else:
            raise LookupError("Could not find matching option")

    def _set_new_commit_report(self, commit_report):
        self.loading_files -= 1

        if commit_report not in self.commit_reports:
            self.commit_reports.append(commit_report)
            self.commit_report_merged_meta.merge(commit_report)
            self._adjust_slider()

        if self.loading_files is 0:
            self.statusLabel.setText("")
        else:
            self.statusLabel.setText("Loading files... " +
                                     str(self.loading_files))

    def _draw_plots(self):
        if self.current_report is None:
            return
        meta = None
        if self.__get_mr_state() != Qt.Unchecked:
            meta = self.commit_report_merged_meta

        if self.__get_scf_state() != Qt.Unchecked:
            self.plot_up.update_plot(self.current_report, meta)
        if self.__get_sdf_state() != Qt.Unchecked:
            self.plot_down.update_plot(self.current_report, meta)

    def _adjust_slider(self):
        self.fileSlider.setMaximum(len(self.commit_reports) - 1)
        self._slider_moved()

    def _slider_moved(self):
        if len(self.commit_reports) >= 1:
            self.current_report = self\
                .commit_reports[self.fileSlider.value()]
            self._draw_plots()

    def enable_cf_plot(self, state: int):
        """
        Enable control-flow plot
        """
        if state == Qt.Unchecked:  # turned off
            self.plot_up.hide()
        else:
            self._draw_plots()
            self.plot_up.show()

    def enable_df_plot(self, state: int):
        """
        Enable data-flow plot
        """
        if state == Qt.Unchecked:  # turned off
            self.plot_down.hide()
        else:
            self._draw_plots()
            self.plot_down.show()

    def __setup_options(self):
        # Fixing header
        self.treeWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.treeWidget.header().setSectionResizeMode(1,
                                                      QHeaderView.Interactive)

        # Add QBox item so select order function
        items = self.treeWidget.findItems(self.__GRP_CR, Qt.MatchExactly)
        grp = items[0]
        drop_item = QTreeWidgetItem(grp)
        self.combo_box = QComboBox()
        self.combo_box.addItem("---")
        self.combo_box.addItem("Linear History")
        self.combo_box.currentIndexChanged.connect(self._update_report_order)
        self.treeWidget.setItemWidget(drop_item, 1, self.combo_box)
        drop_item.setText(0, self.__OPT_CR_RORDER)

    def _update_report_order(self, index: int = -1):
        if index == -1:
            text = self.combo_box.currentText()
        else:
            text = self.combo_box.itemText(index)

        if text == 'Linear History':
            def order_func(x):
                file_path = x.path
                filename = path.basename(file_path)
                c_hash = filename[5:-5]
                if self.c_map is not None:
                    return self.c_map.time_id(c_hash)
                return c_hash
        else:
            def order_func(x):
                return x

        self.commit_reports.sort(key=order_func)
        if self.current_report is not None:
            idx = self.commit_reports.index(self.current_report)
            self.fileSlider.setSliderPosition(idx)

    def __get_mr_state(self):
        items = self.treeWidget.findItems(self.__GRP_CR, Qt.MatchExactly)
        if not items:
            return Qt.Unchecked
        grp = items[0]
        for i in range(0, grp.childCount()):
            if grp.child(i).text(0) == self.__OPT_CR_MR:
                return grp.child(i).checkState(1)
        return Qt.Unchecked

    def __get_scf_state(self):
        items = self.treeWidget.findItems(self.__OPT_SCF, Qt.MatchExactly)
        if not items:
            return Qt.Unchecked
        return items[0].checkState(1)

    def __get_sdf_state(self):
        items = self.treeWidget.findItems(self.__OPT_SDF, Qt.MatchExactly)
        if not items:
            return Qt.Unchecked
        return items[0].checkState(1)
