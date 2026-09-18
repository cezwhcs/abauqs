from abaqus import *
from abaqusConstants import *
from caeModules import *

from concrete import Concrete
from column3p import Column
from itube import Itube
from partitionConcrete import PartitionConcrete

class MeshConcrete:
    def __init__(self, itube:Itube, column:Column,  concrete:Concrete, partitionConcrete:PartitionConcrete,
                 global_size=5, innner_size=10,
                 radius1_outside_elements=2, radius1_inside_elements=5, radius2_elements=3,
                 shearkey_elements=6, edge1_elements = 3, grout_layer_elements=0):
        self.outter_size = global_size
        self.innner_size = innner_size
        self.radius1_outside_elements = radius1_outside_elements
        self.radius1_inside_elements = radius1_inside_elements
        self.radius2_elements = radius2_elements
        self.shearkey_elements = int(shearkey_elements * 0.5)
        self.edge1_elements = edge1_elements
        self.grout_layer_elements = grout_layer_elements
        self.more_partition = partitionConcrete.more_partition
        self.__setElementType(itube, column, concrete)
        self.__setSeed(itube, column, concrete)
        self.__generateMesh(itube, column, concrete)

    def __setElementType(self, itube:Itube, column:Column, concrete:Concrete):
        p = mdb.models[concrete.model_name].parts[concrete.part_name]
        offset_x = 0.5 * (column.width1 - 2 * column.thickness - itube.width1)
        offset_y = 0.5 * (column.height1 - 2 * column.thickness - itube.height1)
        height1 = column.height1 - 2 * column.thickness
        height2 = column.height2
        width1 = column.width1 - 2 * column.thickness
        width2 = column.width2

        #outer
        if self.more_partition:
            pickedRegions = p.sets[concrete.sets.outer_concrete].cells
            p.setMeshControls(regions=pickedRegions, technique=SWEEP, algorithm=MEDIAL_AXIS)

        #inner corner
        pickedRegions = p.cells.getByBoundingBox(
            xMin=itube.thickness + offset_x, xMax=itube.radius1 + offset_x,
            yMin=itube.thickness + offset_y, yMax=itube.radius1 + offset_y,
            zMin=-itube.pad_thickness, zMax=concrete.length)
        p.setMeshControls(regions=pickedRegions, elemShape=WEDGE, technique=SWEEP)

        pickedRegions = p.cells.getByBoundingBox(
            xMin=itube.width1 - itube.radius1 + offset_x,
            xMax=itube.width1 - itube.thickness + offset_x,
            yMin=itube.thickness + offset_y, yMax=itube.radius1 + offset_y,
            zMin=-itube.pad_thickness, zMax=concrete.length)
        p.setMeshControls(regions=pickedRegions, elemShape=WEDGE, technique=SWEEP)

        pickedRegions = p.cells.getByBoundingBox(
            xMin=itube.thickness + offset_x, xMax=itube.radius1 + offset_x,
            yMin=itube.height1 - itube.radius1 + offset_y,
            yMax=itube.height1 - itube.thickness + offset_y,
            zMin=-itube.pad_thickness, zMax=concrete.length)
        p.setMeshControls(regions=pickedRegions, elemShape=WEDGE, technique=SWEEP)

        pickedRegions = p.cells.getByBoundingBox(
            xMin=itube.width1 - itube.width2 - itube.thickness + offset_x,
            xMax=itube.width1 - itube.width2 - itube.thickness + offset_x + itube.radius1,
            yMin=itube.height1 - itube.height2 - itube.thickness + offset_y,
            yMax=itube.height1 - itube.height2 - itube.thickness + offset_y + itube.radius1,
            zMin=-itube.pad_thickness, zMax=concrete.length)
        p.setMeshControls(regions=pickedRegions, elemShape=WEDGE, technique=SWEEP)

        #other
        if concrete.length > itube.length - itube.pad_thickness:
            pickedRegions = p.sets[concrete.sets.other_concrete].cells
            p.setMeshControls(regions=pickedRegions, elemShape=WEDGE, technique=SWEEP)

    def __setSeed(self, itube:Itube, column:Column, concrete:Concrete):
        p = mdb.models[concrete.model_name].parts[concrete.part_name]
        #global
        p.seedPart(size=self.outter_size, deviationFactor=0.1, minSizeFactor=0.1)
        #inner

        offset_x = 0.5 * (column.width1 - 2 * column.thickness - itube.width1)
        offset_y = 0.5 * (column.height1 - 2 * column.thickness - itube.height1)
        if self.innner_size:
            pickedEdges = p.edges.getByBoundingBox(
                xMin=itube.thickness + offset_x, xMax=itube.width1 - itube.width2 - itube.thickness + offset_x,
                yMin=itube.thickness + offset_y, yMax=itube.height1 - itube.thickness + offset_y,
                zMin=-itube.pad_thickness, zMax=concrete.length)
            p.seedEdgeBySize(edges=pickedEdges, size=self.innner_size, deviationFactor=0.1,
                             minSizeFactor=0.1, constraint=FINER)

            pickedEdges = p.edges.getByBoundingBox(
                xMin=itube.thickness + offset_x, xMax=itube.width1 - itube.thickness + offset_x,
                yMin=itube.thickness + offset_y, yMax=itube.height1 - itube.height2 - itube.thickness + offset_y,
                zMin=-itube.pad_thickness, zMax=concrete.length)
            p.seedEdgeBySize(edges=pickedEdges, size=self.innner_size, deviationFactor=0.1,
                             minSizeFactor=0.1, constraint=FINER)
            if itube.length - itube.pad_thickness < concrete.length:
                pickedEdges = _getEdgesParalleToZ(itube.length - itube.pad_thickness, concrete.length, concrete, column)
                p.deleteSeeds(regions=pickedEdges)
        #local
        if self.radius1_outside_elements:
            height1 = column.height1 - 2 * column.thickness
            height2 = column.height2
            width1 = column.width1 - 2 * column.thickness
            width2 = column.width2 - 2 * column.width2
            radius1 = column.radius1 - column.thickness
            deltaZ = 0.1

            pickedEdges = p.edges.getByBoundingBox(
                xMin=0, xMax=radius1,
                yMin=0, yMax=radius1,
                zMin=-deltaZ, zMax=deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)
            pickedEdges = p.edges.getByBoundingBox(
                xMin=0, xMax=radius1,
                yMin=0, yMax=radius1,
                zMin=concrete.length - deltaZ, zMax=concrete.length + deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)

            pickedEdges = p.edges.getByBoundingBox(
                xMin=0, xMax=radius1,
                yMin=height1 - radius1, yMax=height1,
                zMin=-deltaZ, zMax=deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)
            pickedEdges = p.edges.getByBoundingBox(
                xMin=0, xMax=radius1,
                yMin=height1 - radius1, yMax=height1,
                zMin=concrete.length - deltaZ, zMax=concrete.length + deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)

            pickedEdges = p.edges.getByBoundingBox(
                xMin=width1 - radius1, xMax=width1,
                yMin=0, yMax=radius1,
                zMin=-deltaZ, zMax=deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)
            pickedEdges = p.edges.getByBoundingBox(
                xMin=width1 - radius1, xMax=width1,
                yMin=0, yMax=radius1,
                zMin=concrete.length - deltaZ, zMax=concrete.length + deltaZ)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_outside_elements, constraint=FINER)

        if self.radius1_inside_elements:
            length1 = itube.radius1 / (2**0.5)
            length2 = itube.radius1 - length1
            radius1 = itube.radius1
            height1 = itube.height1
            width1 = itube.width1
            deltaZ = 0.1

            pickedEdges = p.edges.getByBoundingBox(
                xMin=0 + offset_x, xMax=length2 + offset_x,
                yMin=length2 + offset_y, yMax=radius1 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)
            pickedEdges += p.edges.getByBoundingBox(
                xMin=length2 + offset_x, xMax=radius1 + offset_x,
                yMin=0 + offset_y, yMax=length2 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)

            pickedEdges += p.edges.getByBoundingBox(
                xMin=0 + offset_x, xMax=length2 + offset_x,
                yMin=height1 - radius1 + offset_y, yMax=height1 - length2 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)
            pickedEdges += p.edges.getByBoundingBox(
                xMin=length2 + offset_x, xMax=radius1 + offset_x,
                yMin=height1 - length2 + offset_y, yMax=height1 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)

            pickedEdges += p.edges.getByBoundingBox(
                xMin=width1 - radius1 + offset_x, xMax=width1 - length2 + offset_x,
                yMin=0 + offset_y, yMax=length2 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)
            pickedEdges += p.edges.getByBoundingBox(
                xMin=width1 - length2 + offset_x, xMax=width1 + offset_x,
                yMin=length2 + offset_y, yMax=radius1 + offset_y,
                zMin=-deltaZ, zMax=deltaZ)

            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius1_inside_elements, constraint=FINER)

        if self.radius2_elements:
            x2 = itube.width1 - itube.width2 - itube.thickness + itube.radius1 - itube.radius1 / (2**0.5) + offset_x
            y2 = itube.height1 - itube.height2 - itube.thickness + itube.radius1 - itube.radius1 / (2**0.5) + offset_y
            pickedEdges = p.edges.findAt(((x2, y2, -itube.pad_thickness), ),
                                         ((x2, y2, 0), ),
                                         ((x2, y2, concrete.length), ))
            p.seedEdgeByNumber(edges=pickedEdges, number=self.radius2_elements, constraint=FINER)
        # shearkey_elements
        if self.shearkey_elements:
            delta = column.shearkey_h
            width1 = column.width1 - 2 * column.thickness
            width2 = column.width2
            height1 = column.height1 - 2 * column.thickness
            height2 = column.height2
            x1min = width1 - width2 - delta
            x1max = width1 - width2
            y1min = height1 - delta
            y1max = height1
            x2min = width1 - delta
            x2max = width1
            y2min = height1 - height2 - delta
            y2max = height1 - height2
            half_w = 0.5 * column.shearkey_w
            pos = column.shearkey_p
            pickedEdges = p.edges.getByBoundingBox(xMin=x1min, xMax=x1max,
                                                   yMin=y1min, yMax=y1max,
                                                   zMin=pos - half_w, zMax=pos + half_w)
            pickedEdges += p.edges.getByBoundingBox(xMin=x2min, xMax=x2max,
                                                    yMin=y2min, yMax=y2max,
                                                    zMin=pos - half_w, zMax=pos + half_w)
            for i in range(column.shearkey_nums - 1):
                pos = column.shearkey_p + (i + 1) * column.shearkey_s
                pickedEdges += p.edges.getByBoundingBox(xMin=x1min, xMax=x1max,
                                                        yMin=y1min, yMax=y1max,
                                                        zMin=pos - half_w, zMax=pos + half_w)
                pickedEdges += p.edges.getByBoundingBox(xMin=x2min, xMax=x2max,
                                                        yMin=y2min, yMax=y2max,
                                                        zMin=pos - half_w, zMax=pos + half_w)
            delta = itube.shearkey_h
            width1 = itube.width1
            width2 = itube.width2
            height1 = itube.height1
            height2 = itube.height2
            x1min = width1 - width2
            x1max = width1 - width2 + delta
            y1min = height1
            y1max = height1 + delta
            x2min = width1
            x2max = width1 + delta
            y2min = height1 - height2
            y2max = height1 - height2 + delta
            half_w = 0.5 * itube.shearkey_w
            offset_x = (column.width1 - 2 * column.thickness - itube.width1) / 2
            offset_y = (column.height1 - 2 * column.thickness - itube.height1) / 2
            for i in range(itube.shearkey_nums):
                pos = itube.shearkey_p + i * itube.shearkey_s
                pickedEdges += p.edges.getByBoundingBox(xMin=x1min + offset_x, xMax=x1max + offset_x,
                                                        yMin=y1min + offset_y, yMax=y1max + offset_y,
                                                        zMin=pos - half_w, zMax=pos + half_w)
                pickedEdges += p.edges.getByBoundingBox(xMin=x2min + offset_x, xMax=x2max + offset_x,
                                                        yMin=y2min + offset_y, yMax=y2max + offset_y,
                                                        zMin=pos - half_w, zMax=pos + half_w)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.shearkey_elements, constraint=FINER)

        if self.edge1_elements:
            x1 = itube.width1 - itube.width2 + offset_x
            y1 = itube.height1 + offset_y
            x2 = itube.width1 + offset_x
            y2 = itube.height1 - itube.height2 + offset_y
            delta = 0.1
            points = [((x1, y1 - delta, 0),),
                      ((x2 - delta, y2, 0),),
                      ((x1, y1 - delta, concrete.length),),
                      ((x2 - delta, y2, concrete.length),),]
            pickedEdges = p.edges.findAt(*points)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.edge1_elements, constraint=FINER)

        if self.grout_layer_elements:
            delta = 0.1
            offset_y = (column.height1 - 2* column.thickness - itube.height1) * 0.5
            points_on_t = []
            points_on_t.append(((delta, offset_y + itube.radius1, concrete.length),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.grout_layer_elements, constraint=FINER)

    def __generateMesh(self, itube:Itube, column:Column, concrete:Concrete):
        p = mdb.models[concrete.model_name].parts[concrete.part_name]
        pickedRegions = p.sets[concrete.sets.outer_concrete].cells
        p.generateMesh(regions=pickedRegions)
        pickedRegions = p.sets[concrete.sets.inner_concrete].cells
        p.generateMesh(regions=pickedRegions)
        if concrete.length > itube.length - itube.pad_thickness:
            pickedRegions = p.sets[concrete.sets.other_concrete].cells
            p.generateMesh(regions=pickedRegions)

def _getEdgesParalleToZ(z0, z1, concrete:Concrete, column:Column):
    p = mdb.models[concrete.model_name].parts[concrete.part_name]
    width = column.width1 - 2 * column.thickness
    height = column.height1 - 2 * column.thickness
    pickedEdges = p.edges.getByBoundingBox(xMin=0, xMax=width,
                                           yMin=0, yMax=height,
                                           zMin=z0, zMax=z1)
    deltaZ = 0.1
    pickedEdgesZ0 = p.edges.getByBoundingBox(xMin=0, xMax=width,
                                             yMin=0, yMax=height,
                                             zMin=z0 - deltaZ, zMax=z0 + deltaZ)
    pickedEdgesZ1 = p.edges.getByBoundingBox(xMin=0, xMax=width,
                                             yMin=0, yMax=height,
                                             zMin=z1 - deltaZ, zMax=z1 + deltaZ)
    set_all = {edge.index for edge in pickedEdges}
    set_0 = {edge.index for edge in pickedEdgesZ0}
    set_1 = {edge.index for edge in pickedEdgesZ1}
    set_need = set_all - set_0 - set_1
    e = p.edges
    return part.EdgeArray([e[i] for i in set_need])