from abaqus import *
from abaqusConstants import *
from caeModules import *
from myAssembly3p import MyAssembly
from steelMaterial import SteelMaterial
from column3p import Column
from partitionColumn3p import PartitionColumn
from meshColumn3p import _getEdgesParalleToZ
from meshColumn3p import MeshColumn
from itube import Itube


def _Sketch_middle_edge(model_name, sketch_name, height1, width1, height2, width2, radius1, thickness):
    sketch = mdb.models[model_name].sketches[sketch_name]
    vertices = ((0, 0), (0, height1), (width1 - width2, height1), (width1 - width2, height1 - height2),
                (width1, height1 - height2), (width1, 0), (0, 0))
    lines = []
    for i in range(len(vertices) - 1):
        lines.append(sketch.Line(point1=vertices[i], point2=vertices[i + 1]))

    lines.append(sketch.FilletByRadius(radius=radius1, curve1=lines[0], nearPoint1=(0, radius1), curve2=lines[5],
                          nearPoint2=(radius1, 0)))
    lines.append(sketch.FilletByRadius(radius=radius1, curve1=lines[0], nearPoint1=(0, height1 - radius1), curve2=lines[1],
                          nearPoint2=(radius1, height1)))
    lines.append(sketch.FilletByRadius(radius=radius1, curve1=lines[4], nearPoint1=(width1, radius1), curve2=lines[5],
                          nearPoint2=(width1 - radius1, 0)))
    lines.append(sketch.FilletByRadius(radius=radius1 - thickness, curve1=lines[2],
                          nearPoint1=(width1 - width2, height1 - height2 + radius1 - thickness),
                          curve2=lines[3], nearPoint2=(width1 - width2 + radius1 - thickness, height1 - height2)))
    #sketch.offset(distance=0.5*thickness, objectList=lines, side=LEFT)
    #sketch.delete(objectList=lines)
    return sketch

def _getFacesParalleToZ(z0, z1, column:Column):
    p = mdb.models[column.model_name].parts[column.part_name]
    faces = p.faces
    pickedFaces = faces.getByBoundingBox(xMin=0, xMax=column.width1,
                                           yMin=0, yMax=column.height1,
                                           zMin=z0, zMax=z1)
    deltaZ = 0.1
    pickedFacesZ0 = faces.getByBoundingBox(xMin=0, xMax=column.width1,
                                             yMin=0, yMax=column.height1,
                                             zMin=z0 - deltaZ, zMax=z0 + deltaZ)
    pickedFacesZ1 = faces.getByBoundingBox(xMin=0, xMax=column.width1,
                                             yMin=0, yMax=column.height1,
                                             zMin=z1 - deltaZ, zMax=z1 + deltaZ)
    set_all = {edge.index for edge in pickedFaces}
    set_0 = {edge.index for edge in pickedFacesZ0}
    set_1 = {edge.index for edge in pickedFacesZ1}
    set_need = set_all - set_0 - set_1
    f = p.faces
    return part.FaceArray([f[i] for i in set_need])

def column_shell(myAssembly:MyAssembly, steelMaterial:SteelMaterial, column:Column, partitionColumn:PartitionColumn,  meshColumn:MeshColumn, itube:Itube):
    p = mdb.models[column.model_name].parts[column.part_name]

    e, d = p.edges, p.datums
    pos = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + 100
    if partitionColumn.mesh_dense_extend_length:
        pos = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + partitionColumn.mesh_dense_extend_length
    datumz = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=pos)
    skt_edge = p.edges.findAt(coordinates=(column.width1, column.radius1 + 0.1, 0))
    t = p.MakeSketchTransform(sketchPlane=d[datumz.id], sketchUpEdge=skt_edge, sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0, 0, pos))
    s = mdb.models[column.model_name].ConstrainedSketch(name='__profile__', sheetSize=1600, gridSpacing=40, transform=t)
    p = mdb.models[column.model_name].parts[column.part_name]
    cut_depth = column.length - pos
    s.rectangle(point1=(0, 0), point2=(column.width1, column.height1))
    p.CutExtrude(sketchPlane=d[datumz.id], sketchUpEdge=skt_edge, sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, depth=cut_depth, flipExtrudeDirection=ON)
    del mdb.models[column.model_name].sketches['__profile__']

#************************************************************

    p = mdb.models[column.model_name].parts[column.part_name]

    f, e, d = p.faces, p.edges, p.datums
    skt_edge = p.edges.findAt(coordinates=(column.width1, column.radius1 + 0.1, 0))
    t = p.MakeSketchTransform(sketchPlane=d[datumz.id], sketchUpEdge=skt_edge, sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0, 0, pos))
    s1 = mdb.models[column.model_name].ConstrainedSketch(name='__profile__', sheetSize=1600, gridSpacing=40, transform=t)
    _Sketch_middle_edge(column.model_name, '__profile__', column.height1, column.width1, column.height2,
                        column.width2, column.radius1, column.thickness)

    p = mdb.models[column.model_name].parts[column.part_name]

    d = p.datums
    p.ShellExtrude(sketchPlane=d[datumz.id], sketchUpEdge=skt_edge, sketchPlaneSide=SIDE1,
                   sketchOrientation=RIGHT, sketch=s1, depth=cut_depth,
                   flipExtrudeDirection=OFF, keepInternalBoundaries=ON)
    del mdb.models[column.model_name].sketches['__profile__']

    mdb.models[column.model_name].HomogeneousShellSection(name='steel-column-shell',
                                                              preIntegrate=OFF, material=steelMaterial.name,
                                                              thicknessType=UNIFORM,
                                                              thickness=column.thickness, thicknessField='',
                                                              nodalThicknessField='',
                                                              idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT,
                                                              thicknessModulus=None, temperature=GRADIENT,
                                                              useDensity=OFF,
                                                              integrationRule=SIMPSON, numIntPts=5)
    p = mdb.models[column.model_name].parts[column.part_name]
    faces = _getFacesParalleToZ(pos, column.length, column)
    region = regionToolset.Region(faces=faces)
    p.SectionAssignment(region=region, sectionName='steel-column-shell',
                        offset=0.0, offsetType=BOTTOM_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)
    p = mdb.models[column.model_name].parts[column.part_name]

    pickedEdges = _getEdgesParalleToZ(pos, pos + cut_depth, column)

    p.seedEdgeBySize(edges=pickedEdges, size=meshColumn.hollow_length_size,
                     deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

    #*****************************************

    p = mdb.models[column.model_name].parts[column.part_name]
    seal_pad_pos = itube.length
    p.features['Datum plane-1'].setValues(offset=column.length - seal_pad_pos)
    p.regenerate()
    skt_edge = p.edges.findAt(coordinates=(column.width1, column.radius1 + 0.1, 0))
    e, d = p.edges, p.datums
    t = p.MakeSketchTransform(sketchPlane=d[2], sketchUpEdge=skt_edge,
                              sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0, 0, column.length - seal_pad_pos))
    s = mdb.models[column.model_name].ConstrainedSketch(name='__profile__', sheetSize=1800, gridSpacing=40, transform=t)
    _Sketch_middle_edge(column.model_name, '__profile__', column.height1, column.width1, column.height2, column.width2, column.radius1, column.thickness)
    e1, d2 = p.edges, p.datums
    skt_edge = p.edges.findAt(coordinates=(column.width1, column.radius1 + 0.1, 0))
    p.Shell(sketchPlane=d2[2], sketchUpEdge=skt_edge, sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s)
    del mdb.models[column.model_name].sketches['__profile__']

    a = mdb.models[myAssembly.model_name].rootAssembly
    a.regenerate()

    mdb.models[column.model_name].HomogeneousShellSection(name='steel-column-pad-shell',
                                                          preIntegrate=OFF, material=steelMaterial.name,
                                                          thicknessType=UNIFORM,
                                                          thickness=4, thicknessField='',
                                                          nodalThicknessField='',
                                                          idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT,
                                                          thicknessModulus=None, temperature=GRADIENT,
                                                          useDensity=OFF,
                                                          integrationRule=SIMPSON, numIntPts=5)
    p = mdb.models[column.model_name].parts[column.part_name]

    faces = p.faces.getByBoundingBox(xMin=0, xMax=column.width1,
                                     yMin=0, yMax=column.height1,
                                     zMin=column.length - seal_pad_pos - 0.1,
                                     zMax=column.length - seal_pad_pos + 0.1)

    region = regionToolset.Region(faces=faces)
    p.SectionAssignment(region=region, sectionName='steel-column-pad-shell',
                        offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)

    p.generateMesh()