import numpy as np
from casadi import MX, SX, DM

from .options import OptionDict, OptionGeneric
from .enums import Node


class Mapping(OptionGeneric):
    """
    Mapping of index set to a different index set

    Example of use:
        - to_map = Mapping([0, 1, 1, 3, None, 1], [3])
        - obj = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        - mapped_obj = to_map.map(obj)
    Expected result:
        - mapped_obj == np.array([0.1, 0.2, 0.2, -0.4, 0, 0.1])

    Attributes
    ----------
    map_idx: list[int]
        The actual index list that links to the other set, an negative value links to a numerical 0
    oppose: list[int]
        Index to multiply by -1

    Methods
    -------
    map(self, obj: list) -> list
        Apply the mapping to an obj
    len(self) -> int
        Get the len of the mapping
    """

    def __init__(
        self,
        map_idx: list | tuple | range | np.ndarray,
        oppose: int | list | tuple | range | np.ndarray = None,
        **params
    ):
        """
        Parameters
        ----------
        map_idx: list | tuple | range | np.ndarray
            The actual index list that links to the other set
        oppose: int | list | tuple | range | np.ndarray
            Index to multiply by -1
        """
        super(Mapping, self).__init__(**params)
        self.map_idx = map_idx
        self.oppose = [1] * len(self.map_idx)
        if oppose is not None:
            if isinstance(oppose, int):
                oppose = [oppose]
            for i in oppose:
                self.oppose[i] = -1

    def map(self, obj: tuple | list | np.ndarray | MX | SX | DM) -> np.ndarray | MX | SX | DM:
        """
        Apply the mapping to an matrix object. The rows are mapped while the columns are preserved as is

        Parameters
        ----------
        obj: tuple | list | np.ndarray | MX | SX | DM
            The matrix to map

        Returns
        -------
        The list mapped
        """
        # Declare a zero filled object
        if isinstance(obj, (tuple, list)):
            obj = np.array(obj)

        if isinstance(obj, np.ndarray):
            if len(obj.shape) == 1:
                obj = obj[:, np.newaxis]
            mapped_obj = np.zeros((len(self.map_idx), obj.shape[1]))
        elif isinstance(obj, (MX, SX, DM)):
            mapped_obj = type(obj).zeros(len(self.map_idx), obj.shape[1])
        else:
            raise RuntimeError("map must be applied on np.ndarray, MX or SX")

        # Fill the positive values
        index_plus_in_origin = []
        index_plus_in_new = []
        index_minus_in_origin = []
        index_minus_in_new = []
        for i, v in enumerate(self.map_idx):
            if v is not None and self.oppose[i] > 0:
                index_plus_in_origin.append(v)
                index_plus_in_new.append(i)
            elif v is not None and self.oppose[i] < 0:
                index_minus_in_origin.append(v)
                index_minus_in_new.append(i)
        mapped_obj[index_plus_in_new, :] = obj[index_plus_in_origin, :]  # Fill the non zeros values
        mapped_obj[index_minus_in_new, :] = -obj[index_minus_in_origin, :]  # Fill the non zeros values

        return mapped_obj

    def __len__(self) -> int:
        """
        Get the len of the mapping

        Returns
        -------
        The len of the mapping
        """

        return len(self.map_idx)


class BiMapping(OptionGeneric):
    """
    Mapping of two index sets between each other

    Attributes
    ----------
    to_second: Mapping
        The mapping that links the first variable to the second
    to_first: Mapping
        The mapping that links the second variable to the first
    """

    def __init__(
        self,
        to_second: Mapping | int | list | tuple | range,
        to_first: Mapping | int | list | tuple | range,
        oppose_to_second: Mapping | int | list | tuple | range = None,
        oppose_to_first: Mapping | int | list | tuple | range = None,
        **params
    ):
        """
        Parameters
        ----------
        to_second: Mapping | int | list | tuple | range
            The mapping that links the first index set to the second
        to_first: Mapping | int | list | tuple | range
            The mapping that links the second index set to the first
        oppose_to_second: Mapping | int | list | tuple | range
            Index to multiply by -1 of the to_second mapping
        oppose_to_first: Mapping | int | list | tuple | range
            Index to multiply by -1 of the to_first mapping
        """
        super(BiMapping, self).__init__(**params)

        if isinstance(to_second, (list, tuple, range)):
            to_second = Mapping(map_idx=to_second, oppose=oppose_to_second)
        if isinstance(to_first, (list, tuple, range)):
            to_first = Mapping(map_idx=to_first, oppose=oppose_to_first)

        if not isinstance(to_second, Mapping):
            raise RuntimeError("to_second must be a Mapping class")
        if not isinstance(to_first, Mapping):
            raise RuntimeError("to_first must be a Mapping class")

        self.to_second = to_second
        self.to_first = to_first


class BiMappingList(OptionDict):
    def __init__(self):
        super(BiMappingList, self).__init__()

    def add(
        self,
        name: str,
        to_second: Mapping | int | list | tuple | range = None,
        to_first: Mapping | int | list | tuple | range = None,
        oppose_to_second: Mapping | int | list | tuple | range = None,
        oppose_to_first: Mapping | int | list | tuple | range = None,
        bimapping: BiMapping = None,
        phase: int = -1,
    ):
        """
        Add a new BiMapping to the list

        Parameters
        name: str
            The name of the new BiMapping
        to_second: Mapping | int | list | tuple | range
            The mapping that links the first variable to the second
        to_first: Mapping | int | list | tuple | range
            The mapping that links the second variable to the first
        oppose_to_second: Mapping | int | list | tuple | range
            Index to multiply by -1 of the to_second mapping
        oppose_to_first: Mapping | int | list | tuple | range
            Index to multiply by -1 of the to_first mapping
        bimapping: BiMapping
            The BiMapping to copy
        """

        if isinstance(bimapping, BiMapping):
            if to_second is not None or to_first is not None:
                raise ValueError("BiMappingList should either be a to_second/to_first or an actual BiMapping")
            self.add(
                name,
                phase=phase,
                to_second=bimapping.to_second,
                to_first=bimapping.to_first,
                oppose_to_second=oppose_to_second,
                oppose_to_first=oppose_to_first,
            )

        else:
            if to_second is None or to_first is None:
                raise ValueError("BiMappingList should either be a to_second/to_first or an actual BiMapping")
            super(BiMappingList, self)._add(
                key=name,
                phase=phase,
                option_type=BiMapping,
                to_second=to_second,
                to_first=to_first,
                oppose_to_second=oppose_to_second,
                oppose_to_first=oppose_to_first,
            )

    def variable_mapping_fill_phases(self, n_phases):
        for mappings in self.options:
            for key in mappings:
                if mappings[key].automatic_multiple_phase:
                    for i_phase in range(n_phases):
                        if i_phase == 0:
                            mappings[key].phase = 0
                        else:
                            self.add(name=key, bimapping=mappings[key], phase=i_phase)
        return self

    def __getitem__(self, item) -> dict | BiMapping:
        return super(BiMappingList, self).__getitem__(item)

    def __contains__(self, item):
        return item in self.options[0].keys()


class NodeMapping(OptionGeneric):
    """
    Mapping of two node sets between each other
    """

    def __init__(
        self,
        map_states: bool = False,
        map_controls: bool = False,
        phase_pre: int = None,  # change name to reference_phase
        phase_post: int = None,  # mapped_phase
        index: list = None,
        variable_mapping: BiMappingList = None,
        **params
    ):
        """
        Parameters
        ----------
        map_states: Bool
            Should we map the states
        map_controls: Bool
            Or should we map the controls
        phase_pre: int
            The number of the first phase to map
        phase_post: int
            The number of the second phase to map
        index: list
            The list of the index to map (ex: the index of the DoFs to map)
        """
        super(NodeMapping, self).__init__(**params)

        self.map_states = map_states
        self.map_controls = map_controls
        self.phase_pre = phase_pre
        self.phase_post = phase_post
        self.index = index
        self.variable_mapping = variable_mapping

class NodeMappingIndex():
    def __init__(self, phase: int = None, index: list | None = None, variable_mapped_index: list | None = None):

        self.phase = phase
        self.index = index
        if variable_mapped_index is None:
            self.variable_mapped_index = index
        else:
            self.variable_mapped_index = variable_mapped_index

class NodeMappingList(OptionDict):
    def __init__(self):
        super(NodeMappingList, self).__init__()

    def add(
        self,
        name: str,
        map_states: bool = False,
        map_controls: bool = False,
        phase_pre: int = None,
        phase_post: int = None,
        index: list = None,
        variable_mapping: BiMappingList = None,
    ):
        """
        Add a new NodeMapping to the list

        Parameters
        name: str
            The name of the new BiMapping
        to_second: Mapping
            The mapping that links the first variable to the second
        to_first: Mapping
            The mapping that links the second variable to the first
        bimapping: BiMapping
            The BiMapping to copy
        """

        if map_states == False and map_controls == False:
            raise Warning(
                "You should use either map_states=True or map_controls=True. "
                "For now your node mapping has no effect."
            )
        if map_states == True and map_controls == True:
            raise ValueError("you cannot map both states and controls at the same time. If it is really what you want to do, use two different node mappings please.")

        if phase_pre is None or phase_post is None:
            raise ValueError("NodeMappingList should contain phase_pre and phase_post.")

        if phase_pre > phase_post:
            raise ValueError("Please provide a phase_pre index value smaller than the phase_post index value.")

        if not (isinstance(variable_mapping, BiMappingList) or variable_mapping is None):
            raise ValueError(f"variable_mapping (of type {type(variable_mapping)}) should be None or a BiMappingList.")

        super(NodeMappingList, self)._add(
            key=name,
            map_states=map_states,
            map_controls=map_controls,
            phase=phase_pre,
            option_type=NodeMapping,
            phase_pre=phase_pre,
            phase_post=phase_post,
            index=index,
            variable_mapping=variable_mapping[phase_pre][name],
        )

    def get_variable_from_phase_idx(self, ocp):

        # use_states_from_phase_idx = [i for i in range(ocp.n_phases)]
        # use_states_dot_from_phase_idx = [i for i in range(ocp.n_phases)]
        # use_controls_from_phase_idx = [i for i in range(ocp.n_phases)]
        # mapped_states_idx = [None for _ in range(ocp.n_phases)]
        # mapped_states_dot_idx = [None for _ in range(ocp.n_phases)]
        # mapped_controls_idx = [None for _ in range(ocp.n_phases)]
        # mapped_variable_states_idx = [None for _ in range(ocp.n_phases)]
        # mapped_variable_states_dot_idx = [None for _ in range(ocp.n_phases)]
        # mapped_variable_controls_idx = [None for _ in range(ocp.n_phases)]
        # names_states = [None for _ in range(ocp.n_phases)]
        # names_states_dot = [None for _ in range(ocp.n_phases)]
        # names_controls = [None for _ in range(ocp.n_phases)]
        #
        # for i, node_mapping in enumerate(self):
        #     for key in node_mapping.keys():
        #         if node_mapping[key].map_states:
        #             use_states_from_phase_idx[node_mapping[key].phase_post] = node_mapping[key].phase_pre
        #             use_states_dot_from_phase_idx[node_mapping[key].phase_post] = node_mapping[key].phase_pre
        #             mapped_states_idx[node_mapping[key].phase_post] = node_mapping[key].index
        #             mapped_states_dot_idx[node_mapping[key].phase_post] = node_mapping[key].index
        #             mapped_variable_states_idx[node_mapping[key].phase_post] = [node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index]
        #             mapped_variable_states_dot_idx[node_mapping[key].phase_post] = [node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index]
        #             names_states[node_mapping[key].phase_post] = key
        #             names_states_dot[node_mapping[key].phase_post] = key
        #         if node_mapping[key].map_controls:
        #             use_controls_from_phase_idx[node_mapping[key].phase_post] = node_mapping[key].phase_pre
        #             mapped_controls_idx[node_mapping[key].phase_post] = node_mapping[key].index
        #             mapped_variable_controls_idx[node_mapping[key].phase_post] = [node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index]
        #             names_controls[node_mapping[key].phase_post] = key

        from ..optimization.non_linear_program import NonLinearProgram

        # states_phase_mapping_idx = []
        # states_dot_phase_mapping_idx = []
        # controls_phase_mapping_idx = []
        # for i in range(ocp.n_phases):
        #     states_phase_mapping_idx += [NodeMappingIndex(use_states_from_phase_idx[i], mapped_states_idx[i], mapped_variable_states_idx[i], names_states[i])]
        #     states_dot_phase_mapping_idx += [NodeMappingIndex(use_states_dot_from_phase_idx[i], mapped_states_dot_idx[i], mapped_variable_states_dot_idx[i], names_states_dot[i])]
        #     controls_phase_mapping_idx += [NodeMappingIndex(use_controls_from_phase_idx[i], mapped_controls_idx[i], mapped_variable_controls_idx[i], names_controls[i])]


        states_phase_mapping_idx = [{} for _ in range(ocp.n_phases)]
        states_dot_phase_mapping_idx = [{} for _ in range(ocp.n_phases)]
        controls_phase_mapping_idx = [{} for _ in range(ocp.n_phases)]
        for i, node_mapping in enumerate(self):
            for key in node_mapping.keys():
                if node_mapping[key].map_states:
                    states_phase_mapping_idx[node_mapping[key].phase_post][key] = NodeMappingIndex(
                        phase=node_mapping[key].phase_pre, index=node_mapping[key].index, variable_mapped_index=[node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index])
                    states_dot_phase_mapping_idx[node_mapping[key].phase_post][key] = NodeMappingIndex(
                        phase=node_mapping[key].phase_pre, index=node_mapping[key].index, variable_mapped_index=[node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index])
                if node_mapping[key].map_controls:
                    controls_phase_mapping_idx[node_mapping[key].phase_post][key] = NodeMappingIndex(
                        phase=node_mapping[key].phase_pre, index=node_mapping[key].index, variable_mapped_index=[node_mapping[key].variable_mapping.to_second.map_idx[j] for j in node_mapping[key].index])

        NonLinearProgram.add(ocp, "states_phase_mapping_idx", states_phase_mapping_idx, False)
        NonLinearProgram.add(ocp, "states_dot_phase_mapping_idx", states_dot_phase_mapping_idx, False)
        NonLinearProgram.add(ocp, "controls_phase_mapping_idx", controls_phase_mapping_idx, False)

        return states_phase_mapping_idx, states_dot_phase_mapping_idx, controls_phase_mapping_idx

    def __getitem__(self, item) -> dict | BiMapping:
        return super(NodeMappingList, self).__getitem__(item)

    def __contains__(self, item):
        return item in self.options[0].keys()
