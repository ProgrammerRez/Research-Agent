from schema import ResearchState
from nodes.a01_Intent_Node import intent_node
from nodes.b02_Planning_Node import plan_node
from nodes.c03_Research_Node import research_node
from nodes.d04_Validation_Summay_Node import validation_node
import asyncio
import json



# Creating an async function


async def main():
    # state = ResearchState(
    #     **{"topic": "Machine Learning Systems Design", "research_mode": 'ultra-fast'}
    # )

    # # Inside a function we need to await async nodes
    # updated_state = await intent_node(state)
    # updated_state = await plan_node(updated_state)
    # research_state = await research_node(updated_state)
    # print(research_state)

    # with open("example.json", "w") as f:
    #     json.dump(research_state, fp=f)

    with open("example.json", "r") as f:
        research_state = json.load(fp=f)
        updated_state = await validation_node(research_state)
        
    print(updated_state)
    
if __name__ == "__main__":
    asyncio.run(main())
