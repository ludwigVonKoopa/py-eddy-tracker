# -*- coding: utf-8 -*-
"""
===========================================================================
This file is part of py-eddy-tracker.

    py-eddy-tracker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    py-eddy-tracker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with py-eddy-tracker.  If not, see <http://www.gnu.org/licenses/>.

Copyright (c) 2014-2015 by Evan Mason
Email: emason@imedea.uib-csic.es
===========================================================================

roms_grid.py

Version 2.0.3

===========================================================================

Class to access ROMS gridfile information
Useful when the output files don't contain the grid
information

"""

import netCDF4 as netcdf
import numpy as np
import matplotlib.path as Path
from . import PyEddyTracker


def root():  # Define just one root path here
    # root_dir = '/acacia/emason/runs/'
    # root_dir = '/media/hd/roms/'
    root_dir = '/home/emason/runs/'
    # root_dir = '/Users/evan/runs/'
    return root_dir


def getcoast(coastfile):
    if coastfile is None:
        # coastfile = '/msasa/emason/data/bathymetry/ne_atlantic_coast.dat'
        # coastfile = '/baobab/data/coastline/ne_atlantic_coast.dat'
        coastfile = '/hun/emason/data/coastline/ne_atlantic_coast.dat'
    data = np.load(coastfile)
    data = np.ma.masked_where(np.isnan(data), data)
    return data[:, 0], data[:, 1]


def read_nc(GRDFILE, var):
    h_nc = netcdf.Dataset(GRDFILE, 'r')
    var = h_nc.variables[var][:]
    h_nc.close()
    return var


class RomsGrid (PyEddyTracker):
    '''
    The 'RomsGrid' class

    Initialises with:
      obcs : [0,0,0,1] where 1 is open [S,E,N,W]
    '''
    def __init__(self, GRDFILE, the_domain, PRODUCT,
                 LONMIN, LONMAX, LATMIN, LATMAX, FILLVAL,
                 with_pad=True):
        """
        # Initialise the grid object
        """
        super(RomsGrid, self).__init__()
        print '\nInitialising the *RomsGrid*'
        self.the_domain = the_domain
        self.product = PRODUCT
        self.lonmin = LONMIN
        self.lonmax = LONMAX
        self.latmin = LATMIN
        self.latmax = LATMAX
        self.fillval = FILLVAL
        self.GRDFILE = GRDFILE

        try:
            with netcdf.Dataset(self.GRDFILE) as h_nc:
                pass
        except Exception:
            try:
                with netcdf.Dataset(root() + self.GRDFILE) as h_nc:
                    self.GRDFILE = root() + self.GRDFILE
            except Exception:
                print 'No file at: ', self.GRDFILE
                print 'or at ', root() + self.GRDFILE
                raise Exception  # no grid file found

        with netcdf.Dataset(self.GRDFILE) as h_nc:
            self._lon = h_nc.variables['lon_rho'][:]
            self._lat = h_nc.variables['lat_rho'][:]
            self._pm = h_nc.variables['p_m'][:]
            self._pn = h_nc.variables['p_n'][:]
            self._f_val = h_nc.variables['f_coriolis'][:]
            self._angle = h_nc.variables['angle'][:]
            self._mask = h_nc.variables['mask_rho'][:]
            self._gof = self.GRAVITY / self._f_val

        self.set_initial_indices()
        self.set_index_padding()
        self.set_basemap(with_pad=with_pad)
        self.uvpmask()
        self.set_u_v_eke()
        self.shape = self.lon().shape
        # pad2 = 2 * self.pad
#         self.shape = (self.f_coriolis().shape[0] -
#                       pad2, self.f_coriolis().shape[1] - pad2)

        # Parameters for different grid files; modify accordingly
        if self.GRDFILE.split('/')[-1] in 'roms_grd_NA2009_7pt5km.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0, 0.0, 120.0, 32.0, 2, [[1, 'S'], [1, 'E'], [1, ' N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'gc_2009_1km_grd_smooth.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0, 2.0, 120.0, 60.0, 2, [[1, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'cb_2009_3km_grd_smooth.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   42.0,   2,           [[1, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'roms_grd_CanBas_smooth_bnd.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          0.0,          120.0,   32.0,   1,           [[1, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'grd_Med14km_2010.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   50.0,   2,           [[0, 'S'], [0, 'E'], [0, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'grd_MedWest4pt75km_2010_smooth.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   50.0,   2,           [[0, 'S'], [0, 'E'], [0, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'grd_ATL_15km.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                10.0,          2.0,          400.0,   40.0,   2,           [[1, 'S'], [1, 'E'], [1, 'N'], [0, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'grd_NA2011_7pt5km.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   42.0,   2,           [[1, 'S'], [1, 'E'], [1, 'N'], [1, 'W']]
        ####
        elif self.GRDFILE.split('/')[-1] in 'grd_MedSea15.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   42.0,   2,           [[0, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        elif self.GRDFILE.split('/')[-1] in 'grd_MedSea5.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   42.0,   2,           [[0, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        elif self.GRDFILE.split('/')[-1] in 'grd_canbas2.5.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          2.0,          120.0,   42.0,   2,           [[1, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        elif self.GRDFILE.split('/')[-1] in 'grd_canwake4km.h_nc':
            self.theta_s, self.theta_b, self.hc, self.N, self.scoord, self.obcs = \
                6.0,          0.0,          200.0,   42.0,   2,           [[1, 'S'], [0, 'E'], [1, 'N'], [1, 'W']]
        else: 
            Exception  # grid not specified, add a new 'elif' on line above with gridfile name and parameters 

    def lon(self):
        return self._lon[self.view]

    def lat(self):
        return self._lat[self.view]

    def lonpad(self):
        return self._lon[self.view_padding]

    def latpad(self):
        return self._lat[self.view_padding]

    def p_m(self):
        return self._pm[self.view_padding]

    def p_n(self):
        return self._pn[self.view_padding]

    def mask(self):
        return self._mask[self.view_padding]

    def angle(self):
        return self._angle[self.view_padding]

    def h(self):
        return self._h[self.view_padding]

    def hraw(self):
        return self._hraw[self.view_padding]

    def f_coriolis(self):
        return self._f_val[self.view_padding]

    def gof(self):
        return self._gof[self.view_padding]

    def umask(self):
        return self._umask[self.jp0:self.jp1, self.ip0:self.ip1-1]

    def vmask(self):
        return self._vmask[self.jp0:self.jp1-1, self.ip0:self.ip1]

    def uvpmask(self):
        '''
        Get mask at u, v, psi points
        '''
        Mp, Lp = self._mask.shape
        M = Mp - 1
        L = Lp - 1
        self._umask = self._mask[:, :L] * self._mask[:, 1:Lp]
        self._vmask = self._mask[:M] * self._mask[1:Mp]
        self._psimask = self._umask[:M] * self._umask[1:Mp]
        return self

    def boundary(self, imin=0, imax=-1, jmin=0, jmax=-1):
        '''
        Return lon, lat of perimeter around a ROMS grid
        Indices to get boundary of specified subgrid
        '''
        lon = np.r_[(self.lon()[jmin:jmax, imin],
                     self.lon()[jmax, imin:imax],
                     self.lon()[jmax:jmin:-1, imax],
                     self.lon()[jmin, imax:imin:-1])]
        lat = np.r_[(self.lat()[jmin:jmax, imin],
                     self.lat()[jmax, imin:imax],
                     self.lat()[jmax:jmin:-1, imax],
                     self.lat()[jmin, imax:imin:-1])]
        return lon, lat

    def brypath(self, imin=0, imax=-1, jmin=0, jmax=-1):
        '''
        Return Path object of perimeter around a ROMS grid
        Indices to get boundary of specified subgrid
        '''
        lon, lat = self.boundary(imin, imax, jmin, jmax)
        brypath = np.array([lon, lat]).T
        return Path.Path(brypath)

    def coastline(self):
        return getcoast(self.coastfile)

    def VertCoordType(self):
        h_nc = netcdf.Dataset(self.GRDFILE, 'r')
        var = h_nc.VertCoordType
        h_nc.close()
        return var

    def resolution(self, meters=False):
        '''
        Get mean grid resolution in degrees or meters
        If meters defined, return degrees
        '''
        mean_earth_radius = 6371315.
        if meters:  # Degrees to meters
            res = np.copy(meters)
            res *= np.pi * mean_earth_radius / 180.0
        else:  # Meters to degrees
            res = np.mean(np.sqrt((1. / self.p_m()) * (1. / self.p_n())))
            res /= np.pi * mean_earth_radius / 180.
        return res

    def title(self):
        h_nc = netcdf.Dataset(self.GRDFILE, 'r')
        var = h_nc.title
        h_nc.close()
        return var

    def scoord2z_r(self, zeta=0., alpha=0., beta=0., verbose=False):
        zr = scoord2z(self.h(), self.theta_s, self.theta_b, self.hc, self.N,
                      'r', self.scoord, zeta=zeta, alpha=alpha, beta=beta,
                      verbose=verbose)
        return zr

    def scoord2z_w(self, zeta=0., alpha=0., beta=0., verbose=False):
        zw = scoord2z(self.h(), self.theta_s, self.theta_b, self.hc, self.N,
                      'w', self.scoord, zeta=zeta, alpha=alpha, beta=beta,
                      verbose=verbose)
        return zw

    def dz(self):
        '''
        Returns cell heights
        '''
        zw = self.scoord2z_w()
        dz = np.diff(zw, axis=0)
        return dz

    def rotate_vec(self, z, m):
        '''
        Rotate to account for grid rotation
        '''
        # angle = self.angle()[jstr:jend,istr:iend].mean()
        cosa = np.cos(self.angle())
        sina = np.sin(self.angle())
        zres = (z * cosa) + (m * sina)
        mres = (m * cosa) - (z * sina)
        return zres, mres

    def transect(self, ln1, lt1, ln2, lt2, d_x):
        '''
        Return lon/lat arrays for a transect between
        two points with resolution d_x
        TO DO: check points are within domain
        Input:   1. lon/lat points  (ln1,lt1,ln2,lt2)
                 2. d_x [km]
        Returns: 1. the two arrays
                 2. the distance [m]
                 2. the angle [degrees]
        '''
        dist = et.distLonLat(ln1, lt1, ln2, lt2)
        num_stn = np.round(dist[0] / (d_x * 1000.))
        tr_ln = np.linspace(ln1, ln2, num=num_stn)
        tr_lt = np.linspace(lt1, lt2, num=num_stn)
        return tr_ln, tr_lt, dist[0], dist[1]
