from abaqus import *
from abaqusConstants import *
from caeModules import *
from tube import Tube

class Column(Tube):
    def __init__(self, shearkey_nums, shearkey_h=4, shearkey_w=9, shearkey_s=40, shearkey_p=20,
                 pad_thickness=20, pad_pos=50, pad_hole_radius=30, pad_hole_pos=[0.42, 0.42],
                 model_name='Model-1', part_name='column',
                 height1=150, width1=150, height2=50, width2=50, radius1=25, thickness=8, length=800,
                 tube_name='Set-tube', pad_name='Set-pad', shearkey_name='Set-shearkey'):
        super().__init__(model_name, part_name, height1, width1, height2, width2, radius1, thickness, length)
        self.shearkey_nums = shearkey_nums
        self.shearkey_h = shearkey_h
        self.shearkey_w = shearkey_w
        self.shearkey_s = shearkey_s
        self.shearkey_p = shearkey_p
        self.pad_thickness = pad_thickness
        self.pad_pos = pad_pos
        self.pad_hole_radius = pad_hole_radius
        self.pad_hole_pos = pad_hole_pos
        self.__generatePad()
        self.__generateShearkey()
        self.sets = _ColumnSet(model_name, part_name, tube_name, pad_name, shearkey_name, shearkey_nums)

    def __generatePad(self):
        plane_z = self.length - self.pad_pos + 0.5 * self.pad_thickness
        p = mdb.models[self.model_name].parts[self.part_name]
        p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE,offset=plane_z)
        f, e1, d1 = p.faces, p.edges, p.datums
        t = p.MakeSketchTransform(sketchPlane=d1[2], sketchUpEdge=e1[19],
                                  sketchPlaneSide=SIDE1, sketchOrientation=RIGHT,
                                  origin=(0.0, 0.0, plane_z))
        s1 = mdb.models[self.model_name].ConstrainedSketch(
            name='__profile__',sheetSize=2000, gridSpacing=50, transform=t)
        p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)
        s1 = _Sketch3(self.model_name, '__profile__', self.height1, self.width1, self.height2,
                      self.width2, self.radius1, self.thickness, self.pad_hole_radius, self.pad_hole_pos)
        f1, e, d2 = p.faces, p.edges, p.datums
        p.SolidExtrude(sketchPlane=d2[2], sketchUpEdge=e[19], sketchPlaneSide=SIDE1,
                       sketchOrientation=RIGHT, sketch=s1, depth=self.pad_thickness,
                       flipExtrudeDirection=ON, keepInternalBoundaries=ON)
        del mdb.models[self.model_name].sketches['__profile__']

    def __generateShearkey(self):
        s1 = mdb.models[self.model_name].ConstrainedSketch(
            name='__profile__',sheetSize=2000, gridSpacing=50,
            transform=(-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -0.0, 1.0, -0.0,
                       self.width1 - self.width2 - self.thickness, self.height1 - self.thickness, 0.0))
        p = mdb.models[self.model_name].parts[self.part_name]
        p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)

        for i in range(self.shearkey_nums):
            pos = i * self.shearkey_s + self.shearkey_p
            s1.Arc3Points(point1=(0.0, pos - 0.5 * self.shearkey_w),
                         point2=(0.0, pos + 0.5 * self.shearkey_w),
                         point3=(self.shearkey_h, pos))
            s1.Line(point1=(0.0, pos - 0.5 * self.shearkey_w),
                   point2=(0.0, pos + 0.5 * self.shearkey_w))
        e = p.edges
        edges = e.getSequenceFromMask(mask=('[#0:2 #8800000 #40810 #354 ]',), )

        p.SolidSweep(path=edges, sketchUpEdge=e[66], sketchOrientation=RIGHT,
                     profile=s1, keepInternalBoundaries=ON)
        del mdb.models[self.model_name].sketches['__profile__']

class _ColumnSet:
    def __init__(self, model_name, part_name, tube_name,
                 pad_name, shearkey_name, shearkey_nums):
        self.tube = tube_name
        self.pad = pad_name
        self.shearkey = shearkey_name
        self.__createSet(model_name, part_name, shearkey_nums)

    def __createSet(self, model_name, part_name, shearkey_nums):
        p = mdb.models[model_name].parts[part_name]
        c = p.cells
        cells = c.getSequenceFromMask(mask=('[#7 ]',), )
        p.Set(cells=cells, name=self.tube)

        cells = c.getSequenceFromMask(mask=('[#8 ]',), )
        p.Set(cells=cells, name=self.pad)

        bi_string = '0000'
        for i in range(shearkey_nums):
            bi_string = '1' + bi_string
        hex_string = hex(int(bi_string, 2))[2:]
        shearkeys_mask = '[#' + hex_string + ' ]'
        cells = c.getSequenceFromMask(mask=(shearkeys_mask,), )
        p.Set(cells=cells, name=self.shearkey)

def _Sketch3(model_name, sketch_name, height1, width1, height2, width2, radius1, thickness, pad_hole_radius, pad_hole_pos):
    sketch = mdb.models[model_name].sketches[sketch_name]
    g, v, d, c = sketch.geometry, sketch.vertices, sketch.dimensions, sketch.constraints
    vertices = ((0, 0), (0, height1), (width1 - width2, height1), (width1 - width2, height1 - height2),
                (width1, height1 - height2), (width1, 0), (0, 0))
    for i in range(len(vertices) - 1):
        sketch.Line(point1=vertices[i], point2=vertices[i + 1])

    sketch.FilletByRadius(radius=radius1, curve1=g[2], nearPoint1=(0, radius1), curve2=g[7],
                          nearPoint2=(radius1, 0))
    sketch.FilletByRadius(radius=radius1, curve1=g[2], nearPoint1=(0, height1 - radius1), curve2=g[3],
                          nearPoint2=(radius1, height1))
    sketch.FilletByRadius(radius=radius1, curve1=g[6], nearPoint1=(width1, radius1), curve2=g[7],
                          nearPoint2=(width1 - radius1, 0))
    sketch.FilletByRadius(radius=radius1 - thickness, curve1=g[4],
                          nearPoint1=(width1 - width2, height1 - height2 + radius1 - thickness),
                          curve2=g[5], nearPoint2=(width1 - width2 + radius1 - thickness, height1 - height2))
    sketch.CircleByCenterPerimeter(center=(width1 * pad_hole_pos[0], height1* pad_hole_pos[1]),
                                   point1=(width1 * pad_hole_pos[0], height1* pad_hole_pos[1] - pad_hole_radius))
    return sketch