#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Application that runs the landscape generator program.
"""
import sys
import json

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, \
    QAction, QSlider, QDialog, QLabel, QScrollArea, QSplitter, QFileDialog
from PySide2.QtGui import QIcon, QPainter, QPalette, QPixmap, QColor
from PySide2.QtCore import Qt, QTimer, QSize, QPoint


class TileSelector(QWidget):
    def __init__(self, tile_size, pixmap, main, parent=None):
        super(TileSelector, self).__init__(parent)

        self.main = main
        self.reset(tile_size, pixmap, 4.0)

    def reset(self, tile_size, pixmap, scale):
        self.tilemap_size = (pixmap.size().width() /
                             tile_size[0], pixmap.size().height() / tile_size[1])
        self.tile_size = tile_size
        self.pixmap = pixmap
        self.scale = scale

        self.setFixedSize(pixmap.size() * self.scale)
        self.setMaximumSize(pixmap.size() * self.scale)

    def sizeHint(self):
        return self.pixmap.size()

    def get_tile_map_coords(self, tile):
        x = (tile % self.tilemap_size[0]) * self.tile_size[0]
        y = (tile // self.tilemap_size[1]) * self.tile_size[1]
        return x, y

    def get_tile(self, x, y):
        tiles_horiz = self.pixmap.size().width() / self.tile_size[0]
        return int((y * tiles_horiz) + x)

    def paintEvent(self, event):
        """
        Redraw application.
        """
        super(TileSelector, self).paintEvent(event)

        painter = QPainter(self)

        painter.setPen(QColor(127, 127, 127))

        painter.drawPixmap(0, 0, self.pixmap.size().width(
        ) * self.scale, self.pixmap.size().height() * self.scale, self.pixmap)

        for y in range(0, self.pixmap.size().height(), self.tile_size[1]):
            for x in range(0, self.pixmap.size().width(), self.tile_size[0]):
                painter.drawRect(x * self.scale, y * self.scale,
                                 self.tile_size[0] * self.scale, self.tile_size[1] * self.scale)

        x, y = self.get_tile_map_coords(self.main.tile)
        painter.setPen(QColor(200, 0, 0))
        painter.drawRect(x * self.scale, y * self.scale,
                         self.tile_size[0] * self.scale, self.tile_size[1] * self.scale)

        painter.end()

    def mousePressEvent(self, event):
        x = int(event.localPos().x() // self.tile_size[0] // self.scale)
        y = int(event.localPos().y() // self.tile_size[1] // self.scale)
        self.main.tile = self.get_tile(x, y)
        self.update()
        return super().mousePressEvent(event)

    def encode_to_JSON(self):
        rdict = dict()
        rdict["scale"] = self.scale
        return rdict

    def decode_from_JSON(self, json, tile_size, pixmap):
        self.scale = json["scale"]
        self.reset(tile_size, pixmap, self.scale)


class TileEd(QWidget):
    def __init__(self, size, tile_size, pixmap, main, parent=None):
        super(TileEd, self).__init__(parent)

        self.main = main
        self.drawing = False

        self.reset(size, tile_size, pixmap, [0, ] * (size[0] * size[1]))

    def reset(self, size, tile_size, pixmap, data):
        self.size = size
        self.tile_size = tile_size
        self.pixmap = pixmap
        self.data = data
        self.tilemap_size = (pixmap.size().width() /
                             tile_size[0], pixmap.size().height() / tile_size[1])

        self.setFixedSize(
            self.size[0] * self.tile_size[0], self.size[1] * self.tile_size[1])
        self.setMaximumSize(
            self.size[0] * self.tile_size[0], self.size[1] * self.tile_size[1])

        self.update()

    def sizeHint(self):
        return QSize(self.size[0] * self.tile_size[0], self.size[1] * self.tile_size[1])

    def get_tile(self, x, y):
        return self.data[(y * self.size[0]) + x]

    def set_tile(self, x, y, value):
        self.data[(y * self.size[0]) + x] = value

    def get_tile_map_coords(self, tile):
        x = (tile % self.tilemap_size[0]) * self.tile_size[0]
        y = (tile // self.tilemap_size[1]) * self.tile_size[1]
        return x, y

    def paintEvent(self, event):
        """
        Redraw application.
        """
        super(TileEd, self).paintEvent(event)

        painter = QPainter(self)

        painter.setPen(QColor(127, 127, 127))

        for y in range(self.size[1]):
            for x in range(self.size[0]):
                tile = self.get_tile(x, y)
                posx, posy = self.get_tile_map_coords(tile)
                painter.drawPixmap(x * self.tile_size[0], y * self.tile_size[1],
                                   self.pixmap, posx, posy, self.tile_size[0], self.tile_size[1])
                painter.drawRect(
                    x * self.tile_size[0], y * self.tile_size[1], self.tile_size[0], self.tile_size[1])

        painter.end()

    def mousePressEvent(self, event):
        self.drawing = True
        x = int(event.localPos().x() // self.tile_size[0])
        y = int(event.localPos().y() // self.tile_size[1])
        self.set_tile(x, y, self.main.tile)
        self.update()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.drawing = False
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        x = int(event.localPos().x() // self.tile_size[0])
        y = int(event.localPos().y() // self.tile_size[1])
        self.set_tile(x, y, self.main.tile)
        self.update()
        return super().mouseMoveEvent(event)

    def encode_to_JSON(self):
        rdict = dict()
        rdict["data"] = self.data
        return rdict

    def decode_from_JSON(self, json, size, tile_size, pixmap):
        self.data = json["data"]
        self.reset(size, tile_size, pixmap, self.data)


class MainWindow(QMainWindow):
    """
    Main application entry-point for Genscape.
    """

    def __init__(self, size, tile_size, tile_image, parent=None):
        super(MainWindow, self).__init__(parent)

        self.reset(size, tile_size, tile_image, 0)
        self.home()

    def reset(self, size, tile_size, tile_image, tile):
        self.tile_image = tile_image
        self.size = size
        self.tile_size = tile_size
        self.pixmap = QPixmap(tile_image)
        self._tile = tile
        self.update()

    def home(self):
        """
        Add the GUI elements to the window that represent the home state of the application.
        """
        toolbar = self.addToolBar("File")
        save = QAction(QIcon("icon_save.png"), "Save", self)
        toolbar.addAction(save)
        load = QAction(QIcon("icon_load.png"), "Load", self)
        toolbar.addAction(load)
        toolbar.addSeparator()
        undo = QAction(QIcon("icon_undo.png"), "Undo", self)
        toolbar.addAction(undo)
        redo = QAction(QIcon("icon_redo.png"), "Redo", self)
        toolbar.addAction(redo)
        toolbar.actionTriggered[QAction].connect(self.toolbar_pressed)

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setHandleWidth(16)

        self.tile_ed = TileEd(self.size, self.tile_size,
                              self.pixmap, self)
        scroll_area_tile_ed = QScrollArea()
        scroll_area_tile_ed.setBackgroundRole(QPalette.Dark)
        scroll_area_tile_ed.setWidgetResizable(True)
        scroll_area_tile_ed.setWidget(self.tile_ed)

        splitter.addWidget(scroll_area_tile_ed)

        self.tile_sel = TileSelector(self.tile_size, self.pixmap, self)
        scroll_area_tile_sel = QScrollArea()
        scroll_area_tile_sel.setBackgroundRole(QPalette.Dark)
        scroll_area_tile_sel.setWidgetResizable(True)
        scroll_area_tile_sel.setWidget(self.tile_sel)

        splitter.addWidget(scroll_area_tile_sel)
        self.setCentralWidget(splitter)

    def toolbar_pressed(self, action):
        """
        Handle a button being pressed on the toolbar.
        """
        actions = {"Save": self.save, "Load": self.load,
                   "Undo": self.undo, "Redo": self.redo}
        actions[action.text()]()

    def save(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save tilemap to file", ".", "JSON file (*.json)")
        if filename[0]:
            with open(filename[0], "w") as output:
                json.dump(self.encode_to_JSON(), output, indent=4)

    def load(self):
        filename = QFileDialog.getOpenFileName(
            self, "Open a tilemap file", ".", "JSON file (*.json)")
        if filename[0]:
            with open(filename[0], "r") as input:
                self.decode_from_JSON(json.load(input))

    def undo(self):
        pass

    def redo(self):
        pass

    def encode_to_JSON(self):
        rdict = dict()
        rdict["width"] = self.size[0]
        rdict["height"] = self.size[1]
        rdict["tile_width"] = self.tile_size[0]
        rdict["tile_height"] = self.tile_size[1]
        rdict["selected_tile"] = self.tile
        rdict["tile_image"] = self.tile_image
        rdict["tile_data"] = self.tile_ed.encode_to_JSON()
        rdict["tile_sel"] = self.tile_sel.encode_to_JSON()
        return rdict

    def decode_from_JSON(self, json):
        self.size = (json["width"], json["height"])
        self.tile_size = (json["tile_width"], json["tile_height"])
        self.tile = json["selected_tile"]
        self.tile_image = json["tile_image"]
        self.reset(self.size, self.tile_size, self.tile_image, self.tile)
        self.tile_ed.decode_from_JSON(
            json["tile_data"], self.size, self.tile_size, self.pixmap)
        self.tile_sel.decode_from_JSON(
            json["tile_sel"], self.tile_size, self.pixmap)

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, value):
        self._tile = value


if __name__ == "__main__":
    # Create the Qt Application
    APP = QApplication(sys.argv)
    # Create and show the form
    MAIN = MainWindow((64, 64), (16, 16), "map_tiles.png")
    MAIN.show()
    # Run the main Qt loop
    sys.exit(APP.exec_())
