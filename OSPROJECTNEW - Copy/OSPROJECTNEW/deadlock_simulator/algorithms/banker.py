def run_bankers(processes_count, resources_count, allocation, max_demand, available):
    """
    Runs Banker's algorithm and records step-by-step state for visualization.
    Returns: { "isSafe": bool, "safeSequence": list, "steps": list, "need": list }
    """
    # Validate that allocation <= max_demand for all processes and resources
    for i in range(processes_count):
        for j in range(resources_count):
            if allocation[i][j] > max_demand[i][j]:
                return {
                    "isSafe": False,
                    "safeSequence": [],
                    "steps": [{
                        "process": -1,
                        "action": "invalid",
                        "message": f"Invalid input: Process P{i} allocation ({allocation[i][j]}) exceeds maximum demand ({max_demand[i][j]}) for resource R{j}"
                    }],
                    "need": [],
                    "suggestion": f"For P{i}, R{j}, set Maximum Demand to at least {allocation[i][j]} or lower the Allocation value. Banker's algorithm requires allocation <= demand."
                }

    need = []
    for i in range(processes_count):
        need_row = []
        for j in range(resources_count):
            need_row.append(max_demand[i][j] - allocation[i][j])
        need.append(need_row)
        
    finish = [False] * processes_count
    safe_sequence = []
    work = list(available)
    
    steps = [] # To store step-by-step execution for frontend replay
    
    count = 0
    while count < processes_count:
        found = False
        for p in range(processes_count):
            if not finish[p]:
                # Log step: checking process P
                step_log = {
                    "process": p,
                    "action": "check",
                    "work": list(work),
                    "need": need[p],
                    "message": f"Checking if Need of P{p} <= Work"
                }
                
                can_allocate = True
                for j in range(resources_count):
                    if need[p][j] > work[j]:
                        can_allocate = False
                        break
                        
                if can_allocate:
                    # Allocate and finish
                    for j in range(resources_count):
                        work[j] += allocation[p][j]
                        
                    finish[p] = True
                    safe_sequence.append(p)
                    found = True
                    count += 1
                    
                    step_log["status"] = "success"
                    step_log["message"] += f" -> Need <= Work. P{p} executes and releases resources. New Work: {list(work)}"
                    step_log["new_work"] = list(work)
                    steps.append(step_log)
                else:
                    step_log["status"] = "wait"
                    step_log["message"] += f" -> Insufficient resources. P{p} must wait."
                    steps.append(step_log)
                    
        if not found:
            # System is not safe
            steps.append({
                "process": -1,
                "action": "unsafe",
                "message": "No process can satisfy its need. System is in an UNSAFE state."
            })
            return {
                "isSafe": False,
                "safeSequence": [],
                "steps": steps,
                "need": need,
                "suggestion": "Banker's algorithm is an avoidance algorithm: it will deny this allocation because the system would become unsafe. Increase Available resources, reduce Maximum Demand, or wait for currently running processes to release resources."
            }
            
    # System is safe
    steps.append({
        "process": -1,
        "action": "safe",
        "message": f"System is SAFE. Sequence: {['P'+str(i) for i in safe_sequence]}"
    })
    
    return {
        "isSafe": True,
        "safeSequence": safe_sequence,
        "steps": steps,
        "need": need,
        "suggestion": "Banker's algorithm can safely allocate these resources. It avoids deadlock by only granting requests that keep the system in a safe state."
    }
