"""
This example is a trivial box that must superimpose one of its corner to a marker at the beginning of the movement
and superimpose the same corner to a different marker at the end.
It is designed to show how one can define its own custom constraints function if the provided ones are not
sufficient.

More specifically this example reproduces the behavior of the SUPERIMPOSE_MARKERS constraint.
"""

import biorbd_casadi as biorbd
from casadi import MX
from bioptim import (
    BiorbdModel,
    Node,
    OptimalControlProgram,
    Dynamics,
    DynamicsFcn,
    Objective,
    ObjectiveFcn,
    ConstraintList,
    PenaltyNodeList,
    Bounds,
    QAndQDotBounds,
    InitialGuess,
    OdeSolver,
    BiorbdInterface,
    Solver,
)


def custom_func_track_markers(all_pn: PenaltyNodeList, first_marker: str, second_marker: str, method) -> MX:
    """
    The used-defined objective function (This particular one mimics the ObjectiveFcn.SUPERIMPOSE_MARKERS)
    Except for the last two

    Parameters
    ----------
    all_pn: PenaltyNodeList
        The penalty node elements
    first_marker: str
        The index of the first marker in the bioMod
    second_marker: str
        The index of the second marker in the bioMod
    method: int
        Two identical ways are shown to help the new user to navigate the biorbd API

    Returns
    -------
    The cost that should be minimize in the MX format. If the cost is quadratic, do not put
    the square here, but use the quadratic=True parameter instead
    """

    # Get the index of the markers from their name
    marker_0_idx = all_pn.nlp.model.marker_index(first_marker)
    marker_1_idx = all_pn.nlp.model.marker_index(second_marker)

    if method == 0:
        # Convert the function to the required format and then subtract
        markers = BiorbdInterface.mx_to_cx("markers", all_pn.nlp.model.markers(), all_pn.nlp.states["q"])
        markers_diff = markers[:, marker_1_idx] - markers[:, marker_0_idx]

    else:
        # Do the calculation in biorbd API and then convert to the required format
        markers = all_pn.nlp.model.markers(all_pn.nlp.states["q"].mx)
        markers_diff = markers[marker_1_idx].to_mx() - markers[marker_0_idx].to_mx()
        markers_diff = BiorbdInterface.mx_to_cx("markers", markers_diff, all_pn.nlp.states["q"])

    return markers_diff


def prepare_ocp(biorbd_model_path: str, ode_solver: OdeSolver = OdeSolver.IRK()) -> OptimalControlProgram:
    """
    Prepare the program

    Parameters
    ----------
    biorbd_model_path: str
        The path of the biorbd model
    ode_solver: OdeSolver
        The type of ode solver used

    Returns
    -------
    The ocp ready to be solved
    """

    # --- Options --- #
    # Model path
    biorbd_model = BiorbdModel(biorbd_model_path)

    # Problem parameters
    n_shooting = 30
    final_time = 2
    tau_min, tau_max, tau_init = -100, 100, 0

    # Add objective functions
    objective_functions = Objective(ObjectiveFcn.Lagrange.MINIMIZE_CONTROL, key="tau", weight=100)

    # Dynamics
    expand = False if isinstance(ode_solver, OdeSolver.IRK) else True
    dynamics = Dynamics(DynamicsFcn.TORQUE_DRIVEN, expand=expand)

    # Constraints
    constraints = ConstraintList()
    constraints.add(custom_func_track_markers, node=Node.START, first_marker="m0", second_marker="m1", method=0)
    constraints.add(custom_func_track_markers, node=Node.END, first_marker="m0", second_marker="m2", method=1)

    # Path constraint
    x_bounds = QAndQDotBounds(biorbd_model)
    x_bounds[1:6, [0, -1]] = 0
    x_bounds[2, -1] = 1.57

    # Initial guess
    x_init = InitialGuess([0] * (biorbd_model.nb_q() + biorbd_model.nb_qdot()))

    # Define control path constraint
    u_bounds = Bounds(
        [tau_min] * biorbd_model.nb_generalized_torque(), [tau_max] * biorbd_model.nb_generalized_torque()
    )

    u_init = InitialGuess([tau_init] * biorbd_model.nb_generalized_torque())

    # ------------- #

    return OptimalControlProgram(
        biorbd_model,
        dynamics,
        n_shooting,
        final_time,
        x_init,
        u_init,
        x_bounds,
        u_bounds,
        objective_functions,
        constraints,
        ode_solver=ode_solver,
    )


def main():
    """
    Solve and animate the solution
    """

    model_path = "models/cube.bioMod"
    ocp = prepare_ocp(biorbd_model_path=model_path)

    # --- Solve the program --- #
    sol = ocp.solve(Solver.IPOPT(show_online_optim=True))

    # --- Show results --- #
    sol.animate()


if __name__ == "__main__":
    main()
