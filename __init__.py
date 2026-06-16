# -*- coding: utf-8 -*-
def classFactory(iface):
    from .plugin import ChargeurNaturalistePlugin
    return ChargeurNaturalistePlugin(iface)
