import numpy as np
from model.iiwa14 import KinematicModel
from model.iiwa14 import DynamicModel


class MainEnv:
    """
    The main iiwa environment class.

    Three subclasses are:

        PositionControl,
        VelocityControl,
        ForceControl

    The main API methods that users of this class are:

        reset
        step
        render
        close
        seed

    And set the following attributes:

        action_space: The Space object corresponding to valid actions
            For continuous action space action_space means elements of valid action
        observation_space: The Space object corresponding to valid observations
        reward_range: A tuple corresponding to the min and max possible rewards
    """

    reward_range = (-float('inf'), float('inf'))
    # Set these in ALL subclasses
    action_space = None
    observation_space = None

    def reset(self):
        """
        Resets the environment to an initial state and returns an initial
        observation.

        :return: observation (object): the initial observation.
        """
        raise NotImplementedError

    def step(self, action):
        """
        Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.

        Accepts an action and returns a tuple (observation, reward, done, info).

        :param action: an action provided by the agent
        :return:
            observation (object): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (bool): whether the episode has ended, in which case further step()
                         calls will return undefined results
            info (str): contains auxiliary diagnostic information (helpful for debugging,
                         and sometimes learning)
        """
        raise NotImplementedError

    def render(self):
        """
        Renders the environment supported by klampt.vis.

        :return: no return
        """
        raise NotImplementedError

    def close(self):
        """Override close in your subclass to perform any necessary cleanup.

        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        pass

    def compute_reward(self, achieved_goal, desired_goal):
        """
        Based on current position and target position calculate the
        distance. Negative distance become reward of applied action.

        :param achieved_goal: TCP position of next observation
        :param desired_goal: Target position of TCP
        :return: Negative reward value
        """
        raise NotImplementedError

    def seed(self, seed=None):
        """
        Sets the seed for this env's random number generator(s).

        :param seed:
        :return:
            list<bigint>: Returns the list of seeds used in this env's random
            number generators. The first value in the list should be the
            "main" seed, or the value which a reproducer should pass to
            'seed'. Often, the main seed equals the provided 'seed', but
            this won't be true if seed=None, for example.
        """
        return

    def class_name(self):
        return str(self.__class__)


class PositionControl(MainEnv):
    def __init__(self):
        self.iiwa = KinematicModel()
        self.current_action = np.zeros(7)
        self.target_position = np.zeros([3, 1])
        self.target_so3 = np.zeros([3, 3])
        self.target_rpy = self.iiwa.so3_to_rpy(self.target_so3)
        self.tol_position = 1e-4  # 0.0001 meter = 0.1 mm, Euclidean Distance
        self.tol_orientation = 2e-3  # approximate 0.115, Euclidean Distance
        self.is_done_counter = 0

    def reset(self):
        current_state = self.iiwa.current_configuration
        return current_state

    def step(self, action):
        next_state = self.iiwa.current_configuration + action
        collision = self.iiwa.check_collision(next_state)
        info = "Everything is fine."
        if collision:
            reward = -100.0
            done = True
            info = "Oops, a collision has occurred."
            return next_state, reward, done, info
        self.iiwa.current_configuration = next_state
        self.iiwa.update_kinematic()
        ee_rpy = self.iiwa.current_ee_rpy
        ee_position = self.iiwa.current_ee_position
        reward, done = self.compute_reward(ee_rpy, ee_position)
        return next_state, reward, done, info

    def render(self):
        config = self.iiwa.current_configuration
        self.iiwa.display_robot(config)

    def compute_reward(self, ee_rpy, ee_position):
        rpy_error = np.linalg.norm(ee_rpy - self.target_so3)
        position_error = np.linalg.norm(ee_position - self.target_position)
        reward = -(rpy_error + position_error)
        is_done = self._is_done(rpy_error, position_error)
        return reward, is_done

    def _is_done(self, orientation_error, position_error):
        if orientation_error <= self.tol_orientation and position_error <= self.tol_position:
            self.is_done_counter += 1
            if self.is_done_counter > 5:
                return True
            else:
                self.is_done_counter = 0
                return False


class VelocityControl(MainEnv):
    def __init__(self):
        pass

    def reset(self):
        pass

    def step(self, action):
        pass

    def render(self):
        pass

    def compute_reward(self, achieved_goal, desired_goal):
        distance = np.linalg.norm(achieved_goal - desired_goal)
        return -distance


class ForceControl(MainEnv):
    def __init__(self):
        pass

    def reset(self):
        pass

    def step(self, action):
        pass

    def render(self):
        pass

    def compute_reward(self, achieved_goal, desired_goal):
        distance = np.linalg.norm(achieved_goal - desired_goal)
        return -distance


class KUKAiiwa:
    control_types = {
        "PositionControl", PositionControl,
        "VelocityControl", VelocityControl,
        "ForceControl", ForceControl}

    def __new__(cls, control_type: str):
        try:
            return cls.control_types[control_type]()
        except TypeError as T:
            print("No class name: ", control_type)
            print("classes: PositionControl, VelocityControl, ForceControl.")