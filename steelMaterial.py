from abaqus import *
from abaqusConstants import *
from caeModules import *
import column4p
import column3p
from itube import Itube
from arcShell import ArcShell

DEFAULT_COLUMN_ELASTICITY = ((209284.0, 0.3), )
DEFAULT_COLUMN_PLASTICITY = ((297.549172, 0.0), (314.0945015, 0.000144539), (330.3550452, 0.000202529), (346.4212817, 0.000265774),
                             (362.4796475, 0.000351647), (378.0577569, 0.000446055), (393.5676041, 0.000562888), (408.5674082, 0.000701841),
                             (423.1913488, 0.000898773), (436.9551053, 0.001160275), (448.3261728, 0.001535357), (454.8687775, 0.00209785),
                             (458.6682264, 0.002838479), (481.9110795, 0.00708633), (503.1864766, 0.013124153), (521.9732644, 0.019136393),
                             (538.4968431, 0.025123885), (552.887138, 0.031085273), (565.1458489, 0.037021448), (575.553892, 0.042930724),
                             (584.2492318, 0.048813059), (591.2442186, 0.054531863), (596.8803312, 0.060172043), (602.1500009, 0.067030132),
                             (605.7419383, 0.072030132), (609.0838756, 0.077030132), (612.175813, 0.082030132), (615.0177503, 0.087030132),
                             (617.6096876, 0.092030132), (619.951625, 0.097030132), (622.2935623, 0.102030132), (624.5354997, 0.107030132),
                             (626.677437, 0.112030132), (628.7193744, 0.117030132), (630.6613117, 0.122030132), (632.5032491, 0.127030132),
                             (634.2451864, 0.132030132), (635.8871238, 0.137030132), (637.4290611, 0.142030132), (638.8709985, 0.147030132),
                             (640.2129358, 0.152030132), (641.4548732, 0.157030132), (642.5968105, 0.162030132), (643.6387479, 0.167030132),
                             (644.5806852, 0.172030132), (645.4226226, 0.177030132), (646.1645599, 0.182030132), (646.8064972, 0.187030132),
                             (647.3484346, 0.192030132), (647.7903719, 0.197030132), (648.1323093, 0.202030132), (648.3742466, 0.207030132),
                             (648.516184, 0.212030132), (648.5581213, 0.217030132), (648.5581213, 0.222030132))

DEFAULT_ITUBE_ELASTICITY = ((206506.0, 0.3), )
DEFAULT_ITUBE_PLASTICITY = ((387.0780564, 0.0), (410.5382646, 0.000176915), (433.9882738, 0.000296734), (457.2729719, 0.000433209),
                            (480.4181193, 0.000589091), (503.4917899, 0.000764522), (526.305164, 0.000973371), (548.5539558, 0.001255499),
                            (568.1793537, 0.001770514), (583.4074736, 0.002475763), (595.0780883, 0.003202435), (603.5493984, 0.003951153),
                            (624.868431, 0.007218368), (640.0467631, 0.010858178), (652.8875973, 0.014502545), (664.7092234, 0.019170811),
                            (675.4508714, 0.024512098), (684.5781177, 0.029832568), (692.2125646, 0.035131841), (698.6595039, 0.040408683),
                            (703.6501548, 0.045548012), (708.0055078, 0.050548012), (711.8608607, 0.055548012), (715.2162137, 0.060548012),
                            (718.0715667, 0.065548012), (720.4269196, 0.070548012), (722.2822726, 0.075548012), (723.6376255, 0.080548012),
                            (724.4929785, 0.085548012), (724.8483315, 0.090548012), (724.8483315, 0.095548012))

DEFAULT_ELASTICITY = ((206000.0, 0.3), )
DEFAULT_DENSITY = ((7.85e-09,),)
DEFAULT_SET = 0

class SteelMaterial:
    def __init__(self, steel, elasticity=DEFAULT_SET, plasticity=DEFAULT_SET, density=DEFAULT_DENSITY, name=''):
        if type(steel) == column4p.Column or type(steel) == column3p.Column:
            self.elasticity = DEFAULT_COLUMN_ELASTICITY if elasticity == DEFAULT_SET else elasticity
            self.plasticity = DEFAULT_COLUMN_PLASTICITY if plasticity == DEFAULT_SET else plasticity
            self.name = name if name else 'steel-column'
        elif type(steel) == Itube:
            self.elasticity = DEFAULT_ITUBE_ELASTICITY if elasticity == DEFAULT_SET else elasticity
            self.plasticity = DEFAULT_ITUBE_PLASTICITY if plasticity == DEFAULT_SET else plasticity
            self.name = name if name else 'steel-itube'
        elif type(steel) == ArcShell:
            self.elasticity = DEFAULT_ELASTICITY if elasticity == DEFAULT_SET else elasticity
            self.name = name if name else 'steel-arcShell'
        else:
            ValueError("tube type error")
        self.density = density
        self.__defineMaterial(steel)
        self.__defineSection(steel)
        self.__assignSection(steel)

    def __defineMaterial(self, steel):
        material = mdb.models[steel.model_name].Material(name=self.name)
        material.Elastic(table=self.elasticity)
        if type(steel) != ArcShell:
            material.Plastic(scaleStress=None, table=self.plasticity)
        material.Density(table=self.density)

    def __defineSection(self, steel):
        if type(steel) == ArcShell:
            mdb.models[steel.model_name].HomogeneousShellSection(name=self.name,
                                                          preIntegrate=OFF, material=self.name, thicknessType=UNIFORM,
                                                          thickness=1.0, thicknessField='', nodalThicknessField='',
                                                          idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT,
                                                          thicknessModulus=None, temperature=GRADIENT, useDensity=OFF,
                                                          integrationRule=SIMPSON, numIntPts=5)
        else:
            mdb.models[steel.model_name].HomogeneousSolidSection(name=self.name, material=self.name, thickness=None)
    def __assignSection(self, steel):
        p = mdb.models[steel.model_name].parts[steel.part_name]

        if type(steel) == ArcShell:
            region = p.sets[steel.sets.geometry_set_name]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)
        else:
            region = p.sets[steel.sets.tube]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)

            region = p.sets[steel.sets.pad]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)

            region = p.sets[steel.sets.shearkey]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)

        if type(steel) == column4p.Column:
            region = p.sets[steel.sets.pad2]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)

            region = p.sets[steel.sets.pad3]
            p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)