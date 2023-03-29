import papermill as pm
import subprocess

# Run MPI example
mpi_example_path = "MPI_example/mpi_example.py"
subprocess.run(f"mpiexec -n 4 python {mpi_example_path}", shell=True)

# Run Jupyter examples
examples = [
    ("Learning_example", "learning_example.ipynb"),
    ("Constellation_example", "constellation.ipynb"),
    ("Sentinel_2_example_notebook", "Sentinel2_example_notebook.ipynb"),
    ("Visualization_example", "visualization_example.ipynb"),
]

for folder, example in examples:
    print(f"Running {example}")
    input_nb_path = f"./examples/{folder}/{example}"
    # execute the notebook using Papermill
    pm.execute_notebook(input_nb_path, input_nb_path)
