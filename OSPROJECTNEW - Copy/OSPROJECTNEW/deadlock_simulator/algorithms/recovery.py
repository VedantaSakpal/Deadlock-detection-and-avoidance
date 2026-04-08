def terminate_process(allocation, request, available, process_id, resources_count):
    """
    Terminates a process to recover from deadlock.
    Releases all its allocated resources to available.
    """
    new_available = list(available)
    new_allocation = [list(row) for row in allocation]
    new_request = [list(row) for row in request]
    
    # Release resources
    for j in range(resources_count):
        new_available[j] += new_allocation[process_id][j]
        new_allocation[process_id][j] = 0
        new_request[process_id][j] = 0 # Process is terminated, no more requests
        
    return {
        "allocation": new_allocation,
        "request": new_request,
        "available": new_available,
        "terminated": process_id,
        "message": f"Process P{process_id} terminated. Resources released."
    }

def preempt_resource(allocation, request, available, process_id, resource_id):
    """
    Preempts 1 instance of a resource from a process.
    """
    new_available = list(available)
    new_allocation = [list(row) for row in allocation]
    new_request = [list(row) for row in request]
    
    if new_allocation[process_id][resource_id] > 0:
        new_allocation[process_id][resource_id] -= 1
        new_available[resource_id] += 1
        # Since it was preempted, its request basically goes up to get it back
        new_request[process_id][resource_id] += 1
        
        return {
            "success": True,
            "allocation": new_allocation,
            "request": new_request,
            "available": new_available,
            "message": f"Preempted 1 instance of R{resource_id} from P{process_id}.",
            "preempted": {"p": process_id, "r": resource_id}
        }
    else:
        return {
            "success": False,
            "message": f"P{process_id} does not hold any instances of R{resource_id} to preempt."
        }
