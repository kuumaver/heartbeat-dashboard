# gps_parser.py - A simple library for parsing NMEA GPS data
# For use with UART GPS modules on Raspberry Pi Pico

import serial
import time

class GPSData:
    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.has_fix = False
        self.satellites = 0
        self.speed_knots = 0.0
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0
        self.time = ""
        self.date = ""

class GPSReader:
    def __init__(self, port="/dev/ttyAMA0", baudrate=9600):
        self.uart = serial.Serial(port, baudrate, timeout=0)  # non-blocking
        self.message_buffer = ""
        self.last_data_time = time.monotonic() * 1000
        self.timeout_ms = 500
        self.current_data = GPSData()
        self.has_new_data = False

    def update(self):
        self.has_new_data = False
        current_time = time.monotonic() * 1000  # ms

        if (current_time - self.last_data_time) > self.timeout_ms and self.message_buffer:
            self._process_buffer()
            self.has_new_data = True

        bytes_available = self.uart.in_waiting  # replaces uart.any()
        if bytes_available > 0:
            try:
                data = self.uart.read(bytes_available).decode('utf-8', errors='replace')
                if not self.message_buffer or (current_time - self.last_data_time) <= self.timeout_ms:
                    self.message_buffer += data
                else:
                    self._process_buffer()
                    self.message_buffer = data
                    self.has_new_data = True
                self.last_data_time = current_time
            except Exception as e:
                print(f"Error reading GPS data: {e}")

        return self.has_new_data
    
    def get_data(self):
        """
        Get the current GPS data.
        Automatically updates before returning the data.
        
        Returns:
            GPSData: The current GPS data object with the most recent reading
        """
        self.update()
        return self.current_data
    
    def _process_buffer(self):
        """Process the complete message in buffer"""
        if not self.message_buffer:
            return
        
        self.current_data = _process_nmea_data(self.message_buffer)
        self.message_buffer = ""
    
    # Convenience properties for direct access to GPS data
    @property
    def latitude(self):
        """Get the current latitude"""
        self.update()
        return self.current_data.latitude
    
    @property
    def longitude(self):
        """Get the current longitude"""
        self.update()
        return self.current_data.longitude
    
    @property
    def altitude(self):
        """Get the current altitude"""
        self.update()
        return self.current_data.altitude
    
    @property
    def has_fix(self):
        """Get the current fix status"""
        self.update()
        return self.current_data.has_fix
    
    @property
    def satellites(self):
        """Get the current number of satellites"""
        self.update()
        return self.current_data.satellites
    
    @property
    def speed(self):
        """Get the current speed in knots"""
        self.update()
        return self.current_data.speed_knots
    
    @property
    def time(self):
        """Get the current GPS time"""
        self.update()
        return self.current_data.time
    
    @property
    def date(self):
        """Get the current GPS date"""
        self.update()
        return self.current_data.date

# For backward compatibility
def parse_gps_data(nmea_chunk):
    """Legacy function to parse GPS data (for compatibility)"""
    return _process_nmea_data(nmea_chunk)

# def _process_nmea_data(nmea_data):
#     """Process a complete NMEA data string"""
#     # Initialize data class
#     gps_data = GPSData()
    
#     # Split the chunk into individual NMEA sentences
#     sentences = nmea_data.strip().split('$')
    
#     # Process each sentence
#     for sentence in sentences:
#         if not sentence:
#             continue
            
#         # Add the $ back for proper format
#         sentence = '$' + sentence.strip()
        
#         # Parse different sentence types
#         if sentence.startswith('$GPRMC') or sentence.startswith('$GNRMC'):
#             _parse_rmc(sentence, gps_data)
#         elif sentence.startswith('$GPGGA') or sentence.startswith('$GNGGA'):
#             _parse_gga(sentence, gps_data)
#         elif sentence.startswith('$GPGSA') or sentence.startswith('$GNGSA'):
#             _parse_gsa(sentence, gps_data)
    
#     return gps_data

def _process_nmea_data(nmea_data):
    """Process a complete NMEA data string"""
    # Initialize data class
    gps_data = GPSData()
    
    # Split the chunk into individual NMEA sentences
    sentences = nmea_data.strip().split('$')
    
    fix_seen_this_batch = False
    
    # Process each sentence
    for sentence in sentences:
        if not sentence:
            continue
            
        # Add the $ back for proper format
        sentence = '$' + sentence.strip()
        
        # Parse different sentence types
        if sentence.startswith('$GPRMC') or sentence.startswith('$GNRMC'):
            _parse_rmc(sentence, gps_data)
            if gps_data.has_fix:
                fix_seen_this_batch = True
            elif fix_seen_this_batch:
                # A later sentence in this same batch reported void status,
                # but an earlier one in the batch already had a valid fix.
                # Don't let this stray void downgrade the fix we already got.
                gps_data.has_fix = True
        elif sentence.startswith('$GPGGA') or sentence.startswith('$GNGGA'):
            _parse_gga(sentence, gps_data)
        elif sentence.startswith('$GPGSA') or sentence.startswith('$GNGSA'):
            _parse_gsa(sentence, gps_data)
    
    return gps_data
# ------------------------------------------------------------------------------------------
def _parse_rmc(sentence, gps_data):
    """Parse RMC sentence for time, date, location, and speed"""
    
    # Split the sentence into parts
    parts = sentence.split(',')
    #print(f"DEBUG parts[2]: '{parts[2]}'")
    
    if len(parts) < 12:
        return
    
    # Check if we have a fix
    if parts[2] == 'A':
        gps_data.has_fix = True
    else:
        gps_data.has_fix = False
        # Don't return here, continue to extract time and date
    
    # Extract time (format: HHMMSS.SS) with error handling
    if parts[1] and len(parts[1]) >= 6:
        try:
            hour = parts[1][0:2]
            minute = parts[1][2:4]
            second = parts[1][4:]
            gps_data.time = f"{hour}:{minute}:{second}"
        except (ValueError, IndexError):
            # Keep the existing time value if parsing fails
            pass
    
    # Extract date (format: DDMMYY) with error handling
    if parts[9] and len(parts[9]) >= 6:
        try:
            day = parts[9][0:2]
            month = parts[9][2:4]
            year = "20" + parts[9][4:6]  # Assuming we're in the 2000s
            gps_data.date = f"{day}/{month}/{year}"
        except (ValueError, IndexError):
            # Keep the existing date value if parsing fails
            pass
    
    # Only extract position and speed if we have a valid fix
    if gps_data.has_fix:
        # Extract latitude and longitude with sign based on direction
        if parts[3] and parts[5]:
            try:
                # Latitude
                lat_deg = float(parts[3][0:2])
                lat_min = float(parts[3][2:])
                lat_decimal = lat_deg + (lat_min / 60)
                
                # Apply sign based on direction (N is positive, S is negative)
                if parts[4] == 'S':
                    lat_decimal = -lat_decimal
                gps_data.latitude = lat_decimal
                
                # Longitude
                lon_deg = float(parts[5][0:3])
                lon_min = float(parts[5][3:])
                lon_decimal = lon_deg + (lon_min / 60)
                
                # Apply sign based on direction (E is positive, W is negative)
                if parts[6] == 'W':
                    lon_decimal = -lon_decimal
                gps_data.longitude = lon_decimal
            except (ValueError, IndexError):
                # If parsing fails, don't update coordinates
                pass
        
        # Extract speed in knots
        if parts[7]:
            try:
                gps_data.speed_knots = float(parts[7])
            except ValueError:
                gps_data.speed_knots = 0.0

def _parse_gga(sentence, gps_data):
    """Parse GGA sentence for satellites, altitude, and HDOP"""
    
    parts = sentence.split(',')
    
    if len(parts) < 15:
        return
    
    # Extract number of satellites
    if parts[7]:
        try:
            gps_data.satellites = int(parts[7])
        except ValueError:
            gps_data.satellites = 0
    
    # Extract HDOP (Horizontal Dilution of Precision)
    if parts[8]:
        try:
            gps_data.hdop = float(parts[8])
        except ValueError:
            gps_data.hdop = 0.0
    
    # Extract altitude
    if parts[9] and parts[10] == 'M':
        try:
            gps_data.altitude = float(parts[9])
        except ValueError:
            gps_data.altitude = 0.0

def _parse_gsa(sentence, gps_data):    
    parts = sentence.split(',')
    
    if len(parts) < 18:
        return
    
    try:
        if parts[15]:
            gps_data.pdop = float(parts[15])
    except (ValueError, IndexError):
        pass
    
    
    try:
        if parts[16]:
            gps_data.hdop = float(parts[16])
    except (ValueError, IndexError):
        pass
    
    
    try:
        vdop_str = parts[17].split('*')[0]
        if vdop_str:
            gps_data.vdop = float(vdop_str)
    except (ValueError, IndexError):
        pass