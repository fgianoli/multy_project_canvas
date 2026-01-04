# -*- coding: utf-8 -*-
"""
Multi Project Canvas Plugin for QGIS v7
With i18n support (English/Italian)
"""


def classFactory(iface):
    from .multi_project_canvas import MultiProjectCanvasPlugin
    return MultiProjectCanvasPlugin(iface)
