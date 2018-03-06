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

from GlyphsApp import *
from GlyphsApp.plugins import *

class RekhaViewer(ReporterPlugin):

	def settings(self):
		self.menuName = u'Rekha'
	
	def rekhaBezierForMasterID(self, rekha, masterID, capName=""):
		layer = GSLayer()
		layer.setAssociatedMasterId_(masterID)
		origin = rekha.origin
		width = rekha.size.width
		height = rekha.size.height
		
		# create rectangle path:
		rectangle = GSPath()
		nodePositions = (
			NSPoint( origin.x,       origin.y ),
			NSPoint( origin.x+width, origin.y ),
			NSPoint( origin.x+width, origin.y+height ),
			NSPoint( origin.x,       origin.y+height ),
		)
		for thisPosition in nodePositions:
			newNode = GSNode()
			newNode.position = thisPosition
			newNode.type = LINE
			rectangle.nodes.append(newNode)
		rectangle.closed = True
		
		# correct path direction:
		if rectangle.direction != -1:
			rectangle.reverse()
			
		# insert rectangle into layer:
		layer.paths.append(rectangle)
		
		for i in (-1,1):
			cap = GSHint()
			cap.type = CAP
			cap.name = capName
			cap.originNode = rectangle.nodes[i]
			cap.setOptions_(3) # fit
			layer.addHint_(cap)
		
		# return the NSBezierPath
		return layer.bezierPath
	
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
				
				# add caps if present in font:
				capName = None
				font = layer.parent.parent
				if font:
					if font.glyphs["_cap.rekha"]:
						capName = "_cap.rekha"
				
				if layer.anchors["rekha_stop"]:
					stopPosition = layer.anchors["rekha_stop"].position.x
					LeftRekha = NSRect()
					LeftRekha.origin = NSPoint(xOrigin, RekhaHeight)
					LeftRekha.size = NSSize(stopPosition-xOrigin, RekhaThickness)
					LeftRekhaBezierPath = self.rekhaBezierForMasterID(LeftRekha, layer.associatedMasterId, capName)
					LeftRekhaBezierPath.fill()
					
				if layer.anchors["rekha"]:
					xOrigin = layer.anchors["rekha"].position.x
		
				Rekha = NSRect()
				Rekha.origin = NSPoint(xOrigin, RekhaHeight)
				Rekha.size = NSSize(layer.width+RekhaOvershoot-xOrigin, RekhaThickness)
				RekhaBezierPath = self.rekhaBezierForMasterID(Rekha, layer.associatedMasterId, capName)
				RekhaBezierPath.fill()
	
	def background(self, layer):
		NSColor.grayColor().set()
		self.drawRekha(layer)
	
	def needsExtraMainOutlineDrawingForInactiveLayer_(self, Layer):
		return True
	
	def inactiveLayers(self, layer):
		# draw rekha:
		NSColor.blackColor().set()
		self.drawRekha(layer)
	
	def preview(self, layer):
		# draw rekha:
		NSColor.orangeColor().set()
		self.drawRekha(layer)
		