# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	Rekha – combined Glyphs plug-in
#	Merges RekhaMaker (filter), RekhaViewer (reporter), and RekhaBrekha (decompose) in one .glyphsPlugin.
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSMenuItem, NSPoint, NSRect, NSSize

SUPPORTED_SCRIPTS = ("gurmukhi", "devanagari", "bengali")
PREF = "com.mekkablue.RekhaMaker"  # keep existing pref domain for backward compatibility


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _makeRekhaPath(rekha):
	"""Return a closed GSPath rectangle (direction -1) for the given NSRect."""
	ox, oy = rekha.origin.x, rekha.origin.y
	w, h   = rekha.size.width, rekha.size.height
	path = GSPath()
	for pos in (
		NSPoint(ox,     oy),
		NSPoint(ox + w, oy),
		NSPoint(ox + w, oy + h),
		NSPoint(ox,     oy + h),
	):
		node = GSNode()
		node.position = pos
		node.type = LINE
		path.nodes.append(node)
	path.closed = True
	if path.direction != -1:
		path.reverse()
	return path


def _capNamesForFont(font):
	"""Return (rightCapName, leftCapName) from font, None where absent."""
	if not font:
		return None, None
	base  = "_cap.rekha"
	right = base + "Right"
	left  = base + "Left"
	hasBase  = bool(font.glyphForName_(base))
	hasRight = bool(font.glyphForName_(right))
	hasLeft  = bool(font.glyphForName_(left))
	return (
		right if hasRight else (base if hasBase else None),
		left  if hasLeft  else (base if hasBase else None),
	)


def _addCapHints(path, layer, rightCap, leftCap):
	"""Attach _cap.rekha hints for nodes[1] (right) and nodes[-1] (left) of path."""
	for nodeIndex, capName in ((1, rightCap), (-1, leftCap)):
		if capName:
			cap = GSHint()
			cap.type = CAP
			cap.name = capName
			cap.originNode = path.nodes[nodeIndex]
			cap.setOptions_(3)  # fit
			layer.addHint_(cap)


def _addRekhaToLayer(rekha, layer, font):
	"""Insert a rekha rectangle with cap hints directly into layer."""
	path = _makeRekhaPath(rekha)
	try:
		layer.shapes.append(path)
	except AttributeError:
		layer.paths.append(path)
	_addCapHints(path, layer, *_capNamesForFont(font))


def _rekhaBezierPath(rekha, masterID, font, rightCap=None, leftCap=None):
	"""Build rekha in a scratch layer and return its NSBezierPath."""
	if font is None:
		font = Glyphs.font
	if font is None:
		return None
	glyph = GSGlyph()
	glyph.parent = font
	scratch = glyph.layers[masterID]
	if scratch is None:
		return None
	path = _makeRekhaPath(rekha)
	try:
		scratch.shapes.append(path)
	except AttributeError:
		scratch.paths.append(path)
	if rightCap or leftCap:
		_addCapHints(path, scratch, rightCap, leftCap)
		scratch.decomposeCorners()
	return scratch.bezierPath


def _rekhaParamsForMaster(master):
	"""Return (height, thickness, overshoot) from master custom parameters, or defaults.

	Checks (in order):
	  1. 'Rekha' / 'rekha'  →  comma-separated  "700, 100, 20"
	  2. 'RekhaMaker' filter parameter  →  "RekhaMaker; height:560; thickness:70; overshoot:0; …"
	"""
	defaults = (700.0, 100.0, 20.0)

	param = master.customParameters["Rekha"] or master.customParameters["rekha"]
	if param:
		try:
			vals = [float(x.strip()) for x in param.split(",")]
			return (
				vals[0] if len(vals) > 0 else defaults[0],
				vals[1] if len(vals) > 1 else defaults[1],
				vals[2] if len(vals) > 2 else defaults[2],
			)
		except Exception:
			pass

	filterParam = master.customParameters["RekhaMaker"]
	if filterParam:
		try:
			kvs = {}
			for part in filterParam.split(";"):
				part = part.strip()
				if ":" in part:
					k, v = part.split(":", 1)
					kvs[k.strip()] = float(v.strip())
			return (
				kvs.get("height",    defaults[0]),
				kvs.get("thickness", defaults[1]),
				kvs.get("overshoot", defaults[2]),
			)
		except Exception:
			pass

	return defaults


def _rekhaRects(layer, height, thickness, overshoot):
	"""
	Return a list of NSRect segments for the rekha in layer.

	All anchors whose name starts with 'rekha' are sorted by x position.
	Anchors starting with 'rekha_stop' (any suffix) end the current segment;
	all other 'rekha*' anchors start or resume a segment at that x.
	With no anchors a single full-width segment is produced.
	"""
	rects  = []
	xStart = -overshoot
	active = True  # rekha is on from the left edge

	anchors = sorted(
		[a for a in layer.anchors if a.name.startswith("rekha")],
		key=lambda a: a.position.x,
	)

	for anchor in anchors:
		ax = anchor.position.x
		if anchor.name.startswith("rekha_stop"):
			if active:
				r = NSRect()
				r.origin = NSPoint(xStart, height)
				r.size   = NSSize(ax - xStart, thickness)
				rects.append(r)
				active = False
		else:
			# Non-stop rekha anchor: start (or resume) from this x.
			# When already active this acts as an indent of the start position.
			xStart = ax
			active = True

	if active:
		r = NSRect()
		r.origin = NSPoint(xStart, height)
		r.size   = NSSize(layer.width + overshoot - xStart, thickness)
		rects.append(r)

	return rects


def _drawRekhaCap(layer, rekhaHeight=100):
	"""Add an open rekha cap path to layer. rekhaHeight should equal the rekha thickness."""
	coords = (
		(0, 5),
		(0, -10),
		(rekhaHeight, -10),
		(rekhaHeight, 5),
	)
	path = GSPath()
	for coord in coords:
		path.nodes.append(GSNode(coord))
	path.closed = False
	try:
		layer.shapes.append(path)
	except AttributeError:
		layer.paths.append(path)


def _decomposeIndicComponents(layer):
	"""Decompose components whose base glyph is a supported-script Letter (RekhaBrekha logic)."""
	indexes = [
		i for i, comp in enumerate(layer.components)
		if comp.component.export
		and comp.component.script in SUPPORTED_SCRIPTS
		and comp.component.category == "Letter"
	]
	for i in reversed(indexes):
		layer.components[i].decompose()


# ---------------------------------------------------------------------------
# RekhaMaker – filter with dialog
# ---------------------------------------------------------------------------

class RekhaMaker(FilterWithDialog):

	dialog                 = objc.IBOutlet()
	rekhaHeightField       = objc.IBOutlet()
	rekhaThicknessField    = objc.IBOutlet()
	rekhaOvershootField    = objc.IBOutlet()
	rekhaDecomposeCheckbox = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.menuName = "RekhaMaker"
		self.actionButtonLabel = "Insert"
		self.loadNib("IBdialog", __file__)

	@objc.python_method
	def start(self):
		height    = Glyphs.defaults[PREF + ".rekhaHeight"]    or 700.0
		thickness = Glyphs.defaults[PREF + ".rekhaThickness"] or 100.0
		overshoot = Glyphs.defaults[PREF + ".rekhaOvershoot"] or 20.0

		font = Glyphs.font
		if font:
			master = (
				font.selectedLayers[0].master if font.selectedLayers
				else font.selectedFontMaster
			)
			if master:
				try:
					height, thickness, overshoot = _rekhaParamsForMaster(master)
				except Exception as e:
					print("⚠️ Could not read Rekha master parameter: %s" % e)

		Glyphs.defaults[PREF + ".rekhaHeight"]    = height
		Glyphs.defaults[PREF + ".rekhaThickness"] = thickness
		Glyphs.defaults[PREF + ".rekhaOvershoot"] = overshoot
		if Glyphs.defaults[PREF + ".decompose"] is None:
			Glyphs.defaults[PREF + ".decompose"] = False

		self.rekhaHeightField.setStringValue_(Glyphs.defaults[PREF + ".rekhaHeight"])
		self.rekhaThicknessField.setStringValue_(Glyphs.defaults[PREF + ".rekhaThickness"])
		self.rekhaOvershootField.setStringValue_(Glyphs.defaults[PREF + ".rekhaOvershoot"])
		self.rekhaDecomposeCheckbox.setIntegerValue_(Glyphs.defaults[PREF + ".decompose"])
		self.rekhaHeightField.becomeFirstResponder()

	@objc.IBAction
	def setrekhaHeight_(self, sender):
		Glyphs.defaults[PREF + ".rekhaHeight"] = sender.floatValue()
		self.update()

	@objc.IBAction
	def setrekhaThickness_(self, sender):
		Glyphs.defaults[PREF + ".rekhaThickness"] = sender.floatValue()
		self.update()

	@objc.IBAction
	def setrekhaOvershoot_(self, sender):
		Glyphs.defaults[PREF + ".rekhaOvershoot"] = sender.floatValue()
		self.update()

	@objc.IBAction
	def setDecompose_(self, sender):
		Glyphs.defaults[PREF + ".decompose"] = sender.intValue()
		self.update()

	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		if customParameters:
			height    = float(customParameters['height'])    if 'height'    in customParameters else 700.0
			thickness = float(customParameters['thickness']) if 'thickness' in customParameters else 100.0
			overshoot = float(customParameters['overshoot']) if 'overshoot' in customParameters else 20.0
			decompose = bool(customParameters['decompose'])  if 'decompose' in customParameters else False
		else:
			height    = float(Glyphs.defaults[PREF + ".rekhaHeight"]    or 700.0)
			thickness = float(Glyphs.defaults[PREF + ".rekhaThickness"] or 100.0)
			overshoot = float(Glyphs.defaults[PREF + ".rekhaOvershoot"] or 20.0)
			decompose = bool(Glyphs.defaults[PREF + ".decompose"])

		if not layer:
			return
		glyph = layer.glyph()
		if not glyph or glyph.script not in SUPPORTED_SCRIPTS or glyph.category != "Letter":
			return

		if decompose:
			_decomposeIndicComponents(layer)

		font = layer.font()
		for rect in _rekhaRects(layer, height, thickness, overshoot):
			_addRekhaToLayer(rect, layer, font)

	@objc.python_method
	def generateCustomParameter(self):
		return "%s; height:%s; thickness:%s; overshoot:%s; decompose:%s" % (
			self.__class__.__name__,
			Glyphs.defaults[PREF + ".rekhaHeight"],
			Glyphs.defaults[PREF + ".rekhaThickness"],
			Glyphs.defaults[PREF + ".rekhaOvershoot"],
			Glyphs.defaults[PREF + ".decompose"],
		)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__


# ---------------------------------------------------------------------------
# RekhaViewer – reporter
# ---------------------------------------------------------------------------

class RekhaViewer(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = "Rekha"

	@objc.python_method
	def _drawRekha(self, layer):
		if not layer:
			return
		glyph = layer.glyph()
		if not glyph or glyph.script not in SUPPORTED_SCRIPTS or glyph.category != "Letter":
			return
		master = layer.associatedFontMaster()
		if not master:
			return
		height, thickness, overshoot = _rekhaParamsForMaster(master)
		font = layer.font()
		rightCap, leftCap = _capNamesForFont(font)
		masterID = layer.associatedMasterId
		for rect in _rekhaRects(layer, height, thickness, overshoot):
			bp = _rekhaBezierPath(rect, masterID, font, rightCap, leftCap)
			if bp:
				bp.fill()

	@objc.python_method
	def background(self, layer):
		NSColor.placeholderTextColor().set()
		self._drawRekha(layer)

	def needsExtraMainOutlineDrawingForInactiveLayer_(self, layer):
		return True

	@objc.python_method
	def inactiveLayer(self, layer):
		NSColor.textColor().set()
		self._drawRekha(layer)

	@objc.python_method
	def inactiveLayerBackground(self, layer):
		NSColor.textColor().set()
		self._drawRekha(layer)

	@objc.python_method
	def preview(self, layer):
		NSColor.textColor().set()
		self._drawRekha(layer)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__


# ---------------------------------------------------------------------------
# RekhaCapMenu – general plug-in: Glyph menu item "Add Rekha Cap"
# ---------------------------------------------------------------------------

class RekhaCapMenu(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = "RekhaCapMenu"

	@objc.python_method
	def start(self):
		menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
			"Add Rekha Cap",
			self.addRekhaCap_,
			"",
		)
		menuItem.setTarget_(self)
		Glyphs.menu[GLYPH_MENU].append(menuItem)

	@objc.python_method
	def _hasDevanagari(self):
		font = Glyphs.font
		return bool(font) and any(g.script == "devanagari" for g in font.glyphs)

	def validateMenuItem_(self, menuItem):
		"""Gray out the item when the frontmost font has no Devanagari glyph."""
		return self._hasDevanagari()

	def addRekhaCap_(self, sender):
		font = Glyphs.font
		if not font:
			return

		capName = "_cap.rekha"

		if not font.glyphForName_(capName):
			capGlyph = GSGlyph()
			capGlyph.name = capName
			font.glyphs.append(capGlyph)

		capGlyph = font.glyphForName_(capName)

		for layer in capGlyph.layers:
			if layer.associatedMasterId == layer.layerId:  # master layers only
				master = layer.associatedFontMaster()
				_, thickness, _ = _rekhaParamsForMaster(master)
				_drawRekhaCap(layer, thickness)

		font.newTab("/" + capName)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
