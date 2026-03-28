import os
import json
import random
import sqlite3
import asyncio
from typing import Dict, Any, List

import dotenv
import oasis
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from oasis import ActionType, AgentGraph, LLMAction, ManualAction, SocialAgent, UserInfo
from oasis.environment.env import OasisEnv

dotenv.load_dotenv()

# Local SQLite file for storing simulation traces.
DB_PATH = "simlation.db"

# Main topic is the shared subject the simulation revolves around.
MAIN_TOPIC = "What is the most trending AI application in 2027?"

# Size of the simulated population.
NUM_PEOPLE = 100

# Number of rounds to run the simulation.
NUM_ROUNDS = 10

# Prompt used during interviews after the simulation.
INTERVIEW_PROMPT = "What will be the most trending AI application in 2027, and why?"

# Number of agents to interview.
NUM_INTERVIEWEES = 5


def pick_mbti_words() -> str:
    return (
        f"{random.choice(['Extraverted', 'Introverted'])}, "
        f"{random.choice(['Sensing', 'Intuitive'])}, "
        f"{random.choice(['Thinking', 'Feeling'])}, "
        f"{random.choice(['Judging', 'Perceiving'])}"
    )


def generate_random_people() -> List[Dict[str, Any]]:
    with open("attributes.json", "rt") as f:
        attributes = json.load(f)

    people = []
    age_range = attributes["age_range"]
    topics = attributes["topics"]
    professions = attributes["professions"]

    for idx in range(NUM_PEOPLE):
        random_n_topics = min(random.randint(2, 5), len(topics))
        sampled_topics = [MAIN_TOPIC] + random.sample(topics, random_n_topics)

        people.append({
            "user_id": idx,
            "name": f"user_{idx}",
            "username": f"user_{idx}",
            "age": random.randint(age_range["min"], age_range["max"]),
            "gender": random.choice(["male", "female"]),
            "mbti": pick_mbti_words(),
            "profession": random.choice(professions),
            "interested_topics": sampled_topics,
        })

    return people


# Action types allowed during the simulation.
SUPPORTED_ACTIONS = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.DISLIKE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.LIKE_COMMENT,
    ActionType.DISLIKE_COMMENT,
    ActionType.REPOST,
    ActionType.FOLLOW,
    ActionType.UNFOLLOW,
    ActionType.DO_NOTHING,
    ActionType.QUOTE_POST,
]

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini"),
    api_key=os.environ.get("LLM_API_KEY"),
    url=os.environ.get("LLM_BASE_URL"),
    model_config_dict={"max_tokens": 32768}
)


def build_agent_graph(people: List[Dict[str, Any]]) -> AgentGraph:
    agent_graph = AgentGraph()

    for p in people:
        topics = ", ".join(p["interested_topics"])
        description = f"{p['profession']}, a {p['age']}-year-old {p['gender']} with an {p['mbti']} personality, interested in {topics}"

        user_info = UserInfo(
            name=p["username"],
            description=description,
            profile={
                "nodes": [],
                "edges": [],
                "other_info": {
                    "user_profile": description
                }
            },
            recsys_type='twitter',
        )

        agent = SocialAgent(
            agent_id=p["user_id"],
            user_info=user_info,
            model=model,
            agent_graph=agent_graph,
            available_actions=SUPPORTED_ACTIONS,
        )

        agent_graph.add_agent(agent)
    return agent_graph


def create_simulation_environment() -> OasisEnv:
    people = generate_random_people()
    agent_graph = build_agent_graph(people)

    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=DB_PATH,
        semaphore=30,
    )

    return env


async def run_simulation(env: OasisEnv):
    await env.reset()

    agents = [agent[1] for agent in env.agent_graph.get_agents()]

    for _ in range(NUM_ROUNDS):
        target_count = max(1, int(len(agents) * random.uniform(0.02, 0.05)))
        active_agents = random.sample(agents, min(target_count, len(agents)))

        actions = {}
        for agent in active_agents:
            actions[agent] = LLMAction()

        await env.step(actions)


def get_interview_results(agent_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    placeholders = ", ".join(["?"] * len(agent_ids))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT user_id, info, created_at
        FROM trace
        WHERE action = ? AND user_id IN ({placeholders})
        ORDER BY created_at DESC
        """,
        (ActionType.INTERVIEW.value, *agent_ids),
    )

    results: Dict[int, Dict[str, Any]] = {
        agent_id: {"agent_id": agent_id, "response": None, "timestamp": None}
        for agent_id in agent_ids
    }

    seen = set()
    for user_id, info_json, created_at in cursor.fetchall():
        if user_id in seen:
            continue
        seen.add(user_id)
        try:
            info = json.loads(info_json) if info_json else {}
            response = info["response"]
        except json.JSONDecodeError:
            response = info_json
        results[user_id]["response"] = response
        results[user_id]["timestamp"] = created_at

        if len(seen) == len(agent_ids):
            break

    conn.close()
    return results


async def run_interview(env: OasisEnv):
    interview_agents = random.sample(env.agent_graph.get_agents(), NUM_INTERVIEWEES)

    interview_actions = {}
    for agent in interview_agents:
        interview_actions[agent[1]] = ManualAction(
            action_type=ActionType.INTERVIEW,
            action_args={"prompt": INTERVIEW_PROMPT},
        )

    try:
        await env.step(interview_actions)
    except Exception:
        pass

    interview_results = get_interview_results([agent[0] for agent in interview_agents])
    for agent in interview_agents:
        response = interview_results[agent[0]]["response"]
        print(f"Interview with agent_{agent[0]}: {response}")


async def main():
    env = create_simulation_environment()

    await run_simulation(env)

    await run_interview(env)

    await env.close()

if __name__ == "__main__":
    asyncio.run(main())
