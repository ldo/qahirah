"""A Python 3 wrapper for the Cairo graphics library <http://cairographics.org/>
using ctypes. This is modelled on Pycairo, but differs from that in
some important ways. It also operates at a higher level than the underlying
Cairo API where this makes sense. For example, it defines a “Vector”
class for representing a 2D point, with operations on the Vector as a
whole, rather than having to operate on individual x- and y-coordinates.
Also, get/set API calls are collapsed into read/write Python properties
where this makes sense; for example, instead of Context.get_line_width()
and Context.set_line_width() calls, there is a Context.line_width property
that may be read and written.
"""
#+
# Copyright 2015 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under the GNU Lesser General Public License v2.1 or later.
#-

import math
from numbers import \
    Number
import ctypes as ct

cairo = ct.cdll.LoadLibrary("libcairo.so.2")

class CAIRO :
    "useful definitions adapted from cairo.h. You will need to use the constants," \
    " but apart from that, see the more Pythonic wrappers defined outside this" \
    " class in preference to accessing low-level structures directly."

    # General ctypes gotcha: when passing addresses of ctypes-constructed objects
    # to routine calls, do not construct the objects directly in the call. Otherwise
    # the refcount goes to 0 before the routine is actually entered, and the object
    # can get prematurely disposed. Always store the object reference into a local
    # variable, and pass the value of the variable instead.

    # cairo_status_t codes
    STATUS_SUCCESS = 0

    STATUS_NO_MEMORY = 1
    STATUS_INVALID_RESTORE = 2
    STATUS_INVALID_POP_GROUP = 3
    STATUS_NO_CURRENT_POINT = 4
    STATUS_INVALID_MATRIX = 5
    STATUS_INVALID_STATUS = 6
    STATUS_NULL_POINTER = 7
    STATUS_INVALID_STRING = 8
    STATUS_INVALID_PATH_DATA = 9
    STATUS_READ_ERROR = 10
    STATUS_WRITE_ERROR = 11
    STATUS_SURFACE_FINISHED = 12
    STATUS_SURFACE_TYPE_MISMATCH = 13
    STATUS_PATTERN_TYPE_MISMATCH = 14
    STATUS_INVALID_CONTENT = 15
    STATUS_INVALID_FORMAT = 16
    STATUS_INVALID_VISUAL = 17
    STATUS_FILE_NOT_FOUND = 18
    STATUS_INVALID_DASH = 19
    STATUS_INVALID_DSC_COMMENT = 20
    STATUS_INVALID_INDEX = 21
    STATUS_CLIP_NOT_REPRESENTABLE = 22
    STATUS_TEMP_FILE_ERROR = 23
    STATUS_INVALID_STRIDE = 24
    STATUS_FONT_TYPE_MISMATCH = 25
    STATUS_USER_FONT_IMMUTABLE = 26
    STATUS_USER_FONT_ERROR = 27
    STATUS_NEGATIVE_COUNT = 28
    STATUS_INVALID_CLUSTERS = 29
    STATUS_INVALID_SLANT = 30
    STATUS_INVALID_WEIGHT = 31
    STATUS_INVALID_SIZE = 32
    STATUS_USER_FONT_NOT_IMPLEMENTED = 33
    STATUS_DEVICE_TYPE_MISMATCH = 34
    STATUS_DEVICE_ERROR = 35
    STATUS_INVALID_MESH_CONSTRUCTION = 36
    STATUS_DEVICE_FINISHED = 37

    STATUS_LAST_STATUS = 38

    # cairo_format_t codes
    FORMAT_INVALID = -1
    FORMAT_ARGB32 = 0
    FORMAT_RGB24 = 1
    FORMAT_A8 = 2
    FORMAT_A1 = 3
    FORMAT_RGB16_565 = 4
    FORMAT_RGB30 = 5

    # cairo_extend_t codes
    EXTEND_NONE = 0
    EXTEND_REPEAT = 1
    EXTEND_REFLECT = 2
    EXTEND_PAD = 3

    # cairo_operator_t codes
    OPERATOR_CLEAR = 0

    OPERATOR_SOURCE = 1
    OPERATOR_OVER = 2
    OPERATOR_IN = 3
    OPERATOR_OUT = 4
    OPERATOR_ATOP = 5

    OPERATOR_DEST = 6
    OPERATOR_DEST_OVER = 7
    OPERATOR_DEST_IN = 8
    OPERATOR_DEST_OUT = 9
    OPERATOR_DEST_ATOP = 10

    OPERATOR_XOR = 11
    OPERATOR_ADD = 12
    OPERATOR_SATURATE = 13

    OPERATOR_MULTIPLY = 14
    OPERATOR_SCREEN = 15
    OPERATOR_OVERLAY = 16
    OPERATOR_DARKEN = 17
    OPERATOR_LIGHTEN = 18
    OPERATOR_COLOR_DODGE = 19
    OPERATOR_COLOR_BURN = 20
    OPERATOR_HARD_LIGHT = 21
    OPERATOR_SOFT_LIGHT = 22
    OPERATOR_DIFFERENCE = 23
    OPERATOR_EXCLUSION = 24
    OPERATOR_HSL_HUE = 25
    OPERATOR_HSL_SATURATION = 26
    OPERATOR_HSL_COLOR = 27
    OPERATOR_HSL_LUMINOSITY = 28

    class matrix_t(ct.Structure) :
        _fields_ = \
            [
                ("xx", ct.c_double),
                ("yx", ct.c_double),
                ("xy", ct.c_double),
                ("yy", ct.c_double),
                ("x0", ct.c_double),
                ("y0", ct.c_double),
            ]
    #end matrix_t

    # cairo_antialias_t codes
    ANTIALIAS_DEFAULT = 0
    # method
    ANTIALIAS_NONE = 1
    ANTIALIAS_GRAY = 2
    ANTIALIAS_SUBPIXEL = 3
    # hints
    ANTIALIAS_FAST = 4
    ANTIALIAS_GOOD = 5
    ANTIALIAS_BEST = 6

    # cairo_fill_rule_t codes
    FILL_RULE_WINDING = 0
    FILL_RULE_EVEN_ODD = 1

    # cairo_line_cap_t codes
    LINE_CAP_BUTT = 0
    LINE_CAP_ROUND = 1
    LINE_CAP_SQUARE = 2

    # cairo_line_join_t codes
    LINE_JOIN_MITER = 0
    LINE_JOIN_ROUND = 1
    LINE_JOIN_BEVEL = 2

#end CAIRO

cairo.cairo_version_string.restype = ct.c_char_p
cairo.cairo_status_to_string.restype = ct.c_char_p

cairo.cairo_status.argtypes = (ct.c_void_p,)
cairo.cairo_create.argtypes = (ct.c_void_p,)
cairo.cairo_create.restype = ct.c_void_p
cairo.cairo_destroy.restype = ct.c_void_p
cairo.cairo_save.argtypes = (ct.c_void_p,)
cairo.cairo_restore.argtypes = (ct.c_void_p,)

cairo.cairo_copy_path.argtypes = (ct.c_void_p,)
cairo.cairo_copy_path.restype = ct.c_void_p
cairo.cairo_copy_path_flat.argtypes = (ct.c_void_p,)
cairo.cairo_copy_path_flat.restype = ct.c_void_p
cairo.cairo_append_path.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_has_current_point.argtypes = (ct.c_void_p,)
cairo.cairo_get_current_point.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_new_path.argtypes = (ct.c_void_p,)
cairo.cairo_new_sub_path.argtypes = (ct.c_void_p,)
cairo.cairo_close_path.argtypes = (ct.c_void_p,)
cairo.cairo_arc.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_arc_negative.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_curve_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_line_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_move_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_rectangle.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_glyph_path.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int)
cairo.cairo_text_path.argtypes = (ct.c_void_p, ct.c_char_p)
cairo.cairo_rel_curve_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_rel_line_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_rel_move_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_path_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)

cairo.cairo_translate.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_scale.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_rotate.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_transform.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_set_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_identity_matrix.argtypes = (ct.c_void_p,)
cairo.cairo_user_to_device.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_user_to_device_distance.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_device_to_user.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_device_to_user_distance.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)

cairo.cairo_image_surface_create.restype = ct.c_void_p
cairo.cairo_get_source.argtypes = (ct.c_void_p,)
cairo.cairo_get_source.restype = ct.c_void_p
cairo.cairo_set_source_rgb.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_set_source_rgba.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_set_source.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_antialias.argtypes = (ct.c_void_p,)
cairo.cairo_set_dash.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_double)
cairo.cairo_get_dash_count.argtypes = (ct.c_void_p,)
cairo.cairo_get_dash.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_set_antialias.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_set_fill_rule.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_get_fill_rule.argtypes = (ct.c_void_p,)
cairo.cairo_set_line_cap.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_get_line_cap.argtypes = (ct.c_void_p,)
cairo.cairo_set_line_join.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_get_line_join.argtypes = (ct.c_void_p,)
cairo.cairo_get_line_width.argtypes = (ct.c_void_p,)
cairo.cairo_get_line_width.restype = ct.c_double
cairo.cairo_set_line_width.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_get_miter_limit.restype = ct.c_double
cairo.cairo_set_miter_limit.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_get_operator.argtypes = (ct.c_void_p,)
cairo.cairo_set_operator.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_get_tolerance.restype = ct.c_double
cairo.cairo_set_tolerance.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_clip.argtypes = (ct.c_void_p,)
cairo.cairo_clip_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_clip_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_reset_clip.argtypes = (ct.c_void_p,)
cairo.cairo_fill.argtypes = (ct.c_void_p,)
cairo.cairo_fill_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_fill_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_in_fill.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_mask.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_mask_surface.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_paint.argtypes = (ct.c_void_p,)
cairo.cairo_paint_with_alpha.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_stroke.argtypes = (ct.c_void_p,)
cairo.cairo_stroke_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_stroke_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_in_stroke.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)

cairo.cairo_surface_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_surface_flush.argtypes = (ct.c_void_p,)
cairo.cairo_surface_write_to_png.argtypes = (ct.c_void_p, ct.c_char_p)
cairo.cairo_image_surface_create.restype = ct.c_void_p
cairo.cairo_image_surface_get_format.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_width.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_height.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_stride.argtypes = (ct.c_void_p,)

cairo.cairo_pattern_status.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_reference.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_reference.restype = ct.c_void_p
cairo.cairo_pattern_create_rgb.argtypes = (ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_create_rgb.restype = ct.c_void_p
cairo.cairo_pattern_create_rgba.argtypes = (ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_create_rgba.restype = ct.c_void_p
cairo.cairo_pattern_get_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_set_matrix.argtypes = (ct.c_void_p, ct.c_void_p)

cairo.cairo_path_destroy.argtypes = (ct.c_void_p,)

def version() :
    "the Cairo version as a single integer."
    return \
        cairo.cairo_version()
#end version

def version_tuple() :
    "the Cairo version as a triple of integers."
    vers = cairo.cairo_version()
    return \
        (vers // 10000, vers // 100 % 100, vers % 100)
#end version_tuple

def version_string() :
    "the Cairo version string."
    return \
        cairo.cairo_version_string().decode("utf-8")
#end version_string

def status_to_string(status) :
    return \
        cairo.cairo_status_to_string(status).decode("utf-8")
#end status_to_string

def debug_reset_static_data() :
    cairo.cairo_debug_reset_static_data()
#end debug_reset_static_data

def check(status) :
    if status != 0 :
        raise CairoError(status)
    #end if
#end check

class CairoError(Exception) :
    "just to identify a Cairo-specific error exception."

    def __init__(self, code) :
        self.args = ("Cairo error %d -- %s" % (code, status_to_string(code)),)
    #end __init__

#end CairoError

deg = 180 / math.pi
  # All angles are in radians. You can use the standard Python functions math.degrees
  # and math.radians to convert back and forth, or multiply and divide by this deg
  # factor: divide by deg to convert degrees to radians, and multiply by deg to convert
  # the other way, e.g.
  #
  #     math.sin(45 / deg)
  #     math.atan(1) * deg

class Vector :
    "something missing from Cairo itself, a representation of a 2D point."

    def __init__(self, x, y) :
        self.x = x
        self.y = y
    #end __init__

    def to_tuple(self) :
        return \
            (self.x, self.y)
    #end to_tuple

    def __repr__(self) :
        return \
            "Vector(%.3f, %.3f)" % (self.x, self.y)
    #end __repr__

    def __getitem__(self, i) :
        "being able to access elements by index allows a Vector to be cast to a tuple or list."
        return \
            (self.x, self.y)[i]
    #end __getitem__

    def __add__(v1, v2) :
        return \
            (
                lambda : NotImplemented,
                lambda : Vector(v1.x + v2.x, v1.y + v2.y)
            )[isinstance(v2, Vector)]()
    #end __add__

    def __neg__(self) :
        """reflect across origin."""
        return Vector \
          (
            x = - self.x,
            y = - self.y
          )
    #end __neg__

    def __sub__(v1, v2) :
        return \
            (
                lambda : NotImplemented,
                lambda : Vector(v1.x - v2.x, v1.y - v2.y)
            )[isinstance(v2, Vector)]()
    #end __sub__

    def __mul__(v, f) :
        if isinstance(f, Vector) :
            result = Vector(v.x * f.x, v.y * f.y)
        elif isinstance(f, Number) :
            result = Vector(v.x * f, v.y * f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __mul__
    __rmul__ = __mul__

    def __truediv__(v, f) :
        if isinstance(f, Vector) :
            result = Vector(v.x / f.x, v.y / f.y)
        elif isinstance(f, Number) :
            result = Vector(v.x / f, v.y / f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __truediv__

    @staticmethod
    def unit(angle) :
        "returns the unit vector with the specified direction."
        return \
            Vector(math.cos(angle), math.sin(angle))
    #end unit

    def rotate(self, angle) :
        "returns the Vector rotated by the specified angle."
        cos = math.cos(angle)
        sin = math.sin(angle)
        return \
            Vector(self.x * cos - self.y * sin, self.x * sin + self.y * cos)
    #end rotate

    def __abs__(self) :
        "use abs() to get the length of a Vector."
        return \
            math.hypot(self.x, self.y)
    #end __abs__

    def angle(self) :
        "returns the Vector’s rotation angle."
        return \
            math.atan2(self.y, self.x)
    #end angle

    @staticmethod
    def from_polar(length, angle) :
        "constructs a Vector from a length and a direction."
        return \
            Vector(length * math.cos(angle), length * math.sin(angle))
    #end from_polar

#end Vector

class Matrix :
    "representation of a 3-by-2 affine homogeneous matrix."

    def __init__(self, xx, yx, xy, yy, x0, y0) :
        self.xx = xx
        self.yx = yx
        self.xy = xy
        self.yy = yy
        self.x0 = x0
        self.y0 = y0
        # self.u = 0
        # self.v = 0
        # self.w = 1
    #end __init__

    @staticmethod
    def from_cairo(m) :
        return \
            Matrix(m.xx, m.yx, m.xy, m.yy, m.x0, m.y0)
    #end from_cairo

    def to_cairo(m) :
        return \
            CAIRO.matrix_t(m.xx, m.yx, m.xy, m.yy, m.x0, m.y0)
    #end to_cairo

    @staticmethod
    def identity() :
        "returns an identity matrix."
        return Matrix(1, 0, 0, 1, 0, 0)
    #end identity

    def __mul__(m1, m2) :
        "returns concatenation with another Matrix."
        return Matrix \
          (
            xx = m2.xx * m1.xx + m2.xy * m1.yx,
            yx = m2.yx * m1.xx + m2.yy * m1.yx,
            xy = m2.xx * m1.xy + m2.xy * m1.yy,
            yy = m2.yx * m1.xy + m2.yy * m1.yy,
            x0 = m2.xx * m1.x0 + m2.xy * m1.y0 + m2.x0,
            y0 = m2.yx * m1.x0 + m2.yy * m1.y0 + m2.y0,
          )
    #end __mul__

    @staticmethod
    def translation(delta) :
        "returns a Matrix that translates by the specified delta Vector."
        return Matrix(1, 0, 0, 1, delta.x, delta.y)
    #end translation

    @staticmethod
    def scaling(factor) :
        "returns a matrix that scales by the specified scalar or Vector factors."
        if isinstance(factor, Number) :
            result = Matrix(factor, 0, 0, factor, 0, 0)
        elif isinstance(factor, Vector) :
            result = Matrix(factor.x, 0, 0, factor.y, 0, 0)
        else :
            raise TypeError("factor must be a number or a Vector")
        #end if
        return \
            result
    #end scaling

    @staticmethod
    def rotation(angle) :
        "returns a Matrix that rotates about the origin by the specified" \
        " angle in radians."
        cos = math.cos(angle)
        sin = math.sin(angle)
        return Matrix(cos, -sin, sin, cos, 0, 0)
    #end rotation

    def det(self) :
        "matrix determinant."
        return \
            (self.xx * self.yy - self.xy * self.yx)
    #end det

    def __abs__(self) :
        "the absolute value of a Matrix is its determinant."
        return \
            self.det()
    #end __abs__

    def adj(self) :
        "matrix adjoint."
        return Matrix \
          (
            xx = self.yy,
            yx = - self.yx,
            x0 = self.xy * self.y0 - self.yy * self.x0,
            xy = - self.xy,
            yy = self.xx,
            y0 = self.yx * self.x0 - self.xx * self.y0,
          )
    #end adj

    def inv(self) :
        "matrix inverse computed using minors" \
        " <http://mathworld.wolfram.com/MatrixInverse.html>."
        adj = self.adj()
        det = self.det()
        return Matrix \
          (
            xx = adj.xx / det,
            yx = adj.yx / det,
            x0 = adj.x0 / det,
            xy = adj.xy / det,
            yy = adj.yy / det,
            y0 = adj.y0 / det,
          )
    #end inv

    def map(self, pt) :
        "maps a Vector through the Matrix."
        return Vector \
          (
            x = pt.x * self.xx + pt.y * self.xy + self.x0,
            y = pt.x * self.yx + pt.y * self.yy + self.y0
          )
    #end map

    def mapdelta(self, pt) :
        "maps a Vector through the Matrix, ignoring the translation part."
        return Vector \
          (
            x = pt.x * self.xx + pt.y * self.xy,
            y = pt.x * self.yx + pt.y * self.yy
          )
    #end mapdelta

    def mapiter(self, pts) :
        "maps an iterable of Vectors through the Matrix."
        pts = iter(pts)
        while True : # until pts raises StopIteration
            yield self.map(pts.next())
        #end while
    #end mapiter

    def mapdeltaiter(self, pts) :
        "maps an iterable of Vectors through the Matrix, ignoring the" \
        " translation part."
        pts = iter(pts)
        while True : # until pts raises StopIteration
            yield self.mapdelta(pts.next())
        #end while
    #end mapdeltaiter

    def __repr__(self) :
        return \
            (
                "Matrix(%f, %f, %f, %f, %f, %f)"
            %
                (
                    self.xx, self.yx,
                    self.xy, self.yy,
                    self.x0, self.y0,
                )
            )
    #end __repr__

#end Matrix

class Context :
    "a Cairo drawing context. Instantiate with a Surface object."
    # <http://cairographics.org/manual/cairo-cairo-t.html>

    def _check(self) :
        # check for error from last operation on this Context.
        check(cairo.cairo_status(self._cairobj))
    #end _check

    def __init__(self, surface) :
        self._cairobj = cairo.cairo_create(surface._cairobj)
        self._check()
    #end __init__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    def save(self) :
        cairo.cairo_save(self._cairobj)
    #end save

    def restore(self) :
        cairo.cairo_restore(self._cairobj)
    #end restore

    # TODO: get_target, push/pop group

    @property
    def source(self) :
        "a copy of the current source Pattern. Will not return the same" \
        " wrapper object each time, but Pattern objects can be compared for equality," \
        " which means they reference the same underlying Cairo pattern_t object."
        return \
            Pattern(cairo.cairo_pattern_reference(cairo.cairo_get_source(self._cairobj)))
    #end source

    @source.setter
    def source(self, source) :
        if not isinstance(source, Pattern) :
            raise TypeError("source is not a Pattern")
        #end if
        cairo.cairo_set_source(self._cairobj, source._cairobj)
        self._check()
    #end source

    def set_source_rgb(self, r, g, b) :
        cairo.cairo_set_source_rgb(self._cairobj, r, g, b)
        self._check()
    #end set_source_rgb

    def set_source_rgba(self, r, g, b, a) :
        cairo.cairo_set_source_rgba(self._cairobj, r, g, b, a)
        self._check()
    #end set_source_rgba

    @property
    def antialias(self) :
        "the current antialias mode."
        return \
            cairo.cairo_get_antialias(self._cairobj)
    #end antialias

    @antialias.setter
    def antialias(self, antialias) :
        cairo.cairo_set_antialias(self._cairobj, antialias)
    #end antialias

    @property
    def dash(self) :
        "the current line dash setting, as a tuple of two items: the first is a tuple" \
        " of reals specifying alternating on- and off-lengths, the second is a real" \
        " specifying the starting offset."
        segs = (cairo.cairo_get_dash_count(self._cairobj) * ct.c_double)()
        offset = ct.c_double()
        cairo.cairo_get_dash(self._cairobj, ct.byref(segs), ct.byref(offset))
        return \
            (tuple(i for i in segs), offset.value)
    #end dash

    @dash.setter
    def dash(self, dashes) :
        segs, offset = dashes
        nrsegs = len(segs)
        csegs = (nrsegs * ct.c_double)()
        for i in range(nrsegs) :
            csegs[i] = segs[i]
        #end for
        cairo.cairo_set_dash(self._cairobj, ct.byref(csegs), nrsegs, offset)
    #end dash

    @property
    def fill_rule(self) :
        return \
            cairo.cairo_get_fill_rule(self._cairobj)
    #end fill_rule

    @fill_rule.setter
    def fill_rule(self, fill_rule) :
        cairo.cairo_set_fill_rule(self._cairobj, fill_rule)
    #end fill_rule

    @property
    def line_cap(self) :
        return \
            cairo.cairo_get_line_cap(self._cairobj)
    #end line_cap

    @line_cap.setter
    def line_cap(self, line_cap) :
        cairo.cairo_set_line_cap(self._cairobj, line_cap)
    #end line_cap

    @property
    def line_join(self) :
        return \
            cairo.cairo_get_line_join(self._cairobj)
    #end line_join

    @line_join.setter
    def line_join(self, line_join) :
        cairo.cairo_set_line_join(self._cairobj, line_join)
    #end line_join

    @property
    def line_width(self) :
        "the current stroke line width."
        return \
            cairo.cairo_get_line_width(self._cairobj)
    #end line_width

    @line_width.setter
    def line_width(self, width) :
        cairo.cairo_set_line_width(self._cairobj, width)
    #end line_width

    @property
    def miter_limit(self) :
        return \
            cairo.cairo_get_miter_limit(self._cairobj)
    #end miter_limit

    @miter_limit.setter
    def miter_limit(self, width) :
        cairo.cairo_set_miter_limit(self._cairobj, width)
    #end miter_limit

    @property
    def operator(self) :
        "the current drawing operator."
        return \
            cairo.cairo_get_operator(self._cairobj)
    #end operator

    @operator.setter
    def operator(self, op) :
        "sets a new drawing operator."
        cairo.cairo_set_operator(self._cairobj, int(op))
        self._check()
    #end operator

    @property
    def tolerance(self) :
        return \
            cairo.cairo_get_tolerance(self._cairobj)
    #end tolerance

    @tolerance.setter
    def tolerance(self, width) :
        cairo.cairo_set_tolerance(self._cairobj, width)
    #end tolerance

    def clip(self) :
        cairo.cairo_clip(self._cairobj)
    #end clip

    def clip_preserve(self) :
        cairo.cairo_clip_preserve(self._cairobj)
    #end clip_preserve

    # TODO: in_clip, clip_extents, rectangle_list

    def reset_clip(self) :
        cairo.cairo_reset_clip(self._cairobj)
    #end reset_clip

    def fill(self) :
        cairo.cairo_fill(self._cairobj)
    #end fill

    def fill_preserve(self) :
        cairo.cairo_fill_preserve(self._cairobj)
    #end fill_preserve

    # TODO: fill_extents, in_fill

    def mask(self, pattern) :
        if not isinstance(pattern, Pattern) :
            raise TypeError("pattern is not a Pattern")
        #end if
        cairo.cairo_mask(self._cairobj, pattern._cairobj)
    #end mask

    def mask_surface(self, surface, origin) :
        if not isinstance(surface, Surface) :
            raise TypeError("surface is not a Surface")
        #end if
        cairo.cairo_mask_surface(self._cairobj, surface._cairobj, origin.x, origin.y)
    #end mask_surface

    def paint(self) :
        cairo.cairo_paint(self._cairobj)
    #end paint

    def paint_with_alpha(self, alpha) :
        cairo.cairo_paint_with_alpha(self._cairobj, alpha)
    #end paint_with_alpha

    def stroke(self) :
        cairo.cairo_stroke(self._cairobj)
    #end stroke

    def stroke_preserve(self) :
        cairo.cairo_stroke_preserve(self._cairobj)
    #end stroke_preserve

    # TODO: stroke_extents, in_stroke
    # TODO: copy/show page, user_data

    # paths <http://cairographics.org/manual/cairo-Paths.html>

    def copy_path(self) :
        return \
            Path(cairo.cairo_copy_path(self._cairobj))
    #end copy_path

    def copy_path_flat(self) :
        return \
            Path(cairo.cairo_copy_path_flat(self._cairobj))
    #end copy_path_flat

    def append_path(self, path) :
        if not isinstance(source, Path) :
            raise TypeError("path is not a Path")
        #end if
        cairo.cairo_append_path(self._cairobj, path._cairobj)
        self._check()
    #end append_path

    @property
    def has_current_point(self) :
        return \
            bool(cairo.cairo_has_current_point(self._cairobj))
    #end has_current_point

    @property
    def current_point(self) :
        if self.has_current_point :
            x = ct.c_double()
            y = ct.c_double()
            cairo.cairo_get_current_point(self._cairobj, ct.byref(x), ct.byref(y))
            result = Vector(x.value, y.value)
        else :
            result = None
        #end if
        return \
            result
    #end current_point

    def new_path(self) :
        cairo.cairo_new_path(self._cairobj)
    #end new_path

    def new_sub_path(self) :
        cairo.cairo_new_sub_path(self._cairobj)
    #end new_sub_path

    def close_path(self) :
        cairo.cairo_close_path(self._cairobj)
    #end close_path

    # TODO: arc, arc_negative

    def curve_to(self, p1, p2, p3) :
        cairo.cairo_curve_to(self._cairobj, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
    #end curve_to

    def curve_to_xy(self, x1, y1, x2, y2, x3, y3) :
        cairo.cairo_curve_to(self._cairobj, x1, y1, x2, y2, x3, y3)
    #end curve_to_xy

    def line_to(self, p) :
        cairo.cairo_line_to(self._cairobj, p.x, p.y)
    #end line_to

    def line_to_xy(self, x, y) :
        cairo.cairo_line_to(self._cairobj, x, y)
    #end line_to_xy

    def move_to(self, p) :
        cairo.cairo_move_to(self._cairobj, p.x, p.y)
    #end move_to

    def move_to_xy(self, x, y) :
        cairo.cairo_move_to(self._cairobj, x, y)
    #end move_to_xy

    # TODO: glyph_paths

    def text_path(self, text) :
        cairo.cairo_text_path(self._cairobj, text.encode("utf-8"))
    #end text_path

    def rel_curve_to(self, p1, p2, p3) :
        cairo.cairo_rel_curve_to(self._cairobj, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
    #end rel_curve_to

    def rel_curve_to_xy(self, x1, y1, x2, y2, x3, y3) :
        cairo.cairo_rel_curve_to(self._cairobj, x1, y1, x2, y2, x3, y3)
    #end rel_curve_to_xy

    def rel_line_to(self, p) :
        cairo.cairo_rel_line_to(self._cairobj, p.x, p.y)
    #end rel_line_to

    def rel_line_to_xy(self, x, y) :
        cairo.cairo_rel_line_to(self._cairobj, x, y)
    #end rel_line_to_xy

    def rel_move_to(self, p) :
        cairo.cairo_rel_move_to(self._cairobj, p.x, p.y)
    #end rel_move_to

    def rel_move_to_xy(self, x, y) :
        cairo.cairo_rel_move_to(self._cairobj, x, y)
    #end rel_move_to_xy

    # TODO: path_extents

    # TODO: Regions <http://cairographics.org/manual/cairo-Regions.html>

    # Transformations <http://cairographics.org/manual/cairo-Transformations.html>

    # TODO: translate, scale, rotate

    def transform(self, m) :
        m = m.to_cairo()
        cairo.cairo_transform(self._cairobj, ct.byref(m))
    #end transform

    @property
    def matrix(self) :
        "the current transformation matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_get_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end matrix

    @matrix.setter
    def matrix(self, m) :
        m = m.to_cairo()
        cairo.cairo_set_matrix(self._cairobj, ct.byref(m))
        self._check()
    #end matrix

    def identity_matrix(self) :
        cairo.cairo_identity_matrix(self._cairobj)
    #end identity_matrix

    # TODO: user to/from device

    # TODO: Text <http://cairographics.org/manual/cairo-text.html>

#end Context

class Surface :
    "base class for Cairo surfaces. Do not instantiate directly."

    def __init__(self, _cairobj) :
        check(cairo.cairo_surface_status(_cairobj))
        self._cairobj = _cairobj
    #end __init__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_surface_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    def flush(self) :
        cairo.cairo_surface_flush(self._cairobj)
    #end flush

    def write_to_png(self, filename) :
        check(cairo.cairo_surface_write_to_png(self._cairobj, filename.encode("utf-8")))
    #end write_to_png

#end Surface

class ImageSurface(Surface) :
    "A Cairo image surface. Instantiate with a suitable CAIRO.FORMAT_xxx code" \
    " and desired integer dimensions."

    def __init__(self, format, width, height) :
        super().__init__(cairo.cairo_image_surface_create(int(format), int(width), int(height)))
    #end __init__

    @staticmethod
    def format_stride_for_width(format, width) :
        return \
            cairo.cairo_format_stride_for_width(int(format), int(width))
    #end format_stride_for_width

    # TODO: create_for_data, get_data

    @property
    def format(self) :
        return \
            cairo.cairo_image_surface_get_format(self._cairobj)
    #end format

    @property
    def width(self) :
        return \
            cairo.cairo_image_surface_get_width(self._cairobj)
    #end width

    @property
    def height(self) :
        return \
            cairo.cairo_image_surface_get_height(self._cairobj)
    #end height

    @property
    def stride(self) :
        return \
            cairo.cairo_image_surface_get_stride(self._cairobj)
    #end stride

#end ImageSurface

# TODO: PDF Surfaces, PNG Surfaces, PostScript Surfaces,
# Recording Surfaces, SVG Surfaces, Script Surfaces

class Pattern :
    "a Cairo Pattern object. Do not instantiate directly; use one of the create methods."
    # <http://cairographics.org/manual/cairo-cairo-pattern-t.html>

    def _check(self) :
        # check for error from last operation on this Pattern.
        check(cairo.cairo_pattern_status(self._cairobj))
    #end _check

    def __init__(self, _cairobj) :
        self._cairobj = _cairobj
        self._check()
    #end __init__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_pattern_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    def __eq__(self, other) :
        "do the two Pattern objects refer to the same Pattern. Needed because" \
        " Context.get_source cannot return the same Pattern object each time."
        return \
            self._cairobj == other._cairobj
    #end __eq__

    # TODO: color_stops

    @staticmethod
    def create_rgb(r, g, b) :
        "creates a Pattern that paints the destination with the specified opaque (r, g, b) colour."
        return \
            Pattern(cairo.cairo_pattern_create_rgb(r, g, b))
    #end create_rgb

    @staticmethod
    def create_rgba(r, g, b, a) :
        "creates a Pattern that paints the destination with the specified (r, g, b, a) colour."
        return \
            Pattern(cairo.cairo_pattern_create_rgba(r, g, b, a))
    #end create_rgb

    # TODO: create linear, radial, mesh

    # TODO: extend, filter

    @property
    def matrix(self) :
        result = CAIRO.matrix_t()
        cairo.cairo_pattern_get_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end matrix

    @matrix.setter
    def matrix(self, m) :
        m = m.to_cairo()
        cairo.cairo_pattern_set_matrix(self._cairobj, ct.byref(m))
    #end matrix

    # TODO: Raster Sources <http://cairographics.org/manual/cairo-Raster-Sources.html>

#end Pattern

class Path :
    "a Cairo Path object. Do not instantiate directly."

    def __init__(self, _cairobj) :
        self._cairobj = _cairobj
    #end __init__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_path_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    # TODO: cairo_path_data_t

#end Path

# TODO: font_face_t, scaled_font_face_t, font_options_t, FreeType fonts, user fonts
