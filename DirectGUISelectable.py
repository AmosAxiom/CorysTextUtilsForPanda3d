#This is mostly copy pasted from the panda3d source for DirectEntry and
#DirectLabel
#
#I wanted versions of both that allow you to select sections of text
#for better text editing functionality.
#
#Strangely, something seems to break when I try to make a subclass of DirectEntry
#and just add my new code
#I don't fully understand it so I did this instead I'm sure at some point someone
#will tell me how to not copy all the code.
#Sorry for being a terrible python programmer.
#-Cory

__all__ = ['DirectGUISelectable']

from CorysTextUtils import TextMapper
from CorysTextUtils import Panda3dTextFormatUtils as TFU

import math

from panda3d.core import *
from direct.showbase import ShowBaseGlobal
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import *
from direct.gui.OnscreenText import OnscreenText
import sys
# import this to make sure it gets pulled into the publish
import encodings.utf_8
from direct.showbase.DirectObject import DirectObject

# DirectEntry States:
ENTRY_FOCUS_STATE    = PGEntry.SFocus      # 0
ENTRY_NO_FOCUS_STATE = PGEntry.SNoFocus    # 1
ENTRY_INACTIVE_STATE = PGEntry.SInactive   # 2

class DirectEntrySelectable(DirectFrame):

	directWtext = ConfigVariableBool('direct-wtext', 1)

	AllowCapNamePrefixes = ("Al", "Ap", "Ben", "De", "Del", "Della", "Delle", "Der", "Di", "Du",
							"El", "Fitz", "La", "Las", "Le", "Les", "Lo", "Los",
							"Mac", "St", "Te", "Ten", "Van", "Von", )
	ForceCapNamePrefixes = ("D'", "DeLa", "Dell'", "L'", "M'", "Mc", "O'", )

	sMoveKeyModifiers = ['shift', 'control', 'alt']
	sMoveKeyEquivalents = ['arrow_left', 'arrow_right', 'home', 'end']

	#Static utlity function to generate all combinations of an input list but 
	#preserve the order in which the list items appear when combining.
	#This is just to ensure all modifier keys are accepted within this function.
	#And also I didn't want to import the combinatorics module
	def orderedCombinations(inputList):
		if len(inputList) == 0:
			return [[]]
		cs = []
		for c in DirectEntrySelectable.orderedCombinations(inputList[:-1]):
			cs += [c, c+[inputList[-1]]]
		return cs

	def __init__(self, parent = None, **kw):
		# Inherits from DirectFrame
		# A Direct Frame can have:
		# - A background texture (pass in path to image, or Texture Card)
		# - A midground geometry item (pass in geometry)
		# - A foreground text Node (pass in text string or Onscreen Text)
		# For a direct entry:
		# Each button has 3 states (focus, noFocus, disabled)
		# The same image/geom/text can be used for all three states or each
		# state can have a different text/geom/image
		# State transitions happen automatically based upon mouse interaction
		optiondefs = (
			# Define type of DirectGuiWidget
			('pgFunc',          PGEntry,          None),
			('numStates',       3,                None),
			('state',           DGG.NORMAL,       None),
			('entryFont',       None,             DGG.INITOPT),
			('width',           10,               self.updateWidth),
			('numLines',        1,                self.updateNumLines),
			('focus',           0,                self.setFocus),
			('cursorKeys',      1,                self.setCursorKeysActive),
			('obscured',        0,                self.setObscureMode),
			# Setting backgroundFocus allows the entry box to get keyboard
			# events that are not handled by other things (i.e. events that
			# fall through to the background):
			('backgroundFocus', 0,                self.setBackgroundFocus),
			# Text used for the PGEntry text node
			# NOTE: This overrides the DirectFrame text option
			('initialText',     '',               DGG.INITOPT),
			# Enable or disable text overflow scrolling
			('overflow',        0,                self.setOverflowMode),
			# Command to be called on hitting Enter
			('command',        None,              None),
			('extraArgs',      [],                None),
			# Command to be called when enter is hit but we fail to submit
			('failedCommand',  None,              None),
			('failedExtraArgs',[],                None),
			# commands to be called when focus is gained or lost
			('focusInCommand', None,              None),
			('focusInExtraArgs', [],              None),
			('focusOutCommand', None,             None),
			('focusOutExtraArgs', [],             None),
			# Sounds to be used for button events
			('rolloverSound',   DGG.getDefaultRolloverSound(), self.setRolloverSound),
			('clickSound',      DGG.getDefaultClickSound(),    self.setClickSound),
			('autoCapitalize',  0,                None),
			('autoCapitalizeAllowPrefixes', DirectEntrySelectable.AllowCapNamePrefixes, None),
			('autoCapitalizeForcePrefixes', DirectEntrySelectable.ForceCapNamePrefixes, None),
			('selectable',		False,				None),
			('textSelectionColor', (0,0,0,0.4),    self.setTextSelectionColor),
			('textSelectionColorGrad', None, self.setTextSelectionColor)
			)
		# Merge keyword options with default options
		self.defineoptions(kw, optiondefs)

		# Initialize superclasses
		DirectFrame.__init__(self, parent)

		if self['entryFont'] == None:
			font = DGG.getDefaultFont()
		else:
			font = self['entryFont']

		# Create Text Node Component
		self.onscreenText = self.createcomponent(
			'text', (), None,
			OnscreenText,
			(), parent = ShowBaseGlobal.hidden,
			# Pass in empty text to avoid extra work, since its really
			# The PGEntry which will use the TextNode to generate geometry
			text = '',
			align = TextNode.ALeft,
			font = font,
			scale = 1,
			# Don't get rid of the text node
			mayChange = 1)

		# We can get rid of the node path since we're just using the
		# onscreenText as an easy way to access a text node as a
		# component
		self.onscreenText.removeNode()

		# Bind command function
		self.bind(DGG.ACCEPT, self.commandFunc)
		self.bind(DGG.ACCEPTFAILED, self.failedCommandFunc)

		self.accept(self.guiItem.getFocusInEvent(), self.focusInCommandFunc)
		self.accept(self.guiItem.getFocusOutEvent(), self.focusOutCommandFunc)

		# Call option initialization functions
		self.initialiseoptions(DirectEntrySelectable)

		if not hasattr(self, 'autoCapitalizeAllowPrefixes'):
			self.autoCapitalizeAllowPrefixes = DirectEntrySelectable.AllowCapNamePrefixes
		if not hasattr(self, 'autoCapitalizeForcePrefixes'):
			self.autoCapitalizeForcePrefixes = DirectEntrySelectable.ForceCapNamePrefixes

		# Update TextNodes for each state
		for i in range(self['numStates']):
			self.guiItem.setTextDef(i, self.onscreenText.textNode)

		# Now we should call setup() again to make sure it has the
		# right font def.
		self.setup()

		# Update initial text
		self.unicodeText = 0
		if self['initialText']:
			self.enterText(self['initialText'])

		# Initialize the selecting variables to tell if the user is trying to hilight text
		self.__selectingText = False
		self.__textSelectionStart = 0
		self.__textSelectionEnd = 0

		self.__prevText = ''

		self.__textMapper = TextMapper(self.guiItem.getTextNode())

		self.__keysPressed = {
			'mouse1': False,
			'shift': False,
			'anymovekey': False,
			'delete': False,
			'backspace': False
		}
		self.__mouseCoords = [0,0]

		vdata = GeomVertexData('testvertexdata', GeomVertexFormat.getV3c4(), Geom.UHStatic)
		vdata.setNumRows(4)

		vertices = GeomVertexWriter(vdata, 'vertex')
		colors = GeomVertexWriter(vdata, 'color')

		vertices.addData3(0,0,0.1)
		colors.addData4(*self['textSelectionColor'])
		vertices.addData3(0,0,0)
		colors.addData4(0,0.5,0,0.5)
		vertices.addData3(0.1,0,0.1)
		colors.addData4(*self['textSelectionColor'])
		vertices.addData3(0.1,0,0)
		colors.addData4(0,0.5,0,0.5)

		primitive = GeomTristrips(Geom.UHStatic)
		primitive.add_next_vertices(4)
		primitive.closePrimitive()

		tmpgeom = Geom(vdata)
		tmpgeom.addPrimitive(primitive)

		self.__textHilightGeomNode = GeomNode(self.guiItem.getId()+'-textHilight')
		self.__textHilightGeomNode.addGeom(tmpgeom)

		self.__textHilightNodePath = self.attachNewNode(self.__textHilightGeomNode, 100)
		self.__textHilightNodePath.setTransparency(TransparencyAttrib.MAlpha)
		self.__textHilightNodePath.hide()

	def destroy(self):
		self.ignoreAll()
		self._autoCapListener.ignoreAll()
		DirectFrame.destroy(self)

	def __setKeyPressed(self, keyName, newVal):
		if keyName in self.__keysPressed.keys():
			if newVal != self.__keysPressed[keyName]:
				self.__keysPressed[keyName] = newVal

			if keyName == 'backspace':
				if newVal:
					self.__backspaceFunc()
			elif keyName == 'delete':
				if newVal:
					self.__deleteFunc()
			else:
				self.__updateSelectingPerKeys(keyName)


	def __updateSelectingPerKeys(self, newKey):
		if newKey == 'mouse1':
			if self.__keysPressed['mouse1']:
				self.__selectingText = self.__keysPressed['shift']
		elif newKey == 'shift':
			if not (self.__keysPressed['shift'] or self.__keysPressed['mouse1']):
				self.__selectingText = False
		elif newKey == 'anymovekey':
			self.__selectingText = self.__keysPressed['anymovekey'] and self.__keysPressed['shift']

	def __updateTextSelection(self, *args):
		if not self.__selectingText:
			self.__textSelectionStart = self.guiItem.getCursorPosition()
		
		self.__textSelectionEnd = self.guiItem.getCursorPosition()

		self.__selectingText = False
		self.render_selection()

	# removes the selection (not the text with in it, just makes the selection nothing)
	def remove_selection(self):
		self.__textSelectionStart = self.guiItem.getCursorPosition()
		self.__textSelectionEnd = self.guiItem.getCursorPosition()

		self.render_selection()

	#updates the selection box
	def render_selection(self):
		print('selection:', self.getTextSelection())
		print(self.getSelectedText())


		if self.__textSelectionStart == self.__textSelectionEnd:
			self.__textHilightNodePath.hide()
		else:
			self.__textHilightNodePath.setScale(self['text_scale'][0], 1, self['text_scale'][1])
			selsindex = self.__textSelectionStart
			seleindex = self.__textSelectionEnd

			if self.__textSelectionEnd < self.__textSelectionStart:
				seleindex = self.__textSelectionStart
				selsindex = self.__textSelectionEnd

			seltopcolor = (0,0,0,0.4)
			selbotcolor = (0,0,0,0.4)

			if (type(self['textSelectionColor']) is tuple) and (len(self['textSelectionColor']) == 4):
				seltopcolor = self['textSelectionColor']
				if (type(self['textSelectionColorGrad']) is tuple) and (len(self['textSelectionColorGrad']) == 4):
					selbotcolor = self['textSelectionColorGrad']
				else:
					selbotcolor = self['textSelectionColor']

			selsrow = self.__textMapper.textAssembler.calcR(selsindex)
			selerow = self.__textMapper.textAssembler.calcR(seleindex)

			txtUl = self.__textMapper.textAssembler.getUl()
			txtLr = self.__textMapper.textAssembler.getLr()

			currgeom = self.__textHilightGeomNode.modifyGeom(0)
			currvertexdata = GeomVertexData('textselverts', GeomVertexFormat.getV3c4(), Geom.UHStatic)
			currprimitive = GeomTristrips(Geom.UHStatic)

			currvertexdata.setNumRows((selerow-selsrow+1)*4)

			selvertex = GeomVertexWriter(currvertexdata, 'vertex')
			selcolor = GeomVertexWriter(currvertexdata, 'color')

			for cselrow in range(selsrow, selerow+1):
				currtopY = txtUl.getY()
				currbotY = txtLr.getY()
				currleftX = txtUl.getX()
				currrightX = txtLr.getX()

				if cselrow < self.__textMapper.numRows:
					currtopY = self.__textMapper.rowBounds[cselrow][0]
					currbotY = self.__textMapper.rowBounds[cselrow][1]

				if cselrow == selsrow:
					currleftX = self.__textMapper.textAssembler.getXpos(cselrow, self.__textMapper.textAssembler.calcC(selsindex))
				if cselrow == selerow:
					currrightX = self.__textMapper.textAssembler.getXpos(cselrow, self.__textMapper.textAssembler.calcC(seleindex))

				selvertex.setData3(currleftX, 0, currtopY)
				selcolor.setData4(*seltopcolor)
				selvertex.setData3(currleftX, 0, currbotY)
				selcolor.setData4(*selbotcolor)
				selvertex.setData3(currrightX, 0, currtopY)
				selcolor.setData4(*seltopcolor)
				selvertex.setData3(currrightX, 0, currbotY)
				selcolor.setData4(*selbotcolor)

				currprimitive.add_next_vertices(4)
				currprimitive.closePrimitive()

			currgeom.clearPrimitives()
			currgeom.setVertexData(currvertexdata)
			currgeom.addPrimitive(currprimitive)
			self.__textHilightNodePath.show()

	# Takes either a tuple containing (start, end) or start, end as two separate arguments.
	def setTextSelection(self, *args):
		start=0
		end=0

		if (len(args) == 1) and type(args[0]) is tuple:
			start = args[0][0]
			end = args[0][1]
		elif (len(args) == 2):
			start = args[0]
			end = args[1]
		else:
			raise TypeError('this method takes a tuple or two integers')

		if (type(start) is int) and (type(end) is int):
			self.__textSelectionStart = start
			self.__textSelectionEnd = end
			self.guiItem.setCursorPosition(end)
		else:
			raise TypeError('Text selection start and end indices must be integers.')

		self.render_selection()

	def __mousePollTask(self, task):
		if base.mouseWatcherNode.hasMouse():
			mpos = base.mouseWatcherNode.getMouse()
			self.__mouseCoords = [mpos.x, mpos.y]

			if task or self.__keysPressed['shift']:
				self.__selectingText = True
			self.__cursorToMouse()
		if task:
			return task.again


	def getTextSelection(self):
		return (self.__textSelectionStart, self.__textSelectionEnd)

	def getSelectedText(self):
		if self.__textSelectionStart < self.__textSelectionEnd :
			return self.guiItem.getPlainText()[self.__textSelectionStart:self.__textSelectionEnd]
		else :
			return self.guiItem.getPlainText()[self.__textSelectionEnd:self.__textSelectionStart]

	def __initCursorFollowMouse(self, *args):
		print('started following mouse')
		self.__updateTextStats()

		self.__mousePollTask(None)

		if not self.__selectingText:
			self.__textSelectionStart = self.guiItem.getCursorPosition()

		self.__textSelectionEnd = self.guiItem.getCursorPosition()
		self.__setKeyPressed('mouse1', True)
		taskMgr.doMethodLater(0.05, self.__mousePollTask, self.guiItem.getId()+'-mousePoller')

	def __stopCursorFollowMouse(self, *args):
		print('stopped following mouse')
		taskMgr.remove(self.guiItem.getId()+'-mousePoller')
		self.__setKeyPressed('mouse1', False)

	def __cursorToMouse(self):
		mat = self.getMat(render2d)
		mat.invertInPlace()
		tmppoint = mat.xformPoint(Point3.rfu(self.__mouseCoords[0], 0.0, self.__mouseCoords[1]))

		tmpmX = tmppoint.getX()/self['text_scale'][0]
		tmpmY = tmppoint.getZ()/self['text_scale'][1]

		self.guiItem.setCursorPosition(self.__textMapper.xyToCursorIndex(tmpmX, tmpmY))

	def __updateTextStats(self):
		self.__textMapper.mapPGEntry(self.guiItem)

	def __backspaceFunc(self):
		if self.guiItem.getCursorPosition() == 0:
			self._handleErasing(None)

	def __deleteFunc(self):
		if self.guiItem.getCursorPosition() == self.__textMapper.plaintextLength:
			self._handleErasing(None)

	def setup(self):
		self.guiItem.setupMinimal(self['width'], self['numLines'])

	def updateWidth(self):
		self.guiItem.setMaxWidth(self['width'])

	def updateNumLines(self):
		self.guiItem.setNumLines(self['numLines'])

	def setFocus(self):
		PGEntry.setFocus(self.guiItem, self['focus'])


	def setCursorKeysActive(self):
		PGEntry.setCursorKeysActive(self.guiItem, self['cursorKeys'])


	def setOverflowMode(self):
		PGEntry.set_overflow_mode(self.guiItem, self['overflow'])


	def setObscureMode(self):
		PGEntry.setObscureMode(self.guiItem, self['obscured'])


	def setBackgroundFocus(self):
		PGEntry.setBackgroundFocus(self.guiItem, self['backgroundFocus'])


	def setRolloverSound(self):
		rolloverSound = self['rolloverSound']
		if rolloverSound:
			self.guiItem.setSound(DGG.ENTER + self.guiId, rolloverSound)
		else:
			self.guiItem.clearSound(DGG.ENTER + self.guiId)


	def setClickSound(self):
		clickSound = self['clickSound']
		if clickSound:
			self.guiItem.setSound(DGG.ACCEPT + self.guiId, clickSound)
		else:
			self.guiItem.clearSound(DGG.ACCEPT + self.guiId)

	def setTextSelectionColor(self):
		canrendersel = False
		try:
			if self.__textHilightGeomNode:
				canrendersel = True
		except AttributeError:
			canrendersel = False
		else:
			self.render_selection()

	def commandFunc(self, event):
		if self['command']:
			# Pass any extra args to command
			self['command'](*[self.get()] + self['extraArgs'])


	def failedCommandFunc(self, event):
		if self['failedCommand']:
			# Pass any extra args
			self['failedCommand'](*[self.get()] + self['failedExtraArgs'])

	def focusInCommandFunc(self):
		if self['focusInCommand']:
			self['focusInCommand'](*self['focusInExtraArgs'])
		self.accept(self.guiItem.getTypeEvent(), self._handleTyping)
		self.accept(self.guiItem.getEraseEvent(), self._handleErasing)

		if(self['selectable']):
			self.accept('press-mouse1-'+self.guiItem.getId(), self.__initCursorFollowMouse)
			self.accept('release-mouse1-'+self.guiItem.getId(), self.__stopCursorFollowMouse)
			self.accept('shift', self.__setKeyPressed, ['shift', True])
			self.accept('shift-up', self.__setKeyPressed, ['shift', False])
			
			for modcombo in DirectEntrySelectable.orderedCombinations(DirectEntrySelectable.sMoveKeyModifiers):
				currmodcombostr = '-'.join(modcombo)

				if currmodcombostr != '':
					currmodcombostr += '-'

				for tmpkeq in DirectEntrySelectable.sMoveKeyEquivalents:
					self.accept(currmodcombostr+tmpkeq, self.__setKeyPressed, ['anymovekey', True])
					self.accept(currmodcombostr+tmpkeq+'-repeat', self.__setKeyPressed, ['anymovekey', True])
					self.accept(currmodcombostr+tmpkeq+'-up', self.__setKeyPressed, ['anymovekey', False])

				self.accept(currmodcombostr+'backspace', self.__setKeyPressed, ['backspace', True])
				self.accept(currmodcombostr+'backspace-repeat', self.__setKeyPressed, ['backspace', True])
				self.accept(currmodcombostr+'backspace-up', self.__setKeyPressed, ['backspace', False])
				self.accept(currmodcombostr+'delete', self.__setKeyPressed, ['delete', True])
				self.accept(currmodcombostr+'delete-repeat', self.__setKeyPressed, ['delete', True])
				self.accept(currmodcombostr+'delete-up', self.__setKeyPressed, ['delete', False])

			self.accept(self.guiItem.getCursormoveEvent(), self.__updateTextSelection)
			self.__updateTextStats()

	def _handleTyping(self, guiEvent):
		if self.__prevText != self.guiItem.getText(): 
			currtext = self.guiItem.getText()
			if self.__textSelectionStart < self.__textSelectionEnd:
				self.guiItem.setText(TFU.formatPresRemove(currtext, self.__textSelectionStart, self.__textSelectionEnd))
				self.guiItem.setCursorPosition(self.__textSelectionStart+1)
				self.remove_selection()
			if self.__textSelectionEnd < self.__textSelectionStart:
				self.guiItem.setText(TFU.formatPresRemove(currtext, self.__textSelectionEnd+1, self.__textSelectionStart+1))
				self.guiItem.setCursorPosition(self.__textSelectionEnd+1)
				self.remove_selection()

			if self['autoCapitalize']:
				self._autoCapitalize()

			self.__updateTextStats()
			self.__selectingText = False
		self.__prevText = self.guiItem.getText()

	def _handleErasing(self, guiEvent):
		if self.__textSelectionStart != self.__textSelectionEnd:

			self.guiItem.setText(TFU.formatPresRemove(self.__prevText,self.__textSelectionStart,self.__textSelectionEnd))
			if self.__textSelectionEnd < self.__textSelectionStart:
				self.guiItem.setCursorPosition(self.__textSelectionEnd)
			else:
				self.guiItem.setCursorPosition(self.__textSelectionStart)
			self.remove_selection()

		if self['autoCapitalize']:
			self._autoCapitalize()

		self.__updateTextStats()
		self.__selectingText = False

		self.__prevText = self.guiItem.getText()

	def _autoCapitalize(self):
		name = self.guiItem.getWtext()
		# capitalize each word, allowing for things like McMutton
		capName = u''
		# track each individual word to detect prefixes like Mc
		wordSoFar = u''
		# track whether the previous character was part of a word or not
		wasNonWordChar = True
		for i, character in enumerate(name):
			# test to see if we are between words
			# - Count characters that can't be capitalized as a break between words
			#   This assumes that string.lower and string.upper will return different
			#   values for all unicode letters.
			# - Don't count apostrophes as a break between words
			if character.lower() == character.upper() and character != u"'":
				# we are between words
				wordSoFar = u''
				wasNonWordChar = True
			else:
				capitalize = False
				if wasNonWordChar:
					# first letter of a word, capitalize it unconditionally;
					capitalize = True
				elif (character == character.upper() and
					  len(self.autoCapitalizeAllowPrefixes) and
					  wordSoFar in self.autoCapitalizeAllowPrefixes):
					# first letter after one of the prefixes, allow it to be capitalized
					capitalize = True
				elif (len(self.autoCapitalizeForcePrefixes) and
					  wordSoFar in self.autoCapitalizeForcePrefixes):
					# first letter after one of the force prefixes, force it to be capitalized
					capitalize = True
				if capitalize:
					# allow this letter to remain capitalized
					character = character.upper()
				else:
					character = character.lower()
				wordSoFar += character
				wasNonWordChar = False
			capName += character
		self.guiItem.setWtext(capName)
		self.guiItem.setCursorPosition(self.guiItem.getNumCharacters())

	def focusOutCommandFunc(self):
		if self['focusOutCommand']:
			self['focusOutCommand'](*self['focusOutExtraArgs'])		
		self.ignore(self.guiItem.getTypeEvent())
		self.ignore(self.guiItem.getEraseEvent())
		self.ignore('press-mouse1-'+self.guiItem.getId())
		self.ignore('release-mouse1-'+self.guiItem.getId())
		self.ignore('shift')
		self.ignore('shift-up')

		for modcombo in DirectEntrySelectable.orderedCombinations(DirectEntrySelectable.sMoveKeyModifiers):
			currmodcombostr = '-'.join(modcombo)

			if currmodcombostr != '':
				currmodcombostr += '-'

			for tmpkeq in DirectEntrySelectable.sMoveKeyEquivalents:
				self.ignore(currmodcombostr+tmpkeq)
				self.ignore(currmodcombostr+tmpkeq+'-repeat')
				self.ignore(currmodcombostr+tmpkeq+'-up')

			self.ignore(currmodcombostr+'backspace')
			self.ignore(currmodcombostr+'backspace-repeat')
			self.ignore(currmodcombostr+'backspace-up')
			self.ignore(currmodcombostr+'delete')
			self.ignore(currmodcombostr+'delete-repeat')
			self.ignore(currmodcombostr+'delete-up')

		self.remove_selection()

	def set(self, text):
		""" Changes the text currently showing in the typable region;
		does not change the current cursor position.  Also see
		enterText(). """

		if sys.version_info >= (3, 0):
			assert not isinstance(text, bytes)
			self.unicodeText = True
			self.guiItem.setWtext(text)
		else:
			self.unicodeText = isinstance(text, unicode)
			if self.unicodeText:
				self.guiItem.setWtext(text)
			else:
				self.guiItem.setText(text)

		self.__prevText = self.guiItem.getText()
		self.__updateTextStats()


	def get(self, plain = False):
		""" Returns the text currently showing in the typable region.
		If plain is True, the returned text will not include any
		formatting characters like nested color-change codes. """

		wantWide = self.unicodeText or self.guiItem.isWtext()
		if not self.directWtext.getValue():
			# If the user has configured wide-text off, then always
			# return an 8-bit string.  This will be encoded if
			# necessary, according to Panda's default encoding.
			wantWide = False

		if plain:
			if wantWide:
				return self.guiItem.getPlainWtext()
			else:
				return self.guiItem.getPlainText()
		else:
			if wantWide:
				return self.guiItem.getWtext()
			else:
				return self.guiItem.getText()


	def getCursorPosition(self):
		return self.guiItem.getCursorPosition()

	def getIndexCoords(self, index):
		# TODO
		pass

	def setCursorPosition(self, pos):
		if (pos < 0):
			self.guiItem.setCursorPosition(self.guiItem.getNumCharacters() + pos)
		else:
			self.guiItem.setCursorPosition(pos)


	def getNumCharacters(self):
		return self.guiItem.getNumCharacters()


	def enterText(self, text):
		""" sets the entry's text, and moves the cursor to the end """
		self.set(text)
		self.setCursorPosition(self.guiItem.getNumCharacters())


	def getFont(self):
		return self.onscreenText.getFont()


	def getBounds(self, state = 0):
		# Compute the width and height for the entry itself, ignoring
		# geometry etc.
		tn = self.onscreenText.textNode
		mat = tn.getTransform()
		align = tn.getAlign()
		lineHeight = tn.getLineHeight()
		numLines = tn.getNumRows()
		width = self['width']

		if align == TextNode.ALeft:
			left = 0.0
			right = width
		elif align == TextNode.ACenter:
			left = -width / 2.0
			right = width / 2.0
		elif align == TextNode.ARight:
			left = -width
			right = 0.0

		bottom = -0.3 * lineHeight - (lineHeight * (numLines - 1))
		top = lineHeight

		self.ll.set(left, 0.0, bottom)
		self.ur.set(right, 0.0, top)
		self.ll = mat.xformPoint(Point3.rfu(left, 0.0, bottom))
		self.ur = mat.xformPoint(Point3.rfu(right, 0.0, top))

		vec_right = Vec3.right()
		vec_up = Vec3.up()
		left = (vec_right[0] * self.ll[0]
			  + vec_right[1] * self.ll[1]
			  + vec_right[2] * self.ll[2])
		right = (vec_right[0] * self.ur[0]
			   + vec_right[1] * self.ur[1]
			   + vec_right[2] * self.ur[2])
		bottom = (vec_up[0] * self.ll[0]
				+ vec_up[1] * self.ll[1]
				+ vec_up[2] * self.ll[2])
		top = (vec_up[0] * self.ur[0]
			 + vec_up[1] * self.ur[1]
			 + vec_up[2] * self.ur[2])
		self.ll = Point3(left, 0.0, bottom)
		self.ur = Point3(right, 0.0, top)

		# Scale bounds to give a pad around graphics.  We also want to
		# scale around the border width.
		pad = self['pad']
		borderWidth = self['borderWidth']
		self.bounds = [self.ll[0] - pad[0] - borderWidth[0],
					   self.ur[0] + pad[0] + borderWidth[0],
					   self.ll[2] - pad[1] - borderWidth[1],
					   self.ur[2] + pad[1] + borderWidth[1]]
		return self.bounds

class DirectLabelSelectable:
	pass