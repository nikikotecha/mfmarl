import argparse

import utils_all # This is the file that contains the functions that are used in this file.
from env3rundivproduct import MultiAgentInvManagementDiv
import torch 
#default configuration but change the environment configuration through the config dictionary
def config_args():
    config = {}
    return config 

config = config_args()
env = MultiAgentInvManagementDiv(config = config)

def add_default_args(parser):
    """
    Build default ArgumentParser.

    Parameters
    ----------
    parser: argparse.ArgumentParser
    """
    # Setting for the description.
    parser.add_argument("--description", type=str, default='Experiment',
                        help="General description for this experiment (or setting). It is only used for the reminder.")
    parser.add_argument("--setting_name", type=str, default='setting_0',
                        help="Setting name for the current setup. This name will be used for the folder name.")

    # Setting for the environment.
    parser.add_argument("--env", type=str, default="MultiAgentInvManagement", help="Name of the environment to use.")
    parser.add_argument("--num_types", type=int, default=2, help="Number of agents' types. Default by number of types in environment")
    parser.add_argument("--num_agents", type=list, default=[12, 12], help="Number of agents for each type.")
    #parser.add_argument("--rew_clean", type=float, default=0, help="Reward for cleaning. "
    #                                                               "It is for CleanUpMultiType environment.")
    #parser.add_argument("--rew_harvest", type=float, default=1, help="Reward for harvesting. "
    #                                                                 "It is for CleanUpMultiType environment.")

    # Setting for the reward designer's problem.
    #parser.add_argument("--lv_penalty", type=float, default=0, help="Penalty level for agents who eat apple. "
    #                                                                "It is for CleanupReward environment.")
    #parser.add_argument("--lv_incentive", type=float, default=0, help="Incentive level for agents who clean the river. "
    #                                                                  "It is for CleanupReward environment.")

    # Setting for the networks.
    parser.add_argument("--mode_ac", type=bool, default=True, help="Mode selection (Actor-critic/psi or critic/psi).")
    parser.add_argument("--mode_psi", type=bool, default=False, help="Mode selection (critic or psi).")
    parser.add_argument("--mode_mfp", type=bool, default=True, help="Mode selection (mfp benchmark).")
    parser.add_argument("--mode_mfap", type=bool, default=False, help="Mode selection (mfap benchmark).")
    parser.add_argument("--mode_is", type=bool, default=False, help="True if we use importance sampling for the critic loss calculation.")

    parser.add_argument("--h_dims_a", type=list, default=[], help="Default layer size for actor hidden layers.")
    parser.add_argument("--h_dims_c", type=list, default=[], help="Default layer size for critic hidden layers.")
    parser.add_argument("--h_dims_p", type=list, default=[], help="Default layer size for psi hidden layers.")
    parser.add_argument("--h_dims_m", type=list, default=[], help="Default layer size for psi hidden layers.")
    parser.add_argument("--h_dims_mfap", type=list, default=[], help="Default layer size for psi hidden layers.")

    parser.add_argument("--lr_a", type=float, default=0, help="Default learning rate for the actor network.")
    parser.add_argument("--lr_c", type=float, default=0, help="Default learning rate for the critic network.")
    parser.add_argument("--lr_p", type=float, default=0, help="Default learning rate for the psi network.")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor.")

    # Setting for the experiment.
    parser.add_argument("--num_episodes", type=int, default=200, help="Number of episodes.")
    parser.add_argument("--episode_length", type=int, default=50, help="Episode length for the experiment.")
    parser.add_argument("--epsilon", type=float, default=0.9, help="Epsilon for exploration.")
    parser.add_argument("--epsilon_decay_ver", type=str, default="linear",
                        help="'linear', 'exponential' can be used for the version of epsilon decay.")
    parser.add_argument("--beta", type=float, default=0.9, help="Temperature for exploration (Boltzmann policy.")
    parser.add_argument("--beta_decay_ver", type=str, default="linear",
                        help="'linear', 'exponential' can be used for the version of beta decay.")
    parser.add_argument("--mode_test", type=bool, default=False,
                        help="True if we do test during the learning. It requires double time.")
    parser.add_argument("--random_seed", type=int, default=1234, help="Random seed.")

    # Setting for the learning.
    parser.add_argument("--K", type=int, default=200, help="Number of samples from the buffer.")
    parser.add_argument("--buffer_size", type=int, default=10000, help="Maximum buffer size.")
    parser.add_argument("--mode_lr_decay", type=bool, default=True, help="True if we do learning rate decay.")
    parser.add_argument("--update_freq", type=int, default=5,
                        help="Update frequency of networks (unit: episode).")
    parser.add_argument("--update_freq_target", type=int, default=50,
                        help="Update frequency of target networks (unit: episode).")
    parser.add_argument("--tau", type=float, default=0.01,
                        help="Learning rate of target networks. If tau is 1, it is hard update.")
    parser.add_argument("--mode_one_hot_obs", type=bool, default=False,
                        help="True if we use one-hot encoded observations.")
    parser.add_argument("--mode_reuse_networks", type=bool, default=False,
                        help="True if we reuse other networks for the initialization.")
    parser.add_argument("--file_path", type=str, default='',
                        help="File path of the results of other networks. "
                             "ex. args.file_path='./results_ssd/setting_14/saved/000011999.tar'")

    # Setting for the draw and the save.
    parser.add_argument("--fps", type=int, default=3, help="Frame per second for videos")
    parser.add_argument("--draw_freq", type=int, default=100,
                        help="Frequency of drawing results (unit: episode).")
    parser.add_argument("--save_freq", type=int, default=1000,
                        help="Frequency of saving results and networks (unit: episode).")
    parser.add_argument("--mode_draw", type=bool, default=False,
                        help="True if we draw plt during the training.")
    parser.add_argument("--importance_sampling", type=bool, default=True,
                        help="True if we use importance sampling for the critic loss calculation.")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device for the training. 'cuda' or 'cpu' can be used.")   
    parser.add_argument("--eqm_analysis", type=bool, default=False,
                        help="True if we do equilibrium analysis.") 



parser = argparse.ArgumentParser()
add_default_args(parser)
args = parser.parse_args()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device: ", device)
args.device = device
""" Setting for the description. """
args.description = '100_mf_retry'
args.setting_name = 'test'+utils_all.get_current_time_tag()+'100_mf_retry'
args.env = 'cleanup_multi_type_regular'
args.num_types = 1
args.num_agents = [100]
args.rew_clean = 0.05
args.rew_harvest = 0.95
args.eqm_analysis = False
""" Setting for the reward designer's problem. """
args.lv_penalty = 0.0
args.lv_incentive = 0.0

""" Setting for the networks. """
args.mode_ac = True  # True if actor-critic/psi.
args.mode_psi = False  # True if SF.
args.mode_mfp = False  # True if MFP.
args.mode_mfap = False # True if MFAP.
args.mode_is = False # True if we use importance sampling for the critic loss calculation.
args.importance_sampling = False # True if we use importance sampling for the critic loss calculation.

args.h_dims_a = [256, 128, 64, 32]
args.h_dims_c = [256, 128, 64, 32]
args.h_dims_p = [256, 128, 64, 32]
args.h_dims_m = [256, 128, 64, 32]
args.h_dims_mfap = [256, 128, 64, 32]

args.lr_a = 0.0001
args.lr_c = 0.001
args.lr_p = 0.001
args.lr_m = 0.001
args.lr_mfap = 0.001
args.gamma = 0.99

""" Setting for the experiment. """
args.num_episodes = 30000
args.episode_length = 365
args.epsilon = 0.99
args.epsilon_decay_ver = 'exponential'
args.beta = 1.0
args.beta_decay_ver = 'linear'  # 'exponential'
args.mode_test = False
args.random_seed = 52  # 1280

""" Setting for the learning. """
args.K = 300
args.buffer_size = 1000000
args.mode_lr_decay = True
args.update_freq = 5
args.update_freq_target = 10
args.tau = 0.01
args.mode_one_hot_obs = False
args.mode_reuse_networks = False  # True for Transfer Learning
args.file_path = './results_ssd_final/alpha=0.50/000029999.tar'

""" Setting for the draw and the save. """
args.fps = 3
args.draw_freq = 100
args.save_freq = 200 #200 usually
args.mode_draw = False

""" Validate the setting. """
utils_all.validate_setting(args)

# """ Execute main_ssd.py file. """
# exec(open('main_ssd.py').read())  # For convenience but recommend to use main_ssd.py (args are called twice)