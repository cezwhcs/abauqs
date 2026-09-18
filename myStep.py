from abaqus import *
from abaqusConstants import *
from caeModules import *
from myAssembly3p import MyAssembly
from enum import Enum
class StepType(Enum):
    STATIC_STEP = 0
    STATIC_RIKS_STEP = 1

class MyStep:
    def __init__(self, myAssembly:MyAssembly, step_type=StepType.STATIC_STEP, step_name='step-1', previous_step_name='Initial', maxNumInc=int(10000),
                 initInc=0.005, minInc=1e-15, maxInc=0.02, output_increment=0.01, timeMarks=OFF, totalArcLength=1):
        self.step_type = step_type
        self.previous_step_name = previous_step_name
        self.step_name = step_name
        self.maxNumInc = maxNumInc
        self.initInc = initInc
        self.minInc = minInc
        self.maxInc = maxInc
        self.output_increment = output_increment
        self.timeMarks = timeMarks
        self.totalArcLength = totalArcLength
        self.__create(myAssembly)
        self.__output(myAssembly)

    def __create(self, myAssembly:MyAssembly):
        if self.step_type == StepType.STATIC_STEP:
            mdb.models[myAssembly.model_name].StaticStep(name=self.step_name, previous=self.previous_step_name, maxNumInc=self.maxNumInc,
                                             initialInc=self.initInc, minInc=self.minInc, maxInc=self.maxInc, nlgeom=ON)
        elif self.step_type == StepType.STATIC_RIKS_STEP:
            mdb.models['Model-1'].StaticRiksStep(name=self.step_name, previous=self.previous_step_name,
                                                 maxLPF=1.0, maxNumInc=self.maxNumInc, initialArcInc=self.initInc, minArcInc=self.minInc,
                                                 maxArcInc=self.maxInc, totalArcLength=self.totalArcLength, nlgeom=ON)

    def __output(self, myAssembly:MyAssembly):
        if self.step_type == StepType.STATIC_STEP:
            mdb.models[myAssembly.model_name].fieldOutputRequests['F-Output-1'].setValues(variables=(
                'S', 'PE', 'PEEQ', 'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 'CDISP','DAMAGEC', 'DAMAGET', 'SDV', 'STATUS'),
                timeInterval=self.output_increment, timeMarks=self.timeMarks)
            regionDef = mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.load_point_name]
            mdb.models[myAssembly.model_name].historyOutputRequests['H-Output-1'].setValues(variables=(
                'U2', 'RF2'), timeInterval=self.output_increment, timeMarks=self.timeMarks, region=regionDef,
                sectionPoints=DEFAULT, rebar=EXCLUDE)
        elif self.step_type == StepType.STATIC_RIKS_STEP:
            mdb.models[myAssembly.model_name].FieldOutputRequest(name='F-Output-1',createStepName=self.step_name,
                                                                 variables=('S', 'E', 'PE', 'U', 'RF', 'DAMAGEC', 'DAMAGET'))
            regionDef = mdb.models[myAssembly.model_name].rootAssembly.sets[myAssembly.sets.load_point_name]
            mdb.models[myAssembly.model_name].HistoryOutputRequest(name='H-Output-1',createStepName=self.step_name,
                                                                   variables=('U2', 'RF2'), region=regionDef,
                                                                   sectionPoints=DEFAULT, rebar=EXCLUDE)
