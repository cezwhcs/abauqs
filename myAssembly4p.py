from abaqus import *
from abaqusConstants import *
from caeModules import *
from column4p import Column
from itube import Itube
from concrete import Concrete
from arcShell import ArcShell

class MyAssembly:
    def __init__(self, itube:Itube, column:Column, concrete:Concrete, arcshell:ArcShell,
                 model_name='Model-1', column_name='', itube_name='', concrete_name='', arcshell_name='',
                 load_plane_name='surf-load', hold_plane_name='surf-hold' ,symmetry_plane_name='surf-symmetry', support_plane_name='surf-support',
                 load_point_name='point-load', support_point_name='point-support'):
        self.model_name = model_name
        self.column_name = column_name if column_name else f"{column.part_name}-1"
        self.itube_name = itube_name if itube_name else f"{itube.part_name}-1"
        self.concrete_name = concrete_name if concrete_name else f"{concrete.part_name}-1"
        self.arcshell_name = arcshell_name if arcshell_name else  f"{arcshell.part_name}-1"
        self.__createPart(itube, column, concrete, arcshell)
        self.__movePosition(itube, column, concrete, arcshell)
        self.sets = _Set(model_name, self.column_name, self.itube_name, self.concrete_name, self.arcshell_name, itube, column, concrete, arcshell,
                         load_plane_name, hold_plane_name, symmetry_plane_name, support_plane_name, load_point_name, support_point_name)

    def __createPart(self, itube:Itube, column:Column, concrete:Concrete, arcshell:ArcShell):
        a = mdb.models[self.model_name].rootAssembly
        a.DatumCsysByDefault(CARTESIAN)

        p = mdb.models[column.model_name].parts[column.part_name]
        a.Instance(name=self.column_name, part=p, dependent=ON)

        p = mdb.models[concrete.model_name].parts[concrete.part_name]
        a.Instance(name=self.concrete_name, part=p, dependent=ON)

        p = mdb.models[itube.model_name].parts[itube.part_name]
        a.Instance(name=self.itube_name, part=p, dependent=ON)

        p = mdb.models[arcshell.model_name].parts[arcshell.part_name]
        a.Instance(name=self.arcshell_name, part=p, dependent=ON)

    def __movePosition(self, itube:Itube, column:Column, concrete:Concrete, arcshell:ArcShell):
        a = mdb.models[self.model_name].rootAssembly

        offset_x = 0.5 * (column.width1 - itube.width1)
        offset_y = 0.5 * (column.height1 - itube.height1)
        a.translate(instanceList=(self.itube_name,), vector=(offset_x, offset_y, -itube.pad_thickness))

        offset_x = offset_y = column.thickness
        a.translate(instanceList=(self.concrete_name,), vector=(offset_x, offset_y, 0))

        a.rotate(instanceList=(self.arcshell_name,), axisPoint=(0.0, 0.0, 0.0),
                 axisDirection=(0.0, 10.0, 0.0), angle=-45.0)
        a.rotate(instanceList=(self.arcshell_name,), axisPoint=(0.0, 0.0, 0.0),
                 axisDirection=(0.0, 0.0, 10.0), angle=-90.0)
        a.translate(instanceList=(self.arcshell_name,),vector=(-0.5 * (arcshell.length - column.width1),
                                                               column.height1 + column.pad3_thickness + arcshell.radius,
                                                               column.pad2_pos - 0.5 * column.pad2_thickness))

class _Set:
    def __init__(self, model_name, column_name, itube_name, concrete_name, arcshell_name,
                 itube: Itube, column: Column, concrete: Concrete, arcshell:ArcShell,
                 load_plane_name, hold_plane_name, symmetry_plane_name, support_plane_name,
                 load_point_name, support_point_name):
        self.load_plane_name = load_plane_name
        self.hold_plane_name = hold_plane_name
        self.symmetry_plane_name = symmetry_plane_name
        self.support_plane_name = support_plane_name
        self.load_point_name = load_point_name
        self.support_point_name = support_point_name
        self.__createPlaneSurfaceAndSet(model_name, column_name, itube_name, concrete_name, arcshell_name, itube, column, concrete, arcshell)
        self.__createPointSet(model_name, column_name, itube_name, concrete_name, arcshell_name, itube, column, concrete, arcshell)

    def __createPlaneSurfaceAndSet(self, model_name, column_name, itube_name, concrete_name, arcshell_name,
                             itube:Itube, column:Column, concrete:Concrete, arcshell:ArcShell):
        a = mdb.models[model_name].rootAssembly
        s = mdb.models[model_name].rootAssembly.instances[arcshell_name].faces
        a.Surface(side2Faces=s, name=self.load_plane_name)
        a.Set(faces=s, name=self.load_plane_name)

        offset_x = -column.pad2_margin
        offset_y = column.height1 + column.pad3_thickness
        offset_z = column.pad2_pos - 0.5 * column.pad3_width
        deltaY = 0.1
        width1 = column.width1 + 2 * column.pad2_margin
        s0 = a.instances[column_name].faces
        faces0 = s0.getByBoundingBox(xMin=offset_x, xMax=width1 + offset_x,
                                     yMin=offset_y - deltaY, yMax=offset_y + deltaY,
                                     zMin=offset_z, zMax=offset_z + column.pad3_width)
        a.Surface(side1Faces=faces0, name=self.hold_plane_name)
        a.Set(faces=faces0, name=self.hold_plane_name)

        width1 = itube.width1 - 2 * itube.thickness
        height1 = itube.height1 - 2 * itube.thickness
        offset_x = (column.width1 - width1) * 0.5
        offset_y = (column.height1 - height1) * 0.5
        offset_z = -itube.pad_thickness
        deltaZ = 0.1

        s1 = a.instances[concrete_name].faces
        faces1 = s1.getByBoundingBox(xMin=offset_x, xMax=width1 + offset_x,
                                          yMin=offset_y, yMax=height1 + offset_y,
                                          zMin=offset_z - deltaZ, zMax=offset_z + deltaZ)
        offset_x = 0.5 * (column.width1 - itube.pad_width)
        offset_y = 0.5 * (column.height1 - itube.pad_height)
        offset_z = -itube.pad_thickness
        width1 = itube.pad_width
        height1 = itube.pad_height
        s2 = a.instances[itube_name].faces
        faces2 = s2.getByBoundingBox(xMin=offset_x, xMax=width1 + offset_x,
                                          yMin=offset_y, yMax=height1 + offset_y,
                                          zMin=offset_z - deltaZ, zMax=offset_z + deltaZ)
        a.Surface(side1Faces=faces1 + faces2, name=self.symmetry_plane_name)
        a.Set(faces=faces1+faces2, name=self.symmetry_plane_name)

        width1 = column.width1 - 2 * column.radius1
        height1 = column.height1 - 2 * column.radius1
        depth1 = column.pad_thickness
        offset_x = column.radius1
        deltaY = 0.1
        offset_z = column.length - column.pad_pos - 0.5 * column.pad_thickness
        s3 = a.instances[column_name].faces
        faces3 = s3.getByBoundingBox(xMin=offset_x, xMax=width1 + offset_x,
                                          yMin=-deltaY, yMax=deltaY,
                                          zMin=offset_z, zMax=depth1 + offset_z)
        a.Surface(side1Faces=faces3, name=self.support_plane_name)
        a.Set(faces=faces3, name=self.support_plane_name)

    def __createPointSet(self, model_name, column_name, itube_name, concrete_name, arcshell_name,
                         itube:Itube, column:Column, concrete:Concrete, arcshell:ArcShell):
        a = mdb.models[model_name].rootAssembly
        ins = mdb.models[model_name].rootAssembly.instances[arcshell_name]
        r = ins.referencePoints
        refPoints = (r[2],)
        a.Set(referencePoints=refPoints, name=self.load_point_name)
        r = a.referencePoints
        offset_y = -35
        offset_z = column.length - column.pad_pos + 0.5 * column.pad_thickness
        width1 = column.width1
        supportPoint = a.ReferencePoint(point=(0.5 * width1, offset_y, offset_z))
        a.Set(referencePoints=(r[supportPoint.id], ), name=self.support_point_name)

def regenerate_assembly(assembly:MyAssembly):
    a = mdb.models[assembly.model_name].rootAssembly
    a.regenerate()