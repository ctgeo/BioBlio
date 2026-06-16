# =============================================================================
# Chargeur de données naturalistes — Plugin QGIS
# Structure : plugin (iface passé en paramètre)
# Usage     : importer ChargeurDonnees depuis le __init__.py du plugin
#             dlg = ChargeurDonnees(iface); dlg.show()
# =============================================================================

import requests
import processing
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QPushButton, QCheckBox, QScrollArea,
    QWidget, QMessageBox, QProgressBar, QFrame, QApplication,
    QCompleter
)
from qgis.PyQt.QtCore import Qt, QStringListModel
from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (
    QgsVectorLayer, QgsProject,
    QgsLayerTreeGroup, QgsLayerTreeLayer,
    QgsLinePatternFillSymbolLayer,
    QgsFillSymbol, QgsLineSymbol, QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer, QgsSimpleLineSymbolLayer,
    QgsUnitTypes
)

WFS_GPF   = "https://data.geopf.fr/wfs/ows"
WFS_SAND  = "https://services.sandre.eaufrance.fr/geo/sandre"
WFS_RPDZH = "http://wms.reseau-zones-humides.org/cgi-bin/wmsfma"
GBIF_API  = "https://api.gbif.org/v1/occurrence/search"
MM        = QgsUnitTypes.RenderMillimeters
API_CARTO_CADASTRE = "https://apicarto.ign.fr/api/cadastre/parcelle"

GBIF_GROUPES = [
    ("Tous groupes",    None),
    ("🦋 Insectes",     216),
    ("🌿 Plantes",      6),
    ("🐦 Oiseaux",      212),
    ("🦇 Chiroptères",  734),
    ("🐾 Mammifères",   359),
    ("🐸 Amphibiens",   131),
    ("🦎 Reptiles",     358),
    ("🐟 Poissons",     204),
    ("🦀 Crustacés",    229),
    ("🐌 Mollusques",   52),
    ("🍄 Champignons",  5),
    ("🌾 Bryophytes",   35),
    ("🦟 Arachnides",   367),
]

# (Catégorie, Nom affiché, typename WFS, serveur, fill_rgba, stroke_hex)
CATALOGUE = [
    ("🛡 Zonages réglementaires", "🔴 ZNIEFF Type 1",
     "patrinat_znieff1:znieff1",        WFS_GPF,  "255,130,0,100",  "#CC5000"),
    ("🛡 Zonages réglementaires", "🟠 ZNIEFF Type 2",
     "patrinat_znieff2:znieff2",        WFS_GPF,  "240,200,60,90",  "#9A7A00"),
    ("🛡 Zonages réglementaires", "🟢 Natura 2000 — ZSC (Habitats)",
     "patrinat_sic:sic",                WFS_GPF,  "34,139,34,100",  "#006400"),
    ("🛡 Zonages réglementaires", "🔵 Natura 2000 — ZPS (Oiseaux)",
     "patrinat_zps:zps",                WFS_GPF,  "30,100,210,110", "#002299"),
    ("🛡 Zonages réglementaires", "🟣 Réserves Naturelles Nationales",
     "patrinat_rnn:rnn",                WFS_GPF,  "180,0,200,90",   "#800090"),
    ("🛡 Zonages réglementaires", "🪻 Réserves Naturelles Régionales",
     "patrinat_rnr:rnr",                WFS_GPF,  "200,50,200,90",  "#900070"),
    ("🛡 Zonages réglementaires", "🌲 Parcs Naturels Régionaux",
     "patrinat_pnr:pnr",                WFS_GPF,  "100,180,100,80", "#2A7A2A"),
    ("🛡 Zonages réglementaires", "🌿 Arrêtés Protection Biotope",
     "patrinat_apb:apb",                WFS_GPF,  "255,200,50,90",  "#AA7000"),
    ("🛡 Zonages réglementaires", "🍃 Conservatoires Espaces Naturels",
     "patrinat_cen:cen",                WFS_GPF,  "50,200,150,90",  "#007755"),
    ("💧 Données eau", "🔷 Cours d'eau L214-17 — Liste 1",
     "sa:SegClassContinuiteEcoListe1_FXX", WFS_SAND, None,          "#08519C"),
    ("💧 Données eau", "🔹 Cours d'eau L214-17 — Liste 2",
     "sa:SegClassContinuiteEcoListe2_FXX", WFS_SAND, None,          "#3182BD"),
    ("💧 Données eau", "🌊 SAGE",
     "sa:Sage_FXX",                     WFS_SAND, "100,180,230,55", "#0A4FA8"),
    ("💧 Zones humides", "💧 Zones humides d'importance majeure — RPDZH",
     "ZHIM",                            WFS_RPDZH, "50,160,220,80", "#006699"),
    ("💧 Zones humides", "🦆 Sites Ramsar — périmètres",
     "patrinat_ramsar:pnm",             WFS_GPF,  "30,120,200,70",  "#004C99"),
    ("📐 Limites administratives", "🏘 Communes",
     "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:commune",     WFS_GPF, "255,255,255,0", "#888888"),
    ("📐 Limites administratives", "🗺 Départements",
     "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:departement", WFS_GPF, "255,255,255,0", "#444444"),
    ("📐 Limites administratives", "📍 Régions",
     "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:region",      WFS_GPF, "255,255,255,0", "#222222"),
    ("🏙 Urbanisme (GPU)", "🟦 Zones PLU / Cartes communales",
     "wfs_du:zone_urba|COMMUNE_ONLY", WFS_GPF, "30,144,255,50", "#0050AA"),
    ("🏙 Urbanisme (GPU)", "🌲 Espaces Boisés Classés (EBC)",
     "wfs_du:prescription_surf|typepsc=01|COMMUNE_ONLY",
                                   WFS_GPF, "34,139,34,70",   "#005000"),
    ("🏙 Urbanisme (GPU)", "🌿 Éléments paysagers à préserver",
     "wfs_du:prescription_surf|typepsc=07|stypepsc=00,02,04|COMMUNE_ONLY",
                                   WFS_GPF, "144,238,144,70", "#2E8B00"),
    ("🏙 Urbanisme (GPU)", "🌳 Arbres / éléments naturels ponctuels à préserver",
     "wfs_du:prescription_pct|typepsc=07|stypepsc=04,05|COMMUNE_ONLY",
                                   WFS_GPF, None, "#1B7F3A"),
    ("🧾 Cadastre", "🧾 Parcelles cadastrales",
     "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle",
                                   WFS_GPF, "255,255,255,0", "#CC00CC"),
    ("🧾 Cadastre", "🏠 Bâtiments cadastraux",
     "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:batiment",
                                   WFS_GPF, "160,160,160,90", "#555555"),
]


def apply_style(lyr, fill_rgba, stroke_hex, width=0.4):
    nom = lyr.name()
    MM  = QgsUnitTypes.RenderMillimeters

    from qgis.core import (QgsLinePatternFillSymbolLayer,
                            QgsSimpleFillSymbolLayer, QgsSimpleLineSymbolLayer)
    from qgis.PyQt.QtCore import Qt

    if "znieff" in nom.lower() and ("type 1" in nom.lower() or "znieff1" in nom.lower()):
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setBrushStyle(Qt.NoBrush)
        fl.setStrokeColor(QColor("#AA1100"))
        fl.setStrokeWidth(0.55); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "znieff" in nom.lower() and ("type 2" in nom.lower() or "znieff2" in nom.lower()):
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        for angle in [45.0, 135.0]:
            h = QgsLinePatternFillSymbolLayer()
            h.setColor(QColor("#CC6600"))
            h.setLineWidth(0.20); h.setLineWidthUnit(MM)
            h.setLineAngle(angle)
            h.setDistance(2.5); h.setDistanceUnit(MM)
            sym.appendSymbolLayer(h)
        fl = QgsSimpleFillSymbolLayer()
        fl.setBrushStyle(Qt.NoBrush)
        fl.setStrokeColor(QColor("#884400"))
        fl.setStrokeWidth(0.40); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "zsc" in nom.lower() or "sic" in nom.lower() or "habitats" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setFillColor(QColor(34, 139, 34, 70))
        fl.setStrokeColor(QColor("#005000"))
        fl.setStrokeWidth(0.35); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "zps" in nom.lower() or "oiseaux" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        h = QgsLinePatternFillSymbolLayer()
        h.setColor(QColor("#1050CC"))
        h.setLineWidth(0.20); h.setLineWidthUnit(MM)
        h.setLineAngle(45.0)
        h.setDistance(2.0); h.setDistanceUnit(MM)
        sym.appendSymbolLayer(h)
        fl = QgsSimpleFillSymbolLayer()
        fl.setBrushStyle(Qt.NoBrush)
        fl.setStrokeColor(QColor("#002299"))
        fl.setStrokeWidth(0.50); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "sage" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        h = QgsLinePatternFillSymbolLayer()
        h.setColor(QColor("#2171B5"))
        h.setLineWidth(0.20); h.setLineWidthUnit(MM)
        h.setLineAngle(0.0)
        h.setDistance(2.5); h.setDistanceUnit(MM)
        sym.appendSymbolLayer(h)
        fl = QgsSimpleFillSymbolLayer()
        fl.setBrushStyle(Qt.NoBrush)
        fl.setStrokeColor(QColor("#08306B"))
        fl.setStrokeWidth(0.50); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "liste1" in nom.lower() or "liste 1" in nom.lower():
        sym = QgsLineSymbol()
        sym.deleteSymbolLayer(0)
        sl = QgsSimpleLineSymbolLayer()
        sl.setColor(QColor("#08519C"))
        sl.setWidth(0.60); sl.setWidthUnit(MM)
        sl.setPenStyle(Qt.SolidLine)
        sym.appendSymbolLayer(sl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "liste2" in nom.lower() or "liste 2" in nom.lower():
        sym = QgsLineSymbol()
        sym.deleteSymbolLayer(0)
        sl = QgsSimpleLineSymbolLayer()
        sl.setColor(QColor("#3182BD"))
        sl.setWidth(0.45); sl.setWidthUnit(MM)
        sl.setPenStyle(Qt.DashLine)
        sym.appendSymbolLayer(sl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "zones humides" in nom.lower() or "rpdzh" in nom.lower() or "zhim" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setFillColor(QColor(50, 160, 220, 80))
        fl.setStrokeColor(QColor("#006699"))
        fl.setStrokeWidth(0.35); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "ramsar" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setFillColor(QColor(30, 120, 200, 70))
        fl.setStrokeColor(QColor("#004C99"))
        fl.setStrokeWidth(0.45); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "parcelles cadastrales" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setBrushStyle(Qt.NoBrush)
        fl.setStrokeColor(QColor("#252425D5"))
        fl.setStrokeWidth(0.18); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    elif "bâtiments cadastraux" in nom.lower() or "batiments cadastraux" in nom.lower():
        sym = QgsFillSymbol()
        sym.deleteSymbolLayer(0)
        fl = QgsSimpleFillSymbolLayer()
        fl.setFillColor(QColor(160, 160, 160, 90))
        fl.setStrokeColor(QColor("#555555"))
        fl.setStrokeWidth(0.15); fl.setStrokeWidthUnit(MM)
        sym.appendSymbolLayer(fl)
        lyr.setRenderer(QgsSingleSymbolRenderer(sym))

    else:
        if lyr.geometryType() == 2:
            sym = QgsFillSymbol()
            sym.deleteSymbolLayer(0)
            fl = QgsSimpleFillSymbolLayer()
            if fill_rgba:
                r, g, b, a = [int(x) for x in fill_rgba.split(',')]
                fl.setFillColor(QColor(r, g, b, a))
            else:
                fl.setBrushStyle(Qt.NoBrush)
            fl.setStrokeColor(QColor(stroke_hex))
            fl.setStrokeWidth(width); fl.setStrokeWidthUnit(MM)
            sym.appendSymbolLayer(fl)
            lyr.setRenderer(QgsSingleSymbolRenderer(sym))
        elif lyr.geometryType() == 1:
            sym = QgsLineSymbol()
            sym.deleteSymbolLayer(0)
            sl = QgsSimpleLineSymbolLayer()
            sl.setColor(QColor(stroke_hex))
            sl.setWidth(0.5); sl.setWidthUnit(MM)
            sym.appendSymbolLayer(sl)
            lyr.setRenderer(QgsSingleSymbolRenderer(sym))
        elif lyr.geometryType() == 0:
            from qgis.core import QgsMarkerSymbol, QgsSimpleMarkerSymbolLayer
            sym = QgsMarkerSymbol()
            sym.deleteSymbolLayer(0)
            mk = QgsSimpleMarkerSymbolLayer()
            mk.setShape(QgsSimpleMarkerSymbolLayer.Shape.Circle)
            mk.setSize(2.2); mk.setSizeUnit(MM)
            mk.setColor(QColor("#2ECC71"))
            mk.setStrokeColor(QColor(stroke_hex))
            mk.setStrokeWidth(0.25); mk.setStrokeWidthUnit(MM)
            sym.appendSymbolLayer(mk)
            sym.setOpacity(0.85)
            lyr.setRenderer(QgsSingleSymbolRenderer(sym))


def build_wfs_uri(serveur, typename_raw, bbox_str=None):
    """Retourne (uri, filtre_expression, is_gpu).
    Format typename : 'typename' ou 'typename|champ=val|COMMUNE_ONLY'
    """
    parts    = typename_raw.split("|")
    typename = parts[0]
    is_gpu   = "GPU" in parts or "COMMUNE_ONLY" in parts

    filtres = []
    for part in parts[1:]:
        if '=' not in part:
            continue
        champ, vals = part.split("=", 1)
        val_list = vals.split(",")
        if len(val_list) == 1:
            filtres.append(f'"{champ}" = \'{val_list[0]}\'')
        else:
            in_vals = ", ".join(f"'{v}'" for v in val_list)
            filtres.append(f'"{champ}" IN ({in_vals})')

    filtre_expr = " AND ".join(filtres)

    if bbox_str:
        uri = (f"url='{serveur}' typename='{typename}' version='auto' "
               f"srsname='EPSG:4326' restrictToRequestBBOX='1' "
               f"bbox='{bbox_str},EPSG:4326'")
    else:
        uri = (f"url='{serveur}' typename='{typename}' version='auto' "
               f"srsname='EPSG:4326' restrictToRequestBBOX='0'")

    return uri, filtre_expr, is_gpu


def layer_has_features(lyr):
    if not lyr or not lyr.isValid():
        return False
    try:
        return next(lyr.getFeatures(), None) is not None
    except Exception:
        return False


def exclude_from_excel(nom):
    nom_lower = nom.lower()
    return (
        "parcelles cadastrales" in nom_lower
        or "bâtiments cadastraux" in nom_lower
        or "batiments cadastraux" in nom_lower
    )


def load_cadastre_parcelles_api(lyr_territoire, nom, lbl_status, app, code_insee=None):
    """Charge les parcelles cadastrales via API Carto (pagination parallèle)."""
    import json, os, tempfile, requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from qgis.core import QgsGeometry, QgsVectorLayer

    PAGE_SIZE   = 1000
    MAX_WORKERS = 6

    def build_geom_params():
        if not lyr_territoire:
            return None
        lbl_status.setText("Cadastre — préparation de la géométrie...")
        app.processEvents()
        geoms = [f.geometry() for f in lyr_territoire.getFeatures() if f.hasGeometry()]
        if not geoms:
            return None
        geom = QgsGeometry.unaryUnion(geoms)
        geom = geom.simplify(0.00002)
        geom_json = json.loads(geom.asJson(6))
        return {"geom": json.dumps(geom_json, separators=(",", ":"))}

    def fetch_page(base_params, start):
        params = dict(base_params)
        if start > 0:
            params["_start"] = start
        try:
            r = requests.get(API_CARTO_CADASTRE, params=params, timeout=60)
            if r.status_code == 200:
                return start, r.json().get("features", [])
            return start, None
        except Exception:
            return start, []

    param_sets = []
    if code_insee:
        param_sets.append((f"commune {code_insee}", {"code_insee": code_insee}))
    geom_params = build_geom_params()
    if geom_params:
        param_sets.append(("géométrie", geom_params))
    if not param_sets:
        return None

    all_features = []

    for mode_label, base_params in param_sets:
        lbl_status.setText(f"Cadastre — {mode_label} (page 0) ...")
        app.processEvents()
        _, first_page = fetch_page(base_params, 0)
        if not first_page:
            continue
        all_features = list(first_page)
        if len(first_page) < PAGE_SIZE:
            break

        offset = PAGE_SIZE
        while True:
            starts = [offset + i * PAGE_SIZE for i in range(MAX_WORKERS)]
            lbl_status.setText(
                f"Cadastre — {mode_label} ({len(all_features)} récupérées"
                f", pages {offset}–{starts[-1]+PAGE_SIZE}) ...")
            app.processEvents()
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(fetch_page, base_params, s): s for s in starts}
                results = {}
                for future in as_completed(futures):
                    s, feats = future.result()
                    results[s] = feats if feats is not None else []
            done = False
            for s in sorted(starts):
                feats = results.get(s, [])
                all_features.extend(feats)
                if len(feats) < PAGE_SIZE:
                    done = True
                    break
            if done:
                break
            offset += MAX_WORKERS * PAGE_SIZE
        break

    if not all_features:
        return None

    fc = {"type": "FeatureCollection", "features": all_features}
    fd, path = tempfile.mkstemp(prefix="cadastre_parcelles_", suffix=".geojson")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f)
    lyr = QgsVectorLayer(path, nom, "ogr")
    return lyr if lyr.isValid() else None


def load_gpu_layer(typename_raw, filtre_expr, lyr_territoire, nom, lbl_status, app):
    """Charge une couche GPU via filtre OGC XML par partition (code INSEE commune)."""
    from qgis.core import QgsFeatureRequest, QgsExpression

    parts    = typename_raw.split("|")
    typename = parts[0]

    lbl_status.setText(f"GPU — communes pour {nom}...")
    app.processEvents()

    ext  = lyr_territoire.extent()
    mx   = ext.width()  * 0.02
    my   = ext.height() * 0.02
    bbox = (f"{ext.xMinimum()-mx},{ext.yMinimum()-my},"
            f"{ext.xMaximum()+mx},{ext.yMaximum()+my}")

    uri_comm = (f"url='{WFS_GPF}' "
                f"typename='LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:commune' "
                f"version='1.1.0' srsname='EPSG:4326' restrictToRequestBBOX='1' "
                f"bbox='{bbox},EPSG:4326'")
    lyr_comm = QgsVectorLayer(uri_comm, "communes_tmp", "WFS")
    if not lyr_comm.isValid():
        return None

    import processing
    try:
        comm_clipped = processing.run("native:clip", {
            'INPUT': lyr_comm, 'OVERLAY': lyr_territoire, 'OUTPUT': 'memory:'
        })['OUTPUT']
    except Exception:
        comm_clipped = lyr_comm

    codes_insee = sorted(set(
        str(f['code_insee'])
        for f in comm_clipped.getFeatures()
        if f['code_insee']
    ))

    lbl_status.setText(f"GPU — codes INSEE trouvés : {codes_insee} | {nom}")
    app.processEvents()

    if not codes_insee:
        lbl_status.setText(f"⚠ {nom} : aucun code INSEE trouvé dans le territoire")
        app.processEvents()
        return None

    lbl_status.setText(f"GPU — {len(codes_insee)} communes | {nom}...")
    app.processEvents()

    all_feats  = []
    ref_fields = None
    ref_crs    = None
    ref_geom   = None
    batch_size = 50

    for i in range(0, len(codes_insee), batch_size):
        batch = codes_insee[i:i+batch_size]

        if len(batch) == 1:
            filtre_partition = (
                f"<PropertyIsEqualTo>"
                f"<PropertyName>partition</PropertyName>"
                f"<Literal>DU_{batch[0]}</Literal>"
                f"</PropertyIsEqualTo>"
            )
        else:
            conditions = "".join(
                f"<PropertyIsEqualTo>"
                f"<PropertyName>partition</PropertyName>"
                f"<Literal>DU_{code}</Literal>"
                f"</PropertyIsEqualTo>"
                for code in batch
            )
            filtre_partition = f"<Or>{conditions}</Or>"

        filtre_ogc = f"<Filter>{filtre_partition}</Filter>"
        uri_batch  = (f"url='{WFS_GPF}' typename='{typename}' version='1.1.0' "
                      f"srsname='EPSG:4326' filter='{filtre_ogc}'")
        lyr_batch  = QgsVectorLayer(uri_batch, "gpu_batch", "WFS")

        if not lyr_batch.isValid():
            continue

        if ref_fields is None:
            ref_fields = lyr_batch.fields().toList()
            ref_crs    = lyr_batch.crs().authid()
            if lyr_batch.geometryType() == 0:
                ref_geom = "Point"
            elif lyr_batch.geometryType() == 1:
                ref_geom = "LineString"
            else:
                ref_geom = "Polygon"

        if filtre_expr:
            expr    = QgsExpression(filtre_expr)
            request = QgsFeatureRequest(expr)
            feats   = list(lyr_batch.getFeatures(request))
        else:
            feats = list(lyr_batch.getFeatures())

        if not feats:
            continue

        all_feats.extend(feats)
        lbl_status.setText(
            f"GPU — lot {i//batch_size+1}/{(len(codes_insee)-1)//batch_size+1} "
            f"| {len(all_feats)} entités | {nom}")
        app.processEvents()

    if not all_feats or ref_fields is None:
        lbl_status.setText(
            f"ℹ {nom} : aucune donnée — commune(s) sans PLU numérique sur le GPU")
        app.processEvents()
        return None

    lyr_result = QgsVectorLayer(f"{ref_geom}?crs={ref_crs}", nom, "memory")
    pr = lyr_result.dataProvider()
    pr.addAttributes(ref_fields)
    lyr_result.updateFields()
    pr.addFeatures(all_feats)
    lyr_result.updateExtents()
    return lyr_result


# =============================================================================
# Dialogue principal — structure plugin QGIS
# =============================================================================

class ChargeurDonnees(QDialog):
    def __init__(self, iface):
        self.iface = iface
        super().__init__(iface.mainWindow())
        self.setWindowTitle("Chargeur de données naturalistes")
        self.setMinimumWidth(540)
        self.setMinimumHeight(900)
        self._territory_extent = None
        self._territory_lyr    = None
        self._territory_code   = None
        self._suggestions      = {}
        self._heavy_layer_rules = {
            "🧾 Parcelles cadastrales": ["Département", "Région", "France entière"],
            "🏠 Bâtiments cadastraux": ["Département", "Région", "France entière"],
            "🟦 Zones PLU / Cartes communales": ["Région", "France entière"],
            "🌲 Espaces Boisés Classés (EBC)": ["Région", "France entière"],
            "🌿 Éléments paysagers à préserver": ["Région", "France entière"],
            "🌳 Arbres / éléments naturels ponctuels à préserver": ["Région", "France entière"],
        }
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        global_scroll = QScrollArea()
        global_scroll.setWidgetResizable(True)
        global_scroll.setFrameShape(QFrame.NoFrame)
        scroll_container = QWidget()
        main = QVBoxLayout(scroll_container)
        main.setSpacing(10)
        main.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Chargeur de données naturalistes")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#1F4E79; padding:8px;")
        main.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#CCCCCC")
        main.addWidget(sep)

        # ── 1. Échelle géographique ───────────────────────────────────────
        grp_scale = QGroupBox("1. Échelle géographique")
        grp_scale.setStyleSheet("QGroupBox{font-weight:bold;}")
        lay_scale = QVBoxLayout(grp_scale)

        self.combo_scale = QComboBox()
        self.combo_scale.addItems([
            "Commune", "Département", "Région", "France entière", "Zone personnalisée"
        ])
        self.combo_scale.currentIndexChanged.connect(self._on_scale_change)
        lay_scale.addWidget(self.combo_scale)

        lay_search = QHBoxLayout()
        self.lbl_search = QLabel("Nom de la commune :")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("ex: Tours, Blois, Issoudun...")
        self._completer_model = QStringListModel()
        self._completer = QCompleter()
        self._completer.setModel(self._completer_model)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self.txt_search.setCompleter(self._completer)
        self.txt_search.textChanged.connect(self._on_text_changed)

        self.btn_search = QPushButton("Rechercher")
        self.btn_search.setStyleSheet(
            "background:#E8F4FD; border:1px solid #3182BD; padding:4px 8px;")
        self.btn_search.clicked.connect(self._search_territory)

        self.btn_browse = QPushButton("📂 Fichier...")
        self.btn_browse.setStyleSheet(
            "background:#FFF3E0; border:1px solid #E65100; padding:4px 8px;")
        self.btn_browse.clicked.connect(self._browse_zone)
        self.btn_browse.setVisible(False)

        self.btn_from_layer = QPushButton("🗂 Projet...")
        self.btn_from_layer.setStyleSheet(
            "background:#E8F5E9; border:1px solid #2E7D32; padding:4px 8px;")
        self.btn_from_layer.clicked.connect(self._use_project_layer)
        self.btn_from_layer.setVisible(False)

        lay_search.addWidget(self.lbl_search)
        lay_search.addWidget(self.txt_search)
        lay_search.addWidget(self.btn_search)
        lay_search.addWidget(self.btn_browse)
        lay_search.addWidget(self.btn_from_layer)
        lay_scale.addLayout(lay_search)

        lay_layer_pick = QHBoxLayout()
        self.combo_layers = QComboBox()
        self.combo_layers.setMinimumWidth(300)
        self.combo_layers.setVisible(False)
        lay_layer_pick.addWidget(self.combo_layers)
        lay_layer_pick.addStretch()
        lay_scale.addLayout(lay_layer_pick)

        # Buffer
        self.chk_buffer = QCheckBox("Appliquer un buffer autour du territoire")
        self.chk_buffer.setChecked(False)
        self.chk_buffer.stateChanged.connect(self._on_buffer_toggle)
        lay_scale.addWidget(self.chk_buffer)

        self.buffer_widget = QWidget()
        lay_buffer = QHBoxLayout(self.buffer_widget)
        lay_buffer.setContentsMargins(0, 0, 0, 0)
        lay_buffer.addWidget(QLabel("Taille :"))
        self.txt_buffer_size = QLineEdit()
        self.txt_buffer_size.setPlaceholderText("ex: 10")
        self.txt_buffer_size.setFixedWidth(70)
        lay_buffer.addWidget(self.txt_buffer_size)
        self.combo_buffer_unit = QComboBox()
        self.combo_buffer_unit.addItems(["Kilomètres", "Mètres"])
        self.combo_buffer_unit.setFixedWidth(110)
        lay_buffer.addWidget(self.combo_buffer_unit)
        lay_buffer.addStretch()
        self.buffer_widget.setVisible(False)
        lay_scale.addWidget(self.buffer_widget)

        self.chk_intersect_only = QCheckBox(
            "Récupérer les entités entières (intersection sans découpage)")
        self.chk_intersect_only.setChecked(False)
        self.chk_intersect_only.setToolTip(
            "Coché : entités qui touchent le territoire chargées entières\n"
            "Décoché : entités découpées exactement sur le contour")
        lay_scale.addWidget(self.chk_intersect_only)

        self.lbl_result = QLabel("")
        self.lbl_result.setStyleSheet("color:#2A7A2A; font-style:italic; padding:2px;")
        lay_scale.addWidget(self.lbl_result)
        main.addWidget(grp_scale)

        # ── 2. Données à charger ──────────────────────────────────────────
        grp_data = QGroupBox("2. Données à charger")
        grp_data.setStyleSheet("QGroupBox{font-weight:bold;}")
        lay_data = QVBoxLayout(grp_data)

        lay_btns = QHBoxLayout()
        btn_all  = QPushButton("Tout cocher")
        btn_none = QPushButton("Tout décocher")
        btn_all.clicked.connect(lambda: self._check_all(True))
        btn_none.clicked.connect(lambda: self._check_all(False))
        btn_all.setStyleSheet("padding:3px 8px;")
        btn_none.setStyleSheet("padding:3px 8px;")
        lay_btns.addWidget(btn_all)
        lay_btns.addWidget(btn_none)
        lay_btns.addStretch()
        lay_data.addLayout(lay_btns)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        scroll.setMaximumHeight(280)
        scroll_widget  = QWidget()
        scroll_layout  = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(4)

        self.checkboxes = {}
        current_cat = None
        for cat, nom, *_ in CATALOGUE:
            if cat != current_cat:
                lbl_cat = QLabel(cat)
                lbl_cat.setFont(QFont("Arial", 9, QFont.Bold))
                lbl_cat.setStyleSheet("color:#555; padding-top:6px;")
                scroll_layout.addWidget(lbl_cat)
                current_cat = cat
            cb = QCheckBox(f"  {nom}")
            cb.setChecked(False)
            cb.setStyleSheet("padding-left:12px;")
            self.checkboxes[nom] = cb
            scroll_layout.addWidget(cb)

        self._update_layer_availability()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        lay_data.addWidget(scroll)
        main.addWidget(grp_data)

        # ── 3. Options ────────────────────────────────────────────────────
        grp_opt = QGroupBox("3. Options")
        grp_opt.setStyleSheet("QGroupBox{font-weight:bold;}")
        lay_opt = QVBoxLayout(grp_opt)
        self.chk_clip  = QCheckBox("Découper les couches sur le territoire sélectionné")
        self.chk_style = QCheckBox("Appliquer la symbologie automatiquement")
        self.chk_group = QCheckBox("Regrouper les couches dans un groupe nommé")
        self.chk_clip.setChecked(True)
        self.chk_style.setChecked(True)
        self.chk_group.setChecked(True)
        lay_opt.addWidget(self.chk_clip)
        lay_opt.addWidget(self.chk_style)
        lay_opt.addWidget(self.chk_group)
        main.addWidget(grp_opt)

        # ── 4. Observations GBIF ──────────────────────────────────────────
        grp_gbif = QGroupBox("4. Observations GBIF (optionnel)")
        grp_gbif.setStyleSheet("QGroupBox{font-weight:bold;}")
        lay_gbif = QVBoxLayout(grp_gbif)

        self.chk_gbif = QCheckBox("Charger les observations GBIF sur le territoire")
        self.chk_gbif.setChecked(False)
        self.chk_gbif.stateChanged.connect(self._on_gbif_toggle)
        lay_gbif.addWidget(self.chk_gbif)

        self.gbif_widget = QWidget()
        lay_gbif_inner = QVBoxLayout(self.gbif_widget)
        lay_gbif_inner.setContentsMargins(0, 4, 0, 0)
        lay_gbif_inner.setSpacing(8)

        lay_gbif_inner.addWidget(QLabel("Groupes taxonomiques (multi-sélection) :"))

        taxon_scroll = QScrollArea()
        taxon_scroll.setWidgetResizable(True)
        taxon_scroll.setFixedHeight(80)
        taxon_widget = QWidget()
        taxon_layout = QVBoxLayout(taxon_widget)
        taxon_layout.setSpacing(2)
        taxon_layout.setContentsMargins(4, 2, 4, 2)

        self.gbif_checkboxes = {}
        for label, key in GBIF_GROUPES:
            cb = QCheckBox(label)
            cb.setChecked(label == "Tous groupes")
            if label == "Tous groupes":
                cb.stateChanged.connect(self._on_tous_groupes_toggle)
            taxon_layout.addWidget(cb)
            self.gbif_checkboxes[label] = (cb, key)

        taxon_widget.setLayout(taxon_layout)
        taxon_scroll.setWidget(taxon_widget)
        lay_gbif_inner.addWidget(taxon_scroll)

        sep_gbif = QFrame()
        sep_gbif.setFrameShape(QFrame.HLine)
        sep_gbif.setStyleSheet("color:#DDDDDD")
        lay_gbif_inner.addWidget(sep_gbif)

        lay_annees = QHBoxLayout()
        lay_annees.addWidget(QLabel("Années :"))
        self.txt_gbif_annee_min = QLineEdit()
        self.txt_gbif_annee_min.setPlaceholderText("ex: 2000")
        self.txt_gbif_annee_min.setFixedWidth(65)
        lay_annees.addWidget(self.txt_gbif_annee_min)
        lay_annees.addWidget(QLabel("→"))
        self.txt_gbif_annee_max = QLineEdit()
        self.txt_gbif_annee_max.setPlaceholderText("ex: 2024")
        self.txt_gbif_annee_max.setFixedWidth(65)
        lay_annees.addWidget(self.txt_gbif_annee_max)
        lay_annees.addStretch()
        lay_gbif_inner.addLayout(lay_annees)

        lay_mois = QHBoxLayout()
        lay_mois.addWidget(QLabel("Mois :"))
        MOIS = ["—", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        self.combo_gbif_mois_min = QComboBox()
        self.combo_gbif_mois_min.addItems(MOIS)
        self.combo_gbif_mois_min.setFixedWidth(105)
        lay_mois.addWidget(self.combo_gbif_mois_min)
        lay_mois.addWidget(QLabel("→"))
        self.combo_gbif_mois_max = QComboBox()
        self.combo_gbif_mois_max.addItems(MOIS)
        self.combo_gbif_mois_max.setFixedWidth(105)
        lay_mois.addWidget(self.combo_gbif_mois_max)
        lay_mois.addStretch()
        lay_gbif_inner.addLayout(lay_mois)

        lay_limit = QHBoxLayout()
        lay_limit.addWidget(QLabel("Nombre max d'occurrences :"))
        self.combo_gbif_limit = QComboBox()
        self.combo_gbif_limit.addItems(["300", "1 000", "3 000", "10 000", "50 000", "100 000"])
        self.combo_gbif_limit.setCurrentIndex(1)
        lay_limit.addWidget(self.combo_gbif_limit)
        lay_limit.addStretch()
        lay_gbif_inner.addLayout(lay_limit)

        self.gbif_widget.setVisible(False)
        lay_gbif.addWidget(self.gbif_widget)
        main.addWidget(grp_gbif)

        # ── 5. Export Excel ───────────────────────────────────────────────
        grp_export = QGroupBox("5. Export Excel (optionnel)")
        grp_export.setStyleSheet("QGroupBox{font-weight:bold;}")
        lay_export = QVBoxLayout(grp_export)

        self.chk_export_excel = QCheckBox("Exporter les données vers un fichier Excel")
        self.chk_export_excel.setChecked(False)
        self.chk_export_excel.stateChanged.connect(self._on_export_toggle)
        lay_export.addWidget(self.chk_export_excel)

        self.export_widget = QWidget()
        lay_export_inner = QVBoxLayout(self.export_widget)
        lay_export_inner.setContentsMargins(0, 4, 0, 0)
        lay_export_inner.setSpacing(6)

        lay_out_path = QHBoxLayout()
        lay_out_path.addWidget(QLabel("Dossier de sortie :"))
        self.txt_export_path = QLineEdit()
        self.txt_export_path.setPlaceholderText("Choisir un dossier...")
        self.txt_export_path.setReadOnly(True)
        lay_out_path.addWidget(self.txt_export_path)
        self.btn_export_browse = QPushButton("📁")
        self.btn_export_browse.setFixedWidth(32)
        self.btn_export_browse.clicked.connect(self._browse_export_path)
        lay_out_path.addWidget(self.btn_export_browse)
        lay_export_inner.addLayout(lay_out_path)

        self.btn_export_now = QPushButton("📊  Exporter les couches du projet en Excel")
        self.btn_export_now.setStyleSheet("""
            QPushButton {
                background-color:#1D6A39; color:white;
                font-weight:bold; border-radius:5px; padding:6px;
            }
            QPushButton:hover   { background-color:#27AE60; }
            QPushButton:pressed { background-color:#145A2C; }
        """)
        self.btn_export_now.clicked.connect(self._export_excel_from_project)
        lay_export_inner.addWidget(self.btn_export_now)

        lbl_export_info = QLabel(
            "ℹ 'Exporter' exporte les couches du projet actuel. "
            "L'export automatique au chargement se fait si cette section est cochée.")
        lbl_export_info.setStyleSheet("color:#666; font-style:italic; font-size:10px;")
        lbl_export_info.setWordWrap(True)
        lay_export_inner.addWidget(lbl_export_info)

        self.export_widget.setVisible(False)
        lay_export.addWidget(self.export_widget)
        main.addWidget(grp_export)

        # ── Progression ───────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#555; font-style:italic;")
        main.addWidget(self.progress)
        main.addWidget(self.lbl_status)

        # ── Boutons principaux ────────────────────────────────────────────
        lay_buttons = QHBoxLayout()

        self.btn_load = QPushButton("🚀  Charger les données")
        self.btn_load.setMinimumHeight(42)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color:#1F4E79; color:white;
                font-size:13px; font-weight:bold;
                border-radius:6px; padding:8px;
            }
            QPushButton:hover   { background-color:#2E75B6; }
            QPushButton:pressed { background-color:#0F3A5C; }
        """)
        self.btn_load.clicked.connect(self._load_data)
        lay_buttons.addWidget(self.btn_load)

        self.btn_save_gpkg = QPushButton("💾  Exporter en GeoPackage")
        self.btn_save_gpkg.setMinimumHeight(42)
        self.btn_save_gpkg.setStyleSheet("""
            QPushButton {
                background-color:#1D6A39; color:white;
                font-size:13px; font-weight:bold;
                border-radius:6px; padding:8px;
            }
            QPushButton:hover   { background-color:#27AE60; }
            QPushButton:pressed { background-color:#145A2C; }
        """)
        self.btn_save_gpkg.clicked.connect(self._export_to_gpkg)
        lay_buttons.addWidget(self.btn_save_gpkg)

        main.addLayout(lay_buttons)

        scroll_container.setLayout(main)
        global_scroll.setWidget(scroll_container)
        root_layout.addWidget(global_scroll)

    # ── Territoire ────────────────────────────────────────────────────────

    def _browse_zone(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        filtres = (
            "Fichiers vecteur (*.gpkg *.geojson *.json *.shp *.kml *.kmz);;"
            "GeoPackage (*.gpkg);;GeoJSON (*.geojson *.json);;"
            "Shapefile (*.shp);;KML/KMZ (*.kml *.kmz);;Tous les fichiers (*)"
        )
        chemin, _ = QFileDialog.getOpenFileName(self, "Choisir une zone personnalisée", "", filtres)
        if not chemin:
            return

        lyr = QgsVectorLayer(chemin, "zone_perso", "ogr")
        if not lyr.isValid() or lyr.featureCount() == 0:
            self.lbl_result.setText("❌ Fichier invalide ou vide.")
            self.lbl_result.setStyleSheet("color:red; font-style:italic;")
            return
        if lyr.geometryType() != 2:
            self.lbl_result.setText("❌ Le fichier doit contenir des polygones.")
            self.lbl_result.setStyleSheet("color:red; font-style:italic;")
            return

        if lyr.crs().authid() != "EPSG:4326":
            import processing
            lyr = processing.run("native:reprojectlayer", {
                'INPUT': lyr, 'TARGET_CRS': 'EPSG:4326', 'OUTPUT': 'memory:'
            })['OUTPUT']

        self._territory_extent = lyr.extent()
        self._territory_lyr    = lyr

        import os
        nom_fichier = os.path.splitext(os.path.basename(chemin))[0]
        self.txt_search.setText(nom_fichier)
        self.txt_search.setEnabled(False)
        n = lyr.featureCount()
        self.lbl_result.setText(
            f"✅ Zone chargée : {nom_fichier} ({n} polygone{'s' if n > 1 else ''})")
        self.lbl_result.setStyleSheet("color:#2A7A2A; font-style:italic;")

    def _refresh_layer_combo(self):
        self.combo_layers.clear()
        self._layer_map = {}
        for lid, lyr in QgsProject.instance().mapLayers().items():
            if hasattr(lyr, 'geometryType') and lyr.geometryType() == 2:
                label = f"{lyr.name()} ({lyr.featureCount()} entités)"
                self.combo_layers.addItem(label)
                self._layer_map[label] = lyr
        if not self._layer_map:
            self.combo_layers.addItem("Aucune couche polygone dans le projet")

    def _use_project_layer(self):
        import processing
        label = self.combo_layers.currentText()
        lyr   = self._layer_map.get(label)
        if not lyr:
            self.lbl_result.setText("❌ Aucune couche sélectionnée.")
            self.lbl_result.setStyleSheet("color:red; font-style:italic;")
            return

        if lyr.crs().authid() != "EPSG:4326":
            lyr_wgs = processing.run("native:reprojectlayer", {
                'INPUT': lyr, 'TARGET_CRS': 'EPSG:4326', 'OUTPUT': 'memory:'
            })['OUTPUT']
        else:
            lyr_wgs = lyr

        self._territory_extent = lyr_wgs.extent()
        self._territory_lyr    = lyr_wgs
        self.txt_search.setText(lyr.name())
        self.lbl_result.setText(
            f"✅ Zone : {lyr.name()} ({lyr.featureCount()} polygone(s))")
        self.lbl_result.setStyleSheet("color:#2A7A2A; font-style:italic;")

    def _on_buffer_toggle(self, state):
        self.buffer_widget.setVisible(state == Qt.Checked)

    def _update_layer_availability(self):
        if not hasattr(self, "checkboxes"):
            return
        scale = self.combo_scale.currentText()
        for nom, cb in self.checkboxes.items():
            disabled_scales = self._heavy_layer_rules.get(nom, [])
            is_disabled = scale in disabled_scales
            cb.setEnabled(not is_disabled)
            if is_disabled:
                cb.setChecked(False)
                cb.setToolTip(
                    "Couche désactivée à cette échelle : elle est trop lourde "
                    "à charger sur un territoire aussi vaste.")
            else:
                cb.setToolTip("")

    def _on_text_changed(self, text):
        import requests
        self._suggestions = {}
        if len(text) < 3:
            self._completer_model.setStringList([])
            return
        scale = self.combo_scale.currentText()
        try:
            if scale == "Commune":
                r = requests.get(
                    "https://geo.api.gouv.fr/communes",
                    params={"nom": text, "fields": "nom,code,codeDepartement",
                            "boost": "population", "limit": 12},
                    timeout=5)
                if r.status_code == 200:
                    suggestions = []
                    for item in r.json():
                        label = f"{item['nom']} ({item.get('codeDepartement', '')})"
                        self._suggestions[label] = item['code']
                        suggestions.append(label)
                    self._completer_model.setStringList(suggestions)

            elif scale == "Département":
                r = requests.get(
                    "https://geo.api.gouv.fr/departements",
                    params={"nom": text, "fields": "nom,code", "limit": 15},
                    timeout=5)
                if r.status_code == 200:
                    suggestions = []
                    for item in r.json():
                        label = f"{item['nom']} ({item['code']})"
                        self._suggestions[label] = item['code']
                        suggestions.append(label)
                    self._completer_model.setStringList(suggestions)

            elif scale == "Région":
                r = requests.get(
                    "https://geo.api.gouv.fr/regions",
                    params={"nom": text, "fields": "nom,code", "limit": 18},
                    timeout=5)
                if r.status_code == 200:
                    suggestions = []
                    for item in r.json():
                        label = f"{item['nom']} ({item['code']})"
                        self._suggestions[label] = item['code']
                        self._suggestions[item['nom']] = item['code']
                        suggestions.append(label)
                    self._completer_model.setStringList(suggestions)
        except Exception:
            pass

    def _on_scale_change(self, idx):
        labels = ["Nom de la commune :", "Nom ou N° du département :",
                  "Nom de la région :", "", "Fichier de zone :"]
        placeholders = ["ex: Tours (37)...", "ex: Indre-et-Loire ou 37",
                        "ex: Centre (tapez 3 lettres)...", "",
                        "Charger un fichier de zone..."]
        self.lbl_search.setText(labels[idx])
        self.txt_search.setPlaceholderText(placeholders[idx])
        self._territory_extent = None
        self._territory_lyr    = None
        self._territory_code   = None
        self._suggestions      = {}
        self.txt_search.clear()
        self._completer_model.setStringList([])
        self.lbl_result.setText("")
        self._update_layer_availability()

        if idx == 3:  # France entière
            self.txt_search.setEnabled(False)
            self.btn_search.setEnabled(False)
            self.btn_browse.setVisible(False)
            self.btn_from_layer.setVisible(False)
            self.combo_layers.setVisible(False)
            self.lbl_result.setText("✅ Chargement sur la France entière")
            self.lbl_result.setStyleSheet("color:#2A7A2A; font-style:italic;")
        elif idx == 4:  # Zone personnalisée
            self.txt_search.setEnabled(False)
            self.btn_search.setEnabled(False)
            self.btn_browse.setVisible(True)
            self.btn_from_layer.setVisible(True)
            self._refresh_layer_combo()
            self.combo_layers.setVisible(True)
        else:
            self.txt_search.setEnabled(True)
            self.btn_search.setEnabled(True)
            self.btn_browse.setVisible(False)
            self.btn_from_layer.setVisible(False)
            self.combo_layers.setVisible(False)

    def _search_territory(self):
        import requests
        scale = self.combo_scale.currentText()
        terme = self.txt_search.text().strip()
        if not terme:
            QMessageBox.warning(self, "Attention", "Saisissez un nom de territoire.")
            return

        self.lbl_result.setText("Recherche en cours...")
        self.lbl_result.setStyleSheet("color:#888; font-style:italic;")
        QApplication.processEvents()

        code = self._suggestions.get(terme, None)

        if scale == "Commune":
            typename = "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:commune"
            if code:
                filtre = (f"<Filter><PropertyIsEqualTo>"
                          f"<PropertyName>code_insee</PropertyName>"
                          f"<Literal>{code}</Literal>"
                          f"</PropertyIsEqualTo></Filter>")
            else:
                nom_seul = terme.split("(")[0].strip()
                filtre = (f"<Filter><PropertyIsLike wildCard='*' singleChar='.' escape='!'>"
                          f"<PropertyName>nom_officiel</PropertyName>"
                          f"<Literal>{nom_seul}</Literal>"
                          f"</PropertyIsLike></Filter>")

        elif scale == "Département":
            typename = "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:departement"
            if code:
                filtre = (f"<Filter><PropertyIsEqualTo>"
                          f"<PropertyName>code_insee</PropertyName>"
                          f"<Literal>{code}</Literal>"
                          f"</PropertyIsEqualTo></Filter>")
            elif terme.isdigit():
                filtre = (f"<Filter><PropertyIsEqualTo>"
                          f"<PropertyName>code_insee</PropertyName>"
                          f"<Literal>{terme.zfill(2)}</Literal>"
                          f"</PropertyIsEqualTo></Filter>")
            else:
                nom_seul = terme.split("(")[0].strip()
                filtre = (f"<Filter><PropertyIsLike wildCard='*' singleChar='.' escape='!'>"
                          f"<PropertyName>nom_officiel</PropertyName>"
                          f"<Literal>*{nom_seul}*</Literal>"
                          f"</PropertyIsLike></Filter>")

        else:  # Région
            typename = "LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:region"
            if code:
                filtre = (f"<Filter><PropertyIsEqualTo>"
                          f"<PropertyName>code_insee</PropertyName>"
                          f"<Literal>{code}</Literal>"
                          f"</PropertyIsEqualTo></Filter>")
            else:
                nom_seul = terme.split("(")[0].strip()
                filtre = (f"<Filter><PropertyIsLike wildCard='*' singleChar='.' escape='!'>"
                          f"<PropertyName>nom_officiel</PropertyName>"
                          f"<Literal>*{nom_seul}*</Literal>"
                          f"</PropertyIsLike></Filter>")

        uri = (f"url='{WFS_GPF}' typename='{typename}' version='auto' "
               f"srsname='EPSG:4326' filter='{filtre}'")
        lyr = QgsVectorLayer(uri, "search", "WFS")

        if not lyr.isValid() or lyr.featureCount() == 0:
            self.lbl_result.setText("❌ Territoire non trouvé.")
            self.lbl_result.setStyleSheet("color:red; font-style:italic;")
            self._territory_extent = None
            return

        for feat in lyr.getFeatures():
            self._territory_extent = feat.geometry().boundingBox()
            nom_trouve = feat['nom_officiel']
            try:
                code_feat = feat['code_insee']
                self._territory_code = str(code_feat) if code_feat else code
            except Exception:
                self._territory_code = code
            break

        lyr_copy = QgsVectorLayer(
            f"MultiPolygon?crs={lyr.crs().authid()}", "territoire", "memory")
        pr_copy = lyr_copy.dataProvider()
        pr_copy.addAttributes(lyr.fields().toList())
        lyr_copy.updateFields()
        pr_copy.addFeatures(list(lyr.getFeatures()))
        lyr_copy.updateExtents()
        self._territory_lyr = lyr_copy

        self.lbl_result.setText(f"✅ {nom_trouve}")
        self.lbl_result.setStyleSheet("color:#2A7A2A; font-style:italic;")

    # ── GBIF ──────────────────────────────────────────────────────────────

    def _on_tous_groupes_toggle(self, state):
        if state == Qt.Checked:
            for label, (cb, key) in self.gbif_checkboxes.items():
                if label != "Tous groupes":
                    cb.setChecked(False)

    def _on_gbif_toggle(self, state):
        self.gbif_widget.setVisible(state == Qt.Checked)
        self.adjustSize()

    def _load_gbif(self, project, root, grp, extent_effectif=None, lyr_clip_effectif=None):
        import requests
        from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry,
                                QgsPointXY, QgsFields, QgsField,
                                QgsLayerTreeLayer, QgsMarkerSymbol,
                                QgsSimpleMarkerSymbolLayer,
                                QgsSingleSymbolRenderer)
        from qgis.PyQt.QtCore import QVariant

        taxon_keys  = []
        tous_coches = self.gbif_checkboxes["Tous groupes"][0].isChecked()

        if not tous_coches:
            for label, (cb, key) in self.gbif_checkboxes.items():
                if cb.isChecked() and key is not None:
                    taxon_keys.append((label, key))
            if not taxon_keys:
                self.lbl_status.setText("⚠ GBIF : sélectionnez au moins un groupe.")
                return

        limit     = int(self.combo_gbif_limit.currentText().replace(" ", ""))
        annee_min = self.txt_gbif_annee_min.text().strip()
        annee_max = self.txt_gbif_annee_max.text().strip()

        base_params = {
            "country": "FR",
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
        }
        if annee_min and annee_max:
            base_params["year"] = f"{annee_min},{annee_max}"
        elif annee_min:
            base_params["year"] = f"{annee_min},{annee_min}"

        mois_min_idx = self.combo_gbif_mois_min.currentIndex()
        mois_max_idx = self.combo_gbif_mois_max.currentIndex()
        if mois_min_idx > 0 and mois_max_idx > 0:
            base_params["month"] = f"{mois_min_idx},{mois_max_idx}"
        elif mois_min_idx > 0:
            base_params["month"] = f"{mois_min_idx},{mois_min_idx}"
        elif mois_max_idx > 0:
            base_params["month"] = f"1,{mois_max_idx}"

        if extent_effectif:
            ext = extent_effectif
            base_params["decimalLongitude"] = f"{ext.xMinimum():.4f},{ext.xMaximum():.4f}"
            base_params["decimalLatitude"]  = f"{ext.yMinimum():.4f},{ext.yMaximum():.4f}"

        requetes = [(label, {**base_params, "taxonKey": key})
                    for label, key in taxon_keys] if taxon_keys \
                 else [("Tous groupes", base_params)]

        all_results     = []
        limit_par_taxon = limit // len(requetes) if len(requetes) > 1 else limit

        for label_req, params in requetes:
            collected = 0
            offset    = 0
            page_size = 300
            self.lbl_status.setText(f"GBIF — chargement {label_req}...")
            QApplication.processEvents()
            while collected < limit_par_taxon:
                params["limit"]  = min(page_size, limit_par_taxon - collected)
                params["offset"] = offset
                try:
                    r = requests.get(GBIF_API, params=params, timeout=20)
                    if r.status_code != 200:
                        break
                    data    = r.json()
                    results = data.get("results", [])
                    if not results:
                        break
                    for obs in results:
                        obs["_groupe_label"] = label_req
                    all_results.extend(results)
                    collected += len(results)
                    if data.get("endOfRecords", True):
                        break
                    offset += page_size
                except Exception:
                    break

        if not all_results:
            self.lbl_status.setText("⚠ GBIF : aucune observation trouvée.")
            return

        fields = QgsFields()
        for fname, ftype in [
            ("gbifID", QVariant.String), ("espece", QVariant.String),
            ("nom_vernaculaire", QVariant.String), ("famille", QVariant.String),
            ("classe", QVariant.String), ("groupe", QVariant.String),
            ("date_obs", QVariant.String), ("annee", QVariant.Int),
            ("source", QVariant.String), ("latitude", QVariant.Double),
            ("longitude", QVariant.Double),
        ]:
            fields.append(QgsField(fname, ftype))

        groupes_label = ("Tous groupes" if tous_coches
                         else " + ".join(l for l, _ in taxon_keys))

        if annee_min and annee_max:
            periode_label = f"{annee_min}–{annee_max}"
        elif annee_min:
            periode_label = f"depuis {annee_min}"
        elif annee_max:
            periode_label = f"jusqu'à {annee_max}"
        else:
            periode_label = "toutes périodes"

        MOIS_COURTS = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                       "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        if mois_min_idx > 0 or mois_max_idx > 0:
            m_min = MOIS_COURTS[mois_min_idx] if mois_min_idx > 0 else "Jan"
            m_max = MOIS_COURTS[mois_max_idx] if mois_max_idx > 0 else "Déc"
            periode_label += f" ({m_min}–{m_max})"

        mem_lyr = QgsVectorLayer(
            "Point?crs=EPSG:4326&index=yes",
            f"GBIF — {groupes_label} — {periode_label}", "memory")
        pr = mem_lyr.dataProvider()
        pr.addAttributes(fields)
        mem_lyr.updateFields()

        feats = []
        for obs in all_results:
            lat = obs.get("decimalLatitude")
            lon = obs.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            f = QgsFeature(mem_lyr.fields())
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            f.setAttribute("gbifID",           str(obs.get("gbifID", "")))
            f.setAttribute("espece",           obs.get("species", obs.get("scientificName", "")))
            f.setAttribute("nom_vernaculaire", obs.get("vernacularName", ""))
            f.setAttribute("famille",          obs.get("family", ""))
            f.setAttribute("classe",           obs.get("class", ""))
            f.setAttribute("groupe",           obs.get("_groupe_label", ""))
            f.setAttribute("date_obs",         obs.get("eventDate", ""))
            f.setAttribute("annee",            obs.get("year"))
            f.setAttribute("source",           obs.get("datasetName", ""))
            f.setAttribute("latitude",         lat)
            f.setAttribute("longitude",        lon)
            feats.append(f)

        pr.addFeatures(feats)
        mem_lyr.updateExtents()

        GBIF_STYLES = {
            "Tous groupes"   : ("#95A5A6", "#607080", QgsSimpleMarkerSymbolLayer.Shape.Circle),
            "🦋 Insectes"    : ("#8E44AD", "#5E2D7D", QgsSimpleMarkerSymbolLayer.Shape.Star),
            "🌿 Plantes"     : ("#27AE60", "#1A7A40", QgsSimpleMarkerSymbolLayer.Shape.Square),
            "🐦 Oiseaux"     : ("#E8A020", "#B06010", QgsSimpleMarkerSymbolLayer.Shape.Circle),
            "🦇 Chiroptères" : ("#2C3E50", "#1A252F", QgsSimpleMarkerSymbolLayer.Shape.Diamond),
            "🐾 Mammifères"  : ("#C0392B", "#8B0000", QgsSimpleMarkerSymbolLayer.Shape.Diamond),
            "🐸 Amphibiens"  : ("#1E8BC3", "#155880", QgsSimpleMarkerSymbolLayer.Shape.Triangle),
            "🦎 Reptiles"    : ("#16A085", "#0E6655", QgsSimpleMarkerSymbolLayer.Shape.Square),
            "🐟 Poissons"    : ("#2980B9", "#1A5276", QgsSimpleMarkerSymbolLayer.Shape.Arrow),
            "🦀 Crustacés"   : ("#E74C3C", "#922B21", QgsSimpleMarkerSymbolLayer.Shape.Pentagon),
            "🐌 Mollusques"  : ("#D35400", "#922B00", QgsSimpleMarkerSymbolLayer.Shape.Pentagon),
            "🍄 Champignons" : ("#E67E22", "#A04000", QgsSimpleMarkerSymbolLayer.Shape.Circle),
            "🌾 Bryophytes"  : ("#2ECC71", "#1A8A4A", QgsSimpleMarkerSymbolLayer.Shape.Cross2),
            "🦟 Arachnides"  : ("#7F8C8D", "#4D5656", QgsSimpleMarkerSymbolLayer.Shape.Star),
        }

        if tous_coches or len(taxon_keys) != 1:
            from qgis.core import QgsRuleBasedRenderer, QgsSymbol
            renderer  = QgsRuleBasedRenderer(QgsSymbol.defaultSymbol(mem_lyr.geometryType()))
            rule_root = renderer.rootRule()
            rule_root.removeChildAt(0)
            groupes_a_styler = (
                [(l, k) for l, k in GBIF_GROUPES if l != "Tous groupes"]
                if tous_coches else taxon_keys
            )
            for label_g, _ in groupes_a_styler:
                fill, stroke, shape = GBIF_STYLES.get(
                    label_g, ("#95A5A6", "#607080", QgsSimpleMarkerSymbolLayer.Shape.Circle))
                sym = QgsMarkerSymbol()
                sym.deleteSymbolLayer(0)
                mk = QgsSimpleMarkerSymbolLayer()
                mk.setShape(shape)
                mk.setSize(1.8); mk.setSizeUnit(MM)
                mk.setColor(QColor(fill))
                mk.setStrokeColor(QColor(stroke))
                mk.setStrokeWidth(0.15); mk.setStrokeWidthUnit(MM)
                sym.appendSymbolLayer(mk)
                sym.setOpacity(0.75)
                rule = QgsRuleBasedRenderer.Rule(sym)
                rule.setFilterExpression(f'"groupe" = \'{label_g}\'')
                rule.setLabel(label_g)
                rule_root.appendChild(rule)

            sym_else = QgsMarkerSymbol()
            sym_else.deleteSymbolLayer(0)
            mk_else = QgsSimpleMarkerSymbolLayer()
            mk_else.setShape(QgsSimpleMarkerSymbolLayer.Shape.Circle)
            mk_else.setSize(1.4); mk_else.setSizeUnit(MM)
            mk_else.setColor(QColor("#BDC3C7"))
            mk_else.setStrokeColor(QColor("#7F8C8D"))
            mk_else.setStrokeWidth(0.12); mk_else.setStrokeWidthUnit(MM)
            sym_else.appendSymbolLayer(mk_else)
            sym_else.setOpacity(0.55)
            rule_else = QgsRuleBasedRenderer.Rule(sym_else)
            rule_else.setIsElse(True)
            rule_else.setLabel("Autre / inconnu")
            rule_root.appendChild(rule_else)
            mem_lyr.setRenderer(renderer)
        else:
            label_seul = taxon_keys[0][0]
            fill, stroke, shape = GBIF_STYLES.get(
                label_seul, ("#E67E22", "#A04000", QgsSimpleMarkerSymbolLayer.Shape.Circle))
            sym = QgsMarkerSymbol()
            sym.deleteSymbolLayer(0)
            mk = QgsSimpleMarkerSymbolLayer()
            mk.setShape(shape)
            mk.setSize(1.8); mk.setSizeUnit(MM)
            mk.setColor(QColor(fill))
            mk.setStrokeColor(QColor(stroke))
            mk.setStrokeWidth(0.15); mk.setStrokeWidthUnit(MM)
            sym.appendSymbolLayer(mk)
            sym.setOpacity(0.75)
            mem_lyr.setRenderer(QgsSingleSymbolRenderer(sym))

        project.addMapLayer(mem_lyr, False)
        if grp:
            grp.addChildNode(QgsLayerTreeLayer(mem_lyr))
        else:
            root.addLayer(mem_lyr)

        self.lbl_status.setText(f"✅ GBIF : {len(feats):,} observations — {groupes_label}")

    # ── Export Excel ──────────────────────────────────────────────────────

    def _on_export_toggle(self, state):
        self.export_widget.setVisible(state == Qt.Checked)

    def _browse_export_path(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        dossier = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie", "")
        if dossier:
            self.txt_export_path.setText(dossier)

    def _export_excel(self, layers_loaded, territoire_label, buffer_label):
        layers_loaded = [(n, l) for n, l in layers_loaded if not exclude_from_excel(n)]
        if not layers_loaded:
            self.lbl_status.setText("⚠ Export Excel : aucune couche exportable hors cadastre.")
            return

        try:
            import openpyxl
        except ImportError:
            try:
                import subprocess, sys
                subprocess.run([sys.executable, "-m", "pip", "install",
                                "openpyxl", "--break-system-packages"],
                               capture_output=True)
                import openpyxl
            except Exception:
                self.lbl_status.setText("❌ Export Excel : impossible d'installer openpyxl.")
                return

        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        import os, re, unicodedata

        dossier = self.txt_export_path.text().strip()
        if not dossier:
            self.lbl_status.setText("❌ Export Excel : choisissez un dossier de sortie.")
            return

        nom_fichier = f"{territoire_label}_{buffer_label}.xlsx"
        nom_fichier = unicodedata.normalize('NFKD', nom_fichier)
        nom_fichier = ''.join(c for c in nom_fichier if unicodedata.category(c) != 'Mn')
        nom_fichier = re.sub(r'[^\x20-\x7E]', '', nom_fichier)
        for c in r'\/:*?"<>|':
            nom_fichier = nom_fichier.replace(c, "_")
        nom_fichier = re.sub(r'\s+', '_', nom_fichier).strip("_")
        if not nom_fichier.endswith(".xlsx"):
            nom_fichier += ".xlsx"
        chemin_excel = os.path.join(dossier, nom_fichier)

        wb = Workbook()
        wb.remove(wb.active)
        header_font  = Font(bold=True, color="FFFFFF")
        header_fill  = PatternFill("solid", fgColor="1F4E79")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for lyr_name, lyr in layers_loaded:
            sheet_name = unicodedata.normalize('NFKD', lyr_name)
            sheet_name = ''.join(c for c in sheet_name if unicodedata.category(c) != 'Mn')
            sheet_name = re.sub(r'[^\x20-\x7E]', '', sheet_name)
            for c in r'\/:*?[]':
                sheet_name = sheet_name.replace(c, "_")
            sheet_name = re.sub(r'\s+', ' ', sheet_name).strip(" -—_")[:31]
            if not sheet_name:
                sheet_name = f"Feuille_{lyr_name[:10]}"

            ws = wb.create_sheet(title=sheet_name)
            fields = [f.name() for f in lyr.fields()]
            for col, field in enumerate(fields, 1):
                cell = ws.cell(row=1, column=col, value=field)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align
                ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 18

            for row_idx, feat in enumerate(lyr.getFeatures(), 2):
                for col_idx, field in enumerate(fields, 1):
                    val = feat[field]
                    if val is None or (hasattr(val, 'isNull') and val.isNull()):
                        val = ""
                    elif not isinstance(val, (int, float, str, bool)):
                        val = str(val)
                    ws.cell(row=row_idx, column=col_idx, value=val)
            ws.freeze_panes = "A2"

        if not wb.sheetnames:
            self.lbl_status.setText("⚠ Export Excel : aucune couche à exporter.")
            return
        try:
            wb.save(chemin_excel)
            self.lbl_status.setText(f"✅ Excel exporté : {nom_fichier}")
        except PermissionError:
            QMessageBox.critical(self, "Fichier inaccessible",
                f"Impossible d'enregistrer :\n{chemin_excel}\n\n"
                f"Le fichier est peut-être ouvert dans Excel.")
            self.lbl_status.setText("❌ Export Excel annulé — fichier déjà ouvert.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", str(e))
            self.lbl_status.setText(f"❌ Export Excel échoué : {str(e)[:60]}")

    def _export_excel_from_project(self):
        dossier = self.txt_export_path.text().strip()
        if not dossier:
            QMessageBox.warning(self, "Attention", "Choisissez d'abord un dossier de sortie.")
            return

        selected = [nom for nom, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Attention",
                "Cochez au moins une couche dans la section 2 avant d'exporter.")
            return

        if self.combo_scale.currentText() != "France entière" and \
                self._territory_extent is None:
            QMessageBox.warning(self, "Attention",
                "Recherchez d'abord un territoire avant d'exporter.")
            return

        self.btn_export_now.setEnabled(False)
        self.lbl_status.setText("Préparation de l'export Excel...")
        QApplication.processEvents()

        lyr_clip_effectif = self._territory_lyr
        extent_effectif   = self._territory_extent

        if self.chk_buffer.isChecked() and self._territory_lyr:
            lyr_buf = self._apply_buffer(self._territory_lyr)
            if lyr_buf:
                lyr_clip_effectif = lyr_buf
                extent_effectif   = lyr_buf.extent()

        catalogue_dict = {nom: (typename, serveur, fill, stroke)
                          for _, nom, typename, serveur, fill, stroke in CATALOGUE}
        layers_for_export = []

        for nom in selected:
            if exclude_from_excel(nom):
                continue
            self.lbl_status.setText(f"Export — chargement : {nom}...")
            QApplication.processEvents()

            typename, serveur, fill, stroke = catalogue_dict[nom]
            if extent_effectif:
                ext = extent_effectif
                mx  = ext.width()  * 0.005
                my  = ext.height() * 0.005
                bbox_str = (f"{ext.xMinimum()-mx},{ext.yMinimum()-my},"
                            f"{ext.xMaximum()+mx},{ext.yMaximum()+my}")
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, bbox_str)
            else:
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, None)

            if typename == "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle" and lyr_clip_effectif:
                code_cadastre = (self._territory_code
                                 if self.combo_scale.currentText() == "Commune" else None)
                lyr = load_cadastre_parcelles_api(
                    lyr_clip_effectif, nom, self.lbl_status, QApplication,
                    code_insee=code_cadastre)
                if lyr and layer_has_features(lyr):
                    layers_for_export.append((nom, lyr))
                continue

            if is_gpu and lyr_clip_effectif:
                lyr = load_gpu_layer(typename, filtre_expr, lyr_clip_effectif,
                                     nom, self.lbl_status, QApplication)
                if lyr and layer_has_features(lyr):
                    layers_for_export.append((nom, lyr))
                continue

            lyr = QgsVectorLayer(uri, nom, "WFS")
            if not lyr.isValid():
                continue

            if lyr_clip_effectif:
                try:
                    key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                          else 'native:clip'
                    params = ({'INPUT': lyr, 'PREDICATE': [0], 'INTERSECT': lyr_clip_effectif,
                                'OUTPUT': 'memory:'}
                               if self.chk_intersect_only.isChecked()
                               else {'INPUT': lyr, 'OVERLAY': lyr_clip_effectif, 'OUTPUT': 'memory:'})
                    lyr = processing.run(key, params)['OUTPUT']
                    lyr.setName(nom)
                except Exception:
                    try:
                        lyr_fixed = processing.run("native:fixgeometries",
                            {'INPUT': lyr, 'OUTPUT': 'memory:'})['OUTPUT']
                        key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                              else 'native:clip'
                        params = ({'INPUT': lyr_fixed, 'PREDICATE': [0],
                                    'INTERSECT': lyr_clip_effectif, 'OUTPUT': 'memory:'}
                                   if self.chk_intersect_only.isChecked()
                                   else {'INPUT': lyr_fixed, 'OVERLAY': lyr_clip_effectif,
                                         'OUTPUT': 'memory:'})
                        lyr = processing.run(key, params)['OUTPUT']
                        lyr.setName(nom)
                    except Exception as e:
                        self.lbl_status.setText(f"⚠ Clip échoué : {str(e)[:60]}")
                        QApplication.processEvents()

            if filtre_expr and layer_has_features(lyr):
                from qgis.core import QgsFeatureRequest, QgsExpression
                feats  = list(lyr.getFeatures(QgsFeatureRequest(QgsExpression(filtre_expr))))
                crs_id = lyr.crs().authid()
                flds   = lyr.fields().toList()
                lyr_m  = QgsVectorLayer(f"Polygon?crs={crs_id}", nom, "memory")
                pr_m   = lyr_m.dataProvider()
                pr_m.addAttributes(flds)
                lyr_m.updateFields()
                pr_m.addFeatures(feats)
                lyr_m.updateExtents()
                lyr = lyr_m

            if layer_has_features(lyr):
                layers_for_export.append((nom, lyr))

        if not layers_for_export:
            QMessageBox.warning(self, "Export Excel",
                "Aucune donnée trouvée sur ce territoire pour les couches sélectionnées.")
            self.btn_export_now.setEnabled(True)
            return

        territoire_label = self.txt_search.text().strip() or "France"
        territoire_label = f"{self.combo_scale.currentText()}_{territoire_label}"
        buffer_label = (f"buffer_{self.txt_buffer_size.text().strip()}"
                        f"_{self.combo_buffer_unit.currentText()}"
                        if self.chk_buffer.isChecked() else "sans_buffer")

        self._export_excel(layers_for_export, territoire_label, buffer_label)
        self.btn_export_now.setEnabled(True)

    # ── Export GeoPackage ─────────────────────────────────────────────────

    def _save_layer_to_gpkg(self, lyr, gpkg_path, first):
        """Sauvegarde une couche dans le GeoPackage et retourne (lyr_gpkg, erreur)."""
        from qgis.core import (QgsVectorFileWriter, QgsCoordinateTransformContext,
                                QgsVectorLayer)

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName   = "GPKG"
        options.layerName    = lyr.name()[:60]
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteFile if first
            else QgsVectorFileWriter.CreateOrOverwriteLayer
        )
        err, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
            lyr, gpkg_path, QgsCoordinateTransformContext(), options)
        if err != 0:
            return None, f"Erreur GPKG pour {lyr.name()} : {msg}"
        uri      = f"{gpkg_path}|layername={options.layerName}"
        lyr_gpkg = QgsVectorLayer(uri, lyr.name(), "ogr")
        if not lyr_gpkg.isValid():
            return None, f"Couche GPKG invalide : {lyr.name()}"
        lyr_gpkg.setRenderer(lyr.renderer().clone())
        return lyr_gpkg, None

    def _export_to_gpkg(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        from qgis.core import (QgsVectorLayer, QgsVectorFileWriter,
                                QgsCoordinateTransformContext)
        import re, unicodedata

        selected = [nom for nom, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Attention", "Cochez au moins une couche dans la section 2.")
            return
        if self.combo_scale.currentText() != "France entière" and \
                self._territory_extent is None:
            QMessageBox.warning(self, "Attention", "Recherchez d'abord un territoire.")
            return

        chemin_gpkg, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le GeoPackage", "", "GeoPackage (*.gpkg)")
        if not chemin_gpkg:
            return
        if not chemin_gpkg.endswith(".gpkg"):
            chemin_gpkg += ".gpkg"

        self.btn_save_gpkg.setEnabled(False)
        self.lbl_status.setText("Préparation de l'export GeoPackage...")
        QApplication.processEvents()

        lyr_clip_effectif = self._territory_lyr
        extent_effectif   = self._territory_extent

        if self.chk_buffer.isChecked() and self._territory_lyr:
            lyr_buf = self._apply_buffer(self._territory_lyr)
            if lyr_buf:
                lyr_clip_effectif = lyr_buf
                extent_effectif   = lyr_buf.extent()

        catalogue_dict = {nom: (typename, serveur, fill, stroke)
                          for _, nom, typename, serveur, fill, stroke in CATALOGUE}

        project = QgsProject.instance()
        root    = project.layerTreeRoot()
        if self.chk_group.isChecked():
            territoire = self.txt_search.text().strip() or "France"
            grp = QgsLayerTreeGroup(
                f"{self.combo_scale.currentText()} — {territoire} — Données naturalistes")
            grp.setExpanded(True)
            root.insertChildNode(0, grp)
        else:
            grp = None

        first = True
        nb_ok = 0

        for nom in selected:
            self.lbl_status.setText(f"GPKG — chargement : {nom}...")
            QApplication.processEvents()

            typename, serveur, fill, stroke = catalogue_dict[nom]

            if extent_effectif:
                ext = extent_effectif
                mx  = ext.width()  * 0.005
                my  = ext.height() * 0.005
                bbox_str = (f"{ext.xMinimum()-mx},{ext.yMinimum()-my},"
                            f"{ext.xMaximum()+mx},{ext.yMaximum()+my}")
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, bbox_str)
            else:
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, None)

            if is_gpu and lyr_clip_effectif:
                lyr = load_gpu_layer(typename, filtre_expr, lyr_clip_effectif,
                                     nom, self.lbl_status, QApplication)
                if not lyr or not layer_has_features(lyr):
                    continue
                self.lbl_status.setText(f"GPU — filtrage spatial : {nom}...")
                QApplication.processEvents()
                try:
                    key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                          else 'native:clip'
                    params = ({'INPUT': lyr, 'PREDICATE': [0], 'INTERSECT': lyr_clip_effectif,
                                'OUTPUT': 'memory:'}
                               if self.chk_intersect_only.isChecked()
                               else {'INPUT': lyr, 'OVERLAY': lyr_clip_effectif, 'OUTPUT': 'memory:'})
                    lyr_c = processing.run(key, params)['OUTPUT']
                    lyr_c.setName(nom)
                    if layer_has_features(lyr_c):
                        lyr = lyr_c
                except Exception:
                    try:
                        params['INPUT'] = processing.run("native:fixgeometries",
                            {'INPUT': lyr, 'OUTPUT': 'memory:'})['OUTPUT']
                        lyr_c = processing.run(key, params)['OUTPUT']
                        lyr_c.setName(nom)
                        if layer_has_features(lyr_c):
                            lyr = lyr_c
                    except Exception as e:
                        self.lbl_status.setText(f"⚠ GPU clip échoué : {str(e)[:80]}")
                        QApplication.processEvents()
                if not layer_has_features(lyr):
                    continue
            else:
                lyr = QgsVectorLayer(uri, nom, "WFS")
                if not lyr.isValid():
                    continue

                if lyr_clip_effectif:
                    try:
                        key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                              else 'native:clip'
                        params = ({'INPUT': lyr, 'PREDICATE': [0],
                                    'INTERSECT': lyr_clip_effectif, 'OUTPUT': 'memory:'}
                                   if self.chk_intersect_only.isChecked()
                                   else {'INPUT': lyr, 'OVERLAY': lyr_clip_effectif,
                                         'OUTPUT': 'memory:'})
                        lyr_f = processing.run(key, params)['OUTPUT']
                        lyr_f.setName(nom)
                        lyr = lyr_f
                    except Exception:
                        try:
                            lyr_fixed = processing.run("native:fixgeometries",
                                {'INPUT': lyr, 'OUTPUT': 'memory:'})['OUTPUT']
                            lyr_f = processing.run(key, params)['OUTPUT']
                            lyr_f.setName(nom)
                            lyr = lyr_f
                        except Exception as e:
                            self.lbl_status.setText(f"⚠ Clip échoué : {str(e)[:60]}")
                            QApplication.processEvents()

                if filtre_expr and layer_has_features(lyr):
                    from qgis.core import QgsFeatureRequest, QgsExpression
                    feats  = list(lyr.getFeatures(
                        QgsFeatureRequest(QgsExpression(filtre_expr))))
                    crs_id = lyr.crs().authid()
                    flds   = lyr.fields().toList()
                    lyr_m  = QgsVectorLayer(f"Polygon?crs={crs_id}", nom, "memory")
                    pr_m   = lyr_m.dataProvider()
                    pr_m.addAttributes(flds)
                    lyr_m.updateFields()
                    pr_m.addFeatures(feats)
                    lyr_m.updateExtents()
                    lyr = lyr_m

            if not layer_has_features(lyr):
                continue

            if self.chk_style.isChecked():
                apply_style(lyr, fill, stroke)

            layer_name = unicodedata.normalize('NFKD', nom)
            layer_name = ''.join(c for c in layer_name if unicodedata.category(c) != 'Mn')
            layer_name = re.sub(r'[^\w\s-]', '', layer_name).strip()
            layer_name = re.sub(r'\s+', '_', layer_name)[:60]

            self.lbl_status.setText(f"GPKG — écriture : {nom}...")
            QApplication.processEvents()

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName   = "GPKG"
            options.layerName    = layer_name
            options.fileEncoding = "UTF-8"
            options.actionOnExistingFile = (
                QgsVectorFileWriter.CreateOrOverwriteFile if first
                else QgsVectorFileWriter.CreateOrOverwriteLayer
            )
            err, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                lyr, chemin_gpkg, QgsCoordinateTransformContext(), options)

            if err == 0:
                uri_gpkg = f"{chemin_gpkg}|layername={layer_name}"
                lyr_gpkg = QgsVectorLayer(uri_gpkg, nom, "ogr")
                if lyr_gpkg.isValid():
                    lyr_gpkg.setRenderer(lyr.renderer().clone())
                    project.addMapLayer(lyr_gpkg, False)
                    if grp:
                        grp.addChildNode(QgsLayerTreeLayer(lyr_gpkg))
                    else:
                        root.addLayer(lyr_gpkg)
                first = False
                nb_ok += 1
            else:
                self.lbl_status.setText(f"⚠ GPKG erreur : {nom} — {msg}")

        if nb_ok > 0:
            self.lbl_status.setText(
                f"✅ GeoPackage exporté : {nb_ok} couche(s) → {chemin_gpkg}")
            QMessageBox.information(self, "Export GeoPackage",
                f"{nb_ok} couche(s) exportée(s) dans :\n{chemin_gpkg}\n\n"
                f"Les couches ont été rechargées depuis le GeoPackage dans le projet.")
        else:
            self.lbl_status.setText("⚠ Aucune couche exportée.")

        self.btn_save_gpkg.setEnabled(True)

    # ── Utilitaires ───────────────────────────────────────────────────────

    def _check_all(self, state):
        for cb in self.checkboxes.values():
            if cb.isEnabled():
                cb.setChecked(state)

    def _apply_buffer(self, lyr):
        import processing
        try:
            taille = float(self.txt_buffer_size.text().strip().replace(",", "."))
        except ValueError:
            self.lbl_result.setText("❌ Taille de buffer invalide.")
            self.lbl_result.setStyleSheet("color:red; font-style:italic;")
            return None

        unite = self.combo_buffer_unit.currentText()
        lyr_l93 = processing.run("native:reprojectlayer", {
            'INPUT': lyr, 'TARGET_CRS': 'EPSG:2154', 'OUTPUT': 'memory:'
        })['OUTPUT']
        distance_m = taille * 1000 if unite == "Kilomètres" else taille
        lyr_buf = processing.run("native:buffer", {
            'INPUT': lyr_l93, 'DISTANCE': distance_m, 'SEGMENTS': 16,
            'END_CAP_STYLE': 0, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2,
            'DISSOLVE': True, 'OUTPUT': 'memory:'
        })['OUTPUT']
        return processing.run("native:reprojectlayer", {
            'INPUT': lyr_buf, 'TARGET_CRS': 'EPSG:4326', 'OUTPUT': 'memory:'
        })['OUTPUT']

    # ── Chargement principal ──────────────────────────────────────────────

    def _load_data(self):
        selected = [nom for nom, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected and not self.chk_gbif.isChecked():
            QMessageBox.warning(self, "Attention",
                "Cochez au moins une couche ou activez le chargement GBIF.")
            return
        if self.combo_scale.currentText() != "France entière" and \
                self._territory_extent is None:
            QMessageBox.warning(self, "Attention", "Recherchez d'abord un territoire.")
            return

        self.btn_load.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(selected))
        self.progress.setValue(0)

        project = QgsProject.instance()
        root    = project.layerTreeRoot()

        if self.chk_group.isChecked():
            territoire = self.txt_search.text().strip() or "France"
            grp = QgsLayerTreeGroup(
                f"{self.combo_scale.currentText()} — {territoire} — Données naturalistes")
            grp.setExpanded(True)
            root.addChildNode(grp)
        else:
            grp = None

        catalogue_dict = {nom: (typename, serveur, fill, stroke)
                          for _, nom, typename, serveur, fill, stroke in CATALOGUE}
        urbanisme_names    = {nom for cat, nom, *_ in CATALOGUE if "Urbanisme" in cat}
        urbanisme_selected = [nom for nom in selected if nom in urbanisme_names]
        urbanisme_loaded   = []

        lyr_clip_effectif = self._territory_lyr
        extent_effectif   = self._territory_extent

        if self.chk_buffer.isChecked() and self._territory_lyr:
            self.lbl_status.setText("Calcul du buffer...")
            QApplication.processEvents()
            lyr_buf = self._apply_buffer(self._territory_lyr)
            if lyr_buf:
                lyr_clip_effectif = lyr_buf
                extent_effectif   = lyr_buf.extent()
                taille = self.txt_buffer_size.text().strip()
                unite  = self.combo_buffer_unit.currentText()
                self.lbl_status.setText(f"Buffer {taille} {unite} appliqué ✅")
                QApplication.processEvents()

        layers_loaded = []
        layers_empty  = []

        for i, nom in enumerate(selected):
            self.lbl_status.setText(f"Chargement : {nom}...")
            QApplication.processEvents()

            typename, serveur, fill, stroke = catalogue_dict[nom]

            if extent_effectif:
                ext = extent_effectif
                mx  = ext.width()  * 0.005
                my  = ext.height() * 0.005
                bbox_str = (f"{ext.xMinimum()-mx},{ext.yMinimum()-my},"
                            f"{ext.xMaximum()+mx},{ext.yMaximum()+my}")
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, bbox_str)
            else:
                uri, filtre_expr, is_gpu = build_wfs_uri(serveur, typename, None)

            # Cadastre via API Carto
            if typename == "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle" and lyr_clip_effectif:
                code_cadastre = (self._territory_code
                                 if self.combo_scale.currentText() == "Commune" else None)
                lyr = load_cadastre_parcelles_api(
                    lyr_clip_effectif, nom, self.lbl_status, QApplication,
                    code_insee=code_cadastre)
                if not lyr or not layer_has_features(lyr):
                    layers_empty.append(nom)
                    self.progress.setValue(i + 1)
                    QApplication.processEvents()
                    continue
                if self.chk_style.isChecked():
                    apply_style(lyr, fill, stroke)
                project.addMapLayer(lyr, False)
                (grp.addChildNode(QgsLayerTreeLayer(lyr)) if grp else root.addLayer(lyr))
                layers_loaded.append((nom, lyr))
                self.progress.setValue(i + 1)
                continue

            # Couches GPU
            if is_gpu and lyr_clip_effectif:
                lyr = load_gpu_layer(typename, filtre_expr, lyr_clip_effectif,
                                     nom, self.lbl_status, QApplication)
                if not lyr or not layer_has_features(lyr):
                    layers_empty.append(nom)
                    self.progress.setValue(i + 1)
                    QApplication.processEvents()
                    continue
                self.lbl_status.setText(f"GPU — filtrage spatial : {nom}...")
                QApplication.processEvents()
                try:
                    key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                          else 'native:clip'
                    params = ({'INPUT': lyr, 'PREDICATE': [0], 'INTERSECT': lyr_clip_effectif,
                                'OUTPUT': 'memory:'}
                               if self.chk_intersect_only.isChecked()
                               else {'INPUT': lyr, 'OVERLAY': lyr_clip_effectif, 'OUTPUT': 'memory:'})
                    lyr_c = processing.run(key, params)['OUTPUT']
                    lyr_c.setName(nom)
                    if layer_has_features(lyr_c):
                        lyr = lyr_c
                except Exception:
                    try:
                        params['INPUT'] = processing.run("native:fixgeometries",
                            {'INPUT': lyr, 'OUTPUT': 'memory:'})['OUTPUT']
                        lyr_c = processing.run(key, params)['OUTPUT']
                        lyr_c.setName(nom)
                        if layer_has_features(lyr_c):
                            lyr = lyr_c
                    except Exception as e:
                        self.lbl_status.setText(f"⚠ GPU clip échoué : {str(e)[:80]}")
                        QApplication.processEvents()
                if not layer_has_features(lyr):
                    layers_empty.append(nom)
                    self.progress.setValue(i + 1)
                    QApplication.processEvents()
                    continue
                if self.chk_style.isChecked():
                    apply_style(lyr, fill, stroke)
                project.addMapLayer(lyr, False)
                (grp.addChildNode(QgsLayerTreeLayer(lyr)) if grp else root.addLayer(lyr))
                layers_loaded.append((nom, lyr))
                if nom in urbanisme_names:
                    urbanisme_loaded.append(nom)
                self.progress.setValue(i + 1)
                continue

            # Couches WFS standard
            lyr = QgsVectorLayer(uri, nom, "WFS")
            if not lyr.isValid():
                layers_empty.append(nom)
                self.progress.setValue(i + 1)
                QApplication.processEvents()
                continue

            if self.chk_clip.isChecked() and lyr_clip_effectif:
                try:
                    key = 'native:extractbylocation' if self.chk_intersect_only.isChecked() \
                          else 'native:clip'
                    params = ({'INPUT': lyr, 'PREDICATE': [0], 'INTERSECT': lyr_clip_effectif,
                                'OUTPUT': 'memory:'}
                               if self.chk_intersect_only.isChecked()
                               else {'INPUT': lyr, 'OVERLAY': lyr_clip_effectif, 'OUTPUT': 'memory:'})
                    lyr_c = processing.run(key, params)['OUTPUT']
                    lyr_c.setName(nom)
                    lyr = lyr_c
                except Exception:
                    try:
                        params['INPUT'] = processing.run("native:fixgeometries",
                            {'INPUT': lyr, 'OUTPUT': 'memory:'})['OUTPUT']
                        lyr_c = processing.run(key, params)['OUTPUT']
                        lyr_c.setName(nom)
                        lyr = lyr_c
                    except Exception as e:
                        self.lbl_status.setText(f"⚠ Clip échoué : {str(e)[:60]}")
                        QApplication.processEvents()

            if filtre_expr and lyr.isValid() and lyr.featureCount() > 0:
                from qgis.core import QgsFeatureRequest, QgsExpression
                feats  = list(lyr.getFeatures(
                    QgsFeatureRequest(QgsExpression(filtre_expr))))
                crs_id = lyr.crs().authid()
                flds   = lyr.fields().toList()
                lyr_m  = QgsVectorLayer(f"Polygon?crs={crs_id}", nom, "memory")
                pr_m   = lyr_m.dataProvider()
                pr_m.addAttributes(flds)
                lyr_m.updateFields()
                pr_m.addFeatures(feats)
                lyr_m.updateExtents()
                lyr = lyr_m

            if not layer_has_features(lyr):
                layers_empty.append(nom)
                self.progress.setValue(i + 1)
                QApplication.processEvents()
                continue

            if self.chk_style.isChecked():
                apply_style(lyr, fill, stroke)
            project.addMapLayer(lyr, False)
            (grp.addChildNode(QgsLayerTreeLayer(lyr)) if grp else root.addLayer(lyr))
            layers_loaded.append((nom, lyr))
            self.progress.setValue(i + 1)

        # Recentrer la carte
        if extent_effectif:
            ext = extent_effectif
            mx  = ext.width()  * 0.1
            my  = ext.height() * 0.1
            self.iface.mapCanvas().setExtent(
                type(ext)(ext.xMinimum()-mx, ext.yMinimum()-my,
                          ext.xMaximum()+mx, ext.yMaximum()+my))
            self.iface.mapCanvas().refresh()

        if self.chk_gbif.isChecked():
            self._load_gbif(project, root, grp, extent_effectif, lyr_clip_effectif)

        if urbanisme_selected and not urbanisme_loaded:
            QMessageBox.information(self, "Données d'urbanisme",
                "La zone sélectionnée n'a pas de donnée d'urbanisme disponible.")

        if self.chk_export_excel.isChecked() and layers_loaded:
            territoire_label = (f"{self.combo_scale.currentText()}_"
                                f"{self.txt_search.text().strip() or 'France'}")
            buffer_label = (f"buffer_{self.txt_buffer_size.text().strip()}"
                            f"_{self.combo_buffer_unit.currentText()}"
                            if self.chk_buffer.isChecked() else "sans_buffer")
            self._export_excel(layers_loaded, territoire_label, buffer_label)

        nb_loaded = len(layers_loaded)
        self.lbl_status.setText(f"{nb_loaded} couche(s) chargée(s) avec succès !")
        self.lbl_status.setStyleSheet("color:#2A7A2A; font-weight:bold;")

        if layers_empty:
            QMessageBox.information(self, "Couches sans données",
                "Les couches suivantes ne contiennent aucune donnée sur la zone "
                "sélectionnée et n'ont pas été ajoutées au projet :\n\n"
                + "\n".join(f"• {nom}" for nom in layers_empty))

        self.btn_load.setEnabled(True)
        self._territory_extent = None
        self._territory_lyr    = None
        self._territory_code   = None
        self._suggestions      = {}
        self.txt_search.clear()
        self._completer_model.setStringList([])
        self.lbl_result.setText("")
        self.progress.setVisible(False)
