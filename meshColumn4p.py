from abaqus import *
from abaqusConstants import *
from caeModules import *
from column4p import Column
from partitionColumn4p import PartitionColumn

class MeshColumn:
    def __init__(self, column: Column, partitionColumn:PartitionColumn, tube_t_elements=3, shearkey_arc_elements=6, pad_t_elements=2,
                 column_3corners_elements=3, column_1corner_elements=3, pad2_thickness_elements=2, pad3_thickness_elements=2,
                 hollow_length_size=25, grouted_length_size=0,
                 shearkey_WEDGE=True, pad_corner_WEDGE=True, pad_hole_WEDGE=True,
                 pad2_3corners_WEDGE=True, pad2_1corner_WEDGE=True):
        self.global_size = partitionColumn.global_size
        self.tube_t_elements = tube_t_elements
        self.shearkey_arc_elements = shearkey_arc_elements
        self.pad_t_elements = pad_t_elements
        self.column_3corners_elements = column_3corners_elements
        self.column_1corner_elements = column_1corner_elements
        self.pad2_thickness_elements = pad2_thickness_elements
        self.pad3_thickness_elements = pad3_thickness_elements
        self.hollow_length_size = hollow_length_size
        self.grouted_length_size = grouted_length_size
        self.shearkey_WEDGE = shearkey_WEDGE
        self.pad_corner_WEDGE = pad_corner_WEDGE
        self.pad_hole_WEDGE = pad_hole_WEDGE
        self.pad2_3corners_WEDGE = pad2_3corners_WEDGE
        self.pad2_1corner_WEDGE = pad2_1corner_WEDGE
        self.__setElementType(column)
        self.__setSseed(column, partitionColumn)
        self.__generateMesh(column)

    def __setElementType(self, column: Column):
        p = mdb.models[column.model_name].parts[column.part_name]

        #corner in pad
        if self.pad_corner_WEDGE:
            inner_pos = column.thickness + 0.5 * column.radius1
            mid_z = column.length - column.pad_pos
            points = [((inner_pos, inner_pos, mid_z), ),
                      ((inner_pos, column.height1 - inner_pos, mid_z),),
                      ((column.width1 - inner_pos, inner_pos, mid_z),)]
            pickedCells = p.cells.findAt(*points)
            p.setMeshControls(regions=pickedCells, elemShape=WEDGE, technique=SWEEP)

        #shearkey
        if self.shearkey_WEDGE:
            shearkeySet = p.sets[column.sets.shearkey]
            p.setMeshControls(regions=shearkeySet.cells, elemShape=WEDGE, technique=SWEEP)

        if self.pad_hole_WEDGE:
            delta = 0.1
            points = [((column.radius1 + delta, column.radius1 + delta, column.length - column.pad_pos),)]
            pickedCells = p.cells.findAt(*points)
            p.setMeshControls(regions=pickedCells, elemShape=WEDGE, technique=SWEEP)

        if self.pad2_3corners_WEDGE:
            delta = 0.1
            points = [((delta, delta, column.pad2_pos),),
                      ((delta, column.height1 - delta, column.pad2_pos),),
                      ((column.width1 - delta, delta, column.pad2_pos),)]
            pickedCells = p.cells.findAt(*points)
            p.setMeshControls(regions=pickedCells, elemShape=WEDGE, technique=SWEEP)

        if self.pad2_1corner_WEDGE:
            delta = 0.1
            points = [((column.width1 - column.width2 - column.thickness + column.radius1 - delta,
                        column.height1 - column.height2 - column.thickness + column.radius1 - delta,
                        column.pad2_pos),)]
            pickedCells = p.cells.findAt(*points)
            p.setMeshControls(regions=pickedCells, elemShape=WEDGE, technique=SWEEP)

    def __setSseed(self, column: Column, partitionColumn:PartitionColumn):
        p = mdb.models[column.model_name].parts[column.part_name]
        p.seedPart(size=self.global_size, deviationFactor=0.1, minSizeFactor=0.1)

        if self.shearkey_arc_elements:
            if not partitionColumn.shearkey_partition:
                points_on_arc = []
                x1 = column.width1 - column.width2 - column.thickness - column.shearkey_h
                y1 = column.height1 - column.thickness - column.shearkey_h
                x2 = column.width1 - column.thickness - column.shearkey_h
                y2 = column.height1 - column.height2 - column.thickness - column.shearkey_h
                for i in range(column.shearkey_nums):
                    z = i * column.shearkey_s + column.shearkey_p
                    points_on_arc.append(((x1, y1, z),))
                    points_on_arc.append(((x2, y2, z),))
                pickedEdges = p.edges.findAt(*points_on_arc)
                p.seedEdgeByNumber(edges=pickedEdges, number=self.shearkey_arc_elements, constraint=FINER)
            else:
                points_on_arc = []
                x1 = column.width1 - column.width2 - column.thickness - column.shearkey_h * 0.5
                y1 = column.height1 - column.thickness - column.shearkey_h * 0.5
                x2 = column.width1 - column.thickness - column.shearkey_h * 0.5
                y2 = column.height1 - column.height2 - column.thickness - column.shearkey_h * 0.5
                deltaZ = 0.5 * (column.shearkey_h**2 + column.shearkey_w**2 / 2)**0.5
                for i in range(column.shearkey_nums):
                    z = i * column.shearkey_s + column.shearkey_p
                    points_on_arc.append(((x1, y1, z - deltaZ),))
                    points_on_arc.append(((x1, y1, z + deltaZ),))
                    points_on_arc.append(((x2, y2, z - deltaZ),))
                    points_on_arc.append(((x2, y2, z + deltaZ),))
                pickedEdges = p.edges.findAt(*points_on_arc)
                p.seedEdgeByNumber(edges=pickedEdges, number=int(0.5 * self.shearkey_arc_elements), constraint=FINER)

        if self.tube_t_elements:
            points_on_t = []
            points_on_t.append(((column.width1 - column.width2 - column.thickness, column.height1 - 0.5 * column.thickness, 0),))
            points_on_t.append(((column.width1 - column.width2 - 0.5 * column.thickness, column.height1 - column.thickness, 0),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.tube_t_elements, constraint=FINER)

        if self.pad_t_elements:
            points_on_t = []
            points_on_t.append(((column.radius1, column.radius1, column.length - column.pad_pos),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.pad_t_elements, constraint=FINER)

        if self.column_3corners_elements:
            points_on_t = []
            out_arc = column.radius1 - column.radius1 / (2 ** 0.5)
            in_arc = column.radius1 - (column.radius1 - column.thickness) / (2 ** 0.5)
            points_on_t.append(((out_arc, out_arc, 0),))
            points_on_t.append(((in_arc, in_arc, 0),))
            points_on_t.append(((out_arc, column.height1 - out_arc, 0),))
            points_on_t.append(((in_arc, column.height1 - in_arc, 0),))
            points_on_t.append(((column.width1 - out_arc, out_arc, 0),))
            points_on_t.append(((column.width1 - in_arc, in_arc, 0),))

            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.column_3corners_elements, constraint=FINER)

        if self.column_1corner_elements:
            points_on_t = []
            out_arc = column.radius1 - column.radius1 / (2 ** 0.5)
            in_arc = column.radius1 - (column.radius1 - column.thickness) / (2 ** 0.5)
            points_on_t.append(((column.width1 - column.width2 - column.thickness + out_arc,
                                 column.height1 - column.height2 - column.thickness + out_arc, 0),))
            points_on_t.append(((column.width1 - column.width2 - column.thickness + in_arc,
                                 column.height1 - column.height2 - column.thickness + in_arc, 0),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.column_1corner_elements, constraint=FINER)

        if self.pad2_thickness_elements:
            points_on_t = []
            points_on_t.append(((-column.pad2_margin, column.height1, column.pad2_pos),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.pad2_thickness_elements, constraint=FINER)

        if self.pad3_thickness_elements:
            points_on_t = []
            points_on_t.append(((-column.pad2_margin, column.height1 + 0.5 * column.pad3_thickness,
                                 column.pad2_pos - 0.5 * column.pad2_thickness),))
            pickedEdges = p.edges.findAt(*points_on_t)
            p.seedEdgeByNumber(edges=pickedEdges, number=self.pad3_thickness_elements, constraint=FINER)

        if self.hollow_length_size:
            last_shearkey_pos = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s
            if partitionColumn.mesh_dense_extend_length:
                z0 = last_shearkey_pos + 0.5 * column.shearkey_w
                z1 = last_shearkey_pos + partitionColumn.mesh_dense_extend_length
                pickedEdges = _getEdgesParalleToZ(z0, z1, column)
                z0 = z1
                z1 = column.pad2_pos - 0.5 * column.pad3_width
                pickedEdges += _getEdgesParalleToZ(z0, z1, column)
            else:
                z0 = last_shearkey_pos + 0.5 * column.shearkey_w
                z1 = column.pad2_pos - 0.5 * column.pad3_width
                pickedEdges = _getEdgesParalleToZ(z0, z1, column)

            z0 = column.pad2_pos + 0.5 * column.pad3_width
            z1 = column.length - column.pad_pos - 0.5 * column.pad_thickness
            pickedEdges += _getEdgesParalleToZ(z0, z1, column)

            z0 = column.length - column.pad_pos + 0.5 * column.pad_thickness
            z1 = column.length
            pickedEdges += _getEdgesParalleToZ(z0, z1, column)
            p.seedEdgeBySize(edges=pickedEdges, size=self.hollow_length_size,
                             deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

        if self.grouted_length_size:
            z0 = 0
            z1 = column.shearkey_p - 0.5 * column.shearkey_w
            pickedEdges = _getEdgesParalleToZ(z0, z1, column)

            for i in range(column.shearkey_nums - 1):
                pos = column.shearkey_p + column.shearkey_s * i
                z0 = pos + 0.5 * column.shearkey_w
                z1 = pos + column.shearkey_s - 0.5 * column.shearkey_w
                pickedEdges += _getEdgesParalleToZ(z0, z1, column)

            p.seedEdgeBySize(edges=pickedEdges, size=self.grouted_length_size,
                             deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

        if self.grouted_length_size:
            z0 = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + 0.5 * column.shearkey_w
            z1 = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + partitionColumn.mesh_dense_extend_length
            pickedEdges = _getEdgesParalleToZ(z0, z1, column)
            p.seedEdgeBySize(edges=pickedEdges, size=self.grouted_length_size,
                             deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

    def __generateMesh(self, column: Column):
        p = mdb.models[column.model_name].parts[column.part_name]
        p.generateMesh()

def _getEdgesParalleToZ(z0, z1, column:Column):
    p = mdb.models[column.model_name].parts[column.part_name]
    pickedEdges = p.edges.getByBoundingBox(xMin=0, xMax=column.width1,
                                           yMin=0, yMax=column.height1,
                                           zMin=z0, zMax=z1)
    deltaZ = 0.1
    pickedEdgesZ0 = p.edges.getByBoundingBox(xMin=0, xMax=column.width1,
                                             yMin=0, yMax=column.height1,
                                             zMin=z0 - deltaZ, zMax=z0 + deltaZ)
    pickedEdgesZ1 = p.edges.getByBoundingBox(xMin=0, xMax=column.width1,
                                             yMin=0, yMax=column.height1,
                                             zMin=z1 - deltaZ, zMax=z1 + deltaZ)
    set_all = {edge.index for edge in pickedEdges}
    set_0 = {edge.index for edge in pickedEdgesZ0}
    set_1 = {edge.index for edge in pickedEdgesZ1}
    set_need = set_all - set_0 - set_1
    e = p.edges
    return part.EdgeArray([e[i] for i in set_need])