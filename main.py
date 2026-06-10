"""
main.py

Main orchestrator script to compile and execute the LangGraph research pipeline.
Connects the Intent, Planning, Research, and Validation nodes sequentially.
"""

from schema import ResearchState
from nodes.a01_Intent_Node import intent_node
from nodes.b02_Planning_Node import plan_node
from nodes.c03_Research_Node import research_node
from nodes.d04_Validation_Summary_Node import validation_node
from langgraph.graph import StateGraph, END, START
import asyncio



def create_workflow():
    """
    Compiles individual business nodes into a sequential StateGraph application.
    """
    graph = StateGraph(ResearchState)
    
    # Adding nodes
    graph.add_node('Intent', intent_node)
    graph.add_node('Plan', plan_node)
    graph.add_node('Research', research_node)
    graph.add_node('Validate', validation_node)

    # Adding Edges
    # Fixed: Changed the destination edge from 'I' to the registered node name 'Intent'
    graph.add_edge(START, 'Intent')
    graph.add_edge('Intent', 'Plan')
    graph.add_edge('Plan', 'Research')
    graph.add_edge('Research', 'Validate')
    graph.add_edge('Validate', END)
    
    return graph.compile()


workflow = create_workflow()


async def main(state: ResearchState) -> ResearchState:
    """
    Invokes the compiled graph asynchronously and handles the returned state.
    """
    # Invoke the fully compiled LangGraph application state
    final_state = await workflow.ainvoke(state)
    
    print("\n--- FINAL GRAPH STATE EXECUTION COMPLETED ---")
    print(final_state)
    
    # LangGraph returns a dictionary payload; cast it or unpack it directly
    return final_state


if __name__ == "__main__":
    # Ensure your initial dictionary conforms to your structural ResearchState keys
    initial_input = {
        "topic": "Machine Learning Systems Design", 
        "research_mode": "ultra-fast"
    }
    
    # Instantiate state safely using dictionary unpacking syntax
    state_instance = ResearchState(**initial_input)
    
    # Run the top-level async main task loop
    asyncio.run(main(state_instance))
