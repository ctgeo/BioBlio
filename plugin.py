# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
import os

class ChargeurNaturalistePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dlg    = None

    def initGui(self):
        """Ajoute le bouton dans la barre d'outils et le menu QGIS."""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "🌿 Chargeur naturaliste", self.iface.mainWindow())
        self.action.setToolTip("Charger des données naturalistes par territoire")
        self.action.triggered.connect(self.run)

        # Ajouter dans le menu Extensions et dans la barre d'outils
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Chargeur naturaliste", self.action)

    def unload(self):
        """Supprime le bouton à la désactivation du plugin."""
        self.iface.removePluginMenu("&Chargeur naturaliste", self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dlg:
            self.dlg.close()

    def run(self):
        """Ouvre la fenêtre principale — réutilise si déjà ouverte."""
        from .dialog import ChargeurDonnees
        if self.dlg is None or not self.dlg.isVisible():
            self.dlg = ChargeurDonnees(self.iface)
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()
