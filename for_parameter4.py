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

def __redefine_boundary_condition(myAssembly:MyAssembly, myBoundary:MyBoundary, column:Column, myStep:MyStep, myInteraction:MyInteraction, U2, axis_m=False, force_ratio=0):
    del mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.symmetry_boundary_name]
    del mdb.models[myAssembly.model_name].constraints[myInteraction.load_constraint_name]
    del mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.load_boundary_name]
    del mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.load_point_name]

    a = mdb.models[myAssembly.model_name].rootAssembly
    region = a.sets[myAssembly.sets.symmetry_plane_name]
    mdb.models[myAssembly.model_name].DisplacementBC(name=myBoundary.symmetry_boundary_name,
                                         createStepName='Initial', region=region, u1=SET, u2=SET, u3=SET,
                                         ur1=SET, ur2=SET, ur3=SET, amplitude=SET, distributionType=UNIFORM,
                                         fieldName='', localCsys=None)
    mdb.models[myAssembly.model_name].boundaryConditions[myBoundary.support_boundary_name].setValuesInStep(
        stepName=myStep.step_name, u2=U2)

    e = a.instances[myAssembly.column_name].edges
    if axis_m:
        a.features['RP-1'].setValues(xValue=0.0, yValue=-71.3 * 2 **0.5)
        a.regenerate()
        max_length = (2 * column.width1 * column.height1)**0.5 + 10
        delta = 0.1
        z_position = column.length
        support_edges = e.getByBoundingBox(xMin=-max_length, xMax=max_length,
                                              yMin=-max_length, yMax=0,
                                              zMin=z_position - delta, zMax=z_position + delta)
        a.Surface(side1Edges=support_edges, name=myAssembly.sets.support_plane_name)
    else:
        a.features['RP-1'].setValues(xValue=71.3, yValue=71.3)
        a.regenerate()
        delta = 0.1
        z_position = column.length
        support_edges = e.getByBoundingBox(xMin=0, xMax=column.width1,
                                           yMin=0, yMax=column.height1,
                                           zMin=z_position - delta, zMax=z_position + delta)
        a.Surface(side1Edges=support_edges, name=myAssembly.sets.support_plane_name)

    if force_ratio != 0:
        a = mdb.models[myAssembly.model_name].rootAssembly
        region = a.sets[myAssembly.sets.support_point_name]
        yield_force = 1927350
        mdb.models[myAssembly.model_name].ConcentratedForce(name='Load-1', createStepName=myStep.step_name,
                                                region=region, cf3=-force_ratio*yield_force, distributionType=UNIFORM, field='',
                                                localCsys=None, follower=OFF)

    regionDef = mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.support_point_name]
    mdb.models[myAssembly.model_name].historyOutputRequests['H-Output-1'].setValues(
        region=regionDef)

    mdb.models[myAssembly.model_name].StaticStep(name='Step-0', previous='Initial',
                                     maxNumInc=10000, initialInc=0.1, minInc=1e-10, maxInc=0.1, nlgeom=ON)
    mdb.models[myAssembly.model_name].loads['Load-1'].move(myStep.step_name, 'Step-0')
    mdb.models[myAssembly.model_name].fieldOutputRequests['F-Output-1'].move(myStep.step_name, 'Step-0')


def for_paramerter4_run(myAssembly:MyAssembly, myBoundary:MyBoundary, column:Column, myStep:MyStep, myInteraction:MyInteraction, U2 = 70, axis_m=False, force_ratio=0):
    if axis_m:
        __rotate_assembly(myAssembly)
    __delete_arcshell(myAssembly)
    __redefine_boundary_condition(myAssembly, myBoundary, column, myStep, myInteraction, U2, axis_m, force_ratio)