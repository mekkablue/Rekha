# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################


from GlyphsApp.plugins import *

class RekhaViewer(ReporterPlugin):

	def settings(self):
		self.menuName = u'Rekha'
	
	def drawRekha(self, layer):
		defaults = (700,100,20) # height, thickness, overshoot
		thisGlyph = layer.glyph()
		if thisGlyph.script in ("gurmukhi","devanagari","bengali"):
			if thisGlyph.category == "Letter":
				RekhaInfo = layer.associatedFontMaster().customParameters["rekha"]
				if not RekhaInfo:
					RekhaInfo = layer.associatedFontMaster().customParameters["Rekha"]
				if not RekhaInfo:
					RekhaInfo = ",".join([str(x) for x in defaults])
				RekhaValues = [float(piece) for piece in RekhaInfo.split(',')]
				
				try:
					RekhaHeight = RekhaValues[0]
				except:
					RekhaHeight = defaults[0]
					
				try:
					RekhaThickness = RekhaValues[1]
				except:
					RekhaThickness = defaults[1]
				
				try:
					RekhaOvershoot = RekhaValues[2]
				except:
					RekhaOvershoot = defaults[2]
		
				xOrigin = -RekhaOvershoot

				if layer.anchors["rekha_stop"]:
					stopPosition = layer.anchors["rekha_stop"].position.x
					LeftRekha = NSRect()
					LeftRekha.origin = NSPoint(xOrigin, RekhaHeight)
					LeftRekha.size = NSSize(stopPosition-xOrigin, RekhaThickness)
					NSBezierPath.fillRect_(LeftRekha)

				if layer.anchors["rekha"]:
					xOrigin = layer.anchors["rekha"].position.x
		
				Rekha = NSRect()
				Rekha.origin = NSPoint(xOrigin, RekhaHeight)
				Rekha.size = NSSize(layer.width+RekhaOvershoot-xOrigin, RekhaThickness)
				NSBezierPath.fillRect_(Rekha)
	
	def background(self, layer):
		NSColor.grayColor().set()
		self.drawRekha(layer)

	def inactiveLayers(self, layer):
		NSColor.blackColor().set()
		
		# draw letter
		if layer.paths:
			layer.bezierPath.fill()
		if layer.components:
			for component in layer.components:
				component.bezierPath.fill()
		
		# draw rekha:
		self.drawRekha(layer)

	def preview(self, layer):
		NSColor.orangeColor().set()
		
		# draw letter
		if layer.paths:
			layer.bezierPath.fill()
		if layer.components:
			for component in layer.components:
				component.bezierPath.fill()
		
		# draw rekha:
		self.drawRekha(layer)
		