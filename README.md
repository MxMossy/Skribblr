# [Skribbl.io](http://skribbl.io) Drawing Tool

Skribblr is a tool for converting images into sketches that can be drawn in any program that uses the mouse to draw. 

**Warning: this tool moves your computers mouse directly. Use at your own risk.** 

## Requires
Python 3.8+

## Setup
1. Run `pip install -r requirements.txt`

## How to use
After running the program, a GUI window will present itself. 

- prefix term: automatically preprended to the query term (e.g. "clipart", "cartoon", "svg")
- query term: used to download images from Bing images
- selection arrows: can be used to navigate between downloaded image contours
- start draw button: activates drawing mode
- threshold slider: can be used to manually adjust contours if desired

### Drawing Mode
Once drawing mode is activated, place cursor at the corner of the area you intend to draw in. Then hold **left alt** and move your cursor to the other corner of the drawing area. Release alt to begin drawing. Hold Escape to abort the current initiated drawing.


## Background
Originally I intended for use on skribbl.io, but found it useable in many different drawing programs
