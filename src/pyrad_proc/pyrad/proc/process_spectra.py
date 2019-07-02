"""
pyrad.proc.process_spectra
==========================

Functions to processes spectral data.

.. autosummary::
    :toctree: generated/

    process_raw_spectra
    process_spectra_point
    process_filter_0Doppler
    process_filter_srhohv
    process_filter_spectra_noise
    process_spectral_power
    process_spectral_phase
    process_spectral_reflectivity
    process_spectral_differential_reflectivity
    process_spectral_differential_phase
    process_spectral_rhohv
    process_pol_variables
    process_reflectivity
    process_differential_reflectivity
    process_differential_phase
    process_rhohv
    process_Doppler_velocity
    process_Doppler_width

"""

from copy import deepcopy
from warnings import warn
import numpy as np
from netCDF4 import num2date

import pyart

from ..io.io_aux import get_datatype_fields, get_fieldname_pyart


def process_raw_spectra(procstatus, dscfg, radar_list=None):
    """
    Dummy function that returns the initial input data set

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, _, _, _ = get_datatype_fields(datatypedescr)
        break
    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    new_dataset = {'radar_out': deepcopy(radar_list[ind_rad])}

    return new_dataset, ind_rad


def process_spectra_point(procstatus, dscfg, radar_list=None):
    """
    Obtains the spectra data at a point location.

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted Configuration Keywords::

        datatype : string. Dataset keyword
            The data type where we want to extract the point measurement
        latlon : boolean. Dataset keyword
            if True position is obtained from latitude, longitude information,
            otherwise position is obtained from antenna coordinates
            (range, azimuth, elevation).
        truealt : boolean. Dataset keyword
            if True the user input altitude is used to determine the point of
            interest.
            if False use the altitude at a given radar elevation ele over the
            point of interest.
        lon : float. Dataset keyword
            the longitude [deg]. Use when latlon is True.
        lat : float. Dataset keyword
            the latitude [deg]. Use when latlon is True.
        alt : float. Dataset keyword
            altitude [m MSL]. Use when latlon is True.
        ele : float. Dataset keyword
            radar elevation [deg]. Use when latlon is False or when latlon is
            True and truealt is False
        azi : float. Dataset keyword
            radar azimuth [deg]. Use when latlon is False
        rng : float. Dataset keyword
            range from radar [m]. Use when latlon is False
        AziTol : float. Dataset keyword
            azimuthal tolerance to determine which radar azimuth to use [deg]
        EleTol : float. Dataset keyword
            elevation tolerance to determine which radar elevation to use [deg]
        RngTol : float. Dataset keyword
            range tolerance to determine which radar bin to use [m]

    radar_list : list of Radar objects
          Optional. list of radar objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the data and metadata at the point of interest
    ind_rad : int
        radar index

    """
    if procstatus == 0:
        return None, None

    field_names = []
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        field_names.append(get_fieldname_pyart(datatype))

    ind_rad = int(radarnr[5:8])-1

    if procstatus == 2:
        if dscfg['initialized'] == 0:
            return None, None

        # prepare for exit
        new_dataset = {
            'radar_out': dscfg['global_data']['psr_poi'],
            'point_coordinates_WGS84_lon_lat_alt': (
                dscfg['global_data']['point_coordinates_WGS84_lon_lat_alt']),
            'antenna_coordinates_az_el_r': (
                dscfg['global_data']['antenna_coordinates_az_el_r']),
            'final': True}

        return new_dataset, ind_rad

    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid psr')
        return None, None
    psr = radar_list[ind_rad]

    projparams = dict()
    projparams.update({'proj': 'pyart_aeqd'})
    projparams.update({'lon_0': psr.longitude['data']})
    projparams.update({'lat_0': psr.latitude['data']})

    truealt = dscfg.get('truealt', True)
    latlon = dscfg.get('latlon', False)

    if latlon:
        lon = dscfg['lon']
        lat = dscfg['lat']
        alt = dscfg.get('alt', 0.)
        latlon_tol = dscfg.get('latlonTol', 1.)
        alt_tol = dscfg.get('altTol', 100.)

        x, y = pyart.core.geographic_to_cartesian(lon, lat, projparams)

        if not truealt:
            ke = 4./3.  # constant for effective radius
            a = 6378100.  # earth radius
            re = a * ke  # effective radius

            elrad = dscfg['ele'] * np.pi / 180.
            r_ground = np.sqrt(x ** 2. + y ** 2.)
            r = r_ground / np.cos(elrad)
            alt_psr = psr.altitude['data']+np.sqrt(
                r ** 2. + re ** 2. + 2. * r * re * np.sin(elrad)) - re
            alt_psr = alt_psr[0]
        else:
            alt_psr = alt

        r, az, el = pyart.core.cartesian_to_antenna(
            x, y, alt_psr-psr.altitude['data'])
        r = r[0]
        az = az[0]
        el = el[0]
    else:
        r = dscfg['rng']
        az = dscfg['azi']
        el = dscfg['ele']
        azi_tol = dscfg.get('AziTol', 0.5)
        ele_tol = dscfg.get('EleTol', 0.5)
        rng_tol = dscfg.get('RngTol', 50.)

        x, y, alt = pyart.core.antenna_to_cartesian(r/1000., az, el)
        lon, lat = pyart.core.cartesian_to_geographic(x, y, projparams)
        lon = lon[0]
        lat = lat[0]

    d_az = np.min(np.abs(psr.azimuth['data'] - az))
    if d_az > azi_tol:
        warn(' No psr bin found for point (az, el, r):(' +
             str(az)+', '+str(el)+', '+str(r) +
             '). Minimum distance to psr azimuth '+str(d_az) +
             ' larger than tolerance')
        return None, None

    d_el = np.min(np.abs(psr.elevation['data'] - el))
    if d_el > ele_tol:
        warn(' No psr bin found for point (az, el, r):(' +
             str(az)+', '+str(el)+', '+str(r) +
             '). Minimum distance to psr elevation '+str(d_el) +
             ' larger than tolerance')
        return None, None

    d_r = np.min(np.abs(psr.range['data'] - r))
    if d_r > rng_tol:
        warn(' No psr bin found for point (az, el, r):(' +
             str(az)+', '+str(el)+', '+str(r) +
             '). Minimum distance to psr range bin '+str(d_r) +
             ' larger than tolerance')
        return None, None

    ind_ray = np.argmin(np.abs(psr.azimuth['data'] - az) +
                        np.abs(psr.elevation['data'] - el))
    ind_rng = np.argmin(np.abs(psr.range['data'] - r))

    time_poi = num2date(psr.time['data'][ind_ray], psr.time['units'],
                        psr.time['calendar'])

    # initialize dataset
    if not dscfg['initialized']:
        psr_poi = deepcopy(psr)

        # prepare space for field
        psr_poi.fields = dict()
        for field_name in field_names:
            psr_poi.add_field(field_name, deepcopy(psr.fields[field_name]))
            psr_poi.fields[field_name]['data'] = np.array([])

        # fixed psr objects parameters
        psr_poi.range['data'] = np.array([r])
        psr_poi.ngates = 1

        psr_poi.time['units'] = pyart.io.make_time_unit_str(time_poi)
        psr_poi.time['data'] = np.array([])
        psr_poi.scan_type = 'poi_time_series'
        psr_poi.sweep_number['data'] = np.array([], dtype=np.int32)
        psr_poi.nsweeps = 1
        psr_poi.sweep_mode['data'] = np.array(['poi_time_series'])
        psr_poi.rays_are_indexed = None
        psr_poi.ray_angle_res = None
        psr_poi.fixed_angle['data'] = np.array([az])

        # ray dependent psr objects parameters
        psr_poi.sweep_end_ray_index['data'] = np.array([-1], dtype='int32')
        psr_poi.rays_per_sweep['data'] = np.array([0], dtype='int32')
        psr_poi.azimuth['data'] = np.array([], dtype='float64')
        psr_poi.elevation['data'] = np.array([], dtype='float64')
        psr_poi.nrays = 0

        if psr_poi.Doppler_velocity is not None:
            psr_poi.Doppler_velocity['data'] = np.array([])
        if psr_poi.Doppler_frequency is not None:
            psr_poi.Doppler_frequency['data'] = np.array([])

        dscfg['global_data'] = {
            'psr_poi': psr_poi,
            'point_coordinates_WGS84_lon_lat_alt': [lon, lat, alt],
            'antenna_coordinates_az_el_r': [az, el, r]}

        dscfg['initialized'] = 1

    psr_poi = dscfg['global_data']['psr_poi']
    start_time = num2date(
        0, psr_poi.time['units'], psr_poi.time['calendar'])
    psr_poi.time['data'] = np.append(
        psr_poi.time['data'], (time_poi - start_time).total_seconds())
    psr_poi.sweep_end_ray_index['data'][0] += 1
    psr_poi.rays_per_sweep['data'][0] += 1
    psr_poi.nrays += 1
    psr_poi.azimuth['data'] = np.append(psr_poi.azimuth['data'], az)
    psr_poi.elevation['data'] = np.append(psr_poi.elevation['data'], el)

    psr_poi.gate_longitude['data'] = (
        np.ones((psr_poi.nrays, psr_poi.ngates), dtype='float64')*lon)
    psr_poi.gate_latitude['data'] = (
        np.ones((psr_poi.nrays, psr_poi.ngates), dtype='float64')*lat)
    psr_poi.gate_altitude['data'] = np.broadcast_to(
        alt, (psr_poi.nrays, psr_poi.ngates))

    for field_name in field_names:
        if field_name not in psr.fields:
            warn('Field '+field_name+' not in psr object')
            poi_data = np.ma.masked_all((1, 1, psr.npulses_max))
        else:
            poi_data = psr.fields[field_name]['data'][ind_ray, ind_rng, :]
            poi_data = poi_data.reshape(1, 1, psr.npulses_max)

        # Put data in radar object
        if np.size(psr_poi.fields[field_name]['data']) == 0:
            psr_poi.fields[field_name]['data'] = poi_data.reshape(
                1, 1, psr_poi.npulses_max)
        else:
            if psr_poi.npulses_max == psr.npulses_max:
                psr_poi.fields[field_name]['data'] = np.ma.append(
                    psr_poi.fields[field_name]['data'], poi_data, axis=0)
            elif psr.npulses_max < psr_poi.npulses_max:
                poi_data_aux = np.ma.masked_all((1, 1, psr_poi.npulses_max))
                poi_data_aux[0, 0, 0:psr.npulses_max] = poi_data
                psr_poi.fields[field_name]['data'] = np.ma.append(
                    psr_poi.fields[field_name]['data'], poi_data_aux, axis=0)
            else:
                poi_data_aux = np.ma.masked_all(
                    (psr_poi.nrays, 1, psr.npulses_max))
                poi_data_aux[0:psr_poi.nrays-1, :, 0:psr_poi.npulses_max] = (
                    psr_poi.fields[field_name]['data'])
                poi_data_aux[psr_poi.nrays-1, :, :] = poi_data
                psr_poi.fields[field_name]['data'] = poi_data_aux

    if psr_poi.Doppler_velocity is not None:
        if np.size(psr_poi.Doppler_velocity['data']) == 0:
            psr_poi.Doppler_velocity['data'] = (
                psr.Doppler_velocity['data'][ind_ray, :].reshape(
                    1, psr_poi.npulses_max))
        else:
            Doppler_data = psr.Doppler_velocity['data'][ind_ray, :]
            Doppler_data = Doppler_data.reshape(1, psr.npulses_max)

            if psr_poi.npulses_max == psr.npulses_max:
                psr_poi.Doppler_velocity['data'] = np.ma.append(
                    psr_poi.Doppler_velocity['data'],
                    Doppler_data, axis=0)
            elif psr.npulses_max < psr_poi.npulses_max:
                Doppler_aux = np.ma.masked_all((1, psr_poi.npulses_max))
                Doppler_aux[0, 0:psr.npulses_max] = Doppler_data
                psr_poi.Doppler_velocity['data'] = np.ma.append(
                    psr_poi.Doppler_velocity['data'], Doppler_aux, axis=0)
            else:
                Doppler_aux = np.ma.masked_all(
                    (psr_poi.nrays, psr.npulses_max))
                Doppler_aux[0:psr_poi.nrays-1, 0:psr_poi.npulses_max] = (
                    psr_poi.Doppler_velocity['data'])
                Doppler_aux[psr_poi.nrays-1, :] = Doppler_data
                psr_poi.Doppler_velocity['data'] = Doppler_aux

    if psr_poi.Doppler_frequency is not None:
        if np.size(psr_poi.Doppler_frequency['data']) == 0:
            psr_poi.Doppler_frequency['data'] = (
                psr.Doppler_frequency['data'][ind_ray, :].reshape(
                    1, psr_poi.npulses_max))
        else:
            Doppler_data = psr.Doppler_frequency['data'][ind_ray, :]
            Doppler_data = Doppler_data.reshape(1, psr.npulses_max)

            if psr_poi.npulses_max == psr.npulses_max:
                psr_poi.Doppler_frequency['data'] = np.ma.append(
                    psr_poi.Doppler_frequency['data'],
                    Doppler_data, axis=0)
            elif psr.npulses_max < psr_poi.npulses_max:
                Doppler_aux = np.ma.masked_all((1, psr_poi.npulses_max))
                Doppler_aux[0, 0:psr.npulses_max] = Doppler_data
                psr_poi.Doppler_frequency['data'] = np.ma.append(
                    psr_poi.Doppler_frequency['data'], Doppler_aux, axis=0)
            else:
                Doppler_aux = np.ma.masked_all(
                    (psr_poi.nrays, psr.npulses_max))
                Doppler_aux[0:psr_poi.nrays-1, 0:psr_poi.npulses_max] = (
                    psr_poi.Doppler_frequency['data'])
                Doppler_aux[psr_poi.nrays-1, :] = Doppler_data
                psr_poi.Doppler_frequency['data'] = Doppler_aux

    psr_poi.npulses_max = max(psr_poi.npulses_max, psr.npulses_max)

    dscfg['global_data']['psr_poi'] = psr_poi

    # prepare for exit
    new_dataset = {
        'radar_out': psr_poi,
        'point_coordinates_WGS84_lon_lat_alt': (
            dscfg['global_data']['point_coordinates_WGS84_lon_lat_alt']),
        'antenna_coordinates_az_el_r': (
            dscfg['global_data']['antenna_coordinates_az_el_r']),
        'final': False}

    return new_dataset, ind_rad


def process_filter_0Doppler(procstatus, dscfg, radar_list=None):
    """
    Function to filter the 0-Doppler line bin and neighbours of the
    Doppler spectra

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        filter_width : float
            The Doppler filter width. Default 0.
        filter_units : str
            Can be 'm/s' or 'Hz'. Default 'm/s'
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    field_name_list = []
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        field_name_list.append(get_fieldname_pyart(datatype))

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    filter_width = dscfg.get('filter_width', 0.)
    filter_units = dscfg.get('filter_units', 'm/s')

    if filter_units == 'm/s':
        axis = psr.Doppler_velocity['data']
    else:
        axis = psr.Doppler_frequency['data']

    fields = dict()
    field_name_list_aux = []
    for field_name in field_name_list:
        if field_name not in psr.fields:
            warn('Unable to filter 0-Doppler. Missing field '+field_name)
            continue

        field = deepcopy(psr.fields[field_name])
        for ray in range(psr.nrays):
            ind = np.ma.where(np.logical_and(
                axis[ray, :] >= -filter_width/2.,
                axis[ray, :] <= filter_width/2.))
            field['data'][ray, :, ind] = np.ma.masked
        fields.update({field_name: field})
        field_name_list_aux.append(field_name)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    for field_name in field_name_list_aux:
        new_dataset['radar_out'].add_field(field_name, fields[field_name])

    return new_dataset, ind_rad


def process_filter_srhohv(procstatus, dscfg, radar_list=None):
    """
    Filter Doppler spectra as a function of spectral RhoHV

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        sRhoHV_threshold : float
            Data with sRhoHV module above this threshold will be filtered.
            Default 1.
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    field_name_list = []
    sRhoHV_found = False
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'sRhoHV' and not sRhoHV_found:
            sRhoHV_field = get_fieldname_pyart(datatype)
            sRhoHV_found = True
        else:
            field_name_list.append(get_fieldname_pyart(datatype))

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sRhoHV_field not in psr.fields:
        warn('Unable to obtain apply sRhoHV filter. Missing field ' +
             sRhoHV_field)
        return None, None

    sRhoHV_threshold = dscfg.get('sRhoHV_threshold', 1.)
    sRhoHV = psr.fields[sRhoHV_field]['data']

    fields = dict()
    field_name_list_aux = []
    for field_name in field_name_list:
        if field_name not in psr.fields:
            warn('Unable to filter 0-Doppler. Missing field '+field_name)
            continue

        field = deepcopy(psr.fields[field_name])
        field['data'][np.ma.abs(sRhoHV) >= sRhoHV_threshold] = np.ma.masked
        fields.update({field_name: field})
        field_name_list_aux.append(field_name)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    for field_name in field_name_list_aux:
        new_dataset['radar_out'].add_field(field_name, fields[field_name])

    return new_dataset, ind_rad


def process_filter_spectra_noise(procstatus, dscfg, radar_list=None):
    """
    Filter the noise of the Doppler spectra by clipping any data below
    the noise level plus a margin

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        clipping_level : float
            The clipping level [dB above noise level]. Default 10.
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('ShhADU', 'SvvADU'):
            signal_field = get_fieldname_pyart(datatype)
        elif datatype in ('NADUh', 'NADUv'):
            noise_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_field not in psr.fields or noise_field not in psr.fields:
        warn('Unable to obtain apply spectral noise filter. Missing fields')
        return None, None

    clipping_level = dscfg.get('clipping_level', 10.)

    clip_pwr = (
        psr.fields[noise_field]['data']*np.power(10., 0.1*clipping_level))

    s_pwr = pyart.retrieve.compute_spectral_power(
        psr, units='ADU', signal_field=signal_field,
        noise_field=noise_field)

    mask = np.ma.less_equal(s_pwr['data'], clip_pwr)

    field = deepcopy(psr.fields[signal_field])
    field['data'][mask] = np.ma.masked

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(signal_field, field)

    return new_dataset, ind_rad


def process_spectral_power(procstatus, dscfg, radar_list=None):
    """
    Computes the spectral power

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        units : str
            The units of the returned signal. Can be 'ADU', 'dBADU' or 'dBm'
        subtract_noise : Bool
            If True noise will be subtracted from the signal
        smooth_window : int or None
            Size of the moving Gaussian smoothing window. If none no smoothing
            will be applied
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    noise_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('ShhADU', 'SvvADU'):
            signal_field = get_fieldname_pyart(datatype)
        elif datatype in ('NADUh', 'NADUv'):
            noise_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_field not in psr.fields:
        warn('Unable to obtain spectral signal power. Missing field ' +
             signal_field)
        return None, None

    units = dscfg.get('units', 'dBADU')
    subtract_noise = dscfg.get('subtract_noise', False)
    smooth_window = dscfg.get('smooth_window', None)

    s_pwr = pyart.retrieve.compute_spectral_power(
        psr, units=units, subtract_noise=subtract_noise,
        smooth_window=smooth_window, signal_field=signal_field,
        noise_field=noise_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(s_pwr['standard_name'], s_pwr)

    return new_dataset, ind_rad


def process_spectral_phase(procstatus, dscfg, radar_list=None):
    """
    Computes the spectral phase

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('ShhADU', 'SvvADU'):
            signal_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_field not in psr.fields:
        warn('Unable to obtain spectral phase. Missing field ' +
             signal_field)
        return None, None

    s_phase = pyart.retrieve.compute_spectral_phase(
        psr, signal_field=signal_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(s_phase['standard_name'], s_phase)

    return new_dataset, ind_rad


def process_spectral_reflectivity(procstatus, dscfg, radar_list=None):
    """
    Computes spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        subtract_noise : Bool
            If True noise will be subtracted from the signal
        smooth_window : int or None
            Size of the moving Gaussian smoothing window. If none no smoothing
            will be applied
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    noise_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('ShhADU', 'SvvADU'):
            signal_field = get_fieldname_pyart(datatype)
        elif datatype in ('NADUh', 'NADUv'):
            noise_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_field not in psr.fields:
        warn('Unable to obtain spectral reflectivity. Missing field ' +
             signal_field)
        return None, None

    subtract_noise = dscfg.get('subtract_noise', False)
    smooth_window = dscfg.get('smooth_window', None)

    sdBZ = pyart.retrieve.compute_spectral_reflectivity(
        psr, subtract_noise=subtract_noise, smooth_window=smooth_window,
        signal_field=signal_field, noise_field=noise_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(sdBZ['standard_name'], sdBZ)

    return new_dataset, ind_rad


def process_spectral_differential_reflectivity(procstatus, dscfg, radar_list=None):
    """
    Computes spectral differential reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        subtract_noise : Bool
            If True noise will be subtracted from the signal
        smooth_window : int or None
            Size of the moving Gaussian smoothing window. If none no smoothing
            will be applied
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    noise_h_field = None
    noise_v_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'ShhADU':
            signal_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'SvvADU':
            signal_v_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUh':
            noise_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUv':
            noise_v_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_h_field not in psr.fields or signal_v_field not in psr.fields:
        warn('Unable to obtain spectral differential reflectivity. ' +
             'Missing fields')
        return None, None

    subtract_noise = dscfg.get('subtract_noise', False)
    smooth_window = dscfg.get('smooth_window', None)

    sZDR = pyart.retrieve.compute_spectral_differential_reflectivity(
        psr, subtract_noise=subtract_noise, smooth_window=smooth_window,
        signal_h_field=signal_h_field, signal_v_field=signal_v_field,
        noise_h_field=noise_h_field, noise_v_field=noise_v_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(sZDR['standard_name'], sZDR)

    return new_dataset, ind_rad


def process_spectral_differential_phase(procstatus, dscfg, radar_list=None):
    """
    Computes the spectral differential phase

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'ShhADU':
            signal_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'SvvADU':
            signal_v_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_h_field not in psr.fields or signal_v_field not in psr.fields:
        warn('Unable to obtain spectral signal differential phase. ' +
             'Missing fields')
        return None, None

    sPhiDP = pyart.retrieve.compute_spectral_differential_phase(
        psr, signal_h_field=signal_h_field, signal_v_field=signal_v_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(sPhiDP['standard_name'], sPhiDP)

    return new_dataset, ind_rad


def process_spectral_rhohv(procstatus, dscfg, radar_list=None):
    """
    Computes the spectral RhoHV

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        subtract_noise : Bool
            If True noise will be subtracted from the signal
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    noise_h_field = None
    noise_v_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'ShhADU':
            signal_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'SvvADU':
            signal_v_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUh':
            noise_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUv':
            noise_v_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_h_field not in psr.fields or signal_v_field not in psr.fields:
        warn('Unable to obtain spectral RhoHV. ' +
             'Missing fields')
        return None, None

    subtract_noise = dscfg.get('subtract_noise', False)

    sRhoHV = pyart.retrieve.compute_spectral_rhohv(
        psr, subtract_noise=subtract_noise, signal_h_field=signal_h_field,
        signal_v_field=signal_v_field, noise_h_field=noise_h_field,
        noise_v_field=noise_v_field)

    # prepare for exit
    new_dataset = {'radar_out': deepcopy(psr)}
    new_dataset['radar_out'].fields = dict()
    new_dataset['radar_out'].add_field(sRhoHV['standard_name'], sRhoHV)

    return new_dataset, ind_rad


def process_pol_variables(procstatus, dscfg, radar_list=None):
    """
    Computes the polarimetric variables from the complex spectra

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        subtract_noise : Bool
            If True noise will be subtracted from the signal
        smooth_window : int or None
            Size of the moving Gaussian smoothing window. If none no smoothing
            will be applied
        variables : list of str
            list of variables to compute. Default dBZ
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """
    if procstatus != 1:
        return None, None

    noise_h_field = None
    noise_v_field = None
    signal_h_field = None
    signal_v_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'ShhADU':
            signal_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'SvvADU':
            signal_v_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUh':
            noise_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUv':
            noise_v_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_h_field not in psr.fields and signal_v_field not in psr.fields:
        warn('Unable to obtain polarimetric variables. ' +
             'Missing fields')
        return None, None

    subtract_noise = dscfg.get('subtract_noise', False)
    smooth_window = dscfg.get('smooth_window', None)
    variables = dscfg.get('variables', ['dBZ'])

    fields_list = []
    for variable in variables:
        fields_list.append(get_fieldname_pyart(variable))

    radar = pyart.retrieve.compute_pol_variables(
        psr, fields_list, subtract_noise=subtract_noise,
        smooth_window=smooth_window, signal_h_field=signal_h_field,
        signal_v_field=signal_v_field, noise_h_field=noise_h_field,
        noise_v_field=noise_v_field)

    # prepare for exit
    new_dataset = {'radar_out': radar}

    return new_dataset, ind_rad


def process_reflectivity(procstatus, dscfg, radar_list=None):
    """
    Computes reflectivity from the spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('sdBZ', 'sdBZv'):
            sdBZ_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sdBZ_field not in psr.fields:
        warn('Unable to obtain reflectivity. ' +
             'Missing field '+sdBZ_field)
        return None, None

    dBZ = pyart.retrieve.compute_reflectivity(
        psr, sdBZ_field=sdBZ_field)

    reflectivity_field = 'reflectivity'
    if datatype == 'sdBZv':
        reflectivity_field += 'vv'

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field(reflectivity_field, dBZ)

    return new_dataset, ind_rad


def process_differential_reflectivity(procstatus, dscfg, radar_list=None):
    """
    Computes differential reflectivity from the horizontal and vertical
    spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'sdBZ':
            sdBZ_field = get_fieldname_pyart(datatype)
        elif datatype == 'sdBZv':
            sdBZv_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sdBZ_field not in psr.fields or sdBZv_field not in psr.fields:
        warn('Unable to obtain differential reflectivity. ' +
             'Missing fields.')
        return None, None

    ZDR = pyart.retrieve.compute_differential_reflectivity(
        psr, sdBZ_field=sdBZ_field, sdBZv_field=sdBZv_field)

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field('differential_reflectivity', ZDR)

    return new_dataset, ind_rad


def process_differential_phase(procstatus, dscfg, radar_list=None):
    """
    Computes the differential phase from the spectral differential phase and
    the spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('sdBZ', 'sdBZv'):
            sdBZ_field = get_fieldname_pyart(datatype)
        elif datatype == 'sPhiDP':
            sPhiDP_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sdBZ_field not in psr.fields or sPhiDP_field not in psr.fields:
        warn('Unable to obtain PhiDP. Missing fields')
        return None, None

    PhiDP = pyart.retrieve.compute_differential_phase(
        psr, sdBZ_field=sdBZ_field, sPhiDP_field=sPhiDP_field)

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field('differential_phase', PhiDP)

    return new_dataset, ind_rad


def process_rhohv(procstatus, dscfg, radar_list=None):
    """
    Computes RhoHV from the complex spectras

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
        subtract_noise : Bool
            If True noise will be subtracted from the signal
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """
    if procstatus != 1:
        return None, None

    noise_h_field = None
    noise_v_field = None
    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype == 'ShhADU':
            signal_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'SvvADU':
            signal_v_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUh':
            noise_h_field = get_fieldname_pyart(datatype)
        elif datatype == 'NADUv':
            noise_v_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if signal_h_field not in psr.fields or signal_v_field not in psr.fields:
        warn('Unable to obtain RhoHV. ' +
             'Missing fields')
        return None, None

    subtract_noise = dscfg.get('subtract_noise', False)

    RhoHV = pyart.retrieve.compute_rhohv(
        psr, subtract_noise=subtract_noise, signal_h_field=signal_h_field,
        signal_v_field=signal_v_field, noise_h_field=noise_h_field,
        noise_v_field=noise_v_field)

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field('cross_correlation_ratio', RhoHV)

    return new_dataset, ind_rad


def process_Doppler_velocity(procstatus, dscfg, radar_list=None):
    """
    Compute the Doppler velocity from the spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('sdBZ', 'sdBZv'):
            sdBZ_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sdBZ_field not in psr.fields:
        warn('Unable to obtain Doppler velocity. ' +
             'Missing field '+sdBZ_field)
        return None, None

    vel = pyart.retrieve.compute_Doppler_velocity(
        psr, sdBZ_field=sdBZ_field)

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field('velocity', vel)

    return new_dataset, ind_rad


def process_Doppler_width(procstatus, dscfg, radar_list=None):
    """
    Compute the Doppler spectrum width from the spectral reflectivity

    Parameters
    ----------
    procstatus : int
        Processing status: 0 initializing, 1 processing volume,
        2 post-processing
    dscfg : dictionary of dictionaries
        data set configuration. Accepted configuration keywords::

        datatype : list of string. Dataset keyword
            The input data types
    radar_list : list of spectra objects
        Optional. list of spectra objects

    Returns
    -------
    new_dataset : dict
        dictionary containing the output
    ind_rad : int
        radar index

    """

    if procstatus != 1:
        return None, None

    for datatypedescr in dscfg['datatype']:
        radarnr, _, datatype, _, _ = get_datatype_fields(datatypedescr)
        if datatype in ('sdBZ', 'sdBZv'):
            sdBZ_field = get_fieldname_pyart(datatype)

    ind_rad = int(radarnr[5:8])-1
    if (radar_list is None) or (radar_list[ind_rad] is None):
        warn('ERROR: No valid radar')
        return None, None
    psr = radar_list[ind_rad]

    if sdBZ_field not in psr.fields:
        warn('Unable to obtain Doppler spectrum width. ' +
             'Missing field '+sdBZ_field)
        return None, None

    width = pyart.retrieve.compute_Doppler_width(
        psr, sdBZ_field=sdBZ_field)

    # prepare for exit
    new_dataset = {'radar_out': pyart.util.radar_from_spectra(psr)}
    new_dataset['radar_out'].add_field('spectrum_width', width)

    return new_dataset, ind_rad
