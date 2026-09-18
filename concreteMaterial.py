from abaqus import *
from abaqusConstants import *
from caeModules import *
from concrete import Concrete

DEFAULT_COMPRESSION = 0
DEFAULT_COMPRESSION_DAMAGE = 0
DEFAULT_TENSION = 0
DEFAULT_TENSION_DAMAGE = 0
DEFAULT_ELASTICITY = 0
DEFAULT_PLASTICITY = ((38, 0.1, 1.16, 0.6667, 0.005),)
DEFAULT_DENSITY = 0

class ConcreteMaterial:
    def __init__(self, concrete:Concrete, name='CDP',
                 elasticity=DEFAULT_ELASTICITY, plasticity=DEFAULT_PLASTICITY,
                 compression=DEFAULT_COMPRESSION, compressionDamage=DEFAULT_COMPRESSION_DAMAGE,
                 tension=DEFAULT_TENSION, tensionDamage=DEFAULT_TENSION_DAMAGE,
                 density= DEFAULT_DENSITY, usdfld=False):
        self.name = name
        self.elasticity = elasticity
        self.plasticity = plasticity
        self.compression = compression
        self.compressionDamage = compressionDamage
        self.tension = tension
        self.tensionDamage = tensionDamage
        self.density = density
        self.usdlfd = usdfld
        self.__defineMaterial(concrete)
        self.__defineSection(concrete)
        self.__assignSection(concrete)

    def __defineMaterial(self, concrete:Concrete):
        mdb.models[concrete.model_name].Material(name=self.name)
        material = mdb.models[concrete.model_name].materials[self.name]
        material.Elastic(table=self.elasticity)
        material.ConcreteDamagedPlasticity(table=self.plasticity)
        material.concreteDamagedPlasticity.ConcreteCompressionHardening(table=self.compression)
        material.concreteDamagedPlasticity.ConcreteCompressionDamage(table=self.compressionDamage)
        material.concreteDamagedPlasticity.ConcreteTensionStiffening(table=self.tension, type=GFI)
        #material.concreteDamagedPlasticity.ConcreteTensionStiffening(table=self.tension)
        if self.tensionDamage:
            material.concreteDamagedPlasticity.ConcreteTensionDamage(table=self.tensionDamage)
        if self.density:
            material.Density(table=self.density)
        if self.usdlfd:
            material.elastic.setValues(dependencies=1,table=self.elasticity)
            material.UserDefinedField()
            material.Depvar(deleteVar=1, n=1)

    def __defineSection(self, concrete:Concrete):
        mdb.models[concrete.model_name].HomogeneousSolidSection(name=self.name, material=self.name, thickness=None)

    def __assignSection(self, concrete:Concrete):
        p = mdb.models[concrete.model_name].parts[concrete.part_name]
        region = regionToolset.Region(cells=p.cells)
        p.SectionAssignment(region=region, sectionName=self.name, offset=0.0,
                            offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)