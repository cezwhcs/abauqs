from abaqus import *
from abaqusConstants import *
from caeModules import *

from column3p import Column
from partitionColumn3p import PartitionColumn
from meshColumn3p import MeshColumn

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

from myAssembly3p import MyAssembly
from myAssembly3p import regenerate_assembly
from myStep import MyStep
from myInteraction3p import MyInteraction
from myBoundary3p import MyBoundary
from ManderCDP import Mander
from jobManagement import *
import time


def iw3p_parameter2_run():
    shearkey_nums = 5
    itube_shearkey_w = 9
    itube_shearkey_h = 4
    column_shearkey_w = 9
    column_shearkey_h = 4
    itube_length = 230
    column_lengthes = [1000, 1200, 1400, 1600, 1800]

    for length in column_lengthes:

        itube = Itube(length=itube_length, shearkey_nums=shearkey_nums, shearkey_w=itube_shearkey_w, shearkey_h=itube_shearkey_h)
        column = Column(shearkey_nums=shearkey_nums, shearkey_w=column_shearkey_w, shearkey_h=column_shearkey_h, length = length)
        concrete = Concrete(itube, column)
        loadShell = ArcShell(radius=30, length=itube.pad_width)
        assembly1 = MyAssembly(itube, column, concrete, loadShell)
        step1 = MyStep(assembly1)
        interaction1 = MyInteraction(assembly1)
        MyBoundary(assembly1, step1, displacement=-70.0 * (length - 40) / 760.0)

        SteelMaterial(column)
        myPartitionColumn = PartitionColumn(column)
        MeshColumn(column, myPartitionColumn)

        SteelMaterial(itube)
        myPartitionItube= PartitionItube(itube)
        MeshItube( itube, myPartitionItube)

        mander = Mander()
        ConcreteMaterial(concrete, 'CDP', elasticity=mander.elasticity, plasticity=mander.plasticity, compression=mander.compression_hardening,
                         compressionDamage=mander.compression_damage, tension=mander.tension)
        myPartitionConcrete = PartitionConcrete(itube, column, concrete)
        MeshConcrete(itube, column, concrete, myPartitionConcrete, grout_layer_elements=0)

        SteelMaterial(loadShell)
        MeshArcshell(loadShell)

        regenerate_assembly(assembly1)

        job_name = f"5w3p-parameter2-{length}"
        CreateJobINP(assembly1, job_name=job_name, cpu_nums=12, gpu_nums=1)
        start_time = time.time()
        submitJob(job_name)
        print(f"start compute {job_name}")
        wait_job(job_name)
        end_time = time.time()
        used_time = end_time - start_time
        file_path = f"{job_name}.txt"
        write_to_file(file_path, f"{job_name} completed, used time: {used_time // 3600} : {(used_time % 3600) // 60} : {used_time % 60}")
        resetModel()

iw3p_parameter2_run()