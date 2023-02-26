class Calculation:
    def __init__(self, mode, downlink_frequency, turn_around_ratio, required_snr):
        self.mode = mode
        self.downlink_frequency = downlink_frequency
        self.turn_around_ratio = turn_around_ratio
        self.required_snr = required_snr

        # Constants
        self.c = 299792458
        self.k = 1.38064852 * pow(10, -23)

        self.system_noise_temperature = None

class Mission:
    def __init__(self, orbit_altitude , elongation_angle,
                  required_uplink_data_rate, mission_type, sc_sun_distance,
                 gravitational_parameter, body_radius, downlink_atmospheric_attenuation, uplink_atmospheric_attenuation):

        self.orbit_altitude = orbit_altitude
        self.elongation_angle = elongation_angle
        self.required_uplink_data_rate = required_uplink_data_rate
        self.mission_type = mission_type
        self.sc_sun_distance = sc_sun_distance
        self.gravitational_parameter = gravitational_parameter
        self.body_radius = body_radius
        self.downlink_atmospheric_attenuation = downlink_atmospheric_attenuation
        self.uplink_atmospheric_attenuation = uplink_atmospheric_attenuation

        self.earth_radius = 6371000
        self.earth_to_sun_distance =  149597870700


        self.system_noise_temperature = None

class Payload:
    def __init__(self, swath_width_angle, payload_pixel_size, payload_bits_per_pixel, duty_cycle, downlink_time,
                 required_ber):
        self.swath_width_angle = swath_width_angle
        self.payload_pixel_size = payload_pixel_size
        self.payload_bits_per_pixel = payload_bits_per_pixel
        self.duty_cycle = duty_cycle
        self.downlink_time = downlink_time
        self.required_ber = required_ber


class Satelite:

    def __init__(self, antenna_type, diameter, efficiency, helix_length, transmitter_power, transmitter_loss_factor,
                 total_sc_power, pointing_offset_angle):
        # Variables
        self.antenna_type = antenna_type
        self.diameter = diameter
        self.efficiency = efficiency
        self.helix_length = helix_length
        self.transmitter_power = transmitter_power
        self.transmitter_loss_factor = transmitter_loss_factor
        self.total_sc_power = total_sc_power
        self.pointing_offset_angle = pointing_offset_angle

        # Results
        self.peak_gain = None
        self.half_power_angle = None
        self.pointing_loss = None


class GroundStation:

    def __init__(self, antenna_type, diameter, efficiency, helix_length, transmitter_power,
                 receiver_loss_factor):
        # Variables
        self.antenna_type = antenna_type
        self.diameter = diameter
        self.efficiency = efficiency
        self.helix_length = helix_length
        self.transmitter_power = transmitter_power
        self.receiver_loss_factor = receiver_loss_factor

        # Results
        self.peak_gain = None
        self.half_power_angle = None
        self.pointing_loss = None

