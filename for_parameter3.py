from abaqus import *
from abaqusConstants import *
from caeModules import *
from myAssembly3p import MyAssembly
from myBoundary3p import MyBoundary
from myStep import MyStep
from myInteraction3p import MyInteraction
from column3p import Column

def __rotate_assembly(myAssembly:MyAssembly):
    a = mdb.models[myAssembly.model_name].rootAssembly
    a.rotate(instanceList=(myAssembly.column_name, myAssembly.concrete_name, myAssembly.itube_name),
             axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 10.0), angle=225.0)
def __delete_arcshell(myAssembly:MyAssembly):
    a = mdb.models[myAssembly.model_name].rootAssembly
    del a.features[myAssembly.arcshell_name]

def __redefine_boundary_condition(myAssembly:MyAssembly, myBoundary:MyBoundary, column:Column, myStep:MyStep, myInteraction:MyInteraction, U2):
    del mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.symmetry_boundary_name]

    a = mdb.models[myAssembly.model_name].rootAssembly
    region = a.sets[myAssembly.sets.symmetry_plane_name]
    mdb.models[myAssembly.model_name].DisplacementBC(name=myBoundary.symmetry_boundary_name,
                                         createStepName='Initial', region=region, u1=SET, u2=SET, u3=SET,
                                         ur1=SET, ur2=SET, ur3=SET, amplitude=SET, distributionType=UNIFORM,
                                         fieldName='', localCsys=None)

    a = mdb.models[myAssembly.model_name].rootAssembly
    a.features['RP-1'].setValues(xValue=0.0, yValue=-column.height1 * 2**-0.5)
    a.regenerate()

    a = mdb.models[myAssembly.model_name].rootAssembly
    s = a.instances[myAssembly.column_name].faces
    max_projection_length = column.height1 * 2**0.5
    delta = 0.1
    z_position = column.length - column.pad_pos + column.pad_thickness * 0.5
    support_faces = s.getByBoundingBox(xMin=-max_projection_length * 0.5, xMax=max_projection_length * 0.5,
                                          yMin=-max_projection_length, yMax=0,
                                          zMin=z_position - delta, zMax=z_position + delta)
    a.Surface(side1Faces=support_faces, name=myAssembly.sets.support_plane_name)

    del mdb.models[myAssembly.model_name].constraints[myInteraction.load_constraint_name]

    del mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.load_boundary_name]
    mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.support_boundary_name].setValuesInStep(
        stepName=myStep.step_name, u2=U2)

    regionDef = mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.support_point_name]
    mdb.models[myAssembly.model_name].historyOutputRequests['H-Output-1'].setValues(
        region=regionDef)
    del mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.load_point_name]


def for_paramerter3_run(myAssembly:MyAssembly, myBoundary:MyBoundary, column:Column, myStep:MyStep, myInteraction:MyInteraction, U2 = 70):
    __rotate_assembly(myAssembly)
    __delete_arcshell(myAssembly)
    __redefine_boundary_condition(myAssembly, myBoundary, column, myStep, myInteraction, U2)