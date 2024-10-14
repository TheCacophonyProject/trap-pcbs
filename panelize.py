from kikit import panelize
from kikit import panelize_ui_impl as ki
from kikit.units import mm, deg
from kikit.panelize import Panel, BasicGridPosition, Origin
from pcbnewTransition.pcbnew import LoadBoard, VECTOR2I
from pcbnewTransition import pcbnew
from itertools import chain



############### Custom config
board1_path = "modbus-pir-2servos/modbus-pir-2servos.kicad_pcb"
board2_path = "trap-plugs/trap-plugs.kicad_pcb"
output_path = "trap-panelized/trap-panelized.kicad_pcb"



board_spacing = 3*mm

################ KiKit Panel Config (Only deviations from default)

framing={
		"type": "frame",
		"vspace" : "3mm",
    "hspace" : "3mm",
		"width": "6mm",
	}
	
cuts =  {
		"type": "mousebites",
    "drill": "0.5mm",
    "spacing": "0.7mm",
    "offset": "0mm"

	}
tabs = {
		"type":"annotation",
		#"vwidth": "5mm",
		#"spacing" : "5mm"
    "fillet": "1.5mm",
    #"tabfootprints": "cacophony-library:Tab8mm", # //TODO Can't get this to work.
    #"width": "10mm"
	}
tooling = {
        "type": "3hole",
        "hoffset": "3mm",
        "voffset": "3mm",
        "size": "3mm",
    }
fiducials = {
  "type": "3fid",
  "hoffset": "3mm",
  "voffset": "6mm",
}

post = {
  #"millradius": "1.5mm" # Will add fillets when needed for manufacturing.
}

# Obtain full config by combining above with default
preset = ki.obtainPreset([], tabs=tabs, cuts=cuts, framing=framing, tooling=tooling, post=post, fiducials=fiducials)

################ Adjusted `panelize_ui#doPanelization`

# Prepare			
board1 = LoadBoard(board1_path)
board2 = LoadBoard(board2_path)
panel = Panel(output_path)


panel.inheritDesignSettings(board1)
panel.inheritProperties(board1)
panel.inheritTitleBlock(board1)




###### Manually build layout. Inspired by `panelize_ui_impl#buildLayout`
sourceArea1 = ki.readSourceArea(preset["source"], board1)
sourceArea2 = ki.readSourceArea(preset["source"], board2)

substrateCount = len(panel.substrates) # Store number of previous boards (probably 0)
# Prepare renaming nets and references
netRenamer = lambda x, y: "Board_{n}-{orig}".format(n=x, orig=y)
refRenamer = lambda x, y: "Board_{n}-{orig}".format(n=x, orig=y)

# Actually place the individual boards
# Use existing grid positioner
# Place two boards above each other
#panelOrigin = VECTOR2I(0,0)
#placer = BasicGridPosition(board_spacing, board_spacing) #HorSpace, VerSpace
area1 = panel.appendBoard(board1_path, pcbnew.wxPointMM(0, 0), origin=Origin.Center, sourceArea=sourceArea1, netRenamer=netRenamer, refRenamer=refRenamer)
area2 = panel.appendBoard(board2_path, pcbnew.wxPointMM(58, 0), rotationAngle=deg*90, origin=Origin.Center, sourceArea=sourceArea2, netRenamer=netRenamer, refRenamer=refRenamer,  inheritDrc=False)

panel.addMillFillets(panelize.fromMm(0.75))

substrates = panel.substrates[substrateCount:] # Collect set of newly added boards

# Prepare frame and partition
framingSubstrates = ki.dummyFramingSubstrate(substrates, preset)
panel.buildPartitionLineFromBB(framingSubstrates)
backboneCuts = ki.buildBackBone(preset["layout"], panel, substrates, preset)


######## --------------------- Continue doPanelization

tabCuts = ki.buildTabs(preset, panel, substrates, framingSubstrates)

frameCuts = ki.buildFraming(preset, panel)


ki.buildTooling(preset, panel)
ki.buildFiducials(preset, panel)
for textSection in ["text", "text2", "text3", "text4"]:
	ki.buildText(preset[textSection], panel)
ki.buildPostprocessing(preset["post"], panel)

ki.makeTabCuts(preset, panel, tabCuts)
ki.makeOtherCuts(preset, panel, chain(backboneCuts, frameCuts))


ki.buildCopperfill(preset["copperfill"], panel)

ki.setStackup(preset["source"], panel)
ki.setPageSize(preset["page"], panel, board1)
ki.positionPanel(preset["page"], panel)

ki.runUserScript(preset["post"], panel)

ki.buildDebugAnnotation(preset["debug"], panel)

panel.save(reconstructArcs=preset["post"]["reconstructarcs"],
		   refillAllZones=preset["post"]["refillzones"])


    
