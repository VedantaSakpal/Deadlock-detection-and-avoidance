import csv
from io import StringIO
from flask import Response

def export_csv_data(sim_data):
    si = StringIO()
    cw = csv.writer(si)
    
    cw.writerow(['Deadlock Simulator Report'])
    cw.writerow(['Mode', sim_data.get('mode', 'N/A')])
    cw.writerow(['Processes', sim_data.get('processes', 0)])
    cw.writerow(['Resources', sim_data.get('resources', 0)])
    cw.writerow([])
    
    cw.writerow(['Initial Available Resources'])
    cw.writerow(sim_data.get('available', []))
    cw.writerow([])
    
    cw.writerow(['Process matrices'])
    header = ['Process', 'Allocation', 'Demand/Request']
    cw.writerow(header)
    
    alloc = sim_data.get('allocation', [])
    demand = sim_data.get('demand', [])
    
    for i in range(sim_data.get('processes', 0)):
        row = [f'P{i}', str(alloc[i]), str(demand[i])]
        cw.writerow(row)
        
    cw.writerow([])
    cw.writerow(['Execution Result'])
    result = sim_data.get('result', {})
    if 'isSafe' in result:
        cw.writerow(['Safe Sequence Documented', result['isSafe']])
        if result['isSafe']:
            cw.writerow(['Safe Sequence', " -> ".join(['P'+str(p) for p in result['safeSequence']])])
    else:
        cw.writerow(['Has Deadlock', result.get('hasDeadlock', False)])
        if result.get('hasDeadlock'):
            cw.writerow(['Deadlocked Processes', result.get('deadlockedProcesses')])
            
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=deadlock_report.csv"}
    )
