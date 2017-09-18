#> Main script
# Add Python bindings directory to PATH
import sys, os
import math
import numpy as np
import time 

# in order to measure the time we use time module ....  
start = time.time()

# Intialise OpenCMISS
from opencmiss.iron import iron

# Set problem parameters
growthModel = 1 # Type of growth. 1 - volumetric; 2 - stress based; 3 - strain based.
isotropic = True # True if the problem is isotropic, False if the problem is anisotropic
homogeneous = False # True if the growth rates are homogeneous, False if the problem is heterogeneous
useFibres = True # True if fibres are used for anisotropic problems
heterogeneousFibres = False # True if the fibre angles vary in space, False if not.
fixBottomRing = True # True if the bottom ring of nodes is fixed, False if not
fixTopRing = False # True if the top ring of nodes is fixed, False if not

# Tube geometry
length = 2.0 # The length of the tube
innerRadius = 0.75 # The inner radius of the tube
outerRadius = 2.0 # The outer radius of the tube

numberOfLengthElements=1 # Number of elements along the length of the tube
numberOfCircumfrentialElementsPerQuarter=1 # Number of elements in the circumfrential direction in one quarter of the tube
numberOfWallElements=1 # Number of elements through the wall of the tube

# Hydrostatic pressure
pInit = -8.0 # The initial hydrostatic pressure

# Fibre angle
#fibreAngle = math.pi/2.0 # The fibre angle wrt the for anisotropic fibres
fibreAngle = 0.0 # The fibre angle wrt the for anisotropic fibres

# Times
startTime = 0.0 # The start time for the growth simulation
stopTime1 = 10.0 # The stop time for the growth simulation
timeIncrement = 1.0 # The time increment for the growth simulation

# Number of Gauss points used
numberOfGaussXi = 3

numberOfCircumfrentialElements = numberOfCircumfrentialElementsPerQuarter
numberOfLengthNodes = numberOfLengthElements+1
numberOfCircumfrentialNodes = numberOfCircumfrentialElements+1
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
lambdaFieldUserNumber = 12
fittingEquationsSetUserNumber = 13
fittingEquationsSetFieldUserNumber = 14
fittingDependentFieldUserNumber = 15
fittingIndependentFieldUserNumber = 16
fittingMaterialsFieldUserNumber = 17
fittingProblemUserNumber = 18

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
numberOfNodes = (numberOfCircumfrentialElements+1)*(numberOfLengthElements+1)*(numberOfWallElements+1)
numberOfElements = numberOfCircumfrentialElements*numberOfLengthElements*numberOfWallElements

# Define nodes for the mesh
nodes = iron.Nodes()
nodes.CreateStart(region,numberOfNodes)
nodes.CreateFinish()
mesh = iron.Mesh()
# Create the mesh. The mesh will have two components - 1. tricubic Hermite elements; 2. trilinear Lagrange elements
mesh.CreateStart(meshUserNumber,region,3)
mesh.NumberOfComponentsSet(2)
mesh.NumberOfElementsSet(numberOfElements)

tricubicHermiteElements = iron.MeshElements()
tricubicHermiteElements.CreateStart(mesh,1,tricubicHermiteBasis)
trilinearLagrangeElements = iron.MeshElements()
trilinearLagrangeElements.CreateStart(mesh,2,trilinearLagrangeBasis)

elementNumber = 0
for wallElementIdx in range(1,numberOfWallElements+1):
    for lengthElementIdx in range(1,numberOfLengthElements+1):
        for circumfrentialElementIdx in range(1,numberOfCircumfrentialElements+1):
            elementNumber = elementNumber + 1
            localNode1 = circumfrentialElementIdx + (lengthElementIdx-1)*numberOfCircumfrentialNodes + \
                (wallElementIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
            localNode2 = localNode1 + 1
            localNode3 = localNode1 + numberOfCircumfrentialNodes
            localNode4 = localNode2 + numberOfCircumfrentialNodes
            localNode5 = localNode1 + numberOfCircumfrentialNodes*numberOfLengthNodes
            localNode6 = localNode2 + numberOfCircumfrentialNodes*numberOfLengthNodes
            localNode7 = localNode3 + numberOfCircumfrentialNodes*numberOfLengthNodes
            localNode8 = localNode4 + numberOfCircumfrentialNodes*numberOfLengthNodes
            localNodes = [localNode1,localNode2,localNode3,localNode4,localNode5,localNode6,localNode7,localNode8]
            print "localNodes", localNodes
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
originalGeometricField.VariableLabelSet(iron.FieldVariableTypes.U,"Geometry")
# Set the domain to be used by the field components to be tricubic Hermite
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,1)
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,1)
originalGeometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,1)
# Set the scaling type
originalGeometricField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
# Finish creating the field
originalGeometricField.CreateFinish()

# Create the geometric field
for wallNodeIdx in range(1,numberOfWallNodes+1):
    for lengthNodeIdx in range(1,numberOfLengthNodes+1):
        for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
            nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + \
                (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
            print nodeNumber
            radius = innerRadius + (outerRadius - innerRadius)*float(wallNodeIdx-1)
            theta = float(circumfrentialNodeIdx-1)*0.5*math.pi
            x = radius*math.cos(theta)
            y = radius*math.sin(theta)
            xtangent = -math.sin(theta)
            ytangent = math.cos(theta)
            xnormal = math.cos(theta)
            ynormal = math.sin(theta)
            z = float(lengthNodeIdx-1)*length
            for field in [geometricField, originalGeometricField]:
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,1,x)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,2,y)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,3,z)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,1,xtangent)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,2,ytangent)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,3,0.0)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,1,0.0)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,2,0.0)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,3,1.0)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,1,xnormal)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,2,ynormal)
                field.ParameterSetUpdateNodeDP(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,
                                                    1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,3,0.0)
# Update the geometric field
geometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
geometricField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
originalGeometricField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES)
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

# Export results
fields = iron.Fields()
fields.CreateRegion(region)
fields.NodesExport("HeartTubeGrowth","FORTRAN")
fields.ElementsExport("HeartTubeGrowth","FORTRAN")
fields.Finalise()

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

# Prescribe boundary conditions (absolute nodal parameters)
boundaryConditions = iron.BoundaryConditions()
nonlinearEquations.BoundaryConditionsCreateStart(boundaryConditions)

for lengthNodeIdx in range(1,3):
    if (lengthNodeIdx == 1 and fixBottomRing) or (lengthNodeIdx == 2 and fixTopRing):
        for wallNodeIdx in range(1,numberOfWallNodes+1):
            for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
                nodeNumber = circumfrentialNodeIdx + (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfCircumfrentialNodes
                # Fix x direction
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix y direction
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix z direction
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.NO_GLOBAL_DERIV,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix S1 (circumfrential) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix S2 (length) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix S3 (wall) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
#there are some more boundary conditions we want to apply to fix the derivative
# some of them are as follows ... 
# we have fixed derivatives of the top surface in a single block 
                nodeNumber = circumfrentialNodeIdx + (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfCircumfrentialNodes + 2
                # Fix S1 (circumfrential) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S1,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix S2 (length) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S2,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                # Fix S3 (wall) direction derivatives
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,1,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,2,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
                boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,
                                           1,iron.GlobalDerivativeConstants.GLOBAL_DERIV_S3,nodeNumber,3,
                                           iron.BoundaryConditionsTypes.FIXED,0.0)
nonlinearEquations.BoundaryConditionsCreateFinish()

fields.Finalise()
print "fields finalized"
# defining the objective to become minimised we need to add the following lines to --- 
# calculate the distance between the coordinates .... 
#
#    OBJECTIVE  FUNCTION =   A(coords)  +   B(Lengths)   +  C(Areas)   
#   
# the third part is not calculated yet ... 
#  for now we have considered the coords and the lengths 

finalLocation = np.zeros((numberOfNodes, 3))
#finalderivatives=np.zeros((numberOfNodes,9))
#nodesLocation = np.zeros((numberOfNodes, 3))
#derivates = np.zeros((numberOfNodes, 9))
finalLocation [0,:] = [  7.50000000e-01,   0.00000000e+00 ,  0.00000000e+00]
finalLocation [1,:] = [  4.59242550e-17  , 7.50000000e-01,   0.00000000e+00]
finalLocation [2,:] = [  7.72635517e-01,  -6.83332508e-02,   2.36728722e+00]
finalLocation [3,:] = [ -6.83332513e-02 ,  7.72635518e-01  , 2.36728722e+00]
finalLocation [4,:] = [  2.00000000e+00,   0.00000000e+00 ,  0.00000000e+00]
finalLocation [5,:] = [  1.22464680e-16  , 2.00000000e+00 ,  0.00000000e+00]
finalLocation [6,:] = [  2.03707575e+00 , -9.05928391e-02 ,  2.39792288e+00]
finalLocation [7,:] = [ -9.05928389e-02,   2.03707575e+00 ,  2.39792288e+00]

finallengths = [1.28956803, 1.26633859, 3.22699772, 3.2447477, 2.36074892, 2.36074892,
                2.39024312, 2.39024312, 1.24452437, 1.24452436, 1.2571413, 1.2571413]

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
    try:
        fibreRate, sheetRate, normalRate = optmin[0],optmin[1],optmin[2]
        # restarting the fields back
        copyingFields(originalGeometricField,geometricField)
        copyingFields(originalGeometricField,dependentField)
        
        # Initialise the hydrostatic pressure
        iron.Field.ComponentValuesInitialiseDP(dependentField,iron.FieldVariableTypes.U,
                                            iron.FieldParameterSetTypes.VALUES,4,pInit)
        for wallElementIdx in range(1,numberOfWallElements+1):
            for lengthElementIdx in range(1,numberOfLengthElements+1):
                for circumfrentialElementIdx in range(1,numberOfCircumfrentialElements+1):
                    elementNumber = circumfrentialElementIdx + (lengthElementIdx-1)*numberOfCircumfrentialElements + \
                                    (wallElementIdx-1)*numberOfCircumfrentialElements*numberOfLengthElements
                    for xiIdx3 in range(1,numberOfGaussXi+1):
                        for xiIdx2 in range(1,numberOfGaussXi+1):
                            for xiIdx1 in range(1,numberOfGaussXi+1):
                                gaussPointNumber = xiIdx1 + (xiIdx2-1)*numberOfGaussXi + (xiIdx3-1)*numberOfGaussXi*numberOfGaussXi
                                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                                                                           iron.FieldParameterSetTypes.VALUES,
                                                                                           gaussPointNumber,elementNumber,1,
                                                                                           fibreRate)
                                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                                                                           iron.FieldParameterSetTypes.VALUES,
                                                                                           gaussPointNumber,elementNumber,2,
                                                                                           sheetRate)
                                growthCellMLParametersField.ParameterSetUpdateGaussPointDP(iron.FieldVariableTypes.U,
                                                                                           iron.FieldParameterSetTypes.VALUES,
                                                                                           gaussPointNumber,elementNumber,3,
                                                                                           normalRate)
                                growthCellMLParametersField.ParameterSetUpdateStart(iron.FieldVariableTypes.U,
                                                                                    iron.FieldParameterSetTypes.VALUES)
                                growthCellMLParametersField.ParameterSetUpdateFinish(iron.FieldVariableTypes.U,
                                                                                     iron.FieldParameterSetTypes.VALUES)

        # Loop over the time steps
        time = startTime
        timeString = format(time)
        while time<=stopTime1:
            timeLoop.TimesSet(time,time+timeIncrement,timeIncrement)
            problem.Solve()
            # Set geometric field to current deformed geometry
            copyingFields(dependentField,geometricField)
            # Reset growth state to 1.0
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,1,1.0)
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,2,1.0)
            growthCellMLStateField.ComponentValuesInitialiseDP(iron.FieldVariableTypes.U,
                                                               iron.FieldParameterSetTypes.VALUES,3,1.0)

            time = time+timeIncrement
        #Geometric field has new values
        for wallNodeIdx in range(1,numberOfWallNodes+1):
            for lengthNodeIdx in range(1,numberOfLengthNodes+1):
                for circumfrentialNodeIdx in range(1,numberOfCircumfrentialNodes+1):
                    nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                    
                    nodesLocation[nodeNumber-1,0] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,1) 
                    nodesLocation[nodeNumber-1,1] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,2) 
                    nodesLocation[nodeNumber-1,2] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,3)
        # there are 12 lines with one brick elements ... therefore, we have just used that number for the 
        lengthIdx   = 0.0
        for i in range(12):
            lengthIdx += (finallengths[i] - geometricField.GeometricParametersElementLineLengthGet(1, i+1))**2         
        # calculating the square of the distances ... we need to calculate the square of all of them ... 
        #  the function math.sqrt should be used for each of the points distance not the whole thing... 

        allDistance = np.sum(np.linalg.norm(nodesLocation-finalLocation,axis=1))

        totalObjective   = allDistance + lengthIdx 
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
    '''
    Get the variable values and computes Re and Rct for that value
    '''
    variables = solution._variables
    consts = [0.0]*3
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
                nodeNumber = circumfrentialNodeIdx + (lengthNodeIdx-1)*numberOfCircumfrentialNodes + (wallNodeIdx-1)*numberOfCircumfrentialNodes*numberOfLengthNodes
                     
                nodesLocation[nodeNumber-1,0] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,1) 
                nodesLocation[nodeNumber-1,1] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,2) 
                nodesLocation[nodeNumber-1,2] = geometricField.ParameterSetGetNodeDP(iron.FieldVariableTypes.U, 
                                                            iron.FieldParameterSetTypes.VALUES, 1,1,nodeNumber,3)
        # there are 12 lines with one brick elements ... therefore, we have just used that number for the 
    lengthIdx   = 0.0
    for i in range(12):
        lengthIdx += (finallengths[i] - geometricField.GeometricParametersElementLineLengthGet(1, i+1))**2     
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
x0 = [0.002, 0.012, 0.0002]
fkeys = ['fibreRate','sheetRate','normalRate']
doGlobalSearch = False

print '************************************* Initial **********************************'
printObjectiveEstimate(x0,fkeys,'BlockForInitialCondition')
print '************************************* Initial **********************************'


bnds = [(2e-4,2e-2),(5e-3,5e-2),(1e-5,1e-3)]
opt_prob = Optimization('GrowthOptimise',findObjective)

for i,v in enumerate(bnds):
    opt_prob.addVar(fkeys[i],'c',lower=v[0],upper=v[1],value=x0[i])
opt_prob.addObj('f')
print opt_prob    

# Global Optimization
if doGlobalSearch:
    nsga2 = NSGA2()
    nsga2(opt_prob,cmiss=cmissobject)
    print opt_prob.solution(0)
    # Local Optimization Refinement
    slsqp = SLSQP()
    slsqp(opt_prob.solution(0),sens_type='FD',cmiss=cmissobject)
    print opt_prob.solution(0).solution(0)
    solution = opt_prob.solution(0).solution(0)
else: 
    # Local Optimization Refinement
    #slsqp = SLSQP()
    slsqp = ALPSO(SwarmSize=20)
    
    slsqp(opt_prob,cmiss=cmissobject)
    #slsqp(opt_prob,sens_type='FD',cmiss=cmissobject)
    
    solution = opt_prob.solution(0)  
#-----------------------------------------------------------------
print '************************************* Solution **********************************'
printObjectiveEstimate(solution,fkeys,'SolutionBlock')
print '************************************* Solution **********************************'

end = time.time()
print "the time tkaen for the code  = ", end - start  


iron.Finalise()
