"""This module defines methods calculating beam properties"""

import scipy.constants as ct
import numpy as np
import matplotlib.pyplot as plt

from aptools.helper_functions import (weighted_std, create_beam_slices,
                                      slope_of_correlation)

def twiss_parameters(x, px, pz, py=None, w=1, emitt='tr',
                     disp_corrected=False):
    """Calculate the alpha and beta functions of the beam in a certain
    transverse plane

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma). Necessary if 
        disp_corrected=True or emitt='ph'.
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma).
    w : array or single value
        Statistical weight of the particles.
    emitt : str
        Determined which emittance to use to calculate the Twiss parameters.
        Possible values are 'tr' for trace-space emittance and 'ph' for
        phase-space emittance 
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.

    Returns:
    --------
    A tuple with the value of the alpha, beta [m] and gamma [m^-1] functions
    """
    if emitt == 'ph':
        em_x = normalized_transverse_rms_emittance(x, px, py, pz, w,
                                                   disp_corrected)
        gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
        gamma_avg = np.average(gamma, weights=w)
        x_avg = np.average(x, weights=w)
        px_avg = np.average(px, weights=w)
        # center x and x
        x -= x_avg
        px -= px_avg
        if disp_corrected:
            # remove x-gamma correlation
            dgamma = (gamma - gamma_avg)/gamma_avg
            slope = slope_of_correlation(x, dgamma, w)
            x -= slope*dgamma
        b_x = np.average(x**2, weights=w)*gamma_avg/em_x
        a_x = -np.average(x*px, weights=w)/em_x
    elif emitt == 'tr':
        em_x = transverse_trace_space_rms_emittance(x, px, py, pz, w,
                                                    disp_corrected)
        xp = px/pz
        # center x and xp
        x_avg = np.average(x, weights=w)
        xp_avg = np.average(xp, weights=w)
        x -= x_avg
        xp -= xp_avg
        if disp_corrected:
            # remove x-gamma correlation
            gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
            gamma_avg = np.average(gamma, weights=w)
            dgamma = (gamma - gamma_avg)/gamma_avg
            slope = slope_of_correlation(x, dgamma, w)
            x -= slope*dgamma
            # remove xp-gamma correlation
            slope = slope_of_correlation(xp, dgamma, w)
            xp -= slope*dgamma
        b_x = np.average(x**2, weights=w)/em_x
        a_x = -np.average(x*xp, weights=w)/em_x
    g_x = (1 + a_x**2)/b_x
    return (a_x, b_x, g_x)

def twiss_parameters_corrected(x, px, py, pz, w=1):
    """Calculate the alpha and beta functions of the beam in a certain
    transverse plane removing contributions from dispersion.

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A tuple with the value of the alpha, beta [m] and gamma [m^-1] functions
    """
    # remove x-gamma correlation
    gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
    gamma_avg = np.average(gamma, weights=w)
    x_avg = np.average(x, weights=w)
    dgamma = (gamma - gamma_avg)/gamma_avg
    p = np.polyfit(dgamma, x, 1, w=w)
    slope = p[0]
    x = x - slope*dgamma
    # remove xp-gamma correlation
    xp = px/pz
    p = np.polyfit(dgamma, xp, 1, w=w)
    slope = p[0]
    xp = xp - slope*dgamma
    px = xp*pz
    # calculate Twiss
    a_x, b_x, g_x = twiss_parameters(x, px, pz, w)
    return (a_x, b_x, g_x)

def rms_length(z, w=1):
    """Calculate the RMS bunch length of the provided particle
    distribution

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the RMS length value in meters.
    """
    s_z = weighted_std(z, weights=w)
    return s_z

def rms_size(x, w=1):
    """Calculate the RMS bunch size of the provided particle
    distribution

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in units of meters
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the RMS length value in meters.
    """
    s_x = weighted_std(x, weights=w)
    return s_x

def mean_kinetic_energy(px, py, pz, w=1):
    """Calculate the mean kinetic energy of the provided particle distribution

    Parameters:
    -----------
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the mean kinetic energy in non-dimmensional
    units, i.e. [1/(m_e c**2)]
    """
    return np.average(np.sqrt(np.square(px) + np.square(py) + np.square(pz)),
                      weights=np.abs(w))

def mean_energy(px, py, pz, w=1):
    """Calculate the mean energy of the provided particle distribution

    Parameters:
    -----------
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the mean energy in non-dimmensional units, i.e. [1/(m_e c**2)]
    """
    kin_ene = mean_kinetic_energy(px, py, pz, w)
    return np.average(1 + np.sqrt(np.square(kin_ene)))

def rms_energy_spread(px, py, pz, w=1):
    """Calculate the absotule RMS energy spread of the provided particle
    distribution

    Parameters:
    -----------
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the energy spread value in non-dimmensional units,
    i.e. [1/(m_e c**2)]
    """
    part_ene = np.sqrt(1 + np.square(px) + np.square(py) + np.square(pz))
    ene_std = weighted_std(part_ene, weights=w)
    return ene_std

def relative_rms_energy_spread(px, py, pz, w=1):
    """Calculate the relative RMS energy spread of the provided particle
    distribution

    Parameters:
    -----------
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the energy spread value in non-dimmensional units,
    i.e. [1/(m_e c**2)]
    """
    abs_spread = rms_energy_spread(px, py, pz, w)
    mean_ene = mean_energy(px, py, pz, w)
    rel_spread = abs_spread/mean_ene
    return rel_spread

def longitudinal_energy_chirp(z, px, py, pz, w=1):
    """Calculate the longitudinal energy chirp, K, of the provided particle
    distribution in units of m**(-1). It is defined as dE/<E> = K*dz.

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the chirp value in units of m^(-1)
    """
    ene = np.sqrt(1 + np.square(px) + np.square(py) + np.square(pz))
    mean_ene = np.average(ene, weights=w)
    mean_z = np.average(z, weights=w)
    dE_rel = (ene-mean_ene) / mean_ene
    dz = z - mean_z
    p = np.polyfit(dz, dE_rel, 1)
    K = p[0]
    return K

def rms_correlated_energy_spread(z, px, py, pz, w=1):
    """Calculate the correlated energy spread of the provided particle
    distribution

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the energy spread value in non-dimmensional units,
    i.e. [1/(m_e c**2)]
    """
    K = longitudinal_energy_chirp(z, px, py, pz, w)
    mean_z = np.average(z, weights=w)
    dz = z - mean_z
    corr_ene = K*dz
    corr_ene_sp = weighted_std(corr_ene, w)
    return corr_ene_sp

def normalized_transverse_rms_emittance(x, px, py=None, pz=None, w=1,
                                                  disp_corrected=False):
    """Calculate the normalized transverse RMS emittance without dispersion
    contributions of the particle distribution in a given plane.

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma). Necessary if 
        disp_corrected=True.
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma). Necessary if disp_corrected=True.
    w : array or single value
        Statistical weight of the particles.
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.

    Returns:
    --------
    A float with the emmitance value in units of m * rad
    """
    if len(x) > 1:
        if disp_corrected:
            # remove x-gamma correlation
            gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
            gamma_avg = np.average(gamma, weights=w)
            x_avg = np.average(x, weights=w)
            dgamma = (gamma - gamma_avg)/gamma_avg
            p = np.polyfit(dgamma, x, 2, w=w)
            s1 = p[1]
            s2 = p[0]
            slope = slope_of_correlation(x, dgamma)
            x = x - s1*dgamma - s2*dgamma**2
            #plt.hist2d(x, px, bins=1000)
            #plt.show()
        cov_x = np.cov(x, px, aweights=np.abs(w))
        em_x = np.sqrt(np.linalg.det(cov_x))
    else:
        em_x = 0
    return em_x

def geometric_transverse_rms_emittance(x, px, py, pz, w=1,
                                       disp_corrected=False):
    """Calculate the geometric transverse RMS emittance without dispersion
    contributions of the particle distribution in a given plane.

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma).
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma).
    w : array or single value
        Statistical weight of the particles.
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.

    Returns:
    --------
    A float with the emmitance value in units of m * rad
    """
    gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
    gamma_avg = np.average(gamma, weights=w)
    em_x = normalized_transverse_rms_emittance(x, px, py, pz, w,
                                                disp_corrected)
    return em_x / gamma_avg

def normalized_transverse_trace_space_rms_emittance(x, px, py, pz, w=1,
                                                    disp_corrected=False):
    """Calculate the normalized trasnverse trace-space RMS emittance of the
    particle distribution in a given plane. 

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma).
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma).
    w : array or single value
        Statistical weight of the particles.
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.

    Returns:
    --------
    A float with the emmitance value in units of m * rad
    """
    gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
    gamma_avg = np.average(gamma, weights=w)
    em_x = transverse_trace_space_rms_emittance(x, px, py, pz, w,
                                                disp_corrected)
    return em_x * gamma_avg

def transverse_trace_space_rms_emittance(x, px, py=None, pz=None, w=1,
                                         disp_corrected=False):
    """Calculate the trasnverse trace-space RMS emittance of the
    particle distribution in a given plane. 

    Parameters:
    -----------
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma). Necessary if 
        disp_corrected=True.
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma). Necessary if disp_corrected=True.
    w : array or single value
        Statistical weight of the particles.
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.

    Returns:
    --------
    A float with the emmitance value in units of m * rad
    """
    if len(x) > 1:
        xp = px/pz
        if disp_corrected:
            # remove x-gamma correlation
            gamma = np.sqrt(np.square(px) + np.square(py) + np.square(pz))
            gamma_avg = np.average(gamma, weights=w)
            dgamma = (gamma - gamma_avg)/gamma_avg
            sl = slope_of_correlation(x, dgamma, w)
            x = x - sl*dgamma
            # remove xp-gamma correlation
            sl = slope_of_correlation(xp, dgamma, w)
            xp = xp - sl*dgamma
        cov_x = np.cov(x, xp, aweights=np.abs(w))
        em_x = np.sqrt(np.linalg.det(cov_x))
    else:
        em_x = 0
    return em_x

def longitudinal_rms_emittance(z, px, py, pz, w=1):
    """Calculate the longitudinal RMS emittance of the particle
    distribution in a given plane.

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.

    Returns:
    --------
    A float with the emmitance value in units of m
    """
    g = np.sqrt(1 + np.square(px) + np.square(py) + np.square(pz))
    cov_l = np.cov(z, g, aweights=np.abs(w))
    em_l = np.sqrt(np.linalg.det(cov_l))
    return em_l

def relative_rms_slice_energy_spread(z, px, py, pz, w=1, n_slices=10,
                                     len_slice=None):
    """Calculate the relative RMS slice energy spread of the provided particle
    distribution

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    px : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum in the x direction of the
        beam particles in non-dimmensional units (beta*gamma)
    pz : array
        Contains the longitudonal momentum of the beam particles in
        non-dimmensional units (beta*gamma)
    w : array or single value
        Statistical weight of the particles.
    n_slices : array
        Number of longitudinal slices in which to divite the particle
        distribution. Not used if len_slice is specified.
    len_slice : array
        Length of the longitudinal slices. If not None, replaces n_slices.

    Returns:
    --------
    A tuple containing:
    - An array with the energy spread value in each slice. Values are in
    non-dimmensional units, i.e. [1/(m_e c**2)]
    - An array with the statistical weight of each slice.
    - An array with the slice edges.
    """
    slice_lims, n_slices = create_beam_slices(z, n_slices, len_slice)
    slice_ene_sp = np.zeros(n_slices)
    slice_weight = np.zeros(n_slices)
    for i in np.arange(0, n_slices):
        a = slice_lims[i]
        b = slice_lims[i+1]
        slice_particle_filter = (z > a) & (z <= b)
        if slice_particle_filter.any():
            z_slice = z[slice_particle_filter]
            px_slice = px[slice_particle_filter]
            py_slice = py[slice_particle_filter]
            pz_slice = pz[slice_particle_filter]
            if hasattr(w, '__iter__'):
                w_slice = w[slice_particle_filter]
            else:
                w_slice = w
            slice_ene_sp[i] = relative_rms_energy_spread(px_slice, py_slice,
                                                         pz_slice, w_slice)
            slice_weight[i] = np.sum(w_slice)
    return slice_ene_sp, slice_weight, slice_lims

def normalized_transverse_rms_slice_emittance(z, x, px, py=None, pz=None, w=1,
                                              disp_corrected=False,
                                              n_slices=10, len_slice=None):
    """Calculate the normalized transverse RMS slice emittance of the particle
    distribution in a given plane.

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    x : array
        Contains the transverse position of the particles in one of the
        transverse planes in units of meters
    px : array
        Contains the transverse momentum of the beam particles in the same
        plane as x in non-dimmensional units (beta*gamma)
    py : array
        Contains the transverse momentum of the beam particles in the opposite
        plane as as x in non-dimmensional units (beta*gamma). Necessary if 
        disp_corrected=True.
    pz : array
        Contains the longitudinal momentum of the beam particles in
        non-dimmensional units (beta*gamma). Necessary if disp_corrected=True.
    w : array or single value
        Statistical weight of the particles.
    disp_corrected : bool
        Whether ot not to correct for dispersion contributions.
    n_slices : array
        Number of longitudinal slices in which to divite the particle
        distribution. Not used if len_slice is specified.
    len_slice : array
        Length of the longitudinal slices. If not None, replaces n_slices.

    Returns:
    --------
    A tuple containing:
    - An array with the emmitance value in each slice in units of m * rad.
    - An array with the statistical weight of each slice.
    - An array with the slice edges.
    """
    slice_lims, n_slices = create_beam_slices(z, n_slices, len_slice)
    slice_em = np.zeros(n_slices)
    slice_weight = np.zeros(n_slices)
    for i in np.arange(0, n_slices):
        a = slice_lims[i]
        b = slice_lims[i+1]
        slice_particle_filter = (z > a) & (z <= b)
        if slice_particle_filter.any():
            x_slice = x[slice_particle_filter]
            px_slice = px[slice_particle_filter]
            if py is not None:
                py_slice = py[slice_particle_filter]
            else:
                py_slice=None
            if pz is not None:
                pz_slice = pz[slice_particle_filter]
            else:
                pz_slice=None
            if hasattr(w, '__iter__'):
                w_slice = w[slice_particle_filter]
            else:
                w_slice = w
            slice_em[i] = normalized_transverse_rms_emittance(
                x_slice, px_slice, py_slice, pz_slice, w_slice, disp_corrected)
            slice_weight[i] = np.sum(w_slice)
    return slice_em, slice_weight, slice_lims

def current_profile(z, q, n_slices=10, len_slice=None):
    """Calculate the current profile of the given particle distribution.

    Parameters:
    -----------
    z : array
        Contains the longitudinal position of the particles in units of meters
    q : array
        Contains the charge of the particles in C
    n_slices : array
        Number of longitudinal slices in which to divite the particle
        distribution. Not used if len_slice is specified.
    len_slice : array
        Length of the longitudinal slices. If not None, replaces n_slices.

    Returns:
    --------
    A tuple containing:
    - An array with the current of each slice in units of A.
    - An array with the slice edges along z.
    """
    max_z = np.max(z)
    min_z = np.min(z)
    if len_slice is not None:
        n_slices = int((max_z-min_z)/len_slice)
    adj_slice_len = (max_z-min_z)/n_slices
    print('Slice length = {} m'.format(adj_slice_len))
    charge_hist, z_edges = np.histogram(z, bins=n_slices, weights=q)
    sl_dur = adj_slice_len/ct.c
    current_prof = charge_hist/sl_dur
    return current_prof, z_edges
