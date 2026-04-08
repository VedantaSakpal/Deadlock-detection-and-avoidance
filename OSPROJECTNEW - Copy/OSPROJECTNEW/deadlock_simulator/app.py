from flask import Flask, render_template, request, jsonify, session
import os
import sys

# Ensure the algorithms folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from algorithms.banker import run_bankers
from algorithms.detection import run_detection

app = Flask(__name__)
app.secret_key = 'super_secret_deadlock_simulator_key' # In production, use os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard_v2.html')

@app.route('/input')
def input_page():
    return render_template('input.html')

@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    if request.method == 'POST':
        data = request.json
        if data:
            # Process algorithms to get full steps
            mode = data.get('mode')
            num_p = data.get('processes')
            num_r = data.get('resources')
            allocation = data.get('allocation')
            demand = data.get('demand') # Max or Request matrix
            available = data.get('available')
            
            algo_result = {}
            if mode == 'banker':
                algo_result = run_bankers(num_p, num_r, allocation, demand, available)
                
                # We need to send back Need matrix as well
                data['need'] = algo_result.get('need')
            else:
                algo_result = run_detection(num_p, num_r, allocation, demand, available)

            data['result'] = algo_result
            session['sim_data'] = data
            return jsonify({"status": "success"})
    
    # GET request
    sim_data = session.get('sim_data', None)
    if not sim_data:
        return render_template('input.html', error="No simulation data found. Please enter data.")
        
    return render_template('simulation.html', sim_data=sim_data)

from algorithms.recovery import terminate_process, preempt_resource

@app.route('/recover/terminate', methods=['POST'])
def recover_terminate():
    try:
        data = request.get_json(silent=True)
        sim_data = session.get('sim_data', None)
        if not sim_data: 
            return jsonify({"status": "error", "message": "No simulation session active"}), 400
        
        if 'result' not in sim_data or 'deadlockedProcesses' not in sim_data['result']:
            return jsonify({"status": "error", "message": "No deadlock detected in current simulation"}), 400
        
        deadlocks = sim_data['result']['deadlockedProcesses']
        if not deadlocks:
            return jsonify({"status": "error", "message": "No deadlocked processes found"}), 400
        
        # Heuristic: terminate highest numbered deadlocked process
        target_p = deadlocks[-1]
        
        # Validate data structure
        required_keys = ['allocation', 'demand', 'available', 'resources']
        for key in required_keys:
            if key not in sim_data:
                return jsonify({"status": "error", "message": f"Missing required data: {key}"}), 400
        
        rec_result = terminate_process(
            sim_data['allocation'], sim_data['demand'], sim_data['available'], 
            target_p, sim_data['resources']
        )
        
        # Update sim data and rerun detection
        sim_data['allocation'] = rec_result['allocation']
        sim_data['demand'] = rec_result['request']
        sim_data['available'] = rec_result['available']
        
        new_result = run_detection(
            sim_data['processes'], sim_data['resources'], 
            sim_data['allocation'], sim_data['demand'], sim_data['available']
        )
        sim_data['result'] = new_result
        session['sim_data'] = sim_data
        
        return jsonify({"status": "success", "message": rec_result['message']})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500

@app.route('/recover/preempt', methods=['POST'])
def recover_preempt():
    try:
        data = request.get_json(silent=True)
        sim_data = session.get('sim_data', None)
        if not sim_data: 
            return jsonify({"status": "error", "message": "No simulation session active"}), 400
        
        if 'result' not in sim_data or 'deadlockedProcesses' not in sim_data['result']:
            return jsonify({"status": "error", "message": "No deadlock detected in current simulation"}), 400
        
        deadlocks = sim_data['result']['deadlockedProcesses']
        if not deadlocks:
            return jsonify({"status": "error", "message": "No deadlocked processes found"}), 400
        
        target_p = deadlocks[-1]
        
        # Validate data structure
        required_keys = ['allocation', 'demand', 'available', 'resources']
        for key in required_keys:
            if key not in sim_data:
                return jsonify({"status": "error", "message": f"Missing required data: {key}"}), 400
        
        # Find a resource to preempt
        target_r = -1
        for r in range(sim_data['resources']):
            if sim_data['allocation'][target_p][r] > 0:
                target_r = r
                break
                
        if target_r == -1:
            return jsonify({"status": "error", "message": f"No resources to preempt from process P{target_p}."})
            
        rec_result = preempt_resource(
            sim_data['allocation'], sim_data['demand'], sim_data['available'],
            target_p, target_r
        )
        
        if not rec_result['success']:
            return jsonify({"status": "error", "message": rec_result['message']})
        
        sim_data['allocation'] = rec_result['allocation']
        sim_data['demand'] = rec_result['request']
        sim_data['available'] = rec_result['available']
        
        new_result = run_detection(
            sim_data['processes'], sim_data['resources'], 
            sim_data['allocation'], sim_data['demand'], sim_data['available']
        )
        sim_data['result'] = new_result
        session['sim_data'] = sim_data
        
        return jsonify({"status": "success", "message": rec_result['message']})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Internal error: {str(e)}"}), 500

from exports.csv_export import export_csv_data
from exports.pdf_export import export_pdf_data

@app.route('/export/csv', methods=['GET'])
def run_export_csv():
    sim_data = session.get('sim_data', None)
    if not sim_data: return "No active simulation", 400
    return export_csv_data(sim_data)

@app.route('/export/pdf', methods=['GET'])
def run_export_pdf():
    sim_data = session.get('sim_data', None)
    if not sim_data: return "No active simulation", 400
    return export_pdf_data(sim_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
