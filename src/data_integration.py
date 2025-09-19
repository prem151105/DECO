import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import threading

class UnifiedNamespaceSimulator:
    """Simulates a Unified Namespace for real-time data integration"""

    def __init__(self):
        self.assets = {
            'train_001': {'type': 'rolling_stock', 'status': 'operational', 'location': 'station_A'},
            'track_005': {'type': 'infrastructure', 'status': 'maintenance', 'location': 'sector_B'},
            'signal_010': {'type': 'signaling', 'status': 'active', 'location': 'junction_C'},
            'power_020': {'type': 'electrical', 'status': 'warning', 'location': 'depot_D'}
        }
        self.iot_sensors = {}
        self._generate_sensors()
        self.running = False

    def _generate_sensors(self):
        """Generate mock IoT sensors for assets"""
        for asset_id, asset_info in self.assets.items():
            self.iot_sensors[asset_id] = {
                'temperature': random.uniform(20, 80),
                'vibration': random.uniform(0, 10),
                'pressure': random.uniform(0, 100),
                'last_updated': datetime.now().isoformat()
            }

    def get_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Get current data for a specific asset"""
        if asset_id in self.assets:
            data = self.assets[asset_id].copy()
            data.update(self.iot_sensors.get(asset_id, {}))
            return data
        return {}

    def get_all_assets(self) -> Dict[str, Dict[str, Any]]:
        """Get data for all assets"""
        all_data = {}
        for asset_id, asset_info in self.assets.items():
            all_data[asset_id] = asset_info.copy()
            all_data[asset_id].update(self.iot_sensors.get(asset_id, {}))
        return all_data

    def update_sensor_data(self):
        """Simulate real-time sensor updates"""
        while self.running:
            for asset_id in self.iot_sensors:
                # Simulate realistic sensor fluctuations
                self.iot_sensors[asset_id]['temperature'] += random.uniform(-2, 2)
                self.iot_sensors[asset_id]['temperature'] = max(15, min(100, self.iot_sensors[asset_id]['temperature']))

                self.iot_sensors[asset_id]['vibration'] += random.uniform(-0.5, 0.5)
                self.iot_sensors[asset_id]['vibration'] = max(0, self.iot_sensors[asset_id]['vibration'])

                self.iot_sensors[asset_id]['pressure'] += random.uniform(-5, 5)
                self.iot_sensors[asset_id]['pressure'] = max(0, self.iot_sensors[asset_id]['pressure'])

                self.iot_sensors[asset_id]['last_updated'] = datetime.now().isoformat()

                # Simulate alerts
                if self.iot_sensors[asset_id]['temperature'] > 75:
                    self.assets[asset_id]['status'] = 'critical'
                elif self.iot_sensors[asset_id]['temperature'] > 60:
                    self.assets[asset_id]['status'] = 'warning'
                else:
                    self.assets[asset_id]['status'] = 'operational'

            time.sleep(5)  # Update every 5 seconds

    def start_simulation(self):
        """Start the real-time data simulation"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.update_sensor_data)
            self.thread.daemon = True
            self.thread.start()

    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()

class MaximoSimulator:
    """Simulates IBM Maximo integration for work orders and asset management"""

    def __init__(self):
        self.work_orders = [
            {
                'wo_id': 'WO001',
                'asset_id': 'train_001',
                'description': 'Scheduled maintenance on rolling stock',
                'status': 'open',
                'priority': 'high',
                'due_date': (datetime.now() + timedelta(days=7)).isoformat()
            },
            {
                'wo_id': 'WO002',
                'asset_id': 'track_005',
                'description': 'Track inspection and repair',
                'status': 'in_progress',
                'priority': 'medium',
                'due_date': (datetime.now() + timedelta(days=3)).isoformat()
            }
        ]

    def get_work_orders(self, asset_id: str = None) -> List[Dict[str, Any]]:
        """Get work orders, optionally filtered by asset"""
        if asset_id:
            return [wo for wo in self.work_orders if wo['asset_id'] == asset_id]
        return self.work_orders

    def link_document_to_work_order(self, doc_id: str, wo_id: str) -> bool:
        """Link a document to a work order"""
        for wo in self.work_orders:
            if wo['wo_id'] == wo_id:
                if 'linked_documents' not in wo:
                    wo['linked_documents'] = []
                wo['linked_documents'].append(doc_id)
                return True
        return False

class SharePointSimulator:
    """Simulates SharePoint integration for document management"""

    def __init__(self):
        self.documents = {
            'doc001': {
                'title': 'Safety Bulletin 2024',
                'path': '/sites/KMRL/Safety/Bulletin2024.pdf',
                'metadata': {'department': 'Safety', 'type': 'bulletin'}
            },
            'doc002': {
                'title': 'Maintenance Manual v2',
                'path': '/sites/KMRL/Maintenance/Manual.pdf',
                'metadata': {'department': 'Maintenance', 'type': 'manual'}
            }
        }

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents in SharePoint"""
        results = []
        query_lower = query.lower()
        for doc_id, doc_info in self.documents.items():
            if query_lower in doc_info['title'].lower() or query_lower in str(doc_info['metadata']).lower():
                results.append({'doc_id': doc_id, **doc_info})
        return results

    def get_document_metadata(self, doc_id: str) -> Dict[str, Any]:
        """Get metadata for a specific document"""
        return self.documents.get(doc_id, {})