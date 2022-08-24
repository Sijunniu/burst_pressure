"""
Python script to generate a penny-shaped crack and a wall loss corrosion within a quarter of a full pipe
There are two free parameters for the elliptical crack:
 - Long axis (length)
 - Location (depth)
There is one free parameter for the wall loss corrosion:
 - Loss height

There are two free parameters for the pipe:
 - Pipe thickness
 - Pipe outer diameter

Written by Sijun Niu, February 22th 2022
"""
############################################################################################################
# -*- coding: mbcs -*-

"""Import modules"""
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from odbAccess import *
import sys
import os
import random
import math
import xlsxwriter
import time

"""This command uses findAt functions to locate objects such as faces and cells, instead of getSequencyFromMask"""
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)

"""Activate the corresponding properties to be used in the simulation"""
# Set the flag to True to activate
crack_length = False
lig_2_length = False
loss_height = False

# Pipe switch
T_small = False  # Small thickness if True
D_small = True  # Small diameter if True

# Material switch
steel_grade = 65  # options: X42, X65, X100

"""Set the parameters of the simulation"""
# Default crack parameters
default_length = 0.0015
default_lig_2 = 0.004
default_height = 0.004

# Pipe parameters
# Set 0.12 for 10'' pipe; set 0.22 for 18'' pipe
if D_small:
	pipe_od = 0.12
else:
	pipe_od = 0.22

# Set 0.015 for 0.6'' pipe; set 0.025 for 1'' pipe
if T_small:
	pipe_thk = 0.015
	crack_par = 0.019  # Partition near the crack
	max_length = 0.014  # Allowable maximum combined ligment, crack and loss length
else:
	pipe_thk = 0.025
	crack_par = 0.021  # Partition near the crack
	max_length = 0.02  # Allowable maximum combined ligment, crack and loss length

pipe_id = pipe_od - pipe_thk  # inner diameter
pipe_len = 0.3  # axial length
crack_width = 0.00025
loss_width = 0.015

# Mesh sizes
mesh_fine = 0.0002
mesh_end1 = 0.0005
mesh_end2 = 0.002

# Material parameters of the plate [SI unit]
young_modulus = 210000000000.0
poisson_ratio = 0.3
mat_density = 7700

# Parameter DOE
flaw_detail = []
if crack_length:
	lengths = [0.0005, 0.00125, 0.002]
else:
	lengths = [default_length]

if lig_2_length:
	if T_small:
		lig_2s = [0.002, 0.0035, 0.005]
	else:
		lig_2s = [0.002, 0.004, 0.006, 0.008]
else:
	lig_2s = [default_lig_2]

if loss_height:
	if T_small:
		heights = [0.002, 0.0035, 0.005]
	else:
		heights = [0.002, 0.004, 0.006, 0.008]
else:
	heights = [default_height]

# Number of simulation
num_of_simulation = len(lengths) * len(lig_2s) * len(heights)

# Job names
job_name = 'Burst_full_cw_bTsD_'

"""Initiate the while loop"""
for index in range(num_of_simulation):

	# Assign the crack parameters to the value
	length = lengths[index % len(lengths)]
	lig_2 = lig_2s[int(index/len(lengths)) % len(lig_2s)]
	height = heights[int(index/len(lengths)/len(lig_2s)) % len(heights)]

	total_length = length * 2 + lig_2 + height
	lig_1 = pipe_thk - total_length

	# If the max length criterion is met, save it for output
	flaw_detail.append([index, height * 1000, length * 2000,  lig_2 * 1000, lig_1 * 1000])

	# Calculate depths
	thk = pipe_thk
	depth = lig_1 + length

	# Create the pipe part
	mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=1.0)
	mdb.models['Model-1'].sketches['__profile__'].ArcByCenterEnds(center=(0.0, 0.0)
		, direction=CLOCKWISE, point1=(0.0, pipe_id), point2=(pipe_id, 0.0))
	mdb.models['Model-1'].sketches['__profile__'].ArcByCenterEnds(center=(0.0, 0.0)
		, direction=CLOCKWISE, point1=(0.0, pipe_id + thk), point2=(pipe_id + thk, 0.0))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, pipe_id + thk),
		point2=(0.0, pipe_id))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(pipe_id, 0.0),
		point2=(pipe_id + thk, 0.0))
	mdb.models['Model-1'].Part(dimensionality=THREE_D, name='pipe', type=
		DEFORMABLE_BODY)
	mdb.models['Model-1'].parts['pipe'].BaseSolidExtrude(depth=pipe_len, sketch=
		mdb.models['Model-1'].sketches['__profile__'])
	del mdb.models['Model-1'].sketches['__profile__']

	# Create the first crack
	mdb.models['Model-1'].ConstrainedSketch(gridSpacing=0.01, name='__profile__',
		sheetSize=0.64, transform=
		mdb.models['Model-1'].parts['pipe'].MakeSketchTransform(
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((pipe_id + 0.0001,
		0.0001, pipe_len), ), sketchPlaneSide=SIDE1,
		sketchUpEdge=mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0,
		pipe_id + 0.0001, pipe_len), ), sketchOrientation=RIGHT, origin=(0.0, pipe_id, pipe_len)))
	mdb.models['Model-1'].parts['pipe'].projectReferencesOntoSketch(filter=
		COPLANAR_EDGES, sketch=mdb.models['Model-1'].sketches['__profile__'])
	mdb.models['Model-1'].sketches['__profile__'].EllipseByCenterPerimeter(
		axisPoint1=(0.0, depth + length), axisPoint2=(crack_width,
		depth), center=(0.0, depth))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth - length),
		point2=(0.0, depth))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth), point2=
		(crack_width, depth))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((-crack_width,
		depth), ), point1=(-crack_width, depth))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((0.0,
		depth + length), ), point1=(0.0, depth + length))
	mdb.models['Model-1'].sketches['__profile__'].ConstructionLine(angle=0.0,
		point1=(0.0, depth))
	mdb.models['Model-1'].parts['pipe'].CutRevolve(angle=180.0,
		flipRevolveDirection=OFF, sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchOrientation=RIGHT,
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((pipe_id + 0.0001,
		0.0001, pipe_len), ), sketchPlaneSide=SIDE1, sketchUpEdge=
		mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0, pipe_id + 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Create the wall loss corrosion
	mdb.models['Model-1'].ConstrainedSketch(gridSpacing=0.01, name='__profile__',
		sheetSize=0.6, transform=
		mdb.models['Model-1'].parts['pipe'].MakeSketchTransform(
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((0.0,
		pipe_od - 0.0001, pipe_len - 0.0001), ), sketchPlaneSide=SIDE1,
		sketchUpEdge=mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0,
		pipe_od - 0.0001, pipe_len), ), sketchOrientation=RIGHT, origin=(0.0, pipe_od, pipe_len)))
	mdb.models['Model-1'].parts['pipe'].projectReferencesOntoSketch(filter=
		COPLANAR_EDGES, sketch=mdb.models['Model-1'].sketches['__profile__'])
	mdb.models['Model-1'].sketches['__profile__'].EllipseByCenterPerimeter(
		axisPoint1=(0.0, -height), axisPoint2=(-loss_width, 0.0), center=(0.0, 0.0))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, -height),
		point2=(0.0, 0.0))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, 0.0), point2=(
		-loss_width, 0.0))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((0.0,
		height), ), point1=(0.0, height))
	mdb.models['Model-1'].sketches['__profile__'].ConstructionLine(angle=90.0,
		point1=(0.0, -height))
	mdb.models['Model-1'].parts['pipe'].CutRevolve(angle=180.0,
		flipRevolveDirection=OFF, sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchOrientation=RIGHT,
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((0.0,
		pipe_od - 0.0001, pipe_len - 0.0001), ), sketchPlaneSide=SIDE1, sketchUpEdge=
		mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0, pipe_od - 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Material properties and assembly
	# Yield stress is 464.5 MPa and ultimate tensile strength is 563.8 MPa according to paper
	mdb.models['Model-1'].Material(name='steel')
	mdb.models['Model-1'].materials['steel'].Density(table=((mat_density,),))
	mdb.models['Model-1'].materials['steel'].Elastic(table=((young_modulus, poisson_ratio),))
	# Default option is X65 steel
	if steel_grade == 65:
		mdb.models['Model-1'].materials['steel'].Plastic(table=((470512820.0,
			0.0), (508974359.0, 0.00811359), (535897435.0, 0.019472617), (570512820.0,
			0.038945233), (601282051.0, 0.060040568), (623076923.0, 0.081135903), (
			641025641.0, 0.102231238), (662820512.0, 0.128194726), (682051282.0,
			0.159026369), (698717948.0, 0.189858012), (717948717.0, 0.223935091), (
			735897435.0, 0.266125761), (751282051.0, 0.30831643), (764102564.0,
			0.344016227), (776923076.0, 0.384584179), (792307692.0, 0.438133874), (
			806410256.0, 0.486815416), (817948717.0, 0.535496958), (830769230.0,
			0.592292089), (842307692.0, 0.644219067), (856410256.0, 0.710750507), (
			866666666.0, 0.782150102), (879487179.0, 0.851926978), (889743589.0,
			0.918458418), (900000000.0, 0.984989858), (908974359.0, 1.045030426), (
			916666666.0, 1.10831643)))
	# Use below if considering X42 steel with hardening power n=8
	if steel_grade == 42:
		mdb.models['Model-1'].materials['steel'].Plastic(table=((290000000.0,
			0.0), (424154992.312889, 0.0275385878489327), (461149210.372505,
			0.0550771756978654), (484627939.600789, 0.082615763546798), (
			502113853.99879, 0.110154351395731), (516156452.599337, 0.137692939244663),
			(527945510.285983, 0.165231527093596), (538137346.323632,
			0.192770114942529), (547134170.004543, 0.220308702791461), (
			555201098.831299, 0.247847290640394), (562522521.885263,
			0.275385878489327), (569232084.272135, 0.30292446633826), (
			575429877.083185, 0.330463054187192), (581192886.274058,
			0.358001642036125), (586581650.56838, 0.385540229885058), (
			591644671.800413, 0.41307881773399), (596421433.175642, 0.440617405582923),
			(600944522.949387, 0.468155993431856), (605241164.835568,
			0.495694581280788), (609334344.104584, 0.523233169129721), (
			613243651.506362, 0.550771756978654), (616985926.081478,
			0.578310344827586), (620575751.9369, 0.605848932676519), (624025847.195306,
			0.633387520525452), (627347372.125112, 0.660926108374384), (
			630550175.865016, 0.688464696223317), (633642995.91325, 0.71600328407225),
			(636633620.869316, 0.743541871921182), (639529024.289882,
			0.771080459770115), (642335475.621264, 0.798619047619048)))
	# Use below if considering X100 steel with hardening power n=20
	if steel_grade == 100:
		mdb.models['Model-1'].materials['steel'].Plastic(table=((690000000.0,
			0.0), (771642152.382901, 0.0274729064039409), (796664582.211452,
			0.0549458128078818), (812208939.81009, 0.0824187192118227), (
			823579589.388454, 0.109891625615764), (832577415.026499,
			0.137364532019704), (840038086.921171, 0.164837438423645), (
			846419394.31807, 0.192310344827586), (851999929.046442, 0.219783251231527),
			(856962103.138024, 0.247256157635468), (861431988.866977,
			0.274729064039409), (865500426.629878, 0.30220197044335), (
			869235075.332677, 0.329674876847291), (872687706.729223,
			0.357147783251232), (875898834.402907, 0.384620689655172), (
			878900768.03402, 0.412093596059113), (881719695.677703, 0.439566502463054),
			(884377143.518149, 0.467039408866995), (886891024.126369,
			0.494512315270936), (889276405.174676, 0.521985221674877), (
			891546083.65349, 0.549458128078818), (893711021.878313, 0.576931034482759),
			(895780683.426378, 0.6044039408867), (897763295.391735, 0.63187684729064),
			(899666055.562975, 0.659349753694581), (901495297.863439,
			0.686822660098522), (903256625.76696, 0.714295566502463), (
			904955020.860924, 0.741768472906404), (906594931.920279,
			0.769241379310345), (908180348.551184, 0.796714285714286)))
	mdb.models['Model-1'].materials['steel'].PorousMetalPlasticity(relativeDensity=
		0.999875, table=((1.5, 1.0, 2.25), ))
	mdb.models['Model-1'].materials['steel'].porousMetalPlasticity.VoidNucleation(
		table=((0.3, 0.1, 0.0008), ))
	mdb.models['Model-1'].HomogeneousSolidSection(material='steel', name='Section-1', thickness=None)
	mdb.models['Model-1'].parts['pipe'].SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE,
		region=Region(cells=mdb.models['Model-1'].parts['pipe'].cells.findAt(
		((pipe_id, 0.0, 0.0),), )), sectionName='Section-1',thicknessAssignment=FROM_SECTION)
	mdb.models['Model-1'].rootAssembly.DatumCsysByDefault(CARTESIAN)

	if index == 0:
		mdb.models['Model-1'].rootAssembly.Instance(dependent=OFF, name='pipe-1',
			part=mdb.models['Model-1'].parts['pipe'])
	else:
		del mdb.models['Model-1'].rootAssembly.instances['pipe-1']
		mdb.models['Model-1'].rootAssembly.Instance(dependent=OFF, name='pipe-1',
			part=mdb.models['Model-1'].parts['pipe'])

	# Create sets: 3 symmetry planes and an end cap
	mdb.models['Model-1'].rootAssembly.Set(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((0.0, pipe_id + 0.001, pipe_len / 2), )),
		name='x_sym')
	mdb.models['Model-1'].rootAssembly.Set(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((pipe_id + 0.001, 0.0, pipe_len - 0.001), )),
		name='y_sym')
	mdb.models['Model-1'].rootAssembly.Set(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((pipe_id + 0.001, 0.001, pipe_len), )),
		name='z_sym')
	mdb.models['Model-1'].rootAssembly.Set(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((0.001, pipe_id + 0.001, 0.0), )),
		name='z_end')

	# Create surface
	mdb.models['Model-1'].rootAssembly.Surface(name='inner', side1Faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((pipe_id, 0.0001, pipe_len / 2),)))

	# Create magic points and edges ;)
	if T_small:
		if D_small:
			magic_pt = (0.0193620651670132, 0.125515379266719)
			magic_edge = (0.017624, 0.114249, pipe_len)
			if steel_grade == 65:
				pres_mag_1 = 58500000
				pres_mag_2 = 78000000
			if steel_grade == 42:
				pres_mag_1 = 40000000
				pres_mag_2 = 60000000
			if steel_grade == 100:
				pres_mag_1 = 90000000
				pres_mag_2 = 110000000
		else:
			magic_pt = (0.0189993341502983, 0.219178067565725)
			magic_edge = (0.018028, 0.20797, pipe_len)
			pres_mag_1 = 31500000
			pres_mag_2 = 42000000
	else:
		if D_small:
			magic_pt = (0.022, 0.125079974416371)
			magic_edge = (0.0187, 0.106318, pipe_len)
			pres_mag_1 = 112000000
			pres_mag_2 = 140000000
		else:
			magic_pt = (0.02, 0.227723428746363)
			magic_edge = (0.018333, 0.208746, pipe_len)
			pres_mag_1 = 57600000
			pres_mag_2 = 72000000

	# Partition face: z-sym face
	mdb.models['Model-1'].ConstrainedSketch(gridSpacing=0.01, name='__profile__',
		sheetSize=0.5, transform=
		mdb.models['Model-1'].rootAssembly.MakeSketchTransform(
		sketchPlane=mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(
		(pipe_id + 0.001, 0.001, pipe_len), ), sketchPlaneSide=SIDE1,
		sketchUpEdge=mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(
		(0.0, pipe_id + 0.0001, pipe_len), ), sketchOrientation=RIGHT, origin=(0.0, 0.0, pipe_len)))
	mdb.models['Model-1'].rootAssembly.projectReferencesOntoSketch(filter=
		COPLANAR_EDGES, sketch=mdb.models['Model-1'].sketches['__profile__'])
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, 0.0), point2=magic_pt)
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((0.0,
		0.0), ), point1=(0.0, 0.0))
	mdb.models['Model-1'].rootAssembly.PartitionFaceBySketch(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((
		pipe_id + 0.001, 0.001, pipe_len), )), sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchUpEdge=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt((0.0,
		pipe_id + 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Partition face: x-sym face
	mdb.models['Model-1'].ConstrainedSketch(gridSpacing=0.01, name='__profile__',
		sheetSize=0.69, transform=
		mdb.models['Model-1'].rootAssembly.MakeSketchTransform(
		sketchPlane=mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(
		(0.0, pipe_id + 0.0001, pipe_len / 2), ), sketchPlaneSide=SIDE1,
		sketchUpEdge=mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(
		(0.0, pipe_id + 0.0001, pipe_len), ), sketchOrientation=RIGHT, origin=(0.0, pipe_id, pipe_len)))
	mdb.models['Model-1'].rootAssembly.projectReferencesOntoSketch(filter=
		COPLANAR_EDGES, sketch=mdb.models['Model-1'].sketches['__profile__'])
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(-crack_par, 0.0), point2=
		(-crack_par, thk))
	mdb.models['Model-1'].rootAssembly.PartitionFaceBySketch(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((0.0,
		pipe_id + 0.0001, pipe_len / 2), )), sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchUpEdge=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt((0.0,
		pipe_id + 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Partition cell: circumferential
	mdb.models['Model-1'].rootAssembly.PartitionCellByPlanePointNormal(cells=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		pipe_id, 0.0, pipe_len), )), normal=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt((0.0,
		pipe_id, pipe_len - 0.02), ), point=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].vertices.findAt((
		0.0, pipe_id, pipe_len - crack_par), ))

	# Partition cell: axial
	mdb.models['Model-1'].rootAssembly.PartitionCellByExtrudeEdge(cells=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		pipe_id, 0.0, pipe_len), ), ((pipe_id, 0.0, 0.0), ), ), edges=(
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(magic_edge, ), ), line=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt((
		pipe_id, 0.0, 0.0001), ), sense=REVERSE)

	# Create a set for the crack region for visualization
	mdb.models['Model-1'].rootAssembly.Set(faces=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].faces.findAt(((
		0.0001, pipe_od, pipe_len - crack_par + 0.0001), ), ((0.0, pipe_id + 0.0001, pipe_len - 0.0001), ), ((
		0.0001, pipe_id + 0.0001, pipe_len), ), ((0.0001, pipe_id, pipe_len - 0.0001), ),
		((0.0001, pipe_od - height, pipe_len - 0.0001), ),), name='flaw_region')

	# Set mesh control for the cracked region
	mdb.models['Model-1'].rootAssembly.setMeshControls(elemShape=TET, regions=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		0.0, pipe_id, pipe_len), )), technique=FREE)
	mdb.models['Model-1'].rootAssembly.setElementType(elemTypes=(ElemType(
		elemCode=C3D20R, elemLibrary=STANDARD), ElemType(elemCode=C3D15,
		elemLibrary=STANDARD), ElemType(elemCode=C3D10M, elemLibrary=STANDARD)),
		regions=(
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		0.0, pipe_id, pipe_len), )), ))

	# Seed the crack tip, double biased on the long edge
	mdb.models['Model-1'].rootAssembly.seedEdgeBySize(deviationFactor=0.8, edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(
		((crack_width, pipe_id + depth + 0.00001, pipe_len), ),
		((crack_width, pipe_id + depth - 0.00001, pipe_len), ),
		), size=mesh_fine)
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=DOUBLE,
		constraint=FINER, endEdges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(
		((0.0, pipe_id + depth, pipe_len - length), ), ),
		maxSize=(mesh_fine*2), minSize=mesh_fine)

	# Biased seeds inside the crack partition
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=SINGLE,
		constraint=FINER, end2Edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((0.0,
		pipe_id, pipe_len - 0.0001), ), ),maxSize=mesh_end2, minSize=mesh_end1)
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=SINGLE,
		constraint=FINER, end2Edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
		0.0001, pipe_id, pipe_len), )), maxSize=mesh_end2, minSize=mesh_end1)

	# Seed the corrsion wall loss
	mdb.models['Model-1'].rootAssembly.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
		0.0001, pipe_od, pipe_len - loss_width), ), ((0.0, pipe_od - height, pipe_len - 0.0001), ), ((0.0001,
		pipe_od - height, pipe_len), ), ), size=0.001)

	# Seed the rest of the pipe
	if T_small:
		if D_small:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016008, 0.103773, 0.28575), ), ((0.01658, 0.107479, 0.3), ), ((0.018295,
				0.118597, 0.29525), ), ((0.017723, 0.114891, 0.0), ), ((0.105, 0.0,
				0.28575), ), ((0.013745, 0.11921, 0.281), ), ((0.0, 0.10875, 0.281), ), ((
				0.004017, 0.104923, 0.281), ), ((0.004591, 0.119912, 0.0), ), ((0.10875,
				0.0, 0.0), ), ((0.10875, 0.0, 0.281), ), ((0.12, 0.0, 0.28575), ), ((
				0.004017, 0.104923, 0.0), ), ((0.11625, 0.0, 0.3), ), ((0.0, 0.11625, 0.0),
				), ), number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016008, 0.103773, 0.07025), ), ((0.018295, 0.118597, 0.21075), ), ((
				0.051028, 0.091767, 0.281), ), ((0.098473, 0.036441, 0.3), ), ((0.051028,
				0.091767, 0.0), ), ((0.105, 0.0, 0.07025), ), ((0.0, 0.12, 0.07025), ), ((
				0.058318, 0.104876, 0.0), ), ((0.112541, 0.041647, 0.281), ), ((0.12, 0.0,
				0.07025), ), ((0.058318, 0.104876, 0.3), ), ((0.0, 0.105, 0.07025), ), ),
				number=10)
		else:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017704, 0.204234, 0.28575), ), ((0.018028, 0.20797, 0.3), ), ((0.018999,
				0.219178, 0.29525), ), ((0.018675, 0.215442, 0.0), ), ((0.205, 0.0,
				0.28575), ), ((0.014257, 0.219538, 0.281), ), ((0.0, 0.20875, 0.281), ), ((
				0.004431, 0.204952, 0.281), ), ((0.004755, 0.219949, 0.0), ), ((0.20875,
				0.0, 0.0), ), ((0.20875, 0.0, 0.281), ), ((0.22, 0.0, 0.28575), ), ((
				0.004431, 0.204952, 0.0), ), ((0.21625, 0.0, 0.3), ), ((0.0, 0.21625, 0.0),
				), ), number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017704, 0.204234, 0.07025), ), ((0.018999, 0.219178, 0.21075), ), ((
				0.090559, 0.183913, 0.281), ), ((0.191047, 0.074338, 0.3), ), ((0.090559,
				0.183913, 0.0), ), ((0.205, 0.0, 0.07025), ), ((0.0, 0.22, 0.07025), ), ((
				0.097185, 0.19737, 0.0), ), ((0.205026, 0.079777, 0.281), ), ((0.22, 0.0,
				0.07025), ), ((0.097185, 0.19737, 0.3), ), ((0.0, 0.205, 0.07025), ), ),
				number=15)
	else:
		if D_small:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017539, 0.099719, 0.3), ), ((0.019705, 0.11203, 0.0), ), ((0.0, 0.10125,
				0.279), ), ((0.10125, 0.0, 0.0), ), ((0.10125, 0.0, 0.279), ), ((0.11375,
				0.0, 0.3), ), ((0.0, 0.11375, 0.0), ), ), number=5)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016457, 0.093564, 0.28425), ), ((0.020787, 0.118186, 0.29475), ), ((
				0.095, 0.0, 0.28425), ), ((0.015625, 0.118978, 0.279), ), ((0.004134,
				0.09491, 0.279), ), ((0.005222, 0.119886, 0.0), ), ((0.12, 0.0, 0.28425),
				), ((0.004134, 0.09491, 0.0), ), ), number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016457, 0.093564, 0.06975), ), ((0.020787, 0.118186, 0.20925), ), ((
				0.047474, 0.082288, 0.279), ), ((0.089267, 0.032501, 0.3), ), ((0.047474,
				0.082288, 0.0), ), ((0.095, 0.0, 0.06975), ), ((0.0, 0.12, 0.06975), ), ((
				0.059967, 0.103942, 0.0), ), ((0.112759, 0.041054, 0.279), ), ((0.12, 0.0,
				0.06975), ), ((0.059967, 0.103942, 0.3), ), ((0.0, 0.095, 0.06975), ), ),
				number=10)
		else:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017607, 0.200478, 0.3), ), ((0.018701, 0.21293, 0.0), ), ((0.0, 0.20125,
				0.279), ), ((0.20125, 0.0, 0.0), ), ((0.20125, 0.0, 0.279), ), ((0.21375,
				0.0, 0.3), ), ((0.0, 0.21375, 0.0), ), ), number=5)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.019248, 0.219156, 0.29475), ), ((0.195, 0.0, 0.28425), ), ((0.014444,
				0.219525, 0.279), ), ((0.004818, 0.219947, 0.0), ), ((0.22, 0.0, 0.28425),
				), ((0.01706, 0.194252, 0.28425), ), ((0.00427, 0.194953, 0.279), ), 
				((0.00427, 0.194953, 0.0), ), ), number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.01706, 0.194252, 0.06975), ), ((0.019248, 0.219156, 0.20925), ), ((
				0.08629, 0.174869, 0.279), ), ((0.181747, 0.07066, 0.3), ), ((0.08629,
				0.174869, 0.0), ), ((0.195, 0.0, 0.06975), ), ((0.0, 0.22, 0.06975), ), ((
				0.097353, 0.197288, 0.0), ), ((0.205048, 0.079719, 0.279), ), ((0.22, 0.0,
				0.06975), ), ((0.097353, 0.197288, 0.3), ), ((0.0, 0.195, 0.06975), ), ),
				number=15)

	# Generate mesh
	mdb.models['Model-1'].rootAssembly.generateMesh(regions=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		pipe_id, 0.0, 0.0), )))
	mdb.models['Model-1'].rootAssembly.generateMesh(regions=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		0.0, pipe_id, 0.0), )))
	mdb.models['Model-1'].rootAssembly.generateMesh(regions=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		pipe_id, 0.0, pipe_len), )))
	mdb.models['Model-1'].rootAssembly.generateMesh(regions=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].cells.findAt(((
		0.0, pipe_id, pipe_len), )))

	# Create step and field output
	mdb.models['Model-1'].StaticStep(maxNumInc=10, name='Step-1', nlgeom=ON,
		previous='Initial')
	mdb.models['Model-1'].StaticStep(initialInc=0.01, maxInc=0.01, minInc=5e-05,
		name='Step-2', previous='Step-1')
	mdb.models['Model-1'].FieldOutputRequest(createStepName='Step-1', name=
		'F-Output-1', rebar=EXCLUDE, region=
		mdb.models['Model-1'].rootAssembly.sets['flaw_region'], sectionPoints=
		DEFAULT, variables=('S', 'PEEQ', 'LE', 'U'))

	# Create load and BC
	mdb.models['Model-1'].Pressure(amplitude=UNSET, createStepName='Step-1',
		distributionType=UNIFORM, field='', magnitude=pres_mag_1, name='Load-1',
		region=mdb.models['Model-1'].rootAssembly.surfaces['inner'])
	mdb.models['Model-1'].loads['Load-1'].setValuesInStep(magnitude=pres_mag_2, stepName=
		'Step-2')
	mdb.models['Model-1'].XsymmBC(createStepName='Step-1', localCsys=None, name=
		'Xsym', region=mdb.models['Model-1'].rootAssembly.sets['x_sym'])
	mdb.models['Model-1'].YsymmBC(createStepName='Step-1', localCsys=None, name=
		'Ysym', region=mdb.models['Model-1'].rootAssembly.sets['y_sym'])
	mdb.models['Model-1'].ZsymmBC(createStepName='Step-1', localCsys=None, name=
		'Zsym', region=mdb.models['Model-1'].rootAssembly.sets['z_sym'])
	mdb.models['Model-1'].DisplacementBC(amplitude=UNSET, createStepName='Step-1',
		distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=None, name=
		'Zend', region=mdb.models['Model-1'].rootAssembly.sets['z_end'], u1=UNSET,
		u2=UNSET, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET)

	# Create job and submit
	mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF,
		explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF,
		memory=90, memoryUnits=PERCENTAGE, model='Model-1', modelPrint=OFF,
		multiprocessingMode=DEFAULT, name=job_name+str(index), nodalOutputPrecision=SINGLE,
		numCpus=16, numDomains=16, numGPUs=0, queue=None, resultsFormat=ODB,
		scratch='', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
	#mdb.jobs[job_name + str(index)].writeInput()
	mdb.jobs[job_name + str(index)].submit(consistencyChecking=OFF)
	mdb.jobs[job_name + str(index)].waitForCompletion()

	# Remove all the files after getting the data
	try:
		os.remove(job_name + str(index) + '.abq')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.mdl')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.pac')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.stt')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.prt')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.res')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.sim')
	except WindowsError:
		pass
	try:
		os.remove(job_name + str(index) + '.dat')
	except WindowsError:
		pass


with open('burst_pressure/' + job_name + 'summary.txt' ,'w') as f:
	f.write('---------------------------------------------------------------')
	f.write('\n Total factorial DOE: ' + str(num_of_simulation))
	f.write('\n Total simulations: ' + str(len(flaw_detail)))
	f.write('\n Pipe outer diameter: ' + str(pipe_od * 2 * 1000) + ' mm')
	f.write('\n Pipe thickness: ' + str(pipe_thk * 1000) + ' mm')
	f.write('\n---------------------------------------------------------------')
	f.write('\n Flaw parameters detail:')
	for item in flaw_detail:
		f.write('\n' + str(item)[1:-1])
	
