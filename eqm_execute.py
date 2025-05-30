import random
import sys
import time

import numpy as np

from networks_backup import Networks
from parsed_args_ssd import args
#from sequential_social_dilemma_games.social_dilemmas.envs.cleanup import CleanupEnvMultiType, CleanupEnvReward
#from sequential_social_dilemma_games.social_dilemmas.envs.harvest import HarvestEnvReward
from env_execute import MultiAgentInvManagementDiv
import utils_all
import utils_ssd
import torch 
import os 
import json 
from collections import defaultdict

GREEDY_BETA = 0.001
file_path = "/rds/general/user/nk3118/home/mfmarl-1/results_ssd/is_30_2_nn/saved/"
file_num = "000029999.tar"

def load_data(path, name, networks, env):
    """
    Load saved data and update the networks.

    Parameters
    ----------
    path: str
    name: str
    networks: networks_ssd.Networks
    args: argparse.Namespace
    """
    checkpoint = torch.load(path + name, map_location="cpu")  # Load onto CPU by default
    # Restore network parameters
    for agent_type in range(env.num_types-1):
        print("Agent type:", agent_type)
        if args.mode_ac:
            networks.actor[agent_type].load_state_dict(checkpoint['actor'][agent_type])
            networks.actor_opt[agent_type].load_state_dict(checkpoint['actor_opt'][agent_type])
            networks.actor_target[agent_type].load_state_dict(checkpoint['actor'][agent_type])
        if args.mode_psi:
            networks.psi[agent_type].load_state_dict(checkpoint['psi'][agent_type])
            networks.psi_opt[agent_type].load_state_dict(checkpoint['psi_opt'][agent_type])
        else:
            networks.critic[agent_type].load_state_dict(checkpoint['critic'][agent_type])
            networks.critic_opt[agent_type].load_state_dict(checkpoint['critic_opt'][agent_type])
            networks.critic_target[agent_type].load_state_dict(checkpoint['critic'][agent_type])
    return checkpoint['args'], checkpoint['explore_params'], checkpoint['episode_trained'], checkpoint['time_trained'], checkpoint['outcomes']


def convert_np(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_np(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np(i) for i in obj]
    else:
        return obj

def roll_out(networks, env, args, init_set, epi_num, explore_params, paths, is_draw=False, is_train=True):
    image_path, video_path, saved_path = paths
    epi_length = args.episode_length
    fps = args.fps
    num_types = env.num_types

    agent_ids = env.node_names
    agent_types = list(env.agent_types.values())

    prev_steps = 0
    samples = [None] * epi_length
    collective_reward = [0 for _ in range(num_types)]
    collective_feature = [np.zeros(np.prod(env.observation_space.shape)) for _ in range(num_types)]

    obs = init_set['obs']
    prev_m_act = init_set['m_act']

    all_infos = []
    all_profits = []
    all_backlog = []
    all_inv = []

    actions_dict = {agent_id: [] for agent_id in agent_ids}
    log_probs_dict = {agent_id: [] for agent_id in agent_ids}
    mean_actions_dict = {f"type_{i}": [] for i in range(num_types)}
    obs_dict = {agent_id: [] for agent_id in agent_ids}

    for i in range(epi_length):
        epsilon = explore_params['epsilon']
        beta = explore_params['beta']
        if args.mode_ac:
            rand_prob = np.random.rand(1)[0]
            if is_train and rand_prob < epsilon:
                act = {agent_id: np.random.uniform(low=env.action_space.low,
                                                   high=env.action_space.high,
                                                   size=env.action_space.shape) for agent_id in agent_ids}
                low = env.action_space.low
                high = env.action_space.high
                pdf_value = 1 / (high - low)
                if pdf_value == 0:
                    pdf_value = 1e-8
                act_probs = {agent_id: np.log(pdf_value) for agent_id in agent_ids}
            else:
                act, act_probs = networks.get_actions(obs, prev_m_act, GREEDY_BETA, is_target=False)
        else:
            if is_train:
                act, act_probs = networks.get_actions(obs, prev_m_act, beta, is_target=False)
            else:
                act, act_probs = networks.get_actions(obs, prev_m_act, GREEDY_BETA, is_target=False)

        if is_draw:
            if i == 0:
                print("Run the episode with saving figures...")
            filename = image_path + "frame" + str(prev_steps + i).zfill(9) + ".png"
            env.render(filename=filename, i=prev_steps + i, epi_num=epi_num, act_probs=act_probs)

        n_obs, act, rew, m_act, n_obs, fea, infos = env.step(act)
        all_infos.append(infos)
        all_profits.append(infos['overall_profit'])
        all_backlog.append(infos['total_backlog'])
        all_inv.append(infos['total_inventory'])

        for agent_id in agent_ids:
            if isinstance(act[agent_id], float):
                actions_dict[agent_id].append(act[agent_id])  # Just append the scalar
            else:
                actions_dict[agent_id].append(act[agent_id].tolist())
            log_probs_dict[agent_id].append(act_probs[agent_id] if isinstance(act_probs[agent_id], float)
                                            else float(act_probs[agent_id]))
            obs_dict[agent_id].append(obs[agent_id].tolist())

        for type_id in range(num_types):
            val = m_act[type_id]
            if isinstance(val, (np.ndarray, list)):
                mean_actions_dict[f"type_{type_id}"].append(val.tolist() if hasattr(val, "tolist") else val)
            else:
                # assume val is dict or scalar, append as is
                mean_actions_dict[f"type_{type_id}"].append(val)

        if is_train:
            samples[i] = (obs, act, act_probs, rew, m_act, n_obs, fea, beta)

        for idx, agent_id in enumerate(agent_ids):
            agent_type = agent_types[idx]
            collective_reward[agent_type] += rew[agent_id]
            collective_feature[agent_type] += fea[agent_id]

        obs = n_obs
        prev_m_act = m_act

        if is_draw and i == epi_length - 1:
            act_probs = {agent_ids[j]: "End" for j in range(len(agent_ids))}
            filename = image_path + "frame" + str(prev_steps + i + 1).zfill(9) + ".png"
            env.render(filename=filename, i=prev_steps + i + 1, epi_num=epi_num, act_probs=act_probs)

    rollout_data = {
        "episode": epi_num,
        "collective_reward": collective_reward,
        "collective_feature": [cf.tolist() for cf in collective_feature],
        "profits": all_profits,
        "backlog": all_backlog,
        "inventory": all_inv,
        "actions": actions_dict,
        "action_log_probs": log_probs_dict,
        "mean_actions": mean_actions_dict,
        "observations": obs_dict
    }

    rollout_data = convert_np(rollout_data)

    json_path = os.path.join(saved_path, f"rollout_episode_{epi_num}.json")
    with open(json_path, "w") as f:
        json.dump(rollout_data, f, indent=2)


    init_set: dict = env.reset()

    return samples, init_set, collective_reward, collective_feature, all_infos, all_profits, all_backlog, all_inv


if __name__ == "__main__":
    # Seed setting.
    utils_all.set_random_seed(args.random_seed)

    # Build the environment.
    env = utils_ssd.get_env(args)
    init_set = env.reset()
    # Build networks
    networks = Networks(env, args)

    args_, explore_params, episode_trained, time_trained, outcome=load_data(file_path, file_num, networks, env)
    epsilon = explore_params['epsilon']
    beta = explore_params['beta']

    # Build paths for saving images.
    path, image_path, video_path, saved_path = utils_ssd.make_dirs(args)
    paths = [image_path, video_path, saved_path]
    args.num_episodes = 100
    # Metrics
    collective_rewards, collective_rewards_test = [np.zeros([args.num_types, args.num_episodes]) for _ in range(2)]
    total_penalties, total_penalties_test = [np.zeros(args.num_episodes) for _ in range(2)]
    total_incentives, total_incentives_test = [np.zeros(args.num_episodes) for _ in range(2)]
    objectives, objectives_test = [np.zeros(args.num_episodes) for _ in range(2)]
    time_start = time.time()

    # Save current setting(args) to txt for easy check
    utils_all.make_setting_txt(args, path)

    # Buffer
    buffer = []
    av_infos = []
    av_profits = []
    av_backlog =[]
    av_inv = []
    # Run
    for i in range(args.num_episodes):
        # Option for visualization.
        #is_draw = (True and args.mode_draw) if (i == 0 or (i + 1) % args.save_freq == 0) else False
        is_draw = False
        # Decayed exploration parameters.
        explore_params = utils_ssd.get_explore_params(explore_params, i, args)
        samples, init_set, collective_reward, collective_feature , all_infos, all_profits, all_backlog, all_inv = roll_out(networks=networks,
                                                                                env=env,
                                                                                args=args,
                                                                                init_set=init_set,
                                                                                epi_num=i,
                                                                                explore_params=explore_params,
                                                                                paths=paths,
                                                                                is_draw=is_draw,
                                                                                is_train=False,
                                                                                )
        av_infos.append(all_infos)
        av_profits.append(all_profits)
        av_backlog.append(all_backlog)
        av_inv.append(all_inv)

        for agent_type in range(args.num_types):
            collective_rewards_test[agent_type, i] = collective_reward[agent_type]
            objectives_test[i] = sum(collective_rewards_test[:, i])

        print(f"Process : {i}/{args.num_episodes}, "
                  f"Time : {time.time() - time_start:.2f}, "
                  f"Collective reward (all types) : {sum(collective_rewards_test[:, i]):.2f}, "
                  f"Objective : {objectives_test[i]:.2f}, "
                  f"Test")

    print(collective_rewards_test)
    print(np.mean(collective_rewards_test, axis = 1))
    print(np.std(collective_rewards_test, axis = 1))
    last_values_backlog = [backlog[-1] for backlog in av_backlog]
    last_values_backlog = np.mean(av_backlog, axis = 0)
    average_backlog = np.mean(last_values_backlog)
    std_deviation_backlog = np.std(last_values_backlog)
    median_backlog = np.median(last_values_backlog)
    print(f"Average Backlog : {average_backlog}")
    print(f"Standard Deviation Backlog : {std_deviation_backlog}")
    print(f"Median Backlog : {median_backlog}")

    #last_values_inv = [inv[-1] for inv in av_inv]
    last_values_inv = np.median(av_inv, axis = 0)
    average_inv = np.median(last_values_inv)
    std_deviation_inv = np.std(last_values_inv)
    print(f"Average Inventory : {average_inv}")
    print(f"Standard Deviation Inventory : {std_deviation_inv}")


    