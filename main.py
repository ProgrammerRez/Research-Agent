from schema import ResearchState
from nodes.a01_Intent_Node import intent_node
import asyncio




# Creating an async function

async def main():
    state = ResearchState(topic="Machine Learning Systems Design", 
            research_mode="deep")
    
    # Inside a function we need to await async nodes
    updated_state = await intent_node(state)
    print(updated_state)



if __name__=='__main__':
    asyncio.run(main())
    
    
    