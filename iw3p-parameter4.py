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
from for_parameter4 import for_paramerter4_run
from jobManagement import *
import time
from column_transfer_to_shell import column_shell

def iw3p_parameter4_run():
    shearkey_nums = 5
    itube_length = 230
    column_length = 3000
    force_ratio = {0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1}

    for ratio in force_ratio:
        itube = Itube(length=itube_length, shearkey_nums=shearkey_nums)
        column = Column(shearkey_nums=shearkey_nums, length=column_length)
        concrete = Concrete(itube, column)
        loadShell = ArcShell(radius=30, length=itube.pad_width)
        assembly1 = MyAssembly(itube, column, concrete, loadShell)
        step1 = MyStep(assembly1)
        interaction1 = MyInteraction(assembly1)
        myBoundary = MyBoundary(assembly1, step1)

        column_material = SteelMaterial(column)
        myPartitionColumn = PartitionColumn(column)
        myMeshColumn = MeshColumn(column, myPartitionColumn)

        SteelMaterial(itube)
        myPartitionItube= PartitionItube(itube)
        MeshItube( itube, myPartitionItube)

        mander = Mander()
        ConcreteMaterial(concrete, 'CDP', elasticity=mander.elasticity, plasticity=mander.plasticity,
                         compression=mander.compression_hardening,
                         compressionDamage=mander.compression_damage, tension=mander.tension)
        myPartitionConcrete = PartitionConcrete(itube, column, concrete)
        MeshConcrete(itube, column, concrete, myPartitionConcrete)

        SteelMaterial(loadShell)
        MeshArcshell(loadShell)

        column_shell(assembly1, column_material, column, myPartitionColumn, myMeshColumn, itube)

        regenerate_assembly(assembly1)
        for_paramerter4_run(myAssembly=assembly1, myBoundary=myBoundary, myStep=step1, myInteraction=interaction1,
                            column=column, U2=-70, force_ratio=ratio, axis_m=False)
        regenerate_assembly(assembly1)

        job_name = f"5w3p-parameter4-ratio{ratio}"
        CreateJobINP(assembly1, job_name=job_name, cpu_nums=12, gpu_nums=1)
        start_time = time.time()
        submitJob(job_name)
        print(f"start compute {job_name}")
        wait_job(job_name)
        end_time = time.time()
        used_time = end_time - start_time
        file_path = f"{job_name}.txt"
        write_to_file(file_path,
                      f"{job_name} completed, used time: {used_time // 3600} : {(used_time % 3600) // 60} : {used_time % 60}")
        resetModel()

iw3p_parameter4_run()