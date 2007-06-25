# Needed ctypes routines
from ctypes import c_int, c_long, c_void_p, byref, string_at

# The GDAL C Library
from django.contrib.gis.gdal.libgdal import lgdal

# Other GDAL imports.
from django.contrib.gis.gdal.Envelope import Envelope, OGREnvelope
from django.contrib.gis.gdal.Feature import Feature
from django.contrib.gis.gdal.OGRError import OGRException, check_err
from django.contrib.gis.gdal.SpatialReference import SpatialReference

# For more information, see the OGR C API source code:
#  http://www.gdal.org/ogr/ogr__api_8h.html
#
# The OGR_L_* routines are relevant here.

get_srs = lgdal.OGR_L_GetSpatialRef
get_srs.restype = c_void_p
get_srs.argtypes = [c_void_p]

class Layer(object):
    "A class that wraps an OGR Layer, needs to be instantiated from a DataSource object."

    _layer = 0 # Initially NULL

    #### Python 'magic' routines ####
    def __init__(self, l):
        "Needs a C pointer (Python/ctypes integer) in order to initialize."
        if not l:
            raise OGRException, 'Cannot create Layer, invalid pointer given'
        self._layer = l
        self._ldefn = lgdal.OGR_L_GetLayerDefn(l)

    def __getitem__(self, index):
        "Gets the Feature at the specified index."
        if index < 0 or index >= self.num_feat:
            raise IndexError, 'index out of range'
        return Feature(lgdal.OGR_L_GetFeature(self._layer, c_long(index)))

    def __iter__(self):
        "Iterates over each Feature in the Layer."

        # Resetting the Layer before beginning iteration
        lgdal.OGR_L_ResetReading(self._layer)

        # Incrementing over each feature in the layer, and yielding
        #  to the caller of the function.
        for i in xrange(self.num_feat):
            yield self.__getitem__(i)

    def __len__(self):
        "The length is the number of features."
        return self.num_feat

    def __str__(self):
        "The string name of the layer."
        return self.name

    #### Layer properties ####
    @property
    def extent(self):
        "Returns the extent (an Envelope) of this layer."
        env = OGREnvelope()
        check_err(lgdal.OGR_L_GetExtent(self._layer, byref(env), c_int(1)))
        return Envelope(env)

    @property
    def name(self):
        "Returns the name of this layer in the Data Source."
        return string_at(lgdal.OGR_FD_GetName(self._ldefn))

    @property
    def num_feat(self, force=1):
        "Returns the number of features in the Layer."
        return lgdal.OGR_L_GetFeatureCount(self._layer, c_int(force))

    @property
    def num_fields(self):
        "Returns the number of fields in the Layer."
        return lgdal.OGR_FD_GetFieldCount(self._ldefn)

    @property
    def geom_type(self):
        "Returns the geometry type (OGRGeomType) of the Layer."
        return lgdal.OGR_FD_GetGeomType(self._ldefn)

    @property
    def srs(self):
        "Returns the Spatial Reference used in this Layer."
        return SpatialReference(lgdal.OSRClone(lgdal.OGR_L_GetSpatialRef(self._layer)), 'ogr')

    @property
    def fields(self):
        "Returns a list of the fields available in this Layer."
        return [ string_at(lgdal.OGR_Fld_GetNameRef(lgdal.OGR_FD_GetFieldDefn(self._ldefn, i)))
                 for i in xrange(self.num_fields) ]
    
