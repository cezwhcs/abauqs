from abaqus import *
from abaqusConstants import *
from caeModules import *

from column4p import Column
from partitionColumn4p import PartitionColumn
from meshColumn4p import MeshColumn

from itube import Itube
from partitionItube import PartitionItube
from meshItube import MeshItube

from concrete import Concrete
from partitionConcrete import PartitionConcrete
from meshConcrete import MeshConcrete

from arcShell import ArcShell
from meshArcshell import MeshArcshell

from steelMaterial import SteelMaterial
from concreteMaterial import ConcreteMaterial

from myAssembly4p import MyAssembly
from myAssembly4p import regenerate_assembly
from myStep import MyStep
from myStep import StepType
from myInteraction4p import MyInteraction
from myBoundary4p import MyBoundary

from ManderCDP import Mander

from jobManagement import *
import time

def iw4p_run():
    shearkey_nums = [2, 3, 5]
    itube_shearkey_w = [9.28, 9.65, 9.78]
    itube_shearkey_h = [4.46, 4.25, 4.33]
    column_shearkey_w = [9.08, 9.04, 8.59]
    column_shearkey_h = [3.85, 3.85, 3.79]
    confine_factor = [0.41, 0.8, 0.8]

    for i, num in enumerate(shearkey_nums):
        itube_length = num * 40 + 30
        itube = Itube(length=itube_length, shearkey_nums=num, shearkey_w=itube_shearkey_w[i], shearkey_h=itube_shearkey_h[i])
        column = Column(shearkey_nums=num, shearkey_w=column_shearkey_w[i], shearkey_h=column_shearkey_h[i])
        concrete = Concrete(itube, column)
        loadShell = ArcShell()
        assembly1 = MyAssembly(itube, column, concrete, loadShell)
        step1 = MyStep(assembly1)
        interaction1 = MyInteraction(assembly1)
        MyBoundary(assembly1, step1)

        SteelMaterial(column)
        myPartitionColumn = PartitionColumn(column)
        MeshColumn(column, myPartitionColumn)

        SteelMaterial(itube)
        myPartitionItube= PartitionItube(itube)
        MeshItube( itube, myPartitionItube)

        mander = Mander(confine_factor=confine_factor[i])
        ConcreteMaterial(concrete, 'CDP', elasticity=mander.elasticity, plasticity=mander.plasticity,
                         compression=mander.compression_hardening, compressionDamage=mander.compression_damage, tension=mander.tension)
        myPartitionConcrete = PartitionConcrete(itube, column, concrete)
        MeshConcrete(itube, column, concrete, myPartitionConcrete)

        SteelMaterial(loadShell)
        MeshArcshell(loadShell, 5)

        regenerate_assembly(assembly1)

        job_name = f"{num}w4p"
        CreateJobINP(assembly1, job_name=job_name, cpu_nums=12, gpu_nums=1)
        start_time = time.time()
        submitJob(job_name)
        print(f"start compute {num}w4p")
        wait_job(job_name)
        end_time = time.time()
        used_time = end_time - start_time
        print(f"{job_name} completed, used time: {used_time // 3600} : {(used_time % 3600) // 60} : {used_time % 60}")
        resetModel()