import data as d
import math as m
from flask import Flask, render_template, request
from pprint import pprint

__author__ = 'dana'

app = Flask(__name__)


def get_peak_gain(antennas, frequency, speed_of_light):
    global peak_gain, half_power_angle

    for antenna in antennas:
        if antenna.antenna_type == "parabolic":
            half_power_angle = 21 / (frequency * antenna.diameter)  # deg
            if antenna.efficiency == 0.55:
                peak_gain = 20 * m.log10(antenna.diameter) + 20 * m.log10(frequency) + 17.8  # dB
            else:
                peak_gain = -159.59 + 20 * m.log10(antenna.diameter) + 20 * m.log10(frequency * pow(10, 9)) + \
                            10 * m.log(antenna.efficiency)
        if antenna.antenna_type == "horn":
            half_power_angle = 225 * speed_of_light / (m.pi * antenna.diameter * antenna.efficiency)
            if antenna.efficiency == 0.52:
                peak_gain = 20 * m.log10(antenna.diameter * m.pi * frequency / speed_of_light) - 2.8
            else:
                peak_gain = -159.59 + 20 * m.log10(antenna.diameter) + 20 * m.log10(
                    frequency * pow(10, 9)) + 10 * m.log(
                    antenna.efficiency)
        if antenna.antenna_type == "helical":
            half_power_angle = 52 / m.sqrt(pow(m.pi, 2) * pow(antenna.diameter, 2) * antenna.helix_length *
                                           pow(frequency, 3) / pow(speed_of_light, 3))
            if antenna.efficiency == 0.7:
                peak_gain = 10 * m.log10(pow(antenna.diameter, 2) * pow(m.pi, 2) * pow(frequency, 3) *
                                         antenna.helix_length / pow(speed_of_light, 3)) - 2.8
            else:
                peak_gain = -159.59 + 20 * m.log10(antenna.diameter) + 20 * m.log10(frequency * pow(10, 9)) + \
                            10 * m.log(antenna.efficiency)

        setattr(antenna, 'peak_gain', peak_gain)
        setattr(antenna, 'half_power_angle', half_power_angle)

    return antennas


def get_pointing_loss(spacecraft, ground_station, mode):
    global receiver_pointing_loss, transmitter_pointing_loss
    if mode == "uplink":
        transmitter_pointing_loss = -12 * pow((0.1), 2)
        receiver_pointing_loss = -12 * pow((spacecraft.pointing_offset_angle / spacecraft.half_power_angle), 2)
    elif mode == "downlink":
        receiver_pointing_loss = -12 * pow((0.1), 2)
        transmitter_pointing_loss = -12 * pow((spacecraft.pointing_offset_angle / spacecraft.half_power_angle), 2)

    return receiver_pointing_loss + transmitter_pointing_loss


def get_noise_temperature(mode, frequency):
    global system_noise_temperature
    if mode == "downlink":
        if frequency == 0.2:
            system_noise_temperature = 221
        elif 2 < frequency < 12:
            system_noise_temperature = 135
        elif frequency == 20:
            system_noise_temperature = 424
    elif mode == "uplink":
        if 2 < frequency < 20:
            system_noise_temperature = 614
        elif frequency == 40:
            system_noise_temperature = 763

    return system_noise_temperature


def get_space_loss(mission_params, frequency):
    global worst_case_distance
    if mission_params.mission_type == "earth_orbiting":
        worst_case_distance = m.sqrt(pow((mission_params.earth_radius + mission_params.orbit_altitude), 2) -
                                     pow(mission_params.earth_radius, 2))
    elif mission_params.mission_type == "interplanetary":
        worst_case_distance = m.sqrt(pow(mission_params.earth_to_sun_distance, 2) +
                                     pow(mission_params.sc_sun_distance, 2) - 2 * mission_params.earth_to_sun_distance *
                                     mission_params.sc_sun_distance * m.cos(mission_params.elongation_angle))
    elif mission_params.mission_type == "lunar":
        worst_case_distance = m.sqrt(pow((mission_params.body_radius + mission_params.orbit_altitude), 2) -
                                     pow(mission_params.body_radius, 2))

    space_loss = 147.55 - 20 * m.log10(worst_case_distance) - 20 * m.log10(frequency * pow(10, 9))

    return space_loss


def get_required_data_rate(payload_params, sc_velocity, mode, mission):
    global required_data_rate
    if mode == "downlink":
        generated_data_rate = payload_params.payload_bits_per_pixel * m.tan(
            payload_params.swath_width_angle) * 2 * mission.orbit_altitude * sc_velocity / \
                              pow(to_rad(payload_params.payload_pixel_size) * 701031, 2)
        required_data_rate = generated_data_rate * payload_params.duty_cycle / payload_params.downlink_time
    elif mode == "uplink":
        required_data_rate = mission.required_uplink_data_rate

    pprint(m.tan(
        payload_params.swath_width_angle))

    return required_data_rate


def to_rad(value):
    return value * m.pi / 10800


def get_spacecraft_velocity(gravitational_parameter, radius_of_the_body, orbit_altitude):
    velocity = m.sqrt(gravitational_parameter / (radius_of_the_body + orbit_altitude))

    return velocity


def get_snr(mode, satellite, ground_station, mission, space_loss, pointing_loss, required_data_rate, k,
            system_noise_temperature):
    global transmitter_power, gain_transmitter, gain_receiver, atmospheric_attenuation

    if mode == "downlink":
        transmitter_power = to_db(satellite.transmitter_power)
        gain_transmitter = satellite.peak_gain
        gain_receiver = ground_station.peak_gain
        atmospheric_attenuation = mission.downlink_atmospheric_attenuation
    elif mode == "uplink":
        transmitter_power = to_db(ground_station.transmitter_power)
        gain_transmitter = ground_station.peak_gain
        gain_receiver = satellite.peak_gain
        atmospheric_attenuation = mission.uplink_atmospheric_attenuation

    snr = transmitter_power + to_db(satellite.transmitter_loss_factor) + gain_transmitter + atmospheric_attenuation + \
          space_loss + pointing_loss + gain_receiver + 228.6 - to_db(system_noise_temperature) - to_db(
        required_data_rate)

    return snr


def get_snr_margin(required_snr, snr):
    margin = snr - required_snr
    return margin


def to_db(value):
    value_in_db = 10 * m.log10(value)
    return value_in_db


def get_eipr(mode, satellite, ground_station):
    global peak_gain, transmitter_power
    if mode == "downlink":
        transmitter_power = satellite.transmitter_power
        peak_gain = satellite.peak_gain


    elif mode == "uplink":
        transmitter_power = ground_station.transmitter_power
        peak_gain = ground_station.peak_gain

    return transmitter_power * peak_gain * satellite.transmitter_loss_factor


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/output', methods=['POST', 'GET'])
def output():
    antenna_type = request.form['antenna_type']
    satellite_antenna_diameter = float(request.form['satellite_antenna_diameter'])
    ground_station_antenna_diameter = float(request.form['ground_station_antenna_diameter'])
    satellite_antenna_efficiency = float(request.form['satellite_antenna_efficiency'])
    ground_station_antenna_efficiency = float(request.form['ground_station_antenna_efficiency'])
    satellite_antenna_helix_length = float(request.form['satellite_antenna_helix_length'])
    ground_station_antenna_helix_length = float(request.form['ground_station_antenna_helix_length'])
    pointing_offset_angle = float(request.form['pointing_offset_angle'])
    transmitter_power_satellite = float(request.form['transmitter_power_satellite'])
    transmitter_power_groundstation = float(request.form['transmitter_power_groundstation'])
    transmitter_loss_factor = float(request.form['transmitter_loss_factor'])
    total_sc_power = float(request.form['total_sc_power'])
    receiver_loss_factor = float(request.form['receiver_loss_factor'])
    orbit_altitude = float(request.form['orbit_altitude'])
    elongation_angle = float(request.form['elongation_angle'])
    required_uplink_data_rate = float(request.form['required_uplink_data_rate'])
    swath_width_angle = float(request.form['swath_width_angle'])
    payload_pixel_size = float(request.form['payload_pixel_size'])
    payload_bits_per_pixel = float(request.form['payload_bits_per_pixel'])
    duty_cycle = float(request.form['duty_cycle'])
    downlink_time = float(request.form['downlink_time'])
    required_ber = float(request.form['required_ber'])
    mode = request.form['mode']
    downlink_frequency = float(request.form['downlink_frequency'])
    turn_around_ratio = float(request.form['turn_around_ratio'])
    mission_type = request.form['mission_type']
    sc_sun_distance = float(request.form['sc_sun_distance'])
    gravitational_parameter = float(request.form['gravitational_parameter'])
    body_radius = float(request.form['body_radius'])
    required_snr = float(request.form['required_snr'])
    downlink_atmospheric_attenuation = float(request.form['downlink_atmospheric_attenuation'])
    uplink_atmospheric_attenuation = float(request.form['uplink_atmospheric_attenuation'])

    satellite = d.Satelite(antenna_type, satellite_antenna_diameter, satellite_antenna_efficiency,
                           satellite_antenna_helix_length, transmitter_power_satellite, transmitter_loss_factor,
                           total_sc_power, pointing_offset_angle)

    ground_station = d.GroundStation(antenna_type, ground_station_antenna_diameter, ground_station_antenna_efficiency,
                                     ground_station_antenna_helix_length,
                                     transmitter_power_groundstation, receiver_loss_factor)

    mission = d.Mission(orbit_altitude, elongation_angle,
                        required_uplink_data_rate, mission_type, sc_sun_distance,
                        gravitational_parameter, body_radius, downlink_atmospheric_attenuation,
                        uplink_atmospheric_attenuation)

    payload = d.Payload(swath_width_angle, payload_pixel_size, payload_bits_per_pixel, duty_cycle, downlink_time,
                        required_ber)

    calculation = d.Calculation(mode, downlink_frequency, turn_around_ratio, required_snr)

    mode = calculation.mode

    global frequency, transmitter_power, transmitter_antenna_gain, receiver_antenna_gain, atmospheric_attenuation
    if mode == "downlink":
        frequency = calculation.downlink_frequency
    elif mode == "uplink":
        frequency = calculation.downlink_frequency * calculation.turn_around_ratio

    antennas = [satellite, ground_station]

    antennas = get_peak_gain(antennas, frequency, calculation.c)

    satellite = antennas[0]
    ground_station = antennas[1]

    pointing_loss = get_pointing_loss(satellite, ground_station, mode)
    system_noise_temperature = get_noise_temperature(mode, frequency)
    space_loss = get_space_loss(mission, frequency)
    sc_velocity = get_spacecraft_velocity(mission.gravitational_parameter, mission.body_radius, mission.orbit_altitude)
    required_data_rate = get_required_data_rate(payload, sc_velocity, mode, mission)
    snr = get_snr(mode, satellite, ground_station, mission, space_loss, pointing_loss, required_data_rate,
                  calculation.k, system_noise_temperature)
    snr_margin = get_snr_margin(calculation.required_snr, snr)

    if mode == "downlink":
        transmitter_power = satellite.transmitter_power
        transmitter_antenna_gain = satellite.peak_gain
        receiver_antenna_gain = ground_station.peak_gain
        atmospheric_attenuation = mission.downlink_atmospheric_attenuation
    elif mode == "uplink":
        transmitter_power = ground_station.transmitter_power
        transmitter_antenna_gain = ground_station.peak_gain
        receiver_antenna_gain = satellite.peak_gain
        atmospheric_attenuation = mission.uplink_atmospheric_attenuation

    results = {
        "mode": mode,
        "received_snr": snr,
        "snr_margin": snr_margin,
        "space_loss": space_loss,
        "transmitter_power": to_db(transmitter_power),
        "loss_factor_transmitter": to_db(satellite.transmitter_loss_factor),
        "transmitter_antenna_gain": transmitter_antenna_gain,
        "transmission_path_loss": atmospheric_attenuation,
        "receiver_antenna_gain": receiver_antenna_gain,
        "antenna_pointing_loss": pointing_loss,
        "loss_factor_receiver": to_db(ground_station.receiver_loss_factor),
        "required_data_rate": to_db(1 / required_data_rate),
        "system_noise_temperature": to_db(1 / system_noise_temperature),
        "required_snr": required_snr
    }

    return render_template('output.html', results=results)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9696, debug=True)
