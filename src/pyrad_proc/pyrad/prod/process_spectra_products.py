"""
pyrad.prod.process_grid_products
================================

Functions for obtaining Pyrad products from spectra datasets

.. autosummary::
    :toctree: generated/

    generate_spectra_products

"""

from warnings import warn

from ..io.io_aux import get_fieldname_pyart
from ..io.io_aux import get_save_dir, make_filename

from ..graph.plots_spectra import plot_range_Doppler, plot_Doppler
from ..graph.plots_spectra import plot_complex_range_Doppler
from ..graph.plots_spectra import plot_amp_phase_range_Doppler
from ..graph.plots_spectra import plot_complex_Doppler, plot_amp_phase_Doppler
from ..graph.plots_spectra import plot_time_Doppler, plot_complex_time_Doppler
from ..graph.plots_spectra import plot_amp_phase_time_Doppler

from ..util.radar_utils import find_ray_index, find_rng_index

from pyart.util import datetime_from_radar


def generate_spectra_products(dataset, prdcfg):
    """
    generates spectra products. Accepted product types:
        'AMPLITUDE_PHASE_DOPPLER': Plots a complex Doppler spectrum
            making two separate plots for the module and phase of the signal
            User defined parameters:
                azi, ele, rng : float
                    azimuth and elevation (deg) and range (m) of the ray to
                    plot
                azi_to, ele_tol, rng_tol : float
                    azimuth and elevation (deg) and range (m) tolerance
                    respect to nominal position to plot. Default 1, 1, 50.
                ind_ray, ind_rng : int
                    index of the ray and range to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                ampli_vmin, ampli_vmax, phase_vmin, phase_vmax : float or None
                    Minimum and maximum of the color scale for the module and
                    phase
        'AMPLITUDE_PHASE_RANGE_DOPPLER': Plots a complex spectra range-Doppler
            making two separate plots for the module and phase of the signal
            User defined parameters:
                azi, ele : float
                    azimuth and elevation (deg) of the ray to plot
                azi_to, ele_tol : float
                    azimuth and elevation (deg) tolerance respect to nominal
                    position to plot. Default 1, 1.
                ind_ray : int
                    index of the ray to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                ampli_vmin, ampli_vmax, phase_vmin, phase_vmax : float or None
                    Minimum and maximum of the color scale for the module and
                    phase
        'AMPLITUDE_PHASE_TIME_DOPPLER': Plots a complex spectra time-Doppler
            making two separate plots for the module and phase of the signal
            User defined parameters:
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                ampli_vmin, ampli_vmax, phase_vmin, phase_vmax : float or None
                    Minimum and maximum of the color scale for the module and
                    phase
                plot_type : str
                    Can be 'final' or 'temporal'. If final the data is only
                    plotted at the end of the processing
        'COMPLEX_DOPPLER': Plots a complex Doppler spectrum making two
            separate plots for the real and imaginary parts
            User defined parameters:
                azi, ele, rng : float
                    azimuth and elevation (deg) and range (m) of the ray to
                    plot
                azi_to, ele_tol, rng_tol : float
                    azimuth and elevation (deg) and range (m) tolerance
                    respect to nominal position to plot. Default 1, 1, 50.
                ind_ray, ind_rng : int
                    index of the ray and range to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
        'COMPLEX_RANGE_DOPPLER': Plots the complex spectra range-Doppler
            making two separate plots for the real and imaginary parts
            User defined parameters:
                azi, ele : float
                    azimuth and elevation (deg) of the ray to plot
                azi_to, ele_tol : float
                    azimuth and elevation (deg) tolerance respect to nominal
                    position to plot. Default 1, 1.
                ind_ray : int
                    index of the ray to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
        'COMPLEX_TIME_DOPPLER': Plots the complex spectra time-Doppler
            making two separate plots for the real and imaginary parts
            User defined parameters:
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
                plot_type : str
                    Can be 'final' or 'temporal'. If final the data is only
                    plotted at the end of the processing
        'DOPPLER': Plots a Doppler spectrum variable
            User defined parameters:
                azi, ele, rng : float
                    azimuth and elevation (deg) and range (m) of the ray to
                    plot
                azi_to, ele_tol, rng_tol : float
                    azimuth and elevation (deg) and range (m) tolerance
                    respect to nominal position to plot. Default 1, 1, 50.
                ind_ray, ind_rng : int
                    index of the ray and range to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
        'RANGE_DOPPLER': Makes a range-Doppler plot of spectral data
            User defined parameters:
                azi, ele : float
                    azimuth and elevation (deg) of the ray to plot
                azi_to, ele_tol : float
                    azimuth and elevation (deg) tolerance respect to nominal
                    position to plot. Default 1, 1.
                ind_ray : int
                    index of the ray to plot. Alternative to
                    defining its antenna coordinates
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
        'TIME_DOPPLER': Makes a time-Doppler plot of spectral data at a point
            of interest.
            User defined parameters:
                xaxis_info : str
                    The xaxis type. Can be 'Doppler_velocity' or
                    'Doppler frequency'
                vmin, vmax : float or None
                    Minimum and maximum of the color scale
                plot_type : str
                    Can be 'final' or 'temporal'. If final the data is only
                    plotted at the end of the processing

    Parameters
    ----------
    dataset : spectra
        spectra object

    prdcfg : dictionary of dictionaries
        product configuration dictionary of dictionaries

    Returns
    -------
    None or name of generated files

    """
    dssavedir = prdcfg['dsname']
    if 'dssavename' in prdcfg:
        dssavedir = prdcfg['dssavename']

    if prdcfg['type'] == 'RANGE_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)

        if azi is None or ele is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)

        if ind_ray is None:
            warn('Ray azi='+str(azi)+', ele='+str(ele) +
                 ' out of radar coverage')
            return None

        gateinfo = 'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele)

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'range_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].ngates == 1:
            plot_Doppler(
                dataset['radar_out'], field_name, ind_ray, 0, prdcfg,
                fname_list, xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)
        else:
            plot_range_Doppler(
                dataset['radar_out'], field_name, ind_ray, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'TIME_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)
        plot_type = prdcfg.get('plot_type', 'final')

        if plot_type == 'final' and not dataset['final']:
            return None

        if 'antenna_coordinates_az_el_r' in dataset:
            az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
            el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
            r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
            gateinfo = ('az'+az+'r'+r+'el'+el)
        else:
            lon = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][0])
            lat = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][1])
            alt = '{:.1f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][2])
            gateinfo = ('lon'+lon+'lat'+lat+'alt'+alt)

        time_info = datetime_from_radar(dataset['radar_out'])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=time_info)

        fname_list = make_filename(
            'time_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=time_info, runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].nrays == 1:
            plot_Doppler(
                dataset['radar_out'], field_name, 0, 0, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)
        else:
            plot_time_Doppler(
                dataset['radar_out'], field_name, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        rng = prdcfg.get('rng', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)
        rng_tol = prdcfg.get('rng_tol', 50.)

        if azi is None or ele is None or rng is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            ind_rng = prdcfg.get('ind_rng', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
            rng = dataset['radar_out'].range['data'][ind_rng]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)
            ind_rng = find_rng_index(
                dataset['radar_out'].range['data'], rng, rng_tol=rng_tol)

        if ind_rng is None or ind_ray is None:
            warn('Point azi='+str(azi)+', ele='+str(ele)+', rng='+str(rng) +
                 ' out of radar coverage')
            return None

        gateinfo = (
            'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele) +
            'r'+'{:.1f}'.format(rng))

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        plot_Doppler(
            dataset['radar_out'], field_name, ind_ray, ind_rng, prdcfg,
            fname_list, xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'COMPLEX_RANGE_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)

        if azi is None or ele is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)

        if ind_ray is None:
            warn('Ray azi='+str(azi)+', ele='+str(ele) +
                 ' out of radar coverage')
            return None

        gateinfo = 'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele)

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'c_range_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].ngates == 1:
            plot_complex_Doppler(
                dataset['radar_out'], field_name, ind_ray, 0, prdcfg,
                fname_list, xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)
        else:
            plot_complex_range_Doppler(
                dataset['radar_out'], field_name, ind_ray, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'COMPLEX_TIME_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)
        plot_type = prdcfg.get('plot_type', 'final')

        if plot_type == 'final' and not dataset['final']:
            return None

        if 'antenna_coordinates_az_el_r' in dataset:
            az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
            el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
            r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
            gateinfo = ('az'+az+'r'+r+'el'+el)
        else:
            lon = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][0])
            lat = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][1])
            alt = '{:.1f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][2])
            gateinfo = ('lon'+lon+'lat'+lat+'alt'+alt)

        time_info = datetime_from_radar(dataset['radar_out'])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=time_info)

        fname_list = make_filename(
            'c_time_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=time_info, runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].nrays == 1:
            plot_complex_Doppler(
                dataset['radar_out'], field_name, 0, 0, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)
        else:
            plot_complex_time_Doppler(
                dataset['radar_out'], field_name, prdcfg, fname_list,
                xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'COMPLEX_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        rng = prdcfg.get('rng', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)
        rng_tol = prdcfg.get('rng_tol', 50.)

        if azi is None or ele is None or rng is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            ind_rng = prdcfg.get('ind_rng', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
            rng = dataset['radar_out'].range['data'][ind_rng]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)
            ind_rng = find_rng_index(
                dataset['radar_out'].range['data'], rng, rng_tol=rng_tol)

        if ind_rng is None or ind_ray is None:
            warn('Point azi='+str(azi)+', ele='+str(ele)+', rng='+str(rng) +
                 ' out of radar coverage')
            return None

        gateinfo = (
            'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele) +
            'r'+'{:.1f}'.format(rng))

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        vmin = prdcfg.get('vmin', None)
        vmax = prdcfg.get('vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'c_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        plot_complex_Doppler(
            dataset['radar_out'], field_name, ind_ray, ind_rng, prdcfg,
            fname_list, xaxis_info=xaxis_info, vmin=vmin, vmax=vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'AMPLITUDE_PHASE_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        rng = prdcfg.get('rng', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)
        rng_tol = prdcfg.get('rng_tol', 50.)

        if azi is None or ele is None or rng is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            ind_rng = prdcfg.get('ind_rng', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
            rng = dataset['radar_out'].range['data'][ind_rng]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)
            ind_rng = find_rng_index(
                dataset['radar_out'].range['data'], rng, rng_tol=rng_tol)

        if ind_rng is None or ind_ray is None:
            warn('Point azi='+str(azi)+', ele='+str(ele)+', rng='+str(rng) +
                 ' out of radar coverage')
            return None

        gateinfo = (
            'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele) +
            'r'+'{:.1f}'.format(rng))

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        ampli_vmin = prdcfg.get('ampli_vmin', None)
        ampli_vmax = prdcfg.get('ampli_vmax', None)
        phase_vmin = prdcfg.get('phase_vmin', None)
        phase_vmax = prdcfg.get('phase_vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'ap_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        plot_amp_phase_Doppler(
            dataset['radar_out'], field_name, ind_ray, ind_rng, prdcfg,
            fname_list, xaxis_info=xaxis_info, ampli_vmin=ampli_vmin,
            ampli_vmax=ampli_vmax, phase_vmin=phase_vmin,
            phase_vmax=phase_vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'AMPLITUDE_PHASE_RANGE_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        azi = prdcfg.get('azi', None)
        ele = prdcfg.get('ele', None)
        azi_tol = prdcfg.get('azi_tol', 1.)
        ele_tol = prdcfg.get('ele_tol', 1.)

        if azi is None or ele is None:
            ind_ray = prdcfg.get('ind_ray', 0)
            azi = dataset['radar_out'].azimuth['data'][ind_ray]
            ele = dataset['radar_out'].elevation['data'][ind_ray]
        else:
            ind_ray = find_ray_index(
                dataset['radar_out'].elevation['data'],
                dataset['radar_out'].azimuth['data'], ele, azi,
                ele_tol=ele_tol, azi_tol=azi_tol)

        if ind_ray is None:
            warn('Ray azi='+str(azi)+', ele='+str(ele) +
                 ' out of radar coverage')
            return None

        gateinfo = 'az'+'{:.1f}'.format(azi)+'el'+'{:.1f}'.format(ele)

        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        ampli_vmin = prdcfg.get('ampli_vmin', None)
        ampli_vmax = prdcfg.get('ampli_vmax', None)
        phase_vmin = prdcfg.get('phase_vmin', None)
        phase_vmax = prdcfg.get('phase_vmax', None)

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=prdcfg['timeinfo'])

        fname_list = make_filename(
            'ap_range_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=prdcfg['timeinfo'], runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].ngates == 1:
            plot_amp_phase_Doppler(
                dataset['radar_out'], field_name, ind_ray, 0, prdcfg,
                fname_list, xaxis_info=xaxis_info, ampli_vmin=ampli_vmin,
                ampli_vmax=ampli_vmax, phase_vmin=phase_vmin,
                phase_vmax=phase_vmax)
        else:
            plot_amp_phase_range_Doppler(
                dataset['radar_out'], field_name, ind_ray, prdcfg, fname_list,
                xaxis_info=xaxis_info, ampli_vmin=ampli_vmin,
                ampli_vmax=ampli_vmax, phase_vmin=phase_vmin,
                phase_vmax=phase_vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    if prdcfg['type'] == 'AMPLITUDE_PHASE_TIME_DOPPLER':
        field_name = get_fieldname_pyart(prdcfg['voltype'])
        if field_name not in dataset['radar_out'].fields:
            warn(
                ' Field type ' + field_name +
                ' not available in data set. Skipping product ' +
                prdcfg['type'])
            return None

        # user defined values
        xaxis_info = prdcfg.get('xaxis_info', 'Doppler_velocity')
        ampli_vmin = prdcfg.get('ampli_vmin', None)
        ampli_vmax = prdcfg.get('ampli_vmax', None)
        phase_vmin = prdcfg.get('phase_vmin', None)
        phase_vmax = prdcfg.get('phase_vmax', None)
        plot_type = prdcfg.get('plot_type', 'final')

        if plot_type == 'final' and not dataset['final']:
            return None

        if 'antenna_coordinates_az_el_r' in dataset:
            az = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][0])
            el = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][1])
            r = '{:.1f}'.format(dataset['antenna_coordinates_az_el_r'][2])
            gateinfo = ('az'+az+'r'+r+'el'+el)
        else:
            lon = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][0])
            lat = '{:.3f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][1])
            alt = '{:.1f}'.format(
                dataset['point_coordinates_WGS84_lon_lat_alt'][2])
            gateinfo = ('lon'+lon+'lat'+lat+'alt'+alt)

        time_info = datetime_from_radar(dataset['radar_out'])

        savedir = get_save_dir(
            prdcfg['basepath'], prdcfg['procname'], dssavedir,
            prdcfg['prdname'], timeinfo=time_info)

        fname_list = make_filename(
            'ap_time_Doppler', prdcfg['dstype'], prdcfg['voltype'],
            prdcfg['imgformat'], prdcfginfo=gateinfo,
            timeinfo=time_info, runinfo=prdcfg['runinfo'])

        for i, fname in enumerate(fname_list):
            fname_list[i] = savedir+fname

        if dataset['radar_out'].nrays == 1:
            plot_amp_phase_Doppler(
                dataset['radar_out'], field_name, 0, 0, prdcfg, fname_list,
                xaxis_info=xaxis_info, ampli_vmin=ampli_vmin,
                ampli_vmax=ampli_vmax, phase_vmin=phase_vmin,
                phase_vmax=phase_vmax)
        else:
            plot_amp_phase_time_Doppler(
                dataset['radar_out'], field_name, prdcfg, fname_list,
                xaxis_info=xaxis_info, ampli_vmin=ampli_vmin,
                ampli_vmax=ampli_vmax, phase_vmin=phase_vmin,
                phase_vmax=phase_vmax)

        print('----- save to '+' '.join(fname_list))

        return fname_list

    warn(' Unsupported product type: ' + prdcfg['type'])
    return None
