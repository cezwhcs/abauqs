from abaqus import *
from abaqusConstants import *
from caeModules import *
from myAssembly4p import MyAssembly

class MyInteraction:
    def __init__(self, myAssembly:MyAssembly, friction_ratio=0.4, friction2_ratio=0.15, createStepName='Initial',
                 interactionProperties_name='IntProp-1', interaction_name='Int-1',
                 interactionProperties2_name='IntProp-2', interaction2_name='Int-2',
                 load_constraint_name='constrain-load', support_constraint_name='constraint-support'):
        self.createStepName = createStepName
        self.friction_ratio = friction_ratio
        self.friction2_ratio = friction2_ratio
        self.interactionProperties_name = interactionProperties_name
        self.interactionProperties2_name = interactionProperties2_name
        self.interaction_name = interaction_name
        self.interaction2_name = interaction2_name
        self.load_constraint_name = load_constraint_name
        self.support_constraint_name = support_constraint_name
        self.__defineInteractionProperties(myAssembly)
        self.__defineInteraction(myAssembly)
        self.__defineCoupling(myAssembly)

    def __defineInteractionProperties(self, myAssembly:MyAssembly):
        #IntProp - 1
        mdb.models[myAssembly.model_name].ContactProperty(self.interactionProperties_name)
        mdb.models[myAssembly.model_name].interactionProperties[self.interactionProperties_name].NormalBehavior(
            pressureOverclosure=HARD, allowSeparation=ON,
            constraintEnforcementMethod=DEFAULT)
        mdb.models[myAssembly.model_name].interactionProperties[self.interactionProperties_name].TangentialBehavior(
            formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF,
            pressureDependency=OFF, temperatureDependency=OFF, dependencies=0,
            table=((self.friction_ratio,),), shearStressLimit=None, maximumElasticSlip=FRACTION,
            fraction=0.005, elasticSlipStiffness=None)

        mdb.models[myAssembly.model_name].ContactProperty(self.interactionProperties2_name)
        mdb.models[myAssembly.model_name].interactionProperties[self.interactionProperties2_name].NormalBehavior(
            pressureOverclosure=HARD, allowSeparation=ON,
            constraintEnforcementMethod=DEFAULT)
        mdb.models[myAssembly.model_name].interactionProperties[self.interactionProperties2_name].TangentialBehavior(
            formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF,
            pressureDependency=OFF, temperatureDependency=OFF, dependencies=0,
            table=((self.friction2_ratio,),), shearStressLimit=None, maximumElasticSlip=FRACTION,
            fraction=0.005, elasticSlipStiffness=None)

    def __defineInteraction(self, myAssembly:MyAssembly):
        mdb.models[myAssembly.model_name].ContactStd(name=self.interaction_name, createStepName=self.createStepName)
        mdb.models[myAssembly.model_name].interactions[self.interaction_name].includedPairs.setValuesInStep(
            stepName=self.createStepName, useAllstar=ON)
        mdb.models[myAssembly.model_name].interactions[self.interaction_name].contactPropertyAssignments.appendInStep(
            stepName=self.createStepName, assignments=((GLOBAL, SELF, self.interactionProperties_name),))

        r11 = mdb.models[myAssembly.model_name].rootAssembly.surfaces[myAssembly.sets.load_plane_name]
        r12 = mdb.models[myAssembly.model_name].rootAssembly.surfaces[myAssembly.sets.hold_plane_name]
        mdb.models[myAssembly.model_name].interactions[self.interaction_name].contactPropertyAssignments.appendInStep(
            stepName='Initial', assignments=((r11, r12, self.interactionProperties2_name),))

    def __defineCoupling(self, myAssembly:MyAssembly):
        a = mdb.models[myAssembly.model_name].rootAssembly
        region1 = a.sets[myAssembly.sets.load_point_name]
        region2 = a.sets[myAssembly.sets.load_plane_name]
        mdb.models[myAssembly.model_name].RigidBody(name=self.load_constraint_name, refPointRegion=region1, bodyRegion=region2)

        region1 = a.sets[myAssembly.sets.support_point_name]
        region2 = a.surfaces[myAssembly.sets.support_plane_name]
        mdb.models[myAssembly.model_name].Coupling(name=self.support_constraint_name, controlPoint=region1,
                                       surface=region2, influenceRadius=WHOLE_SURFACE, couplingType=KINEMATIC,
                                       alpha=0.0, localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

