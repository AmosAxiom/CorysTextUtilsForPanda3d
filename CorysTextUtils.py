#A collection of utility classes
#
# TextMapper provides utilities for quickly determining
# statistics about rendered text, as well as being able
# to tell which character is at which X,Y location
# 
# Panda3dTextFormatUtils has a set of functions for
# splicing and editing text containing panda3d
# formatting strings, without messing up the 
# formatting.
#
# Hopefully other people also find this useful
# -Cory (Dr. Axiom)

__all__ = ['CorysTextUtils']

import math

from panda3d.core import *
import encodings.utf_8
import unicodedata


#Static utlity function to generate all combinations of an input list but 
#preserve the order in which the list items appear when combining.
#This is just to ensure all modifier keys are accepted within this function.
#And also I didn't want to import the combinatorics module
def orderedCombinations(inputList):
	if len(inputList) == 0:
		return [[]]
	cs = []
	for c in orderedCombinations(inputList[:-1]):
		cs += [c, c+[inputList[-1]]]
	return cs

#A collection of formatting utility functions I find useful
#for working with text in panda3d containing formatting
# characters
class Panda3dTextFormatUtils:

	def removeControlCharacters(inputStr, replacementChar=''):
		return ''.join(ch if unicodedata.category(ch)[0]!='C' else replacementChar for ch in inputStr)

	# Converts the integer index of a plaintext rendered string (i.e. cursor index in a PGEntry)
	# into the corresponding index at a formatted string.
	# Returns -1 if the plaintext index passed is outside the bounds of the formatted string.
	def plaintextIndexToFormatIndex(inputStr, plaintextIndex):
		(plaintextChunks, formatChunks) = Panda3dTextFormatUtils.chunkTextAndFormatting(inputStr)

		indexsofar = 0
		fmatindexsofar
		for ptcind in range(len(plaintextChunks)):
			if  indexsofar <= plaintextIndex < len(plaintextChunks[ptcind]):
				return fmatindexsofar + (plaintextIndex-indexsofar)

			indexsofar += len(plaintextChunks[ptcind])
			fmatindexsofar += len(plaintextChunks[ptcind])
			if ptcind < len(formatChunks):
				fmatindexsofar += len(formatChunks[ptcind])

		return -1

	# Converts the integer index within the formatted text string to the corresponding index
	# at a rendered plaintext string (i.e. to find out what the corresponding cursor index in
	# a PGEntry is)
	def formattedIndextoPlaintextIndex(inputStr, formattedIndex):
		return len( Panda3dTextFormatUtils.toPlainText(inputStr[:formattedIndex]) )


	# provide this function with a list of formatting strings
	# that are found back to back, and it will eliminate any
	# \1*\1 chunks that will be cancelled out by subsequent \2
	# chunks
	def pareFormatChunks(inputFormatChunks):
		retval = inputFormatChunks[:] 

		while '\2' in retval:
			
			rindex = len(retval)-1
			foundamatch = False
			while rindex > 0 :

				if retval[rindex] == '\2' and retval[rindex-1][0] == '\1':
					del (retval[rindex-1:rindex+1])
					rindex -=2
					foundamatch = True

				rindex -= 1

			if not foundamatch:
				break

		return retval

	#split returns empty strings before and after so no need to check what the first character is.
	def toPlainText(inputStr):\
		return ''.join(   (''.join( inputStr.split('\1')[::2] )).split('\2')   )

	#Returns a length 2 tuple. The first element of the tuple is
	#an array containing the various plaintext elements of the string
	#the second element of the tuple is an array containing the
	#various formatting strings
	def chunkTextAndFormatting(inputStr):
		split1arr = inputStr.split('\1')

		plainArr = []
		modArr = []

		for s1aind in range(len(split1arr)):
			if s1aind % 2 == 0:
				currs2arr = split1arr[s1aind].split('\2')
				plainArr += currs2arr
				modArr += (['\2']*(len(currs2arr)-1))
			else:
				modArr += [ '\1'+split1arr[s1aind]+'\1' ]

		#at this point plain Arr contains segments of plaintext, the end of each contains a modifier
		#modArr contains the text formatting strings that go at the end of each plaintext element.

		return (plainArr, modArr)

	#Removes a segment of text from the input string while preserving
	#Panda3d formatting characters. 
	#startIndex and endIndex correspond to indices in the plaintext
	#string- i.e. the string as if the formatting characters were 
	#removed.
	#Respects negative indexing, and also will behave sensibly if
	#endIndex is before the startIndex.
	#Inclusive of the smaller index and EXCLUSIVE of the larger index
	def formatPresRemove(inputStr, startIndex, endIndex, ignoreOutOfBounds=False):
		(plaintextChunks, formatChunks) = Panda3dTextFormatUtils.chunkTextAndFormatting(inputStr)

		revSindex = startIndex
		revEindex = endIndex

		totalPlaintextLength = len(''.join(plaintextChunks))

		if startIndex > totalPlaintextLength:
			if ignoreOutOfBounds:
				revSindex = totalPlaintextLength
			else:
				raise IndexError('start index is outside the bounds of the total length of the plaintext')
		if endIndex > totalPlaintextLength:
			if ignoreOutOfBounds:
				revEindex = totalPlaintextLength
			else:
				raise IndexError('end index is outside the bounds of the total length of the plaintext')

		if startIndex < 0:
			revSindex = totalPlaintextLength-startIndex
			if -startIndex > totalPlaintextLength:
				if ignoreOutOfBounds:
					revSindex = 0
				else:
					raise IndexError('start index is outside the bounds of the total length of the plaintext')
		if endIndex < 0:
			revEindex = totalPlaintextLength-endIndex
			if -endIndex > totalPlaintextLength:
				if ignoreOutOfBounds:
					revEindex = 0
				else:
					raise IndexError('end index is outside the bounds of the total length of the plaintext')

		finSindex = revSindex
		finEindex = revEindex

		if revEindex < revSindex:
			finSindex = revEindex
			finEindex = revSindex

		preval = ''
		modsinthemiddle = []
		postval = ''
		indexsofar = 0
		chunkIndices = [0, 0]
		inchunkIndices = [0, 0]

		for ptcind in range(len(plaintextChunks)):
			if indexsofar <= finSindex < indexsofar+len(plaintextChunks[ptcind]):
				chunkIndices[0] = ptcind
				inchunkIndices[0] = finSindex-indexsofar
			if indexsofar < finEindex <= indexsofar+len(plaintextChunks[ptcind]):
				chunkIndices[1] = ptcind
				inchunkIndices[1] = finEindex-indexsofar

			indexsofar += len(plaintextChunks[ptcind])


		for ptcind in range(len(plaintextChunks)):
			if ptcind < chunkIndices[0]:
				preval += plaintextChunks[ptcind]
				if ptcind < len(formatChunks):
					preval += formatChunks[ptcind]
			elif ptcind == chunkIndices[0]:
				preval += plaintextChunks[ptcind][:inchunkIndices[0]]
				if ptcind != chunkIndices[1] and ptcind < len(formatChunks):
					modsinthemiddle.append(formatChunks[ptcind])

			if chunkIndices[0] < ptcind < chunkIndices[1]:
				modsinthemiddle.append(formatChunks[ptcind]) 
			elif ptcind == chunkIndices[1]:
				postval += plaintextChunks[ptcind][inchunkIndices[1]:]
				if ptcind < len(formatChunks):
					postval += formatChunks[ptcind]
			elif ptcind > chunkIndices[1]:
				postval += plaintextChunks[ptcind]
				if ptcind < len(formatChunks):
					postval += formatChunks[ptcind]

		return preval+(''.join( Panda3dTextFormatUtils.pareFormatChunks(modsinthemiddle) ))+postval

	#Inserts a formatted string into another formatted string, preserving the formatting
	#of both strings.
	def formatPresInsert(inputStr, insertStr, insertIndex, ignoreOutOfBounds=False):
		(plaintextChunks, formatChunks) = Panda3dTextFormatUtils.chunkTextAndFormatting(inputStr)

		(insertptChunks, insertfmtChunks) = Panda3dTextFormatUtils.chunkTextAndFormatting(insertStr)

		totalPlaintextLength = len( ''.join(plaintextChunks) )

		finSindex = insertIndex

		if insertIndex > totalPlaintextLength:
			if ignoreOutOfBounds:
				finSindex = totalPlaintextLength
			else:
				raise IndexError('insert index is outside the bounds of the total length of the plaintext')

		if insertIndex < 0:
			if -insertIndex > totalPlaintextLength:
				if ignoreOutOfBounds:
					finSindex = 0
				else:
					raise IndexError('insert index is outside the bounds of the total length of the plaintext')

		indexsofar = 0
		chunkIndex = len(plaintextChunks)
		inchunkIndex = 0

		for ptcind in range(len(plaintextChunks)):
			if indexsofar <= finSindex < indexsofar+len(plaintextChunks[ptcind]):
				chunkIndex = ptcind
				inchunkIndex = finSindex-indexsofar
				break

			indexsofar += len(plaintextChunks[ptcind])

		premods = Panda3dTextFormatUtils.pareFormatChunks(formatChunks[:chunkIndex])

		while len(premods)>=1 and premods[0] == '\2':
			del premods[0]

		invpremods = []

		for currmod in premods:
			if currmod[0] == '\1':
				invpremods.append('\2')

		#revise format chunks inside insert text to remove any redundant \2's
		num1s = 0
		for trindex in range(len(insertfmtChunks)):
			if insertfmtChunks[trindex][0] == '\1':
				num1s += 1
			elif insertfmtChunks[trindex] == '\2' and num1s > 0 :
				insertfmtChunks[trindex] == ''
				num1s -= 1

		retval = ''
		for cindex in range(chunkIndex):
			retval += plaintextChunks[cindex]
			if cindex < len(formatChunks):
				retval += formatChunks[cindex]

		if chunkIndex < len(plaintextChunks):
			retval += plaintextChunks[chunkIndex][:inchunkIndex]

		retval += ''.join(invpremods)
		retval += insertStr

		if chunkIndex < len(plaintextChunks):
			insertmods = Panda3dTextFormatUtils.pareFormatChunks(insertfmtChunks)
			invinsertmods = []

			for currmod in insertmods:
				if currmod[0] == '\1':
					invinsertmods.append('\2')

			retval += ''.join(invinsertmods)
			retval += ''.join(premods)
			retval += plaintextChunks[chunkIndex][inchunkIndex:]

			for cindex in range(chunkIndex+1,len(plaintextChunks)):
				retval += plaintextChunks[cindex]
				retval += formatChunks[cindex]

		return retval

	def formatPresSubstr(inputStr, startIndex, endIndex, ignoreOutOfBounds=False):
		(plaintextChunks, formatChunks) = Panda3dTextFormatUtils.chunkTextAndFormatting(inputStr)

		revSindex = startIndex
		revEindex = endIndex

		totalPlaintextLength = len(''.join(plaintextChunks))

		if startIndex > totalPlaintextLength:
			if ignoreOutOfBounds:
				revSindex = totalPlaintextLength
			else:
				raise IndexError('start index is outside the bounds of the total length of the plaintext')
		if endIndex > totalPlaintextLength:
			if ignoreOutOfBounds:
				revEindex = totalPlaintextLength
			else:
				raise IndexError('end index is outside the bounds of the total length of the plaintext')

		if startIndex < 0:
			revSindex = totalPlaintextLength-startIndex
			if -startIndex > totalPlaintextLength:
				if ignoreOutOfBounds:
					revSindex = 0
				else:
					raise IndexError('start index is outside the bounds of the total length of the plaintext')
		if endIndex < 0:
			revEindex = totalPlaintextLength-endIndex
			if -endIndex > totalPlaintextLength:
				if ignoreOutOfBounds:
					revEindex = 0
				else:
					raise IndexError('end index is outside the bounds of the total length of the plaintext')

		finSindex = revSindex
		finEindex = revEindex

		if revEindex < revSindex:
			finSindex = revEindex
			finEindex = revSindex

		indexsofar = 0
		chunkIndices = [0, 0]
		inchunkIndices = [0, 0]

		for ptcind in range(len(plaintextChunks)):
			if indexsofar <= finSindex < indexsofar+len(plaintextChunks[ptcind]):
				chunkIndices[0] = ptcind
				inchunkIndices[0] = finSindex-indexsofar
			if indexsofar < finEindex <= indexsofar+len(plaintextChunks[ptcind]):
				chunkIndices[1] = ptcind
				inchunkIndices[1] = finEindex-indexsofar

			indexsofar += len(plaintextChunks[ptcind])

		premods = Panda3dTextFormatUtils.pareFormatChunks(formatChunks[:chunkIndices[0]])

		while len(premods)>=1 and premods[0] == '\2':
			del premods[0]

		retval = ''.join(premods)
		if chunkIndices[0] == chunkIndices[1]:
			retval += plaintextChunks[chunkIndices[0]][inchunkIndices[0]:inchunkIndices[1]]
		else:
			for ptcind in range(chunkIndices[0], chunkIndices[1]+1):
				if ptcind == chunkIndices[0]:
					retval += plaintextChunks[chunkIndices[0]][inchunkIndices[0]:]+formatChunks[ptcind]
				elif ptcind == chunkIndices[1]:
					retval += plaintextChunks[chunkIndices[1]][:inchunkIndices[1]]
				else:
					retval += plaintextChunks[ptcind]+formatChunks[ptcind]

		return retval


	def formatSegment(inputStr, formatStr, startIndex, endIndex):
		pass

	def removeFormatSegment(inputstr, startIndex, endIndex):
		pass


#A slightly smart mapping class that only does 
#computationally intensive bounds and character
#location tracking if the content has changed.
# has utility functions to map x, y locations to
# a specific character, and also computes several
# text stats.
class TextMapper:
	def __init__(self, textNodeToMap: TextNode):
		self.numRows = 0
		self.charsPerRow = [] 
		self.plaintextLength = 0
		self.rowBaselines = []
		self.rowBounds = []
		self.rowLineheights = []

		if not(type(textNodeToMap) is TextNode):
			raise TypeError('textNodeToMap must be a TextNode')

		self.textAssembler = TextAssembler(textNodeToMap)

	def mapTextNode(self, textNodeToMap: TextNode):
		if not(type(textNodeToMap) is TextNode):
			raise TypeError('mapTextNode must take a TextNode object')
		# To do- Pull in actual properties from object

		prevprops = self.textAssembler.getProperties()
		prevwtext = self.textAssembler.getWtext()

		self.textAssembler.setProperties(TextProperties(textNodeToMap))
		self.textAssembler.setWtext(textNodeToMap.getWtext())

		if ( (prevprops == self.textAssembler.getProperties()) or 
				(prevwtext == self.textAssembler.getWtext()) ):
			self.__updateTextStats()

	def mapPGEntry(self, pgEntryToMap: PGEntry):
		if not(type(pgEntryToMap) is PGEntry):
			raise TypeError('mapPGEntry must take a PGEntry object')

		prevprops = self.textAssembler.getProperties()
		prevwtext = self.textAssembler.getWtext()

		tmpprops = TextProperties( pgEntryToMap.getTextDef(0) )
		tmpprops.setWordwrap( pgEntryToMap.getMaxWidth() )
		#tmpprops.addProperties( pgEntryToMap.getTextNode() )

		self.textAssembler.setProperties(tmpprops)
		self.textAssembler.setWtext(pgEntryToMap.getWtext())

		if ( (prevprops == self.textAssembler.getProperties())
				or (prevwtext == self.textAssembler.getWtext()) ):
			self.__updateTextStats()

	def setWtext(self, wtext: str):
		if not(type(wtext) is str):
			raise TypeError('Invalid string object')

		prevWtext = self.textAssembler.getWtext()
		self.textAssembler.setWtext(wtext)

		if(prevWtext != self.textAssembler.getWtext()):
			self.__updateTextStats()

	def setProperties(self, propsToSet: TextProperties):
		prevProps = self.textAssembler.getProperties()

		self.textAssembler.setProperties(propsToSet)

		if(prevProps != self.textAssembler.getProperties()):
			self.__updateTextStats()

	def addProperties(self, propsToAdd: TextProperties):
		prevProps = TextProperties(self.textAssembler.getProperties())

		self.textAssembler.getProperties().addProperties(propsToAdd)

		if(prevProps != self.textAssembler.getProperties()):
			self.__updateTextStats()

	def __updateTextStats(self) :
		#TODO 
		#the functions that modify this thing should call this function to update the stats
		
		self.textAssembler.assembleText()

		self.plaintextLength = self.textAssembler.getNumCharacters()
		self.numRows = self.textAssembler.getNumRows()
		self.charsPerRow = []
		self.rowBaselines = []
		for trindex in range(self.numRows):
			self.charsPerRow.append(self.textAssembler.getNumCols(trindex))
			self.rowBaselines.append(self.textAssembler.getYpos(trindex,0))

		hasFormatting = False
		currLineHeight = self.textAssembler.getProperties().getFont().getLineHeight()

		#a quick check to see if no formatting, default lineheight will be enough
		if self.plaintextLength < len(self.textAssembler.getWtext()) : 
			hasFormatting = True

		self.rowBounds = [] # (top, bottom)
		for trindex in range(self.numRows):
			if hasFormatting:
				currLineHeight = 0
				try:
					currLineHeight = self.textAssembler.getProperties(trindex, 0).getFont().getLineHeight()
				except (AssertionError):
					pass

				for crcindex in range(1, self.charsPerRow[trindex]):
					testLHeight = self.textAssembler.getProperties(trindex, crcindex).getFont().getLineHeight()
					if testLHeight > currLineHeight:
						currLineHeight = testLHeight

			#currLineHeight should now represent the tallest formatting in the segment.
			#This ratio 0.7 above baseline to 0.3 below baseline I *think* is hardcoded
			#into panda but I am having trouble confirming it.
			self.rowBounds.append( (self.rowBaselines[trindex]+(0.7*currLineHeight), self.rowBaselines[trindex]-(0.3*currLineHeight))  )

	def xyToCursorRc(self, x_coord, y_coord):
		# print("current number of rows: ", self.textAssembler.getNumRows())
		testr = self.numRows
		testc = 0
		for trindex in range(self.numRows):
			if self.rowBounds[trindex][1] < y_coord:
				testr = trindex
				break

		if testr < self.numRows:
			for tcindex in range(self.charsPerRow[testr]+1): #remember max c is actually 1+ the number of chars in the row
				if abs(self.textAssembler.getXpos(testr, tcindex)-x_coord) < abs(self.textAssembler.getXpos(testr, testc)-x_coord):
					testc = tcindex

		return (testr, testc)

	def xyToCursorIndex(self, x_coord, y_coord):
		return self.textAssembler.calcIndex(*self.xyToCursorRc(x_coord, y_coord))		

	def cursorRcToXy(self, row, column):
		return ( self.textAssembler.getXpos(row, column), self.textAssembler.getYpos(row, column) )

	#The character row and column under the XY position represented.
	#THIS IS DIFFERENT from the cursor xy of the character which sits
	# to the left of the character!
	# returns -1 in row or column if the XY is to the top or left 
	# and 1+ the max index if the XY is below or right of any valid characters.
	def charRcAtXy(self, x_coord, y_coord):
		testr = -1
		testc = -1

		for trindex in range(self.numRows):
			if ( self.rowBounds[trindex][1] < y_coord ) and ( y_coord < self.rowBounds[trindex][0] ):
				testr = trindex
				break

		if testr == -1:
			return (-1, -1)

		for tcindex in range(self.charsPerRow[testr]):
			if ( ( self.textAssembler.getXpos(testr, tcindex) < x_coord ) and 
					( x_coord < self.textAssembler.getXpos(testr, tcindex+1) ) ):
				testc = tcindex
				break

		if testc == -1:
			return (-1, -1)

		return (testr, testc)

	#The character index under the XY position represented
	# i.e. if the user clicks, what character they would click on.
	#THIS IS DIFFERENT from the text cursor xy of the character which sits
	# to the left of the character!
	# returns -1 if the XY is not over a character.
	def charIndexAtXy(self, x_coord, y_coord):
		tmprc = self.charRcAtXy()

		if temprc[0] == -1 or temprc[1] == -1:
			return -1

		return self.textAssembler.calcIndex(*temprc)

	#When supplied a row and a column, finds the column in the
	# target row corresponding to the horizontally closest
	#cursor position
	def closestHorizCol(self, row, column, targetRow):
		if targetRow < 0 or targetRow >= self.numRows:
			raise IndexError('Target row is not within the bounds of the text.')

		if row < 0 or row >= self.numRows:
			raise IndexError('Initial row is not within the bounds of the text')

		if column < 0 or column > self.charsPerRow[row]:
			raise IndexError('Initial column is not within the bounds of the text')

		targetX = self.textAssembler.getXpos(row, column)
		retcol = 0
		prevbest = abs(self.textAssembler.getXpos(targetRow, 0)-targetX)

		for tstcol in range(1, self.charsPerRow[targetRow]):
			newtest = abs(self.textAssembler.getXpos(targetRow, tstcol)-targetX)
			if newtest < prevbest:
				prevbest = newtest
				retcol = tstcol

		return retcol

	#When supplied a target row,
	# finds the index of the character at the
	# target row which is horizontally closest to the index supplied
	def indexAtClosestColumn(self, index, targetRow):
		row = self.textAssembler.calcR(index)
		col = self.textAssembler.calcC(index)

		if row == -1:
			rindexoffset = 0
			while row == -1:
				rindexoffset = rindexoffset+1
				if index+rindexoffset >= self.plaintextLength:
					row = self.numRows-1
					col = self.charsPerRow[row]
					break
				row = self.textAssembler.calcR(index+rindexoffset)
				col = self.textAssembler.calcC(index+rindexoffset)

		newrow = row
		newcol = col

		if col == self.charsPerRow[row]:
			newrow = row+1
			if newrow >= self.numRows:
				newrow = self.numRows-1
				newcol = self.charsPerRow[newrow]
			else:
				newcol = 0

		return self.textAssembler.calcIndex(targetRow, self.closestHorizCol(newrow, newcol, targetRow))

	def pageIndex(self, index, pageUp=True, numRows=8):
		if self.numRows == 0:
			return 0
		if numRows == 0:
			return index

		row = self.textAssembler.calcR(index)
		col = self.textAssembler.calcC(index)

		if row == -1:
			rindexoffset = 0
			while row == -1:
				rindexoffset = rindexoffset+1
				if index+rindexoffset >= self.plaintextLength:
					row = self.numRows-1
					col = self.charsPerRow[row]
					break
				row = self.textAssembler.calcR(index+rindexoffset)
				col = self.textAssembler.calcC(index+rindexoffset)

		newrow = row
		newcol = col

		if col == self.charsPerRow[row]:
			newrow = row+1
			if newrow >= self.numRows:
				newrow = self.numRows-1
				newcol = self.charsPerRow[newrow]
			else:
				newcol = 0

		pagedrow = newrow
		if pageUp:
			if newrow == 0:
				return 0
			pagedrow -= numRows
		else:
			if newrow == self.numRows-1:
				return self.plaintextLength
			pagedrow += numRows

		if pagedrow >= self.numRows:
			pagedrow = self.numRows-1
		if pagedrow < 0:
			pagedrow = 0

		return self.textAssembler.calcIndex(pagedrow, self.closestHorizCol(newrow, newcol, pagedrow))

