# -*- coding: utf-8 -*-
def classFactory(iface):
    from .plugin import BioBlio
    return BioBlio(iface)
