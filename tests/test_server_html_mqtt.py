# test_server.py - Improved connection test for simulating project connections
# Simulates WiFi setup, HTTP server, and MQTT connection like in main.py
# Includes debug prints and error handling to identify issues

import network
import socket
import utime
import uasyncio as asyncio
from umqtt.simple import MQTTClient  # Added for MQTT simulation
from secrets import ssid, password  # WiFi credentials from secrets.py

# MQTT settings (simulate project's MQTT)
MQTT_BROKER = '192.168.0.100'  # Local broker IP (change as needed)
MQTT_CLIENT_ID = 'test_client'
MQTT_TOPIC = 'test/topic'

def set_station(time_module, network_module, ssid, password):
    """
    WiFi connection function from api_functions.py (simulated here for consistency)
    Configures static IP and DNS as in project.
    """
    print("Starting WiFi connection attempt...")
    station = network_module.WLAN(network_module.STA_IF)
    station.active(True)
    print(f"Connecting to SSID: {ssid}")
    station.connect(ssid, password)
    
    # Static IP and DNS as in api_functions.py (DNS fixed to 8.8.8.8)
    station.ifconfig(('192.168.0.99', '255.255.255.0', '192.168.0.10', '8.8.8.8'))
    ip_address = station.ifconfig()[0]
    
    max_wait = 10  # Increased for reliability
    while max_wait > 0:
        status = station.status()
        print(f"WiFi status: {status} (wait: {max_wait}s)")
        if status < 0 or status >= 3:
            break
        max_wait -= 1
        time_module.sleep(1)
    
    if not station.isconnected():
        print("WiFi connection failed!")
        raise RuntimeError('network connection failed')
    else:
        print("WiFi connected successfully")
        print(f"IP address: {ip_address}")
        print(f"Test server at: http://{ip_address}")
        return True

async def handle_client(reader, writer):
    """
    Simulate HTTP request handling like in main.py.
    """
    print("Incoming client connection")
    try:
        request = await reader.read(1024)
        request_str = request.decode('utf-8', errors='ignore')
        print(f"Request: {request_str[:200]}...")
        
        # Simple response simulating project's HTML
        response = """HTTP/1.1 200 OK
Content-type:text/html

<html><body><h1>Test Server</h1><p>Simulating project API.</p></body></html>"""
        
        writer.write(response.encode())
        await writer.drain()
        print("Response sent")
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print("Connection closed")

async def api_server():
    """
    Simulate async HTTP server like in main.py.
    """
    print("Starting HTTP server...")
    try:
        server = await asyncio.start_server(handle_client, '0.0.0.0', 80)
        print("Server created")
        
        async with server:
            print("Server listening")
            while True:
                await asyncio.sleep(60)
                print("Server tick")
    except OSError as e:
        print(f"Server failed: {e}")
    except Exception as e:
        print(f"Server error: {e}")

async def test_mqtt():
    """
    Simulate MQTT connection and publish like in main.py.
    """
    print("Starting MQTT connection...")
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
        client.connect()
        print("MQTT connected")
        
        while True:
            client.publish(MQTT_TOPIC, "Test message")
            print("MQTT message published")
            await asyncio.sleep(5)
    except OSError as e:
        print(f"MQTT error: {e}")
    except Exception as e:
        print(f"MQTT unexpected error: {e}")

async def main():
    print("=== Starting test_server.py ===")
    
    try:
        set_station(utime, network, ssid, password)
        print("WiFi ready")
    except Exception as e:
        print(f"WiFi failed: {e}")
        return
    
    print("Starting tasks...")
    asyncio.create_task(api_server())
    asyncio.create_task(test_mqtt())
    print("Tasks created")
    
    while True:
        await asyncio.sleep(5)
        print("Main loop tick")

try:
    asyncio.run(main())
except Exception as e:
    print(f"asyncio.run error: {e}")