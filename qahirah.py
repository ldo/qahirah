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
# Copyright 2015-2020 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under the GNU Lesser General Public License v2.1 or later.
#-

import sys
import math
from numbers import \
    Real, \
    Complex
from collections import \
    namedtuple
import io
import colorsys
import array
import ctypes as ct
from weakref import \
    WeakKeyDictionary, \
    WeakValueDictionary
import atexit
try :
    import fontconfig
      # my Fontconfig wrapper, get from <https://github.com/ldo/python_fontconfig>
except ImportError :
    fontconfig = None
#end try
try :
    import freetype2
      # my FreeType wrapper, get from <https://github.com/ldo/python_freetype>
except ImportError :
    freetype2 = None
#end try

LIBNAME = \
    {
        "linux" :
            {
                "cairo" : "libcairo.so.2",
                "freetype" : "libfreetype.so.6",
                "fontconfig" : "libfontconfig.so.1",
            },
        "openbsd6" :
            {
                "cairo" : "libcairo.so.12",
                "freetype" : "libfreetype.so.28",
                "fontconfig" : "libfontconfig.so.11",
            },
    }[sys.platform]

cairo = ct.cdll.LoadLibrary(LIBNAME["cairo"])
if freetype2 == None :
    _ft = ct.cdll.LoadLibrary(LIBNAME["freetype"])
#end if
if fontconfig == None :
    try :
        _fc = ct.cdll.LoadLibrary(LIBNAME["fontconfig"])
    except OSError as fail :
        if True : # if fail.errno == 2 : # ENOENT
          # no point checking, because it is None! (Bug?)
            _fc = None
        else :
            raise
        #end if
    #end try
#end if

class CAIRO :
    "useful definitions adapted from cairo.h. You will need to use the constants," \
    " but apart from that, see the more Pythonic wrappers defined outside this" \
    " class in preference to accessing low-level structures directly."

    # General ctypes gotcha: when passing addresses of ctypes-constructed objects
    # to routine calls, do not construct the objects directly in the call. Otherwise
    # the refcount goes to 0 before the routine is actually entered, and the object
    # can get prematurely disposed. Always store the object reference into a local
    # variable, and pass the value of the variable instead.

    status_t = ct.c_uint
    c_ptr_p = ct.POINTER(ct.c_void_p)
    c_ubyte_p = ct.POINTER(ct.c_ubyte)
    c_int_p = ct.POINTER(ct.c_int)
    c_uint_p = ct.POINTER(ct.c_uint)
    c_ulong_p = ct.POINTER(ct.c_ulong)

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
    STATUS_JBIG2_GLOBAL_MISSING = 38
    STATUS_PNG_ERROR = 39
    STATUS_FREETYPE_ERROR = 40
    STATUS_WIN32_GDI_ERROR = 41
    STATUS_TAG_ERROR = 42

    STATUS_LAST_STATUS = 43

    # codes for cairo_surface_type_t
    SURFACE_TYPE_IMAGE = 0
    SURFACE_TYPE_PDF = 1
    SURFACE_TYPE_PS = 2
    SURFACE_TYPE_XLIB = 3
    SURFACE_TYPE_XCB = 4
    SURFACE_TYPE_GLITZ = 5
    SURFACE_TYPE_QUARTZ = 6
    SURFACE_TYPE_WIN32 = 7
    SURFACE_TYPE_BEOS = 8
    SURFACE_TYPE_DIRECTFB = 9
    SURFACE_TYPE_SVG = 10
    SURFACE_TYPE_OS2 = 11
    SURFACE_TYPE_WIN32_PRINTING = 12
    SURFACE_TYPE_QUARTZ_IMAGE = 13
    SURFACE_TYPE_SCRIPT = 14
    SURFACE_TYPE_QT = 15
    SURFACE_TYPE_RECORDING = 16
    SURFACE_TYPE_VG = 17
    SURFACE_TYPE_GL = 18
    SURFACE_TYPE_DRM = 19
    SURFACE_TYPE_TEE = 20
    SURFACE_TYPE_XML = 21
    SURFACE_TYPE_SKIA = 22
    SURFACE_TYPE_SUBSURFACE = 23
    SURFACE_TYPE_COGL = 24

    # cairo_format_t codes
    FORMAT_INVALID = -1
    FORMAT_ARGB32 = 0
    FORMAT_RGB24 = 1
    FORMAT_A8 = 2
    FORMAT_A1 = 3
    FORMAT_RGB16_565 = 4
    FORMAT_RGB30 = 5

    # cairo_content_t codes
    CONTENT_COLOR = 0x1000
    CONTENT_COLOUR = 0x1000
    CONTENT_ALPHA = 0x2000
    CONTENT_COLOR_ALPHA = 0x3000
    CONTENT_COLOUR_ALPHA = 0x3000

    # cairo_extend_t codes
    EXTEND_NONE = 0
    EXTEND_REPEAT = 1
    EXTEND_REFLECT = 2
    EXTEND_PAD = 3

    # cairo_filter_t codes
    FILTER_FAST = 0
    FILTER_GOOD = 1
    FILTER_BEST = 2
    FILTER_NEAREST = 3
    FILTER_BILINEAR = 4
    FILTER_GAUSSIAN = 5

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
    OPERATOR_COLOUR_DODGE = 19
    OPERATOR_COLOR_BURN = 20
    OPERATOR_COLOUR_BURN = 20
    OPERATOR_HARD_LIGHT = 21
    OPERATOR_SOFT_LIGHT = 22
    OPERATOR_DIFFERENCE = 23
    OPERATOR_EXCLUSION = 24
    OPERATOR_HSL_HUE = 25
    OPERATOR_HSL_SATURATION = 26
    OPERATOR_HSL_COLOR = 27
    OPERATOR_HSL_COLOUR = 27
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

    # cairo_subpixel_order_t codes
    SUBPIXEL_ORDER_DEFAULT = 0
    SUBPIXEL_ORDER_RGB = 1
    SUBPIXEL_ORDER_BGR = 2
    SUBPIXEL_ORDER_VRGB = 3
    SUBPIXEL_ORDER_VBGR = 4

    # cairo_hint_style_t codes
    HINT_STYLE_DEFAULT = 0
    HINT_STYLE_NONE = 1
    HINT_STYLE_SLIGHT = 2
    HINT_STYLE_MEDIUM = 3
    HINT_STYLE_FULL = 4

    # cairo_hint_metrics_t codes
    HINT_METRICS_DEFAULT = 0
    HINT_METRICS_OFF = 1
    HINT_METRICS_ON = 2

    # cairo_fill_rule_t codes
    FILL_RULE_WINDING = 0
    FILL_RULE_EVEN_ODD = 1

    # cairo_line_cap_t codes
    LINE_CAP_BUTT = 0
    LINE_CAP_ROUND = 1
    LINE_CAP_SQUARE = 2

    # cairo_line_join_t codes
    LINE_JOIN_MITER = 0
    LINE_JOIN_MITRE = 0
    LINE_JOIN_ROUND = 1
    LINE_JOIN_BEVEL = 2

    # cairo_path_data_type_t codes
    PATH_MOVE_TO = 0
    PATH_LINE_TO = 1
    PATH_CURVE_TO = 2
    PATH_CLOSE_PATH = 3
    path_data_type_t = ct.c_uint

    class path_data_t(ct.Union) :

        class header_t(ct.Structure) :
            "followed by header_t.length point_t structs."
            _fields_ = \
                [
                    ("type", ct.c_uint), # path_data_type_t
                    ("length", ct.c_int), # number of following points
                ]
        #end header_t
        header_ptr_t = ct.POINTER(header_t)

        class point_t(ct.Structure) :
            _fields_ = \
                [
                    ("x", ct.c_double),
                    ("y", ct.c_double),
                ]
        #end point_t
        point_ptr_t = ct.POINTER(point_t)

        _fields_ = \
            [
                ("header", header_t),
                ("point" , point_t),
            ]

    #end path_data_t
    path_data_t_ptr = ct.POINTER(path_data_t)

    class path_t(ct.Structure) :
        pass
    path_t._fields_ = \
        [
            ("status", status_t),
            ("data", ct.c_void_p), # path_data_t_ptr
            ("num_data", ct.c_int), # number of elements in data
        ]
    #end path_t
    path_ptr_t = ct.POINTER(path_t)

    class rectangle_t(ct.Structure) :
        _fields_ = \
            [
                ("x", ct.c_double),
                ("y", ct.c_double),
                ("width", ct.c_double),
                ("height", ct.c_double),
            ]
    #end rectangle_t
    rectangle_ptr_t = ct.POINTER(rectangle_t)

    class rectangle_list_t(ct.Structure) :
        pass
    rectangle_list_t._fields_ = \
        [
            ("status", status_t),
            ("rectangles", rectangle_ptr_t),
            ("num_rectangles", ct.c_int),
        ]
    #end rectangle_list_t
    rectangle_list_ptr_t = ct.POINTER(rectangle_list_t)

    class rectangle_int_t(ct.Structure) :
        _fields_ = \
            [
                ("x", ct.c_int),
                ("y", ct.c_int),
                ("width", ct.c_int),
                ("height", ct.c_int),
            ]
    #end rectangle_int_t
    rectangle_int_ptr_t = ct.POINTER(rectangle_int_t)

    # codes for cairo_region_overlap_t
    REGION_OVERLAP_IN = 0
    REGION_OVERLAP_OUT = 1
    REGION_OVERLAP_PART = 2

    # since 1.16, for tag_begin/end
    TAG_DEST = "cairo.dest"
    TAG_LINK = "Link"

    class glyph_t(ct.Structure) :
        _fields_ = \
            [
                ("index", ct.c_ulong), # glyph index
                ("x", ct.c_double), # position relative to origin
                ("y", ct.c_double),
            ]
    #end glyph_t
    glyph_ptr_t = ct.POINTER(glyph_t)

    class cluster_t(ct.Structure) :
        _fields_ = \
            [
                ("num_bytes", ct.c_int),
                ("num_glyphs", ct.c_int),
            ]
    #end cluster_t
    cluster_ptr_t = ct.POINTER(cluster_t)

    # cairo_text_cluster_flags_t codes
    TEXT_CLUSTER_FLAG_BACKWARD = 0x00000001

    # cairo_font_type_t codes
    FONT_TYPE_TOY = 0
    FONT_TYPE_FT = 1
    FONT_TYPE_WIN32 = 2
    FONT_TYPE_QUARTZ = 3
    FONT_TYPE_USER = 4

    destroy_func_t = ct.CFUNCTYPE(None, ct.c_void_p)

    class font_extents_t(ct.Structure) :
        _fields_ = \
            [
                ("ascent", ct.c_double),
                ("descent", ct.c_double),
                ("height", ct.c_double),
                ("max_x_advance", ct.c_double),
                ("max_y_advance", ct.c_double),
            ]
    #end font_extents_t
    font_extents_ptr_t = ct.POINTER(font_extents_t)

    class text_extents_t(ct.Structure) :
        _fields_ = \
            [
                ("x_bearing", ct.c_double),
                ("y_bearing", ct.c_double),
                ("width", ct.c_double),
                ("height", ct.c_double),
                ("x_advance", ct.c_double),
                ("y_advance", ct.c_double),
            ]
    #end text_extents_t
    text_extents_ptr_t = ct.POINTER(text_extents_t)

    user_scaled_font_init_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_void_p, font_extents_ptr_t)
    user_scaled_font_render_glyph_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_ulong, ct.c_void_p, text_extents_ptr_t)
    user_scaled_font_text_to_glyphs_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, c_ubyte_p, ct.c_int, c_ptr_p, c_int_p, c_ptr_p, c_int_p, c_uint_p)
    user_scaled_font_unicode_to_glyph_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_ulong, c_ulong_p)

    # codes for cairo_font_slant_t
    FONT_SLANT_NORMAL = 0
    FONT_SLANT_ITALIC = 1
    FONT_SLANT_OBLIQUE = 2

    # codes for cairo_font_weight_t
    FONT_WEIGHT_NORMAL = 0
    FONT_WEIGHT_BOLD = 1

    # bit masks for cairo_ft_synthesize_t
    FT_SYNTHESIZE_BOLD = 1 << 0
    FT_SYNTHESIZE_OBLIQUE = 1 << 1

    read_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_uint)
    write_func_t = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_uint)

    cairo_pdf_version_t = ct.c_uint
    # codes for cairo_pdf_version_t
    PDF_VERSION_1_4 = 0
    PDF_VERSION_1_5 = 1

    pdf_outline_flags_t = ct.c_uint # since 1.16
    # flags for pdf_outline_flags_t
    PDF_OUTLINE_FLAG_OPEN = 0x1
    PDF_OUTLINE_FLAG_BOLD = 0x2
    PDF_OUTLINE_FLAG_ITALIC = 0x4

    PDF_OUTLINE_ROOT = 0

    pdf_metadata_t = ct.c_uint # since 1.16
    PDF_METADATA_TITLE = 0
    PDF_METADATA_AUTHOR = 1
    PDF_METADATA_SUBJECT = 2
    PDF_METADATA_KEYWORDS = 3
    PDF_METADATA_CREATOR = 4
    PDF_METADATA_CREATE_DATE = 5
    PDF_METADATA_MOD_DATE = 6

    # cairo_ps_level_t
    PS_LEVEL_2 = 0
    PS_LEVEL_3 = 1

    # codes for cairo_svg_version_t
    SVG_VERSION_1_1 = 0
    SVG_VERSION_1_2 = 1

    svg_unit_t = ct.c_uint # since 1.16
    # values for svg_unit_t
    SVG_UNIT_USER = 0
    SVG_UNIT_EM = 1
    SVG_UNIT_EX = 2
    SVG_UNIT_PX = 3
    SVG_UNIT_IN = 4
    SVG_UNIT_CM = 5
    SVG_UNIT_MM = 6
    SVG_UNIT_PT = 7
    SVG_UNIT_PC = 8
    SVG_UNIT_PERCENT = 9

    # codes for cairo_device_type_t
    DEVICE_TYPE_DRM = 0
    DEVICE_TYPE_GL = 1
    DEVICE_TYPE_SCRIPT = 2
    DEVICE_TYPE_XCB = 3
    DEVICE_TYPE_XLIB = 4
    DEVICE_TYPE_XML = 5
    DEVICE_TYPE_COGL = 6
    DEVICE_TYPE_WIN32 = 7
    DEVICE_TYPE_INVALID = -1

    # codes for cairo_script_mode_t
    SCRIPT_MODE_ASCII = 0
    SCRIPT_MODE_BINARY = 1

#end CAIRO

class XCB :
    "minimal needed XCB-related definitions."

    # from xproto.h:

    window_t = ct.c_uint
    pixmap_t = ct.c_uint
    visualid_t = ct.c_uint
    drawable_t = ct.c_uint
    colormap_t = ct.c_uint

    visual_class_t = ct.c_uint
    # values for visual_class_t:
    VISUAL_CLASS_STATIC_GRAY = 0
    VISUAL_CLASS_GRAY_SCALE = 1
    VISUAL_CLASS_STATIC_COLOR = 2
    VISUAL_CLASS_PSEUDO_COLOR = 3
    VISUAL_CLASS_TRUE_COLOR = 4
    VISUAL_CLASS_DIRECT_COLOR = 5

    class visualtype_t(ct.Structure) :
        pass
    visualtype_t._fields_ = \
        [
            ("visual_id", visualid_t),
            ("_class", ct.c_ubyte),
            ("bits_per_rgb_value", ct.c_ubyte),
            ("colormap_entries", ct.c_ushort),
            ("red_mask", ct.c_uint),
            ("green_mask", ct.c_uint),
            ("blue_mask", ct.c_uint),
            ("pad0", ct.c_ubyte * 4),
        ]
    #end visualtype_t
    visualtype_ptr_t = ct.POINTER(visualtype_t)

    class screen_t(ct.Structure) :
        pass
    screen_t._fields_ = \
        [
            ("root", window_t),
            ("default_colormap", colormap_t),
            ("white_pixel", ct.c_uint),
            ("black_pixel", ct.c_uint),
            ("current_input_masks", ct.c_uint),
            ("width_in_pixels", ct.c_ushort),
            ("height_in_pixels", ct.c_ushort),
            ("width_in_millimeters", ct.c_ushort),
            ("height_in_millimeters", ct.c_ushort),
            ("min_installed_maps", ct.c_ushort),
            ("max_installed_maps", ct.c_ushort),
            ("root_visual", visualid_t),
            ("backing_stores", ct.c_ubyte),
            ("save_unders", ct.c_ubyte),
            ("root_depth", ct.c_ubyte),
            ("allowed_depths_len", ct.c_ubyte),
        ]
    #end screen_t
    screen_ptr_t = ct.POINTER(screen_t)

    # from xrender.h:

    render_pictformat_t = ct.c_uint

    class render_directformat_t(ct.Structure) :
        _fields_ = \
            [
                ("red_shift", ct.c_short),
                ("red_mask", ct.c_short),
                ("green_shift", ct.c_short),
                ("green_mask", ct.c_short),
                ("blue_shift", ct.c_short),
                ("blue_mask", ct.c_short),
                ("alpha_shift", ct.c_short),
                ("alpha_mask", ct.c_short),
            ]
    #end render_directformat_t

    # values for render_pictforminfo_t.type
    RENDER_PICT_TYPE_INDEXED = 0
    RENDER_PICT_TYPE_DIRECT = 1

    class render_pictforminfo_t(ct.Structure) :
        pass
    render_pictforminfo_t._fields_ = \
        [
            ("id", render_pictformat_t),
            ("type", ct.c_ubyte),
            ("depth", ct.c_ubyte),
            ("pad0", ct.c_ubyte * 2),
            ("direct", render_directformat_t),
            ("colormap", colormap_t),
        ]
    #end render_pictforminfo_t
    render_pictforminfo_ptr_t = ct.POINTER(render_pictforminfo_t)

#end XCB

class XLIB :
    "minimal needed Xlib-related definitions."

    XID = ct.c_uint
    Colormap = XID
    Drawable = XID
    PictFormat = XID

    # values for PictFormat
    PictFormatID = (1 << 0)
    PictFormatType = (1 << 1)
    PictFormatDepth = (1 << 2)
    PictFormatRed = (1 << 3)
    PictFormatRedMask = (1 << 4)
    PictFormatGreen = (1 << 5)
    PictFormatGreenMask = (1 << 6)
    PictFormatBlue = (1 << 7)
    PictFormatBlueMask = (1 << 8)
    PictFormatAlpha = (1 << 9)
    PictFormatAlphaMask = (1 << 10)
    PictFormatColormap = (1 << 11)

    class XRenderDirectFormat(ct.Structure) :
        _fields_ = \
            [
                ("red", ct.c_ushort),
                ("redMask", ct.c_ushort),
                ("green", ct.c_ushort),
                ("greenMask", ct.c_ushort),
                ("blue", ct.c_ushort),
                ("blueMask", ct.c_ushort),
                ("alpha", ct.c_ushort),
                ("alphaMask", ct.c_ushort),
            ]
    #end XRenderDirectFormat

    class XRenderPictFormat(ct.Structure) :
        pass
    #end XRenderPictFormat
    XRenderPictFormat._fields_ = \
        [
            ("id", PictFormat),
            ("type", ct.c_int),
            ("depth", ct.c_int),
            ("direct", XRenderDirectFormat),
            ("colormap", Colormap),
        ]

#end XLIB

class HAS :
    "functionality queries. These are implemented by checking for the presence" \
    " of particular library functions."
    ISCLOSE = hasattr(math, "isclose") # introduced in Python 3.5
    # rest filled in below
#end HAS
for \
    symname, funcname \
in \
    (
        ("FT_FONT", "ft_font_face_create_for_ft_face"),
        ("FC_FONT", "ft_font_face_create_for_pattern"),
        ("IMAGE_SURFACE", "image_surface_create"),
        # TODO: MIME_SURFACE, OBSERVER_SURFACE?
        ("PDF_SURFACE", "pdf_surface_create"),
        ("PNG_FUNCTIONS", "surface_write_to_png"),
        ("PS_SURFACE", "ps_surface_create"),
        ("RECORDING_SURFACE", "recording_surface_create"),
        ("SCRIPT_SURFACE", "script_create"),
        ("SVG_SURFACE", "svg_surface_create"),
        ("USER_FONT", "user_font_face_create"),
        ("XCB_SURFACE", "xcb_surface_create"),
        ("XCB_SHM_FUNCTIONS", "xcb_device_debug_cap_xshm_version"),
        ("XLIB_SURFACE", "xlib_surface_create"),
        ("XLIB_XRENDER", "xlib_surface_create_with_xrender_format"),
    ) \
:
    setattr \
      (
        HAS,
        symname,
        hasattr(cairo, "cairo_" + funcname)
      )
#end for
del symname, funcname

if HAS.ISCLOSE :
    # copy same defaults as math.isclose
    default_rel_tol = 1.0e-9
    default_abs_tol = 0
#end if

def def_struct_class(name, ctname, extra = None) :
    # defines a class with attributes that are a straightforward mapping
    # of a ctypes struct. Optionally includes extra members from extra
    # if specified.

    ctstruct = getattr(CAIRO, ctname)

    class result_class :

        __slots__ = tuple(field[0] for field in ctstruct._fields_) # to forestall typos

        def to_cairo(self) :
            "returns a Cairo representation of the structure."
            result = ctstruct()
            for name, cttype in ctstruct._fields_ :
                setattr(result, name, getattr(self, name))
            #end for
            return \
                result
        #end to_cairo

        @classmethod
        def from_cairo(celf, r) :
            "decodes the Cairo representation of the structure."
            result = celf()
            for name, cttype in ctstruct._fields_ :
                setattr(result, name, getattr(r, name))
            #end for
            return \
                result
        #end from_cairo

        def __getitem__(self, i) :
            "allows the object to be coerced to a tuple."
            return \
                getattr(self, ctstruct._fields_[i][0])
        #end __getitem__

        def __repr__(self) :
            return \
                (
                    "%s(%s)"
                %
                    (
                        name,
                        ", ".join
                          (
                            "%s = %s" % (field[0], getattr(self, field[0]))
                            for field in ctstruct._fields_
                          ),
                    )
                )
        #end __repr__

    #end result_class

#begin def_struct_class
    result_class.__name__ = name
    result_class.__doc__ = \
        (
            "representation of a Cairo %s structure. Fields are %s."
            "\nCreate by decoding the Cairo form with the from_cairo method;"
            " convert an instance to Cairo form with the to_cairo method."
        %
            (
                ctname,
                ", ".join(f[0] for f in ctstruct._fields_),
            )
        )
    if extra != None :
        for attr in dir(extra) :
            if not attr.startswith("__") :
                setattr(result_class, attr, getattr(extra, attr))
            #end if
        #end for
    #end if
    return \
        result_class
#end def_struct_class

#+
# Routine arg/result types
#-

cairo.cairo_version_string.restype = ct.c_char_p
cairo.cairo_status_to_string.restype = ct.c_char_p

cairo.cairo_status.argtypes = (ct.c_void_p,)
cairo.cairo_create.argtypes = (ct.c_void_p,)
cairo.cairo_create.restype = ct.c_void_p
cairo.cairo_reference.restype = ct.c_void_p
cairo.cairo_reference.argtypes = (ct.c_void_p,)
cairo.cairo_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_destroy.restype = ct.c_void_p
cairo.cairo_save.argtypes = (ct.c_void_p,)
cairo.cairo_save.restype = ct.c_void_p
cairo.cairo_restore.argtypes = (ct.c_void_p,)
cairo.cairo_restore.restype = ct.c_void_p
cairo.cairo_get_target.restype = ct.c_void_p
cairo.cairo_get_target.argtypes = (ct.c_void_p,)
cairo.cairo_push_group.argtypes = (ct.c_void_p,)
cairo.cairo_push_group_with_content.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_pop_group.restype = ct.c_void_p
cairo.cairo_pop_group.argtypes = (ct.c_void_p,)
cairo.cairo_pop_group_to_source.argtypes = (ct.c_void_p,)
cairo.cairo_get_group_target.restype = ct.c_void_p
cairo.cairo_get_group_target.argtypes = (ct.c_void_p,)

cairo.cairo_copy_path.argtypes = (ct.c_void_p,)
cairo.cairo_copy_path.restype = ct.c_void_p
cairo.cairo_copy_path_flat.argtypes = (ct.c_void_p,)
cairo.cairo_copy_path_flat.restype = ct.c_void_p
cairo.cairo_append_path.argtypes = (ct.c_void_p, ct.c_void_p) # not used
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

cairo.cairo_get_source.argtypes = (ct.c_void_p,)
cairo.cairo_get_source.restype = ct.c_void_p
cairo.cairo_set_source_rgb.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double) # not used
cairo.cairo_set_source_rgba.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_set_source.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_set_source_surface.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_double, ct.c_double)
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
cairo.cairo_get_tolerance.argtypes = (ct.c_void_p,)
cairo.cairo_get_tolerance.restype = ct.c_double
cairo.cairo_set_tolerance.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_clip.argtypes = (ct.c_void_p,)
cairo.cairo_clip_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_clip_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_in_clip.restype = ct.c_bool
cairo.cairo_in_clip.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_copy_clip_rectangle_list.restype = CAIRO.rectangle_list_ptr_t
cairo.cairo_copy_clip_rectangle_list.argtypes = (ct.c_void_p,)
cairo.cairo_rectangle_list_destroy.argtypes = (CAIRO.rectangle_list_ptr_t,)
if hasattr(cairo, "cairo_tag_begin") : # since 1.16
    cairo.cairo_tag_begin.restype = None
    cairo.cairo_tag_begin.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_char_p)
    cairo.cairo_tag_end.restype = None
    cairo.cairo_tag_end.argtypes = (ct.c_void_p, ct.c_char_p)
#end if
cairo.cairo_reset_clip.argtypes = (ct.c_void_p,)
cairo.cairo_fill.argtypes = (ct.c_void_p,)
cairo.cairo_fill_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_fill_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_in_fill.restype = ct.c_bool
cairo.cairo_in_fill.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_mask.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_mask_surface.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_paint.argtypes = (ct.c_void_p,)
cairo.cairo_paint_with_alpha.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_stroke.argtypes = (ct.c_void_p,)
cairo.cairo_stroke_preserve.argtypes = (ct.c_void_p,)
cairo.cairo_stroke_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_in_stroke.restype = ct.c_bool
cairo.cairo_in_stroke.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_copy_page.argtypes = (ct.c_void_p,)
cairo.cairo_show_page.argtypes = (ct.c_void_p,)
cairo.cairo_get_reference_count.restype = ct.c_uint
cairo.cairo_get_reference_count.argtypes = (ct.c_void_p,)

cairo.cairo_path_destroy.argtypes = (ct.c_void_p,)

cairo.cairo_select_font_face.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_int, ct.c_int)
cairo.cairo_set_font_size.argtypes = (ct.c_void_p, ct.c_double)
cairo.cairo_set_font_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_font_matrix.argtypes = (ct.c_void_p,)
cairo.cairo_get_font_matrix.restype = ct.c_void_p
cairo.cairo_set_font_options.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_font_options.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_set_font_face.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_font_face.restype = ct.c_void_p
cairo.cairo_get_font_face.argtypes = (ct.c_void_p,)
cairo.cairo_font_face_get_reference_count.restype = ct.c_uint
cairo.cairo_font_face_get_reference_count.argtypes = (ct.c_void_p,)
cairo.cairo_set_scaled_font.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_get_scaled_font.restype = ct.c_void_p
cairo.cairo_get_scaled_font.argtypes = (ct.c_void_p,)
cairo.cairo_scaled_font_get_reference_count.restype = ct.c_uint
cairo.cairo_scaled_font_get_reference_count.argtypes = (ct.c_void_p,)

cairo.cairo_user_font_face_create.restype = ct.c_void_p
cairo.cairo_user_font_face_set_init_func.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_user_font_face_get_init_func.restype = ct.c_void_p
cairo.cairo_user_font_face_get_init_func.argtypes = (ct.c_void_p,)
cairo.cairo_user_font_face_set_render_glyph_func.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_user_font_face_get_render_glyph_func.restype = ct.c_void_p
cairo.cairo_user_font_face_get_render_glyph_func.argtypes = (ct.c_void_p,)
cairo.cairo_user_font_face_set_unicode_to_glyph_func.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_user_font_face_get_unicode_to_glyph_func.restype = ct.c_void_p
cairo.cairo_user_font_face_get_unicode_to_glyph_func.argtypes = (ct.c_void_p,)
cairo.cairo_user_font_face_set_text_to_glyphs_func.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_user_font_face_get_text_to_glyphs_func.restype = ct.c_void_p
cairo.cairo_user_font_face_get_text_to_glyphs_func.argtypes = (ct.c_void_p,)

cairo.cairo_show_text.argtypes = (ct.c_void_p, ct.c_char_p)
cairo.cairo_show_glyphs.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_show_text_glyphs.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_void_p, ct.c_int, ct.c_void_p, ct.c_int, ct.c_uint)
cairo.cairo_font_extents.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_text_extents.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_void_p)
cairo.cairo_glyph_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_void_p)

cairo.cairo_device_reference.restype = ct.c_void_p
cairo.cairo_device_reference.argtypes = (ct.c_void_p,)
cairo.cairo_device_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_device_get_reference_count.restype = ct.c_uint
cairo.cairo_device_get_reference_count.argtypes = (ct.c_void_p,)

cairo.cairo_surface_status.argtypes = (ct.c_void_p,)
cairo.cairo_surface_get_type.argtypes = (ct.c_void_p,)
cairo.cairo_surface_create_similar.restype = ct.c_void_p
cairo.cairo_surface_create_similar.argtypes = (ct.c_void_p, ct.c_int, ct.c_int, ct.c_int)
cairo.cairo_surface_create_similar_image.restype = ct.c_void_p
cairo.cairo_surface_create_similar_image.argtypes = (ct.c_void_p, ct.c_int, ct.c_int, ct.c_int)
cairo.cairo_surface_create_for_rectangle.restype = ct.c_void_p
cairo.cairo_surface_create_for_rectangle.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_surface_reference.restype = ct.c_void_p
cairo.cairo_surface_reference.argtypes = (ct.c_void_p,)
cairo.cairo_surface_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_surface_flush.argtypes = (ct.c_void_p,)
cairo.cairo_surface_get_device.restype = ct.c_void_p
cairo.cairo_surface_get_device.argtypes = (ct.c_void_p,)
cairo.cairo_surface_get_font_options.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_surface_get_content.restype = ct.c_int
cairo.cairo_surface_get_content.argtypes = (ct.c_void_p,)
cairo.cairo_surface_mark_dirty.argtypes = (ct.c_void_p,)
cairo.cairo_surface_mark_dirty_rectangle.argtypes = (ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.c_int)
cairo.cairo_surface_set_device_offset.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_surface_get_device_offset.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_surface_set_device_scale.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_surface_get_device_scale.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_surface_set_fallback_resolution.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_surface_get_fallback_resolution.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_surface_write_to_png.argtypes = (ct.c_void_p, ct.c_char_p)
cairo.cairo_surface_write_to_png_stream.argtypes = (ct.c_void_p, CAIRO.write_func_t, ct.c_void_p)
cairo.cairo_surface_copy_page.argtypes = (ct.c_void_p,)
cairo.cairo_surface_show_page.argtypes = (ct.c_void_p,)
cairo.cairo_surface_has_show_text_glyphs.restype = ct.c_bool
cairo.cairo_surface_has_show_text_glyphs.argtypes = (ct.c_void_p,)
cairo.cairo_surface_get_reference_count.restype = ct.c_uint
cairo.cairo_surface_get_reference_count.argtypes = (ct.c_void_p,)

cairo.cairo_format_stride_for_width.argtypes = (ct.c_int, ct.c_int)
cairo.cairo_image_surface_create.restype = ct.c_void_p
cairo.cairo_image_surface_create.argtypes = (ct.c_int, ct.c_int, ct.c_int)
cairo.cairo_image_surface_create_from_png.restype = ct.c_void_p
cairo.cairo_image_surface_create_from_png_stream.restype = ct.c_void_p
cairo.cairo_image_surface_create_from_png_stream.argtypes = (CAIRO.read_func_t, ct.c_void_p)
cairo.cairo_image_surface_create_for_data.restype = ct.c_void_p
cairo.cairo_image_surface_create_for_data.argtypes = (ct.c_void_p, ct.c_int, ct.c_int, ct.c_int, ct.c_int)
cairo.cairo_image_surface_get_data.restype = ct.c_void_p
cairo.cairo_image_surface_get_data.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_format.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_width.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_height.argtypes = (ct.c_void_p,)
cairo.cairo_image_surface_get_stride.argtypes = (ct.c_void_p,)

cairo.cairo_pdf_surface_create.restype = ct.c_void_p
cairo.cairo_pdf_surface_create.argtypes = (ct.c_char_p, ct.c_double, ct.c_double)
cairo.cairo_pdf_surface_create_for_stream.restype = ct.c_void_p
cairo.cairo_pdf_surface_create_for_stream.argtypes = (CAIRO.write_func_t, ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_pdf_surface_restrict_to_version.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_pdf_get_versions.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pdf_version_to_string.restype = ct.c_char_p
cairo.cairo_pdf_version_to_string.argtypes = (ct.c_int,)
cairo.cairo_pdf_surface_set_size.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
if hasattr(cairo, "cairo_pdf_surface_add_outline") : # since 1.16
    cairo.cairo_pdf_surface_add_outline.restype = ct.c_int
    cairo.cairo_pdf_surface_add_outline.argtypes = (ct.c_void_p, ct.c_int, ct.c_char_p, ct.c_char_p, CAIRO.pdf_outline_flags_t)
    cairo.cairo_pdf_surface_set_metadata.restype = None
    cairo.cairo_pdf_surface_set_metadata.argtypes = (ct.c_void_p, CAIRO.pdf_metadata_t, ct.c_char_p)
    cairo.cairo_pdf_surface_set_page_label.restype = None
    cairo.cairo_pdf_surface_set_page_label.argtypes = (ct.c_void_p, ct.c_char_p)
    cairo.cairo_pdf_surface_set_thumbnail_size.restype = None
    cairo.cairo_pdf_surface_set_thumbnail_size.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
#end if
cairo.cairo_ps_surface_create.restype = ct.c_void_p
cairo.cairo_ps_surface_create.argtypes = (ct.c_char_p, ct.c_double, ct.c_double)
cairo.cairo_ps_surface_create_for_stream.restype = ct.c_void_p
cairo.cairo_ps_surface_create_for_stream.argtypes = (CAIRO.write_func_t, ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_ps_surface_restrict_to_level.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_ps_get_levels.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_ps_level_to_string.restype = ct.c_char_p
cairo.cairo_ps_level_to_string.argtypes = (ct.c_int,)
cairo.cairo_ps_surface_set_eps.argtypes = (ct.c_void_p, ct.c_bool)
cairo.cairo_ps_surface_get_eps.restype = ct.c_bool
cairo.cairo_ps_surface_get_eps.argtypes = (ct.c_void_p,)
cairo.cairo_ps_surface_set_size.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_ps_surface_dsc_begin_setup.argtypes = (ct.c_void_p,)
cairo.cairo_ps_surface_dsc_begin_page_setup.argtypes = (ct.c_void_p,)
cairo.cairo_ps_surface_dsc_comment.argtypes = (ct.c_void_p, ct.c_char_p)
cairo.cairo_svg_surface_create.restype = ct.c_void_p
cairo.cairo_svg_surface_create.argtypes = (ct.c_char_p, ct.c_double, ct.c_double)
cairo.cairo_svg_surface_create_for_stream.restype = ct.c_void_p
cairo.cairo_svg_surface_create_for_stream.argtypes = (CAIRO.write_func_t, ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_svg_surface_restrict_to_version.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_svg_get_versions.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_svg_version_to_string.restype = ct.c_char_p
cairo.cairo_svg_version_to_string.argtypes = (ct.c_int,)
if hasattr(cairo, "cairo_svg_surface_set_document_unit") : # since 1.16
    cairo.cairo_svg_surface_set_document_unit.restype = None
    cairo.cairo_svg_surface_set_document_unit.argtypes = (ct.c_void_p, CAIRO.svg_unit_t)
    cairo.cairo_svg_surface_get_document_unit.restype = CAIRO.svg_unit_t
    cairo.cairo_svg_surface_get_document_unit.argtypes = (ct.c_void_p,)
#end if
cairo.cairo_recording_surface_create.restype = ct.c_void_p
cairo.cairo_recording_surface_create.argtypes = (ct.c_int, ct.c_void_p)
cairo.cairo_recording_surface_ink_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_recording_surface_get_extents.restype = ct.c_bool
cairo.cairo_recording_surface_get_extents.argtypes = (ct.c_void_p, ct.c_void_p)

cairo.cairo_device_status.argtypes = (ct.c_void_p,)
cairo.cairo_device_get_type.argtypes = (ct.c_void_p,)

cairo.cairo_script_create.restype = ct.c_void_p
cairo.cairo_script_create.argtypes = (ct.c_char_p,)
cairo.cairo_script_create_for_stream.restype = ct.c_void_p
cairo.cairo_script_create_for_stream.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_script_from_recording_surface.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_script_get_mode.restype = ct.c_int
cairo.cairo_script_get_mode.argtypes = (ct.c_void_p,)
cairo.cairo_script_set_mode.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_script_surface_create.restype = ct.c_void_p
cairo.cairo_script_surface_create.argtypes = (ct.c_void_p, ct.c_int, ct.c_double, ct.c_double)
cairo.cairo_script_surface_create_for_target.restype = ct.c_int
cairo.cairo_script_surface_create_for_target.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_script_write_comment.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int)

cairo.cairo_pattern_status.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_reference.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_reference.restype = ct.c_void_p
cairo.cairo_pattern_add_color_stop_rgb.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double) # not used
cairo.cairo_pattern_add_color_stop_rgba.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_get_color_stop_count.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_get_color_stop_rgba.argtypes = (ct.c_void_p, ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_create_rgb.argtypes = (ct.c_double, ct.c_double, ct.c_double) # not used
cairo.cairo_pattern_create_rgb.restype = ct.c_void_p # not used
cairo.cairo_pattern_create_rgba.argtypes = (ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_create_rgba.restype = ct.c_void_p
cairo.cairo_pattern_get_rgba.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_create_for_surface.restype = ct.c_void_p
cairo.cairo_pattern_create_for_surface.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_create_linear.argtypes = (ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_create_linear.restype = ct.c_void_p
cairo.cairo_pattern_get_linear_points.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_create_radial.argtypes = (ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_pattern_create_radial.restype = ct.c_void_p
cairo.cairo_pattern_get_radial_circles.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_get_extend.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_set_extend.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_pattern_get_filter.argtypes = (ct.c_void_p,)
cairo.cairo_pattern_set_filter.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_pattern_get_surface.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_get_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_set_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_pattern_create_mesh.restype = ct.c_void_p
cairo.cairo_pattern_create_mesh.argtypes = ()
cairo.cairo_pattern_get_reference_count.restype = ct.c_uint
cairo.cairo_pattern_get_reference_count.argtypes = (ct.c_void_p,)
cairo.cairo_mesh_pattern_begin_patch.argtypes = (ct.c_void_p,)
cairo.cairo_mesh_pattern_end_patch.argtypes = (ct.c_void_p,)
cairo.cairo_mesh_pattern_move_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_mesh_pattern_line_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)
cairo.cairo_mesh_pattern_curve_to.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_mesh_pattern_set_control_point.argtypes = (ct.c_void_p, ct.c_uint, ct.c_double, ct.c_double)
cairo.cairo_mesh_pattern_set_corner_color_rgb.argtypes = (ct.c_void_p, ct.c_uint, ct.c_double, ct.c_double, ct.c_double) # not used
cairo.cairo_mesh_pattern_set_corner_color_rgba.argtypes = (ct.c_void_p, ct.c_uint, ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_mesh_pattern_get_patch_count.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_mesh_pattern_get_path.restype = ct.c_void_p
cairo.cairo_mesh_pattern_get_path.argtypes = (ct.c_void_p, ct.c_uint)
cairo.cairo_mesh_pattern_get_control_point.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint, ct.c_void_p, ct.c_void_p)
cairo.cairo_mesh_pattern_get_corner_color_rgba.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)

# Cairo matrix functions are here in case you want to make direct
# calls to them. The Python Matrix class implements its own calculations,
# because this is faster than converting to/from CAIRO.matrix_t structures
# just to use the Cairo calls. But if you have a case where you can directly
# use the Cairo type without conversion, then calling the Cairo routines
# might be faster.
cairo.cairo_matrix_init.restype = None
cairo.cairo_matrix_init.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double, ct.c_double, ct.c_double, ct.c_double)
cairo.cairo_matrix_init_identity.restype = None
cairo.cairo_matrix_init_identity.argtypes = (ct.POINTER(CAIRO.matrix_t),)
cairo.cairo_matrix_init_translate.restype = None
cairo.cairo_matrix_init_translate.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double, ct.c_double)
cairo.cairo_matrix_init_scale.restype = None
cairo.cairo_matrix_init_scale.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double, ct.c_double)
cairo.cairo_matrix_init_rotate.restype = None
cairo.cairo_matrix_init_rotate.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double)
cairo.cairo_matrix_translate.restype = None
cairo.cairo_matrix_translate.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double, ct.c_double)
cairo.cairo_matrix_scale.restype = None
cairo.cairo_matrix_scale.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double, ct.c_double)
cairo.cairo_matrix_rotate.restype = None
cairo.cairo_matrix_rotate.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.c_double)
cairo.cairo_matrix_invert.restype = CAIRO.status_t
cairo.cairo_matrix_invert.argtypes = (ct.POINTER(CAIRO.matrix_t),)
cairo.cairo_matrix_multiply.restype = None
cairo.cairo_matrix_multiply.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.POINTER(CAIRO.matrix_t), ct.POINTER(CAIRO.matrix_t))
cairo.cairo_matrix_transform_distance.restype = None
cairo.cairo_matrix_transform_distance.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double))
cairo.cairo_matrix_transform_point.restype = None
cairo.cairo_matrix_transform_point.argtypes = (ct.POINTER(CAIRO.matrix_t), ct.POINTER(ct.c_double), ct.POINTER(ct.c_double))

cairo.cairo_region_status.argtypes = (ct.c_void_p,)
cairo.cairo_region_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_region_create.restype = ct.c_void_p
cairo.cairo_region_create_rectangle.restype = ct.c_void_p
cairo.cairo_region_create_rectangle.argtypes = (ct.c_void_p,)
cairo.cairo_region_create_rectangles.restype = ct.c_void_p
cairo.cairo_region_create_rectangles.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_region_copy.restype = ct.c_void_p
cairo.cairo_region_copy.argtypes = (ct.c_void_p,)
cairo.cairo_region_get_extents.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_num_rectangles.argtypes = (ct.c_void_p,)
cairo.cairo_region_get_rectangle.argtypes = (ct.c_void_p, ct.c_int, ct.c_void_p)
cairo.cairo_region_is_empty.argtypes = (ct.c_void_p,)
cairo.cairo_region_is_empty.restype = ct.c_bool
cairo.cairo_region_contains_point.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
cairo.cairo_region_contains_point.restype = ct.c_bool
cairo.cairo_region_contains_rectangle.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_contains_rectangle.restype = ct.c_int
cairo.cairo_region_equal.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_equal.restype = ct.c_bool
cairo.cairo_region_translate.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_intersect.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_intersect_rectangle.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_subtract.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_subtract_rectangle.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_union.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_union_rectangle.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_xor.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_region_xor_rectangle.argtypes = (ct.c_void_p, ct.c_void_p)
# no cairo.cairo_region_get_reference_count!

cairo.cairo_font_options_status.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_create.restype = ct.c_void_p
cairo.cairo_font_options_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_copy.restype = ct.c_void_p
cairo.cairo_font_options_copy.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_merge.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_font_options_equal.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_font_options_equal.restype = ct.c_bool
cairo.cairo_font_options_get_antialias.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_set_antialias.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_font_options_get_subpixel_order.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_set_subpixel_order.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_font_options_get_hint_style.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_set_hint_style.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_font_options_get_hint_metrics.argtypes = (ct.c_void_p,)
cairo.cairo_font_options_set_hint_metrics.argtypes = (ct.c_void_p, ct.c_int)
if hasattr(cairo, "cairo_font_options_get_variations") : # since 1.16
    cairo.cairo_font_options_get_variations.restype = ct.c_char_p
    cairo.cairo_font_options_get_variations.argtypes = (ct.c_void_p,)
    cairo.cairo_font_options_set_variations.restype = None
    cairo.cairo_font_options_set_variations.argtypes = (ct.c_void_p, ct.c_char_p)
#end if

cairo.cairo_font_face_reference.restype = ct.c_void_p
cairo.cairo_font_face_reference.argtypes = (ct.c_void_p,)
cairo.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_font_face_status.argtypes = (ct.c_void_p,)
cairo.cairo_font_face_get_type.argtypes = (ct.c_void_p,)
cairo.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_font_face_get_user_data.restype = ct.c_void_p
cairo.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_toy_font_face_create.argtypes = (ct.c_char_p, ct.c_int, ct.c_int)
cairo.cairo_toy_font_face_create.restype = ct.c_void_p
cairo.cairo_toy_font_face_get_family.argtypes = (ct.c_void_p,)
cairo.cairo_toy_font_face_get_family.restype = ct.c_char_p
cairo.cairo_toy_font_face_get_slant.argtypes = (ct.c_void_p,)
cairo.cairo_toy_font_face_get_weight.argtypes = (ct.c_void_p,)
cairo.cairo_ft_font_face_create_for_ft_face.argtypes = (ct.c_void_p, ct.c_int)
cairo.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
cairo.cairo_ft_font_face_create_for_pattern.argtypes = (ct.c_void_p,)
cairo.cairo_ft_font_face_create_for_pattern.restype = ct.c_void_p
cairo.cairo_ft_font_options_substitute.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_ft_font_face_get_synthesize.restype = ct.c_uint
cairo.cairo_ft_font_face_get_synthesize.argtypes = (ct.c_void_p,)
cairo.cairo_ft_font_face_set_synthesize.argtypes = (ct.c_void_p, ct.c_uint)
cairo.cairo_ft_font_face_unset_synthesize.argtypes = (ct.c_void_p, ct.c_uint)
cairo.cairo_ft_scaled_font_lock_face.restype = ct.c_void_p
cairo.cairo_ft_scaled_font_lock_face.argtypes = (ct.c_void_p,)
cairo.cairo_ft_scaled_font_unlock_face.restype = None
cairo.cairo_ft_scaled_font_unlock_face.argtypes = (ct.c_void_p,)

cairo.cairo_glyph_allocate.restype = ct.c_void_p
cairo.cairo_glyph_free.argtypes = (ct.c_void_p,)
cairo.cairo_text_cluster_allocate.restype = ct.c_void_p
cairo.cairo_text_cluster_free.argtypes = (ct.c_void_p,)

cairo.cairo_scaled_font_reference.restype = ct.c_void_p
cairo.cairo_scaled_font_reference.argtypes = (ct.c_void_p,)
cairo.cairo_scaled_font_destroy.argtypes = (ct.c_void_p,)
cairo.cairo_scaled_font_status.argtypes = (ct.c_void_p,)
cairo.cairo_scaled_font_create.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_create.restype = ct.c_void_p
cairo.cairo_scaled_font_extents.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_text_extents.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_void_p)
cairo.cairo_scaled_font_glyph_extents.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_void_p)
cairo.cairo_scaled_font_text_to_glyphs.argtypes = (ct.c_void_p, ct.c_double, ct.c_double, ct.c_void_p, ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_get_font_face.restype = ct.c_void_p
cairo.cairo_scaled_font_get_font_face.argtypes = (ct.c_void_p,)
cairo.cairo_scaled_font_get_font_options.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_get_font_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_get_ctm.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_get_scale_matrix.argtypes = (ct.c_void_p, ct.c_void_p)
cairo.cairo_scaled_font_get_type.argtypes = (ct.c_void_p,)

if HAS.XCB_SURFACE :

    cairo.cairo_xcb_surface_create.restype = ct.c_void_p
    cairo.cairo_xcb_surface_create.argtypes = (ct.c_void_p, XCB.drawable_t, XCB.visualtype_ptr_t, ct.c_int, ct.c_int)
    cairo.cairo_xcb_surface_create_for_bitmap.restype = ct.c_void_p
    cairo.cairo_xcb_surface_create_for_bitmap.argtypes = (ct.c_void_p, XCB.screen_ptr_t, XCB.pixmap_t, ct.c_int, ct.c_int)
    cairo.cairo_xcb_surface_create_with_xrender_format.restype = ct.c_void_p
    cairo.cairo_xcb_surface_create_with_xrender_format.argtypes = (ct.c_void_p, XCB.screen_ptr_t, ct.c_uint, XCB.render_pictforminfo_ptr_t, ct.c_int, ct.c_int)
    cairo.cairo_xcb_surface_set_size.restype = None
    cairo.cairo_xcb_surface_set_size.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
    cairo.cairo_xcb_surface_set_drawable.restype = None
    cairo.cairo_xcb_surface_set_drawable.argtypes = (ct.c_void_p, ct.c_uint, ct.c_int, ct.c_int)
    cairo.cairo_xcb_device_get_connection.restype = ct.c_void_p
    cairo.cairo_xcb_device_get_connection.argtypes = (ct.c_void_p,)

    if HAS.XCB_SHM_FUNCTIONS :
        cairo.cairo_xcb_device_debug_cap_xshm_version.restype = None
        cairo.cairo_xcb_device_debug_cap_xshm_version.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
    #end if

    cairo.cairo_xcb_device_debug_cap_xrender_version.restype = None
    cairo.cairo_xcb_device_debug_cap_xrender_version.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)

    cairo.cairo_xcb_device_debug_set_precision.restype = None
    cairo.cairo_xcb_device_debug_set_precision.argtypes = (ct.c_void_p, ct.c_int)
    cairo.cairo_xcb_device_debug_get_precision.restype = ct.c_int
    cairo.cairo_xcb_device_debug_get_precision.argtypes = (ct.c_void_p,)

#end if

if HAS.XLIB_SURFACE :

    cairo.cairo_xlib_surface_create.restype = ct.c_void_p
    cairo.cairo_xlib_surface_create.argtypes = (ct.c_void_p, XLIB.Drawable, ct.c_void_p, ct.c_int, ct.c_int)
    cairo.cairo_xlib_surface_create_for_bitmap.restype = ct.c_void_p
    cairo.cairo_xlib_surface_create_for_bitmap.argtypes = (ct.c_void_p, XLIB.Drawable, ct.c_void_p, ct.c_int, ct.c_int)
    cairo.cairo_xlib_surface_set_size.restype = None
    cairo.cairo_xlib_surface_set_size.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
    cairo.cairo_xlib_surface_set_drawable.restype = None
    cairo.cairo_xlib_surface_set_drawable.argtypes = (ct.c_void_p, XLIB.Drawable, ct.c_int, ct.c_int)
    cairo.cairo_xlib_surface_get_display.restype = ct.c_void_p
    cairo.cairo_xlib_surface_get_display.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_drawable.restype = ct.c_void_p
    cairo.cairo_xlib_surface_get_drawable.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_screen.restype = ct.c_void_p
    cairo.cairo_xlib_surface_get_screen.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_visual.restype = ct.c_void_p
    cairo.cairo_xlib_surface_get_visual.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_depth.restype = ct.c_int
    cairo.cairo_xlib_surface_get_depth.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_width.restype = ct.c_int
    cairo.cairo_xlib_surface_get_width.argtypes = (ct.c_void_p,)
    cairo.cairo_xlib_surface_get_height.restype = ct.c_int
    cairo.cairo_xlib_surface_get_height.argtypes = (ct.c_void_p,)

    cairo.cairo_xlib_device_debug_cap_xrender_version.restype = None
    cairo.cairo_xlib_device_debug_cap_xrender_version.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
    cairo.cairo_xlib_device_debug_set_precision.restype = None
    cairo.cairo_xlib_device_debug_set_precision.argtypes = (ct.c_void_p, ct.c_int)
    cairo.cairo_xlib_device_debug_get_precision.restype = ct.c_int
    cairo.cairo_xlib_device_debug_get_precision.argtypes = (ct.c_void_p,)

    if HAS.XLIB_XRENDER :

        cairo.cairo_xlib_surface_create_with_xrender_format.restype = ct.c_void_p
        cairo.cairo_xlib_surface_create_with_xrender_format.argtypes = (ct.c_void_p, XLIB.Drawable, ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_int)
        cairo.cairo_xlib_surface_get_xrender_format.restype = ct.c_void_p
        cairo.cairo_xlib_surface_get_xrender_format.argtypes = (ct.c_void_p,)

    #end if

#end if

_ft_destroy_key = ct.c_int() # dummy address

if freetype2 != None :

    def _ensure_ft() :
        pass
    #end _ensure_ft

    def get_ft_lib() :
        "returns the freetype2.Library object that I use."
        return \
            freetype2.get_default_lib()
    #end get_ft_lib

else :
    # fallback to my own minimal wrapper for FreeType

    _ft_lib = None

    def _ensure_ft() :
        # ensures FreeType is usable, raising suitable exceptions if not.
        global _ft_lib
        if _ft_lib == None :
            lib = ct.c_void_p()
            status = _ft.FT_Init_FreeType(ct.byref(lib))
            if status != 0 :
                raise RuntimeError("Error %d initializing FreeType" % status)
            #end if
            _ft_lib = lib.value
        #end if
    #end _ensure_ft

    def get_ft_lib() :
        "not available without python_freetype."
        raise NotImplementedError("not available without freetype2.")
    #end get_ft_lib

#end if freetype2 != None

if fontconfig == None :

    if _fc != None :
        _fc.FcInit.restype = ct.c_bool
        _fc.FcNameParse.argtypes = (ct.c_char_p,)
        _fc.FcNameParse.restype = ct.c_void_p
        _fc.FcConfigSubstitute.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int)
        _fc.FcConfigSubstitute.restype = ct.c_bool
        _fc.FcDefaultSubstitute.argtypes = (ct.c_void_p,)
        _fc.FcDefaultSubstitute.restype = None
        _fc.FcFontMatch.restype = ct.c_void_p
        _fc.FcFontMatch.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
        _fc.FcPatternDestroy.argtypes = (ct.c_void_p,)
        _fc.FcPatternDestroy.restype = None

        class _FC :
            # minimal Fontconfig interface, just sufficient for my needs.

            FcMatchPattern = 0
            FcResultMatch = 0

        #end _FC

        class _FcPatternManager :
            # context manager which collects a list of FcPattern objects requiring disposal.

            def __init__(self) :
                self.to_dispose = []
            #end __init__

            def __enter__(self) :
                return \
                    self
            #end __enter__

            def collect(self, pattern) :
                "collects another FcPattern reference to be disposed."
                # c_void_p function results are peculiar: they return integers
                # for non-null values, but None for null.
                if pattern != None :
                    self.to_dispose.append(pattern)
                #end if
                return \
                    pattern
            #end collect

            def __exit__(self, exception_type, exception_value, traceback) :
                for pattern in self.to_dispose :
                    _fc.FcPatternDestroy(pattern)
                #end for
            #end __exit__

        #end _FcPatternManager

    #end if _fc != None

    _fc_inited = False

    def _ensure_fc() :
        # ensures Fontconfig is usable, raising suitable exceptions if not.
        global _fc_inited
        if not _fc_inited :
            if _fc == None :
                raise NotImplementedError("Fontconfig not available")
            #end if
            if not _fc.FcInit() :
                raise RuntimeError("failed to initialize Fontconfig.")
            #end if
            _fc_inited = True
        #end if
    #end _ensure_fc

#end if fontconfig == None

#+
# Higher-level stuff begins here
#-

def version() :
    "returns the Cairo version as a single integer."
    return \
        cairo.cairo_version()
#end version

def version_tuple() :
    "returns the Cairo version as a triple of integers."
    vers = cairo.cairo_version()
    return \
        (vers // 10000, vers // 100 % 100, vers % 100)
#end version_tuple

def version_string() :
    "returns the Cairo version string."
    return \
        cairo.cairo_version_string().decode("utf-8")
#end version_string

def status_to_string(status) :
    "returns the message for a given Cairo status code."
    return \
        cairo.cairo_status_to_string(status).decode("utf-8")
#end status_to_string

def debug_reset_static_data() :
    cairo.cairo_debug_reset_static_data()
#end debug_reset_static_data

def check(status) :
    "checks status for success, raising a CairoError if not."
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

deg = math.pi / 180
  # All angles are in radians. You can use the standard Python functions math.degrees
  # and math.radians to convert back and forth, or multiply and divide by this deg
  # factor: multiply by deg to convert degrees to radians, and divide by deg to convert
  # the other way, e.g.
  #
  #     math.sin(45 * deg)
  #     math.atan(1) / deg
circle = 2 * math.pi
  # Alternatively, you can work in units of full circles. E.g.
  # 0.25 * circle is equivalent to 90°

base_dpi = 72 # for scaling things to different relative resolutions

def int_fits_bits(val, bits) :
    "is val a signed integer that fits within the specified number of bits."
    limit = (1 << bits - 1) - 1
    return \
        (
            isinstance(val, int)
        and
            - limit <= val <= limit
              # yes, I ignore the extra negative value in 2s-complement
        )
#end int_fits_bits

class Vector :
    "something missing from Cairo itself, a representation of a 2D point."

    __slots__ = ("x", "y") # to forestall typos

    def __init__(self, x, y) :
        self.x = x
        self.y = y
    #end __init__

    @classmethod
    def from_tuple(celf, v) :
        "converts a tuple of 2 numbers to a Vector. Can be used to ensure that" \
        " v is a Vector."
        if not isinstance(v, celf) :
            v = celf(*v)
        #end if
        return \
            v
    #end from_tuple

    @classmethod
    def from_complex(celf, x) :
        return \
            celf(x.real, x.imag)
    #end from_complex

    def to_complex(self) :
        return \
            complex(self.x, self.y)
    #end to_complex

    def isint(self) :
        "are the components signed 32-bit integers."
        return \
            int_fits_bits(self.x, 32) and int_fits_bits(self.y, 32)
    #end isint

    def assert_isint(self) :
        "checks that the components are signed 32-bit integers."
        if not self.isint() :
            raise ValueError("components must be signed 32-bit integers")
        #end if
        return \
            self
    #end assert_isint

    def __repr__(self) :
        return \
            (
                "%%s(%%%(fmt)s, %%%(fmt)s)"
            %
                {"fmt" : ("g", "d")[self.isint()]}
            %
                (type(self).__name__, self.x, self.y)
            )
    #end __repr__

    def __getitem__(self, i) :
        "being able to access elements by index allows a Vector to be cast to a tuple or list."
        return \
            (self.x, self.y)[i]
    #end __getitem__

    def __eq__(v1, v2) :
        "equality of two Vectors."
        return \
            (
                isinstance(v2, Vector)
            and
                v1.x == v2.x
            and
                v1.y == v2.y
            )
    #end __eq__

    if HAS.ISCLOSE :

        def iscloseto(v1, v2, rel_tol = default_rel_tol, abs_tol = default_abs_tol) :
            "approximate equality of two Vectors to within the specified tolerances."
            return \
                (
                    math.isclose(v1.x, v2.x, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(v1.y, v2.y, rel_tol = rel_tol, abs_tol = abs_tol)
                )
        #end iscloseto

    #end if

    def __add__(v1, v2) :
        "offset one Vector by another."
        return \
            (
                lambda : NotImplemented,
                lambda : type(v1)(v1.x + v2.x, v1.y + v2.y)
            )[isinstance(v2, Vector)]()
    #end __add__

    def __neg__(self) :
        "reflect across origin."
        return type(self) \
          (
            x = - self.x,
            y = - self.y
          )
    #end __neg__

    def __sub__(v1, v2) :
        "difference between two Vectors."
        return \
            (
                lambda : NotImplemented,
                lambda : type(v1)(v1.x - v2.x, v1.y - v2.y)
            )[isinstance(v2, Vector)]()
    #end __sub__

    def __mul__(v, f) :
        "scale a Vector uniformly by a number or non-uniformly by another Vector."
        if isinstance(f, Vector) :
            result = type(v)(v.x * f.x, v.y * f.y)
        elif isinstance(f, Real) :
            result = type(v)(v.x * f, v.y * f)
        elif isinstance(f, Complex) :
            result = type(v).from_complex(v.to_complex() * f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __mul__
    __rmul__ = __mul__

    def __truediv__(v, f) :
        "inverse-scale a Vector uniformly by a number or non-uniformly by another Vector."
        if isinstance(f, Vector) :
            result = type(v)(v.x / f.x, v.y / f.y)
        elif isinstance(f, Real) :
            result = type(v)(v.x / f, v.y / f)
        elif isinstance(f, Complex) :
            result = type(v).from_complex(v.to_complex() / f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __truediv__

    def __floordiv__(v, f) :
        "inverse-scale an integer Vector uniformly by an integer or non-uniformly" \
        " by another integer Vector."
        v.assert_isint()
        if isinstance(f, Vector) :
            f.assert_isint()
            result = type(v)(v.x // f.x, v.y // f.y)
        elif isinstance(f, int) :
            result = type(v)(v.x // f, v.y // f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __floordiv__

    def __mod__(v, f) :
        "remainder on division of one Vector by another."
        if isinstance(f, Vector) :
            result = type(v)(v.x % f.x, v.y % f.y)
        elif isinstance(f, Real) :
            result = type(v)(v.x % f, v.y % f)
        elif isinstance(f, Complex) :
            result = type(v).from_complex(v.to_complex() % f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __mod__

    def __round__(self) :
        "returns the Vector with all coordinates rounded to integers."
        return \
            type(self)(round(self.x), round(self.y))
    #end __round__

    def __floor__(self) :
        "returns the Vector with all coordinates rounded down to integers."
        return \
            type(self)(math.floor(self.x), math.floor(self.y))
    #end __floor__

    def __ceil__(self) :
        "returns the Vector with all coordinates rounded up to integers."
        return \
            type(self)(math.ceil(self.x), math.ceil(self.y))
    #end __ceil__

    @classmethod
    def unit(celf, angle) :
        "returns the unit vector with the specified direction."
        return \
            celf(math.cos(angle), math.sin(angle))
    #end unit

    def dot(v1, v2) :
        "returns the dot product of two Vectors."
        return \
            v1.x * v2.x + v1.y * v2.y
    #end dot
    __matmul__ = dot # allow v1 @ v2 for dot product (Python 3.5 and later)

    def cross(v1, v2) :
        "returns the (scalar) cross product of two Vectors."
        return \
            v1.x * v2.y - v1.y * v2.x
    #enc cross

    def rotate(self, angle) :
        "returns the Vector rotated by the specified angle."
        cos = math.cos(angle)
        sin = math.sin(angle)
        return \
            type(self)(self.x * cos - self.y * sin, self.x * sin + self.y * cos)
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

    def norm(self) :
        "returns the unit Vector in the same direction as this one."
        return \
            type(self).unit(self.angle())
    #end norm

    @classmethod
    def from_polar(celf, length, angle) :
        "constructs a Vector from a length and a direction."
        return \
            celf(length * math.cos(angle), length * math.sin(angle))
    #end from_polar

    def axis_swap(self, swap = True) :
        "returns the Vector with the x- and y-axis coordinates swapped" \
        " or not, depending on swap."
        return \
            type(self)((self.x, self.y)[swap], (self.y, self.x)[swap])
    #end axis_swap

#end Vector
Vector.zero = Vector(0, 0)

class Matrix :
    "representation of a 3-by-2 affine homogeneous matrix. This does not" \
    " actually use any Cairo routines to implement its calculations; these" \
    " are done entirely using Python numerics. The from_cairo and to_cairo" \
    " methods provide conversion to/from cairo_matrix_t structs. Routines" \
    " elsewhere expect this Matrix type where the underlying Cairo routine" \
    " wants a cairo_matrix_t, and return this type where the Cairo routine" \
    " returns a cairo_matrix_t."

    __slots__ = ("xx", "yx", "xy", "yy", "x0", "y0") # to forestall typos

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

    def __getitem__(self, i) :
        "being able to access elements by index allows a Matrix to be cast to a tuple or list."
        return \
            getattr(self, ("xx", "yx", "xy", "yy", "x0", "y0")[i])
    #end __getitem__

    @classmethod
    def from_cairo(celf, m) :
        return \
            celf(m.xx, m.yx, m.xy, m.yy, m.x0, m.y0)
    #end from_cairo

    def to_cairo(m) :
        return \
            CAIRO.matrix_t(m.xx, m.yx, m.xy, m.yy, m.x0, m.y0)
    #end to_cairo

    if HAS.ISCLOSE :

        def iscloseto(m1, m2, rel_tol = default_rel_tol, abs_tol = default_abs_tol) :
            "approximate equality of two Matrices to within the specified tolerances."
            return \
                (
                    math.isclose(m1.xx, m2.xx, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(m1.yx, m2.yx, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(m1.xy, m2.xy, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(m1.yy, m2.yy, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(m1.x0, m2.x0, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(m1.y0, m2.y0, rel_tol = rel_tol, abs_tol = abs_tol)
                )
        #end iscloseto

    #end if

    def __mul__(m1, m2) :
        "returns concatenation with another Matrix, or mapping of a Vector."
        if isinstance(m2, Matrix) :
            result = type(m1) \
              (
                xx = m1.xx * m2.xx + m1.xy * m2.yx,
                yx = m1.yx * m2.xx + m1.yy * m2.yx,
                xy = m1.xx * m2.xy + m1.xy * m2.yy,
                yy = m1.yx * m2.xy + m1.yy * m2.yy,
                x0 = m1.xx * m2.x0 + m1.xy * m2.y0 + m1.x0,
                y0 = m1.yx * m2.x0 + m1.yy * m2.y0 + m1.y0,
              )
        elif isinstance(m2, Vector) :
            result = type(m2) \
              (
                x = m2.x * m1.xx + m2.y * m1.xy + m1.x0,
                y = m2.x * m1.yx + m2.y * m1.yy + m1.y0
              )
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __mul__
    __matmul__ = __mul__ # allow v1 @ v2 for dot product (Python 3.5 and later)

    def __pow__(m, p) :
        "raising of a Matrix to an integer power p is equivalent to applying" \
        " the transformation p times in succession."
        if isinstance(p, int) :
            if p < 0 :
                m = m.inv()
                p = -p
            #end if
            result = type(m).identity
            # O(N) exponentiation algorithm should be good enough for small
            # powers, not expecting large ones
            for i in range(p) :
                result *= m
            #end for
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __pow__

    @classmethod
    def translate(celf, delta) :
        "returns a Matrix that translates by the specified delta Vector."
        tx, ty = Vector.from_tuple(delta)
        return celf(1, 0, 0, 1, tx, ty)
    #end translate

    @classmethod
    def scale(celf, factor, centre = None) :
        "returns a Matrix that scales by the specified scalar or Vector factors" \
        " about Vector centre, or the origin if not specified."
        if isinstance(factor, Real) :
            result = celf(factor, 0, 0, factor, 0, 0)
        elif isinstance(factor, Vector) :
            result = celf(factor.x, 0, 0, factor.y, 0, 0)
        elif isinstance(factor, tuple) :
            sx, sy = factor
            result = celf(sx, 0, 0, sy, 0, 0)
        else :
            raise TypeError("factor must be a number or a Vector")
        #end if
        if centre != None :
            centre = Vector.from_tuple(centre)
            result = celf.translate(centre) * result * celf.translate(- centre)
        #end if
        return \
            result
    #end scale

    @classmethod
    def rotate(celf, angle, centre = None) :
        "returns a Matrix that rotates about the origin by the specified" \
        " angle in radians about Vector centre, or the origin if not specified."
        cos = math.cos(angle)
        sin = math.sin(angle)
        result = celf(cos, sin, -sin, cos, 0, 0)
        if centre != None :
            centre = Vector.from_tuple(centre)
            result = celf.translate(centre) * result * celf.translate(- centre)
        #end if
        return \
            result
    #end rotate

    @classmethod
    def skew(celf, vec, centre = None) :
        "returns a Matrix that skews by the specified vec.x and vec.y factors" \
        " about Vector centre, or the origin if not specified."
        sx, sy = Vector.from_tuple(vec)
        result = celf(1, sy, sx, 1, 0, 0)
        if centre != None :
            centre = Vector.from_tuple(centre)
            result = celf.translate(centre) * result * celf.translate(- centre)
        #end if
        return \
            result
    #end skew

    def det(self) :
        "matrix determinant."
        return \
            self.xx * self.yy - self.xy * self.yx
    #end det

    def adj(self) :
        "matrix adjoint."
        return type(self) \
          (
            xx = self.yy,
            yx = - self.yx,
            xy = - self.xy,
            yy = self.xx,
            x0 = self.xy * self.y0 - self.yy * self.x0,
            y0 = self.yx * self.x0 - self.xx * self.y0,
          )
    #end adj

    def inv(self) :
        "matrix inverse."
        # computed using minors <http://mathworld.wolfram.com/MatrixInverse.html>
        adj = self.adj()
        det = self.det()
        return type(self) \
          (
            xx = adj.xx / det,
            yx = adj.yx / det,
            xy = adj.xy / det,
            yy = adj.yy / det,
            x0 = adj.x0 / det,
            y0 = adj.y0 / det,
          )
    #end inv
    __invert__ = inv # so ~Matrix works

    def map(self, pt) :
        "maps a Vector through the Matrix."
        pt = Vector.from_tuple(pt)
        return type(pt) \
          (
            x = pt.x * self.xx + pt.y * self.xy + self.x0,
            y = pt.x * self.yx + pt.y * self.yy + self.y0
          )
    #end map

    def mapdelta(self, pt) :
        "maps a Vector through the Matrix, ignoring the translation part."
        pt = Vector.from_tuple(pt)
        return type(pt) \
          (
            x = pt.x * self.xx + pt.y * self.xy,
            y = pt.x * self.yx + pt.y * self.yy
          )
    #end mapdelta

    def mapiter(self, pts) :
        "maps an iterable of Vectors through the Matrix."
        pts = iter(pts)
        while True :
            try :
                yield self.map(next(pts))
            except StopIteration :
                break
            #end try
        #end while
    #end mapiter

    def mapdeltaiter(self, pts) :
        "maps an iterable of Vectors through the Matrix, ignoring the" \
        " translation part."
        pts = iter(pts)
        while True :
            try :
                yield self.mapdelta(next(pts))
            except StopIteration :
                break
            #end try
        #end while
    #end mapdeltaiter

    def __repr__(self) :
        return \
            (
                "%s(%g, %g, %g, %g, %g, %g)"
            %
                (
                    type(self).__name__,
                    self.xx, self.yx,
                    self.xy, self.yy,
                    self.x0, self.y0,
                )
            )
    #end __repr__

#end Matrix
Matrix.identity = Matrix(1, 0, 0, 1, 0, 0)

def interp(fract, p1, p2) :
    "returns the point along p1 to p2 at relative position fract."
    return (p2 - p1) * fract + p1
#end interp

def distribute(nrdivs, p1 = 0.0, p2 = 1.0, endincl = False) :
    "returns a sequence of nrdivs values evenly distributed over" \
    " [p1, p2) (if not endincl) or nrdivs + 1 values over [p1, p2] (if endincl)."
    interval = p2 - p1
    return tuple \
      (
        interval * (i / nrdivs) + p1
            for i in range(0, nrdivs + int(endincl))
      )
#end distribute

class Rect :
    "an axis-aligned rectangle. The constructor takes the left and top coordinates," \
    " and the width and height. Or use from_corners to construct one from two Vectors" \
    " representing opposite corners, or from_dimensions to construct one from a Vector" \
    " giving the width and height, with the topleft set to (0, 0)."

    __slots__ = ("left", "top", "width", "height") # to forestall typos

    def __init__(self, left, top, width, height) :
        self.left = left
        self.top = top
        self.width = width
        self.height = height
    #end __init__

    @classmethod
    def from_corners(celf, pt1, pt2) :
        "constructs a Rect from two opposite corner Vectors."
        pt1 = Vector.from_tuple(pt1)
        pt2 = Vector.from_tuple(pt2)
        min_x = min(pt1.x, pt2.x)
        max_x = max(pt1.x, pt2.x)
        min_y = min(pt1.y, pt2.y)
        max_y = max(pt1.y, pt2.y)
        return \
            celf(min_x, min_y, max_x - min_x, max_y - min_y)
    #end from_corners

    @classmethod
    def from_dimensions(celf, pt) :
        "a Rect with its top left at (0, 0) and the given width and height."
        pt = Vector.from_tuple(pt)
        return \
            celf(0, 0, pt.x, pt.y)
    #end from_dimensions

    def flip(self, flip_x = True, flip_y = True) :
        "returns a Rect describing the same bounds, but with the sign" \
        " of the width or height flipped, and topleft transposed" \
        " accordingly."
        return \
            type(self) \
              (
                (self.left, self.right)[flip_x],
                (self.top, self.bottom)[flip_y],
                (self.width, - self.width)[flip_x],
                (self.height, - self.height)[flip_y],
              )
    #end flip

    def abs(self, flip_x = True, flip_y = True) :
        "returns a Rect describing the same bounds, ensuring that the" \
        " width or height (or both) are non-negative."
        return \
            self.flip \
              (
                flip_x = flip_x and self.width < 0,
                flip_y = flip_y and self.height < 0
              )
    #end abs

    if HAS.ISCLOSE :

        def iscloseto(r1, r2, rel_tol = default_rel_tol, abs_tol = default_abs_tol) :
            "approximate equality of two Rects to within the specified tolerances."
            return \
                (
                    math.isclose(r1.left, r2.left, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(r1.top, r2.top, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(r1.width, r2.width, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(r1.height, r2.height, rel_tol = rel_tol, abs_tol = abs_tol)
                )
        #end iscloseto

    #end if

    @classmethod
    def from_cairo(celf, r) :
        "converts a CAIRO.rectangle_t to a Rect."
        return \
            celf(r.x, r.y, r.width, r.height)
    #end from_cairo

    def to_cairo(self) :
        "converts the Rect to a CAIRO.rectangle_t."
        return \
            CAIRO.rectangle_t(self.left, self.top, self.width, self.height)
    #end to_cairo

    def to_cairo_int(self) :
        "converts the Rect to a CAIRO.rectangle_int_t."
        self.assert_isint()
        return \
            CAIRO.rectangle_int_t(self.left, self.top, self.width, self.height)
    #end to_cairo_int

    @property
    def bottom(self) :
        "the bottom y-coordinate of the Rect."
        return \
            self.top + self.height
    #end bottom

    @property
    def right(self) :
        "the right x-coordinate of the Rect."
        return \
            self.left + self.width
    #end right

    @property
    def topleft(self) :
        "the top-left corner point."
        return \
            Vector(self.left, self.top)
    #end topleft

    @property
    def botright(self) :
        "the bottom-right corner point."
        return \
            Vector(self.left + self.width, self.top + self.height)
    #end botright

    @property
    def dimensions(self) :
        "the dimensions of the Rect as a Vector."
        return \
            Vector(self.width, self.height)
    #end dimensions

    @property
    def middle(self) :
        "the midpoint as a Vector."
        return \
            Vector(self.left + self.width / 2, self.top + self.height / 2)
    #end middle

    def __round__(self) :
        "returns the Rect with all corner coordinates rounded to integers."
        return \
            type(self).from_corners(round(self.topleft), round(self.botright))
    #end __round__

    def __floor__(self) :
        "returns the Rect with the top-left rounded up and the bottom-right" \
        " rounded down to integers. This gives the largest Rect with integer" \
        " coordinates that fits within the original."
        return \
            type(self).from_corners(math.ceil(self.topleft), math.floor(self.botright))
    #end __floor__

    def __ceil__(self) :
        "returns the Rect with the top-left rounded down and the bottom-right" \
        " rounded up to integers. This gives the smallest Rect with integer" \
        " coordinates that encloses the original."
        return \
            type(self).from_corners(math.floor(self.topleft), math.ceil(self.botright))
    #end __ceil__

    def __add__(self, v) :
        "add a Rect to a Vector to return the Rect offset by the Vector."
        if isinstance(v, Vector) :
            result = type(self)(self.left + v.x, self.top + v.y, self.width, self.height)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __add__

    def __sub__(self, v) :
        "subtract a Vector from a Rect to return the Rect offset in the" \
        " opposite direction to the Vector."
        if isinstance(v, Vector) :
            result = type(self)(self.left - v.x, self.top - v.y, self.width, self.height)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __sub__

    def __mul__(self, f) :
        "scale a Rect uniformly by a number or non-uniformly by a Vector."
        if isinstance(f, Vector) :
            result = type(self)(self.left * f.x, self.top * f.y, self.width * f.x, self.height * f.y)
        elif isinstance(f, Real) :
            result = type(self)(self.left * f, self.top * f, self.width * f, self.height * f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __mul__
    __rmul__ = __mul__

    def __truediv__(self, f) :
        "inverse-scale a Rect uniformly by a number or non-uniformly by a Vector."
        if isinstance(f, Vector) :
            result = type(self)(self.left / f.x, self.top / f.y, self.width / f.x, self.height / f.y)
        elif isinstance(f, Real) :
            result = type(self)(self.left / f, self.top / f, self.width / f, self.height / f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __truediv__

    def __floordiv__(self, f) :
        "inverse-scale an integer Rect uniformly by an integer or non-uniformly" \
        " by an integer Vector."
        self.assert_isint()
        if isinstance(f, Vector) :
            f.assert_isint()
            result = type(self)(self.left // f.x, self.top // f.y, self.width // f.x, self.height // f.y)
        elif isinstance(f, int) :
            result = type(self)(self.left // f, self.top // f, self.width // f, self.height // f)
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __floordiv__

    def __eq__(r1, r2) :
        "equality of two rectangles."
        return \
            (
                isinstance(r2, Rect)
            and
                r1.left == r2.left
            and
                r1.top == r2.top
            and
                r1.width == r2.width
            and
                r1.height == r2.height
            )
    #end __eq__

    @property
    def is_empty(self) :
        "is this Rect empty."
        return \
            self.width <= 0 or self.height <= 0
    #end is_empty

    def transform(self, matrix) :
        "returns the transformation of this Rect by a Matrix. Only" \
        " scaling and translation is allowed."
        topleft, topright, botleft, botright = matrix.mapiter \
          ((
            self.topleft,
            Vector(self.right, self.top),
            Vector(self.left, self.bottom),
            self.botright,
          ))
        assert \
            (
                topleft.y == topright.y
            and
                topright.x == botright.x
            and
                botright.y == botleft.y
            and
                botleft.x == topleft.x
            )
        return \
            type(self).from_corners(topleft, botright)
    #end transform

    def union(r1, r2) :
        "smallest rectangle enclosing both rectangles."
        if r1.is_empty :
            result = r2
        elif r2.is_empty :
            result = r1
        else :
            vmin = Vector(min(r1.left, r2.left), min(r1.top, r2.top))
            vmax = Vector(max(r1.left + r1.width, r2.left + r2.width), max(r1.top + r1.height, r2.top + r2.height))
            result = type(r1).from_corners(vmin, vmax)
        #end if
        return \
            result
    #end union

    def intersection(r1, r2) :
        "largest rectangle contained by both rectangles."
        if r1.is_empty :
            result = r1
        elif r2.is_empty :
            result = r2
        elif r1.right <= r2.left or r2.right <= r1.left or r1.bottom <= r2.top or r2.bottom <= r1.top :
            result = Rect.empty
        else :
            vmin = Vector(max(r1.left, r2.left), max(r1.top, r2.top))
            vmax = Vector(min(r1.right, r2.right), min(r1.bottom, r2.bottom))
            result = type(r1).from_corners(vmin, vmax)
        #end if
        return \
            result
    #end intersection

    def __and__(r1, r2) :
        "r1 & r2 = largest rectangle contained by both rectangles."
        return \
            r1.intersection(r2)
    #end __and__

    def __or__(r1, r2) :
        "r1 | r2 = smallest rectangle enclosing both rectangles."
        return \
            r1.union(r2)
    #end __union__

    def isint(self) :
        "are the components signed 32-bit integers."
        return \
            (
                int_fits_bits(self.left, 32)
            and
                int_fits_bits(self.top, 32)
            and
                int_fits_bits(self.width, 32)
            and
                int_fits_bits(self.height, 32)
            )
    #end isint

    def assert_isint(self) :
        "checks that the components are signed 32-bit integers."
        if not self.isint() :
            raise ValueError("components must be signed 32-bit integers")
        #end if
        return \
            self
    #end assert_isint

    def __repr__(self) :
        return \
            (
                "%%s(%%%(fmt)s, %%%(fmt)s, %%%(fmt)s, %%%(fmt)s)"
            %
                {"fmt" : ("g", "d") [self.isint()]}
            %
                (type(self).__name__, self.left, self.top, self.width, self.height)
            )
    #end __repr__

    def to_path(self) :
        "returns a Path object which draws this rectangle."
        return \
            Path \
              (
                [
                    Path.Segment
                      (
                        [
                            Path.Point((self.left, self.top), False),
                            Path.Point((self.right, self.top), False),
                            Path.Point((self.right, self.bottom), False),
                            Path.Point((self.left, self.bottom), False),
                        ],
                        True
                      )
                ]
              )
    #end to_path

    def inset(self, v) :
        "returns a Rect inset by the specified x and y amounts from this one" \
        " (use negative values to outset)."
        dx, dy = Vector.from_tuple(v)
        return \
            type(self)(self.left + dx, self.top + dy, self.width - 2 * dx, self.height - 2 * dy)
    #end inset

    def position(self, relpt, halign = None, valign = None) :
        "returns a copy of this Rect repositioned relative to Vector relpt, horizontally" \
        " according to halign and vertically according to valign (if not None" \
        " in each case). halign = 0 means the left edge is on the point, while" \
        " halign = 1 means the right edge is on the point. Similarly valign = 0" \
        " means the top edge is on the point, while valign = 1 means the bottom" \
        " edge is on the point. Intermediate values correspond to intermediate" \
        " linearly-interpolated positions."
        left = self.left
        top = self.top
        if halign != None :
            left = relpt.x - interp(halign, 0, self.width)
        #end if
        if valign != None :
            top = relpt.y - interp(valign, 0, self.height)
        #end if
        return type(self)(left = left, top = top, width = self.width, height = self.height)
    #end position

    def align(self, within, halign = None, valign = None) :
        "returns a copy of this Rect repositioned relative to within, which is" \
        " another Rect, horizontally according to halign and vertically according" \
        " to valign (if not None in each case). halign = 0 means the left edges" \
        " coincide, while halign = 1 means the right edges coincide. Similarly" \
        " valign = 0 means the top edges coincide, while valign = 1 means the" \
        " bottom edges coincide. Intermediate values correspond to intermediate" \
        " linearly-interpolated positions."
        left = self.left
        top = self.top
        if halign != None :
            left = interp(halign, within.left, within.left + within.width - self.width)
        #end if
        if valign != None :
            top = interp(valign, within.top, within.top + within.height - self.height)
        #end if
        return type(self)(left = left, top = top, width = self.width, height = self.height)
    #end align

    def transform_to(src, dst) :
        "returns a Matrix which maps this Rect into dst Rect."
        return \
            (
                Matrix.translate(dst.topleft)
            *
                Matrix.scale(dst.dimensions / src.dimensions)
            *
                Matrix.translate(- src.topleft)
            )
    #end transform_to

    def fit_to(src, dst, outside = False) :
        "returns a Matrix which maps this Rect onto dst Rect without distortion" \
        " if the aspect ratios don’t match. Instead, src will be uniformly scaled" \
        " to the largest possible size that fits within dst if outside is False," \
        " or to the smallest possible size that dst will fit within if outside is" \
        " True."
        scale = dst.dimensions / src.dimensions
        scale = (min, max)[outside](scale.x, scale.y)
        return \
          (
                Matrix.translate(dst.middle)
            *
                Matrix.scale((scale, scale))
            *
                Matrix.translate(- src.middle)
          )
    #end fit_to

#end Rect
Rect.empty = Rect(0, 0, 0, 0)

class Glyph :
    "specifies a glyph index and position relative to the origin."

    __slots__ = ("index", "pos") # to forestall typos

    def __init__(self, index, pos) :
        pos = Vector.from_tuple(pos)
        self.index = index
        self.pos = Vector.from_tuple(pos)
    #end __init__

    def __eq__(g1, g2) :
        return \
            g1.index == g2.index and g1.pos == g2.pos
    #end __eq__

    def __repr__(self) :
        return \
            "Glyph(%d, %s)" % (self.index, repr(self.pos))
    #end __repr__

#end Glyph

def offset_glyphs(glyphs, offset) :
    "applies an offset Vector to the pos field of an iterable of Glyph" \
    " objects."
    # Q: Why not apply a more general Matrix?
    # A: Because in that case, you are likely to want to apply the
    #    transformation to the glyph shape itself, which this routine
    #    does not (and cannot) do.
    for glyph in glyphs :
        yield Glyph(glyph.index, glyph.pos + offset)
    #end for
#end offset_glyphs

def glyphs_to_cairo(glyphs) :
    "converts a sequence of Glyph objects to Cairo form."
    nr_glyphs = len(glyphs)
    buf = (nr_glyphs * CAIRO.glyph_t)()
    for i in range(nr_glyphs) :
        src = glyphs[i]
        buf[i] = CAIRO.glyph_t(src.index, src.pos.x, src.pos.y)
    #end for
    return \
        buf, nr_glyphs
#end glyphs_to_cairo

default_tolerance = 0.1 # for flattening paths

#+
# Notes on object design:
#
# Qahirah objects which wrap Cairo objects store address of latter
# in _cairobj attribute. Object constructors are reserved for internal
# use.
#
# Round-trip object identity: when one Cairo object is set as an attribute
# of another (e.g. a Context.source is set to a Pattern) and then retrieved
# again, it is nice if the caller gets back the same Qahirah wrapper object.
# I do this by maintaining a WeakValueDictionary in each of the relevant
# (base) classes, which is updated by the constructors.
#-

_dependent_src = WeakKeyDictionary()
_dependent_target = WeakKeyDictionary()
  # for propagating dependencies on Python objects that must not go
  # away even if caller forgets them, as long as depending object exists.
  # Currently this is just array.array objects used to hold ImageSurface pixels.

class UserDataDict(dict) :
    "a subclass of dict that allows weakrefs."

    __slots__ = ("__weakref__",)

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
    #end __init__

#end UserDataDict

class Context :
    "a Cairo drawing context. Do not instantiate directly; use the create methods." \
    " Many methods return the context to allow method chaining."
    # <http://cairographics.org/manual/cairo-cairo-t.html>

    __slots__ = ("_cairobj", "_user_data", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this Context.
        check(cairo.cairo_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    @classmethod
    def create(celf, surface) :
        "creates a new Context that draws into the specified Surface."
        if not isinstance(surface, Surface) :
            raise TypeError("surface must be a Surface")
        #end if
        result = celf(cairo.cairo_create(surface._cairobj))
          # might raise exception on _check() call
        _dependent_target[result] = _dependent_src.get(surface)
          # to ensure any storage attached to it doesn't go away prematurely
        return \
            result
    #end create

    @classmethod
    def create_for_dummy(celf) :
        "creates a new Context that draws into a 0×0-pixel ImageSurface." \
        " This is useful for doing path/text calculations without drawing."
        return \
            celf.create \
              (
                ImageSurface.create
                  (
                    format = CAIRO.FORMAT_ARGB32,
                    dimensions = (0, 0)
                  )
              )
    #end create_for_dummy

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    def save(self) :
        "saves the Cairo graphics state."
        cairo.cairo_save(self._cairobj)
        return \
            self
    #end save

    def restore(self) :
        "restores the last saved-but-not-restored graphics state."
        cairo.cairo_restore(self._cairobj)
        self._check()
        return \
            self
    #end restore

    @property
    def target(self) :
        "the current target Surface."
        return \
            Surface(cairo.cairo_surface_reference(cairo.cairo_get_target(self._cairobj)))
    #end target

    def push_group(self) :
        "temporarily redirects drawing to a temporary surface with content" \
        " CAIRO.CONTENT_COLOUR_ALPHA."
        cairo.cairo_push_group(self._cairobj)
        return \
            self
    #end push_group

    def push_group_with_content(self, content) :
        "temporarily redirects drawing to a temporary surface. content is a CAIRO.CONTENT_xxx value."
        cairo.cairo_push_group_with_content(self._cairobj, content)
        return \
            self
    #end push_group_with_content

    def pop_group(self) :
        "pops the last pushed-but-not-popped group redirection, and returns a Pattern" \
        " containing the result of the redirected drawing."
        return \
            Pattern(cairo.cairo_pop_group(self._cairobj))
    #end pop_group

    def pop_group_to_source(self) :
        "pops the last pushed-but-not-popped group redirection, and sets the Pattern" \
        " containing the result of the redirected drawing as the Context.source."
        cairo.cairo_pop_group_to_source(self._cairobj)
        self._check()
        return \
            self
    #end pop_group_to_source

    @property
    def group_target(self) :
        "returns the current group redirection target, or the original Surface if no" \
        " redirection is in effect."
        return \
            Surface(cairo.cairo_surface_reference(cairo.cairo_get_group_target(self._cairobj)))
    #end group_target

    @property
    def source(self) :
        "the current source Pattern."
        return \
            Pattern(cairo.cairo_pattern_reference(cairo.cairo_get_source(self._cairobj)))
    #end source

    @source.setter
    def source(self, source) :
        "the current source Pattern."
        self.set_source(source)
    #end source

    def set_source(self, source) :
        "sets a new source Pattern. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the source property."
        if not isinstance(source, Pattern) :
            raise TypeError("source is not a Pattern")
        #end if
        cairo.cairo_set_source(self._cairobj, source._cairobj)
        self._check()
        _dependent_src[self] = _dependent_src.get(source)
          # to ensure any storage attached to it doesn't go away prematurely
        return \
            self
    #end set_source

    @property
    def source_colour(self) :
        "returns the current source pattern Colour. The current source Pattern must" \
        " be a plain-colour pattern."
        return \
            self.source.colour
    #end source_colour

    @source_colour.setter
    def source_colour(self, c) :
        self.set_source_colour(c)
    #end source_colour

    def set_source_colour(self, c) :
        "sets a new plain-colour pattern as the source. c must be a Colour" \
        " object or a tuple. Use for method-chaining; otherwise it’s probably" \
        " more convenient to assign to the source_colour property."
        cairo.cairo_set_source_rgba(*((self._cairobj,) + tuple(Colour.from_rgba(c))))
        self._check()
        _dependent_src[self] = None # remove dependency on any previous source
        return \
            self
    #end set_source_colour

    def set_source_surface(self, surface, origin) :
        "creates a Pattern from a Surface and sets it as the source in one step."
        if not isinstance(surface, Surface) :
            raise TypeError("surface must be a Surface")
        #end if
        x, y = Vector.from_tuple(origin)
        cairo.cairo_set_source_surface(self._cairobj, surface._cairobj, x, y)
        self._check()
        _dependent_src[self] = _dependent_src.get(surface)
          # to ensure any storage attached to it doesn't go away prematurely
        return \
            self
    #end set_source_surface

    @property
    def antialias(self) :
        "the current antialias mode, CAIRO.ANTIALIAS_xxx."
        return \
            cairo.cairo_get_antialias(self._cairobj)
    #end antialias

    @antialias.setter
    def antialias(self, antialias) :
        self.set_antialias(antialias)
    #end antialias

    def set_antialias(self, antialias) :
        "sets a new antialias mode. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the antialias property."
        cairo.cairo_set_antialias(self._cairobj, antialias)
        return \
            self
    #end set_antialias

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
        self.set_dash(dashes)
    #end dash

    def set_dash(self, dashes) :
        "sets a new line dash. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the dash property."
        segs, offset = dashes
        nrsegs = len(segs)
        csegs = (nrsegs * ct.c_double)()
        for i in range(nrsegs) :
            csegs[i] = segs[i]
        #end for
        cairo.cairo_set_dash(self._cairobj, ct.byref(csegs), nrsegs, offset)
        return \
            self
    #end set_dash

    @property
    def fill_rule(self) :
        "the current fill rule CAIRO.FILL_RULE_xxx."
        return \
            cairo.cairo_get_fill_rule(self._cairobj)
    #end fill_rule

    @fill_rule.setter
    def fill_rule(self, fill_rule) :
        self.set_fill_rule(fill_rule)
    #end fill_rule

    def set_fill_rule(self, fill_rule) :
        "sets a new fill rule. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the fill_rule property."
        cairo.cairo_set_fill_rule(self._cairobj, fill_rule)
        return \
            self
    #end set_fill_rule

    @property
    def line_cap(self) :
        "the current CAIRO.LINE_CAP_xxx setting."
        return \
            cairo.cairo_get_line_cap(self._cairobj)
    #end line_cap

    @line_cap.setter
    def line_cap(self, line_cap) :
        self.set_line_cap(line_cap)
    #end line_cap

    def set_line_cap(self, line_cap) :
        "sets a new line cap. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the line_cap property."
        cairo.cairo_set_line_cap(self._cairobj, line_cap)
        return \
            self
    #end set_line_cap

    @property
    def line_join(self) :
        "the current CAIRO.LINE_JOIN_xxx setting."
        return \
            cairo.cairo_get_line_join(self._cairobj)
    #end line_join

    @line_join.setter
    def line_join(self, line_join) :
        self.set_line_join(line_join)
    #end line_join

    def set_line_join(self, line_join) :
        "sets a new line join. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the line_join property."
        cairo.cairo_set_line_join(self._cairobj, line_join)
        return \
            self
    #end set_line_join

    @property
    def line_width(self) :
        "the current stroke line width."
        return \
            cairo.cairo_get_line_width(self._cairobj)
    #end line_width

    @line_width.setter
    def line_width(self, width) :
        self.set_line_width(width)
    #end line_width

    def set_line_width(self, width) :
        "sets a new line width. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the line_width property."
        cairo.cairo_set_line_width(self._cairobj, width)
        return \
            self
    #end set_line_width

    @property
    def mitre_limit(self) :
        "the current mitre limit."
        return \
            cairo.cairo_get_miter_limit(self._cairobj)
    #end mitre_limit

    @mitre_limit.setter
    def mitre_limit(self, limit) :
        self.set_mitre_limit(limit)
    #end mitre_limit

    def set_mitre_limit(self, limit) :
        "sets a new mitre limit. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the mitre_limit property."
        cairo.cairo_set_miter_limit(self._cairobj, limit)
        return \
            self
    #end set_mitre_limit

    @property
    def operator(self) :
        "the current drawing operator, as a CAIRO.OPERATOR_xxx code."
        return \
            cairo.cairo_get_operator(self._cairobj)
    #end operator

    @operator.setter
    def operator(self, op) :
        self.set_operator(op)
    #end operator

    def set_operator(self, op) :
        "sets a new drawing operator. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the operator property."
        cairo.cairo_set_operator(self._cairobj, op)
        self._check()
        return \
            self
    #end set_operator

    @property
    def tolerance(self) :
        "the curve-flattening tolerance."
        return \
            cairo.cairo_get_tolerance(self._cairobj)
    #end tolerance

    @tolerance.setter
    def tolerance(self, tolerance) :
        self.set_tolerance(tolerance)
    #end tolerance

    def set_tolerance(self, tolerance) :
        "sets a new curve-rendering tolerance. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the tolerance property."
        cairo.cairo_set_tolerance(self._cairobj, tolerance)
        return \
            self
    #end set_tolerance

    def clip(self) :
        "sets the current clip to the intersection of itself and the" \
        " current path, clearing the latter."
        cairo.cairo_clip(self._cairobj)
        return \
            self
    #end clip

    def clip_preserve(self) :
        "sets the current clip to the intersection of itself and the" \
        " current path, preserving the latter."
        cairo.cairo_clip_preserve(self._cairobj)
        return \
            self
    #end clip_preserve

    @property
    def clip_extents(self) :
        "returns a Rect bounding the current clip."
        x1 = ct.c_double()
        x2 = ct.c_double()
        y1 = ct.c_double()
        y2 = ct.c_double()
        cairo.cairo_clip_extents(self._cairobj, ct.byref(x1), ct.byref(y1), ct.byref(x2), ct.byref(y2))
        return \
            Rect(x1.value, y1.value, x2.value - x1.value, y2.value - y1.value)
    #end clip_extents

    def in_clip(self, pt) :
        "is the given Vector pt within the current clip."
        x, y = Vector.from_tuple(pt)
        return \
            cairo.cairo_in_clip(self._cairobj, x, y)
    #end in_clip

    @property
    def clip_rectangle_list(self) :
        "returns a copy of the current clip region as a list of Rects. Whether this works" \
        " depends on the backend."
        rects = cairo.cairo_copy_clip_rectangle_list(self._cairobj)
        try :
            check(rects.contents.status)
            result = list(Rect.from_cairo(rects.contents.rectangles[i]) for i in range(rects.contents.num_rectangles))
        finally :
            cairo.cairo_rectangle_list_destroy(rects)
        #end try
        return \
            result
    #end clip_rectangle_list

    def reset_clip(self) :
        "resets the clip to infinite extent."
        cairo.cairo_reset_clip(self._cairobj)
        return \
            self
    #end reset_clip

    def fill(self) :
        "fills the current path, then clears it."
        cairo.cairo_fill(self._cairobj)
        return \
            self
    #end fill

    def fill_preserve(self) :
        "fills the current path, preserving it."
        cairo.cairo_fill_preserve(self._cairobj)
        return \
            self
    #end fill_preserve

    @property
    def fill_extents(self) :
        "returns a Rect bounding the current path if filled."
        x1 = ct.c_double()
        x2 = ct.c_double()
        y1 = ct.c_double()
        y2 = ct.c_double()
        cairo.cairo_fill_extents(self._cairobj, ct.byref(x1), ct.byref(y1), ct.byref(x2), ct.byref(y2))
        return \
            Rect(x1.value, y1.value, x2.value - x1.value, y2.value - y1.value)
    #end fill_extents

    def in_fill(self, pt) :
        "is the given Vector pt within the current path if filled."
        x, y = Vector.from_tuple(pt)
        return \
            cairo.cairo_in_fill(self._cairobj, x, y)
    #end in_fill

    def mask(self, pattern) :
        "fills the current clip area with the current source using the alpha channel" \
        " of the given Pattern as a mask."
        if not isinstance(pattern, Pattern) :
            raise TypeError("pattern is not a Pattern")
        #end if
        cairo.cairo_mask(self._cairobj, pattern._cairobj)
        return \
            self
    #end mask

    def mask_surface(self, surface, origin) :
        "fills the current clip area with the current source using the alpha channel" \
        " of the given Surface, offset to origin, as a mask."
        if not isinstance(surface, Surface) :
            raise TypeError("surface is not a Surface")
        #end if
        x, y = Vector.from_tuple(origin)
        cairo.cairo_mask_surface(self._cairobj, surface._cairobj, x, y)
        return \
            self
    #end mask_surface

    def paint(self) :
        "fills the current clip area with the source."
        cairo.cairo_paint(self._cairobj)
        return \
            self
    #end paint

    def paint_with_alpha(self, alpha) :
        "fills the current clip area with the source faded with the given alpha value."
        cairo.cairo_paint_with_alpha(self._cairobj, alpha)
        return \
            self
    #end paint_with_alpha

    def stroke(self) :
        "strokes the current path, and clears it."
        cairo.cairo_stroke(self._cairobj)
        return \
            self
    #end stroke

    def stroke_preserve(self) :
        "strokes the current path, preserving it."
        cairo.cairo_stroke_preserve(self._cairobj)
        return \
            self
    #end stroke_preserve

    @property
    def stroke_extents(self) :
        "returns a Rect bounding the current path if stroked."
        x1 = ct.c_double()
        x2 = ct.c_double()
        y1 = ct.c_double()
        y2 = ct.c_double()
        cairo.cairo_stroke_extents(self._cairobj, ct.byref(x1), ct.byref(y1), ct.byref(x2), ct.byref(y2))
        return \
            Rect(x1.value, y1.value, x2.value - x1.value, y2.value - y1.value)
    #end stroke_extents

    def in_stroke(self, pt) :
        "is the given Vector pt within the current path if stroked."
        x, y = Vector.from_tuple(pt)
        return \
            cairo.cairo_in_stroke(self._cairobj, x, y)
    #end in_stroke

    def copy_page(self) :
        "emits the current page for Surfaces that support multiple pages."
        cairo.cairo_copy_page(self._cairobj)
        self._check()
        return \
            self
    #end copy_page

    def show_page(self) :
        "emits and clears the current page for Surfaces that support multiple pages."
        cairo.cairo_show_page(self._cairobj)
        self._check()
        return \
            self
    #end show_page

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    # paths <http://cairographics.org/manual/cairo-Paths.html>

    def copy_path(self) :
        "returns a copy of the current path as a Path object."
        temp = cairo.cairo_copy_path(self._cairobj)
        try :
            result = Path.from_cairo(temp)
        finally :
            cairo.cairo_path_destroy(temp)
        #end try
        return \
            result
    #end copy_path

    def copy_path_flat(self) :
        "returns a copy of the current path as a Path object, with curves" \
        " flattened to line segments."
        temp = cairo.cairo_copy_path_flat(self._cairobj)
        try :
            result = Path.from_cairo(temp)
        finally :
            cairo.cairo_path_destroy(temp)
        #end try
        return \
            result
    #end copy_path_flat

    def append_path(self, path, matrix = None) :
        "appends another Path onto the current path, optionally transformed" \
        " by a Matrix."
        # Note I do not use cairo_append_path because my Path structure
        # is implemented entirely in Python.
        if not isinstance(path, Path) :
            raise TypeError("path is not a Path")
        #end if
        path.draw(self, matrix)
        return \
            self
    #end append_path

    @property
    def has_current_point(self) :
        "is current_point currently defined."
        return \
            bool(cairo.cairo_has_current_point(self._cairobj))
    #end has_current_point

    @property
    def current_point(self) :
        "returns the current point if defined, else None."
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
        "clears the current path."
        cairo.cairo_new_path(self._cairobj)
        return \
            self
    #end new_path

    def new_sub_path(self) :
        "clears the current_point without actually affecting the current path."
        cairo.cairo_new_sub_path(self._cairobj)
        return \
            self
    #end new_sub_path

    def close_path(self) :
        "draws a line from the current point back to the start of the current path segment."
        cairo.cairo_close_path(self._cairobj)
        return \
            self
    #end close_path

    def arc(self, centre, radius, angle1, angle2, negative) :
        "draws a segment of a circular arc in the positive-x-to-positive-y" \
        " direction (if not negative) or the positive-y-to-positive-x direction" \
        " (if negative). centre can be a Vector or a tuple of 2 coord values."
        centre = Vector.from_tuple(centre)
        getattr(cairo, ("cairo_arc", "cairo_arc_negative")[negative]) \
            (self._cairobj, centre.x, centre.y, radius, angle1, angle2)
        return \
            self
    #end arc

    def circle(self, centre, radius) :
        "extremely common case of arc forming a full circle."
        centre = Vector.from_tuple(centre)
        cairo.cairo_new_sub_path(self._cairobj)
        cairo.cairo_arc(self._cairobj, centre.x, centre.y, radius, 0, circle)
        cairo.cairo_close_path(self._cairobj)
        cairo.cairo_new_sub_path(self._cairobj)
        return \
            self
    #end circle

    def curve_to(self, p1, p2, p3) :
        "curve_to(p1, p2, p3) or curve_to((x1, y1), (x2, y2), (x3, y3)) -- draws a cubic" \
        " Bézier curve from the current point through the specified control points." \
        " Does a move_to(p1) first if there is no current point."
        p1 = Vector.from_tuple(p1)
        p2 = Vector.from_tuple(p2)
        p3 = Vector.from_tuple(p3)
        cairo.cairo_curve_to(self._cairobj, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
        return \
            self
    #end curve_to

    def line_to(self, p) :
        "line_to(p) or line_to((x, y)) -- draws a line from the current point to the" \
        " new point. Acts like move_to(p) if there is no current point."
        p = Vector.from_tuple(p)
        cairo.cairo_line_to(self._cairobj, p.x, p.y)
        return \
            self
    #end line_to

    def move_to(self, p) :
        "move_to(p) or move_to((x, y)) -- sets the current point to the new point."
        p = Vector.from_tuple(p)
        cairo.cairo_move_to(self._cairobj, p.x, p.y)
        return \
            self
    #end move_to

    def rectangle(self, rect) :
        "appends a rectangular outline to the current path."
        cairo.cairo_rectangle(self._cairobj, rect.left, rect.top, rect.width, rect.height)
        return \
            self
    #end rectangle

    def glyph_path(self, glyphs) :
        "glyphs is a sequence of Glyph objects; appends the glyph outlines to" \
        " the current path at the specified positions."
        buf, nr_glyphs = glyphs_to_cairo(glyphs)
        cairo.cairo_glyph_path(self._cairobj, ct.byref(buf), nr_glyphs)
        return \
            self
    #end glyph_path

    def text_path(self, text) :
        "adds text outlines to the current path."
        c_text = text.encode()
        cairo.cairo_text_path(self._cairobj, c_text)
        return \
            self
    #end text_path

    def rel_curve_to(self, p1, p2, p3) :
        "rel_curve_to(p1, p2, p3) or rel_curve_to((x1, y1), (x2, y2), (x3, y3)) -- does" \
        " a curve_to through the specified control points interpreted as offsets from" \
        " the current point. There must be a current point."
        p1 = Vector.from_tuple(p1)
        p2 = Vector.from_tuple(p2)
        p3 = Vector.from_tuple(p3)
        cairo.cairo_rel_curve_to(self._cairobj, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
        return \
            self
    #end rel_curve_to

    def rel_line_to(self, p) :
        "rel_line_to(p) or rel_line_to((x, y)) -- does a line_to to the specified point" \
        " interpreted as an offset from the current point. There must be a current point."
        p = Vector.from_tuple(p)
        cairo.cairo_rel_line_to(self._cairobj, p.x, p.y)
        return \
            self
    #end rel_line_to

    def rel_move_to(self, p) :
        "rel_move_to(p) or rel_move_to((x, y)) -- offsets the current point by the" \
        " specified Vector amount. There must be a current point."
        p = Vector.from_tuple(p)
        cairo.cairo_rel_move_to(self._cairobj, p.x, p.y)
        return \
            self
    #end rel_move_to

    @property
    def path_extents(self) :
        "returns a Rect bounding the current path."
        x1 = ct.c_double()
        x2 = ct.c_double()
        y1 = ct.c_double()
        y2 = ct.c_double()
        cairo.cairo_path_extents(self._cairobj, ct.byref(x1), ct.byref(y1), ct.byref(x2), ct.byref(y2))
        return \
            Rect(x1.value, y1.value, x2.value - x1.value, y2.value - y1.value)
    #end path_extents

    # Transformations <http://cairographics.org/manual/cairo-Transformations.html>

    def translate(self, v) :
        "translate(Vector) or translate((x, y))\n" \
        "applies a translation to the current coordinate system."
        tx, ty = Vector.from_tuple(v)
        cairo.cairo_translate(self._cairobj, tx, ty)
        return \
            self
    #end translate

    def scale(self, s) :
        "scale(Vector) or scale((x, y)) or scale(Real)\n" \
        "applies a scaling to the current coordinate system."
        if isinstance(s, Real) :
            sx = sy = s
        elif isinstance(s, Vector) or isinstance(s, tuple) :
            sx, sy = tuple(s)
        else :
            raise TypeError("s must be a number or a Vector")
        #end if
        cairo.cairo_scale(self._cairobj, sx, sy)
        return \
            self
    #end scale

    def rotate(self, angle) :
        "applies a rotation by the specified angle to the current coordinate system."
        cairo.cairo_rotate(self._cairobj, angle)
        return \
            self
    #end rotate

    def transform(self, m) :
        "appends Matrix m onto the current coordinate transformation."
        m = m.to_cairo()
        cairo.cairo_transform(self._cairobj, ct.byref(m))
        return \
            self
    #end transform

    @property
    def matrix(self) :
        "the current transformation Matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_get_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end matrix

    @matrix.setter
    def matrix(self, m) :
        self.set_matrix(m)
    #end matrix

    def set_matrix(self, m) :
        "sets a new transformation matrix. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the matrix property."
        m = m.to_cairo()
        cairo.cairo_set_matrix(self._cairobj, ct.byref(m))
        self._check()
        return \
            self
    #end set_matrix

    def identity_matrix(self) :
        "resets the coordinate transformation to the identity Matrix."
        cairo.cairo_identity_matrix(self._cairobj)
        return \
            self
    #end identity_matrix

    def user_to_device(self, p) :
        "returns the transformed Vector in device coordinates corresponding to Vector" \
        " p in user coordinates."
        x = ct.c_double()
        y = ct.c_double()
        x.value, y.value = Vector.from_tuple(p)
        cairo.cairo_user_to_device(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end user_to_device

    def user_to_device_distance(self, p) :
        "returns the transformed Vector in device coordinates corresponding to Vector" \
        " p in user coordinates, ignoring any translation."
        x = ct.c_double()
        y = ct.c_double()
        x.value, y.value = Vector.from_tuple(p)
        cairo.cairo_user_to_device_distance(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end user_to_device_distance

    def device_to_user(self, p) :
        "returns the transformed Vector in user coordinates corresponding to Vector" \
        " p in device coordinates."
        x = ct.c_double()
        y = ct.c_double()
        x.value, y.value = Vector.from_tuple(p)
        cairo.cairo_device_to_user(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end device_to_user

    def device_to_user_distance(self, p) :
        "returns the transformed Vector in user coordinates corresponding to Vector" \
        " p in device coordinates, ignoring any translation."
        x = ct.c_double()
        y = ct.c_double()
        x.value, y.value = Vector.from_tuple(p)
        cairo.cairo_device_to_user_distance(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end device_to_user_distance

    if hasattr(cairo, "cairo_tag_begin") : # since 1.16

        def tag_begin(self, tag_name, attributes) :
            c_tag_name = tag_name.encode()
            c_attributes = attributes.encode()
            cairo.cairo_tag_begin(self._cairobj, c_tag_name, c_attributes)
        #end tag_begin

        def tag_end(self, tag_name) :
            c_tag_name = tag_name.encode()
            cairo.cairo_tag_end(self._cairobj, c_tag_name)
        #end tag_end

    #end if

    # Text <http://cairographics.org/manual/cairo-text.html>
    # (except toy_font_face stuff, which goes in FontFace)

    def select_font_face(self, family, slant, weight) :
        "toy selection of a font face."
        c_family = family.encode()
        cairo.cairo_select_font_face(self._cairobj, c_family, slant, weight)
        return \
            self
    #end select_font_face

    def set_font_size(self, size) :
        "sets the font matrix to a scaling by the specified size."
        cairo.cairo_set_font_size(self._cairobj, size)
        return \
            self
    #end set_font_size

    @property
    def font_matrix(self) :
        "the current font matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_get_font_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end font_matrix

    @font_matrix.setter
    def font_matrix(self, matrix) :
        self.set_font_matrix(matrix)
    #end font_matrix

    def set_font_matrix(self, matrix) :
        "sets a new font matrix. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the font_matrix property."
        if not isinstance(matrix, Matrix) :
            raise TypeError("matrix must be a Matrix")
        #end if
        matrix = matrix.to_cairo()
        cairo.cairo_set_font_matrix(self._cairobj, ct.byref(matrix))
        return \
            self
    #end set_font_matrix

    @property
    def font_options(self) :
        "a copy of the current font options."
        result = FontOptions.create()
        cairo.cairo_get_font_options(self._cairobj, result._cairobj)
        return \
            result
    #end font_options

    @font_options.setter
    def font_options(self, options) :
        self.set_font_options(options)
    #end font_options

    def set_font_options(self, options) :
        "sets new font options. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the font_options property."
        if not isinstance(options, FontOptions) :
            raise TypeError("options must be a FontOptions")
        #end if
        cairo.cairo_set_font_options(self._cairobj, options._cairobj)
        return \
            self
    #end set_font_options

    @property
    def font_face(self) :
        "the current font face."
        return \
            FontFace(cairo.cairo_font_face_reference(cairo.cairo_get_font_face(self._cairobj)))
    #end font_face

    @font_face.setter
    def font_face(self, font_face) :
        self.set_font_face(font_face)
    #end font_face

    def set_font_face(self, font_face) :
        "sets a new font face. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the font_face property."
        if not isinstance(font_face, FontFace) :
            raise TypeError("font_face must be a FontFace")
        #end if
        cairo.cairo_set_font_face(self._cairobj, font_face._cairobj)
        return \
            self
    #end set_font_face

    @property
    def scaled_font(self) :
        "the current scaled font."
        return \
            ScaledFont(cairo.cairo_scaled_font_reference(cairo.cairo_get_scaled_font(self._cairobj)))
    #end scaled_font

    @scaled_font.setter
    def scaled_font(self, scaled_font) :
        self.set_scaled_font(scaled_font)
    #end scaled_font

    def set_scaled_font(self, scaled_font) :
        "sets a new scaled font face. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the scaled_font property."
        if not isinstance(scaled_font, ScaledFont) :
            raise TypeError("scaled_font must be a ScaledFont")
        #end if
        cairo.cairo_set_scaled_font(self._cairobj, scaled_font._cairobj)
        return \
            self
    #end set_scaled_font

    def show_text(self, text) :
        "renders the specified text starting at the current point."
        c_text = text.encode()
        cairo.cairo_show_text(self._cairobj, c_text)
        return \
            self
    #end show_text

    def show_glyphs(self, glyphs) :
        "glyphs must be a sequence of Glyph objects, to be rendered starting" \
        " at the specified positions."
        buf, nr_glyphs = glyphs_to_cairo(glyphs)
        cairo.cairo_show_glyphs(self._cairobj, ct.byref(buf), nr_glyphs)
        return \
            self
    #end show_glyphs

    def show_text_glyphs(self, text, glyphs, clusters, cluster_flags) :
        "displays an array of Glyphs, also including text and cluster information" \
        " (for, e.g., searching/indexing/selection purposes) if the back-end supports" \
        " it. clusters is a sequence of 2-tuples, (nr_chars/nr_bytes, nr_glyphs); the" \
        " first element of each pair is a number of characters if text is a Unicode string," \
        " a number of bytes if text is a bytes object. If cluster_flags has" \
        " CAIRO.TEXT_CLUSTER_FLAG_BACKWARD, set, then the numbers of glyphs in the clusters" \
        " count from the end of the Glyphs array, not from the start."
        encode = not isinstance(text, bytes)
        nr_clusters = len(clusters)
        if encode :
            c_text = text.encode("utf-8")
            e_clusters = []
            pos = 0
            for c in clusters :
                # convert cluster num_chars to num_bytes
                next_pos = pos + c[0]
                e_clusters.append \
                  (
                    (len(text[pos:next_pos].encode()), c[1])
                  )
                pos = next_pos
            #end for
        else :
            c_text = text
            e_clusters = clusters
        #end if
        c_glyphs, nr_glyphs = glyphs_to_cairo(glyphs)
        c_clusters = (nr_clusters * CAIRO.cluster_t)()
        for i, c in enumerate(e_clusters) :
            c_clusters[i] = CAIRO.cluster_t(c[0], c[1])
        #end for
        cairo.cairo_show_text_glyphs(self._cairobj, c_text, len(c_text), ct.byref(c_glyphs), nr_glyphs, ct.byref(c_clusters), nr_clusters, cluster_flags)
        return \
            self
    #end show_text_glyphs

    @property
    def font_extents(self) :
        "returns a FontExtents object giving information about the current font settings."
        result = CAIRO.font_extents_t()
        cairo.cairo_font_extents(self._cairobj, ct.byref(result))
        return \
            FontExtents.from_cairo(result)
    #end font_extents

    def text_extents(self, text) :
        "returns a TextExtents object giving information about drawing the" \
        " specified text at the current font settings."
        result = CAIRO.text_extents_t()
        c_text = text.encode()
        cairo.cairo_text_extents(self._cairobj, c_text, ct.byref(result))
        return \
            TextExtents.from_cairo(result)
    #end text_extents

    def glyph_extents(self, glyphs) :
        "returns a TextExtents object giving information about drawing the" \
        " specified sequence of Glyphs at the current font settings."
        buf, nr_glyphs = glyphs_to_cairo(glyphs)
        result = CAIRO.text_extents_t()
        cairo.cairo_glyph_extents(self._cairobj, buf, nr_glyphs, ct.byref(result))
        return \
            TextExtents.from_cairo(result)
    #end glyph_extents

#end Context

def file_write_func(fileobj) :
    "fileobj must have a .write method that accepts a single bytes argument." \
    " This function returns a write_func that can be passed to the various" \
    " create_for_xxx_stream and write_to_xxx_stream methods which will write" \
    " the data to the file object. The write_func ignores its closure argument," \
    " so feel free to pass None for that."

    def write_data(_, data, length) :
        buf = array.array("B", (0,) * length)
        ct.memmove(buf.buffer_info()[0], data, length)
        fileobj.write(buf.tobytes())
        return \
            CAIRO.STATUS_SUCCESS
    #end write_data

#begin file_write_func
    return \
        write_data
#end file_write_func

class Surface :
    "base class for Cairo surfaces. Do not instantiate directly; use create methods" \
    " provided by subclasses."
    # <http://cairographics.org/manual/cairo-cairo-surface-t.html>

    __slots__ = ("_cairobj", "_user_data", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this Surface.
        check(cairo.cairo_surface_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_surface_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_surface_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @property
    def type(self) :
        "returns the surface type code CAIRO.SURFACE_TYPE_xxx."
        return \
            cairo.cairo_surface_get_type(self._cairobj)
    #end type

    def create_similar(self, content, dimensions) :
        "creates a new Surface with the specified Vector dimensions, which is as" \
        " compatible as possible with this one. content is a CAIRO.CONTENT_xxx value."
        dimensions = round(Vector.from_tuple(dimensions))
        return \
            type(self)(cairo.cairo_surface_create_similar(self._cairobj, content, dimensions.x, dimensions.y))
            # fixme: need to choose right Surface subclass based on result surface type
    #end create_similar

    def create_similar_image(self, format, dimensions) :
        "creates an ImageSurface with the specified CAIRO.FORMAT_xxx format and Vector" \
        " dimensions that is as compatible as possible with this one."
        dimensions = round(Vector.from_tuple(dimensions))
        return \
            ImageSurface(cairo.cairo_surface_create_similar_image(self._cairobj, format, dimensions.x, dimensions.y))
    #end create_similar_image

    def create_for_rectangle(self, bounds) :
        "creates a new Surface where drawing is strictly limited to the bounds Rect" \
        " within this one."
        return \
            type(self)(cairo.cairo_surface_create_for_rectangle(self._cairobj, bounds.left, bounds.top, bounds.width, bounds.height))
            # assumes it returns same type of surface as self!
    #end create_for_rectangle

    def flush(self) :
        "ensures that Cairo has finished all drawing to this Surface, restoring" \
        " any temporary modifications made to its state."
        cairo.cairo_surface_flush(self._cairobj)
        return \
            self
    #end flush

    @property
    def device(self) :
        "returns the Device for this Surface."
        result = cairo.cairo_surface_get_device(self._cairobj)
        if result != None :
            result = Device(cairo.cairo_device_reference(result))
        #end if
        return \
            result
    #end device

    @property
    def font_options(self) :
        "returns a copy of the font_options for this Surface."
        result = FontOptions.create()
        cairo.cairo_surface_get_font_options(self._cairobj, result._cairobj)
        return \
            result
    #end font_options

    @property
    def content(self) :
        "returns the content code CAIRO.CONTENT_xxx for this Surface."
        return \
            cairo.cairo_surface_get_content(self._cairobj)
    #end content

    def mark_dirty(self) :
        "tells Cairo that you have modified the Surface in some way outside Cairo."
        cairo.cairo_surface_mark_dirty(self._cairobj)
        self._check()
        return \
            self
    #end mark_dirty

    def mark_dirty_rectangle(self, rect) :
        "tells Cairo that you have modified the specified Rect portion of the Surface" \
        " in some way outside Cairo."
        rect.assert_isint()
        cairo.cairo_surface_mark_dirty_rectangle(self._cairobj, rect.left, rect.top, rect.width, rect.height)
        self._check()
        return \
            self
    #end mark_dirty_rectangle

    @property
    def device_offset(self) :
        "the current device offset as a Vector."
        x = ct.c_double()
        y = ct.c_double()
        cairo.cairo_surface_get_device_offset(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end device_offset

    @device_offset.setter
    def device_offset(self, offset) :
        self.set_device_offset(offset)
    #end device_offset

    def set_device_offset(self, offset) :
        "sets a new device offset Vector. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the device_offset property."
        offset = Vector.from_tuple(offset)
        cairo.cairo_surface_set_device_offset(self._cairobj, offset.x, offset.y)
        self._check()
        return \
            self
    #end device_offset

    @property
    def device_scale(self) :
        "the current device scale as a Vector."
        x = ct.c_double()
        y = ct.c_double()
        cairo.cairo_surface_get_device_scale(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end device_scale

    @device_scale.setter
    def device_scale(self, scale) :
        self.set_device_scale(scale)
    #end device_scale

    def set_device_scale(self, scale) :
        "sets a new device scale Vector. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the device_scale property."
        scale = Vector.from_tuple(scale)
        cairo.cairo_surface_set_device_scale(self._cairobj, scale.x, scale.y)
        self._check()
        return \
            self
    #end device_scale

    @property
    def fallback_resolution(self) :
        "the current device fallback_resolution as a Vector."
        x = ct.c_double()
        y = ct.c_double()
        cairo.cairo_surface_get_fallback_resolution(self._cairobj, ct.byref(x), ct.byref(y))
        return \
            Vector(x.value, y.value)
    #end fallback_resolution

    @fallback_resolution.setter
    def fallback_resolution(self, fallback_resolution) :
        self.set_fallback_resolution(fallback_resolution)
    #end fallback_resolution

    def set_fallback_resolution(self, fallback_resolution) :
        "sets a new device fallback_resolution Vector. Use for method chaining;" \
        " otherwise, it’s  probably more convenient to assign to the" \
        " fallback_resolution property."
        fallback_resolution = Vector.from_tuple(fallback_resolution)
        cairo.cairo_surface_set_fallback_resolution(self._cairobj, fallback_resolution.x, fallback_resolution.y)
        self._check()
        return \
            self
    #end fallback_resolution

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    @property
    def has_show_text_glyphs(self) :
        return \
            cairo.cairo_surface_has_show_text_glyphs(self._cairobj)
    #end has_show_text_glyphs

    # TODO: mime_data, map/unmap image
    # <http://cairographics.org/manual/cairo-cairo-surface-t.html>

    def copy_page(self) :
        "emits the current page for Surfaces that support multiple pages."
        cairo.cairo_surface_copy_page(self._cairobj)
        self._check()
        return \
            self
    #end copy_page

    def show_page(self) :
        "emits and clears the current page for Surfaces that support multiple pages."
        cairo.cairo_surface_show_page(self._cairobj)
        self._check()
        return \
            self
    #end show_page

    def write_to_png(self, filename) :
        c_filename = filename.encode()
        check(cairo.cairo_surface_write_to_png(self._cairobj, c_filename))
        return \
            self
    #end write_to_png

    def write_to_png_stream(self, write_func, closure) :
        "direct low-level interface to cairo_image_surface_write_to_png_stream." \
        " write_func must match signature of CAIRO.write_func_t, while closure is a" \
        " ctypes.c_void_p."
        c_write_func = CAIRO.write_func_t(write_func)
        check(cairo.cairo_surface_write_to_png_stream(self._cairobj, c_write_func, closure))
        return \
            self
    #end write_to_png_stream

    def write_to_png_file(self, outfile) :
        "converts the contents of the Surface to a sequence of PNG bytes which" \
        " is written to the specified file-like object. For io.IOBase and subclasses," \
        " this should be faster than using write_to_png_stream."

        def write_data(_, data, length) :
            s = ct.string_at(data, length)
            outfile.write(s)
            return \
                CAIRO.STATUS_SUCCESS
        #end write_data

    #begin write_to_png_file
        self.write_to_png_stream(write_data, None)
    #end write_to_png_file

    def to_png_bytes(self) :
        "converts the contents of the Surface to a sequence of PNG bytes which" \
        " is returned."
        buf = io.BytesIO()
        self.write_to_png_file(buf)
        return \
            buf.getvalue()
    #end to_png_bytes

#end Surface

class ImageSurface(Surface) :
    "A Cairo image surface. Do not instantiate directly; instead," \
    " call one of the create methods."

    __slots__ = () # to forestall typos

    max_dimensions = Vector(32767, 32767) # largest image Cairo will let me create

    @classmethod
    def create(celf, format, dimensions) :
        "creates a new ImageSurface with dynamically-allocated memory for the pixels." \
        " dimensions can be a Vector or a (width, height) tuple."
        dimensions = Vector.from_tuple(dimensions).assert_isint()
        return \
            celf(cairo.cairo_image_surface_create(format, dimensions.x, dimensions.y))
    #end create

    def create_like(self) :
        "convenience method which creates an ImageSurface with the same format and" \
        " dimensions as this one."
        return \
            type(self).create(self.format, self.dimensions)
    #end create_like

    @classmethod
    def create_from_png(celf, filename) :
        "loads an image from a PNG file and creates an ImageSurface for it."
        c_filename = filename.encode()
        return \
            celf(cairo.cairo_image_surface_create_from_png(c_filename))
    #end create_from_png

    @classmethod
    def create_from_png_stream(celf, read_func, closure) :
        "direct low-level interface to cairo_image_surface_create_from_png_stream." \
        " read_func must match signature CAIRO.read_func_t, while closure is a ctypes.c_void_p."
        c_read_func = CAIRO.read_func_t(read_func)
        return \
            celf(cairo.cairo_image_surface_create_from_png_stream(c_read_func, closure))
    #end create_from_png_stream

    @classmethod
    def create_from_png_bytes(celf, data) :
        "creates an ImageSurface from a PNG-format data sequence. This can be" \
        " of the bytes or bytearray types, or an array.array with \"B\" type code."

        offset = 0
        baseadr = None

        def read_data(_, buf, length) :
            nonlocal offset
            if offset + length <= len(data) :
                ct.memmove(buf, baseadr + offset, length)
                offset += length
                status = CAIRO.STATUS_SUCCESS
            else :
                status = CAIRO.STATUS_READ_ERROR
            #end if
            return \
                status
        #end read_data

    #begin create_from_png_bytes
        if isinstance(data, bytes) :
            baseadr = ct.cast(data, ct.c_void_p).value
        elif isinstance(data, bytearray) :
            baseadr = ct.addressof((ct.c_char * len(data)).from_buffer(data))
        elif isinstance(data, array.array) and data.typecode == "B" :
            baseadr = data.buffer_info()[0]
        else :
            raise TypeError("data is not bytes, bytearray or array.array of bytes")
        #end if
        return \
            celf.create_from_png_stream(read_data, None)
    #end create_from_png_bytes

    @classmethod
    def create_for_array(celf, arr, format, dimensions, stride) :
        "calls cairo_image_surface_create_for_data on arr, which must be" \
        " a Python array.array object."
        width, height = Vector.from_tuple(dimensions)
        address, length = arr.buffer_info()
        assert height * stride <= length * arr.itemsize
        result = celf(cairo.cairo_image_surface_create_for_data(ct.c_void_p(address), format, width, height, stride))
        _dependent_src[result] = arr
          # to ensure it doesn't go away prematurely, as long as this
          # ImageSurface object exists.
        return \
            result
    #end create_for_array

    @classmethod
    def create_for_data(celf, data, format, dimensions, stride) :
        "LOW-LEVEL: calls cairo_image_surface_create_for_data with an arbitrary" \
        " data address."
        width, height = Vector.from_tuple(dimensions)
        return \
            celf(cairo.cairo_image_surface_create_for_data(data, format, width, height, stride))
    #end create_for_data

    @property
    def data(self) :
        "LOW-LEVEL: the data address."
        return \
            cairo.cairo_image_surface_get_data(self._cairobj)
    #end data

    @staticmethod
    def format_stride_for_width(format, width) :
        "returns a suitable stride value (number of bytes per row of pixels) for" \
        " an ImageSurface with the specified format CAIRO.FORMAT_xxx and pixel width."
        return \
            cairo.cairo_format_stride_for_width(format, width)
    #end format_stride_for_width

    @property
    def format(self) :
        "the pixel format CAIRO.FORMAT_xxx."
        result = cairo.cairo_image_surface_get_format(self._cairobj)
        self._check()
        return \
            result
    #end format

    @property
    def width(self) :
        "the width in pixels."
        result = cairo.cairo_image_surface_get_width(self._cairobj)
        self._check()
        return \
            result
    #end width

    @property
    def height(self) :
        "the height in pixels."
        result = cairo.cairo_image_surface_get_height(self._cairobj)
        self._check()
        return \
            result
    #end height

    @property
    def dimensions(self) :
        "the dimensions in pixels, as a Vector."
        return \
            Vector(self.width, self.height)
    #end dimensions

    @property
    def stride(self) :
        "the number of bytes per row of pixels."
        result = cairo.cairo_image_surface_get_stride(self._cairobj)
        self._check()
        return \
            result
    #end stride

#end ImageSurface

class PDFSurface(Surface) :
    "A Cairo surface that outputs its renderings to a PDF file. Do not instantiate" \
    " directly; use one of the create methods."

    __slots__ = ("_write_func",) # to forestall typos

    @classmethod
    def create(celf, filename, dimensions_in_points) :
        "creates a PDF surface that outputs to the specified file, with the dimensions" \
        " of each page given by the Vector dimensions_in_points."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_filename = filename.encode()
        return \
            celf(cairo.cairo_pdf_surface_create(c_filename, dimensions_in_points.x, dimensions_in_points.y))
    #end create

    @classmethod
    def create_for_stream(celf, write_func, closure, dimensions_in_points) :
        "direct low-level interface to cairo_pdf_surface_create_for_stream." \
        " write_func must match signature of CAIRO.write_func_t, while closure is a" \
        " ctypes.c_void_p."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_write_func = CAIRO.write_func_t(write_func)
        result = celf \
          (
            cairo.cairo_pdf_surface_create_for_stream
              (
                c_write_func,
                closure,
                dimensions_in_points.x,
                dimensions_in_points.y
              )
          )
        result._write_func = c_write_func
          # to ensure it doesn’t disappear unexpectedly
        return \
            result
    #end create_for_stream

    @classmethod
    def create_for_file(celf, outfile, dimensions_in_points) :
        "creates a PDF surface that outputs to the specified file-like object." \
        " For io.IOBase and subclasses, this should be faster than using create_for_stream."

        def write_data(_, data, length) :
            s = ct.string_at(data, length)
            outfile.write(s)
            return \
                CAIRO.STATUS_SUCCESS
        #end write_data

    #begin create_for_file
        return \
            celf.create_for_stream(write_data, None, dimensions_in_points)
    #end create_for_file

    def restrict_to_version(self, version) :
        "restricts the version of PDF file created. If used, should" \
        " be called before any actual drawing is done."
        cairo.cairo_pdf_surface_restrict_to_version(self._cairobj, version)
        self._check()
        return \
            self
    #end restrict_to_version

    @staticmethod
    def get_versions() :
        "returns a tuple of supported PDF version number codes CAIRO.PDF_VERSION_xxx."
        versions = ct.POINTER(ct.c_int)()
        num_versions = ct.c_int()
        cairo.cairo_pdf_get_versions(ct.byref(versions), ct.byref(num_versions))
        return \
            tuple(versions[i] for i in range(num_versions.value))
    #end get_versions

    @staticmethod
    def version_to_string(version) :
        "returns the canonical version string for the specified PDF" \
        " version code CAIRO.PDF_VERSION_xxx."
        result = cairo.cairo_pdf_version_to_string(version)
        if bool(result) :
            result = result.decode("utf-8")
        else :
            result = None
        #end if
        return \
            result
    #end version_to_string

    def set_size(self, dimensions_in_points) :
        "resizes the page. Must be empty at this point (e.g. immediately" \
        " after show_page or initial creation)."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        cairo.cairo_pdf_surface_set_size(self._cairobj, dimensions_in_points.x, dimensions_in_points.y)
        self._check()
        return \
            self
    #end set_size

    if hasattr(cairo, "cairo_pdf_surface_add_outline") : # since 1.16

        def add_outline(self, parent_id, text, link_attribs, flags) :
            c_text = text.encode()
            c_link_attribs = link_attribs.encode()
            return \
                cairo.cairo_pdf_surface_add_outline \
                  (
                    self._cairobj,
                    parent_id,
                    c_text,
                    c_link_attribs,
                    flags
                  )
        #end add_outline

        def set_metadata(self, metadata, text) :
            c_text = text.encode()
            cairo.cairo_pdf_surface_set_metadata(self._cairobj, metadata, c_text)
        #end set_metadata

        def set_page_label(self, text) :
            c_text = text.encode()
            cairo.cairo_pdf_surface_set_page_label(self._cairobj, c_text)
        #end set_page_label

        def set_thumbnail_size(self, dimensions) :
            width, height = Vector.from_tuple(dimensions)
            cairo.cairo_pdf_surface_set_thumbnail_size(self._cairobj, width, height)
        #end set_thumbnail_size

    #end if

#end PDFSurface

class PSSurface(Surface) :
    "a Cairo surface which translates drawing actions into PostScript program sequences." \
    " Do not instantiate directly; use one of the create methods."

    __slots__ = ("_write_func",) # to forestall typos

    @classmethod
    def create(celf, filename, dimensions_in_points) :
        "creates a PostScript surface that outputs to the specified file, with the dimensions" \
        " of each page given by the Vector dimensions_in_points."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_filename = filename.encode()
        return \
            celf(cairo.cairo_ps_surface_create(c_filename, dimensions_in_points.x, dimensions_in_points.y))
    #end create

    @classmethod
    def create_for_stream(celf, write_func, closure, dimensions_in_points) :
        "direct low-level interface to cairo_ps_surface_create_for_stream." \
        " write_func must match signature of CAIRO.write_func_t, while closure is a" \
        " ctypes.c_void_p."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_write_func = CAIRO.write_func_t(write_func)
        result = celf \
          (
            cairo.cairo_ps_surface_create_for_stream
              (
                c_write_func,
                closure,
                dimensions_in_points.x,
                dimensions_in_points.y
              )
          )
        result._write_func = c_write_func
          # to ensure it doesn’t disappear unexpectedly
        return \
            result
    #end create_for_stream

    @classmethod
    def create_for_file(celf, outfile, dimensions_in_points) :
        "creates a PostScript surface that outputs to the specified file-like object." \
        " For io.IOBase and subclasses, this should be faster than using create_for_stream."

        def write_data(_, data, length) :
            s = ct.string_at(data, length)
            outfile.write(s)
            return \
                CAIRO.STATUS_SUCCESS
        #end write_data

    #begin create_for_file
        return \
            celf.create_for_stream(write_data, None, dimensions_in_points)
    #end create_for_file

    def restrict_to_level(self, level) :
        "restricts the language level of PostScript created, one of the CAIRO.PS_LEVEL_xxx" \
        " codes. If used, should be called before any actual drawing is done."
        cairo.cairo_ps_surface_restrict_to_level(self._cairobj, level)
        self._check()
        return \
            self
    #end restrict_to_level

    @staticmethod
    def get_levels() :
        "returns a tuple of supported PostScript language level codes CAIRO.PS_LEVEL_xxx."
        levels = ct.POINTER(ct.c_int)()
        num_levels = ct.c_int()
        cairo.cairo_ps_get_levels(ct.byref(levels), ct.byref(num_levels))
        return \
            tuple(levels[i] for i in range(num_levels.value))
    #end get_levels

    @staticmethod
    def level_to_string(level) :
        "returns the canonical string for the specified PostScript" \
        " language level code CAIRO.PS_LEVEL_xxx."
        result = cairo.cairo_ps_level_to_string(level)
        if bool(result) :
            result = result.decode("utf-8")
        else :
            result = None
        #end if
        return \
            result
    #end level_to_string

    @property
    def eps(self) :
        "whether the Surface outputs Encapsulated PostScript."
        result = cairo.cairo_ps_surface_get_eps(self._cairobj)
        self._check()
        return \
            result
    #end eps

    @eps.setter
    def eps(self, eps) :
        self.set_eps(eps)
    #end eps

    def set_eps(self, eps) :
        "specifies whether the Surface outputs Encapsulated PostScript."
        cairo.cairo_ps_surface_set_eps(self._cairobj, eps)
        self._check()
        return \
            self
    #end set_eps

    def set_size(self, dimensions_in_points) :
        "resizes the page. Must be empty at this point (e.g. immediately" \
        " after show_page or initial creation)."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        cairo.cairo_ps_surface_set_size(self._cairobj, dimensions_in_points.x, dimensions_in_points.y)
        self._check()
        return \
            self
    #end set_size

    def dsc_begin_setup(self) :
        "indicates that subsequent calls to dsc_comment should go to the Setup section."
        cairo.cairo_ps_surface_dsc_begin_setup(self._cairobj)
        self._check()
        return \
            self
    #end dsc_begin_setup

    def dsc_begin_page_setup(self) :
        "indicates that subsequent calls to dsc_comment should go to the PageSetup section."
        cairo.cairo_ps_surface_dsc_begin_page_setup(self._cairobj)
        self._check()
        return \
            self
    #end dsc_begin_page_setup

    def dsc_comment(self, comment) :
        "emits a DSC comment."
        c_comment = comment.encode()
        cairo.cairo_ps_surface_dsc_comment(self._cairobj, c_comment)
        self._check()
        return \
            self
    #end dsc_comment

#end PSSurface

class RecordingSurface(Surface) :
    "a Surface that records the sequence of drawing calls made into it" \
    " and plays them back when used as a source Pattern. Do not instantiate" \
    " directly; use the create method."

    __slots__ = () # to forestall typos

    @classmethod
    def create(celf, content, extents = None) :
        "content is a CAIRO.CONTENT_xxx value, and extents is an optional" \
        " Rect defining the drawing extents. If omitted, the extents are unbounded."
        if extents != None :
            extents = extents.to_cairo()
            extentsarg = ct.byref(extents)
        else :
            extentsarg = None
        #end if
        return \
            celf(cairo.cairo_recording_surface_create(content, extentsarg))
    #end create

    @property
    def ink_extents(self) :
        "the extents of the operations recorded, as a Rect."
        x0 = ct.c_double()
        y0 = ct.c_double()
        width = ct.c_double()
        height = ct.c_double()
        cairo.cairo_recording_surface_ink_extents(self._cairobj, ct.byref(x0), ct.byref(y0), ct.byref(width), ct.byref(height))
        return \
            Rect(x0.value, y0.value, width.value, height.value)
    #end ink_extents

    @property
    def extents(self) :
        "the original extents the surface was created with as a Rect, or None if unbounded."
        result = CAIRO.rectangle_t()
        if cairo.cairo_recording_surface_get_extents(self._cairobj, ct.byref(result)) :
            result = Rect.from_cairo(result)
        else :
            result = None
        #end if
        return \
            result
    #end extents

#end RecordingSurface

class SVGSurface(Surface) :
    "Surface that writes its contents to an SVG file. Do not instantiate directly;" \
    " use one of the create methods."

    __slots__ = ("_write_func",) # to forestall typos

    @classmethod
    def create(celf, filename, dimensions_in_points) :
        "creates an SVG surface that outputs to the specified file, with the dimensions" \
        " of each page given by the Vector dimensions_in_points."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_filename = filename.encode()
        return \
            celf(cairo.cairo_svg_surface_create(c_filename, dimensions_in_points.x, dimensions_in_points.y))
    #end create

    @classmethod
    def create_for_stream(celf, write_func, closure, dimensions_in_points) :
        "direct low-level interface to cairo_svg_surface_create_for_stream." \
        " write_func must match signature of CAIRO.write_func_t, while closure is a" \
        " ctypes.c_void_p."
        dimensions_in_points = Vector.from_tuple(dimensions_in_points)
        c_write_func = CAIRO.write_func_t(write_func)
        result = celf \
          (
            cairo.cairo_svg_surface_create_for_stream
              (
                c_write_func,
                closure,
                dimensions_in_points.x,
                dimensions_in_points.y
              )
          )
        result._write_func = c_write_func
          # to ensure it doesn’t disappear unexpectedly
        return \
            result
    #end create_for_stream

    @classmethod
    def create_for_file(celf, outfile, dimensions_in_points) :
        "creates an SVG surface that outputs to the specified file-like object." \
        " For io.IOBase and subclasses, this should be faster than using create_for_stream."

        def write_data(_, data, length) :
            s = ct.string_at(data, length)
            outfile.write(s)
            return \
                CAIRO.STATUS_SUCCESS
        #end write_data

    #begin create_for_file
        return \
            celf.create_for_stream(write_data, None, dimensions_in_points)
    #end create_for_file

    def restrict_to_version(self, version) :
        "restricts the version of SVG file created. If used, must" \
        " be called before any actual drawing is done."
        cairo.cairo_svg_surface_restrict_to_version(self._cairobj, version)
        self._check()
        return \
            self
    #end restrict_to_version

    @staticmethod
    def get_versions() :
        "returns a tuple of supported SVG version number codes CAIRO.SVG_VERSION_xxx."
        versions = ct.POINTER(ct.c_int)()
        num_versions = ct.c_int()
        cairo.cairo_svg_get_versions(ct.byref(versions), ct.byref(num_versions))
        return \
            tuple(versions[i] for i in range(num_versions.value))
    #end get_versions

    @staticmethod
    def version_to_string(version) :
        "returns the canonical version string for the specified SVG" \
        " version code CAIRO.SVG_VERSION_xxx."
        result = cairo.cairo_svg_version_to_string(version)
        if bool(result) :
            result = result.decode("utf-8")
        else :
            result = None
        #end if
        return \
            result
    #end version_to_string

    if hasattr(cairo, "cairo_svg_surface_set_document_unit") : # since 1.16

        @property
        def document_unit(self) :
            return \
                cairo.cairo_svg_surface_get_document_unit(self._cairobj)
        #end document_unit

        @document_unit.setter
        def document_unit(self, unit) :
            self.set_document_unit(unit)
        #end document_unit

        def set_document_unit(self, unit) :
            cairo.cairo_svg_surface_set_document_unit(self._cairobj, unit)
        #end set_document_unit

    #end if

#end SVGSurface

class Device :
    "a Cairo device_t object. Do not instantiate directly; get from Surface.device" \
    " or ScriptDevice.create."
    # <http://cairographics.org/manual/cairo-cairo-device-t.html>

    __slots__ = ("_cairobj", "_user_data", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this Surface.
        check(cairo.cairo_device_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_device_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_device_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @property
    def type(self) :
        "the type of the Device, a CAIRO.DEVICE_TYPE_xxx code."
        return \
            cairo.cairo_device_get_type(self._cairobj)
    #end type

    # TODO: acquire, release, observer stuff

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    if HAS.XCB_SURFACE :
        # debug interface

        if HAS.XCB_SHM_FUNCTIONS :

            def xcb_debug_cap_xshm_version(self, major_version, minor_version) :
                cairo.cairo_xcb_device_debug_cap_xshm_version \
                  (
                    self._cairobj,
                    major_version,
                    minor_version
                  )
                self._check()
            #end xcb_debug_cap_xshm_version

        #end if

        def xcb_debug_cap_xrender_version(self, major_version, minor_version) :
            cairo.cairo_xcb_device_debug_cap_xrender_version \
              (
                self._cairobj,
                major_version,
                minor_version
              )
            self._check()
        #end xcb_debug_cap_xrender_version

        @property
        def xcb_debug_precision(self) :
            "-1 to choose value based on antialiasing mode, else set corresponding" \
            " PolyMode."
            result = cairo.cairo_xcb_device_debug_get_precision(self._cairobj)
            self._check()
            return \
                result
        #end xcb_debug_precision

        @xcb_debug_precision.setter
        def xcb_debug_precision(self, precision) :
            cairo.cairo_xcb_device_debug_set_precision(self._cairobj, precision)
            self._check()
        #end xcb_debug_precision

        @property
        def xcb_connection(self) :
            "note this returns a raw ctypes.c_void_p value."
            result = cairo.cairo_xcb_device_get_connection(self._cairobj)
            self._check()
            return \
                result
        #end xcb_connection

    #end if

    if HAS.XLIB_SURFACE :
        # debug interface

        def xlib_debug_cap_xrender_version(self, major_version, minor_version) :
            cairo.cairo_xcb_device_debug_cap_xrender_version(self._cairobj, major_version, minor_version)
        #end xlib_debug_cap_xrender_version

        @property
        def xlib_debug_precision(self) :
            "-1 means choose automatically based on anti-aliasing mode."
            result = cairo.cairo_xlib_device_debug_get_precision(self._cairobj)
            self._check()
            return \
                result
        #end xlib_debug_precision

        @xlib_debug_precision.setter
        def xlib_debug_precision(self, precision) :
            cairo.cairo_xlib_device_debug_set_precision(self._cairobj, precision)
            self._check()
        #end xlib_debug_precision

    #end if

#end Device

class ScriptDevice(Device) :
    "for rendering to replayable Cairo scripts."
    # <http://cairographics.org/manual/cairo-Script-Surfaces.html>

    __slots__ = ("_write_func",) # to forestall typos

    @classmethod
    def create(celf, filename) :
        "creates a ScriptDevice that outputs to the specified file."
        c_filename = filename.encode()
        return \
            celf(cairo.cairo_script_create(c_filename))
    #end create

    @classmethod
    def create_for_stream(celf, write_func, closure) :
        "direct low-level interface to cairo_script_create_for_stream." \
        " write_func must match signature of CAIRO.write_func_t, while closure is a" \
        " ctypes.c_void_p."
        c_write_func = CAIRO.write_func_t(write_func)
        result = celf(cairo.cairo_script_create_for_stream(c_write_func, closure))
        result._write_func = c_write_func
          # to ensure it doesn’t disappear unexpectedly
        return \
            result
    #end create_for_stream

    @classmethod
    def create_for_file(celf, outfile) :
        "creates a recording surface that outputs to the specified file-like object." \
        " For io.IOBase and subclasses, this should be faster than using create_for_stream."

        def write_data(_, data, length) :
            s = ct.string_at(data, length)
            outfile.write(s)
            return \
                CAIRO.STATUS_SUCCESS
        #end write_data

    #begin create_for_file
        return \
            celf.create_for_stream(write_data, None)
    #end create_for_file

    def from_recording_surface(self, recording_surface) :
        "converts the recorded operations in recording_surface (a RecordingSurface)" \
        " into a script."
        if not isinstance(recording_surface, RecordingSurface) :
            raise TypeError("recording_surface must be a RecordingSurface")
        #end if
        check(cairo.cairo_script_from_recording_surface(self._cairobj, recording_surface._cairobj))
    #end create_from_recording_surface

    @property
    def mode(self) :
        "the current mode CAIRO.SCRIPT_MODE_xxx value."
        return \
            cairo.cairo_script_get_mode(self._cairobj)
    #end mode

    @mode.setter
    def mode(self, mode) :
        cairo.cairo_script_set_mode(self._cairobj, mode)
        self._check()
    #end mode

    def surface_create(self, content, dimensions) :
        "creates a new Surface that will emit its rendering through this" \
        " ScriptDevice. content is a CAIRO.CONTENT_xxx value."
        dimensions = Vector.from_tuple(dimensions)
        return \
            Surface(cairo.cairo_script_surface_create(self._cairobj, content, dimensions.x, dimensions.y))
    #end surface_create

    def surface_create_for_target(self, target) :
        "creates a proxy Surface that will render to Surface target and record its" \
        " operations through this ScriptDevice."
        if not isinstance(target, Surface) :
            raise TypeError("target must be a Surface")
        #end if
        result = Surface(cairo.cairo_script_surface_create_for_target(self._cairobj, target._cairobj))
        _dependent_src[result] = _dependent_src.get(target)
          # to ensure any storage attached to it doesn't go away prematurely
        return \
            result
    #end surface_create_for_target

    def write_comment(self, comment) :
        "writes a comment to the script. comment can be a string or bytes."
        if isinstance(comment, str) :
            comment = comment.encode("utf-8")
        elif not isinstance(comment, bytes) :
            raise TypeError("comment must be str or bytes")
        #end if
        c_comment = (ct.c_ubyte * len(comment))()
        for i in range(len(comment)) :
            c_comment[i] = comment[i]
        #end for
        cairo.cairo_script_write_comment(self._cairobj, ct.byref(c_comment), len(comment))
    #end write_comment

#end ScriptDevice

class Colour :
    "a representation of a colour plus alpha, convertible to/from the various colour" \
    " spaces available in the Python colorsys module. Internal representation is" \
    " always (r, g, b, a)."

    __slots__ = ("r", "g", "b", "a") # to forestall typos

    # to allow referencing colour components by name:
    RGBA = namedtuple("RGBA", ("r", "g", "b", "a"))
    HSVA = namedtuple("HSVA", ("h", "s", "v", "a"))
    HLSA = namedtuple("HLSA", ("h", "l", "s", "a"))
    YIQA = namedtuple("YIQA", ("y", "i", "q", "a"))

    def __init__(self, r, g, b, a) :
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    #end __init__

    def __getitem__(self, i) :
        "being able to access elements by index allows a Colour to be cast to a tuple or list."
        return \
            (self.r, self.g, self.b, self.a)[i]
    #end __getitem__

    def __repr__(self) :
        return \
            "%s%s" % (type(self).__name__, repr(tuple(self)))
    #end __repr__

    if HAS.ISCLOSE :

        def iscloseto(c1, c2, rel_tol = default_rel_tol, abs_tol = default_abs_tol) :
            "approximate equality of two Colours to within the specified tolerances."
            return \
                (
                    math.isclose(c1.r, c2.r, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(c1.g, c2.g, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(c1.b, c2.b, rel_tol = rel_tol, abs_tol = abs_tol)
                and
                    math.isclose(c1.a, c2.a, rel_tol = rel_tol, abs_tol = abs_tol)
                )
        #end iscloseto

    #end if

    @classmethod
    def _alpha_tuple(celf, c, norm_hue = False) :
        # ensures that c is a tuple of 4 elements, appending a default alpha if omitted
        c = tuple(c)
        if len(c) == 3 :
            c = c + (1,) # default to full-opaque alpha
        elif len(c) != 4 :
            raise TypeError("colour tuple must have 3 or 4 elements")
        #end if
        if norm_hue :
            # first component is hue, normalize to [0, 1) range
            c = (c[0] % 1,) + c[1:]
        #end if
        return \
            c
    #end _alpha_tuple

    @classmethod
    def _convert_space(celf, c, conv, tupleclass = None, norm_hue = False) :
        # puts the non-alpha components of c through the conversion function conv
        # and returns the result with the alpha restored.
        c = celf._alpha_tuple(c, norm_hue)
        result = conv(*c[:3]) + (c[3],)
        if tupleclass != None :
            result = tupleclass(*result)
        #end if
        return \
            result
    #end _convert_space

    @classmethod
    def from_rgba(celf, c) :
        "constructs a Colour from an (r, g, b) or (r, g, b, a) tuple."
        return \
            celf(*celf._alpha_tuple(c))
    #end from_rgba

    @classmethod
    def from_hsva(celf, c) :
        "constructs a Colour from an (h, s, v) or (h, s, v, a) tuple."
        return \
            celf(*celf._convert_space(c, colorsys.hsv_to_rgb, norm_hue = True))
    #end from_hsva

    @classmethod
    def from_hlsa(celf, c) :
        "constructs a Colour from an (h, l, s) or (h, l, s, a) tuple."
        return \
            celf(*celf._convert_space(c, colorsys.hls_to_rgb, norm_hue = True))
    #end from_hlsa

    @classmethod
    def from_yiqa(celf, c) :
        "constructs a Colour from a (y, i, q) or (y, i, q, a) tuple."
        return \
            celf(*celf._convert_space(c, colorsys.yiq_to_rgb))
    #end from_yiqa

    @classmethod
    def grey(celf, i, a = 1) :
        "constructs a monochrome Colour with r, g and b components set to i" \
        " and alpha set to a."
        return \
            celf(i, i, i, a)
    #end grey

    def to_rgba(self) :
        "returns an (r, g, b, a) namedtuple."
        return \
            self.RGBA(*tuple(self))
    #end to_rgba

    def to_hsva(self) :
        "returns an (h, s, v, a) namedtuple."
        return \
            type(self)._convert_space(self, colorsys.rgb_to_hsv, self.HSVA)
    #end to_hsva

    def to_hlsa(self) :
        "returns an (h, l, s, a) namedtuple."
        return \
            type(self)._convert_space(self, colorsys.rgb_to_hls, self.HLSA)
    #end to_hlsa

    def to_yiqa(self) :
        "returns a (y, i, q, a) namedtuple."
        return \
            type(self)._convert_space(self, colorsys.rgb_to_yiq, self.YIQA)
    #end to_yiqa

    @staticmethod
    def _replace_components(construct, old_components, new_components) :
        # replaces components in 4-tuple old_components with corresponding values
        # from new_components where latter are not None, and passes resulting
        # tuple to construct, returning the result.
        return \
            construct \
              (
                (
                    lambda : c1[j],
                    lambda : c2[j],
                    lambda : c2[j](c1[j]),
                )[callable(c2[j]) + (c2[j] != None)]()
                for c1 in (old_components,)
                for c2 in (new_components,)
                for j in range(4)
              )
    #end _replace_components

    def replace_rgba(self, r = None, g = None, b = None, a = None) :
        "returns a new Colour with the specified (r, g, b, a) components replaced with new" \
        " values. Each arg can be a real number, or a function of a single real argument" \
        " that, given the old component value, returns the new component value."
        return \
            type(self)._replace_components(type(self).from_rgba, self.to_rgba(), (r, g, b, a))
    #end replace_rgba

    def replace_hsva(self, h = None, s = None, v = None, a = None) :
        "returns a new Colour with the specified (h, s, v, a) components replaced with new" \
        " values. Each arg can be a real number, or a function of a single real argument" \
        " that, given the old component value, returns the new component value."
        return \
            type(self)._replace_components(type(self).from_hsva, self.to_hsva(), (h, s, v, a))
    #end replace_hsva

    def replace_hlsa(self, h = None, l = None, s = None, a = None) :
        "returns a new Colour with the specified (h, l, s, a) components replaced with new" \
        " values. Each arg can be a real number, or a function of a single real argument" \
        " that, given the old component value, returns the new component value."
        return \
            type(self)._replace_components(type(self).from_hlsa, self.to_hlsa(), (h, l, s, a))
    #end replace_hlsa

    def replace_yiqa(self, y = None, i = None, q = None, a = None) :
        "returns a new Colour with the specified (y, i, q, a) components replaced with new" \
        " values. Each arg can be a real number, or a function of a single real argument" \
        " that, given the old component value, returns the new component value."
        return \
            type(self)._replace_components(type(self).from_yiqa, self.to_yiqa(), (y, i, q, a))
    #end replace_yiqa

    def combine(self, other, rgb_func, alpha_func) :
        "produces a combination of this Colour with other by applying the specified" \
        " functions on the respective components. rgb_func must take four arguments" \
        " (ac, aa, bc, ba), where ac and bc are the corresponding colour components" \
        " (r, g or b) and aa and ba are the alphas, and returns a new value for that" \
        " colour component. alpha_func takes two arguments (aa, ba), being the alpha" \
        " values, and returns the new alpha."
        return \
            type(self) \
              (
                r = rgb_func(self.r, self.a, other.r, other.a),
                g = rgb_func(self.g, self.a, other.g, other.a),
                b = rgb_func(self.b, self.a, other.b, other.a),
                a = alpha_func(self.a, other.a)
              )
    #end combine

    def mix(self, other, amt) :
        "returns a mixture of this Colour with other in the proportion given by amt;" \
        " if amt is 0, then the result is purely this colour, while if amt is 1, then" \
        " it is purely other."
        return \
            self.combine \
              (
                other = other,
                rgb_func = lambda ac, aa, bc, ba : interp(amt, ac, bc),
                alpha_func = lambda aa, ba : interp(amt, aa, ba)
              )
    #end mix

    class X11_Colours :
        "a dictionary mapping the X11 colour names to their standard values."

        colours_filename = "/usr/share/X11/rgb.txt"

        class NamedColour :
            "stores the colour with its name in the original case, while allowing" \
            " case-insensitive dictionary lookup."

            __slots__ = ("name", "colour")

            def __init__(self, name, colour) :
                self.name = name
                self.colour = colour
            #end __init__

            @property
            def contents(self) :
                return \
                    (self.name, self.colour)
            #end contents

        #end NamedColour

        def __init__(self) :
            self._colours = None
        #end __init__

        class DictView :
            "behaves like a dictionary view object. The point of doing this is so" \
            " the caller can find colours with case-insensitive names, while seeing" \
            " the original case in the names when enumerating colours."

            def __init__(self, parent, view_method, repr_name, attr_name) :
                # _parent is the underlying dict;
                # view_method is the method to call on _parent;
                # repr_name is the type name to use in the repr string
                # (follow same names used by dict);
                # attr_name is name of attribute of NamedColour objects to retrieve
                self._parent = parent
                self.view_method = view_method
                self.repr_name = repr_name
                self.attr_name = attr_name
            #end __init

            def __len__(self) :
                return \
                    len(self._parent)
            #end __len__

            def __iter__(self) :
                for item in self._parent.values() :
                    yield getattr(item, self.attr_name)
                #end for
            #end __iter__

            def __contains__(self, item) :
                return \
                    item in getattr(self._parent, self.view_method)()
            #end __contains__

            def __repr__(self) :
                return \
                    (
                            "%(name)s(%(items)s)"
                        %
                            {
                                "name" : self.repr_name,
                                "items" : "[%s]" % ", ".join
                                  (
                                    repr(getattr(item, self.attr_name))
                                    for item in self._parent.values()
                                  ),
                            }
                    )
            #end __repr__

        #end DictView

        def _load(self) :
            # one-shot method which loads the colours on demand.
            # Every user-accessible method has to call this.
            colours = {}
            seen = set() # so I prefer unconverted names in case of duplicate entries
              # (not that there actually are any duplicate entries)
            NamedColour = type(self).NamedColour
            try :
                for line in open(self.colours_filename, "r") :
                    if not line.startswith("!") :
                        line = line.strip()
                        for junk in ("\t", "  ") :
                            while True :
                                line2 = line.replace(junk, " ")
                                if line2 == line :
                                    break
                                line = line2
                            #end while
                        #end for
                        r, g, b, name = line.split(" ", 3)
                        r, g, b = int(r), int(g), int(b)
                        lc_name = name.lower()
                        if name == lc_name or lc_name not in seen :
                            colours[lc_name] = NamedColour \
                              (
                                name = name,
                                colour = Colour.from_rgba((r / 255, g / 255, b / 255))
                              )
                            seen.add(lc_name)
                        #end if
                    #end if
                #end for
            except IOError :
                pass
            #end try
            self._colours = colours
            # easier reference to inner class names
            self.NamedColour = NamedColour
            self.DictView = type(self).DictView
            type(self)._load = lambda self : None # you don’t need me any more
        #end _load

        # add whatever dict-like methods are useful below

        def __getitem__(self, name) :
            self._load()
            return \
                self._colours[name.lower()].colour
        #end __getitem__

        def __len__(self) :
            self._load()
            return \
                len(self._colours)
        #end __len__

        def __iter__(self) :
            self._load()
            return \
                iter(self.keys())
        #end __iter__

        def __contains__(self, name) :
            self._load()
            return \
                name.lower() in self._colours
        #end __contains__

        def keys(self) :
            self._load()
            return \
                self.DictView \
                  (
                    parent = self._colours,
                    view_method = "keys",
                    repr_name = "dict_keys",
                    attr_name = "name"
                  )
        #end keys

        def values(self) :
            self._load()
            return \
                self.DictView \
                  (
                    parent = self._colours,
                    view_method = "values",
                    repr_name = "dict_values",
                    attr_name = "colour"
                  )
        #end values

        def items(self) :
            self._load()
            return \
                self.DictView \
                  (
                    parent = self._colours,
                    view_method = "items",
                    repr_name = "dict_items",
                    attr_name = "contents"
                  )
        #end items

        def __repr__(self) :
            self._load()
            return \
                repr(self.items())
        #end __repr__

    #end X11_Colours

    x11 = X11_Colours()

#end Colour

class Pattern :
    "a Cairo Pattern object. Do not instantiate directly; use one of the create methods."
    # <http://cairographics.org/manual/cairo-cairo-pattern-t.html>

    __slots__ = ("_cairobj", "_user_data", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this Pattern.
        check(cairo.cairo_pattern_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_pattern_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_pattern_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    def add_colour_stop(self, offset, c) :
        "adds a colour stop. This must be a gradient Pattern, offset is a number in [0, 1]" \
        " and c must be a Colour or tuple. Returns the same Pattern, to allow for" \
        " method chaining."
        cairo.cairo_pattern_add_color_stop_rgba(*((self._cairobj, offset) + tuple(Colour.from_rgba(c))))
        self._check()
        return \
            self
    #end add_colour_stop

    def add_colour_stops(self, stops) :
        "adds a whole lot of colour stops at once. stops must be a tuple, each" \
        "element of which must be an (offset, Colour) tuple."
        for offset, colour in stops :
            self.add_colour_stop(offset, colour)
        #end for
        return \
            self
    #end add_colour_stops

    @property
    def colour_stops(self) :
        "a tuple of the currently-defined (offset, Colour) colour stops. This must" \
        " be a gradient Pattern."
        count = ct.c_int()
        check(cairo.cairo_pattern_get_color_stop_count(self._cairobj, ct.byref(count)))
        count = count.value
        result = []
        offset = ct.c_double()
        r = ct.c_double()
        g = ct.c_double()
        b = ct.c_double()
        a = ct.c_double()
        for i in range(count) :
            check(cairo.cairo_pattern_get_color_stop_rgba(self._cairobj, i, ct.byref(offset), ct.byref(r), ct.byref(g), ct.byref(b), ct.byref(a)))
            result.append((offset.value, Colour(r.value, g.value, b.value, a.value)))
        #end for
        return \
            tuple(result)
    #end colour_stops

    @classmethod
    def create_colour(celf, c) :
        "creates a Pattern that paints the destination with the specified Colour."
        return \
            celf(cairo.cairo_pattern_create_rgba(*Colour.from_rgba(c).to_rgba()))
    #end create_rgb

    @property
    def colour(self) :
        "assumes the Pattern is a solid-colour pattern, returns its Colour."
        r = ct.c_double()
        g = ct.c_double()
        b = ct.c_double()
        a = ct.c_double()
        check(cairo.cairo_pattern_get_rgba(self._cairobj, ct.byref(r), ct.byref(g), ct.byref(g), ct.byref(a)))
        return \
            Colour(r.value, g.value, b.value, a.value)
    #end colour

    @classmethod
    def create_for_surface(celf, surface) :
        "creates a Pattern that takes its image from the specified Surface."
        if not isinstance(surface, Surface) :
            raise TypeError("surface is not a Surface")
        #end if
        result = celf(cairo.cairo_pattern_create_for_surface(surface._cairobj))
        _dependent_src[result] = _dependent_src.get(surface)
          # to ensure any storage attached to it doesn't go away prematurely
        return \
            result
    #end create_for_surface

    @property
    def surface(self) :
        "assuming there is a Surface for which this Pattern was created, returns the Surface."
        surf = ct.c_void_p()
        check(cairo.cairo_pattern_get_surface(self._cairobj, ct.byref(surf)))
        return \
            Surface(cairo.cairo_surface_reference(surf.value))
    #end surface

    @classmethod
    def create_linear(celf, p0, p1, colour_stops = None) :
        "creates a linear gradient Pattern that varies between the specified Vector" \
        " points in pattern space. colour_stops is an optional tuple of (offset, Colour)" \
        " to define the colour stops."
        p0 = Vector.from_tuple(p0)
        p1 = Vector.from_tuple(p1)
        result = celf(cairo.cairo_pattern_create_linear(p0.x, p0.y, p1.x, p1.y))
        if colour_stops != None :
            result.add_colour_stops(colour_stops)
        #end if
        return \
            result
    #end create_linear

    @property
    def linear_p0(self) :
        "the first Vector point for a linear gradient Pattern."
        x = ct.c_double()
        y = ct.c_double()
        check(cairo.cairo_pattern_get_linear_points(self._cairobj, ct.byref(x), ct.byref(y), None, None))
        return \
            Vector(x.value, y.value)
    #end linear_p0

    @property
    def linear_p1(self) :
        "the second Vector point for a linear gradient Pattern."
        x = ct.c_double()
        y = ct.c_double()
        check(cairo.cairo_pattern_get_linear_points(self._cairobj, None, None, ct.byref(x), ct.byref(y)))
        return \
            Vector(x.value, y.value)
    #end linear_p1

    @classmethod
    def create_radial(celf, c0, r0, c1, r1, colour_stops = None) :
        "creates a radial gradient Pattern varying between the circle centred at Vector c0," \
        " radius r0 and the one centred at Vector c1, radius r1. colour_stops is an optional" \
        " tuple of (offset, Colour) to define the colour stops."
        c0 = Vector.from_tuple(c0)
        c1 = Vector.from_tuple(c1)
        result = celf(cairo.cairo_pattern_create_radial(c0.x, c0.y, r0, c1.x, c1.y, r1))
        if colour_stops != None :
            result.add_colour_stops(colour_stops)
        #end if
        return \
            result
    #end create_radial

    @property
    def radial_c0(self) :
        "the centre of the start circle for a radial gradient Pattern."
        x = ct.c_double()
        y = ct.c_double()
        check(cairo.cairo_pattern_get_radial_circles(self._cairobj, ct.byref(x), ct.byref(y), None, None, None, None))
        return \
            Vector(x.value, y.value)
    #end radial_c0

    @property
    def radial_r0(self) :
        "the radius of the start circle for a radial gradient Pattern."
        r = ct.c_double()
        check(cairo.cairo_pattern_get_radial_circles(self._cairobj, None, None, ct.byref(r), None, None, None))
        return \
            r.value
    #end radial_r0

    @property
    def radial_c1(self) :
        "the centre of the end circle for a radial gradient Pattern."
        x = ct.c_double()
        y = ct.c_double()
        check(cairo.cairo_pattern_get_radial_circles(self._cairobj, None, None, None, ct.byref(x), ct.byref(y), None))
        return \
            Vector(x.value, y.value)
    #end radial_c1

    @property
    def radial_r1(self) :
        "the radius of the end circle for a radial gradient Pattern."
        r = ct.c_double()
        check(cairo.cairo_pattern_get_radial_circles(self._cairobj, None, None, None, None, None, ct.byref(r)))
        return \
            r.value
    #end radial_r1

    @property
    def extend(self) :
        "how to extend the Pattern to cover a larger area, as a CAIRO.EXTEND_xxx code." \
        " Note this is ignored for mesh patterns."
        return \
            cairo.cairo_pattern_get_extend(self._cairobj)
    #end extend

    @extend.setter
    def extend(self, ext) :
        self.set_extend(ext)
    #end extend

    def set_extend(self, ext) :
        "sets a new extend mode. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the extend property."
        cairo.cairo_pattern_set_extend(self._cairobj, ext)
        return \
            self
    #end set_extend

    @property
    def filter(self) :
        "how to resize the Pattern, as a CAIRO.FILTER_xxx code."
        return \
            cairo.cairo_pattern_get_filter(self._cairobj)
    #end filter

    @filter.setter
    def filter(self, filt) :
        self.set_filter(filt)
    #end filter

    def set_filter(self, filt) :
        "sets a new filter mode. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the filter property."
        cairo.cairo_pattern_set_filter(self._cairobj, filt)
        return \
            self
    #end set_filter

    @property
    def matrix(self) :
        "the transformation from user space to Pattern space."
        result = CAIRO.matrix_t()
        cairo.cairo_pattern_get_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end matrix

    @matrix.setter
    def matrix(self, m) :
        self.set_matrix(m)
    #end matrix

    def set_matrix(self, m) :
        "sets a new matrix. Use for method chaining; otherwise, it’s" \
        " probably more convenient to assign to the matrix property."
        m = m.to_cairo()
        cairo.cairo_pattern_set_matrix(self._cairobj, ct.byref(m))
        return \
            self
    #end set_matrix

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    # TODO: Raster Sources <http://cairographics.org/manual/cairo-Raster-Sources.html>

#end Pattern

class MeshPattern(Pattern) :
    "a Cairo tensor-product mesh pattern. Do not instantiate directly; use the create" \
    " method."
    # could let user instantiate directly, but having a create method
    # seems more consistent with behaviour of most other wrapper objects
    # (including superclass).

    __slots__ = () # to forestall typos

    @classmethod
    def create(celf) :
        "creates a new, empty MeshPattern."
        return \
            celf(cairo.cairo_pattern_create_mesh())
    #end create

    def begin_patch(self) :
        "starts defining a new patch for the MeshPattern. The sides of the patch" \
        " must be defined by one move_to followed by up to 4 line_to/curve_to calls."
        cairo.cairo_mesh_pattern_begin_patch(self._cairobj)
        self._check()
        return \
            self
    #end begin_patch

    def end_patch(self) :
        "finishes defining a patch for the MeshPattern."
        cairo.cairo_mesh_pattern_end_patch(self._cairobj)
        self._check()
        return \
            self
    #end end_patch

    def move_to(self, p) :
        "move_to(p) or move_to((x, y)) -- defines the start point for the sides of the patch."
        p = Vector.from_tuple(p)
        cairo.cairo_mesh_pattern_move_to(self._cairobj, p.x, p.y)
        self._check()
        return \
            self
    #end move_to

    def line_to(self, p) :
        "line_to(p) or line_to((x, y)) -- defines a straight-line side for the current patch."
        p = Vector.from_tuple(p)
        cairo.cairo_mesh_pattern_line_to(self._cairobj, p.x, p.y)
        self._check()
        return \
            self
    #end line_to

    def curve_to(self, p1, p2, p3) :
        "curve_to(p1, p2, p3) or curve_to((x1, y1), (x2, y2), (x3, y3))" \
        " -- defines a curved side for the current patch."
        p1 = Vector.from_tuple(p1)
        p2 = Vector.from_tuple(p2)
        p3 = Vector.from_tuple(p3)
        cairo.cairo_mesh_pattern_curve_to(self._cairobj, p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
        self._check()
        return \
            self
    #end curve_to

    def set_control_point(self, point_num, p) :
        "defines an interior control point, where point_num must be an integer in [0 .. 3]." \
        " Changing these from the default turns a Coons patch into a general tensor-product patch."
        p = Vector.from_tuple(p)
        cairo.cairo_mesh_pattern_set_control_point(self._cairobj, point_num, p.x, p.y)
        self._check()
        return \
            self
    #end set_control_point

    def set_corner_colour(self, corner_num, c) :
        "defines the Colour at one of the corners, where corner_num must be an integer" \
        " in [0 .. 3]. Any colours not set default to Colour.grey(0, 0)."
        c = Colour.from_rgba(c)
        cairo.cairo_mesh_pattern_set_corner_color_rgba(self._cairobj, corner_num, c.r, c.g, c.b, c.a)
        self._check()
        return \
            self
    #end set_corner_colour

    @property
    def patch_count(self) :
        "the count of patches defined for the MeshPattern."
        result = ct.c_uint()
        check(cairo.cairo_mesh_pattern_get_patch_count(self._cairobj, ct.byref(result)))
        return \
            result.value
    #end patch_count

    def get_path(self, patch_num) :
        "returns a Path defining the sides of the specified patch_num in [0 .. patch_count - 1]."
        temp = cairo.cairo_mesh_pattern_get_path(self._cairobj, patch_num)
        try :
            result = Path.from_cairo(temp)
        finally :
            cairo.cairo_path_destroy(temp)
        #end try
        return \
            result
    #end get_path

    def get_control_point(self, patch_num, point_num) :
        "returns a Vector for one of the interior control points of the specified" \
        " patch_num in [0 .. patch_count - 1], point_num in [0 .. 3]."
        x = ct.c_double()
        y = ct.c_double()
        check(cairo.cairo_mesh_pattern_get_control_point(self._cairobj, patch_num, point_num, ct.byref(x), ct.byref(y)))
        return \
            Vector(x.value, y.value)
    #end get_control_point

    def get_corner_colour(self, patch_num, corner_num) :
        "returns a Colour for one of the corners of the specified" \
        " patch_num in [0 .. patch_count - 1], corner_num in [0 .. 3]."
        r = ct.c_double()
        g = ct.c_double()
        b = ct.c_double()
        a = ct.c_double()
        check(cairo.cairo_mesh_pattern_get_corner_color_rgba(self._cairobj, patch_num, corner_num, ct.byref(r), ct.byref(g), ct.byref(b), ct.byref(a)))
        return \
            Colour(r.value, g.value, b.value, a.value)
    #end get_corner_colour

#end MeshPattern

class Region :
    "a Cairo region. Do not instantiate directly; use the create or copy methods."
    # <http://cairographics.org/manual/cairo-Regions.html>

    __slots__ = ("_cairobj", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
      # should I bother? regions cannot currently be attached to other objects.

    def _check(self) :
        # check for error from last operation on this Region.
        check(cairo.cairo_region_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            # self._user_data = {} # not defined for regions
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_region_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_region_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @classmethod
    def create(celf, initial = None) :
        "creates a new Region. If initial is not None, it must be a Rect or a tuple or" \
        " list of Rects specifying the initial extent of the Region. Otherwise, the" \
        " Region will be initially empty."
        if initial != None :
            if isinstance(initial, Rect) :
                c_rect = initial.to_cairo_int()
                result = cairo.cairo_region_create_rectangle(ct.byref(c_rect))
            elif isinstance(initial, tuple) or isinstance(initial, list) :
                count = len(initial)
                c_rects = (count * CAIRO.rectangle_int_t)()
                for i in range(count) :
                    c_rects[i] = initial[i].to_cairo_int()
                #end for
                result = cairo.cairo_region_create_rectangles(ct.byref(c_rects), count)
            else :
                raise TypeError("initial arg must be a Rect, a tuple/list of Rects or None")
            #end if
        else :
            result = cairo.cairo_region_create()
        #end if
        return \
            celf(result)
    #end create

    def copy(self) :
        "returns a new Region which is a copy of this one."
        return \
            type(self)(cairo.cairo_region_copy(self._cairobj))
    #end copy

    @property
    def extents(self) :
        "returns a Rect defining the extents of this Region."
        result = CAIRO.rectangle_int_t()
        cairo.cairo_region_get_extents(self._cairobj, ct.byref(result))
        return \
            Rect.from_cairo(result)
    #end extents

    @property
    def rectangles(self) :
        "iterates over the component Rects of this Region."
        rect = CAIRO.rectangle_int_t()
        for i in range(cairo.cairo_region_num_rectangles(self._cairobj)) :
            cairo.cairo_region_get_rectangle(self._cairobj, i, ct.byref(rect))
            yield Rect.from_cairo(rect)
        #end for
    #end rectangles

    @property
    def is_empty(self) :
        "is this Region empty."
        return \
            cairo.cairo_region_is_empty(self._cairobj)
    #end is_empty

    def contains_point(self, p) :
        "does this region contain the specified (integral) Vector point."
        p = Vector.from_tuple(p).assert_isint()
        return \
            cairo.cairo_region_contains_point(self._cairobj, p.x, p.y)
    #end contains_point

    def contains_rectangle(self, rect) :
        "returns a CAIRO.REGION_OVERLAP_xxx code indicating how the specified" \
        " Rect overlaps this Region."
        c_rect = rect.to_cairo_int()
        return \
            cairo.cairo_region_contains_rectangle(self._cairobj, ct.byref(c_rect))
    #end contains_rectangle

    def __eq__(r1, r2) :
        "equality of coverage of two Regions."
        return \
            isinstance(r2, Region) and cairo.cairo_region_equal(r1._cairobj, r2._cairobj)
    #end __eq__

    def __repr__(self) :
        "displays the rectangles making up this Region."
        return \
            "Region.create(%s)" % repr(list(self.rectangles))
    #end __repr__

    def translate(self, p) :
        "translates the Region by the specified (integral) Vector."
        p = Vector.from_tuple(p).assert_isint()
        cairo.cairo_region_translate(self._cairobj, p.x, p.y)
        return \
            self
    #end translate

    def intersect(self, other) :
        "replaces this Region with the intersection of itself and the" \
        " specified Rect or Region."
        if isinstance(other, Region) :
            check(cairo.cairo_region_intersect(self._cairobj, other._cairobj))
        elif isinstance(other, Rect) :
            c_rect = other.to_cairo_int()
            check(cairo.cairo_region_intersect_rectangle(self._cairobj, ct.byref(c_rect)))
        else :
            raise TypeError("can only intersect with another Rect or Region")
        #end if
        return \
            self
    #end intersect

    def subtract(self, other) :
        "subtracts the specified Rect or Region from this Region."
        if isinstance(other, Region) :
            check(cairo.cairo_region_subtract(self._cairobj, other._cairobj))
        elif isinstance(other, Rect) :
            c_rect = other.to_cairo_int()
            check(cairo.cairo_region_subtract_rectangle(self._cairobj, ct.byref(c_rect)))
        else :
            raise TypeError("can only subtract another Rect or Region")
        #end if
        return \
            self
    #end subtract

    def union(self, other) :
        "includes the specified Rect or Region in this Region."
        if isinstance(other, Region) :
            check(cairo.cairo_region_union(self._cairobj, other._cairobj))
        elif isinstance(other, Rect) :
            c_rect = other.to_cairo_int()
            check(cairo.cairo_region_union_rectangle(self._cairobj, ct.byref(c_rect)))
        else :
            raise TypeError("can only unite with another Rect or Region")
        #end if
        return \
            self
    #end union

    def xor(self, other) :
        "replaces this Region with the exclusive-or between itself and the" \
        " specified Rect or Region."
        if isinstance(other, Region) :
            check(cairo.cairo_region_xor(self._cairobj, other._cairobj))
        elif isinstance(other, Rect) :
            c_rect = other.to_cairo_int()
            check(cairo.cairo_region_xor_rectangle(self._cairobj, ct.byref(c_rect)))
        else :
            raise TypeError("can only xor with another Region")
        #end if
        return \
            self
    #end xor

#end Region

class Path :
    "a high-level representation of a Cairo path_t. Instantiate with a sequence" \
    " of Path.Segment objects, or use the from_cairo, from_elements or from_ft_outline" \
    " class methods.\n" \
    "\n" \
    " Elements are a representation of paths that correspond directly to Cairo" \
    " path-construction calls, while Segments are a simpler form for doing various" \
    " path manipulations. Conversions are provided in both directions."

    # Unfortunately I cannot provide a to_cairo method, because there is no
    # public Cairo call for allocating a cairo_path_data_t structure. So
    # the conversion from Cairo is one-way, and I have to implement all
    # the drawing from then on.

    __slots__ = ("segments",) # to forestall typos

    class Point :
        "a control point on a Path.Segment. “pt” is the Vector coordinate," \
        " and “off” is a boolean, True if the point is off-curve, False if" \
        " on-curve. Two successive on-curve points define a straight line;" \
        " one off-curve in-between defines a quadratic Bézier, while two" \
        " successive off-curve points in-between define a cubic Bézier."

        __slots__ = ("pt", "off")

        def __init__(self, pt, off) :
            self.pt = Vector.from_tuple(pt)
            self.off = bool(off)
        #end __init__

        @classmethod
        def from_tuple(celf, p) :
            "allows specifying a Point as e.g. ((x, y), off) tuple."
            if not isinstance(p, celf) :
                p = celf(*p)
            #end if
            return \
                p
        #end from_tuple

        def transform(self, matrix) :
            "returns the Point transformed through the Matrix."
            return \
                Path.Point(matrix.map(self.pt), self.off)
        #end transform

        def __eq__(p1, p2) :
            return \
                (
                    isinstance(p2, Path.Point)
                and
                    p1.pt == p2.pt
                and
                    p1.off == p2.off
                )
        #end __eq__

        def __repr__(self) :
            return \
                "Path.Point(%s, %s)" % (repr(self.pt), repr(self.off))
        #end __repr__

    #end Point

    class Segment :
        "represents a continuous segment of a Path, consisting of a sequence" \
        " of Points, and an indication of whether the path is closed or not." \
        " The segment must start (and end, if not closed) with on-curve points."

        __slots__ = ("points", "closed")

        def __init__(self, points, closed) :
            self.points = tuple(Path.Point.from_tuple(p) for p in points)
            self.closed = bool(closed)
            assert \
                (
                    len(self.points) == 0
                or
                        not self.points[0].off
                    and
                        (closed or not self.points[-1].off)
                )
        #end __init__

        def __repr__(self) :
            return \
                "Path.Segment([%s], %s)" % (", ".join(repr(p) for p in self.points), self.closed)
        #end __repr__

        def transform(self, matrix) :
            "returns the Segment transformed through the Matrix."
            return \
                Path.Segment((p.transform(matrix) for p in self.points), self.closed)
        #end transform

        def reverse(self) :
            "returns a Segment with the same control points, but in reverse order."
            return \
                Path.Segment(reversed(self.points), self.closed)
        #end reverse

        def clockwise(self) :
            "does the path segment go in a clockwise direction (assuming the default" \
            " Cairo coordinate orientation)."
            sum = 0
            prevpt = self.points[-1].pt
            for pt in self.points :
                pt = pt.pt
                sum += prevpt.cross(pt - prevpt)
                prevpt = pt
            #end for
            return \
                sum >= 0
        #end clockwise

        def pieces(self) :
            "iterates over the pieces of the path, namely the sequence of Vector coordinates" \
            " of the points between two successive on-curve points."
            seg_points = iter(self.points)
            try :
                p0 = next(seg_points)
                assert not p0.off
                p0 = p0.pt
                while True :
                    pt = next(seg_points, None)
                    if pt == None :
                        break
                    pts = [p0]
                    while True :
                        # piece ends at next on-curve point
                        pts.append(pt.pt)
                        if not pt.off :
                            break
                        pt = next(seg_points)
                    #end while
                    yield tuple(pts)
                    p0 = pts[-1]
                #end while
            except StopIteration :
                return
            #end try
        #end pieces

        def to_elements(self, relative = False, origin = None) :
            "yields a sequence of Path.Element objects that will draw the path segment."
            pts = []
            prevpt = None
            points = self.points
            if self.closed and len(points) != 0 and points[-1].off :
                points += (points[0],)
            #end if
            for p in points :
                if relative and origin != None :
                    p = Path.Point(p.pt - origin, p.off)
                #end if
                pts.append(p.pt)
                if p.off :
                    assert prevpt != None
                else :
                    if prevpt == None :
                        yield (Path.MoveTo, Path.RelMoveTo)[relative](pts[0])
                    #end if
                    if len(pts) == 1 :
                        if prevpt != None :
                            yield (Path.LineTo, Path.RelLineTo)[relative](pts[0])
                        #end if
                    elif len(pts) == 2 :
                        if prevpt != None :
                            p0 = prevpt
                        else :
                            p0 = pts[0]
                        #end if
                        yield (Path.CurveTo, Path.RelCurveTo)[relative](*Path.cubify(*([p0] + pts))[1:])
                    elif len(pts) == 3 :
                        yield (Path.CurveTo, Path.RelCurveTo)[relative](*pts)
                    else :
                        raise NotImplementedError \
                          (
                            "Cairo cannot handle higher-order Béziers than cubic"
                          )
                    #end if
                    if origin != None :
                        origin += pts[-1]
                    else :
                        origin = pts[-1]
                    #end if
                    prevpt = origin
                    pts = []
                #end if
            #end for
            assert len(pts) == 0
            if self.closed :
                yield Path.Close()
            #end if
        #end to_elements

        def draw(self, ctx, matrix = None, relative = False, origin = None) :
            "draws the path segment into the Context, optionally transformed by" \
            " the Matrix."
            if not isinstance(ctx, Context) :
                raise TypeError("ctx must be a Context")
            #end if
            for elt in self.to_elements(relative, origin) :
                elt.draw(ctx, matrix)
            #end for
        #end draw

        def flatten(self, tolerance = default_tolerance) :
            "returns a flattened version of this Segment, with all curves expanded" \
            " to straight-line segments according to the specified tolerance."
            result_path = \
                (Context.create_for_dummy()
                    .set_tolerance(tolerance)
                    .append_path(Path([self]))
                    .copy_path_flat()
                )
            assert len(result_path.segments) == 1
            return \
                result_path.segments[0]
        #end flatten

        def extents(self, tolerance = default_tolerance) :
            "returns a Rect representing the extents of this path segment."
            return \
                (Context.create_for_dummy()
                    .set_tolerance(tolerance)
                    .append_path(Path([self]))
                    .path_extents
                )
        #end extents

    #end Segment

    def __init__(self, segments) :
        self.segments = []
        for seg in segments :
            if not isinstance(seg, Path.Segment) :
                raise TypeError("path segment is not a Path.Segment")
            #end if
            self.segments.append(seg)
        #end for
    #end __init__

    def __repr__(self) :
        return \
            "Path(%s)" % repr(tuple(self.segments))
    #end __repr__

    def __add__(p1, p2) :
        "returns a Path which combines the Segments from two Paths."
        if not isinstance(p2, Path) :
            raise TypeError("can only add to another Path")
        #end if
        return \
            Path(p1.segments + p2.segments)
    #end __add__

    class Element :
        "base class for path elements that map directly to Cairo path-construction" \
        " calls. Do not instantiate directly; instantiate subclasses intead."

        __slots__ = ("type", "relative", "points", "meth")

        def __init__(self, type, relative, points, meth) :
            # type is CAIRO.PATH_xxxx code, points is tuple of points,
            # relative indicates whether to use relative or absolute Cairo
            # path-construction calls, meth is Context instance method
            # to draw the Element
            self.type = type
            self.points = tuple(Vector.from_tuple(p) for p in points)
            self.relative = relative
            self.meth = meth
        #end __init__

        def transform(self, matrix) :
            "returns a copy of the Element with control points transformed" \
            " by the specified Matrix."
            return \
                type(self)(*matrix.mapiter(self.points))
        #end transform

        def draw(self, g, matrix = None) :
            "draws the element into the Context g, optionally transformed by the matrix."
            if matrix != None :
                p = tuple(matrix.mapiter(self.points))
            else :
                p = self.points
            #end if
            self.meth(*((g,) + p))
        #end draw

        def __repr__(self) :
            return \
                "%s(%s)" % (type(self).__name__, ", ".join(repr(tuple(p)) for p in self.points))
        #end __repr__

    #end Element

    class MoveTo(Element) :
        "represents a move_to the specified Vector position."

        def __init__(self, p) :
            super().__init__(CAIRO.PATH_MOVE_TO, False, (p,), Context.move_to)
        #end __init__

    #end MoveTo

    class RelMoveTo(Element) :
        "represents a rel_move_to the specified Vector position."

        def __init__(self, p) :
            super().__init__(CAIRO.PATH_MOVE_TO, True, (p,), Context.rel_move_to)
        #end __init__

    #end RelMoveTo

    class LineTo(Element) :
        "represents a line_to the specified Vector position."

        def __init__(self, p) :
            super().__init__(CAIRO.PATH_LINE_TO, False, (p,), Context.line_to)
        #end __init__

    #end LineTo

    class RelLineTo(Element) :
        "represents a rel_line_to the specified Vector position."

        def __init__(self, p) :
            super().__init__(CAIRO.PATH_LINE_TO, True, (p,), Context.rel_line_to)
        #end __init__

    #end RelLineTo

    class CurveTo(Element) :
        "represents a curve_to via the specified three Vector positions."

        def __init__(self, p1, p2, p3) :
            super().__init__(CAIRO.PATH_CURVE_TO, False, (p1, p2, p3), Context.curve_to)
        #end __init__

    #end CurveTo

    class RelCurveTo(Element) :
        "represents a rel_curve_to via the specified three Vector positions."

        def __init__(self, p1, p2, p3) :
            super().__init__(CAIRO.PATH_CURVE_TO, True, (p1, p2, p3), Context.rel_curve_to)
        #end __init__

    #end RelCurveTo

    class Close(Element) :
        "represents a closing of the current path."

        def __init__(self) :
            super().__init__(CAIRO.PATH_CLOSE_PATH, False, (), Context.close_path)
        #end __init__

    #end Close

    element_types = \
        { # number of control points and Element subclasses for each path element type
            CAIRO.PATH_MOVE_TO : {"nr" : 1, "type" : MoveTo, "reltype" : RelMoveTo},
            CAIRO.PATH_LINE_TO : {"nr" : 1, "type" : LineTo, "reltype" : RelLineTo},
            CAIRO.PATH_CURVE_TO : {"nr" : 3, "type" : CurveTo, "reltype" : RelCurveTo},
            CAIRO.PATH_CLOSE_PATH : {"nr" : 0, "type" : Close, "reltype" : Close},
        }

    @classmethod
    def from_elements(celf, elts, clean = True, origin = None) :
        "constructs a Path from a sequence of Path.Element objects in elts. clean indicates" \
        " whether to omit isolated single-point segments. origin is a Vector only" \
        " needed if elts begins with a relative operator; otherwise it is ignored."
        segs = []
        seg = None
        elts = iter(elts)
        while True :
            elt = next(elts, None)
            if elt == None or elt.type == CAIRO.PATH_MOVE_TO :
                if seg != None :
                    if not clean or len(seg) > 1 :
                        segs.append(Path.Segment(seg, False))
                    #end if
                    seg = None
                #end if
                if elt == None :
                    break
            #end if
            if elt.type == CAIRO.PATH_CLOSE_PATH :
                if seg != None :
                    if not clean or len(seg) > 1 :
                        if not clean or seg[-1] != seg[0] :
                            seg.append(seg[0])
                        #end if
                        segs.append(Path.Segment(seg, True))
                    #end if
                    seg = None
                #end if
            else :
                segstarted = False
                if elt.relative :
                    assert origin != None, "no origin available for relative path element"
                    points = list(p + origin for p in elt.points)
                else :
                    points = elt.points
                #end if
                origin = points[-1]
                if seg == None :
                    seg = [Path.Point(points[0], False)]
                    segstarted = True
                #end if
                if elt.type == CAIRO.PATH_LINE_TO :
                    if not segstarted :
                        seg.append(Path.Point(points[0], False))
                    #end if
                elif elt.type == CAIRO.PATH_CURVE_TO :
                    seg.extend \
                      (
                        [
                            Path.Point(points[0], True),
                            Path.Point(points[1], True),
                            Path.Point(points[2], False),
                        ]
                      )
                #end if
            #end if
        #end while
        return \
            celf(segs)
    #end from_elements

    @classmethod
    def from_cairo(celf, path) :
        "translates a CAIRO.path_data_t to a Path."
        elements = []
        data = ct.cast(path, CAIRO.path_ptr_t).contents.data
        nrelts = ct.cast(path, CAIRO.path_ptr_t).contents.num_data
        i = 0
        while True :
            if i == nrelts :
                break
            i += 1
            header = ct.cast(data, CAIRO.path_data_t.header_ptr_t).contents
            assert header.length == celf.element_types[header.type]["nr"] + 1, \
                (
                    "expecting %d control points for path elt type %d, got %d"
                %
                    (celf.element_types[header.type]["nr"] + 1, header.type, header.length)
                )
            data += ct.sizeof(CAIRO.path_data_t)
            points = []
            for j in range(header.length - 1) :
                assert i < nrelts, "buffer overrun"
                i += 1
                point = ct.cast(data, CAIRO.path_data_t.point_ptr_t).contents
                points.append((point.x, point.y))
                data += ct.sizeof(CAIRO.path_data_t)
            #end for
            elements.append(celf.element_types[header.type]["type"](*points))
        #end for
        return \
            celf.from_elements(elements)
    #end from_cairo

    @classmethod
    def from_ft_outline(celf, outline, shift = 0, delta = 0) :
        "converts a freetype2.Outline to a Path."

        segs = []
        seg = None

        def flush_seg() :
            nonlocal seg
            if seg != None :
                segs.append(Path.Segment(seg, True))
                seg = None
            #end if
        #end flush_seg

        def move_to(p, _) :
            nonlocal seg
            flush_seg()
            seg = [Path.Point(p, False)]
            return \
                0
        #end move_to

        def line_to(p, _) :
            seg.append(Path.Point(p, False))
            return \
                0
        #end line_to

        def conic_to(p1, p2, _) :
            seg.extend([Path.Point(p1, True), Path.Point(p2, False)])
            return \
                0
        #end conic_to

        def cubic_to(p1, p2, p3, _) :
            seg.extend([Path.Point(p1, True), Path.Point(p2, True), Path.Point(p3, False)])
            return \
                0
        #end cubic_to

    #begin from_ft_outline
        outline.decompose \
          (
            move_to = move_to,
            line_to = line_to,
            conic_to = conic_to,
            cubic_to = cubic_to,
            arg = None,
            shift = shift,
            delta = delta,
          )
        flush_seg()
        return \
            Path(segs)
    #end from_ft_outline

    @staticmethod
    def create_arc(centre, radius, angle1, angle2, negative, closed = False) :
        "creates a Path consisting of a segment of a circular arc as constructed" \
        " by Context.arc."
        g = Context.create_for_dummy()
        g.arc(centre, radius, angle1, angle2, negative)
        if closed :
            g.close_path()
        #end if
        return \
                g.copy_path()
    #end create_arc

    @staticmethod
    def create_circle(centre, radius) :
        "extremely common case of arc forming a full circle."
        return \
            Path.create_arc(centre, radius, 0, circle, False, True)
    #end create_circle

    @staticmethod
    def create_round_rect(bounds, radius) :
        "creates a Path representing a rounded-corner rectangle. bounds is a" \
        " Rect defining the bounds of the rectangle, and radius is either a number" \
        " or a Vector defining the horizontal and vertical corner radii."
        if isinstance(radius, Real) :
            radius = Vector(1, 1) * radius
        elif isinstance(radius, tuple) :
            radius = Vector.from_tuple(radius)
        elif not isinstance(radius, Vector) :
            raise TypeError("radius must be a number or a Vector")
        #end if
        g = Context.create_for_dummy()
        corner1 = bounds.topleft
        for side in range(4) :
            angle = side / 4 * circle
            step = Vector(1, 0).rotate(angle)
            corner2 = corner1 + step * bounds.dimensions
            g.line_to(corner1 + step * radius)
            g.rel_line_to(step * (bounds.dimensions - 2 * radius))
            for elt in \
                (Path.create_arc
                  (
                    centre = (0, 0),
                    radius = 1,
                    angle1 = angle - 90 * deg,
                    angle2 = angle,
                    negative = False
                  )
                    .transform
                      (
                            Matrix.translate
                              (
                                    corner2
                                +
                                    Vector(1, 1).rotate(angle + 90 * deg) * radius
                              )
                        *
                            Matrix.scale(radius)
                      )
                    .to_elements()
                ) \
            :
                if elt.type != CAIRO.PATH_MOVE_TO :
                    elt.draw(g)
                #end if
            #end for
            corner1 = corner2
        #end for
        g.close_path()
        return \
            g.copy_path()
    #end create_round_rect

    def to_elements(self, relative = False) :
        "yields a sequence of Path.Element objects that will draw the path."
        origin = None
        for seg in self.segments :
            for elt in seg.to_elements(relative, origin) :
                yield elt
            #end for
            if relative and len(seg.points) != 0 :
                origin = seg.points[-1].pt
            #end if
        #end for
    #end to_elements

    @staticmethod
    def cubify(p1, p2, p3) :
        "given three Vectors defining a quadratic Bézier, returns a tuple of four" \
        " Vectors defining the same curve as a cubic Bézier."
        # quadratic-to-cubic conversion taken from
        # <http://stackoverflow.com/questions/3162645/convert-a-quadratic-bezier-to-a-cubic>
        p1 = Vector.from_tuple(p1)
        p2 = Vector.from_tuple(p2)
        p3 = Vector.from_tuple(p3)
        return \
            (
                p1,
                p1 + 2 * (p2 - p1) / 3,
                p3 + 2 * (p2 - p3) / 3,
                p3
            )
    #end cubify

    def draw(self, ctx, matrix = None, relative = False) :
        "draws the Path into a Context, optionally transformed by the given Matrix."
        if not isinstance(ctx, Context) :
            raise TypeError("ctx must be a Context")
        #end if
        for seg in self.segments :
            seg.draw(ctx, matrix, relative)
        #end for
    #end draw

    def transform(self, matrix) :
        "returns a copy of this Path with elements transformed by the given Matrix."
        return \
            Path \
              (
                seg.transform(matrix) for seg in self.segments
              )
    #end transform

    def reverse(self) :
        "returns a Path with the same shape, but which goes through the points" \
        " in the opposite order from this one."
        return \
            Path(reversed(tuple(seg.reverse() for seg in self.segments)))
    #end reverse

    def flatten(self, tolerance = default_tolerance) :
        "returns a flattened version of this Path, with all curves expanded" \
        " to straight-line segments according to the specified tolerance."
        return \
            (Context.create_for_dummy()
                .set_tolerance(tolerance)
                .append_path(self)
                .copy_path_flat()
            )
    #end flatten

    def extents(self, tolerance = default_tolerance) :
        "returns a Rect representing the extents of this Path."
        return \
            (Context.create_for_dummy()
                .set_tolerance(tolerance)
                .append_path(self)
                .path_extents
            )
    #end extents

#end Path

class FontOptions :
    "Cairo font options. Use the create method, with optional initial settings," \
    " to create a new font_options_t object."
    # <http://cairographics.org/manual/cairo-cairo-font-options-t.html>

    __slots__ = ("_cairobj",) # to forestall typos

    props = \
        (
            "antialias",
            "subpixel_order",
            "hint_style",
            "hint_metrics",
        )
    if hasattr(cairo, "cairo_font_options_get_variations") : # since 1.16
        props += ("variations",)
    #end if

    def _check(self) :
        # check for error from last operation on this FontOptions.
        check(cairo.cairo_font_options_status(self._cairobj))
    #end _check

    def __init__(self, existing = None) :
        if existing == None :
            self._cairobj = cairo.cairo_font_options_create()
        else :
            self._cairobj = existing
        #end if
        self._check()
    #end __init__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_font_options_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @classmethod
    def create(celf, **kwargs) :
        "creates a new FontOptions object. See FontOptions.props for valid arg keywords."
        leftover = set(kwargs.keys()) - set(FontOptions.props)
        if len(leftover) != 0 :
            raise TypeError("unexpected arguments %s" % ", ".join(leftover))
        #end if
        result = celf()
        for k in celf.props :
            if k in kwargs :
                setattr(result, k, kwargs[k])
            #end if
        #end for
        return \
            result
    #end create
    # create.__doc__ = "valid args are %s" % ", ".join(props) # either not allowed or no point

    def copy(self) :
        "returns a copy of this FontOptions in a new object."
        return \
            type(self)(cairo.cairo_font_options_copy(self._cairobj))
    #end copy

    def merge(self, other) :
        "merges non-default options from another FontOptions object."
        if not isinstance(other, FontOptions) :
            raise TypeError("can only merge with another FontOptions object")
        #end if
        cairo.cairo_font_options_merge(self._cairobj, other._cairobj)
        self._check()
    #end merge

    def __eq__(self, other) :
        "equality of settings in two FontOptions objects."
        if not isinstance(other, FontOptions) :
            raise TypeError("can only compare equality with another FontOptions object")
        #end if
        return \
            cairo.cairo_font_options_equal(self._cairobj, other._cairobj)
    #end __eq__

    @property
    def antialias(self) :
        "antialias mode for this FontOptions, CAIRO.ANTIALIAS_xxx."
        return \
            cairo.cairo_font_options_get_antialias(self._cairobj)
    #end antialias

    @antialias.setter
    def antialias(self, anti) :
        cairo.cairo_font_options_set_antialias(self._cairobj, anti)
    #end antialias

    @property
    def subpixel_order(self) :
        "subpixel order for this FontOptions, CAIRO.SUBPIXEL_ORDER_xxx."
        return \
            cairo.cairo_font_options_get_subpixel_order(self._cairobj)
    #end subpixel_order

    @subpixel_order.setter
    def subpixel_order(self, sub) :
        cairo.cairo_font_options_set_subpixel_order(self._cairobj, sub)
    #end subpixel_order

    @property
    def hint_style(self) :
        "hint style for this FontOptions, CAIRO.HINT_STYLE_xxx."
        return \
            cairo.cairo_font_options_get_hint_style(self._cairobj)
    #end hint_style

    @hint_style.setter
    def hint_style(self, hint) :
        cairo.cairo_font_options_set_hint_style(self._cairobj, hint)
    #end hint_style

    @property
    def hint_metrics(self) :
        "hint metrics for this FontOptions, CAIRO.HINT_METRICS_xxx."
        return \
            cairo.cairo_font_options_get_hint_metrics(self._cairobj)
    #end hint_metrics

    @hint_metrics.setter
    def hint_metrics(self, hint) :
        cairo.cairo_font_options_set_hint_metrics(self._cairobj, hint)
    #end hint_metrics

    if hasattr(cairo, "cairo_font_options_get_variations") : # since 1.16

        @property
        def variations(self) :
            c_text = cairo.cairo_font_options_get_variations(self._cairobj)
            if c_text != None :
                result = c_text.decode()
            else :
                result = None
            #end if
            return \
                result
        #end variations

        @variations.setter
        def variations(self, variations) :
            self.set_variations(variations)
        #end variations

        def set_variations(self, variations) :
            if variations != None :
                c_variations = variations.encode()
            else :
                c_variations = None
            #end if
            cairo.cairo_font_options_set_variations(self._cairobj, c_variations)
        #end set_variations

    #end if

    if fontconfig != None :

        # <https://www.cairographics.org/manual/cairo-FreeType-Fonts.html#cairo-ft-font-options-substitute>
        def substitute(self, pattern) :
            if not isinstance(pattern, fontconfig.Pattern) :
                raise TypeError("pattern must be a fontconfig.Pattern")
            #end if
            cairo.cairo_ft_font_options_substitute(pattern._fcobj, self._cairobj)
        #end substitute

    #end if

    def __repr__(self) :
        return \
            (
                "FontOptions.create(%s)"
            %
                ", ".join
                  (
                        "%s = %s"
                    %
                        (
                            name,
                            (
                                lambda x : "%d" % x,
                                lambda x : "%s" % repr(x),
                            )[name == "variations"](getattr(self, name))
                        )
                    for name in self.props
                  )
            )
    #end __repr__

#end FontOptions

class FontFace :
    "a general Cairo font object. Do not instantiate directly; use the create methods."
    # <http://cairographics.org/manual/cairo-cairo-font-face-t.html>

    __slots__ = ("_cairobj", "_user_data", "ft_face", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this FontFace.
        check(cairo.cairo_font_face_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_font_face_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_font_face_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @property
    def type(self) :
        "the type of font underlying this FontFace, CAIRO.FONT_TYPE_xxx."
        return \
            cairo.cairo_font_face_get_type(self._cairobj)
    #end type

    if freetype2 != None :

        @classmethod
        def create_for_ft_face(celf, face, load_flags = 0) :
            "creates a FontFace from a freetype2.Face."
            if not isinstance(face, freetype2.Face) :
                raise TypeError("face must be a freetype2.Face")
            #end if
            cairo_face = cairo.cairo_ft_font_face_create_for_ft_face(face._ftobj, load_flags)
            result = celf(cairo_face)
            if cairo.cairo_font_face_get_user_data(cairo_face, ct.byref(_ft_destroy_key)) == None :
                check(cairo.cairo_font_face_set_user_data
                  (
                    cairo_face,
                    ct.byref(_ft_destroy_key),
                    ct.cast(face._ftobj, ct.c_void_p).value,
                    freetype2.ft.FT_Done_Face
                  ))
                freetype2.check(freetype2.ft.FT_Reference_Face(face._ftobj))
                  # need another reference since Cairo has stolen previous one
                  # not expecting this to fail!
            #end if
            result.ft_face = face
            return \
                result
        #end create_for_ft_face

        @classmethod
        def create_for_file(celf, filename, face_index = 0, load_flags = 0) :
            "uses FreeType to load a font from the specified filename, and returns" \
            " a new FontFace for it."
            return \
                celf.create_for_ft_face(get_ft_lib().new_face(filename, face_index), load_flags)
        #end create_for_file

    else :

        @classmethod
        def create_for_ft_face(celf, face) :
            "not implemented (requires python_freetype)."
            raise NotImplementedError("requires python_freetype")
        #end create_for_ft_face

        @classmethod
        def create_for_file(celf, filename, face_index = 0, load_flags = 0) :
            "uses FreeType to load a font from the specified filename, and returns" \
            " a new FontFace for it."
            _ensure_ft()
            ft_face = ct.c_void_p()
            c_filename = filename.encode()
            status = _ft.FT_New_Face(ct.c_void_p(_ft_lib), c_filename, face_index, ct.byref(ft_face))
            if status != 0 :
                raise RuntimeError("Error %d loading FreeType font" % status)
            #end if
            try :
                cairo_face = cairo.cairo_ft_font_face_create_for_ft_face(ft_face.value, load_flags)
                result = celf(cairo_face)
                check(cairo.cairo_font_face_set_user_data
                  (
                    cairo_face,
                    ct.byref(_ft_destroy_key),
                    ft_face.value,
                    _ft.FT_Done_Face
                  ))
                ft_face = None # so I don't free it yet
            finally :
                if ft_face != None :
                    _ft.FT_Done_Face(ft_face)
                #end if
            #end try
            return \
                result
        #end create_for_file

    #end if freetype2 != None

    if fontconfig != None :

        @classmethod
        def create_for_pattern(celf, pattern, options = None, config = None) :
            "uses Fontconfig to find a font matching the specified pattern string," \
            " uses FreeType to load the font, and returns a new FontFace for it." \
            " options, if present, must be a FontOptions object."
            _ensure_ft()
            if pattern != None and not isinstance(pattern, (fontconfig.Pattern, str)) :
                raise TypeError("options must be a pattern string or fontconfig.Pattern")
            #end if
            if options != None and not isinstance(options, FontOptions) :
                raise TypeError("options must be a FontOptions")
            #end if
            if config != None and not isinstance(config, fontconfig.Config) :
                raise TypeError("config must be a fontconfig.Config")
            #end if
            if isinstance(pattern, fontconfig.Pattern) :
                search_pattern = pattern.duplicate()
            else :
                search_pattern = fontconfig.Pattern.name_parse(pattern)
                if search_pattern == None :
                    raise RuntimeError("cannot parse Fontconfig name pattern")
                #end if
            #end if
            if config == None :
                config = fontconfig.Config.get_current()
            #end if
            config.substitute(search_pattern, fontconfig.FC.MatchPattern)
            if options != None :
                options.substitute(search_pattern)
            #end if
            search_pattern.default_substitute()
            found_pattern, match_result = config.font_match(search_pattern)
            if found_pattern == None or match_result != fontconfig.FC.ResultMatch :
                raise RuntimeError("Fontconfig cannot match font name")
            #end if
            cairo_face = cairo.cairo_ft_font_face_create_for_pattern(found_pattern._fcobj)
            return \
                celf(cairo_face)
        #end create_for_pattern

    else :

        @classmethod
        def create_for_pattern(celf, pattern, options = None) :
            "uses Fontconfig to find a font matching the specified pattern string," \
            " uses FreeType to load the font, and returns a new FontFace for it." \
            " options, if present, must be a FontOptions object."
            _ensure_ft()
            _ensure_fc()
            if options != None and not isinstance(options, FontOptions) :
                raise TypeError("options must be a FontOptions")
            #end if
            with _FcPatternManager() as patterns :
                c_pattern = pattern.encode()
                search_pattern = patterns.collect(_fc.FcNameParse(c_pattern))
                if search_pattern == None :
                    raise RuntimeError("cannot parse Fontconfig name pattern")
                #end if
                if not _fc.FcConfigSubstitute(None, search_pattern, _FC.FcMatchPattern) :
                    raise RuntimeError("cannot substitute Fontconfig configuration")
                #end if
                if options != None :
                    cairo.cairo_ft_font_options_substitute(search_pattern, options._cairobj)
                #end if
                _fc.FcDefaultSubstitute(search_pattern)
                match_result = ct.c_int()
                found_pattern = patterns.collect(_fc.FcFontMatch(None, search_pattern, ct.byref(match_result)))
                if found_pattern == None or match_result.value != _FC.FcResultMatch :
                    raise RuntimeError("Fontconfig cannot match font name")
                #end if
                cairo_face = cairo.cairo_ft_font_face_create_for_pattern(found_pattern)
            #end with
            return \
                celf(cairo_face)
        #end create_for_pattern

    #end if

    @property
    def ft_synthesize(self) :
        "the bold/italic synthesize flags for the font, CAIRO.FT_SYNTHESIZE_xxx" \
        " (FreeType fonts only)."
        return \
            cairo.cairo_ft_font_face_get_synthesize(self._cairobj)
    #end ft_synthesize

    @ft_synthesize.setter
    def ft_synthesize(self, synth_flags) :
        self.ft_unset_synthesize(~synth_flags).ft_set_synthesize(synth_flags)
    #end ft_synthesize

    def ft_set_synthesize(self, synth_flags) :
        "sets the specified bits in the bold/italic synthesize flags for the font," \
        " CAIRO.FT_SYNTHESIZE_xxx (FreeType fonts only)."
        cairo.cairo_ft_font_face_set_synthesize(self._cairobj, synth_flags)
        return \
            self
    #end ft_set_synthesize

    def ft_unset_synthesize(self, synth_flags) :
        "clears the specified bits in the bold/italic synthesize flags for the font," \
        " CAIRO.FT_SYNTHESIZE_xxx (FreeType fonts only)."
        cairo.cairo_ft_font_face_unset_synthesize(self._cairobj, synth_flags)
        return \
            self
    #end ft_unset_synthesize

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    # toy font face functions from <http://cairographics.org/manual/cairo-text.html>

    @classmethod
    def toy_create(celf, family, slant, weight) :
        "creates a “toy” FontFace."
        c_family = family.encode()
        return \
            celf(cairo.cairo_toy_font_face_create(c_family, slant, weight))
    #end toy_create

    @property
    def toy_family(self) :
        "the family name (only for “toy” fonts)"
        result = cairo.cairo_toy_font_face_get_family(self._cairobj)
        self._check()
        return \
            result.decode("utf-8")
    #end toy_family

    @property
    def toy_slant(self) :
        "the slant setting (only for “toy” fonts)"
        result = cairo.cairo_toy_font_face_get_slant(self._cairobj)
        self._check()
        return \
            result
    #end toy_slant

    @property
    def toy_weight(self) :
        "the weight setting (only for “toy” fonts)"
        result = cairo.cairo_toy_font_face_get_weight(self._cairobj)
        self._check()
        return \
            result
    #end toy

#end FontFace

class ScaledFont :
    "a representation of a Cairo scaled_font_t, which is a font with particular" \
    " size and option settings. Do not instantiate directly; use the create method," \
    " or get one from Context.scaled_font."

    __slots__ = ("_cairobj", "_user_data", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def _check(self) :
        # check for error from last operation on this ScaledFont.
        check(cairo.cairo_scaled_font_status(self._cairobj))
    #end _check

    def __new__(celf, _cairobj) :
        self = celf._instances.get(_cairobj)
        if self == None :
            self = super().__new__(celf)
            self._cairobj = _cairobj
            self._check()
            user_data = celf._ud_refs.get(_cairobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_cairobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_cairobj] = self
        else :
            cairo.cairo_scaled_font_destroy(self._cairobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._cairobj != None :
            cairo.cairo_scaled_font_destroy(self._cairobj)
            self._cairobj = None
        #end if
    #end __del__

    @classmethod
    def create(celf, font_face, font_matrix, ctm, options) :
        "creates a ScaledFont from the specified FontFace, Matrix font_matrix" \
        " and ctm, and FontOptions options."
        # Q: Are any of these optional?
        # A: Looking at Cairo source file src/cairo-scaled-font.c, No.
        if not isinstance(font_face, FontFace) :
            raise TypeError("font_face must be a FontFace")
        #end if
        if not isinstance(font_matrix, Matrix) or not isinstance(ctm, Matrix) :
            raise TypeError("font_matrix and ctm must be Matrix objects")
        #end if
        if not isinstance(options, FontOptions) :
            raise TypeError("options must be a FontOptions")
        #end if
        font_matrix = font_matrix.to_cairo()
        ctm = ctm.to_cairo()
        return \
            celf(cairo.cairo_scaled_font_create(font_face._cairobj, ct.byref(font_matrix), ct.byref(ctm), options._cairobj))
    #end create

    @property
    def font_extents(self) :
        "returns a FontExtents object giving information about the font settings."
        result = CAIRO.font_extents_t()
        cairo.cairo_scaled_font_extents(self._cairobj, ct.byref(result))
        return \
            FontExtents.from_cairo(result)
    #end font_extents

    def text_extents(self, text) :
        "returns a TextExtents object giving information about drawing the" \
        " specified text at the font settings."
        result = CAIRO.text_extents_t()
        c_text = text.encode()
        cairo.cairo_scaled_font_text_extents(self._cairobj, c_text, ct.byref(result))
        return \
            TextExtents.from_cairo(result)
    #end text_extents

    def glyph_extents(self, glyphs) :
        "returns a TextExtents object giving information about drawing the" \
        " specified glyphs at the font settings."
        buf, nr_glyphs = glyphs_to_cairo(glyphs)
        result = CAIRO.text_extents_t()
        cairo.cairo_scaled_font_glyph_extents(self._cairobj, buf, nr_glyphs, ct.byref(result))
        return \
            TextExtents.from_cairo(result)
    #end glyph_extents

    @property
    def font_face(self) :
        "the FontFace from which this ScaledFont was created."
        return \
            FontFace(cairo.cairo_font_face_reference(cairo.cairo_scaled_font_get_font_face(self._cairobj)))
    #end font_face

    def text_to_glyphs(self, pos, text, cluster_mapping = False) :
        "converts text (which can be a Unicode string or utf-8-encoded bytes) to an" \
        " array of glyphs, optionally including cluster mapping information." \
        " If not cluster_mapping, then the result will be a tuple of" \
        " a single element, being a tuple of Glyph objects. If cluster_mapping, then" \
        " the result tuple will have three elements, the first being the tuple of Glyphs" \
        " as before, the second being a tuple of (nr_chars/nr_bytes, nr_glyphs) tuples," \
        " and the third being the cluster_flags, of which only CAIRO.TEXT_CLUSTER_FLAG_BACKWARD" \
        " is currently defined; this indicates that the numbers of glyphs in the clusters" \
        " count from the end of the Glyphs array, not from the start."
        pos = Vector.from_tuple(pos)
        encode = not isinstance(text, bytes)
        if encode :
            c_text = text.encode("utf-8")
        else :
            c_text = text
        #end if
        c_glyphs = CAIRO.glyph_ptr_t()
        num_glyphs = ct.c_int(0)
        if cluster_mapping :
            clusters_ptr = ct.pointer(CAIRO.cluster_ptr_t())
            num_clusters = ct.pointer(ct.c_int(0))
            cluster_flags = ct.pointer(ct.c_uint())
        else :
            clusters_ptr = None
            num_clusters = None
            cluster_flags = None
        #end if
        check(cairo.cairo_scaled_font_text_to_glyphs(self._cairobj, pos.x, pos.y, c_text, len(c_text), ct.byref(c_glyphs), ct.byref(num_glyphs), clusters_ptr, num_clusters, cluster_flags))
        result = \
            (
                tuple
                  (
                    Glyph(g.index, Vector(g.x, g.y))
                    for i in range(num_glyphs.value)
                    for g in (c_glyphs[i],)
                  ),
            )
        if cluster_mapping :
            c_clusters = clusters_ptr.contents
            num_clusters = num_clusters.contents.value
            cluster_flags = cluster_flags.contents.value
            if encode :
                clusters = []
                pos = 0
                for i in range(num_clusters) :
                    # convert cluster num_bytes to cluster num_chars
                    next_pos = pos + c_clusters[i].num_bytes
                    clusters.append \
                      (
                        (len(c_text[pos:next_pos].decode("utf-8")), c_clusters[i].num_glyphs)
                      )
                    pos = next_pos
                #end for
                clusters = tuple(clusters)
            else :
                clusters = tuple \
                  (
                    (c.num_bytes, c.num_glyphs)
                    for i in range(num_clusters)
                    for c in (c_clusters[i],)
                  )
            #end if
            result += (clusters, cluster_flags)
            cairo.cairo_text_cluster_free(clusters_ptr.contents)
        #end if
        cairo.cairo_glyph_free(c_glyphs)
        return \
            result
    #end text_to_glyphs

    @property
    def font_options(self) :
        "a copy of the font options."
        result = FontOptions.create()
        cairo.cairo_scaled_font_get_font_options(self._cairobj, result._cairobj)
        return \
            result
    #end font_options

    @property
    def font_matrix(self) :
        "the font matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_scaled_font_get_font_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end font_matrix

    @property
    def ctm(self) :
        "the transformation matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_scaled_font_get_ctm(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end ctm

    @property
    def scale_matrix(self) :
        "the scale matrix."
        result = CAIRO.matrix_t()
        cairo.cairo_scaled_font_get_scale_matrix(self._cairobj, ct.byref(result))
        return \
            Matrix.from_cairo(result)
    #end scale_matrix

    @property
    def type(self) :
        "the type of font underlying this ScaledFont, CAIRO.FONT_TYPE_xxx other" \
        " than FONT_TYPE_TOY."
        return \
            cairo.cairo_scaled_font_get_type(self._cairobj)
    #end type

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # Cairo user_data not exposed to caller, probably not useful

    if freetype2 != None :

        # <https://www.cairographics.org/manual/cairo-FreeType-Fonts.html>

        def lock_face(self) :
            ft_face = cairo.cairo_ft_scaled_font_lock_face(self._cairobj)
            self._check()
            return \
                freetype2.Face(lib = get_ft_lib(), face = ft_face, filename = None)
        #end lock_face

        def unlock_face(self) :
            cairo.cairo_ft_scaled_font_unlock_face(self._cairobj)
            self._check()
        #end unlock_face

    #end if

#end ScaledFont

class UserFontFace(FontFace) :
    "font support with data provided by the user. Do not instantiate directly; use" \
    " the create method. You supply up to four callbacks (only one of which is required)" \
    " that define the behaviour of the font: init_func, render_glyph_func (required)," \
    " text_to_glyphs_func and unicode_to_glyph_func."

    __slots__ = \
        (
            "_init_func",
            "_render_glyph_func",
            "_text_to_glyphs_func",
            "_unicode_to_glyph_func",
            "pass_unicode",
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_init_func",
            "_wrap_render_glyph_func",
            "_wrap_text_to_glyphs_func",
            "_wrap_unicode_to_glyph_func",
        ) # to forestall typos

    @classmethod
    def create \
      (
        celf,
        init_func = None,
        render_glyph_func = None,
        text_to_glyphs_func = None,
        unicode_to_glyph_func = None,
      ) :
        "creates a new UserFontFace. You can specify callbacks here, or later, via assignment" \
        " to the properties or using the set_xxx methods."
        result = celf(cairo.cairo_user_font_face_create())
        result._init_func = None
        result._render_glyph_func = None
        result._text_to_glyphs_func = None
        result._unicode_to_glyph_func = None
        result.pass_unicode = True
        result._wrap_init_func = None
        result._wrap_render_glyph_func = None
        result._wrap_text_to_glyphs_func = None
        result._wrap_unicode_to_glyph_func = None
        if init_func != None :
            result.set_init_func(init_func)
        #end if
        if render_glyph_func != None :
            result.set_render_glyph_func(render_glyph_func)
        #end if
        if text_to_glyphs_func != None :
            result.set_text_to_glyphs_func(text_to_glyphs_func)
        #end if
        if unicode_to_glyph_func != None :
            result.set_unicode_to_glyph_func(unicode_to_glyph_func)
        #end if
        return \
            result
    #end create

    @property
    def init_func(self) :
        "the current init_func, invoked as follows:\n" \
        "\n" \
        "    status = init_func(scaled_font : ScaledFont, ctx : Context, font_extents : FontExtents)\n" \
        "\n" \
        "Mainly, this should set fields in the font_extents to define the metrics of the font.\n" \
        "This callback is optional."
        return \
            self._init_func
    #end init_func

    @init_func.setter
    def init_func(self, init) :
        self.set_init_func(init)
    #end init_func

    def set_init_func(self, init) :
        "sets a new value for the init_func. Useful for method chaining; otherwise just" \
        " assign to the init_func property."
        temp = self._wrap_init_func # so the old value doesn't disappear until it's no longer needed
        if init != None :
            def wrap_init_func(c_scaled_font, c_ctx, c_font_extents) :
                scaled_font = ScaledFont(cairo.cairo_scaled_font_reference(c_scaled_font))
                ctx = Context(cairo.cairo_reference(cairo.cairo_reference(c_ctx)))
                font_extents = FontExtents.from_cairo(c_font_extents.contents)
                status = init(scaled_font, ctx, font_extents)
                for f, _ in CAIRO.font_extents_t._fields_ :
                    # return any changes made by user to caller
                    setattr(c_font_extents.contents, f, getattr(font_extents, f))
                #end for
                return \
                    status
            #end wrap_init_func
            self._wrap_init_func = CAIRO.user_scaled_font_init_func_t(wrap_init_func)
        else :
            self._wrap_init_func = None
        #end if
        cairo.cairo_user_font_face_set_init_func(self._cairobj, self._wrap_init_func)
        self._init_func = init
        return \
            self
    #end set_init_func

    @property
    def render_glyph_func(self) :
        "the current render_glyph_func, invoked as follows\n" \
        "\n" \
        "    status = render_glyph_func(scaled_font : ScaledFont, glyph : int, ctx : Context, text_extents : TextExtents)\n" \
        "\n" \
        " where glyph is the index of the glyph to render, ctx is the Context into which to" \
        " render the glyph, and text_extents can be adjusted to return the metrics of" \
        " the glyph.\n" \
        "This callback is mandatory."
        return \
            self._render_glyph_func
    #end render_glyph_func

    @render_glyph_func.setter
    def render_glyph_func(self, render_glyph) :
        self.set_render_glyph_func(render_glyph)
    #end render_glyph_func

    def set_render_glyph_func(self, render_glyph) :
        "sets a new value for the render_glyph_func. Useful for method chaining; otherwise just" \
        " assign to the render_glyph_func property."
        temp = self._wrap_render_glyph_func # so the old value doesn't disappear until it's no longer needed
        if render_glyph != None :
            def wrap_render_glyph_func(c_scaled_font, glyph, c_ctx, c_text_extents) :
                scaled_font = ScaledFont(cairo.cairo_scaled_font_reference(c_scaled_font))
                ctx = Context(cairo.cairo_reference(cairo.cairo_reference(c_ctx)))
                text_extents = TextExtents.from_cairo(c_text_extents.contents)
                status = render_glyph(scaled_font, glyph, ctx, text_extents)
                for f, _ in CAIRO.text_extents_t._fields_ :
                    # return any changes made by user to caller
                    setattr(c_text_extents.contents, f, getattr(text_extents, f))
                #end for
                return \
                    status
            #end wrap_render_glyph_func
            self._wrap_render_glyph_func = CAIRO.user_scaled_font_render_glyph_func_t(wrap_render_glyph_func)
        else :
            self._wrap_render_glyph_func = None
        #end if
        cairo.cairo_user_font_face_set_render_glyph_func(self._cairobj, self._wrap_render_glyph_func)
        self._render_glyph_func = render_glyph
        return \
            self
    #end set_render_glyph_func

    @property
    def unicode_to_glyph_func(self) :
        "the current unicode_to_glyph_func, invoked as follows:\n" \
        "\n" \
        "    status, glyph_index = unicode_to_glyph_func(scaled_font : ScaledFont, unicode : int)\n" \
        "\n" \
        "where it is expected to return the glyph code corresponding to the character code," \
        " along with a status.\n" \
        "This callback is optional, and is only used if a text_to_glyphs_func is not specified." \
        " If neither is specified, then Unicode character codes are directly interpreted as" \
        " glyph codes."
        return \
            self._unicode_to_glyph_func
    #end unicode_to_glyph_func

    @unicode_to_glyph_func.setter
    def unicode_to_glyph_func(self, unicode_to_glyph) :
        self.set_unicode_to_glyph_func(unicode_to_glyph)
    #end unicode_to_glyph_func

    def set_unicode_to_glyph_func(self, unicode_to_glyph) :
        "sets a new value for the unicode_to_glyph_func. Useful for method chaining; otherwise" \
        " just assign to the unicode_to_glyph_func property."
        temp = self._wrap_unicode_to_glyph_func # so the old value doesn't disappear until it's no longer needed
        if unicode_to_glyph != None :
            def wrap_unicode_to_glyph_func(c_scaled_font, unicode, c_glyph_index) :
                scaled_font = ScaledFont(cairo.cairo_scaled_font_reference(c_scaled_font))
                status, glyph_index = unicode_to_glyph(scaled_font, unicode)
                if glyph_index != None :
                    c_glyph_index.contents.value = glyph_index
                #end if
                return \
                    status
            #end wrap_unicode_to_glyph_func
            self._wrap_unicode_to_glyph_func = CAIRO.user_scaled_font_unicode_to_glyph_func_t(wrap_unicode_to_glyph_func)
        else :
            self._wrap_unicode_to_glyph_func = None
        #end if
        cairo.cairo_user_font_face_set_unicode_to_glyph_func(self._cairobj, self._wrap_unicode_to_glyph_func)
        self._unicode_to_glyph_func = unicode_to_glyph
        return \
            self
    #end set_unicode_to_glyph_func

    @property
    def text_to_glyphs_func(self) :
        "the current text_to_glyphs_func, invoked as follows:\n" \
        "\n" \
        "    status, glyphs = text_to_glyphs(scaled_font : ScaledFont, text : str, False)\n" \
        "or\n" \
        "    status, glyphs, clusters, cluster_flags = text_to_glyphs(scaled_font : ScaledFont, text : str, True)\n" \
        "\n" \
        "The second element of the result tuple is a sequence of Glyph objects. If the third" \
        " (cluster_mapping) argument is True, then the result tuple is expected to contain two" \
        " more elements, being the sequence of clusters ((num_chars, num_glyphs) tuples) for" \
        " mapping character indexes to glyph indexes, and the cluster flags.\n" \
        "This callback is optional, and overrides the unicode_to_glyph_func if specified."
        return \
            self._text_to_glyphs_func
    #end text_to_glyphs_func

    @text_to_glyphs_func.setter
    def text_to_glyphs_func(self, text_to_glyphs) :
        self.set_text_to_glyphs_func(text_to_glyphs)
    #end text_to_glyphs_func

    def set_text_to_glyphs_func(self, text_to_glyphs) :
        "sets a new value for the text_to_glyphs_func. Useful for method chaining; otherwise" \
        " just assign to the text_to_glyphs_func property."
        temp = self._wrap_text_to_glyphs_func # so the old value doesn't disappear until it's no longer needed
        if text_to_glyphs != None :
            def wrap_text_to_glyphs_func(c_scaled_font, c_utf8, utf8_len, c_glyphs, c_num_glyphs, c_clusters, c_num_clusters, c_cluster_flags) :
                scaled_font = ScaledFont(cairo.cairo_scaled_font_reference(c_scaled_font))
                text = bytes(c_utf8[i] for i in range(utf8_len))
                if self.pass_unicode :
                    text = text.decode("utf-8")
                #end if
                cluster_mapping = bool(c_clusters)
                result = text_to_glyphs(scaled_font, text, cluster_mapping)
                if cluster_mapping :
                    status, glyphs, clusters, cluster_flags = result
                else :
                    status, glyphs = result[:2]
                    clusters = None
                #end if
                if glyphs != None :
                    nr_glyphs = len(glyphs)
                    if c_num_glyphs.contents.value < nr_glyphs :
                        c_glyphs.contents.value = cairo.cairo_glyph_allocate(nr_glyphs)
                        if c_glyphs.contents.value == None :
                            raise MemoryError("cairo_glyph_allocate failure")
                              # don't bother trying to recover
                        #end if
                    #end if
                    c_num_glyphs.contents.value = nr_glyphs
                    dstarr = ct.cast(c_glyphs.contents, CAIRO.glyph_ptr_t)
                    for i in range(nr_glyphs) :
                        dst = dstarr[i]
                        src = glyphs[i]
                        dst.index = src.index
                        dst.x = src.pos.x
                        dst.y = src.pos.y
                    #end for
                #end if
                if clusters != None :
                    if self.pass_unicode :
                        # convert cluster num_chars to num_bytes
                        pos = 0
                        e_clusters = []
                        for c in clusters :
                            next_pos = pos + c[0]
                            e_clusters.append \
                              (
                                (len(text[pos:next_pos].encode("utf-8")), c[1])
                              )
                            pos = next_pos
                        #end for
                    else :
                        e_clusters = clusters
                    #end if
                    nr_clusters = len(clusters)
                    if c_num_clusters.contents.value < nr_clusters :
                        c_clusters.contents.value = cairo.cairo_text_cluster_allocate(nr_clusters)
                        if c_clusters.contents.value == None :
                            raise MemoryError("cairo_text_cluster_allocate failure")
                              # don't bother trying to recover
                        #end if
                    #end if
                    c_num_clusters.contents.value = nr_clusters
                    dstarr = ct.cast(c_clusters.contents, CAIRO.cluster_ptr_t)
                    for i in range(nr_clusters) :
                        dst = dstarr[i]
                        src = e_clusters[i]
                        dst.num_bytes = src[0]
                        dst.num_glyphs = src[1]
                    #end for
                    c_cluster_flags.contents.value = cluster_flags
                #end if
                return \
                    status
            #end wrap_text_to_glyphs_func
            self._wrap_text_to_glyphs_func = CAIRO.user_scaled_font_text_to_glyphs_func_t(wrap_text_to_glyphs_func)
        else :
            self._wrap_text_to_glyphs_func = None
        #end if
        cairo.cairo_user_font_face_set_text_to_glyphs_func(self._cairobj, self._wrap_text_to_glyphs_func)
        self._text_to_glyphs_func = text_to_glyphs
        return \
            self
    #end set_text_to_glyphs_func

    def copy(self) :
        "returns a new UserFontFace with the same callbacks as this one, and a copy" \
        " of the user_data. The purpose is so that Cairo’s scaled fonts will not" \
        " recognize the copy as the same as the original font."
        result = UserFontFace.create \
          (
            init_func = self.init_func,
            render_glyph_func = self.render_glyph_func,
            text_to_glyphs_func = self.text_to_glyphs_func,
            unicode_to_glyph_func = self.unicode_to_glyph_func,
          )
        result.pass_unicode = self.pass_unicode
        for k in self.user_data :
            result.user_data[k] = self.user_data[k]
        #end for
        return \
            result
    #end copy

#end UserFontFace

FontExtents = def_struct_class \
  (
    name = "FontExtents",
    ctname = "font_extents_t"
  )
class TextExtentsExtra :
    # extra members for TextExtents class.

    @property
    def bounds(self) :
        "returns the bounds of the text_extents as a Rect."
        return \
            Rect(self.x_bearing, self.y_bearing, self.width, self.height)
    #end bounds

    @property
    def advance(self) :
        "returns the x- and y-advance of the text_extents as a Vector."
        return \
            Vector(self.x_advance, self.y_advance)
    #end advance

#end TextExtentsExtra
TextExtents = def_struct_class \
  (
    name = "TextExtents",
    ctname = "text_extents_t",
    extra = TextExtentsExtra
  )
del TextExtentsExtra

#+
# XCB
#-

if HAS.XCB_SURFACE :

    def def_xcb_class(name, ctname, substructs = None, ignore = None) :

        ctstruct = getattr(XCB, ctname)

        class result_class :

            __slots__ = tuple(field[0] for field in ctstruct._fields_) # to forestall typos
            # for use by subclasses:
            _ignore = ignore
            _ctname = ctname
            _ctstruct = ctstruct

            def __init__(self, **fields) :
                unused = set(fields.keys())
                for name, cttype in ctstruct._fields_ :
                    if ignore == None or name not in ignore :
                        setattr(self, name, fields[name])
                        unused.remove(name)
                    #end if
                #end for
                if len(unused) != 0 :
                    raise TypeError("unrecognized fields: %s" % ", ".join(sorted(unused)))
                #end if
            #end __init__

            def to_cairo(self) :
                "returns a Cairo representation of the structure."
                result = ctstruct()
                for name, cttype in ctstruct._fields_ :
                    if ignore == None or name not in ignore :
                        field = getattr(self, name)
                        if substructs != None and name in substructs :
                            field = field.to_cairo()
                        #end if
                        setattr(result, name, field)
                    #end if
                #end for
                return \
                    result
            #end to_cairo

            def __getitem__(self, i) :
                "allows the object to be coerced to a tuple."
                return \
                    getattr(self, ctstruct._fields_[i][0])
            #end __getitem__

            def __repr__(self) :
                return \
                    (
                        "%s(%s)"
                    %
                        (
                            name,
                            ", ".join
                              (
                                "%s = %s" % (field[0], getattr(self, field[0]))
                                for field in ctstruct._fields_
                                if ignore == None or field[0] not in ignore
                              ),
                        )
                    )
            #end __repr__

        #end result_class

    #begin def_xcb_class
        result_class.__name__ = name
        result_class.__doc__ = \
            (
                "representation of an XCB %s structure. Fields are %s."
                "\nCreate by passing all field values by name to the constructor;"
                " convert an instance to Cairo form with the to_cairo method."
            %
                (
                    ctname,
                    ", ".join
                      (
                        f[0] for f in ctstruct._fields_ if ignore == None or f[0] not in ignore
                      ),
                )
            )
        return \
            result_class
    #end def_xcb_class

    XCBVisualType = def_xcb_class \
      (
        name = "XCBVisualType",
        ctname = "visualtype_t",
        ignore = {"pad0"}
      )
    XCBRenderDirectFormat = def_xcb_class \
      (
        name = "XCBRenderDirectFormat",
        ctname = "render_directformat_t"
      )
    XCBScreen = def_xcb_class \
      (
        name = "XCBScreen",
        ctname = "screen_t"
      )
    XCBRenderPictFormInfo = def_xcb_class \
      (
        name = "XCBRenderPictFormInfo",
        ctname = "render_pictforminfo_t",
        substructs = {"direct"},
        ignore = {"pad0"}
      )

    del def_xcb_class # my work is done

    class XCBSurface(Surface) :
        "Surface that draws to an on-screen window via XCB. Do not instantiate" \
        " directly; use one of the create methods. Note that all of these take a" \
        " low-level address (e.g. ctypes.c_void_p) for the connection argument," \
        " and equally low-level ctypes structures for other arguments; it will be" \
        " up to the particular XCB binding to provide appropriate translations to" \
        " these types from its connection and other objects."

        __slots__ = () # to forestall typos

        @classmethod
        def create(celf, connection, drawable, visual, width, height) :
            c_visual = visual.to_cairo()
            c_result = cairo.cairo_xcb_surface_create \
              (
                connection,
                drawable,
                ct.byref(c_visual),
                width,
                height
              )
            return \
                celf(c_result)
        #end create

        @classmethod
        def create_for_bitmap(celf, connection, screen, bitmap, width, height) :
            c_screen = screen.to_cairo()
            c_result = cairo.cairo_xcb_surface_create_for_bitmap \
              (
                connection,
                ct.byref(c_screen),
                bitmap,
                width,
                height
              )
            return \
                celf(c_result)
        #end create_for_bitmap

        @classmethod
        def create_with_xrender_format(celf, connection, screen, drawable, format, width, height) :
            c_screen = screen.to_cairo()
            c_format = format.to_cairo()
            c_result = cairo.cairo_xcb_surface_create_with_xrender_format \
              (
                connection,
                ct.byref(c_screen),
                drawable,
                ct.byref(c_format),
                width,
                height
              )
            return \
                celf(c_result)
        #end create_with_xrender_format

        def set_size(self, dims) :
            dims = Vector.from_tuple(dims)
            cairo.cairo_xcb_surface_set_size(self._cairobj, dims.x, dims.y)
            self._check()
        #end set_size

        def set_drawable(self, drawable, dims) :
            dims = Vector.from_tuple(dims)
            cairo.cairo_xcb_surface_set_drawable(self._cairobj, drawable, dims.x, dims.y)
            self._check()
        #end set_drawable

    #end XCBSurface

#end if

#+
# Xlib
#-

if HAS.XLIB_SURFACE :

    class XlibSurface(Surface) :
        "Surface that draws to an on-screen window via Xlib. Do not instantiate" \
        " directly; use the create methods. Note that these take low-level pointers" \
        " and ctypes structures for arguments; it will be up to the particular Xlib" \
        " binding to provide appropriate translations to these types from its own" \
        " object wrapper types."

        __slots__ = () # to forestall typos

        @classmethod
        def create(celf, dpy, drawable, visual, width, height) :
            c_result = cairo.cairo_xlib_surface_create(dpy, drawable, visual, width, height)
            return \
                celf(c_result)
        #end create

        @classmethod
        def create_for_bitmap(celf, dpy, bitmap, screen, width, height) :
            c_result = cairo.cairo_xlib_surface_create(dpy, bitmap, visual, width, height)
            return \
                celf(c_result)
        #end create_for_bitmap

        @property
        def size(self) :
            return \
                Vector \
                  (
                    cairo.cairo_xlib_surface_get_width(self._cairobj),
                    cairo.cairo_xlib_surface_get_height(self._cairobj),
                  )
        #end size

        @size.setter
        def size(self, size) :
            self.set_size(size)
        #end size

        def set_size(self, size) :
            size = Vector.from_tuple(size)
            cairo.cairo_xlib_surface_set_size(self._cairobj, size.x, size.y)
            self._check()
            return \
                self
        #end set_size

        @property
        def depth(self) :
            return \
                cairo.cairo_xlib_surface_get_depth(self._cairobj)
        #end depth

        @property
        def width(self) :
            return \
                cairo.cairo_xlib_surface_get_width(self._cairobj)
        #end width

        @property
        def height(self) :
            return \
                cairo.cairo_xlib_surface_get_height(self._cairobj)
        #end height

        @property
        def display(self) :
            return \
                cairo.cairo_xlib_surface_get_display(self._cairobj)
        #end display

        @property
        def drawable(self) :
            return \
                cairo.cairo_xlib_surface_get_drawable(self._cairobj)
        #end drawable

        @property
        def screen(self) :
            return \
                cairo.cairo_xlib_surface_get_screen(self._cairobj)
        #end screen

        @property
        def visual(self) :
            return \
                cairo.cairo_xlib_surface_get_visual(self._cairobj)
        #end visual

        if HAS.XLIB_XRENDER :

            @classmethod
            def create_with_xrender_format(celf, dpy, drawable, screen, format, width, height) :
                c_result = cairo.cairo_xlib_surface_create_with_xrender_format(dpy, drawable, screen, format, width, height)
                return \
                    celf(c_result)
            #end create_with_xrender_format

            @property
            def xrender_format(self) :
                return \
                    cairo.cairo_xlib_surface_get_xrender_format(self._cairobj)
            #end xrender_format

        #end if

    #end XlibSurface

#end if

#+
# Overall
#-

def _atexit() :
    # disable all __del__ methods at process termination to avoid segfaults
    for cls in Context, Surface, Device, Pattern, Region, FontOptions, FontFace, ScaledFont :
        delattr(cls, "__del__")
    #end for
#end _atexit
atexit.register(_atexit)
del _atexit

del def_struct_class # my work is done
