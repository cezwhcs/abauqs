from abaqus import *
from abaqusConstants import *
from caeModules import *
from odbAccess import *

def get_LoadPoint_U2_RF2(odb_name, point_name):
    odb = openOdb(path=odb_name)
    step = odb.steps['step-1']
    frames = step.frames
    node = odb.rootAssembly.nodeSets[point_name]
    odb_name0 = odb_name.removesuffix('.odb')
    dispFile = open(f'{odb_name0}_u2-rf2.dat', 'w')
    for i, frame in enumerate(frames):
        displacements = frame.fieldOutputs['U']
        reaction = frame.fieldOutputs['RF']
        nodeDisplacements = displacements.getSubset(region=node)
        nodeReaction = reaction.getSubset(region=node)
        disp = nodeDisplacements.values[0].data[1]
        force = nodeReaction.values[0].data[1]
        dispFile.write('%.1f   %.0f\n' % (-disp, -2 * force / 1000))

    dispFile.close()
    #odb.close()

for i in {2, 3, 5}:
    get_LoadPoint_U2_RF2(odb_name=f"{i}w3p-mander4.odb", point_name='POINT-LOAD')
    get_LoadPoint_U2_RF2(odb_name=f"{i}w4p-mander4.odb", point_name='POINT-LOAD')
#get_LoadPoint_U2_RF2(odb_name=session.viewports['Viewport: 1'].odbDisplay.name, point_name='POINT-LOAD')