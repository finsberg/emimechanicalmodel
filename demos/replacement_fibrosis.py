"""

Åshild Telle / Simula Research Laboratory / 2022

Script for simulating active contraction; over (parts of) one cardiac cycle,
with one or more of the cells replaced with matrix material.

"""

import numpy as np
import dolfin as df
from mpi4py import MPI


from emimechanicalmodel import (
    load_mesh,
    compute_active_component,
    EMIModel,
)

df.parameters["form_compiler"]["cpp_optimize"] = True
df.parameters["form_compiler"]["representation"] = "uflacs"
df.parameters["form_compiler"]["quadrature_degree"] = 4


def replace_cell_with_matrix(volumes, cell_idt):

    assert cell_idt in volumes.array(), \
            "Error: No cell with id {cell_idt} identified."

    volumes_array = volumes.array()[:]

    matrix_idt = 0
    new_array = np.where(volumes_array == cell_idt, 0, volumes_array)
    
    volumes.array()[:] = new_array


# simulate 500 ms with active contraction from the Rice model

num_time_steps = 250

time = np.linspace(0, 500, num_time_steps)  # ms
active_values, scaling_value = compute_active_component(time)
print(scaling_value)
active_values *= 0.28 / scaling_value

# load mesh, subdomains

mesh_file = "meshes/tile_connected_10p0_1_3_3.h5"
mesh, volumes = load_mesh(mesh_file)

# specifiy list of cells to remove, by their identities

cells_to_be_removed = [1, 2]

for cell_idt in cells_to_be_removed:
    new_volumes = replace_cell_with_matrix(volumes, cell_idt)

# initiate EMI model

model = EMIModel(
    mesh,
    volumes,
    experiment="contr",
)

# then run the simulation
for i in range(num_time_steps):
    print(f"Time step {i+1} / {num_time_steps}", flush=True)
    
    time_pt, a_str = time[i], active_values[i]

    model.update_active_fn(a_str)
    model.solve()