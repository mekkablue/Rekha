# encoding: utf-8

###########################################################################################################
#
#
#	Filter with dialog Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20with%20Dialog
#
#	For help on the use of Interface Builder:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

import objc
from GlyphsApp.plugins import *
from GlyphsApp import *

class RekhaMaker(FilterWithDialog):

	# Definitions of IBOutlets
	
	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text fields in dialog
	rekhaHeightField = objc.IBOutlet()
	rekhaThicknessField = objc.IBOutlet()
	rekhaOvershootField = objc.IBOutlet()
	rekhaDecomposeCheckbox = objc.IBOutlet()
	
	def settings(self):
		self.menuName = u'RekhaMaker'
		self.actionButtonLabel = 'Insert'
		
		# supported scripts:
		self.supportedScripts = ("gurmukhi","devanagari","bengali")
		
		# Load dialog from .nib (without .extension)
		self.loadNib('IBdialog', __file__)

	# On dialog show
	def start(self):

		# Set default setting if not present
		if not Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight']:
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight'] = 700.0
		if not Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness']:
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness'] = 100.0
		if not Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot']:
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot'] = 20.0
		if not Glyphs.defaults['com.mekkablue.RekhaMaker.decompose']:
			Glyphs.defaults['com.mekkablue.RekhaMaker.decompose'] = False

		# Set value of text field
		self.rekhaHeightField.setStringValue_(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight'])
		self.rekhaThicknessField.setStringValue_(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness'])
		self.rekhaOvershootField.setStringValue_(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot'])
		self.rekhaDecomposeCheckbox.setIntegerValue_(Glyphs.defaults['com.mekkablue.RekhaMaker.decompose'])
		
		# Set focus to text field
		self.rekhaHeightField.becomeFirstResponder()

	# Action triggered by UI
	@objc.IBAction
	def setrekhaHeight_( self, sender ):
		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight'] = sender.floatValue()
		# Trigger redraw
		self.update()

	@objc.IBAction
	def setrekhaThickness_( self, sender ):
		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness'] = sender.floatValue()
		# Trigger redraw
		self.update()

	@objc.IBAction
	def setrekhaOvershoot_( self, sender ):
		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot'] = sender.floatValue()
		# Trigger redraw
		self.update()

	@objc.IBAction
	def setDecompose_( self, sender ):
		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.RekhaMaker.decompose'] = sender.intValue()
		# Trigger redraw
		self.update()

	# Actual filter
	def filter(self, layer, inEditView, customParameters):
		
		# Called on font export, get value from customParameters
		if customParameters:
			if customParameters.has_key('height'):
				rekhaHeight = customParameters['height']
			else:
				rekhaHeight = 700.0
				
			if customParameters.has_key('thickness'):
				rekhaThickness = customParameters['thickness']
			else:
				rekhaThickness = 100.0
				
			if customParameters.has_key('overshoot'):
				rekhaOvershoot = customParameters['overshoot']
			else:
				rekhaOvershoot = 20.0

			if customParameters.has_key('decompose'):
				decompose = bool(customParameters['decompose'])
			else:
				decompose = False

		# Called through UI, use stored value
		else:
			rekhaHeight = float(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight'])
			rekhaThickness = float(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness'])
			rekhaOvershoot = float(Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot'])
			decompose = bool(Glyphs.defaults['com.mekkablue.RekhaMaker.decompose'])

		# Shift all nodes in x and y direction by the value
		thisGlyph = layer.glyph()
		if thisGlyph.script in self.supportedScripts:
			if thisGlyph.category == "Letter":
				
				# determine rekha origin:
				xOrigin = -rekhaOvershoot
				
				# draw rekha from the left if there is a stop anchor:
				if layer.anchors["rekha_stop"]:
					stopPosition = layer.anchors["rekha_stop"].position.x
					leftRekha = NSRect()
					leftRekha.origin = NSPoint( xOrigin, rekhaHeight )
					leftRekha.size = NSSize( stopPosition-xOrigin, rekhaThickness )
					self.drawRekhaInLayer( leftRekha, layer )
				
				# draw a rekha from the middle to the right if there is a rekha anchor:
				if layer.anchors["rekha"]:
					xOrigin = layer.anchors["rekha"].position.x
				
				# define rekha rectangle:
				rekha = NSRect()
				rekha.origin = NSPoint( xOrigin, rekhaHeight )
				rekha.size = NSSize( layer.width + rekhaOvershoot - xOrigin, rekhaThickness )
				self.drawRekhaInLayer( rekha, layer )
				
				if decompose:
					layer.decomposeComponents()
	
	def drawRekhaInLayer(self, rekha, layer):
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
		font = layer.font()
		if font:
			capName      = "_cap.rekha"
			capNameLeft  = capName + "Left"
			capNameRight = capName + "Right"
			capNames = (capName,capNameRight,capNameLeft)

			for i in (-1,1):
				
				# determine if a left or right or a general cap is present:
				insertedCapName = None
				if font.glyphs[capNames[i]]:
					insertedCapName = capNames[i]
				elif font.glyphs[capNames[0]]:
					insertedCapName = capNames[0]
				
				# if so, add the cap on the appropriate node:
				if insertedCapName:
					cap = GSHint()
					cap.type = CAP
					cap.name = insertedCapName
					cap.originNode = rectangle.nodes[i]
					cap.setOptions_(3) # fit
					layer.addHint_(cap)
	
	def generateCustomParameter( self ):
		return "%s; height:%s; thickness:%s; overshoot:%s; decompose:%s" % (
			self.__class__.__name__, 
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaHeight'],
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaThickness'],
			Glyphs.defaults['com.mekkablue.RekhaMaker.rekhaOvershoot'],
			Glyphs.defaults['com.mekkablue.RekhaMaker.decompose'],
		)
