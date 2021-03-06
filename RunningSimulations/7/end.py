#> Main script
# Add Python bindings directory to PATH
import sys, os
import math
import numpy as np
import time
import exfile

start = time.time() 
# Intialise OpenCMISS
from opencmiss.iron import iron

# Set problem parameters
growthModel = 1 # Type of growth. 1 - volumetric; 2 - stress based; 3 - strain based.
isotropic = False # True if the problem is isotropic, False if the problem is anisotropic
homogeneous = False # True if the growth rates are homogeneous, False if the problem is heterogeneous
useFibres = True # True if fibres are used for anisotropic problems
heterogeneousFibres = False # True if the fibre angles vary in space, False if not.
fixBottomRing = True # True if the bottom ring of nodes is fixed, False if not
fixTopRing = False # True if the top ring of nodes is fixed, False if not
exfileMesh = True # The files of the mesh will be accessed through the code ... exnode exelem


numberOfLengthElements=8 # Number of elements along the length of the tube
numberOfCircumfrentialElements=8 # Number of elements in the circumfrential direction in one quarter of the tube
numberOfWallElements=1 # Number of elements through the wall of the tube

# Hydrostatic pressure
pInit = -8.0 # The initial hydrostatic pressure

# Fibre angle
#fibreAngle = math.pi/2.0 # The fibre angle wrt the for anisotropic fibres
fibreAngle = 0.0 # The fibre angle wrt the for anisotropic fibres

# Times
startTime = 0.0 # The start time for the growth simulation
timeIncrement = 1.0 # The time increment for the growth simulation

# Number of Gauss points used
numberOfGaussXi = 3

numberOfLengthNodes = numberOfLengthElements+1
numberOfCircumfrentialNodes = numberOfCircumfrentialElements
numberOfWallNodes = numberOfWallElements+1


coordinateSystemUserNumber = 1
regionUserNumber = 1
tricubicHermiteBasisUserNumber = 1
trilinearLagrangeBasisUserNumber = 2
meshUserNumber = 1
decompositionUserNumber = 1
geometricFieldUserNumber = 1
originalGeometricFieldUserNumber = 12
fibreFieldUserNumber = 2
dependentFieldUserNumber = 3
equationsSetUserNumber = 1
equationsSetFieldUserNumber = 5
growthCellMLUserNumber = 1
growthCellMLModelsFieldUserNumber = 6
growthCellMLStateFieldUserNumber = 7
growthCellMLParametersFieldUserNumber = 8
constitutiveCellMLUserNumber = 2
constitutiveCellMLModelsFieldUserNumber = 9
constitutiveCellMLParametersFieldUserNumber = 10
constitutiveCellMLIntermediateFieldUserNumber = 11
problemUserNumber = 1

#iron.DiagnosticsSetOn(iron.DiagnosticTypes.FROM,[1,2,3,4,5],"diagnostics",["FiniteElasticity_FiniteElementResidualEvaluate"])
# Get the number of computational nodes and this computational node number
numberOfComputationalNodes = iron.ComputationalNumberOfNodesGet()
computationalNodeNumber = iron.ComputationalNodeNumberGet()

# Create a 3D rectangular cartesian coordinate system
coordinateSystem = iron.CoordinateSystem()
coordinateSystem.CreateStart(coordinateSystemUserNumber)
# Set the number of dimensions to 3
coordinateSystem.DimensionSet(3)
# Finish the creation of the coordinate system
coordinateSystem.CreateFinish()

# Create a region and assign the coordinate system to the region
region = iron.Region()
region.CreateStart(regionUserNumber,iron.WorldRegion)
region.LabelSet("HeartTubeRegion")
# Set the regions coordinate system to the 3D RC coordinate system that we have created
region.coordinateSystem = coordinateSystem
# Finish the creation of the region
region.CreateFinish()

# Define basis
# Start the creation of a tricubic Hermite basis function
tricubicHermiteBasis = iron.Basis()
tricubicHermiteBasis.CreateStart(tricubicHermiteBasisUserNumber)
tricubicHermiteBasis.type = iron.BasisTypes.LAGRANGE_HERMITE_TP
tricubicHermiteBasis.numberOfXi = 3
tricubicHermiteBasis.interpolationXi = [iron.BasisInterpolationSpecifications.CUBIC_HERMITE]*3
tricubicHermiteBasis.quadratureNumberOfGaussXi = [numberOfGaussXi]*3
tricubicHermiteBasis.CreateFinish()
# Start the creation of a trilinear Hermite basis function
trilinearLagrangeBasis = iron.Basis()
trilinearLagrangeBasis.CreateStart(trilinearLagrangeBasisUserNumber)
trilinearLagrangeBasis.type = iron.BasisTypes.LAGRANGE_HERMITE_TP
trilinearLagrangeBasis.numberOfXi = 3
trilinearLagrangeBasis.interpolationXi = [iron.BasisInterpolationSpecifications.LINEAR_LAGRANGE]*3
trilinearLagrangeBasis.quadratureNumberOfGaussXi = [numberOfGaussXi]*3
trilinearLagrangeBasis.CreateFinish()

# Start the creation of a manually generated mesh in the region
numberOfNodes = numberOfCircumfrentialElements*(numberOfLengthElements+1)*(numberOfWallElements+1)
numberOfElements = numberOfCircumfrentialElements*numberOfLengthElements*numberOfWallElements

print numberOfNodes, numberOfElements
stageNumber = 7
partNumber = 0
# providing the names of the exfile mesh ... exnode and exelem files ... 
if exfileMesh:
    exnode = exfile.Exnode("mesh" + str(stageNumber) + "-8x8.part0.exnode")
#    exelem = exfile.Exelem("initial" + str(stageNumber) + "-4x4.part0.exelem")
#if exfileMesh:
#    exnode = exfile.Exnode("UndeformedGeometry.part" + str(partNumber) + ".exnode")
#    exelem = exfile.Exelem("UndeformedGeometry.part" + str(partNumber) + ".exelem")
else:
    exfileMesh = False

# reading the data from the exnode and exelem files ... 
if (not exfileMesh):
    # Read previous mesh
    mesh = iron.Mesh()
    mesh.CreateStart(meshUserNumber, region, 3)
    mesh.NumberOfComponentsSet(2)
    mesh.NumberOfElementsSet(numberOfElements)
    #mesh.NumberOfElementsSet(exelem.num_elements)
    # Define nodes for the mesh
    nodes = iron.Nodes()
    nodes.CreateStart(region, exnode.num_nodes)
    nodes.CreateFinish()
    # Define elements for the mesh
    trilinearLagrangeElements = iron.MeshElements()
    trilinearLagrangeElements.CreateStart(mesh, 2, trilinearLagrangeBasis)
    tricubicHermiteElements = iron.MeshElements()
    tricubicHermiteElements.CreateStart(mesh, 1, tricubicHermiteBasis)
    #for elem in exelem.trilinearLagrangeElements:
    #    trilinearLagrangeElements.NodesSet(elementNumber,localNodes)
    #    trilinearLagrangeElements.NodesSet(elem.number, elem.nodes)
    #for elem in exelem.tricubicHermiteElements:
    #    tricubicHermiteElements.NodesSet(elementNumber,localNodes)
    #    tricubicHermiteElements.NodesSet(elem.number, elem.nodes)
    tricubicHermiteElements.CreateFinish()
    trilinearLagrangeElements.CreateFinish()
    mesh.CreateFinish()
# Create the mesh. The mesh will have two components - 1. tricubic Hermite elements; 2. trilinear Lagrange elements
else:
    mesh = iron.Mesh()
    mesh.CreateStart(meshUserNumber, region, 3)
    mesh.NumberOfComponentsSet(2)
    #mesh.NumberOfElementsSet(exelem.num_elements)
    mesh.NumberOfElementsSet(numberOfElements)
    # Define nodes for the mesh
    nodes = iron.Nodes()
    nodes.CreateStart(region, exnode.num_nodes)
    nodes.CreateFinish()
    # Define elements for the mesh
    tricubicHermiteElements = iron.MeshElements()
    tricubicHermiteElements.CreateStart(mesh, 1, tricubicHermiteBasis)
    trilinearLagrangeElements = iron.MeshElements()
    trilinearLagrangeElements.CreateStart(mesh, 2, trilinearLagrangeBasis)
    elementNumber = 0
    for wallElementIdx in range(1,numberOfWallElements+1):
        for lengthElementIdx in range(1,numberOfLengthElements+1):
            for circumfrentialElementIdx in range(1,numberOfCircumfrentialElements+1):
                elementNumber = elementNumber + 1
                #print elementNumber, "elementNumber Order"
                localNode1 = circumfrentialElementIdx + (lengthElementIdx-1)*numberOfCircumfrentialNodes + \
                    (wallElementIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                if circumfrentialElementIdx == numberOfCircumfrentialElements:
                    localNode2 = 1 + (lengthElementIdx-1)*numberOfCircumfrentialNodes + \
                        (wallElementIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                else:
                    localNode2 = localNode1 + 1
                localNode3 = localNode1 + numberOfCircumfrentialNodes
                localNode4 = localNode2 + numberOfCircumfrentialNodes
                localNode5 = localNode1 + numberOfCircumfrentialNodes*numberOfLengthNodes
                localNode6 = localNode2 + numberOfCircumfrentialNodes*numberOfLengthNodes
                localNode7 = localNode3 + numberOfCircumfrentialNodes*numberOfLengthNodes
                localNode8 = localNode4 + numberOfCircumfrentialNodes*numberOfLengthNodes
                localNodes = [localNode1,localNode2,localNode3,localNode4,localNode5,localNode6,localNode7,localNode8]
                tricubicHermiteElements.NodesSet(elementNumber,localNodes)
                trilinearLagrangeElements.NodesSet(elementNumber,localNodes)

    tricubicHermiteElements.CreateFinish()
    trilinearLagrangeElements.CreateFinish()

    # Finish the mesh creation
    mesh.CreateFinish() 

# Create a decomposition for the mesh
decomposition = iron.Decomposition()
decomposition.CreateStart(decompositionUserNumber,mesh)
# Set the decomposition to be a general decomposition with the specified number of domains
decomposition.type = iron.DecompositionTypes.CALCULATED
decomposition.numberOfDomains = numberOfComputationalNodes
# Finish the decomposition
decomposition.CreateFinish()

# Get nodes
nodes = iron.Nodes()
region.NodesGet(nodes)
numberOfNodes = nodes.numberOfNodes

# Create a field for the geometry
geometricField = iron.Field()
geometricField.CreateStart(geometricFieldUserNumber,region)
# Set the decomposition to use
geometricField.MeshDecompositionSet(decomposition)
geometricField.TypeSet(iron.FieldTypes.GEOMETRIC)
# Set the field label
geometricField.VariableLabelSet(iron.FieldVariableTypes.U,"Geometry")
# Set the domain to be used by the field components to be tricubic Hermite
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,1)
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,1)
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,1)
# Set the scaling type
geometricField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
# Finish creating the field
geometricField.CreateFinish()

# defining another Geometric  field with the same set-up to be used for any new iteration of optimization 
originalGeometricField = iron.Field()
originalGeometricField.CreateStart(originalGeometricFieldUserNumber,region)
# Set the decomposition to use
originalGeometricField.MeshDecompositionSet(decomposition)
originalGeometricField.TypeSet(iron.FieldTypes.GEOMETRIC)
# Set the field label
originalGeometricField.VariableLabelSet(iron.FieldVariableTypes.U,"OriginalGeometry")
# Set the domain to be used by the field components to be tricubic Hermite
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,1)
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,1)
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,1)
# Set the scaling type
originalGeometricField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
# Finish creating the field
originalGeometricField.CreateFinish()

derivativeValues = []

#adding coordinates of the nodes 
geometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
originalGeometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
#adding dervatives of the nodes 
for node_num in range(1, exnode.num_nodes + 1):
    version = 1
    derivative = 1        
    for component in range(1, 3 + 1):
        component_name = ["x", "y", "z"][component - 1]
        value = exnode.node_value("Coordinate", component_name, node_num, derivative)
        geometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, value)        
        originalGeometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, value)        
    derivative = 2
    for component in range(1, 3 + 1):
        component_name = ["x", "y", "z"][component - 1]
        derivativeValues = exnode.node_values("Coordinate", component_name, node_num)
        geometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[1])
        originalGeometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[1])
    derivative = 3
    for component in range(1, 3 + 1):
        component_name = ["x", "y", "z"][component - 1]
        derivativeValues = exnode.node_values("Coordinate", component_name, node_num)
        geometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[2])        
        originalGeometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[2])        
    derivative = 5
    for component in range(1, 3 + 1):
        component_name = ["x", "y", "z"][component - 1]
        derivativeValues = exnode.node_values("Coordinate", component_name, node_num)
        geometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[4])
        originalGeometricField.ParameterSetUpdateNode(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES, version, derivative, node_num, component, derivativeValues[4])
geometricField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
originalGeometricField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)

if useFibres:
    # Create a fibre field and attach it to the geometric field
    fibreField = iron.Field()
    fibreField.CreateStart(fibreFieldUserNumber,region)
    fibreField.TypeSet(iron.FieldTypes.FIBRE)
    # Set the decomposition 
    fibreField.MeshDecompositionSet(decomposition)
    # Set the geometric field
    fibreField.GeometricFieldSet(geometricField)
    # Set the field variable label
    fibreField.VariableLabelSet(iron.FieldVariableTypes.U,"Fibre")
    # Set the fibre field to use trilinear-Lagrange elements
    fibreField.NumberOfComponentsSet(iron.FieldVariableTypes.U,3)
    fibreField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,2)
    fibreField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,2)
    fibreField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,2)
    # Finish creating the field
    fibreField.CreateFinish()
    #Initialise the fibre field
    for wallNodeIdx in range(1,numberOfWallNodes+1):
        for lengthNodeIdx in range(1,numberOfLengthNodes+1):
            for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
                nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + \
                    (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                # Set the fibre angle
                if heterogeneousFibres == True:
                    theta = float(circumfrentialNodeIdx-1)/float(numberOfCircumfrentialNodes)*2.0*math.pi
                    angle = fibreAngle*math.sin(theta)
                else:
                    angle = fibreAngle
                fibreField.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                        1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,1,angle)
                fibreField.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                        1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,2,0.0)
                fibreField.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                        1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,3,0.0)
    # Update the fibre field
    fibreField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
    fibreField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)

# Create the dependent field
dependentField = iron.Field()
dependentField.CreateStart(dependentFieldUserNumber,region)
dependentField.TypeSet(iron.FieldTypes.GEOMETRIC_GENERAL)
# Set the decomposition
dependentField.MeshDecompositionSet(decomposition)
# Set the geometric field
dependentField.GeometricFieldSet(geometricField) 
dependentField.DependentTypeSet(iron.FieldDependentTypes.DEPENDENT)
# Set the field variables for displacement, traction, strain, stress and growth
dependentField.NumberOfVariablesSet(5)
dependentField.VariableTypesSet([iron.FieldVariableTypes.U,iron.FieldVariableTypes.DELUDELN,
                                 iron.FieldVariableTypes.U1,iron.FieldVariableTypes.U2,iron.FieldVariableTypes.U3])
dependentField.VariableLabelSet(iron.FieldVariableTypes.U,"Dependent")
dependentField.VariableLabelSet(iron.FieldVariableTypes.DELUDELN,"del U/del n")
dependentField.VariableLabelSet(iron.FieldVariableTypes.U1,"Strain")
dependentField.VariableLabelSet(iron.FieldVariableTypes.U2,"Stress")
dependentField.VariableLabelSet(iron.FieldVariableTypes.U3,"Growth")
dependentField.NumberOfComponentsSet(iron.FieldVariableTypes.U,4)
dependentField.NumberOfComponentsSet(iron.FieldVariableTypes.DELUDELN,4)
dependentField.NumberOfComponentsSet(iron.FieldVariableTypes.U1,6)
dependentField.NumberOfComponentsSet(iron.FieldVariableTypes.U2,6)
dependentField.NumberOfComponentsSet(iron.FieldVariableTypes.U3,3)
# Set the hydrostatic pressure to use tri-linear Lagrange elements
dependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,4,2)
dependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.DELUDELN,4,2)
# Set the strain, stress and growth variables to be Gauss point based.
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,1,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,2,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,3,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,4,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,5,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U1,6,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,1,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,2,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,3,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,4,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,5,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U2,6,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U3,1,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U3,2,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U3,3,
                                         iron.FieldInterpolationTypes.GAUSS_POINT_BASED)
# Set the field scaling
dependentField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
# Finish creating the field
dependentField.CreateFinish()

# Initialise dependent field from undeformed geometry
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1)
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2)
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,3,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,3)
# Initialise the hydrostatic pressure
iron.Field.ComponentValuesInitialiseDP(dependentField,iron.FieldVariableTypes.U,
                                       iron.FieldParameterSetTypes.VALUES,4,pInit)

# Create the equations_set
equationsSetField = iron.Field()
equationsSet = iron.EquationsSet()
# Specify a finite elasticity equations set with the growth and constitutive law in CellML
equationsSetSpecification = [iron.EquationsSetClasses.ELASTICITY,
    iron.EquationsSetTypes.FINITE_ELASTICITY,
    iron.EquationsSetSubtypes.CONSTIT_AND_GROWTH_LAW_IN_CELLML]
if useFibres:
    equationsSet.CreateStart(equationsSetUserNumber,region,fibreField,
                             equationsSetSpecification,equationsSetFieldUserNumber,
                             equationsSetField)
else:
    equationsSet.CreateStart(equationsSetUserNumber,region,geometricField,
                             equationsSetSpecification,equationsSetFieldUserNumber,
                             equationsSetField)
equationsSet.CreateFinish()

# Set up the equation set dependent field
equationsSet.DependentCreateStart(dependentFieldUserNumber,dependentField)
equationsSet.DependentCreateFinish()

# Create equations
equations = iron.Equations()
equationsSet.EquationsCreateStart(equations)
# Use sparse equations
equations.sparsityType = iron.EquationsSparsityTypes.SPARSE
# Do not output any equations information
equations.outputType = iron.EquationsOutputTypes.NONE
# Finish creating the equations
equationsSet.EquationsCreateFinish()

# Set up the growth CellML model
growthCellML = iron.CellML()
growthCellML.CreateStart(growthCellMLUserNumber,region)
if growthModel == 1:
    # Create the CellML environment for the simple growth law
    growthCellMLIdx = growthCellML.ModelImport("simplegrowth.cellml")
    # Flag the CellML variables that OpenCMISS will supply
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/fibrerate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/sheetrate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/normalrate")
elif growthModel == 2:
    # Create the CellML environment for the stress based growth law
    growthCellML = iron.CellML()
    growthCellML.CreateStart(growthCellMLUserNumber,region)
    growthCellMLIdx = growthCellML.ModelImport("stressgrowth.cellml")
    # Flag the CellML variables that OpenCMISS will supply
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/fibrerate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/sheetrate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/normalrate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/S11")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/S22")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/S33")
elif growthModel == 3:
    # Create the CellML environment for the strain based growth law
    growthCellML = iron.CellML()
    growthCellML.CreateStart(growthCellMLUserNumber,region)
    growthCellMLIdx = growthCellML.ModelImport("straingrowth.cellml")
    # Flag the CellML variables that OpenCMISS will supply
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/fibrerate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/sheetrate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/normalrate")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/C11")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/C22")
    growthCellML.VariableSetAsKnown(growthCellMLIdx,"Main/C33")
# Finish the growth CellML
growthCellML.CreateFinish()

# Create CellML <--> OpenCMISS field maps
growthCellML.FieldMapsCreateStart()
if growthModel == 2:
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U2,1,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/S11",iron.FieldParameterSetTypes.VALUES)
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U2,2,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/S22",iron.FieldParameterSetTypes.VALUES)
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U2,3,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/S33",iron.FieldParameterSetTypes.VALUES)
elif growthModel == 3:
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,1,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/C11",iron.FieldParameterSetTypes.VALUES)
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,2,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/C22",iron.FieldParameterSetTypes.VALUES)
    growthCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,3,iron.FieldParameterSetTypes.VALUES,
                                        growthCellMLIdx,"Main/C33",iron.FieldParameterSetTypes.VALUES)
growthCellML.CreateCellMLToFieldMap(growthCellMLIdx,"Main/lambda1",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U3,1,iron.FieldParameterSetTypes.VALUES)
growthCellML.CreateCellMLToFieldMap(growthCellMLIdx,"Main/lambda2",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U3,2,iron.FieldParameterSetTypes.VALUES)
growthCellML.CreateCellMLToFieldMap(growthCellMLIdx,"Main/lambda3",iron.FieldParameterSetTypes.VALUES,
        dependentField,iron.FieldVariableTypes.U3,3,iron.FieldParameterSetTypes.VALUES)
growthCellML.FieldMapsCreateFinish()

# Create the CELL models field
growthCellMLModelsField = iron.Field()
growthCellML.ModelsFieldCreateStart(growthCellMLModelsFieldUserNumber,growthCellMLModelsField)
growthCellMLModelsField.VariableLabelSet(iron.FieldVariableTypes.U,"GrowthModelMap")
growthCellML.ModelsFieldCreateFinish()

# Create the CELL parameters field
growthCellMLParametersField = iron.Field()
growthCellML.ParametersFieldCreateStart(growthCellMLParametersFieldUserNumber,growthCellMLParametersField)
growthCellMLParametersField.VariableLabelSet(iron.FieldVariableTypes.U,"GrowthParameters")
growthCellML.ParametersFieldCreateFinish()

# Create the CELL state field
growthCellMLStateField = iron.Field()
growthCellML.StateFieldCreateStart(growthCellMLStateFieldUserNumber,growthCellMLStateField)
growthCellMLStateField.VariableLabelSet(iron.FieldVariableTypes.U,"GrowthState")
growthCellML.StateFieldCreateFinish()

# Create the CellML environment for the consitutative law
constitutiveCellML = iron.CellML()
constitutiveCellML.CreateStart(constitutiveCellMLUserNumber,region)
constitutiveCellMLIdx = constitutiveCellML.ModelImport("mooneyrivlin.cellml")
# Flag the CellML variables that OpenCMISS will supply
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E11")
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E12")
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E13")
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E22")
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E23")
constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/E33")
#constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/c1")
#constitutiveCellML.VariableSetAsKnown(constitutiveCellMLIdx,"equations/c2")
# Flag the CellML variables that OpenCMISS will obtain
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev11")
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev12")
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev13")
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev22")
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev23")
constitutiveCellML.VariableSetAsWanted(constitutiveCellMLIdx,"equations/Tdev33")
constitutiveCellML.CreateFinish()

# Create CellML <--> OpenCMISS field maps
constitutiveCellML.FieldMapsCreateStart()
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,1,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E11",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,2,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E12",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,3,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E13",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,4,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E22",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,5,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E23",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateFieldToCellMLMap(dependentField,iron.FieldVariableTypes.U1,6,iron.FieldParameterSetTypes.VALUES,
    constitutiveCellMLIdx,"equations/E33",iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev11",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,1,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev12",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,2,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev13",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,3,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev22",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,4,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev23",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,5,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.CreateCellMLToFieldMap(constitutiveCellMLIdx,"equations/Tdev33",iron.FieldParameterSetTypes.VALUES,
    dependentField,iron.FieldVariableTypes.U2,6,iron.FieldParameterSetTypes.VALUES)
constitutiveCellML.FieldMapsCreateFinish()

# Create the CELL models field
constitutiveCellMLModelsField = iron.Field()
constitutiveCellML.ModelsFieldCreateStart(constitutiveCellMLModelsFieldUserNumber,
                                           constitutiveCellMLModelsField)
constitutiveCellMLModelsField.VariableLabelSet(iron.FieldVariableTypes.U,"ConstitutiveModelMap")
constitutiveCellML.ModelsFieldCreateFinish()

# Create the CELL parameters field
constitutiveCellMLParametersField = iron.Field()
constitutiveCellML.ParametersFieldCreateStart(constitutiveCellMLParametersFieldUserNumber,
                                               constitutiveCellMLParametersField)
constitutiveCellMLParametersField.VariableLabelSet(iron.FieldVariableTypes.U,"ConstitutiveParameters")
constitutiveCellML.ParametersFieldCreateFinish()

# Create the CELL intermediate field
constitutiveCellMLIntermediateField = iron.Field()
constitutiveCellML.IntermediateFieldCreateStart(constitutiveCellMLIntermediateFieldUserNumber,
                                                 constitutiveCellMLIntermediateField)
constitutiveCellMLIntermediateField.VariableLabelSet(iron.FieldVariableTypes.U,"ConstitutiveIntermediate")
constitutiveCellML.IntermediateFieldCreateFinish()

# Define the problem
problem = iron.Problem()
problemSpecification = [iron.ProblemClasses.ELASTICITY,
        iron.ProblemTypes.FINITE_ELASTICITY,
        iron.ProblemSubtypes.FINITE_ELASTICITY_WITH_GROWTH_CELLML]
problem.CreateStart(problemUserNumber,problemSpecification)
problem.CreateFinish()

# Create control loops
timeLoop = iron.ControlLoop()
problem.ControlLoopCreateStart()
problem.ControlLoopGet([iron.ControlLoopIdentifiers.NODE],timeLoop)
problem.ControlLoopCreateFinish()

# Create problem solvers
odeIntegrationSolver = iron.Solver()
nonlinearSolver = iron.Solver()
linearSolver = iron.Solver()
cellMLEvaluationSolver = iron.Solver()
problem.SolversCreateStart()
problem.SolverGet([iron.ControlLoopIdentifiers.NODE],1,odeIntegrationSolver)
problem.SolverGet([iron.ControlLoopIdentifiers.NODE],2,nonlinearSolver)
#nonlinearSolver.outputType = iron.SolverOutputTypes.MONITOR
nonlinearSolver.NewtonJacobianCalculationTypeSet(iron.JacobianCalculationTypes.FD)
nonlinearSolver.NewtonCellMLSolverGet(cellMLEvaluationSolver)
nonlinearSolver.NewtonLinearSolverGet(linearSolver)
linearSolver.linearType = iron.LinearSolverTypes.DIRECT
problem.SolversCreateFinish()

# Create nonlinear equations and add equations set to solver equations
nonlinearEquations = iron.SolverEquations()
problem.SolverEquationsCreateStart()
nonlinearSolver.SolverEquationsGet(nonlinearEquations)
nonlinearEquations.sparsityType = iron.SolverEquationsSparsityTypes.SPARSE
nonlinearEquationsSetIndex = nonlinearEquations.EquationsSetAdd(equationsSet)
problem.SolverEquationsCreateFinish()

# Create CellML equations and add growth and constitutive equations to the solvers
growthEquations = iron.CellMLEquations()
constitutiveEquations = iron.CellMLEquations()
problem.CellMLEquationsCreateStart()
odeIntegrationSolver.CellMLEquationsGet(growthEquations)
growthEquationsIndex = growthEquations.CellMLAdd(growthCellML)
cellMLEvaluationSolver.CellMLEquationsGet(constitutiveEquations)
constitutiveEquationsIndex = constitutiveEquations.CellMLAdd(constitutiveCellML)
problem.CellMLEquationsCreateFinish()

# defining the objective to become minimised we need to add the following lines to --- 
# calculate the distance between the coordinates .... 
#

initialLocation = np.zeros((numberOfNodes, 3))
with open("Coords7.txt", "r") as ins:
    arrayOfInitialInputData = []
    for line in ins:
        arrayOfInitialInputData.append(line)
x,y,z = 0.0,0.0,0.0
for i in range (numberOfNodes):
    for j in range (3):
        sample = arrayOfInitialInputData[i*3 + j]
        if (math.fmod(j,3) == 0):
            x = float (sample[0:25])                
        elif (math.fmod(j,3) == 1):
            y = float (sample[0:25])
        elif (math.fmod(j,3) == 2):
            z = float (sample[0:25])
            initialLocation[i,:] = [x,y,z]

finalLocation = np.zeros((numberOfNodes, 3))
with open("Coords8.txt", "r") as ins:
    arrayOfInputData = []
    for line in ins:
        arrayOfInputData.append(line)
x,y,z = 0.0,0.0,0.0
for i in range (numberOfNodes):
    for j in range (3):
        sample = arrayOfInputData[i*3 + j]
        if (math.fmod(j,3) == 0):
            x = float (sample[0:25])                
        elif (math.fmod(j,3) == 1):
            y = float (sample[0:25])
        elif (math.fmod(j,3) == 2):
            z = float (sample[0:25])
            finalLocation[i,:] = [x,y,z]

############# MCC ;  # Fixing x,y,z directions and derivatives - relocating  ====>  applying the displaced values 
boundaryConditions = iron.BoundaryConditions()
nonlinearEquations.BoundaryConditionsCreateStart(boundaryConditions)

#nodelistx = [139,73,74,76,77,81,82,84,85,137,129,121,113,105,97,93]
#nodelisty = [139,73,74,76,77,81,82,84,85,137,129,121,113,105,97,93]
#nodelistz = [65,66,67,68,69,70,71,72,75,83,137,138,139,140,141,142,143,144,93]

nodelistx = [73,74,76,77,81,82,84,85,91,99,107,115,123,131,139]
nodelisty = [73,74,76,77,81,82,84,85,91,99,107,115,123,131,139]
nodelistz = [65,66,67,68,69,70,71,72,137,138,139,140,141,142,143,144]


for nodeNumber in nodelistz:
        # Fix S3 and Z direction
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,3,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,1,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,2,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,3,iron.BoundaryConditionsTypes.FIXED,0.0) 

for nodeNumber in nodelisty:
        # Fix S2 and Y direction
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,2,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,1,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,2,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,3,iron.BoundaryConditionsTypes.FIXED,0.0) 

for nodeNumber in nodelistx:
        # Fix S1 and X direction
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,1,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,1,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,2,iron.BoundaryConditionsTypes.FIXED,0.0)
    boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,3,iron.BoundaryConditionsTypes.FIXED,0.0) 

nonlinearEquations.BoundaryConditionsCreateFinish() 

'''
# Export results
fields = iron.Fields()
fields.CreateRegion(region)
fields.NodesExport("HeartTubeGrowth","FORTRAN")
fields.ElementsExport("HeartTubeGrowth","FORTRAN")
fields.Finalise()
'''
finallengths = np.zeros((numberOfElements, 12))
with open("Lengths8.txt", "r") as ins:
    arrayOfInputData = []
    for line in ins:
        arrayOfInputData.append(line)
L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12= 0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
for i in range (numberOfElements):
    for j in range (12):
        sample = arrayOfInputData[i*12 + j]
        if (math.fmod(j,12) == 0):
            L1 = float (sample[0:25])                
        elif (math.fmod(j,12) == 1):
            L2 = float (sample[0:25])
        elif (math.fmod(j,12) == 2):
            L3 = float (sample[0:25])
        elif (math.fmod(j,12) == 3):
            L4 = float (sample[0:25])
        elif (math.fmod(j,12) == 4):
            L5 = float (sample[0:25])
        elif (math.fmod(j,12) == 5):
            L6 = float (sample[0:25])
        elif (math.fmod(j,12) == 6):
            L7 = float (sample[0:25])
        elif (math.fmod(j,12) == 7):
            L8 = float (sample[0:25])
        elif (math.fmod(j,12) == 8):
            L9 = float (sample[0:25])
        elif (math.fmod(j,12) == 9):
            L10 = float (sample[0:25])
        elif (math.fmod(j,12) == 10):
            L11 = float (sample[0:25])
        elif (math.fmod(j,12) == 11):
            L12 = float (sample[0:25])
            finallengths[i,:] = [L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12]

# defining the growth tensor 
growthTensor = np.zeros((numberOfElements,3))


def copyingFields(fromField, toField):
    for i in range(1,4):
            iron.Field.ParametersToFieldParametersComponentCopy(
                    fromField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,i,
                    toField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,i)
        
def findObjective(optmin,**kwargs):
    cmissobject=kwargs['cmiss']
    geometricField = cmissobject['geometricField']
    dependentField= cmissobject['dependentField']
    numberOfWallNodes= cmissobject['numberOfWallNodes']
    numberOfCircumfrentialNodes= cmissobject['numberOfCircumfrentialNodes']
    g = []
    nodesLocation = np.zeros((numberOfNodes, 3))   
    maxFibreGrowthRate = 0.025
    maxSheetGrowthRate = 0.025
    #maxNormalGrowthRate = 0.030    
    timesteps = int(np.max([np.floor(optmin[0]/maxFibreGrowthRate),np.floor(optmin[1]/maxSheetGrowthRate),np.floor(optmin[2]/maxFibreGrowthRate),np.floor(optmin[3]/maxSheetGrowthRate),
                            np.floor(optmin[4]/maxFibreGrowthRate),np.floor(optmin[5]/maxSheetGrowthRate),np.floor(optmin[6]/maxFibreGrowthRate),np.floor(optmin[7]/maxSheetGrowthRate),
                            np.floor(optmin[8]/maxFibreGrowthRate),np.floor(optmin[9]/maxSheetGrowthRate),np.floor(optmin[10]/maxFibreGrowthRate),np.floor(optmin[11]/maxSheetGrowthRate),
                            np.floor(optmin[12]/maxFibreGrowthRate),np.floor(optmin[13]/maxSheetGrowthRate),np.floor(optmin[14]/maxFibreGrowthRate),np.floor(optmin[15]/maxSheetGrowthRate),
							np.floor(optmin[16]/maxFibreGrowthRate),np.floor(optmin[17]/maxSheetGrowthRate),np.floor(optmin[18]/maxFibreGrowthRate),np.floor(optmin[19]/maxSheetGrowthRate),
                            np.floor(optmin[20]/maxFibreGrowthRate),np.floor(optmin[21]/maxSheetGrowthRate),np.floor(optmin[22]/maxFibreGrowthRate),np.floor(optmin[23]/maxSheetGrowthRate),
                            np.floor(optmin[24]/maxFibreGrowthRate),np.floor(optmin[25]/maxSheetGrowthRate),np.floor(optmin[26]/maxFibreGrowthRate),np.floor(optmin[27]/maxSheetGrowthRate),
							np.floor(optmin[28]/maxFibreGrowthRate),np.floor(optmin[29]/maxSheetGrowthRate),np.floor(optmin[30]/maxFibreGrowthRate),np.floor(optmin[31]/maxSheetGrowthRate),
                            np.floor(optmin[32]/maxFibreGrowthRate),np.floor(optmin[33]/maxSheetGrowthRate),np.floor(optmin[34]/maxFibreGrowthRate),np.floor(optmin[35]/maxSheetGrowthRate),
                            np.floor(optmin[36]/maxFibreGrowthRate),np.floor(optmin[37]/maxSheetGrowthRate),np.floor(optmin[38]/maxFibreGrowthRate),np.floor(optmin[39]/maxSheetGrowthRate),
							np.floor(optmin[40]/maxFibreGrowthRate),np.floor(optmin[41]/maxSheetGrowthRate),np.floor(optmin[42]/maxFibreGrowthRate),np.floor(optmin[43]/maxSheetGrowthRate),
                            np.floor(optmin[44]/maxFibreGrowthRate),np.floor(optmin[45]/maxSheetGrowthRate),np.floor(optmin[46]/maxFibreGrowthRate),np.floor(optmin[47]/maxSheetGrowthRate),
                            np.floor(optmin[48]/maxFibreGrowthRate),np.floor(optmin[49]/maxSheetGrowthRate),np.floor(optmin[50]/maxFibreGrowthRate),np.floor(optmin[51]/maxSheetGrowthRate),
							np.floor(optmin[52]/maxFibreGrowthRate),np.floor(optmin[53]/maxSheetGrowthRate),np.floor(optmin[54]/maxFibreGrowthRate),np.floor(optmin[55]/maxSheetGrowthRate),
                            np.floor(optmin[56]/maxFibreGrowthRate),np.floor(optmin[57]/maxSheetGrowthRate),np.floor(optmin[58]/maxFibreGrowthRate),np.floor(optmin[59]/maxSheetGrowthRate),
                            np.floor(optmin[60]/maxFibreGrowthRate),np.floor(optmin[61]/maxSheetGrowthRate),np.floor(optmin[62]/maxFibreGrowthRate),np.floor(optmin[63]/maxSheetGrowthRate)]))
    for i in range (numberOfElements/2):
        growthTensor[2*i,0] = optmin[2*i]/timesteps
        growthTensor[2*i,1] = optmin[2*i+1]/timesteps
        growthTensor[2*i,2] = 0
    for i in range (numberOfCircumfrentialElements/2):
        for j in range (numberOfLengthElements):
            if (i < numberOfCircumfrentialElements/2-1):
                growthTensor[j*8+2*i+1,:] = (growthTensor[j*8+2*i,:]+ growthTensor[j*8+2*i+2,:])/2 
            else:
                growthTensor[j*8+2*i+1,:] = (growthTensor[j*8+2*i,:]+ growthTensor[j*8+2*i-(numberOfCircumfrentialElements/2-1),:])/2
    
    try:   
        # restarting the fields back 
        copyingFields(originalGeometricField,geometricField)
        copyingFields(originalGeometricField,dependentField)
        #print "optmin", optmin 
        # Initialise the hydrostatic pressure
        iron.Field.ComponentValuesInitialiseDP(dependentField,iron.FieldVariableTypes.U, iron.FieldParameterSetTypes.VALUES,4,pInit)
        for gaussPointNumber in range (1,27+1):
            for elementNumber in range (1,numberOfElements+1):
                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                iron.FieldParameterSetTypes.VALUES,gaussPointNumber,elementNumber,1,growthTensor[elementNumber-1,0])
                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                iron.FieldParameterSetTypes.VALUES,gaussPointNumber,elementNumber,2,growthTensor[elementNumber-1,1])
                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                iron.FieldParameterSetTypes.VALUES,gaussPointNumber,elementNumber,3,growthTensor[elementNumber-1,2])
                growthCellMLParametersField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
                growthCellMLParametersField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
        
        
            # Loop over the time steps
        time = startTime
        timeString = format(time)
        #print "timesteps =" , timesteps
        #print 'rates = ', growthTensor
        for t in range(timesteps):
            timeLoop.TimesSet(time,time+timeIncrement,timeIncrement)
            try:
                problem.Solve()
            except Exception as ex1:
                print 'Exciting due to exception ', str(ex1)
                print 'At time step ',t,' of ',timesteps
                filename = 'convergeFailed'
                fields = iron.Fields()
                fields.CreateRegion(region)
                fields.NodesExport(filename,"FORTRAN")
                fields.ElementsExport(filename,"FORTRAN")
                t =  timesteps
                #sys.exit(0)
            
            # Set geometric field to current deformed geometry
            copyingFields(dependentField,geometricField)
            geometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
            geometricField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
        
            # Reset growth state to 1.0
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,1,1.0)
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,2,1.0)
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,3,1.0)
            time = time+timeIncrement

        #print time, "here we are writing the files"    
        timeString = format(time-1)
        filename = "HeartTubeGrowth_"+timeString
        # Export results
        #fields = iron.Fields()
        #fields.CreateRegion(region)
        #fields.NodesExport(filename,"FORTRAN")
        #fields.ElementsExport(filename,"FORTRAN")
        #fields.Finalise()
                    
        # update the geometric fields to be used to calculate the linelength the 
        geometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
        geometricField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
 
        # there are 12 lines with one brick elements ... therefore, we have just used that number for the 
        lengthIdx   = 0.0
        rmsTotal = 0.0
        for j in range(numberOfElements):
            for i in range(12):
                lengthIdx += (finallengths[j,i] - geometricField.GeometricParametersElementLineLengthGet(j+1, i+1))**2 
                rmsTotal += math.fabs(finallengths[j,i] - geometricField.GeometricParametersElementLineLengthGet(j+1, i+1))/finallengths[j,i]
        rmsLength = rmsTotal/(numberOfElements*12)
        #print "rmsLength =" , rmsLength
        #print "*****************************"
        
        #Geometric field has new values
        for wallNodeIdx in range(1,numberOfWallNodes+1):
            for lengthNodeIdx in range(1,numberOfLengthNodes+1):
                for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
                    nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + \
                            (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                    nodesLocation[nodeNumber-1,0] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,1) 
                    nodesLocation[nodeNumber-1,1] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,2) 
                    nodesLocation[nodeNumber-1,2] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,3)

        sumComponents = 0.0
        outerDistance = 0.0
        for nodeNumber in range (numberOfLengthNodes*numberOfCircumfrentialNodes, numberOfLengthNodes*numberOfCircumfrentialNodes*numberOfWallNodes):
            for index in range (3):
                a = nodesLocation[nodeNumber,index]
                b = finalLocation[nodeNumber,index]
            sumComponents += math.pow(a - b, 2) 
            outerDistance += math.sqrt(sumComponents)
            sumComponents = 0.0
        rmsOuterNodes = outerDistance/(numberOfNodes*0.5) 
        #print "rmsOuterNodes=", rmsOuterNodes
        #print "*****************************"

        sumComponents = 0.0
        innerDistance = 0.0
        for nodeNumber in range (0, numberOfLengthNodes*numberOfCircumfrentialNodes):
            for index in range (3):
                a = nodesLocation[nodeNumber,index]
                b = finalLocation[nodeNumber,index]
            sumComponents += math.pow(a - b, 2) 
            innerDistance += math.sqrt(sumComponents)
            sumComponents = 0.0
        rmsInnerNodes = innerDistance/(numberOfNodes*0.5) 
        #print "rmsInnerNodes=", rmsInnerNodes
        #print "*****************************"
            
        allDistance = 0.0
        #allDistanceNorm = 0.0
        sumComponents = 0.0
        for nodeNumber in range (numberOfLengthNodes*numberOfCircumfrentialNodes, numberOfLengthNodes*numberOfCircumfrentialNodes*numberOfWallNodes):
            for index in range (3):
                a = nodesLocation[nodeNumber,index]
                b = finalLocation[nodeNumber,index]
                sumComponents += math.pow(a - b, 2)
            allDistance += math.sqrt(sumComponents)
            sumComponents = 0
        #allDistance = np.sum(np.linalg.norm(nodesLocation-finalLocation,axis=1))
        #totalObjective   = rmsOuterNodes+rmsLength*20
        totalObjective   = rmsInnerNodes+rmsOuterNodes+rmsLength*20
        #totalObjective   = allDistance + 0.01*lengthIdx
        #totalObjective   = allDistance + 0.1*lengthIdx 
        #totalObjective   = allDistance + 0.2*lengthIdx 
        #print "allDistanceNorm =", allDistanceNorm
        #print "totalDistance", allDistance
        #print "totalObjective", totalObjective
        #print "============================================"
        bestMatchError   = 10e16
        bestMatchError   = min([totalObjective,bestMatchError])
        f=bestMatchError
        fail = 0
        return f,g,fail        
    except Exception, e:
        print optmin,str(e)
        fail = 1
        f = 1e16
    return f,g,fail
        
cmissobject = dict()
cmissobject['geometricField']    =  geometricField 
cmissobject['dependentField']    =  dependentField
cmissobject['numberOfWallNodes'] =  numberOfWallNodes
cmissobject['numberOfCircumfrentialNodes'] =  numberOfCircumfrentialNodes


def getSolutions(solution):
    variables = solution._variables
    consts = [0.0]*64
    for key,var in variables.iteritems():
        consts[key] = var.value
    return consts


def printObjectiveEstimate(solution,keys,filename):
    if not isinstance(solution, list):
        xv  = getSolutions(solution)
    else:
        xv = solution
    findObjective(xv,cmiss=cmissobject)
    nodesLocation = np.zeros((numberOfNodes, 3))
    #Geometric field has new values
    for wallNodeIdx in range(1,numberOfWallNodes+1):
        for lengthNodeIdx in range(1,numberOfLengthNodes+1):
            for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
                nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + \
                        (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes        
                nodesLocation[nodeNumber-1,0] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,1) 
                nodesLocation[nodeNumber-1,1] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,2) 
                nodesLocation[nodeNumber-1,2] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,3)
    lengthIdx   = 0.0
    for j in range (numberOfElements):
        for i in range(12):
            lengthIdx += (finallengths[j,i] - geometricField.GeometricParametersElementLineLengthGet(j+1, i+1))**2 
    # calculating the square of the distances ... we need to calculate the square of all of them ... 
    #  the function math.sqrt should be used for each of the points distance not the whole thing... 
    allDistance = np.sum(np.linalg.norm(nodesLocation-finalLocation,axis=1))
    print "Objective value is ", allDistance + lengthIdx,' Coordinates component ',allDistance,' Length component',  lengthIdx
    for i,k in enumerate(keys):    
        print k,xv[i]

    # Export results
    fields = iron.Fields()
    fields.CreateRegion(region)
    fields.NodesExport(filename,"FORTRAN")
    fields.ElementsExport(filename,"FORTRAN")
    fields.Finalise()

from pyOpt import Optimization
from pyOpt import NSGA2
from pyOpt import SLSQP
from pyOpt import ALPSO
#from pyOpt import NLPQLP    # non-linear programming sequential quadratic programming ...  
from pyOpt import MIDACO    # mized integer distributed Ant Colony Optimization
#from pyOpt import SNOPT
from pyOpt import ALHSO


x0 = [0.01423, 0.0043898, 0.0061094,  0.002544726,  0.00284208, 0.0028, 0.0137680, 0.003685, 1.177e-05, 0.0102569, 1.710937e-05, 0.00229767,0.01423, 0.0043898, 0.0061094,  0.002544726,
      0.00284208, 0.0028, 0.0137680, 0.003685, 1.177e-05, 0.0102569, 1.710937e-05, 0.00229767,0.01423, 0.0043898, 0.0061094,  0.002544726,  0.00284208, 0.0028, 0.0137680, 0.003685, 
      1.177e-05, 0.0102569, 1.710937e-05, 0.00229767, 0.01423, 0.0043898, 0.0061094,  0.002544726,  0.00284208, 0.0028, 0.0137680, 0.003685, 1.177e-05, 0.0102569, 1.710937e-05, 0.00267,
      1.177e-05, 0.0102569, 1.710937e-05, 0.00229767, 0.01423, 0.0043898, 0.0061094,  0.002544726,  0.00284208, 0.0028, 0.0137680, 0.003685, 1.177e-05, 0.01069, 1.710937e-05, 0.002267]
fkeys = ['fibreRate1','sheetRate1','fibreRate2','sheetRate2','fibreRate3','sheetRate3','fibreRate4','sheetRate4','fibreRate5','sheetRate5','fibreRate6','sheetRate6',
         'fibreRate7','sheetRate7','fibreRate8','sheetRate8','fibreRate9','sheetRate9','fibreRate10','sheetRate10','fibreRate11','sheetRate11','fibreRate12','sheetRate12',
		'fibreRate13','sheetRate13','fibreRate14','sheetRate14','fibreRate15','sheetRate15','fibreRate16','sheetRate16','fibreRate17','sheetRate17','fibreRate18','sheetRate18',
        'fibreRate19','sheetRate19','fibreRate20','sheetRate20','fibreRate21','sheetRate21','fibreRate22','sheetRate22','fibreRate23','sheetRate23','fibreRate24','sheetRate24',
        'fibreRate25','sheetRate25','fibreRate26','sheetRate26','fibreRate27','sheetRate27','fibreRate28','sheetRate28',
        'fibreRate29','sheetRate29','fibreRate30','sheetRate30','fibreRate31','sheetRate31','fibreRate32','sheetRate32']

doGlobalSearch = False
doSwarmIntelligence = True
doMIDACO = False
doNonlinearSearch = False
doSparseNonlinear = False
doHarmonySearch = False


#print '************************************* Initial **********************************'
#printObjectiveEstimate(x0,fkeys,'BlockForInitialCondition')
#print '************************************* Initial **********************************'

bnds = [(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),
        (0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099),(0.0,0.099)]


opt_prob = Optimization('GrowthOptimise',findObjective)

for i,v in enumerate(bnds):
    opt_prob.addVar(fkeys[i],'c',lower=v[0],upper=v[1],value=x0[i])
opt_prob.addObj('f')
print opt_prob

# Global Optimization
if doGlobalSearch:
    nsga2 = NSGA2()
    nsga2.setOption('maxGen', 20)
    nsga2.setOption('PopSize', 40)
    nsga2(opt_prob,cmiss=cmissobject)
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)
    
elif doSwarmIntelligence: 
    augmentedLagrnagePSO = ALPSO()
    augmentedLagrnagePSO.setOption('SwarmSize',10)
    augmentedLagrnagePSO(opt_prob,cmiss=cmissobject)      
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)
    
elif doHarmonySearch:
    augmentedLagrnageHSO = ALHSO()
    augmentedLagrnageHSO.setOption('hms',20)
    augmentedLagrnageHSO(opt_prob,cmiss=cmissobject)      
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)  

elif doSparseNonlinear: 
    sparseNonlinear = SNOPT()
    sparseNonlinear(opt_prob,cmiss=cmissobject)      
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)
    
elif doMIDACO:
    # Solve Problem (No-Parallelization)
    midaco_none = MIDACO()
    #midaco_none.setOption('IPRINT',-1)
    #midaco_none.setOption('MAXEVAL',50000)
    midaco_none(opt_prob,cmiss=cmissobject)
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)
    
   
elif doNonlinearSearch:
    # Solve Problem (No-Parallelization)
    nlpqlp_none = NLPQLP()
    nlpqlp_none.setOption('IPRINT',0)
    nlpqlp_none(opt_prob)
    print opt_prob.solution(0)
     
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)

else: 
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob,sens_type='FD',cmiss=cmissobject)
    solution = opt_prob.solution(0)  
    
    
#-----------------------------------------------------------------
print '************************************* Solution **********************************'
printObjectiveEstimate(solution,fkeys,'SolutionBlock')
print '************************************* Solution **********************************'

end = time.time()
print "the time took for this run  = ", end - start  
iron.Finalise()

