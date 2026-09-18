from abaqus import *
from abaqusConstants import *
from caeModules import *
from column3p import Column

class PartitionColumn:
    def __init__(self, column: Column, global_size=14, mesh_dense_extend_length=100, shearkey_partition=False):
        self.global_size = global_size
        self.mesh_dense_extend_length = mesh_dense_extend_length
        self.shearkey_partition = shearkey_partition
        self.__partition(column)

    def __partition(self, column: Column):
        self.__partition_z(column)
        self.__partition_xy(column)

    def __partition_z(self, column: Column):
        p = mdb.models[column.model_name].parts[column.part_name]
        datumz_index = []

        for i in range(column.shearkey_nums):
            pos = column.shearkey_p + i * column.shearkey_s
            datumz = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=pos - 0.5 * column.shearkey_w)
            datumz_index.append(datumz.id)
            datumz = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=pos + 0.5 * column.shearkey_w)
            datumz_index.append(datumz.id)

        if self.mesh_dense_extend_length:
            pos = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + self.mesh_dense_extend_length
            datumz = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=pos)
            datumz_index.append(datumz.id)

        d = p.datums
        for i in datumz_index:
            pickedCells = p.cells
            p.PartitionCellByDatumPlane(datumPlane=d[i], cells=pickedCells)

        # local partition of shearkey
        if self.shearkey_partition:
            datumz_index = []
            for i in range(column.shearkey_nums):
                pos = column.shearkey_p + i * column.shearkey_s
                datumz = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=pos)
                datumz_index.append(datumz.id)
            d = p.datums
            for i in datumz_index:
                pickedCells = p.sets[column.sets.shearkey].cells
                p.PartitionCellByDatumPlane(datumPlane=d[i], cells=pickedCells)


    def __partition_xy(self, column):
        p = mdb.models[column.model_name].parts[column.part_name]

        edge1_len = column.width1 - column.width2 - column.thickness - column.radius1
        cell1_nums = round(edge1_len / self.global_size)
        edge2_len = column.height1 - column.height2 - column.thickness - column.radius1
        cell2_nums = round(edge2_len / self.global_size)

        x_pos = [column.radius1,
                 column.width1 - column.width2 - column.thickness - edge1_len / cell1_nums,
                 column.width1 - column.width2 - column.thickness,
                 column.width1 - column.width2 - column.thickness + column.radius1,
                 column.width1 - column.radius1,
                 column.width1 - column.thickness]
        y_pos = [column.radius1,
                 column.height1 - column.height2 - column.thickness - edge2_len / cell2_nums,
                 column.height1 - column.height2 - column.thickness,
                 column.height1 - column.height2 - column.thickness + column.radius1,
                 column.height1 - column.radius1,
                 column.height1 - column.thickness]
        datumx_index = []
        datumy_index = []
        for i in range(len(x_pos)):
            datumx = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=x_pos[i])
            datumx_index.append(datumx.id)
        for i in range(len(y_pos)):
            datumy = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=y_pos[i])
            datumy_index.append(datumy.id)
        d = p.datums

        # 1
        for i in range(len(datumy_index)):
            if i == 0 or i == 3 or i == 4:
                pickedCells = p.cells
                p.PartitionCellByDatumPlane(datumPlane=d[datumx_index[i]], cells=pickedCells)
                pickedCells = p.cells
                p.PartitionCellByDatumPlane(datumPlane=d[datumy_index[i]], cells=pickedCells)

        pad_xMin = column.thickness
        pad_xMax = column.width1 - column.thickness
        pad_yMin = column.thickness
        pad_yMax = column.height1 - column.thickness
        pad_zMin = column.length - column.pad_pos - 0.5 * column.pad_thickness
        pad_zMax = pad_zMin + column.pad_thickness
        tube_xMax = column.width1
        tube_yMax = column.height1
        tube_zMax = column.length

        #2
        short_width = column.width1 - column.width2
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[0], xMax=short_width,
            yMin=y_pos[4], yMax=tube_yMax,
            zMin=0, zMax=tube_zMax)
        p.PartitionCellByDatumPlane(datumPlane=d[datumx_index[2]], cells=pickedCells)
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[0], xMax=short_width,
            yMin=y_pos[4], yMax=tube_yMax,
            zMin=0, zMax=tube_zMax)
        p.PartitionCellByDatumPlane(datumPlane=d[datumy_index[5]], cells=pickedCells)

        short_height = column.height1 - column.height2
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[4], xMax=tube_xMax,
            yMin=y_pos[0], yMax=short_height,
            zMin=0, zMax=tube_zMax)
        p.PartitionCellByDatumPlane(datumPlane=d[datumx_index[5]], cells=pickedCells)
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[4], xMax=tube_xMax,
            yMin=y_pos[0], yMax=short_height,
            zMin=0, zMax=tube_zMax)
        p.PartitionCellByDatumPlane(datumPlane=d[datumy_index[2]], cells=pickedCells)

        #3
        grout_length = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + column.shearkey_w
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[0], xMax=x_pos[2],
            yMin=y_pos[4], yMax=y_pos[5],
            zMin=0, zMax=grout_length)
        datum1 = p.DatumPointByCoordinate(coords=(x_pos[2], y_pos[5], 0.0)).id
        datum2 = p.DatumPointByCoordinate(coords=(x_pos[2], y_pos[5], 2)).id
        datum3 = p.DatumPointByCoordinate(coords=(x_pos[2] + 1, y_pos[5] + 1, 0.0)).id
        p.PartitionCellByPlaneThreePoints(point1=d[datum1], point2=d[datum2],
                                          cells=pickedCells, point3=d[datum3])
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[4], xMax=x_pos[5],
            yMin=y_pos[0], yMax=y_pos[2],
            zMin=0, zMax=grout_length)
        datum1 = p.DatumPointByCoordinate(coords=(x_pos[5], y_pos[2], 0.0)).id
        datum2 = p.DatumPointByCoordinate(coords=(x_pos[5], y_pos[2], 1)).id
        datum3 = p.DatumPointByCoordinate(coords=(x_pos[5] + 1, y_pos[2] + 1, 0.0)).id
        p.PartitionCellByPlaneThreePoints(point1=d[datum1], point2=d[datum2],
                                          cells=pickedCells, point3=d[datum3])

        #4
        grout_length = column.shearkey_p + (column.shearkey_nums - 1) * column.shearkey_s + column.shearkey_w
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[0], xMax=x_pos[2],
            yMin=y_pos[4], yMax=y_pos[5],
            zMin=0, zMax=grout_length)
        p.PartitionCellByDatumPlane(datumPlane=d[datumx_index[1]], cells=pickedCells)
        pickedCells = p.cells.getByBoundingBox(
            xMin=x_pos[4], xMax=x_pos[5],
            yMin=y_pos[0], yMax=y_pos[2],
            zMin=0, zMax=grout_length)
        p.PartitionCellByDatumPlane(datumPlane=d[datumy_index[1]], cells=pickedCells)