"""
Python script to generate two penny-shaped cracks within a quarter of a full pipe
There are two free parameters for the each of the elliptical crack:
 - Long axis (length)
 - Location (depth)

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
crack_length_1 = True
crack_length_2 = True
lig_length_1 = True
lig_length_2 = True

# Pipe switch
T_small = True  # Small thickness if True
D_small = True  # Small diameter if True

"""Set the parameters of the simulation"""
# Default crack parameters
default_length_1 = 0.0005
default_length_2 = 0.0005
default_lig_1 = 0.004
default_lig_2 = 0.004

# Pipe parameters
# Set 0.12 for 10'' pipe; set 0.22 for 18'' pipe
if D_small:
	pipe_od = 0.12
else:
	pipe_od = 0.22

# Set 0.0152 for 0.6'' pipe; set 0.0254 for 1'' pipe
if T_small:
	pipe_thk = 0.015
	crack_par = 0.014  # Partition near the crack
	max_length = 0.014  # Allowable maximum combined ligment and crack length
else:
	pipe_thk = 0.025
	crack_par = 0.018  # Partition near the crack
	max_length = 0.02  # Allowable maximum combined ligment and crack length

pipe_id = pipe_od - pipe_thk  # inner diameter
pipe_len = 0.3  # axial length
crack_width = 0.00025

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
if crack_length_1:
	if T_small:
		length_1s = [0.0005, 0.001, 0.0015]
	else:
		length_1s = [0.0005, 0.0015, 0.0025]
else:
	length_1s = [default_length_1]

if crack_length_2:
	if T_small:
		length_2s = [0.0005, 0.001, 0.0015]
	else:
		length_2s = [0.0005, 0.0015, 0.0025]
else:
	length_2s = [default_length_2]

if lig_length_1:
	if T_small:
		lig_1s = [0.002, 0.003, 0.004]
	else:
		lig_1s = [0.002, 0.004, 0.006]
else:
	lig_1s = [default_lig_1]

if lig_length_2:
	if T_small:
		lig_2s = [0.002, 0.003, 0.004]
	else:
		lig_2s = [0.002, 0.004, 0.006]
else:
	lig_2s = [default_lig_2]

# Number of simulation
num_of_simulation = len(length_1s) * len(length_2s) * len(lig_1s) * len(lig_2s)

# Job names
job_name = 'Burst_full_cc_sTsD_'

"""Initiate the while loop"""
for index in range(num_of_simulation):

	# Assign the crack parameters to the value
	length_1 = length_1s[index % len(length_1s)]
	length_2 = length_2s[int(index/len(length_1s)) % len(length_2s)]
	lig_1 = lig_1s[int(index/len(length_1s)/len(length_2s)) % len(lig_1s)]
	lig_2 = lig_2s[int(index/len(length_1s)/len(length_2s)/len(lig_1s)) % len(lig_2s)]

	total_length = length_1 * 2 + length_2 * 2 + lig_1 + lig_2
	lig_3 = pipe_thk - total_length

	# If the max length criterion is met, save it for output
	flaw_detail.append([index, length_1 * 2000, length_2 * 2000, lig_1 * 1000, lig_2 * 1000, lig_3 * 1000])

	# Calculate depths
	thk = pipe_thk
	depth_1 = lig_1 + length_1
	depth_2 = lig_1 + length_1 * 2 + lig_2 + length_2

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
		axisPoint1=(0.0, depth_1 + length_1), axisPoint2=(crack_width,
		depth_1), center=(0.0, depth_1))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth_1 - length_1),
		point2=(0.0, depth_1))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth_1), point2=
		(crack_width, depth_1))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((-crack_width,
		depth_1), ), point1=(-crack_width, depth_1))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((0.0,
		depth_1 + length_1), ), point1=(0.0, depth_1 + length_1))
	mdb.models['Model-1'].sketches['__profile__'].ConstructionLine(angle=0.0,
		point1=(0.0, depth_1))
	mdb.models['Model-1'].parts['pipe'].CutRevolve(angle=180.0,
		flipRevolveDirection=OFF, sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchOrientation=RIGHT,
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((pipe_id + 0.0001,
		0.0001, pipe_len), ), sketchPlaneSide=SIDE1, sketchUpEdge=
		mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0, pipe_id + 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Create the second crack
	mdb.models['Model-1'].ConstrainedSketch(gridSpacing=0.01, name='__profile__',
		sheetSize=0.64, transform=
		mdb.models['Model-1'].parts['pipe'].MakeSketchTransform(
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((pipe_id + 0.0001,
		0.0001, pipe_len), ), sketchPlaneSide=SIDE1,
		sketchUpEdge=mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0,
		pipe_od - 0.0001, pipe_len), ), sketchOrientation=RIGHT, origin=(0.0, pipe_id, pipe_len)))
	mdb.models['Model-1'].parts['pipe'].projectReferencesOntoSketch(filter=
		COPLANAR_EDGES, sketch=mdb.models['Model-1'].sketches['__profile__'])
	mdb.models['Model-1'].sketches['__profile__'].EllipseByCenterPerimeter(
		axisPoint1=(0.0, depth_2 + length_2), axisPoint2=(crack_width,
		depth_2), center=(0.0, depth_2))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth_2 - length_2),
		point2=(0.0, depth_2))
	mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, depth_2), point2=
		(crack_width, depth_2))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((-crack_width,
		depth_2), ), point1=(-crack_width, depth_2))
	mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((0.0,
		depth_2 + length_2), ), point1=(0.0, depth_2 + length_2))
	mdb.models['Model-1'].sketches['__profile__'].ConstructionLine(angle=0.0,
		point1=(0.0, depth_2))
	mdb.models['Model-1'].sketches['__profile__'].sketchOptions.setValues(
		constructionGeometry=ON)
	mdb.models['Model-1'].sketches['__profile__'].assignCenterline(line=
		mdb.models['Model-1'].sketches['__profile__'].geometry.findAt((-0.1,
		depth_2), ))
	mdb.models['Model-1'].parts['pipe'].CutRevolve(angle=180.0,
		flipRevolveDirection=OFF, sketch=
		mdb.models['Model-1'].sketches['__profile__'], sketchOrientation=RIGHT,
		sketchPlane=mdb.models['Model-1'].parts['pipe'].faces.findAt((pipe_id + 0.0001,
		0.0001, pipe_len), ), sketchPlaneSide=SIDE1, sketchUpEdge=
		mdb.models['Model-1'].parts['pipe'].edges.findAt((0.0, pipe_od - 0.0001, pipe_len), ))
	del mdb.models['Model-1'].sketches['__profile__']

	# Material properties and assembly
	# Yield stress is 464.5 MPa and ultimate tensile strength is 563.8 MPa according to paper
	mdb.models['Model-1'].Material(name='steel')
	mdb.models['Model-1'].materials['steel'].Density(table=((mat_density,),))
	mdb.models['Model-1'].materials['steel'].Elastic(table=((young_modulus, poisson_ratio),))
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
			magic_pt = (0.0154052750086153, 0.126062196958124)
			magic_edge = (0.014022, 0.114746, pipe_len)
			pres_mag_1 = 73500000
			pres_mag_2 = 79000000
		else:
			magic_pt = (0.0146274740894786, 0.228131534430823)
			magic_edge = (0.013898, 0.216755, pipe_len)
			pres_mag_1 = 38000000
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
		0.0001, pipe_od, pipe_len - 0.0001), ), ((0.0, pipe_id + 0.0001, pipe_len - 0.0001), ), ((
		0.0001, pipe_id + 0.0001, pipe_len), ), ((0.0001, pipe_id, pipe_len - 0.0001), ), ), name=
		'flaw_region')

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
		((crack_width, pipe_id + depth_1 + 0.00001, pipe_len), ),
		((crack_width, pipe_id + depth_1 - 0.00001, pipe_len), ),
		((crack_width, pipe_id + depth_2 + 0.00001, pipe_len), ),
		((crack_width, pipe_id + depth_2 - 0.00001, pipe_len), ),
		), size=mesh_fine)
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=DOUBLE,
		constraint=FINER, endEdges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((0.0,
		pipe_id + depth_1, pipe_len - length_1), ), ((0.0, pipe_id + depth_2, pipe_len - length_2), ), ),
		maxSize=(mesh_fine*2), minSize=mesh_fine)

	# Biased seeds inside the crack partition
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=SINGLE,
		constraint=FINER, end2Edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((0.0,
		pipe_id, pipe_len - 0.0001), ), ((0.0, pipe_od, pipe_len - 0.0001), ), ),
		maxSize=mesh_end2, minSize=mesh_end1)
	mdb.models['Model-1'].rootAssembly.seedEdgeByBias(biasMethod=SINGLE,
		constraint=FINER, end2Edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
		0.0001, pipe_id, pipe_len), )), end1Edges=
		mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
		0.0001, pipe_od, pipe_len), )), maxSize=mesh_end2, minSize=mesh_end1)

	# Seed the rest of the pipe
	if T_small:
		if D_small:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.012737, 0.104225, 0.2895), ), ((0.013192, 0.107947, 0.3), ), ((0.014556,
				0.119114, 0.2965), ), ((0.014101, 0.115392, 0.0), ), ((0.105, 0.0, 0.2895),
				), ((0.010929, 0.119501, 0.286), ), ((0.0, 0.10875, 0.286), ), ((0.003192,
				0.104951, 0.286), ), ((0.003647, 0.119945, 0.0), ), ((0.10875, 0.0, 0.0),
				), ((0.10875, 0.0, 0.286), ), ((0.12, 0.0, 0.2895), ), ((0.003192,
				0.104951, 0.0), ), ((0.11625, 0.0, 0.3), ), ((0.0, 0.11625, 0.0), ), ),
				number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.012737, 0.104225, 0.0715), ), ((0.014556, 0.119114, 0.2145), ), ((
				0.04885, 0.092945, 0.286), ), ((0.098184, 0.037215, 0.3), ), ((0.04885,
				0.092945, 0.0), ), ((0.105, 0.0, 0.0715), ), ((0.0, 0.12, 0.0715), ), ((
				0.055828, 0.106222, 0.0), ), ((0.11221, 0.042531, 0.286), ), ((0.12, 0.0,
				0.0715), ), ((0.055828, 0.106222, 0.3), ), ((0.0, 0.105, 0.0715), ), ),
				number=10)
		else:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.013117, 0.20458, 0.2895), ), ((0.013357, 0.208322, 0.3), ), ((0.014077,
				0.219549, 0.2965), ), ((0.013837, 0.215807, 0.0), ), ((0.205, 0.0, 0.2895),
				), ((0.010561, 0.219746, 0.286), ), ((0.0, 0.20875, 0.286), ), ((0.003281,
				0.204974, 0.286), ), ((0.003522, 0.219972, 0.0), ), ((0.20875, 0.0, 0.0),
				), ((0.20875, 0.0, 0.286), ), ((0.22, 0.0, 0.2895), ), ((0.003281,
				0.204974, 0.0), ), ((0.21625, 0.0, 0.3), ), ((0.0, 0.21625, 0.0), ), ),
				number=3)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.013117, 0.20458, 0.0715), ), ((0.014077, 0.219549, 0.2145), ), ((
				0.087452, 0.185411, 0.286), ), ((0.190627, 0.075408, 0.3), ), ((0.087452,
				0.185411, 0.0), ), ((0.205, 0.0, 0.0715), ), ((0.0, 0.22, 0.0715), ), ((
				0.09385, 0.198978, 0.0), ), ((0.204575, 0.080926, 0.286), ), ((0.22, 0.0,
				0.0715), ), ((0.09385, 0.198978, 0.3), ), ((0.0, 0.205, 0.0715), ), ),
				number=15)
	else:
		if D_small:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016457, 0.093564, 0.2865), ), ((0.017539, 0.099719, 0.3), ), ((0.020787,
				0.118186, 0.2955), ), ((0.019705, 0.11203, 0.0), ), ((0.095, 0.0, 0.2865),
				), ((0.015625, 0.118978, 0.282), ), ((0.0, 0.10125, 0.282), ), ((0.004134,
				0.09491, 0.282), ), ((0.005222, 0.119886, 0.0), ), ((0.10125, 0.0, 0.0), ),
				((0.10125, 0.0, 0.282), ), ((0.12, 0.0, 0.2865), ), ((0.004134, 0.09491,
				0.0), ), ((0.11375, 0.0, 0.3), ), ((0.0, 0.11375, 0.0), ), ), number=4)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.016457, 0.093564, 0.0705), ), ((0.020787, 0.118186, 0.2115), ), ((
				0.047474, 0.082288, 0.282), ), ((0.089267, 0.032501, 0.3), ), ((0.047474,
				0.082288, 0.0), ), ((0.095, 0.0, 0.0705), ), ((0.0, 0.12, 0.0705), ), ((
				0.059967, 0.103942, 0.0), ), ((0.112759, 0.041054, 0.282), ), ((0.12, 0.0,
				0.0705), ), ((0.059967, 0.103942, 0.3), ), ((0.0, 0.095, 0.0705), ), ),
				number=10)
		else:
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017778, 0.202421, 0.2865), ), ((0.018333, 0.208746, 0.3), ), ((0.02,
				0.227723, 0.2955), ), ((0.019444, 0.221398, 0.0), ), ((0.2032, 0.0,
				0.2865), ), ((0.015008, 0.228107, 0.282), ), ((0.0, 0.20955, 0.282), ), ((
				0.00445, 0.203151, 0.282), ), ((0.005006, 0.228545, 0.0), ), ((0.20955,
				0.0, 0.0), ), ((0.20955, 0.0, 0.282), ), ((0.2286, 0.0, 0.2865), ), ((
				0.00445, 0.203151, 0.0), ), ((0.22225, 0.0, 0.3), ), ((0.0, 0.22225, 0.0),
				), ), number=4)
			mdb.models['Model-1'].rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
				mdb.models['Model-1'].rootAssembly.instances['pipe-1'].edges.findAt(((
				0.017778, 0.202421, 0.0705), ), ((0.02, 0.227723, 0.2115), ), ((0.089919,
				0.182222, 0.282), ), ((0.18939, 0.073632, 0.3), ), ((0.089919, 0.182222,
				0.0), ), ((0.2032, 0.0, 0.0705), ), ((0.0, 0.2286, 0.0705), ), ((0.101159,
				0.205, 0.0), ), ((0.213064, 0.082836, 0.282), ), ((0.2286, 0.0, 0.0705), ),
				((0.101159, 0.205, 0.3), ), ((0.0, 0.2032, 0.0705), ), ), number=12)

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
		numCpus=18, numDomains=18, numGPUs=0, queue=None, resultsFormat=ODB,
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


with open('burst_pressure/' + job_name + 'summary.txt', 'w') as f:
	f.write('---------------------------------------------------------------')
	f.write('\n Total factorial DOE: ' + str(num_of_simulation))
	f.write('\n Total simulations: ' + str(len(flaw_detail)))
	f.write('\n Pipe outer diameter: ' + str(pipe_od * 2 * 1000) + ' mm')
	f.write('\n Pipe thickness: ' + str(pipe_thk * 1000) + ' mm')
	f.write('\n---------------------------------------------------------------')
	f.write('\n Flaw parameters detail:')
	for item in flaw_detail:
		f.write('\n' + str(item)[1:-1])
