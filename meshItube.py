from abaqus import *
from abaqusConstants import *
from caeModules import *
from itube import Itube
from partitionItube import PartitionItube

class MeshItube:
    def __init__(self, itube:Itube, partitionItube:PartitionItube, global_size=12,
                 tube_t_elements=3, arc_elements=6, pad_t_elements=2,
                 corner3_elements=4, corner1_elements=3,
                 shearkey_WEDGE = True, corner_WEDGE= True):
        self.global_size = global_size
        self.tube_t_elements = tube_t_elements
        self.arc_elements = arc_elements
        self.pad_t_elements = pad_t_elements
        self.corner3_elements = corner3_elements
        self.corner1_elements = corner1_elements
        self.shearkey_WEDGE = shearkey_WEDGE
        self.corner_WEDGE = corner_WEDGE
        self.__setElementType(itube)
        self.__setSseed(itube)
        self.__generateMesh(itube)

    def __setElementType(self, itube: Itube):
        p = mdb.models[itube.model_name].parts[itube.part_name]

        #corner in pad
        if self.corner_WEDGE:
            inner_pos = (2 - 2**0.5) / 4.0 * itube.radius1
            mid_z = 0.5 * itube.pad_thickness
            points = [((inner_pos, inner_pos, mid_z), ),
                      ((itube.width1 - inner_pos, inner_pos, mid_z), ),
                      ((inner_pos, itube.height1 - inner_pos, mid_z), ),
                      ((itube.width1 - itube.width2 + 0.5 * (itube.radius1 - itube.thickness),
                        itube.height1 - itube.height2 + 0.5 * (itube.radius1 - itube.thickness),
                        mid_z), )]
            pickedCells = p.cells.findAt(*points)
            p.setMeshControls(regions=pickedCells, elemShape=WEDGE, technique=SWEEP)

        #shearkey
        if self.shearkey_WEDGE:
            shearkeySet = p.sets[itube.sets.shearkey]
            p.setMeshControls(regions=shearkeySet.cells, elemShape=WEDGE, technique=SWEEP)

    def __setSseed(self, itube: Itube):
        p = mdb.models[itube.model_name].parts[itube.part_name]
        p.seedPart(size=self.global_size, deviationFactor=0.1, minSizeFactor=0.1)

        if self.arc_elements:
            points_on_arc = []
            x1 = itube.width1 - itube.width2 + itube.shearkey_h
            y1 = itube.height1 + itube.shearkey_h
            x2 = itube.width1 + itube.shearkey_h
            y2 = itube.height1 - itube.height2 + itube.shearkey_h
            z = itube.pad_thickness + itube.shearkey_p
            for i in range(itube.shearkey_nums):
                points_on_arc.append(((x1, y1, z + i * itube.shearkey_s), ))
                points_on_arc.append(((x2, y2, z + i * itube.shearkey_s), ))
            pickedEdges = p.edges.findAt(*points_on_arc)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.arc_elements, constraint=FINER)

        if self.tube_t_elements:
            points_on_t = []
            points_on_t.append(((itube.width1 - itube.width2 - itube.thickness, itube.height1 - 0.5 * itube.thickness, 0), ))
            points_on_t.append(((itube.width1 - itube.width2 - 0.5 * itube.thickness, itube.height1 - itube.thickness, 0), ))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.tube_t_elements, constraint=FINER)

        if self.pad_t_elements:
            points_on_t = []
            points_on_t.append(((0, 0, 0.5 * itube.pad_thickness),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.pad_t_elements, constraint=FINER)

        if self.corner3_elements:
            points_on_t = []
            out_arc = itube.radius1 - itube.radius1 / (2**0.5)
            in_arc = itube.radius1 - (itube.radius1 - itube.thickness) / (2**0.5)
            points_on_t.append(((out_arc, out_arc, 0),))
            points_on_t.append(((in_arc, in_arc, 0),))
            points_on_t.append(((out_arc, itube.height1 - out_arc, 0),))
            points_on_t.append(((in_arc, itube.height1 - in_arc, 0),))
            points_on_t.append(((itube.width1 - out_arc, out_arc, 0),))
            points_on_t.append(((itube.width1 - in_arc, in_arc, 0),))

            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.corner3_elements, constraint=FINER)

        if self.corner1_elements:
            points_on_t = []
            out_arc = itube.radius1 - itube.radius1 / (2 ** 0.5)
            in_arc = itube.radius1 - (itube.radius1 - itube.thickness) / (2 ** 0.5)
            points_on_t.append(((itube.width1 - itube.width2 - itube.thickness + out_arc,
                                 itube.height1 - itube.height2 - itube.thickness + out_arc, 0),))
            points_on_t.append(((itube.width1 - itube.width2 - itube.thickness + in_arc,
                                 itube.height1 - itube.height2 - itube.thickness + in_arc, 0),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.corner1_elements, constraint=FINER)

    def __generateMesh(self, itube: Itube):
        p = mdb.models[itube.model_name].parts[itube.part_name]
        p.generateMesh()