from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Service for interacting with InfluxDB time-series database"""

    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None

    def connect(self):
        """Connect to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("Connected to InfluxDB")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def disconnect(self):
        """Disconnect from InfluxDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from InfluxDB")

    def write_sensor_data(
        self,
        device_id: str,
        device_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """Write sensor data to InfluxDB"""
        try:
            point = Point("sensor_data") \
                .tag("device_id", device_id) \
                .tag("device_type", device_type)

            # Add all data fields
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    point = point.field(key, float(value))
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    point = point.field(key, value)

            # Set timestamp
            if timestamp:
                point = point.time(timestamp)

            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )

        except Exception as e:
            logger.error(f"Failed to write sensor data to InfluxDB: {e}")
            raise

    def write_batch_sensor_data(
        self,
        device_id: str,
        device_type: str,
        data_points: List[Dict[str, Any]]
    ):
        """Write batch sensor data to InfluxDB"""
        try:
            points = []
            for data_point in data_points:
                timestamp = data_point.pop('timestamp', None)
                point = Point("sensor_data") \
                    .tag("device_id", device_id) \
                    .tag("device_type", device_type)

                for key, value in data_point.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, float(value))
                    elif isinstance(value, bool):
                        point = point.field(key, value)
                    elif isinstance(value, str):
                        point = point.field(key, value)

                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    point = point.time(timestamp)

                points.append(point)

            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=points
            )

        except Exception as e:
            logger.error(f"Failed to write batch sensor data to InfluxDB: {e}")
            raise

    def query_device_data(
        self,
        device_id: str,
        start_time: str = "-1h",
        stop_time: str = "now()",
        measurement: str = "sensor_data"
    ) -> List[Dict[str, Any]]:
        """Query device data from InfluxDB"""
        try:
            query = f'''
                from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: {start_time}, stop: {stop_time})
                |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
            '''

            result = self.query_api.query(org=settings.INFLUXDB_ORG, query=query)

            data_points = []
            for table in result:
                for record in table.records:
                    data_points.append({
                        'time': record.get_time(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        'device_id': record.values.get('device_id'),
                        'device_type': record.values.get('device_type'),
                    })

            return data_points

        except Exception as e:
            logger.error(f"Failed to query device data from InfluxDB: {e}")
            raise

    def query_aggregated_data(
        self,
        device_type: str,
        field: str,
        aggregation: str = "mean",
        window: str = "1h",
        start_time: str = "-24h"
    ) -> List[Dict[str, Any]]:
        """Query aggregated data from InfluxDB"""
        try:
            query = f'''
                from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: {start_time})
                |> filter(fn: (r) => r["_measurement"] == "sensor_data")
                |> filter(fn: (r) => r["device_type"] == "{device_type}")
                |> filter(fn: (r) => r["_field"] == "{field}")
                |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
            '''

            result = self.query_api.query(org=settings.INFLUXDB_ORG, query=query)

            data_points = []
            for table in result:
                for record in table.records:
                    data_points.append({
                        'time': record.get_time(),
                        'value': record.get_value(),
                        'device_type': record.values.get('device_type'),
                    })

            return data_points

        except Exception as e:
            logger.error(f"Failed to query aggregated data from InfluxDB: {e}")
            raise


# Global instance
influxdb_service = InfluxDBService()
