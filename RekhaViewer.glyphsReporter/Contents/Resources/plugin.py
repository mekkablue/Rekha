# encoding: utf-8
from __future__ import division, print_function, unicode_literals

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

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

class RekhaViewer(ReporterPlugin):
	
	@objc.python_method
	def settings(self):
		self.menuName = u'Rekha'
	
	@objc.python_method
	def rekhaBezierForMasterIDWithCapInFont(self, rekha, masterID, leftCap=None, rightCap=None, font=None):
		glyph = GSGlyph()
		if font:
			glyph.parent = font
		elif Glyphs.font:
			glyph.parent = Glyphs.font
		else:
			return None
			
		layer = glyph.layers[masterID]
		if layer is None:
			return None
			
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
		
		# add caps if present in font:
		if rightCap or leftCap:
			caps = (None, rightCap, leftCap)
			for i in (-1,1):
				if caps[i] != None and caps[i].startswith("_cap."):
					cap = GSHint()
					cap.type = CAP
					cap.name = caps[i]
					cap.originNode = rectangle.nodes[i]
					cap.setOptions_(3) # fit
					layer.addHint_(cap)
			layer.decomposeCorners()
			
		# return the NSBezierPath
		return layer.bezierPath
	
	@objc.python_method
	def drawRekha(self, layer):
		defaults = (700,100,20) # height, thickness, overshoot
		thisGlyph = layer.glyph()
		if thisGlyph and thisGlyph.script in ("gurmukhi","devanagari","bengali"):
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
				leftCap, rightCap = None, None
				font = layer.parent.parent
				if font:
					generalCap = "_cap.rekha"
					if font.glyphs[generalCap]:
						leftCap, rightCap = generalCap, generalCap
					if font.glyphs[generalCap+"Left"]:
						leftCap = generalCap+"Left"
					if font.glyphs[generalCap+"Right"]:
						rightCap = generalCap+"Right"
				
				if layer.anchors["rekha_stop"]:
					stopPosition = layer.anchors["rekha_stop"].position.x
					LeftRekha = NSRect()
					LeftRekha.origin = NSPoint(xOrigin, RekhaHeight)
					LeftRekha.size = NSSize(stopPosition-xOrigin, RekhaThickness)
					LeftRekhaBezierPath = self.rekhaBezierForMasterIDWithCapInFont(LeftRekha, layer.associatedMasterId, leftCap, rightCap, font)
					LeftRekhaBezierPath.fill()
					
				if layer.anchors["rekha"]:
					xOrigin = layer.anchors["rekha"].position.x
		
				Rekha = NSRect()
				Rekha.origin = NSPoint(xOrigin, RekhaHeight)
				Rekha.size = NSSize(layer.width+RekhaOvershoot-xOrigin, RekhaThickness)
				RekhaBezierPath = self.rekhaBezierForMasterIDWithCapInFont(Rekha, layer.associatedMasterId, leftCap, rightCap)
				# only draw if not None:
				if RekhaBezierPath:
					RekhaBezierPath.fill()
	
	@objc.python_method
	def background(self, layer):
		NSColor.grayColor().set()
		self.drawRekha(layer)
	
	@objc.python_method
	def needsExtraMainOutlineDrawingForInactiveLayer_(self, Layer):
		return True
	
	@objc.python_method
	def inactiveLayers(self, layer):
		# draw rekha:
		NSColor.blackColor().set()
		self.drawRekha(layer)
	
	@objc.python_method
	def preview(self, layer):
		# draw rekha:
		NSColor.orangeColor().set()
		self.drawRekha(layer)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
