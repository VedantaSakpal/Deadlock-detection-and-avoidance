def run_detection(processes_count, resources_count, allocation, request, available):
    """
    Runs Deadlock Detection algorithm. Similar to Banker's but uses Request matrix.
    Returns: { "hasDeadlock": bool, "deadlockedProcesses": list, "steps": list, "work": list }
    """
    work = list(available)
    finish = [False] * processes_count
    
    # Initialization: If allocation = 0 for all resources, finish[i] = True
    for i in range(processes_count):
        if sum(allocation[i]) == 0:
            finish[i] = True

    steps = []
    
    while True:
        found = False
        for p in range(processes_count):
            if not finish[p]:
                # Log check
                step_log = {
                    "process": p,
                    "action": "check",
                    "work": list(work),
                    "request": request[p],
                    "message": f"Checking if Request of P{p} <= Work"
                }

                can_grant = True
                for j in range(resources_count):
                    if request[p][j] > work[j]:
                        can_grant = False
                        break
                        
                if can_grant:
                    for j in range(resources_count):
                        work[j] += allocation[p][j]
                    finish[p] = True
                    found = True
                    
                    step_log["status"] = "success"
                    step_log["message"] += f" -> Request can be granted. P{p} executes and releases resources. New Work: {list(work)}."
                    step_log["new_work"] = list(work)
                    steps.append(step_log)
                else:
                    step_log["status"] = "wait"
                    step_log["message"] += f" -> Insufficient resources. P{p} must wait."
                    steps.append(step_log)
                    
        if not found:
            break
            
    deadlocked = []
    for i in range(processes_count):
        if not finish[i]:
            deadlocked.append(i)
            
    if deadlocked:
        steps.append({
            "process": -1,
            "action": "deadlock",
            "message": f"DEADLOCK DETECTED! Processes involved: {['P'+str(i) for i in deadlocked]}",
            "deadlocked": deadlocked
        })
    else:
        steps.append({
            "process": -1,
            "action": "safe",
            "message": "No deadlock detected."
        })
        
    return {
        "hasDeadlock": len(deadlocked) > 0,
        "deadlockedProcesses": deadlocked,
        "steps": steps,
        "finalWork": work
    }
