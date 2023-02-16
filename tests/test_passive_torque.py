import pytest

import numpy as np
from casadi import MX, SX
from bioptim import (
    ConfigureProblem,
    ControlType,
    RigidBodyDynamics,
    BiorbdModel,
    NonLinearProgram,
    DynamicsFcn,
    Dynamics,
    ConstraintList,
    OdeSolver,
    Solver,
    NodeMappingIndex,
)
from bioptim.optimization.optimization_vector import OptimizationVector
from .utils import TestUtils
import os


class OptimalControlProgram:
    def __init__(self, nlp):
        self.n_phases = 1
        self.nlp = [nlp]
        self.v = OptimizationVector(self)
        self.implicit_constraints = ConstraintList()


@pytest.mark.parametrize("cx", [MX, SX])
@pytest.mark.parametrize(
    "with_passive_torque",
    [
        False,
        True,
    ],
)
@pytest.mark.parametrize(
    "rigidbody_dynamics",
    [
        RigidBodyDynamics.ODE,
    ],
)
def test_torque_driven_with_passive_torque(with_passive_torque, cx, rigidbody_dynamics):
    # Prepare the program
    nlp = NonLinearProgram()
    nlp.model = BiorbdModel(
        TestUtils.bioptim_folder() + "/examples/getting_started/models/2segments_4dof_2contacts.bioMod"
    )
    nlp.ns = 5
    nlp.cx = cx
    nlp.x_scaling = {}
    nlp.xdot_scaling = {}
    nlp.u_scaling = {}

    nlp.x_bounds = np.zeros((nlp.model.nb_q * 3, 1))
    nlp.u_bounds = np.zeros((nlp.model.nb_q, 1))
    ocp = OptimalControlProgram(nlp)
    nlp.control_type = ControlType.CONSTANT
    NonLinearProgram.add(
        ocp,
        "dynamics_type",
        Dynamics(
            DynamicsFcn.TORQUE_DRIVEN, rigidbody_dynamics=rigidbody_dynamics, with_passive_torque=with_passive_torque
        ),
        False,
    )
    phase_index = [i for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "phase_idx", phase_index, False)

    states_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    states_dot_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    controls_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "states_phase_mapping_idx", states_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "states_dot_phase_mapping_idx", states_dot_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "controls_phase_mapping_idx", controls_phase_mapping_idx, False)

    np.random.seed(42)

    # Prepare the dynamics
    ConfigureProblem.initialize(ocp, nlp)

    # Test the results
    states = np.random.rand(nlp.states.shape, nlp.ns)
    controls = np.random.rand(nlp.controls.shape, nlp.ns)
    params = np.random.rand(nlp.parameters.shape, nlp.ns)
    x_out = np.array(nlp.dynamics_func(states, controls, params))
    if rigidbody_dynamics == RigidBodyDynamics.ODE:
        if with_passive_torque:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.6118529, 0.785176, 0.6075449, 0.8083973, -5.0261535, -10.5570666, 18.569191, 24.2237134],
            )
        else:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [
                    0.61185289,
                    0.78517596,
                    0.60754485,
                    0.80839735,
                    -0.30241366,
                    -10.38503791,
                    1.60445173,
                    35.80238642,
                ],
            )
    elif rigidbody_dynamics == RigidBodyDynamics.DAE_FORWARD_DYNAMICS:
        if with_passive_torque:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.6118529, 0.785176, 0.6075449, 0.8083973, 0.3886773, 0.5426961, 0.7722448, 0.7290072],
            )
        else:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.6118529, 0.785176, 0.6075449, 0.8083973, 0.3886773, 0.5426961, 0.7722448, 0.7290072],
            )
    elif rigidbody_dynamics == RigidBodyDynamics.DAE_INVERSE_DYNAMICS:
        if with_passive_torque:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.6118529, 0.785176, 0.6075449, 0.8083973, 0.3886773, 0.5426961, 0.7722448, 0.7290072],
            )
        else:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.6118529, 0.785176, 0.6075449, 0.8083973, 0.3886773, 0.5426961, 0.7722448, 0.7290072],
            )


@pytest.mark.parametrize("cx", [MX, SX])
@pytest.mark.parametrize("with_passive_torque", [False, True])
def test_torque_derivative_driven_with_passive_torque(with_passive_torque, cx):
    # Prepare the program
    nlp = NonLinearProgram()
    nlp.model = BiorbdModel(
        TestUtils.bioptim_folder() + "/examples/getting_started/models/2segments_4dof_2contacts.bioMod"
    )
    nlp.ns = 5
    nlp.cx = cx
    nlp.x_scaling = {}
    nlp.xdot_scaling = {}
    nlp.u_scaling = {}

    nlp.x_bounds = np.zeros((nlp.model.nb_q * 3, 1))
    nlp.u_bounds = np.zeros((nlp.model.nb_q, 1))
    ocp = OptimalControlProgram(nlp)
    nlp.control_type = ControlType.CONSTANT

    NonLinearProgram.add(
        ocp,
        "dynamics_type",
        Dynamics(DynamicsFcn.TORQUE_DERIVATIVE_DRIVEN, with_passive_torque=with_passive_torque),
        False,
    )

    phase_index = [i for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "phase_idx", phase_index, False)

    states_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    states_dot_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    controls_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "states_phase_mapping_idx", states_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "states_dot_phase_mapping_idx", states_dot_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "controls_phase_mapping_idx", controls_phase_mapping_idx, False)

    np.random.seed(42)

    # Prepare the dynamics
    ConfigureProblem.initialize(ocp, nlp)

    # Test the results
    states = np.random.rand(nlp.states.shape, nlp.ns)
    controls = np.random.rand(nlp.controls.shape, nlp.ns)
    params = np.random.rand(nlp.parameters.shape, nlp.ns)
    x_out = np.array(nlp.dynamics_func(states, controls, params))
    if with_passive_torque:
        np.testing.assert_almost_equal(
            x_out[:, 0],
            [
                0.6118529,
                0.785176,
                0.6075449,
                0.8083973,
                -5.0261535,
                -10.5570666,
                18.569191,
                24.2237134,
                0.3886773,
                0.5426961,
                0.7722448,
                0.7290072,
            ],
        )
    else:
        np.testing.assert_almost_equal(
            x_out[:, 0],
            [
                0.61185289,
                0.78517596,
                0.60754485,
                0.80839735,
                -0.30241366,
                -10.38503791,
                1.60445173,
                35.80238642,
                0.38867729,
                0.54269608,
                0.77224477,
                0.72900717,
            ],
        )


@pytest.mark.parametrize("cx", [MX, SX])
@pytest.mark.parametrize("with_passive_torque", [False, True])
def test_torque_activation_driven_with_passive_torque(with_passive_torque, cx):
    # Prepare the program
    nlp = NonLinearProgram()
    nlp.model = BiorbdModel(
        TestUtils.bioptim_folder() + "/examples/getting_started/models/2segments_4dof_2contacts.bioMod"
    )
    nlp.ns = 5
    nlp.cx = cx
    nlp.x_scaling = {}
    nlp.xdot_scaling = {}
    nlp.u_scaling = {}
    nlp.x_bounds = np.zeros((nlp.model.nb_q * 2, 1))
    nlp.u_bounds = np.zeros((nlp.model.nb_q, 1))
    ocp = OptimalControlProgram(nlp)
    nlp.control_type = ControlType.CONSTANT
    NonLinearProgram.add(
        ocp,
        "dynamics_type",
        Dynamics(DynamicsFcn.TORQUE_ACTIVATIONS_DRIVEN, with_passive_torque=with_passive_torque),
        False,
    )
    phase_index = [i for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "phase_idx", phase_index, False)

    states_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    states_dot_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    controls_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "states_phase_mapping_idx", states_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "states_dot_phase_mapping_idx", states_dot_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "controls_phase_mapping_idx", controls_phase_mapping_idx, False)

    np.random.seed(42)

    # Prepare the dynamics
    ConfigureProblem.initialize(ocp, nlp)

    # Test the results
    states = np.random.rand(nlp.states.shape, nlp.ns)
    controls = np.random.rand(nlp.controls.shape, nlp.ns)
    params = np.random.rand(nlp.parameters.shape, nlp.ns)
    x_out = np.array(nlp.dynamics_func(states, controls, params))
    if with_passive_torque:
        np.testing.assert_almost_equal(
            x_out[:, 0],
            [
                6.1185289472e-01,
                7.8517596139e-01,
                6.0754485190e-01,
                8.0839734812e-01,
                -2.8550037341e01,
                -5.8375374025e01,
                1.4440375924e02,
                3.6537329536e03,
            ],
            decimal=6,
        )
    else:
        np.testing.assert_almost_equal(
            x_out[:, 0],
            [
                6.11852895e-01,
                7.85175961e-01,
                6.07544852e-01,
                8.08397348e-01,
                -2.38262975e01,
                -5.82033454e01,
                1.27439020e02,
                3.66531163e03,
            ],
            decimal=5,
        )


@pytest.mark.parametrize("cx", [MX, SX])
@pytest.mark.parametrize("with_passive_torque", [False, True])
@pytest.mark.parametrize("rigidbody_dynamics", [RigidBodyDynamics.ODE])
def test_muscle_driven_with_passive_torque(with_passive_torque, rigidbody_dynamics, cx):
    # Prepare the program
    nlp = NonLinearProgram()
    nlp.model = BiorbdModel(TestUtils.bioptim_folder() + "/examples/muscle_driven_ocp/models/arm26_with_contact.bioMod")
    nlp.ns = 5
    nlp.cx = cx
    nlp.x_scaling = {}
    nlp.xdot_scaling = {}
    nlp.u_scaling = {}
    nlp.x_bounds = np.zeros((nlp.model.nb_q * 2 + nlp.model.nb_muscles, 1))
    nlp.u_bounds = np.zeros((nlp.model.nb_muscles, 1))

    ocp = OptimalControlProgram(nlp)
    nlp.control_type = ControlType.CONSTANT
    NonLinearProgram.add(
        ocp,
        "dynamics_type",
        Dynamics(
            DynamicsFcn.MUSCLE_DRIVEN,
            rigidbody_dynamics=rigidbody_dynamics,
            with_passive_torque=with_passive_torque,
        ),
        False,
    )
    phase_index = [i for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "phase_idx", phase_index, False)

    states_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    states_dot_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    controls_phase_mapping_idx = [NodeMappingIndex(i, None) for i in range(ocp.n_phases)]
    NonLinearProgram.add(ocp, "states_phase_mapping_idx", states_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "states_dot_phase_mapping_idx", states_dot_phase_mapping_idx, False)
    NonLinearProgram.add(ocp, "controls_phase_mapping_idx", controls_phase_mapping_idx, False)

    np.random.seed(42)

    # Prepare the dynamics
    if rigidbody_dynamics == RigidBodyDynamics.DAE_INVERSE_DYNAMICS:
        pass
    ConfigureProblem.initialize(ocp, nlp)

    # Test the results
    states = np.random.rand(nlp.states.shape, nlp.ns)
    controls = np.random.rand(nlp.controls.shape, nlp.ns)
    params = np.random.rand(nlp.parameters.shape, nlp.ns)
    x_out = np.array(nlp.dynamics_func(states, controls, params))

    if rigidbody_dynamics == RigidBodyDynamics.DAE_INVERSE_DYNAMICS:
        if with_passive_torque:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.183405, 0.611853, 0.785176, 0.388677, 0.542696, 0.772245],
                decimal=6,
            )
        else:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [0.183405, 0.611853, 0.785176, 0.388677, 0.542696, 0.772245],
                decimal=6,
            )
    else:
        if with_passive_torque:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [
                    1.8340450985e-01,
                    6.1185289472e-01,
                    7.8517596139e-01,
                    -5.3408086130e00,
                    1.6890917494e02,
                    -5.4766884856e02,
                ],
                decimal=6,
            )
        else:
            np.testing.assert_almost_equal(
                x_out[:, 0],
                [
                    1.83404510e-01,
                    6.11852895e-01,
                    7.85175961e-01,
                    -4.37708456e00,
                    1.33221135e02,
                    -4.71307550e02,
                ],
                decimal=6,
            )


@pytest.mark.parametrize(
    "rigidbody_dynamics",
    [
        RigidBodyDynamics.DAE_FORWARD_DYNAMICS,
        RigidBodyDynamics.DAE_INVERSE_DYNAMICS,
    ],
)
@pytest.mark.parametrize(
    "with_passive_torque",
    [
        False,
        True,
    ],
)
def test_pendulum_passive_torque(rigidbody_dynamics, with_passive_torque):
    from bioptim.examples.torque_driven_ocp import pendulum_with_passive_torque as ocp_module

    bioptim_folder = os.path.dirname(ocp_module.__file__)

    # Define the problem
    biorbd_model_path = bioptim_folder + "/models/pendulum_with_passive_torque.bioMod"
    final_time = 0.1
    n_shooting = 5

    ocp = ocp_module.prepare_ocp(
        biorbd_model_path,
        final_time,
        n_shooting,
        rigidbody_dynamics=RigidBodyDynamics.ODE,
        with_passive_torque=with_passive_torque,
    )
    solver = Solver.IPOPT()

    # solver.set_maximum_iterations(10)
    sol = ocp.solve(solver)

    # Check some results
    q, qdot, tau = sol.states["q"], sol.states["qdot"], sol.controls["tau"]

    if rigidbody_dynamics == RigidBodyDynamics.DAE_INVERSE_DYNAMICS:
        if with_passive_torque:
            # initial and final position
            np.testing.assert_almost_equal(q[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(q[:, -1], np.array([0.0, 3.14]))
            # initial and final velocities
            np.testing.assert_almost_equal(qdot[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(qdot[:, -1], np.array([0.0, 0.0]))
            # initial and final controls
            np.testing.assert_almost_equal(
                tau[:, 0],
                np.array([37.2828933, 0.0]),
                decimal=6,
            )
            np.testing.assert_almost_equal(tau[:, -2], np.array([-4.9490898, 0.0]), decimal=6)

        else:
            # initial and final position
            np.testing.assert_almost_equal(q[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(q[:, -1], np.array([0.0, 3.14]))
            # initial and final velocities
            np.testing.assert_almost_equal(qdot[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(qdot[:, -1], np.array([0.0, 0.0]))
            # initial and final controls
            np.testing.assert_almost_equal(
                tau[:, 0],
                np.array([-70.3481693, 0.0]),
                decimal=6,
            )
            np.testing.assert_almost_equal(
                tau[:, -2],
                np.array([-35.5389502, 0.0]),
                decimal=6,
            )

    else:
        if with_passive_torque:
            # initial and final position
            np.testing.assert_almost_equal(q[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(q[:, -1], np.array([0.0, 3.14]))
            # initial and final velocities
            np.testing.assert_almost_equal(qdot[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(qdot[:, -1], np.array([0.0, 0.0]))
            # initial and final controls
            np.testing.assert_almost_equal(
                tau[:, 0],
                np.array([37.2828933, 0.0]),
                decimal=6,
            )
            np.testing.assert_almost_equal(
                tau[:, -2],
                np.array([-4.9490898, 0.0]),
                decimal=6,
            )

        else:
            # initial and final position
            np.testing.assert_almost_equal(q[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(q[:, -1], np.array([0.0, 3.14]))
            # initial and final velocities
            np.testing.assert_almost_equal(qdot[:, 0], np.array([0.0, 0.0]))
            np.testing.assert_almost_equal(qdot[:, -1], np.array([0.0, 0.0]))
            # initial and final controls
            np.testing.assert_almost_equal(
                tau[:, 0],
                np.array([-70.3481693, 0.0]),
                decimal=6,
            )
            np.testing.assert_almost_equal(
                tau[:, -2],
                np.array([-35.5389502, 0.0]),
                decimal=6,
            )
