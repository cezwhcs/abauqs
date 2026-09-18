from abaqus import *
from abaqusConstants import *
from caeModules import *
from myAssembly3p import MyAssembly
from myStep import MyStep

class MyBoundary:
    def __init__(self, myAssembly:MyAssembly, myStep:MyStep, displacement=-70,
                 symmetry_boundary_name='BC-symmetry', load_boundary_name='BC-load', support_boundary_name='BC-support'):
        self.symmetry_boundary_name = symmetry_boundary_name
        self.load_boundary_name = load_boundary_name
        self.support_boundary_name = support_boundary_name
        self.displacement = displacement
        self.__boundaryCondition(myAssembly, myStep)

    def __boundaryCondition(self, myAssembly:MyAssembly, myStep:MyStep):
        a = mdb.models[myAssembly.model_name].rootAssembly

        region = a.sets[myAssembly.sets.symmetry_plane_name]
        mdb.models[myAssembly.model_name].ZsymmBC(name=self.symmetry_boundary_name, createStepName='Initial', region=region, localCsys=None)

        region = a.sets[myAssembly.sets.load_point_name]
        mdb.models[myAssembly.model_name].DisplacementBC(
            name=self.load_boundary_name, createStepName=myStep.step_name, region=region,
            u1=SET, u2=self.displacement, u3=SET, ur1=SET, ur2=SET, ur3=SET,
            amplitude=SET, distributionType=UNIFORM, fieldName='', localCsys=None)

        region = a.sets[myAssembly.sets.support_point_name]
        mdb.models[myAssembly.model_name].DisplacementBC(
            name=self.support_boundary_name, createStepName='Initial',region=region,
            u1=SET, u2=SET, u3=UNSET, ur1=UNSET, ur2=SET, ur3=SET,
            amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)