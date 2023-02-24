import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import subprocess

# Run MPI example
os.chdir("MPI_example")
subprocess.run("mpiexec -n 4 python mpi_example.py", shell=True)
os.chdir("..")

# Run Jupyter examples
examples = [
    ("Learning_example", "learning_example.ipynb"),
    ("Constellation_example", "constellation.ipynb"),
    ("Sentinel_2_example_notebook", "Sentinel2_example_notebook.ipynb"),
    ("Visualization_example", "visualization_example.ipynb"),
]

for folder, example in examples:
    os.chdir(folder)
    print(f"Running {example}")

    with open(example) as ff:
        nb_in = nbformat.read(example, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        nb_out = ep.preprocess(nb_in)
        print(f"Finished running {example}")
        os.chdir("..")
