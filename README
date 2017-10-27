**Qahirah** is yet another Python language binding for the [Cairo graphics
library](http://cairographics.org/), for use with Python 3.3 or later.
It is modelled to some extent on [Pycairo](http://cairographics.org/pycairo/),
but differs from it in important ways:

* It is implemented entirely in Python, using the ctypes module.
  This offers advantages: automatic support for passing arguments
  by keyword, and argument names appearing in help() output.
* It tries to operate at a higher level than the actual C-centric Cairo API,
  taking advantage of Python’s powerful data-manipulation facilities.
  This is explained in more detail below.
* Because it is pure Python, the abstractions it implements are “leaky”.
  As Guido van Rossum has made clear, “We’re all consenting adults here”.
  If you want to bypass Qahirah’s facilities and make calls directly
  to the underlying Cairo library, there is nothing to prevent you from
  doing so. Whether your code will still work with a future version of
  Qahirah is another matter...


Installation
============

Installation is explained in the setup.py script.


Overview
========

This introduction will assume you have some knowledge of the Cairo
API itself; possibly you have even used the Pycairo Python binding.
Qahirah also has “Context”, “Surface” and “Pattern” classes, similar
to those in Pycairo. To summarize:

* A _Surface_ (underlying Cairo type cairo_surface_t) is a holder
  for the results of drawing. An _ImageSurface_ is a subclass of
  Surface that specifically holds a two-dimensional array of pixels
  (of one of the Cairo-supported formats), but there are other kinds
  of surfaces for rendering direct to PDF files, SVG files and
  other purposes.
* You do not do drawing directly into a Surface. Instead, you do
  your drawing into a _Context_ (underlying Cairo type cairo_t).
  A Context is like a wrapper around a Surface; it holds additional
  state that can affect subsequent drawing calls (e.g. current
  position, source pattern, operator), but are not part of the
  actual contents of the Surface.
* A _Pattern_ (underlying Cairo type cairo_pattern_t) defines how
  pixels are individually affected while drawing. A Pattern can
  consist of a single plain colour (possibly with transparency), or it
  can be a linear or radial gradient of colours, or it can even take
  the image from a Surface.

(There are other object types, but understanding these three is,
I think, core to understanding how Cairo works.)

However, Qahirah introduces some important differences from Pycairo
(and from the underlying Cairo API):

* Vectors
* Properties
* Method-chaining
* Colours
* Rects
* Paths
* FreeType fonts

These are further explained in the sections below.


Vectors
=======

Qahirah makes heavy use of the *Vector* type. This
corresponds to the usual mathematical idea of a 2D vector, with *x*
and *y* components. Where Cairo wants you to pass separate *x*- and
*y*-coordinate values, Qahirah wants you to pass the two as a single
Vector. The reason for this is to reduce repetitiveness of coding:
very often, you want to do a calculation for the *x*-coordinate, and
then repeat the exact same form of calculation for the *y*-coordinate.
The Qahirah Vector type defines addition, subtraction, multiplication
and division directly on Vectors in terms of the corresponding
operations on their components, allowing you to write your coordinate
calculations just once.

However, you will still sometimes need to work with separate coordinate
values. To ease the job of conversion, all Vector arguments to Qahirah
calls can also be written directly as 2-tuples of coordinates, and
Vector call results can be directly interpreted as 2-tuples of
coordinates. Thus, where the cairo_move_to call takes separate x and y
arguments, the Qahirah call works more like this:

    p = Vector(x, y)
    ctx.move_to(p)

which can of course be written as

    ctx.move_to(Vector(x, y))

but even more compactly, and closer to the underlying Cairo call, as

    ctx.move_to((x, y))

Similarly, where cairo_get_current_point returns separate x and
y values, Qahirah returns both at once:

    p = ctx.current_point
    x = p.x
    y = p.y

which, if you need to separate them out, can also be written more
directly as

    x, y = ctx.current_point

The coordinate components of a Vector can be integers or reals.
Some uses (e.g. specifying the dimensions of an ImageSurface)
require integer coordinates; the builtin Python “round()” function
can be used on a Vector to round its coordinates to the nearest
corresponding integers, e.g.:

    >>> v = Vector(3.5, 4.5)
    >>> round(v)
    Vector(4, 4)


Properties
==========

Cairo defines lots of pairs of cairo_get_*property* and cairo_set_*property*
calls. Qahirah collapses these down to a single *property* which can be used
directly in an expression, or assigned to. For example, instead of

    cairo_set_source(ctx, pat)

you can write

    ctx.source = pat

and instead of

    pat = cairo_get_source(ctx)

you write

    pat = ctx.source

However, the set_*property* versions of the calls are still provided,
for use with method-chaining.


Method-chaining
===============

*Method-chaining* is a technique for reducing repetitiveness when making
a series of calls on the same object. This is achieved by having the
method calls return the object itself, allowing the immediate application
of another method call, and so on. For example, instead of this series
of a drawing calls on a Context:

    ctx.new_path()
    ctx.move_to(p1)
    ctx.curve_to(p2, p3, p4)
    ctx.dash = ((1, 1), 0)
    ctx.stroke()

you can write

    (ctx
        .new_path()
        .move_to(p1)
        .curve_to(p2, p3, p4)
        .set_dash((1, 1), 0)
        .stroke()
    )

Method-chaining is also available on appropriate methods of Pattern and
Surface objects.


Colours
=======

Qahirah defines a *Colour* type, which takes advantage of the standard
Python colorsys module to provide conversions between RGB colour space
(the only one supported by Cairo) and HSV, HLS and YIQ colour spaces.
You can construct a Colour by specifying components in any of these
spaces, and you can retrieve the components in any of these spaces
from a Colour. Internally, a Colour always stores R, G, B and alpha
components.

Where Cairo provides calls to set separate RGB or RGBA colour
components, Qahirah does a set of a single Colour value. For
convenience, you can directly pass an (R, G, B) or (R, G, B, A) tuple,
and it will be automatically converted to a Colour. Correspondingly,
where a call returns a Colour, you can convert it directly to an
(R, G, B, A) tuple. If you don’t want the alpha value, just append
“[:-1]” or “[:3]” to the tuple.


Rects
=====

Qahirah defines a *Rect* type, which wraps either an underlying
cairo_rectangle_int_t or cairo_rectangle_t, depending on whether
the coordinates are all integers or not. As with Vectors, the
builtin Python “round()” function can be used to convert a Rect
to one with all-integer coordinates.

Qahirah’s Rect type also defines many useful additional operations.
For example, the “transform_to()” method generates a Matrix that
maps the area covered by a Rect onto another Rect, which is a
very common operation for positioning drawing of figures on a
Surface.


Paths
=====

Cairo defines cairo_path_t and cairo_path_data_t types for holding
path data. The only way to create these is to perform path-creation
operations into a context, and then use cairo_copy_path or cairo_copy_path_flat
to retrieve a copy of the path data.

Qahirah instead offers the Path class. While one of these can
be created with Context.copy_path or Context.copy_path_flat, you can
also construct them yourself from a sequence of Path.Segment objects
(directly representing control point geometry) or Path.Element objects
(mapping more directly to Cairo path-construction calls). Furthermore,
Qahirah allows you to transform a Path through a Matrix, either at
drawing time or to produce a new Path. Context.append_path no longer
calls cairo_append_path; instead, the Path object directly generates
move_to, line_to, curve_to and close_path calls from its elements.


FreeType Fonts
==============

Qahirah gives access to Cairo’s support for FreeType fonts. It has
a built-in minimal FreeType wrapper, but it can also take advantage
of the more extensive freetype2 Python module, available from
[GitLab](https://gitlab.com/ldo/python_freetype>) or
[GitHub](https://github.com/ldo/python_freetype>).

For example, with this module installed, the Path.from_ft_outline
method becomes available, for converting a freetype2.Outline to a
Path.


Other Functional Differences From Pycairo
=========================================

Apart from the above differences, Qahirah is not exactly at functional
parity with Pycairo. Qahirah implements the following major Cairo
features that Pycairo does not:

* User fonts
* Script surfaces
* ScaledFont.text_to_glyphs

while it does not handle most of the GUI-specific surface types that
Pycairo does: Win32 and XLib surfaces.


Examples
========

Examples of Qahirah in action are available in the following
repositories:

* qahirah_examples: [GitLab](https://gitlab.com/ldo/qahirah_examples),
  [GitHub](https://github.com/ldo/qahirah_examples)
* qahirah_notebooks: [GitLab](https://gitlab.com/ldo/qahirah_notebooks),
  [GitHub](https://github.com/ldo/qahirah_notebooks)
* python_pixman_examples: [GitLab](https://gitlab.com/ldo/python_pixman_examples),
  [GitHub](https://github.com/ldo/python_pixman_examples)
* python_freetype_examples: [GitLab](https://gitlab.com/ldo/python_freetype_examples),
  [GitHub](https://github.com/ldo/python_freetype_examples)
* harfpy_examples: [GitLab](https://gitlab.com/ldo/harfpy_examples),
  [GitHub](https://github.com/ldo/harfpy_examples)
* HersheyPy: [GitLab](https://gitlab.com/ldo/hersheypy), [GitHub](https://github.com/ldo/hersheypy)
* anim_framework_examples: [GitLab](https://gitlab.com/ldo/anim_framework_examples),
  [GitHub](https://github.com/ldo/anim_framework_examples)
* curve: [GitLab](https://gitlab.com/ldo/curve), [GitHub](https://github.com/ldo/curve)
* GrainyPy: [GitLab](https://gitlab.com/ldo/grainypy), [GitHub](https://github.com/ldo/grainypy)

Lawrence D'Oliveiro <ldo@geek-central.gen.nz>
2017 October 26
