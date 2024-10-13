# Corys Text Utilities for Panda3d

This is a collection of shareable utilities that I find useful for more detailed text handling in Panda3d.
I was somewhat disappointed when I found out that the built-in GUI objects couldn't handle text selection and basic editing, so I went down a rabbit hole to try to fix that.

The main two classes you're probably here for are DirectEntrySelectable and DirectLabelSelectable, so I'll explain those first.
If you'd like to hop right into it, try running SelectableExample.py. I would highly recommend installing the pyperclip package first with

```
pip install pyperclip
```

which will let SelectableExample demonstrate copy and pasting functionality.

Pyperclip is a bit old, and if you want improved copy-paste functionality you should probably implement your own version of CopyPasteHandler that uses a newer package.

## DirectEntrySelectable
Probably the class you're really here for, contained within the DirectGUISelectable module. This module has a dependency of CorysTextUtilsForPanda3d, so grab that file as well even if you just want DirectEntrySelectable.

This class acts just like a DirectEntry- but panda is directed to keep track of events and selection indices and render a text selection hilight over the text.

Note if you don't want this to act like a regular DirectEntry- you MUST PASS
```
selectable= True
```
to the kwargs of the constructor.

Useful parameters to know:
* selectable - Setting selectable=True will make this DirectEntrySelectable render a selection box and behave sensibly with selected text.
* textSelectionColor - The color of the text selection hilight as a 4-tuple. I would recommend a transparency between 0.3 and 0.7.
* textSelectionColorGrad - If this is defined- the bottom of each line of the text hilight will be this color, and the top color will be textSelectionColor

## DirectLabelSelectable
A version of directlabel which allows text selection- in case you want to display text you want to allow the user to hilight and copy from.

Useful parameters to know:
* textSelectionColor - The color of the text selection hilight as a 4-tuple. I would recommend a transparency between 0.3 and 0.7.
* textSelectionColorGrad - If this is defined- the bottom of each line of the text hilight will be this color, and the top color will be textSelectionColor

## SelectableExample and CorysCopyPasteHandler

If you're going to implement your own versions of this- note how I've had to do
```
loadPrcFileData('', 'paste-emit-keystrokes false')
```
prior to calling ShowBase.__init__() - because on windows panda has the default behavior of emitting keystrokes to replicate any text on the clipboard.
