# -*- coding: utf-8 -*-
# BioBlio — Plugin QGIS
# Auteur : Thomas Clapasson
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
import os

class BioBlio:
    """Classe principale du plugin BioBlio enregistrée auprès de QGIS."""

    def __init__(self, iface):
        self.iface  = iface
        self.action = None
        self.dlg    = None

    def initGui(self):
        """Crée le bouton dans la barre d'outils et le menu Extensions."""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "BioBlio", self.iface.mainWindow())
        self.action.setToolTip(
            "BioBlio — Chargeur de données naturalistes\n"
            "ZNIEFF · Natura 2000 · GBIF · Cadastre · Urbanisme"
        )
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&BioBlio", self.action)

    def unload(self):
        """Nettoie le bouton et ferme la fenêtre à la désactivation."""
        self.iface.removePluginMenu("&BioBlio", self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dlg:
            self.dlg.close()

    def run(self):
        """Ouvre la fenêtre BioBlio — la réutilise si elle est déjà ouverte."""
        from .dialog import ChargeurDonnees
        if self.dlg is None or not self.dlg.isVisible():
            self.dlg = ChargeurDonnees()
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()
