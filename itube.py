from abaqus import *
from abaqusConstants import *
from caeModules import *
from tube import Tube

class _ItubeSet:
    def __init__(self, model_name, part_name, tube_name,
                 pad_name, shearkey_name, shearkey_nums):
        self.tube = tube_name
        self.pad = pad_name
        self.shearkey = shearkey_name
        self.__createSet(model_name, part_name, shearkey_nums)

    def __createSet(self, model_name, part_name, shearkey_nums):
        p = mdb.models[model_name].parts[part_name]
        c = p.cells

        cells = c.getSequenceFromMask(mask=('[#1 ]',), )
        p.Set(cells=cells, name=self.tube)

        cells = c.getSequenceFromMask(mask=('[#2 ]',), )
        p.Set(cells=cells, name=self.pad)

        bi_string = '00'
        for i in range(shearkey_nums):
            bi_string = '1' + bi_string
        hex_string = hex(int(bi_string, 2))[2:]
        shearkeys_mask = '[#' + hex_string + ' ]'
        cells = c.getSequenceFromMask(mask=(shearkeys_mask,), )
        p.Set(cells=cells, name=self.shearkey)

def _Sketch2(model_name, sketch_name, pad_width, pad_height, height1, width1, height2, width2, radius1, thickness):
    sketch = mdb.models[model_name].sketches[sketch_name]
    if pad_width < width1 or pad_height < height1:
        print("pad_width < width1 or pad_height < height1")
        return -1
    vertices = ((0, 0), (0, height1), (width1 - width2, height1), (width1 - width2, height1 - height2),
                (width1, height1 - height2), (width1, 0), (0, 0))
    lines = []
    for i in range(len(vertices) - 1):
        line = sketch.Line(point1=vertices[i], point2=vertices[i + 1])
        lines.append(line)

    sketch.FilletByRadius(radius=radius1, curve1=lines[0], nearPoint1=(0, radius1), curve2=lines[5],
                          nearPoint2=(radius1, 0))
    sketch.FilletByRadius(radius=radius1, curve1=lines[0], nearPoint1=(0, height1 - radius1), curve2=lines[1],
                          nearPoint2=(radius1, height1))
    sketch.FilletByRadius(radius=radius1, curve1=lines[4], nearPoint1=(width1, radius1), curve2=lines[5],
                          nearPoint2=(width1 - radius1, 0))
    sketch.FilletByRadius(radius=radius1 - thickness, curve1=lines[2],
                          nearPoint1=(width1 - width2, height1 - height2 + radius1 - thickness),
                          curve2=lines[3], nearPoint2=(width1 - width2 + radius1 - thickness, height1 - height2))
    sketch.rectangle(point1=(-0.5*(pad_width-width1), -0.5*(pad_height-height1)),
                     point2=(width1 + 0.5*(pad_width-width1), height1 + 0.5*(pad_height-height1)))
    return sketch


class Itube(Tube):

    def __init__(self, length, shearkey_nums, shearkey_h=4, shearkey_w=9, shearkey_s=40, shearkey_p=40,
                 pad_thickness=10, pad_width=154, pad_height=154,
                 model_name='Model-1', part_name='itube',
                 height1=100, width1=100, height2=50, width2=50, radius1=20, thickness=10,
                 tube_name='Set-tube', pad_name='Set-pad', shearkey_name='Set-shearkey'):
        super().__init__(model_name, part_name, height1, width1, height2, width2, radius1, thickness, length=length)
        self.shearkey_nums = shearkey_nums
        self.shearkey_h = shearkey_h
        self.shearkey_w = shearkey_w
        self.shearkey_s = shearkey_s
        self.shearkey_p = shearkey_p
        self.pad_thickness = pad_thickness
        self.pad_width = pad_width
        self.pad_height = pad_height
        self.check_legality()
        self.itube = self.__generatePad()
        self.__generateShearkey()
        self.sets = _ItubeSet(model_name, part_name, tube_name, pad_name, shearkey_name, shearkey_nums)

    def check_legality(self):
        check = (self.pad_thickness <= 0 or self.pad_height <= 0 or self.pad_width <= 0 or
                              self.shearkey_p <=0 or self.shearkey_s <= 0 or self.shearkey_w <= 0 or self.shearkey_h <=0)
        if check: raise ValueError('non positive value')
        check = self.shearkey_w >= self.shearkey_s
        if check: raise ValueError('shearkey too close')
        check = self.pad_width < self.width1 or self.pad_height < self.height1
        if check: raise ValueError('pad less than tube')
        check = (self.pad_thickness + self.shearkey_p + (self.shearkey_nums - 1)
                                  * self.shearkey_s + self.shearkey_w * 0.5 > self.length)
        if check: raise ValueError('itube length too short')

    def __generatePad(self):
        p = mdb.models[self.model_name].parts[self.part_name]
        f1, e1 = p.faces, p.edges
        t = p.MakeSketchTransform(sketchPlane=f1[21], sketchUpEdge=e1[9], sketchPlaneSide=SIDE2,
                                  sketchOrientation=TOP, origin=(0.0, 0.0, 0.0))
        s = mdb.models[self.model_name].ConstrainedSketch(
            name='__profile__',sheetSize=280, gridSpacing=7, transform=t)
        p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
        s = _Sketch2(self.model_name, '__profile__', self.pad_width, self.pad_height, self.height1,
                     self.width1, self.height2, self.width2, self.radius1, self.thickness)
        f, e = p.faces, p.edges
        p.SolidExtrude(sketchPlane=f[21], sketchUpEdge=e[9], sketchPlaneSide=SIDE2,
                       sketchOrientation=TOP, sketch=s, depth=self.pad_thickness, flipExtrudeDirection=OFF,
                       keepInternalBoundaries=ON)
        del mdb.models[self.model_name].sketches['__profile__']
        return p

    def __generateShearkey(self):
        s = mdb.models[self.model_name].ConstrainedSketch(
            name='__profile__', sheetSize=487.98, gridSpacing=12.19,
            transform=(-0.0, 1.0, 0.0, 0.0, -0.0, 1.0, 1.0, 0.0, 0.0, self.width1 - self.radius1, 0.0, self.thickness))
        p = mdb.models[self.model_name].parts[self.part_name]
        p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
        for i in range(self.shearkey_nums):
            pos = i * self.shearkey_s + self.shearkey_p
            s.Arc3Points(point1=(0.0, pos - 0.5*self.shearkey_w),
                         point2=(0.0, pos + 0.5*self.shearkey_w),
                         point3=(-self.shearkey_h, pos))
            s.Line(point1=(0.0, pos - 0.5*self.shearkey_w),
                   point2=(0.0, pos + 0.5*self.shearkey_w))
        e = p.edges
        edges = e.getSequenceFromMask(mask=('[#3ff000 ]',), )
        p.SolidSweep(path=edges, sketchUpEdge=e[54], sketchOrientation=RIGHT,
                     profile=s, keepInternalBoundaries=ON)
        del mdb.models[self.model_name].sketches['__profile__']