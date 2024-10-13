from direct.showbase.DirectObject import DirectObject

from CorysTextUtils import orderedCombinations
from panda3d.core import KeyboardButton, PGItem

import platform

__all__ = ['CorysCopyPasteHandler']

pyperclipLoaded = False
try:
	pyperclip = __import__('pyperclip')
	pyperclipLoaded = True
except (ModuleNotFoundError):
	print('The pyperclip module does not appear to be installed.')
	print('Any copy pasting will simply print to command line for debug purposes instead.')
	print('if you wish to actually copy-paste, install the pyperclip module to your Python')
	print('if you wish to use a more modern copy paste module, you\'re going to have to implement it yourself')

ALLMODSTRS = ['shift', 'control', 'alt', 'meta']

SELECTABLECOPYMODKEY = KeyboardButton.control()
SELECTABLEINVMODS = [KeyboardButton.shift(), KeyboardButton.alt()]
if platform.system().lower() == 'darwin':
	SELECTABLECOPYMODKEY = KeyboardButton.meta()
	SELECTABLEINVMODS += [KeyboardButton.control()]
else:
	SELECTABLEINVMODS += [KeyboardButton.meta()]

class CorysCopyPasteHandler(DirectObject):
	def __init__(self):
		DirectObject.__init__(self)

		for modcombo in orderedCombinations(ALLMODSTRS):
			currmodcombostr = '-'.join(modcombo)

			if currmodcombostr != '':
				currmodcombostr += '-'

			self.accept(currmodcombostr+'x', self.checkforModKeyAndRoute, ['cut'])
			self.accept(currmodcombostr+'c', self.checkforModKeyAndRoute, ['copy'])
			self.accept(currmodcombostr+'v', self.checkforModKeyAndRoute, ['paste'])


	def checkforModKeyAndRoute(self, clipboardfunc):
		rightmods = False
		if base.mouseWatcherNode.is_button_down(SELECTABLECOPYMODKEY):
			rightmods = True

		for keyhandle in SELECTABLEINVMODS:
			if base.mouseWatcherNode.is_button_down(keyhandle):
				rightmods = False

		if rightmods:
			if clipboardfunc == 'copy':
				self.copyFunc()
			elif clipboardfunc == 'paste':
				self.pasteFunc()
			elif clipboardfunc == 'cut':
				self.cutFunc()

	def copyFunc(self, guiEvent=None):
		if ( PGItem.getFocusItem() 
			and PGItem.getFocusItem().hasPythonTag('textSelectionHandleObj')
			and hasattr(PGItem.getFocusItem().getPythonTag('textSelectionHandleObj'), 'getSelectedText') ):

			texttocopy = PGItem.getFocusItem().getPythonTag('textSelectionHandleObj').getSelectedText()

			if texttocopy != '':
				if pyperclipLoaded:
					pyperclip.copy(texttocopy)
				else:
					print('The following text was attempted to be copied:', texttocopy)

	def pasteFunc(self, guiEvent=None):
		if ( PGItem.getFocusItem() 
			and PGItem.getFocusItem().hasPythonTag('textSelectionHandleObj')
			and hasattr(PGItem.getFocusItem().getPythonTag('textSelectionHandleObj'), 'insertTextAtCursor') ):

			texttopaste = pyperclip.paste()

			if texttopaste != '':
				if pyperclipLoaded:
					PGItem.getFocusItem().getPythonTag('textSelectionHandleObj').insertTextAtCursor( texttopaste )
				else:
					print('Attempted to paste from clipboard.')

	def cutFunc(self, guiEvent=None):
		if ( PGItem.getFocusItem() 
			and PGItem.getFocusItem().hasPythonTag('textSelectionHandleObj')
			and hasattr(PGItem.getFocusItem().getPythonTag('textSelectionHandleObj'), 'getSelectedText') ):

			texttocopy = PGItem.getFocusItem().getPythonTag('textSelectionHandleObj').getSelectedText()

			if texttocopy != '':
				if pyperclipLoaded:
					pyperclip.copy(texttocopy)
				else:
					print('The following text was attempted to be cut:', texttocopy)

				if hasattr(PGItem.getFocusItem().getPythonTag('textSelectionHandleObj'), 'removeSelectedText'):
					PGItem.getFocusItem().getPythonTag('textSelectionHandleObj').removeSelectedText()