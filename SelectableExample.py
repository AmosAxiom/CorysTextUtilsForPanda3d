from direct.showbase.ShowBase import ShowBase

from direct.gui.DirectGui import DirectFrame, DirectScrolledFrame

from panda3d.core import TextNode, loadPrcFileData

from DirectGUISelectable import DirectEntrySelectable, DirectLabelSelectable
from DirectGUISelectable import orderedCombinations

from CorysCopyPasteHandler import CorysCopyPasteHandler as CopyPasteHandler


class SelectableExampleBase(ShowBase):
	def __init__(self):
		fgframecolor = (0,0,0,0.8)
		textfgcolor = (1,1,1,1)
		selecttopcolor = (0,0,0.4,0.5)
		selectbotcolor = (0,0.15,0.55,0.4)

		loadPrcFileData('', 'paste-emit-keystrokes false')

		ShowBase.__init__(self)

		self.copyPasteHandler = CopyPasteHandler()

		self.mainFrame = DirectFrame(frameColor=(0.2,0.2,0.2, 0.8), pos = (0,0,0), frameSize=(-1,1,-1,1), sortOrder=100)

		self.inputBox = DirectEntrySelectable(parent=self.mainFrame,
									pos=(-0.9,0,0.88),
									text_scale=0.1,
									width=18,
									frameColor=fgframecolor,
									selectable=True,
									textSelectionColor= selecttopcolor,
									textSelectionColorGrad = selectbotcolor,
									numLines=4,
									text_fg=textfgcolor,
									pad=(0.05,0.05),
									borderWidth=(0,0),
									frameSize=(-0.05,1.85,-0.43, 0.07))

		self.inputBox.set('You can type and copy/paste')

		self.inputBox2 = DirectEntrySelectable(parent=self.mainFrame,
									pos=(-0.9,0,0.33),
									text_scale=0.1,
									width=18,
									frameColor=fgframecolor,
									selectable=True,
									textSelectionColor= selecttopcolor,
									textSelectionColorGrad = selectbotcolor,
									numLines=4,
									text_fg=textfgcolor,
									pad=(0.05,0.05),
									borderWidth=(0,0),
									frameSize=(-0.05,1.85,-0.43, 0.07))

		self.inputBox2.set('in either of these top two boxes,')


		self.inputBox['command'] = self.append1TextToOutput
		self.inputBox2['command'] = self.append2TextToOutput

		self.outputframe = DirectScrolledFrame(parent=self.mainFrame,
												frameColor=fgframecolor,
												frameSize=(0,1.9,-0.8,0),
												canvasSize=(0,1.8,-5,0),
												scrollBarWidth=0.1,
												pos=(-0.95,0,-0.15)
												)

		self.outputLabel = DirectLabelSelectable(parent=self.outputframe.getCanvas(),
											text='and it will get appended to this text when you hit enter.',
											text_scale=0.05,
											text_align=TextNode.ALeft,
											text_wordwrap=34,
											text_fg=textfgcolor,
											frameColor = (0,0,0,0),
											pos=(0.05,0,-0.035),
											textSelectionColor= selecttopcolor,
											textSelectionColorGrad = selectbotcolor
											)

	def append1TextToOutput(self, guiItem=None):
		self.outputLabel['text'] = self.outputLabel['text'] + '\n' + self.inputBox.get()
		self.inputBox.set('')

	def append2TextToOutput(self, guiItem=None):
		self.outputLabel['text'] = self.outputLabel['text'] + '\n' + self.inputBox2.get()
		self.inputBox2.set('')


if __name__ == "__main__" :
	selbase = SelectableExampleBase()
	# base.messenger.toggleVerbose()
	selbase.run()